#!/usr/bin/env python3
"""Translate rAthena msg_conf files with validation and resumable cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent.parent
WORK_DIR = ROOT / "tmp" / "ai_translate_msg_conf"
MEMORY_FILE = WORK_DIR / "translation_memory.json"
BATCH_DIR = WORK_DIR / "batches"
REPORT_FILE = WORK_DIR / "last_report.json"

sys.path.insert(0, str(TOOLS_DIR))
from translate_fast import RateLimiter, call_openai_json, load_api_config  # noqa: E402

CN_RE = re.compile(r"[\u4e00-\u9fff]")
EN_WORD_RE = re.compile(r"[A-Za-z]{2,}")
ENTRY_RE = re.compile(r"^(\s*)(\d+)(\s*:\s*)(.*?)(\s*)$")
FORMAT_RE = re.compile(r"%(?:\d+\$)?[-+0 #]*(?:\*|\d+)?(?:\.(?:\*|\d+))?[hljztL]*[diuoxXfFeEgGaAcspn%]")
COLOR_RE = re.compile(r"\^[0-9A-Fa-f]{6}")
SCRIPT_RE = re.compile(r"[@#$]\w+|\.@\w+|\b[A-Z][A-Z0-9_]{2,}\b")

DEFAULT_TARGETS = [
    ("conf/msg_conf/map_msg.conf", "conf/msg_conf/map_msg.conf"),
    ("conf/msg_conf/map_msg.conf", "conf/msg_conf/map_msg_chn.conf"),
    ("conf/msg_conf/char_msg.conf", "conf/msg_conf/char_msg.conf"),
    ("conf/msg_conf/login_msg.conf", "conf/msg_conf/login_msg.conf"),
]


@dataclass(frozen=True)
class MsgItem:
    id: str
    source_file: str
    dest_file: str
    line_index: int
    msg_id: int
    original: str


@dataclass(frozen=True)
class Batch:
    batch_id: str
    items: list[MsgItem]


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp936", "euc_kr"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def should_translate(text: str) -> bool:
    stripped = text.strip()
    if not stripped or CN_RE.search(stripped):
        return False
    return bool(EN_WORD_RE.search(stripped))


def make_item_id(source_file: str, dest_file: str, line_index: int, msg_id: int, original: str) -> str:
    raw = f"{source_file}\0{dest_file}\0{line_index}\0{msg_id}\0{original}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def parse_target(value: str) -> tuple[str, str]:
    if "=" in value:
        source, dest = value.split("=", 1)
        return source.strip().replace("\\", "/"), dest.strip().replace("\\", "/")
    normalized = value.strip().replace("\\", "/")
    return normalized, normalized


def target_pairs(args: argparse.Namespace) -> list[tuple[str, str]]:
    if args.targets:
        return [parse_target(value) for value in args.targets]
    return DEFAULT_TARGETS


def extract_items(pairs: list[tuple[str, str]]) -> list[MsgItem]:
    items: list[MsgItem] = []
    for source_file, dest_file in pairs:
        path = ROOT / source_file
        text = read_text(path)
        for line_index, line in enumerate(text.splitlines()):
            match = ENTRY_RE.match(line)
            if not match:
                continue
            msg_id = int(match.group(2))
            original = match.group(4)
            if not should_translate(original):
                continue
            items.append(
                MsgItem(
                    id=make_item_id(source_file, dest_file, line_index, msg_id, original),
                    source_file=source_file,
                    dest_file=dest_file,
                    line_index=line_index,
                    msg_id=msg_id,
                    original=original,
                )
            )
    return items


def load_memory() -> dict[str, str]:
    if not MEMORY_FILE.exists():
        return {}
    return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))


def save_memory(memory: dict[str, str]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = MEMORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(memory, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(MEMORY_FILE)


def merge_batch_outputs(memory: dict[str, str]) -> int:
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


def unique_pending(items: Iterable[MsgItem], memory: dict[str, str]) -> list[MsgItem]:
    seen: set[str] = set()
    pending: list[MsgItem] = []
    for item in items:
        if item.original in memory or item.original in seen:
            continue
        seen.add(item.original)
        pending.append(item)
    return pending


def pack_batches(items: list[MsgItem], max_chars: int) -> list[Batch]:
    batches: list[Batch] = []
    current: list[MsgItem] = []
    current_chars = 0

    def flush() -> None:
        nonlocal current, current_chars
        if not current:
            return
        digest = hashlib.sha1("\n".join(f"{item.id}:{item.original}" for item in current).encode()).hexdigest()[:16]
        batches.append(Batch(f"{len(batches):05d}-{digest}", current))
        current = []
        current_chars = 0

    for item in items:
        estimate = len(item.original) + len(item.id) + 32
        if current and current_chars + estimate > max_chars:
            flush()
        current.append(item)
        current_chars += estimate
    flush()
    return batches


def build_prompt() -> str:
    return """You are localizing Ragnarok Online server message configuration to Simplified Chinese.

Return strict JSON only. Preserve:
- ids exactly
- printf placeholders such as %s, %d, %.0f, %% exactly and in the same order
- color codes like ^RRGGBB exactly
- script variables, command names, item IDs, map names, constants and @commands
- punctuation that is semantically part of commands

Use concise Simplified Chinese suitable for in-game system messages.
Do not add explanations or markdown.

Output schema:
{"translations":[{"id":"...","text":"..."}]}"""


def batch_output_path(batch: Batch) -> Path:
    return BATCH_DIR / f"{batch.batch_id}.json"


def parse_response(response: str, expected_ids: set[str]) -> dict[str, str]:
    data = json.loads(response)
    rows = data.get("translations")
    if rows is None:
        rows = data.get("items")
    if not isinstance(rows, list):
        raise ValueError("Response JSON does not contain a translations/items array")
    translations: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        item_id = row.get("id")
        text = row.get("text", row.get("translated"))
        if isinstance(item_id, str) and isinstance(text, str):
            translations[item_id] = text
    missing = expected_ids - translations.keys()
    extra = translations.keys() - expected_ids
    if missing:
        raise ValueError(f"Response missing {len(missing)} ids")
    if extra:
        raise ValueError(f"Response contains {len(extra)} unexpected ids")
    return translations


def translate_batch(batch: Batch, model: str, api_key: str, base_url: str, limiter: RateLimiter) -> dict[str, str]:
    output_path = batch_output_path(batch)
    if output_path.exists():
        data = json.loads(output_path.read_text(encoding="utf-8"))
        return {row["id"]: row["translated"] for row in data["items"]}

    payload = {
        "items": [
            {"id": item.id, "text": item.original, "msg_id": item.msg_id}
            for item in batch.items
        ]
    }
    messages = [
        {"role": "system", "content": build_prompt()},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    limiter.acquire()
    response = call_openai_json(messages, model, api_key, base_url)
    translations = parse_response(response, {item.id for item in batch.items})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "batch_id": batch.batch_id,
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


def validate_pair(original: str, translated: str) -> list[str]:
    issues: list[str] = []
    if not translated.strip():
        issues.append("empty translation")
    original_formats = FORMAT_RE.findall(original)
    translated_formats = FORMAT_RE.findall(translated)
    if original_formats != translated_formats:
        issues.append(f"printf placeholders mismatch: {original_formats} != {translated_formats}")
    original_colors = COLOR_RE.findall(original)
    translated_colors = COLOR_RE.findall(translated)
    if original_colors != translated_colors:
        issues.append(f"color codes mismatch: {original_colors} != {translated_colors}")
    for token in SCRIPT_RE.findall(original):
        if token.startswith("@") and token not in translated:
            issues.append(f"command token missing: {token}")
    return issues


def apply_memory(pairs: list[tuple[str, str]], memory: dict[str, str], dry_run: bool) -> dict:
    items = extract_items(pairs)
    by_dest: dict[str, list[MsgItem]] = {}
    for item in items:
        if item.original in memory:
            by_dest.setdefault(item.dest_file, []).append(item)

    stats = {"files": 0, "replaced": 0, "missing": 0, "errors": 0, "dry_run": dry_run}
    errors = []
    for source_file, dest_file in pairs:
        source_path = ROOT / source_file
        dest_path = ROOT / dest_file
        lines = read_text(source_path).splitlines()
        line_items = {item.line_index: item for item in by_dest.get(dest_file, [])}
        changed = False
        for line_index, line in enumerate(lines):
            item = line_items.get(line_index)
            if not item:
                continue
            translated = memory[item.original]
            issues = validate_pair(item.original, translated)
            if issues:
                stats["errors"] += len(issues)
                errors.append({"item": asdict(item), "translated": translated, "issues": issues})
                continue
            match = ENTRY_RE.match(line)
            if not match:
                continue
            lines[line_index] = f"{match.group(1)}{match.group(2)}{match.group(3)}{translated}{match.group(5)}"
            stats["replaced"] += 1
            changed = True
        if changed:
            stats["files"] += 1
            if not dry_run:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    memory_keys = set(memory)
    stats["missing"] = sum(1 for item in items if item.original not in memory_keys)
    report = {"stats": stats, "errors": errors}
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def command_plan(args: argparse.Namespace) -> None:
    pairs = target_pairs(args)
    items = extract_items(pairs)
    memory = load_memory()
    merged = merge_batch_outputs(memory)
    if merged:
        save_memory(memory)
    pending = unique_pending(items, memory)
    batches = pack_batches(pending, args.max_chars)
    print(json.dumps({
        "targets": pairs,
        "items": len(items),
        "memory_entries": len(memory),
        "merged": merged,
        "unique_pending": len(pending),
        "batches": len(batches),
    }, ensure_ascii=False, indent=2))


def command_translate(args: argparse.Namespace) -> None:
    load_api_config()
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    items = extract_items(target_pairs(args))
    memory = load_memory()
    merge_batch_outputs(memory)
    pending = unique_pending(items, memory)
    batches = pack_batches(pending, args.max_chars)
    if args.limit_batches:
        batches = batches[: args.limit_batches]
    limiter = RateLimiter(args.rpm)
    print(f"items={len(items)} memory={len(memory)} pending={len(pending)} batches={len(batches)}")
    completed = 0
    failures = []
    for batch in batches:
        try:
            translations = translate_batch(batch, model, api_key, base_url, limiter)
            for item in batch.items:
                memory[item.original] = translations[item.id]
            completed += 1
            print(f"[ok] {completed}/{len(batches)} {batch.batch_id} items={len(batch.items)}")
            if completed % args.save_every == 0:
                save_memory(memory)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{batch.batch_id}: {exc}")
            print(f"[fail] {batch.batch_id}: {exc}")
    save_memory(memory)
    summary = {"completed": completed, "failed": failures, "memory_entries": len(memory)}
    (WORK_DIR / "translate_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


def command_apply(args: argparse.Namespace) -> None:
    memory = load_memory()
    merge_batch_outputs(memory)
    report = apply_memory(target_pairs(args), memory, args.dry_run)
    print(json.dumps(report["stats"], ensure_ascii=False, indent=2))
    if report["stats"]["errors"] or report["stats"]["missing"]:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "translate", "apply"):
        command = sub.add_parser(name)
        command.add_argument("--target", dest="targets", action="append", help="source or source=dest path")
        if name in {"plan", "translate"}:
            command.add_argument("--max-chars", type=int, default=1200)
        if name == "translate":
            command.add_argument("--rpm", type=int, default=120)
            command.add_argument("--limit-batches", type=int)
            command.add_argument("--save-every", type=int, default=10)
        if name == "apply":
            command.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "plan":
        command_plan(args)
    elif args.command == "translate":
        command_translate(args)
    elif args.command == "apply":
        command_apply(args)


if __name__ == "__main__":
    main()
