#!/usr/bin/env python3
"""
Fast NPC AI translation pipeline.

Design goals:
- Extract untranslated NPC strings at text granularity, not whole-file/block granularity.
- Deduplicate identical English strings into a translation memory.
- Pack large but bounded requests by file context to reduce API calls.
- Allow concurrent API calls behind one in-process global rate limiter.
- Never write NPC files during translation; apply is a separate single-threaded step.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

TOOLS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))

from npc_cn_translate import (  # noqa: E402
    CAPTION_RE,
    MES_RE,
    SELECT_RE,
    backup_file,
    parse_blocks,
    read_npc_file,
    write_gbk,
)
from ai_translate.translate import load_glossary, build_glossary_prompt  # noqa: E402
from ai_translate.validate import (  # noqa: E402
    check_color_codes,
    check_empty_translation,
    check_gbk_encoding,
    check_has_chinese,
    check_script_references,
    check_select_separators,
)


RATHENA_ROOT = Path(__file__).resolve().parent.parent.parent
NPC_DIR = RATHENA_ROOT / "npc"
WORK_DIR = RATHENA_ROOT / "tmp" / "ai_translate_fast"
MEMORY_FILE = WORK_DIR / "translation_memory.json"
BATCH_DIR = WORK_DIR / "batches"
REPORT_FILE = WORK_DIR / "last_report.json"

TRANSLATABLE_DIRS = [
    "cities",
    "airports",
    "battleground",
    "events",
    "guild",
    "guild2",
    "instances",
    "jobs",
    "kafras",
    "merchants",
    "other",
    "quests",
    "custom",
    "pre-re",
    "re",
]
SKIP_DIRS = {"mapflag", "warps", "mobs", "test"}
CN_RE = re.compile(r"[\u4e00-\u9fff]")
ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")
MAX_RETRIES = 3


@dataclass(frozen=True)
class TextItem:
    id: str
    source_file: str
    block_index: int
    text_type: str
    text_index: int
    original: str
    npc_label: str | None
    line_start: int


@dataclass
class Batch:
    batch_id: str
    context_file: str
    items: list[TextItem]
    chars: int


class RateLimiter:
    def __init__(self, rpm: int):
        self.interval = 60.0 / max(1, rpm)
        self.lock = threading.Lock()
        self.next_start = 0.0

    def acquire(self) -> None:
        with self.lock:
            now = time.time()
            wait = max(0.0, self.next_start - now)
            self.next_start = max(now, self.next_start) + self.interval
        if wait > 0:
            time.sleep(wait)


def has_chinese(text: str) -> bool:
    return bool(CN_RE.search(text))


def should_translate_text(text: str) -> bool:
    """Return true only for untranslated English-like display text.

    This deliberately skips pure punctuation, numbers, and mojibake fragments
    such as EUC-KR punctuation decoded as latin-1. Those should be fixed by
    encoding cleanup, not sent to the model.
    """
    if not text.strip() or has_chinese(text):
        return False
    return bool(ASCII_WORD_RE.search(text))


def load_api_config() -> None:
    config_path = Path(__file__).resolve().parent / "api_config.txt"
    if not config_path.exists():
        return
    for line in config_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def iter_target_files(dirs: list[str]) -> Iterable[Path]:
    for dir_name in dirs:
        target = NPC_DIR / dir_name
        if not target.exists():
            continue
        for path in sorted(target.rglob("*.txt")):
            rel_parts = path.relative_to(NPC_DIR).parts
            if any(part in SKIP_DIRS for part in rel_parts):
                continue
            yield path


def make_item_id(source_file: str, block_index: int, text_type: str, text_index: int, original: str) -> str:
    raw = f"{source_file}\0{block_index}\0{text_type}\0{text_index}\0{original}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def extract_items(dirs: list[str]) -> list[TextItem]:
    items: list[TextItem] = []
    for path in iter_target_files(dirs):
        source_file = path.relative_to(NPC_DIR).as_posix()
        content = read_npc_file(path)
        for block_index, block in enumerate(parse_blocks(content)):
            typed_lists = [
                ("mes", block.mes_list),
                ("select", block.select_list),
                ("caption", block.caption_list),
            ]
            for text_type, texts in typed_lists:
                for text_index, original in enumerate(texts):
                    if not should_translate_text(original):
                        continue
                    items.append(
                        TextItem(
                            id=make_item_id(source_file, block_index, text_type, text_index, original),
                            source_file=source_file,
                            block_index=block_index,
                            text_type=text_type,
                            text_index=text_index,
                            original=original,
                            npc_label=block.ident,
                            line_start=block.start + 1,
                        )
                    )
    return items


def load_memory(path: Path = MEMORY_FILE) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def merge_batch_outputs(memory: dict[str, str]) -> int:
    """Merge completed batch shard files into memory.

    This makes interrupted runs recoverable even if the process stopped before
    the periodic memory checkpoint.
    """
    if not BATCH_DIR.exists():
        return 0
    added = 0
    for path in sorted(BATCH_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for row in data.get("items", []):
            original = row.get("original")
            translated = row.get("translated")
            if isinstance(original, str) and isinstance(translated, str) and original not in memory:
                memory[original] = translated
                added += 1
    return added


def save_memory(memory: dict[str, str], path: Path = MEMORY_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(memory, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def unique_pending(items: list[TextItem], memory: dict[str, str]) -> list[TextItem]:
    seen: set[str] = set()
    pending: list[TextItem] = []
    for item in items:
        if item.original in memory or item.original in seen:
            continue
        seen.add(item.original)
        pending.append(item)
    return pending


def pack_batches(items: list[TextItem], max_chars: int) -> list[Batch]:
    batches: list[Batch] = []
    current: list[TextItem] = []
    current_chars = 0
    current_file = ""

    def flush() -> None:
        nonlocal current, current_chars, current_file
        if not current:
            return
        digest = hashlib.sha1(
            "\n".join(f"{item.id}:{item.original}" for item in current).encode("utf-8")
        ).hexdigest()[:16]
        batches.append(Batch(f"{len(batches):05d}-{digest}", current_file, current, current_chars))
        current = []
        current_chars = 0
        current_file = ""

    for item in items:
        estimated = len(item.original) + len(item.id) + 32
        if current and (item.source_file != current_file or current_chars + estimated > max_chars):
            flush()
        if not current:
            current_file = item.source_file
        current.append(item)
        current_chars += estimated
    flush()
    return batches


def build_system_prompt() -> str:
    glossary_text = build_glossary_prompt(load_glossary())
    return f"""You are a professional game translator for Ragnarok Online NPC dialogue.

Translate English to Simplified Chinese. Return strict JSON only.

Rules:
- Preserve IDs exactly.
- Preserve color codes like ^RRGGBB exactly.
- Preserve script variables/functions/constants like .@var, @var, $var, #var, getarg(), countitem(), Red_Potion.
- For select strings, keep ':' separators and option count exactly.
- Use GBK-compatible Simplified Chinese; avoid emoji and rare Unicode.
- Translate NPC name headers like [Guard] into [卫兵].
- Do not add explanations or markdown.

Glossary:
{glossary_text}

Output schema:
{{"items":[{{"id":"same id","translated":"Chinese translation"}}]}}
"""


def call_openai_json(messages: list[dict], model: str, api_key: str, base_url: str) -> str:
    url = f"{base_url}/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def parse_translation_response(response: str, expected_ids: set[str]) -> dict[str, str]:
    text = response.strip()
    if text.startswith("```"):
        match = re.match(r"```(?:\w+)?\s*\n(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    data = json.loads(text)
    if isinstance(data, list):
        rows = data
    else:
        rows = data.get("items")
    if not isinstance(rows, list):
        raise ValueError("Response JSON does not contain an items array")

    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        item_id = str(row.get("id", ""))
        translated = row.get("translated")
        if item_id in expected_ids and isinstance(translated, str):
            result[item_id] = translated

    missing = expected_ids - set(result)
    if missing:
        raise ValueError(f"Response missing {len(missing)} ids")
    return result


def batch_output_path(batch: Batch) -> Path:
    return BATCH_DIR / f"{batch.batch_id}.json"


def split_batch(batch: Batch) -> tuple[Batch, Batch]:
    midpoint = max(1, len(batch.items) // 2)
    left_items = batch.items[:midpoint]
    right_items = batch.items[midpoint:]
    left = Batch(f"{batch.batch_id}a", batch.context_file, left_items, sum(len(item.original) for item in left_items))
    right = Batch(f"{batch.batch_id}b", batch.context_file, right_items, sum(len(item.original) for item in right_items))
    return left, right


def translate_one_batch(batch: Batch, model: str, api_key: str, base_url: str, limiter: RateLimiter) -> dict[str, str]:
    existing_path = batch_output_path(batch)
    if existing_path.exists():
        data = json.loads(existing_path.read_text(encoding="utf-8"))
        return {row["id"]: row["translated"] for row in data["items"]}

    system_prompt = build_system_prompt()
    payload = {
        "context_file": batch.context_file,
        "items": [{"id": item.id, "text": item.original} for item in batch.items],
    }
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    expected_ids = {item.id for item in batch.items}

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            limiter.acquire()
            response = call_openai_json(messages, model, api_key, base_url)
            translations = parse_translation_response(response, expected_ids)
            existing_path.parent.mkdir(parents=True, exist_ok=True)
            existing_path.write_text(
                json.dumps(
                    {
                        "batch_id": batch.batch_id,
                        "context_file": batch.context_file,
                        "items": [
                            {"id": item.id, "original": item.original, "translated": translations[item.id]}
                            for item in batch.items
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return translations
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            if isinstance(exc, (json.JSONDecodeError, ValueError)) and len(batch.items) > 1:
                left, right = split_batch(batch)
                translations = translate_one_batch(left, model, api_key, base_url, limiter)
                translations.update(translate_one_batch(right, model, api_key, base_url, limiter))
                return translations
            sleep_seconds = 5 * attempt if isinstance(exc, urllib.error.HTTPError) and exc.code == 429 else 2 * attempt
            time.sleep(sleep_seconds)

    raise RuntimeError(f"Batch {batch.batch_id} failed after retries: {last_error}")


def validate_pair(item: TextItem, translated: str) -> list[str]:
    issues: list[str] = []
    translated = normalize_translation(item, translated)
    for check in (check_gbk_encoding, check_empty_translation, check_color_codes, check_script_references):
        if check is check_color_codes or check is check_script_references:
            issues.extend(check(item.original, translated))
        else:
            issues.extend(check(translated))
    if item.text_type == "select":
        issues.extend(check_select_separators(item.original, translated))
    return issues


def normalize_translation(item: TextItem, translated: str) -> str:
    if item.text_type == "select" and translated.count(":") != item.original.count(":"):
        normalized = translated.replace("\uFF1A", ":").replace("\uFE55", ":")
        if normalized.count(":") == item.original.count(":"):
            return normalized
    return translated

def apply_memory(items: list[TextItem], memory: dict[str, str], dry_run: bool, no_backup: bool) -> dict:
    by_file: dict[str, list[TextItem]] = {}
    for item in items:
        if item.original in memory:
            by_file.setdefault(item.source_file, []).append(item)

    stats = {"files": 0, "replaced": 0, "missing": 0, "errors": 0, "dry_run": dry_run}
    errors = []

    for source_file, file_items in sorted(by_file.items()):
        path = NPC_DIR / source_file
        content = read_npc_file(path)
        lines = content.splitlines(keepends=False)
        blocks = parse_blocks(content)

        wanted: dict[tuple[int, str, int, str], str] = {}
        for item in file_items:
            translated = normalize_translation(item, memory[item.original])
            pair_issues = validate_pair(item, translated)
            if pair_issues:
                stats["errors"] += len(pair_issues)
                errors.append({"item": asdict(item), "translated": translated, "issues": pair_issues})
                continue
            wanted[(item.block_index, item.text_type, item.text_index, item.original)] = translated

        replacements = 0
        for block_index, block in enumerate(blocks):
            counters = {"mes": 0, "select": 0, "caption": 0}
            for line_index in range(block.start, min(block.end + 1, len(lines))):
                line = lines[line_index]
                mes_match = MES_RE.match(line)
                caption_match = CAPTION_RE.match(line)
                select_match = SELECT_RE.search(line)
                if mes_match:
                    original = mes_match.group(2)
                    key = (block_index, "mes", counters["mes"], original)
                    counters["mes"] += 1
                    if key in wanted and not has_chinese(original):
                        lines[line_index] = mes_match.group(1) + '"' + wanted[key] + '"' + (mes_match.group(3) or ";")
                        replacements += 1
                elif caption_match:
                    original = caption_match.group(2)
                    key = (block_index, "caption", counters["caption"], original)
                    counters["caption"] += 1
                    if key in wanted and not has_chinese(original):
                        lines[line_index] = caption_match.group(1) + '"' + wanted[key] + '"' + (caption_match.group(3) or ";")
                        replacements += 1
                elif select_match:
                    original = select_match.group(2)
                    key = (block_index, "select", counters["select"], original)
                    counters["select"] += 1
                    if key in wanted and not has_chinese(original):
                        lines[line_index] = (
                            line[: select_match.start(1)]
                            + select_match.group(1)
                            + wanted[key]
                            + select_match.group(3)
                            + line[select_match.end() :]
                        )
                        replacements += 1

        if replacements:
            stats["files"] += 1
            stats["replaced"] += replacements
            print(f"[apply] {source_file}: {replacements} replacements")
            if not dry_run:
                if not no_backup:
                    backup_file(path)
                write_gbk(path, "\n".join(lines))

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps({"stats": stats, "errors": errors[:1000]}, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def parse_dirs(value: str | None) -> list[str]:
    if not value or value == "all":
        return TRANSLATABLE_DIRS
    return [part.strip().replace("\\", "/") for part in value.split(",") if part.strip()]


def command_plan(args: argparse.Namespace) -> None:
    dirs = parse_dirs(args.dirs)
    items = extract_items(dirs)
    memory = load_memory()
    merged = merge_batch_outputs(memory)
    if merged:
        save_memory(memory)
    pending = unique_pending(items, memory)
    batches = pack_batches(pending, args.max_chars)
    total_chars = sum(len(item.original) for item in pending)
    summary = {
        "dirs": dirs,
        "untranslated_occurrences": len(items),
        "memory_entries": len(memory),
        "memory_entries_merged_from_batches": merged,
        "unique_pending": len(pending),
        "pending_chars": total_chars,
        "batches": len(batches),
        "max_chars": args.max_chars,
        "estimated_minutes_at_rpm": round(len(batches) * 60.0 / max(1, args.rpm) / 60.0, 2),
        "estimated_minutes_with_workers_floor": round(math.ceil(len(batches) / max(1, args.workers)) * 60.0 / max(1, args.rpm) / 60.0, 2),
    }
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    (WORK_DIR / "plan.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def command_translate(args: argparse.Namespace) -> None:
    load_api_config()
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    dirs = parse_dirs(args.dirs)
    items = extract_items(dirs)
    memory = load_memory()
    merged = merge_batch_outputs(memory)
    if merged:
        save_memory(memory)
    pending = unique_pending(items, memory)
    batches = pack_batches(pending, args.max_chars)
    if args.limit_batches:
        batches = batches[: args.limit_batches]

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    log_path = WORK_DIR / f"translate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log(message: str) -> None:
        print(message, flush=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(message + "\n")

    log(
        f"items={len(items)} memory={len(memory)} merged={merged} "
        f"unique_pending={len(pending)} batches={len(batches)} "
        f"workers={args.workers} rpm={args.rpm} max_chars={args.max_chars}"
    )
    limiter = RateLimiter(args.rpm)
    id_to_original = {item.id: item.original for batch in batches for item in batch.items}
    completed = 0
    failed: list[str] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                translate_one_batch,
                batch,
                args.model,
                api_key,
                args.base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                limiter,
            ): batch
            for batch in batches
        }
        for future in concurrent.futures.as_completed(futures):
            batch = futures[future]
            try:
                translations = future.result()
                for item_id, translated in translations.items():
                    memory[id_to_original[item_id]] = translated
                completed += 1
                if completed % args.save_every == 0:
                    save_memory(memory)
                log(f"[ok] {completed}/{len(batches)} {batch.batch_id} items={len(batch.items)}")
            except Exception as exc:
                failed.append(f"{batch.batch_id}: {exc}")
                log(f"[fail] {batch.batch_id}: {exc}")

    save_memory(memory)
    result = {"completed": completed, "failed": failed, "memory_entries": len(memory)}
    (WORK_DIR / "translate_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if failed:
        raise SystemExit(f"{len(failed)} batches failed; inspect {WORK_DIR / 'translate_summary.json'}")


def command_apply(args: argparse.Namespace) -> None:
    dirs = parse_dirs(args.dirs)
    items = extract_items(dirs)
    memory = load_memory()
    stats = apply_memory(items, memory, args.dry_run, args.no_backup)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fast NPC AI translation pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--dirs", default="all", help="Comma-separated NPC dirs, or all")
        p.add_argument("--max-chars", type=int, default=16000, help="Approximate max input chars per request")
        p.add_argument("--workers", type=int, default=4, help="Concurrent API workers")
        p.add_argument("--rpm", type=int, default=60, help="Global requests per minute")

    plan = sub.add_parser("plan", help="Estimate work without API calls")
    add_common(plan)
    plan.set_defaults(func=command_plan)

    translate = sub.add_parser("translate", help="Translate pending unique strings into memory")
    add_common(translate)
    translate.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    translate.add_argument("--base-url", default=None)
    translate.add_argument("--limit-batches", type=int, default=0, help="Translate only first N batches")
    translate.add_argument("--save-every", type=int, default=5)
    translate.set_defaults(func=command_translate)

    apply_cmd = sub.add_parser("apply", help="Apply memory to NPC files")
    apply_cmd.add_argument("--dirs", default="all", help="Comma-separated NPC dirs, or all")
    apply_cmd.add_argument("--dry-run", action="store_true")
    apply_cmd.add_argument("--no-backup", action="store_true")
    apply_cmd.set_defaults(func=command_apply)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
