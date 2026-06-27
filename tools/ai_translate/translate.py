#!/usr/bin/env python3
"""
NPC AI Translation Engine
==========================
Reads extracted task JSON files and translates text using OpenAI API.
Supports batch translation, rate limiting, retry, and resume.

Usage:
    python tools/ai_translate/translate.py --input tmp/ai_translate/tasks/quests.json
    python tools/ai_translate/translate.py --input tmp/ai_translate/tasks/quests.json --model gpt-4o-mini --rpm 30

Environment:
    OPENAI_API_KEY  - Required. Your OpenAI API key.
    OPENAI_BASE_URL - Optional. Custom API base URL (for proxies/compatible APIs).
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ─── Configuration ──────────────────────────────────────────────────────────

RATHENA_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT = RATHENA_ROOT / "tmp" / "ai_translate" / "results"
GLOSSARY_PATH = Path(__file__).resolve().parent / "glossary.json"

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_RPM = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds, multiplied by attempt number

# Max texts per API call (to stay within token limits)
MAX_TEXTS_PER_BATCH = 80

# ─── Glossary ────────────────────────────────────────────────────────────────

def load_glossary() -> dict:
    """Load the RO glossary for translation context."""
    if not GLOSSARY_PATH.exists():
        return {}
    with open(GLOSSARY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_glossary_prompt(glossary: dict) -> str:
    """Build a concise glossary section for the system prompt."""
    lines = []
    for category, terms in glossary.items():
        entries = [f"{en}={zh}" for en, zh in terms.items()]
        lines.append(f"[{category}] " + ", ".join(entries))
    return "\n".join(lines)


# ─── System Prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are a professional game translator for Ragnarok Online (RO), translating NPC dialogue from English to Simplified Chinese.

## Rules
1. Translate naturally in a style fitting a medieval fantasy MMORPG.
2. PRESERVE these elements exactly (do NOT translate):
   - Color codes: ^RRGGBB (e.g., ^3355FF, ^000000)
   - Variable references: .@var, @var, $var, #var, getarg(), strcharinfo(), etc.
   - Script functions: callfunc, getitem, countitem, etc.
   - Item/monster DB constants: Red_Potion, Butterfly_Wing, etc.
   - Numeric values and formulas
3. For NPC name headers like [Guard] or [Kafra Employee], translate the name inside brackets.
4. For select options separated by ":", translate each option but keep the ":" separator. The number of ":" must stay the same.
5. Keep the same punctuation style (periods, exclamation marks, question marks).
6. The translation MUST be encodable in GBK charset. Avoid rare Unicode characters.
7. Return ONLY the JSON array of translated strings, no explanations.

## Glossary
{glossary}

## Output Format
Return a JSON array of translated strings in the SAME ORDER as the input.
Example input: ["Hello adventurer!", "Yes:No:Cancel", "[Guard]"]
Example output: ["你好，冒险者！", "是:否:取消", "[卫兵]"]"""


# ─── OpenAI API ──────────────────────────────────────────────────────────────

def call_openai(messages: list, model: str, api_key: str,
                base_url: str = "https://api.openai.com/v1") -> str:
    """Call OpenAI chat completion API. Returns the assistant message content."""
    url = f"{base_url}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 8192,
    }).encode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode('utf-8'))

    return result["choices"][0]["message"]["content"]


def translate_batch(texts: list, model: str, api_key: str, base_url: str,
                    system_prompt: str) -> list:
    """Translate a batch of texts using OpenAI API.

    Returns list of translated strings (same length as input).
    """
    user_content = json.dumps(texts, ensure_ascii=False)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = call_openai(messages, model, api_key, base_url)

            # Parse response - extract JSON array
            # Handle potential markdown code blocks
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code block (```json ... ``` or ``` ... ```)
                fence_match = re.match(r'```(?:\w+)?\s*\n(.*?)```', response, re.DOTALL)
                if fence_match:
                    response = fence_match.group(1).strip()
                else:
                    # Fallback: remove first and last lines
                    lines = response.split('\n')
                    response = '\n'.join(lines[1:-1]).strip() if len(lines) > 2 else response

            translated = json.loads(response)

            if not isinstance(translated, list):
                raise ValueError(f"Expected JSON array, got {type(translated)}")

            if len(translated) != len(texts):
                raise ValueError(
                    f"Length mismatch: input {len(texts)}, output {len(translated)}")

            return translated

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            if isinstance(e, urllib.error.HTTPError) and e.code == 429:
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF * attempt * 5  # longer wait for rate limit
                    print(f"    Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise
            elif attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF * attempt
                print(f"    API error (attempt {attempt}/{MAX_RETRIES}): {e}")
                print(f"    Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

        except (json.JSONDecodeError, ValueError) as e:
            if attempt < MAX_RETRIES:
                print(f"    Parse error (attempt {attempt}/{MAX_RETRIES}): {e}")
                time.sleep(RETRY_BACKOFF)
            else:
                raise

    raise RuntimeError(f"All {MAX_RETRIES} attempts exhausted for batch of {len(texts)} texts")


# ─── Translation Pipeline ───────────────────────────────────────────────────

def translate_task_file(input_path: Path, output_path: Path, model: str,
                        api_key: str, base_url: str, rpm: int,
                        dry_run: bool = False) -> dict:
    """Translate a single task JSON file.

    Returns stats dict.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    glossary = load_glossary()
    glossary_text = build_glossary_prompt(glossary)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(glossary=glossary_text)

    # Load existing results for resume support
    existing_results = {}
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        for task in existing:
            key = task["source_file"]
            existing_results[key] = task

    min_interval = 60.0 / rpm  # seconds between API calls
    last_call_time = 0

    results = []
    total_translated = 0
    total_skipped = 0
    total_api_calls = 0

    for task_idx, task in enumerate(tasks):
        source_file = task["source_file"]
        print(f"  [{task_idx+1}/{len(tasks)}] {source_file}")

        # Check if already translated (resume support)
        if source_file in existing_results:
            existing_task = existing_results[source_file]
            # Check if all blocks are translated
            all_done = True
            for blk in existing_task.get("npc_blocks", []):
                for t in blk.get("texts", []):
                    if "translated" not in t:
                        all_done = False
                        break
                if not all_done:
                    break
            if all_done:
                print(f"    -> Already translated, skipping")
                results.append(existing_task)
                total_skipped += 1
                continue

        result_task = {
            "source_file": source_file,
            "total_blocks": task["total_blocks"],
            "total_texts": task["total_texts"],
            "npc_blocks": [],
        }

        for blk in task["npc_blocks"]:
            result_blk = {
                "npc_label": blk["npc_label"],
                "npc_name": blk["npc_name"],
                "block_index": blk["block_index"],
                "line_start": blk["line_start"],
                "line_end": blk["line_end"],
                "texts": [],
            }

            # Collect all texts for this block
            originals = [t["original"] for t in blk["texts"]]

            if dry_run:
                # In dry-run mode, just copy originals as "translated"
                for t in blk["texts"]:
                    result_blk["texts"].append({
                        **t,
                        "translated": f"[DRY-RUN] {t['original']}",
                    })
            else:
                # Batch translate (split if too many texts)
                all_translated = []
                for batch_start in range(0, len(originals), MAX_TEXTS_PER_BATCH):
                    batch = originals[batch_start:batch_start + MAX_TEXTS_PER_BATCH]

                    # Rate limiting
                    now = time.time()
                    elapsed = now - last_call_time
                    if elapsed < min_interval:
                        time.sleep(min_interval - elapsed)

                    translated = translate_batch(
                        batch, model, api_key, base_url, system_prompt)
                    last_call_time = time.time()
                    total_api_calls += 1

                    all_translated.extend(translated)

                # Build result texts
                if len(all_translated) != len(blk["texts"]):
                    print(f"    WARNING: Translation count mismatch: "
                          f"expected {len(blk['texts'])}, got {len(all_translated)}")
                for i, t in enumerate(blk["texts"]):
                    if i < len(all_translated):
                        translated_text = all_translated[i]
                    else:
                        print(f"    WARNING: Missing translation for text {i}, using original")
                        translated_text = t["original"]
                    result_blk["texts"].append({
                        **t,
                        "translated": translated_text,
                    })

            total_translated += len(result_blk["texts"])
            result_task["npc_blocks"].append(result_blk)

        results.append(result_task)

        # Save intermediate results (for crash recovery)
        if not dry_run and (task_idx + 1) % 5 == 0:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"    -> Checkpoint saved ({task_idx+1}/{len(tasks)})")

    # Final save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return {
        "input_file": str(input_path),
        "output_file": str(output_path),
        "total_tasks": len(tasks),
        "total_translated": total_translated,
        "total_skipped": total_skipped,
        "total_api_calls": total_api_calls,
    }


def main():
    parser = argparse.ArgumentParser(description="AI-translate NPC text")
    parser.add_argument("--input", type=str, required=True,
                        help="Input task JSON file from extract.py")
    parser.add_argument("--output", type=str, default=None,
                        help="Output result JSON file (default: auto from input name)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        help=f"OpenAI model (default: {DEFAULT_MODEL})")
    parser.add_argument("--rpm", type=int, default=DEFAULT_RPM,
                        help=f"Max requests per minute (default: {DEFAULT_RPM})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't call API, generate placeholder translations")
    parser.add_argument("--base-url", type=str, default=None,
                        help="Custom OpenAI API base URL")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = DEFAULT_OUTPUT / input_path.name

    # API key
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = args.base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not args.dry_run and not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("Set it with: set OPENAI_API_KEY=sk-...")
        sys.exit(1)

    print(f"NPC AI Translation Engine")
    print(f"  Input:    {input_path}")
    print(f"  Output:   {output_path}")
    print(f"  Model:    {args.model}")
    print(f"  RPM:      {args.rpm}")
    print(f"  Base URL: {base_url}")
    print(f"  Dry run:  {args.dry_run}")
    print()

    stats = translate_task_file(
        input_path, output_path, args.model,
        api_key, base_url, args.rpm, args.dry_run)

    print()
    print("=== Translation Summary ===")
    print(f"  Tasks processed: {stats['total_tasks']}")
    print(f"  Texts translated: {stats['total_translated']}")
    print(f"  Tasks skipped (resume): {stats['total_skipped']}")
    print(f"  API calls made: {stats['total_api_calls']}")
    print(f"  Output: {stats['output_file']}")


if __name__ == '__main__':
    main()
