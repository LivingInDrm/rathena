#!/usr/bin/env python3
"""Translate player-visible text fields in rAthena DB YAML files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent.parent
WORK_DIR = ROOT / "tmp" / "ai_translate_db"
MEMORY_FILE = WORK_DIR / "translation_memory.json"
BATCH_DIR = WORK_DIR / "batches"
REPORT_FILE = WORK_DIR / "last_report.json"

sys.path.insert(0, str(TOOLS_DIR))
from translate_fast import RateLimiter, call_openai_json, load_api_config  # noqa: E402

CN_RE = re.compile(r"[\u4e00-\u9fff]")
EN_WORD_RE = re.compile(r"[A-Za-z]{2,}")
FIELD_RE = re.compile(r"^(\s*)([A-Za-z][A-Za-z0-9_]*)(\s*:\s*)(.*?)(\s*(?:#.*)?)$")
FORMAT_RE = re.compile(r"%(?:\d+\$)?[-+0 #]*(?:\*|\d+)?(?:\.(?:\*|\d+))?[hljztL]*[diuoxXfFeEgGaAcspn%]")
COLOR_RE = re.compile(r"\^[0-9A-Fa-f]{6}")


@dataclass(frozen=True)
class DbItem:
    id: str
    source_file: str
    line_index: int
    key: str
    original: str


@dataclass(frozen=True)
class Batch:
    batch_id: str
    items: list[DbItem]


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp936"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def yaml_unquote(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    if value[0] in "\"'" and value[-1:] == value[0]:
        try:
            if value[0] == '"':
                return json.loads(value)
            return value[1:-1].replace("''", "'")
        except Exception:
            return value[1:-1]
    return value


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def is_constant_like(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if re.fullmatch(r"[A-Z0-9_./-]+", stripped):
        return True
    if re.fullmatch(r"\d+(?:\.\d+)?", stripped):
        return True
    return False


def visible_keys_for(path: Path) -> set[str]:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if name in {"mob_db.yml"}:
        return {"Name", "JapaneseName"}
    if name.startswith("item_db_") and name.endswith(".yml"):
        return {"Name"}
    if name == "quest_db.yml":
        return {"Title", "MapName"}
    if name == "skill_db.yml":
        return {"Description"}
    if name == "achievement_db.yml":
        return {"Name"}
    if name in {"instance_db.yml", "castle_db.yml", "battleground_db.yml", "homunculus_db.yml", "pet_db.yml"}:
        return {"Name"}
    if "generator" in parts:
        return set()
    return set()


def target_files(scope: str) -> list[Path]:
    if scope == "all":
        roots = [ROOT / "db" / "re", ROOT / "db" / "pre-re", ROOT / "db"]
    elif scope == "re":
        roots = [ROOT / "db" / "re"]
    elif scope == "pre-re":
        roots = [ROOT / "db" / "pre-re"]
    else:
        roots = [ROOT / value for value in scope.split(",")]
    files: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root.is_file():
            candidates = [root]
        else:
            candidates = sorted(root.rglob("*.yml"))
        for path in candidates:
            if "import" in {part.lower() for part in path.parts}:
                continue
            if visible_keys_for(path) and path not in seen:
                files.append(path)
                seen.add(path)
    return files


def should_translate(value: str) -> bool:
    if CN_RE.search(value):
        return False
    if is_constant_like(value):
        return False
    return bool(EN_WORD_RE.search(value))


def make_item_id(source_file: str, line_index: int, key: str, original: str) -> str:
    raw = f"{source_file}\0{line_index}\0{key}\0{original}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def extract_items(scope: str) -> list[DbItem]:
    items: list[DbItem] = []
    for path in target_files(scope):
        keys = visible_keys_for(path)
        source_file = path.relative_to(ROOT).as_posix()
        for line_index, line in enumerate(read_text(path).splitlines()):
            match = FIELD_RE.match(line)
            if not match:
                continue
            key = match.group(2)
            if key not in keys:
                continue
            raw_value = match.group(4).strip()
            if not raw_value or raw_value in {"[]", "{}"}:
                continue
            value = yaml_unquote(raw_value)
            if should_translate(value):
                items.append(DbItem(make_item_id(source_file, line_index, key, value), source_file, line_index, key, value))
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


def unique_pending(items: Iterable[DbItem], memory: dict[str, str]) -> list[DbItem]:
    seen: set[str] = set()
    pending: list[DbItem] = []
    for item in items:
        if item.original in memory or item.original in seen:
            continue
        seen.add(item.original)
        pending.append(item)
    return pending


def pack_batches(items: list[DbItem], max_chars: int) -> list[Batch]:
    batches: list[Batch] = []
    current: list[DbItem] = []
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
        estimate = len(item.original) + len(item.id) + len(item.key) + 48
        if current and current_chars + estimate > max_chars:
            flush()
        current.append(item)
        current_chars += estimate
    flush()
    return batches


def build_prompt() -> str:
    return """Translate Ragnarok Online database display text into Simplified Chinese.

Return strict JSON only.
Rules:
- Preserve ids exactly.
- Preserve printf placeholders, color codes, skill/item constants, map IDs and numbers exactly.
- Keep official Ragnarok proper nouns recognizable; transliterate names when no common Chinese name is obvious.
- Translate monster names, item display names, quest titles, achievements, instance names and skill descriptions concisely.
- Do not add explanations.

Output schema:
{"translations":[{"id":"...","text":"..."}]}"""


def parse_response(response: str, expected_ids: set[str]) -> dict[str, str]:
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
    missing = expected_ids - result.keys()
    if missing:
        raise ValueError(f"Response missing {len(missing)} ids")
    return result


def batch_output_path(batch: Batch) -> Path:
    return BATCH_DIR / f"{batch.batch_id}.json"


def translate_batch(batch: Batch, model: str, api_key: str, base_url: str, limiter: RateLimiter) -> dict[str, str]:
    output_path = batch_output_path(batch)
    if output_path.exists():
        data = json.loads(output_path.read_text(encoding="utf-8"))
        return {row["id"]: row["translated"] for row in data["items"]}
    payload = {"items": [{"id": item.id, "key": item.key, "text": item.original} for item in batch.items]}
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
    if FORMAT_RE.findall(original) != FORMAT_RE.findall(translated):
        issues.append("printf placeholders mismatch")
    if COLOR_RE.findall(original) != COLOR_RE.findall(translated):
        issues.append("color codes mismatch")
    return issues


def apply_memory(scope: str, memory: dict[str, str], dry_run: bool) -> dict:
    items = extract_items(scope)
    by_file: dict[str, list[DbItem]] = {}
    for item in items:
        if item.original in memory:
            by_file.setdefault(item.source_file, []).append(item)
    stats = {"files": 0, "replaced": 0, "missing": 0, "errors": 0, "dry_run": dry_run}
    errors = []
    for source_file, file_items in sorted(by_file.items()):
        path = ROOT / source_file
        lines = read_text(path).splitlines()
        wanted = {item.line_index: item for item in file_items}
        changed = False
        for index, line in enumerate(lines):
            item = wanted.get(index)
            if not item:
                continue
            translated = memory[item.original]
            issues = validate_pair(item.original, translated)
            if issues:
                errors.append({"item": asdict(item), "translated": translated, "issues": issues})
                stats["errors"] += len(issues)
                continue
            match = FIELD_RE.match(line)
            if not match:
                continue
            lines[index] = f"{match.group(1)}{match.group(2)}{match.group(3)}{yaml_quote(translated)}{match.group(5)}"
            changed = True
            stats["replaced"] += 1
        if changed:
            stats["files"] += 1
            if not dry_run:
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stats["missing"] = sum(1 for item in items if item.original not in memory)
    report = {"stats": stats, "errors": errors}
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def command_plan(args: argparse.Namespace) -> None:
    items = extract_items(args.scope)
    memory = load_memory()
    merged = merge_batch_outputs(memory)
    if merged:
        save_memory(memory)
    pending = unique_pending(items, memory)
    batches = pack_batches(pending, args.max_chars)
    by_file = {}
    for item in pending:
        by_file[item.source_file] = by_file.get(item.source_file, 0) + 1
    print(json.dumps({
        "scope": args.scope,
        "files": len(target_files(args.scope)),
        "items": len(items),
        "memory_entries": len(memory),
        "merged": merged,
        "unique_pending": len(pending),
        "batches": len(batches),
        "top_pending_files": sorted(by_file.items(), key=lambda row: row[1], reverse=True)[:20],
    }, ensure_ascii=False, indent=2))


def command_translate(args: argparse.Namespace) -> None:
    load_api_config()
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    items = extract_items(args.scope)
    memory = load_memory()
    merge_batch_outputs(memory)
    pending = unique_pending(items, memory)
    batches = pack_batches(pending, args.max_chars)
    if args.limit_batches:
        batches = batches[: args.limit_batches]
    limiter = RateLimiter(args.rpm)
    print(f"items={len(items)} memory={len(memory)} pending={len(pending)} batches={len(batches)} workers={args.workers}")
    failures = []
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_batch = {
            executor.submit(translate_batch, batch, model, api_key, base_url, limiter): batch
            for batch in batches
        }
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                translations = future.result()
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
    report = apply_memory(args.scope, memory, args.dry_run)
    print(json.dumps(report["stats"], ensure_ascii=False, indent=2))
    if report["stats"]["errors"] or report["stats"]["missing"]:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "translate", "apply"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--scope", default="all", help="all, re, pre-re, or comma-separated paths")
        if name in {"plan", "translate"}:
            cmd.add_argument("--max-chars", type=int, default=1200)
        if name == "translate":
            cmd.add_argument("--rpm", type=int, default=120)
            cmd.add_argument("--workers", type=int, default=8)
            cmd.add_argument("--limit-batches", type=int)
            cmd.add_argument("--save-every", type=int, default=10)
        if name == "apply":
            cmd.add_argument("--dry-run", action="store_true")
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
