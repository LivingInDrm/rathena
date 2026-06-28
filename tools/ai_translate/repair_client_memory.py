"""Repair client translation memory entries that failed format validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent.parent
WORK_DIR = ROOT / "tmp" / "ai_translate_client_core"
MEMORY_FILE = WORK_DIR / "translation_memory.json"
REPORT_FILE = WORK_DIR / "last_report.json"
REPAIR_DIR = WORK_DIR / "repair_batches"

sys.path.insert(0, str(TOOLS_DIR))
from translate_fast import RateLimiter, call_openai_json, load_api_config  # noqa: E402
from translate_client_core import COLOR_RE, format_tokens, save_memory, validate_pair  # noqa: E402


@dataclass(frozen=True)
class RepairItem:
    id: str
    original: str
    bad: str
    issues: list[str]


@dataclass(frozen=True)
class RepairBatch:
    batch_id: str
    items: list[RepairItem]


def stable_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_memory() -> dict[str, str]:
    if not MEMORY_FILE.exists():
        return {}
    return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))


def load_repair_items() -> list[RepairItem]:
    report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
    seen: set[str] = set()
    items: list[RepairItem] = []
    for error in report["errors"]:
        original = error["item"]["original"]
        if original in seen:
            continue
        seen.add(original)
        items.append(
            RepairItem(
                id=stable_id(original),
                original=original,
                bad=error["translated"],
                issues=error["issues"],
            )
        )
    return items


def pack_batches(items: list[RepairItem], max_chars: int) -> list[RepairBatch]:
    batches: list[RepairBatch] = []
    current: list[RepairItem] = []
    current_chars = 0
    for item in items:
        estimate = len(item.original) + len(item.bad) + 160
        if current and current_chars + estimate > max_chars:
            digest = stable_id("\n".join(row.id for row in current))
            batches.append(RepairBatch(f"{len(batches):05d}-{digest}", current))
            current = []
            current_chars = 0
        current.append(item)
        current_chars += estimate
    if current:
        digest = stable_id("\n".join(row.id for row in current))
        batches.append(RepairBatch(f"{len(batches):05d}-{digest}", current))
    return batches


def build_prompt() -> str:
    return """Repair Simplified Chinese translations for Ragnarok Online client text.

Return strict JSON only.
Rules:
- Translate only the exact source fragment; do not complete missing context from neighboring lines.
- Preserve the exact ordered printf placeholders from source, including %%.
- Preserve the exact ordered color codes from source, such as ^RRGGBB.
- Copy every required color code token verbatim, even if it looks malformed or unusual.
- Do not add color codes or placeholders not present in source.
- Keep concise in-game Simplified Chinese.

Output schema:
{"translations":[{"id":"...","text":"..."}]}"""


def output_path(batch: RepairBatch) -> Path:
    return REPAIR_DIR / f"{batch.batch_id}.json"


def parse_response(response: str) -> dict[str, str]:
    data = json.loads(response)
    rows = data.get("translations", data.get("items"))
    if not isinstance(rows, list):
        raise ValueError("Response JSON does not contain translations/items")
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        item_id = row.get("id")
        text = row.get("text", row.get("translated"))
        if isinstance(item_id, str) and isinstance(text, str):
            result[item_id] = text
    return result


def repair_batch(batch: RepairBatch, model: str, api_key: str, base_url: str, limiter: RateLimiter) -> dict[str, str]:
    path = output_path(batch)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return {row["id"]: row["translated"] for row in data["items"]}
    payload = {
        "items": [
            {
                "id": item.id,
                "source": item.original,
                "required_printf": format_tokens(item.original),
                "required_colors": COLOR_RE.findall(item.original),
                "issues": item.issues,
            }
            for item in batch.items
        ]
    }
    messages = [
        {"role": "system", "content": build_prompt()},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    limiter.acquire()
    translations = parse_response(call_openai_json(messages, model, api_key, base_url))
    path.parent.mkdir(parents=True, exist_ok=True)
    cache_items = [
        {"id": item.id, "original": item.original, "translated": translations[item.id]}
        for item in batch.items
        if item.id in translations
    ]
    path.write_text(json.dumps({"batch_id": batch.batch_id, "items": cache_items}, ensure_ascii=False, indent=2), encoding="utf-8")
    return translations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-chars", type=int, default=2500)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--rpm", type=int, default=120)
    parser.add_argument("--limit-batches", type=int, default=0)
    args = parser.parse_args()

    load_api_config()
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = args.model or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    memory = load_memory()
    items = [item for item in load_repair_items() if validate_pair(item.original, memory.get(item.original, item.bad))]
    batches = pack_batches(items, args.max_chars)
    if args.limit_batches:
        batches = batches[: args.limit_batches]
    print(f"items={len(items)} batches={len(batches)} workers={args.workers}")

    completed = 0
    failures: list[str] = []
    limiter = RateLimiter(args.rpm)
    id_to_item = {item.id: item for item in items}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(repair_batch, batch, model, api_key, base_url, limiter): batch for batch in batches}
        for future in as_completed(futures):
            batch = futures[future]
            try:
                translations = future.result()
                accepted = 0
                rejected = 0
                for item_id, text in translations.items():
                    item = id_to_item[item_id]
                    issues = validate_pair(item.original, text)
                    if issues:
                        rejected += 1
                        continue
                    memory[item.original] = text
                    accepted += 1
                completed += 1
                print(f"[ok] {completed}/{len(batches)} {batch.batch_id} accepted={accepted} rejected={rejected}")
                save_memory(memory)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{batch.batch_id}: {exc}")
                print(f"[fail] {batch.batch_id}: {exc}")
    save_memory(memory)
    summary = {"completed": completed, "failed": failures, "memory_entries": len(memory)}
    (WORK_DIR / "repair_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
