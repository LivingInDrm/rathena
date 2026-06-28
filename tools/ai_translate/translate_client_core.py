#!/usr/bin/env python3
"""Translate core text resources in an extracted Ragnarok client directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent.parent
WORK_DIR = ROOT / "tmp" / "ai_translate_client_core"
MEMORY_FILE = WORK_DIR / "translation_memory.json"
BATCH_DIR = WORK_DIR / "batches"
REPORT_FILE = WORK_DIR / "last_report.json"

sys.path.insert(0, str(TOOLS_DIR))
from translate_fast import RateLimiter, call_openai_json, load_api_config  # noqa: E402

CN_RE = re.compile(r"[\u4e00-\u9fff]")
EN_WORD_RE = re.compile(r"[A-Za-z]{2,}")
FORMAT_RE = re.compile(r"%(?:\d+\$)?[-+0 #]*(?:\*|\d+)?(?:\.(?:\*|\d+))?[hljztL]*[diuoxXfFeEgGaAcspn%]")
COLOR_RE = re.compile(r"\^[0-9A-Fa-f]{6}")
LUA_STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
XML_TEXT_RE = re.compile(r">(.*?)<")


@dataclass(frozen=True)
class ClientItem:
    id: str
    file: str
    kind: str
    line_index: int
    segment_index: int
    original: str


@dataclass(frozen=True)
class Batch:
    batch_id: str
    items: list[ClientItem]


DEFAULT_FILES = [
    r"data\msgstringtable.txt",
    r"data\mapnametable.txt",
    r"data\questid2display.txt",
    r"data\ba_frostjoke.txt",
    r"data\dc_scream.txt",
    r"data\luafiles514\lua files\skillinfoz\skilldescript.lub",
]


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp936", "euc_kr", "latin1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def should_translate(text: str) -> bool:
    stripped = text.strip()
    if not stripped or CN_RE.search(stripped):
        return False
    if stripped in {"#", "_", "_______________________"}:
        return False
    if re.fullmatch(r"[\W\d_]+", stripped):
        return False
    if re.fullmatch(r"[A-Z0-9_.:/\\-]+", stripped):
        return False
    return bool(EN_WORD_RE.search(stripped))


def make_item_id(file: str, kind: str, line_index: int, segment_index: int, original: str) -> str:
    raw = f"{file}\0{kind}\0{line_index}\0{segment_index}\0{original}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def client_files(client_dir: Path, values: list[str] | None) -> list[Path]:
    rels = values or DEFAULT_FILES
    return [client_dir / rel for rel in rels]


def lua_unescape(text: str) -> str:
    return text.replace(r"\"", '"').replace(r"\\", "\\")


def lua_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\r", r"\r").replace("\n", r"\n").replace("\t", r"\t").replace('"', r"\"")


def is_lua_internal_string(rel: str, line: str, segment_index: int) -> bool:
    rel_lower = rel.lower()
    stripped = line.strip()

    if rel_lower.endswith("\\itemdbnametbl.lub"):
        return True
    if rel_lower.endswith("\\worldviewdata\\worldviewdata_list.lub"):
        return True
    if rel_lower.endswith("\\pcjobname.lub") or rel_lower.endswith("\\pcjobnamegender.lub"):
        return True
    if rel_lower.endswith("\\accname.lub") or rel_lower.endswith("\\spriterobename.lub"):
        return True

    if segment_index == 0 and stripped.startswith('["'):
        return True

    internal_markers = (
        "ResourceName =",
        "BaseItem =",
        "ResultItem =",
        "Material =",
        "RandomOptionCode =",
        "AddTargetItem(",
        "SetRequire(",
        "SetReset(",
        "AddUpgradeEnchant(",
        "AddPerfectEnchant(",
    )
    if any(marker in line for marker in internal_markers):
        return "SetCaution(" not in line

    if (
        ("lapine" in rel_lower or "itemreform" in rel_lower or "enchant" in rel_lower)
        and re.search(r'^\s*\{\s*"[^"]+"\s*,\s*\d+', line)
    ):
        return True

    return False


def extract_file(client_dir: Path, path: Path) -> list[ClientItem]:
    rel = str(path.relative_to(client_dir)).replace("/", "\\")
    text = read_text(path)
    items: list[ClientItem] = []
    name = path.name.lower()
    lines = text.splitlines()

    def add(kind: str, line_index: int, segment_index: int, value: str) -> None:
        if should_translate(value):
            items.append(ClientItem(make_item_id(rel, kind, line_index, segment_index, value), rel, kind, line_index, segment_index, value))

    for line_index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped in {"FROST JOKE", "SCREAM"}:
            continue
        if name == "msgstringtable.txt":
            if line.endswith("#"):
                add("line_hash_suffix", line_index, 0, line[:-1])
            else:
                add("line", line_index, 0, line)
        elif name == "mapnametable.txt":
            parts = line.split("#")
            if len(parts) >= 2 and parts[0].endswith(".rsw"):
                add("hash_field", line_index, 1, parts[1])
        elif name == "questid2display.txt":
            parts = line.split("#")
            if len(parts) >= 5 and parts[0].isdigit():
                add("hash_field", line_index, 1, parts[1])
            elif len(parts) >= 2:
                add("hash_field", line_index, 0, parts[0])
        elif name in {"ba_frostjoke.txt", "dc_scream.txt"}:
            add("indented_line", line_index, 0, stripped)
        elif rel.lower().startswith("data\\book\\") and name.endswith(".txt"):
            if not stripped.startswith("%"):
                add("line", line_index, 0, line)
        elif name.endswith(".xml"):
            segment_index = 0
            for match in XML_TEXT_RE.finditer(line):
                value = match.group(1).strip()
                add("xml_text", line_index, segment_index, value)
                segment_index += 1
        elif name.endswith((".lua", ".lub")):
            segment_index = 0
            for match in LUA_STRING_RE.finditer(line):
                value = lua_unescape(match.group(1))
                if not is_lua_internal_string(rel, line, segment_index):
                    add("lua_string", line_index, segment_index, value)
                segment_index += 1
    return items


def extract_items(client_dir: Path, paths: list[Path]) -> list[ClientItem]:
    items: list[ClientItem] = []
    for path in paths:
        if path.exists():
            items.extend(extract_file(client_dir, path))
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


def seed_memory(memory: dict[str, str]) -> int:
    added = 0
    for path in [
        ROOT / "tmp" / "ai_translate_db" / "translation_memory.json",
        ROOT / "tmp" / "ai_translate_msg_conf" / "translation_memory.json",
    ]:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, value in data.items():
            if key not in memory:
                memory[key] = value
                added += 1
    return added


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


def unique_pending(items: Iterable[ClientItem], memory: dict[str, str]) -> list[ClientItem]:
    seen: set[str] = set()
    pending: list[ClientItem] = []
    for item in items:
        if item.original in memory or item.original in seen:
            continue
        seen.add(item.original)
        pending.append(item)
    return pending


def pack_batches(items: list[ClientItem], max_chars: int) -> list[Batch]:
    batches: list[Batch] = []
    current: list[ClientItem] = []
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
        estimate = len(item.original) + len(item.id) + 48
        if current and current_chars + estimate > max_chars:
            flush()
        current.append(item)
        current_chars += estimate
    flush()
    return batches


def build_prompt() -> str:
    return """Translate Ragnarok Online client UI text to Simplified Chinese.

Return strict JSON only.
Rules:
- Preserve ids exactly.
- Preserve # delimiters only if they are part of the provided text.
- Preserve printf placeholders, color codes like ^RRGGBB, commands (/sit, @commands), item/skill constants and numbers.
- Use concise in-game Simplified Chinese.
- Keep proper nouns recognizable; transliterate if needed.
- Do not add explanations.

Output schema:
{"translations":[{"id":"...","text":"..."}]}"""


def parse_response(response: str, expected_ids: set[str]) -> tuple[dict[str, str], set[str]]:
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
    return result, missing


def batch_output_path(batch: Batch) -> Path:
    return BATCH_DIR / f"{batch.batch_id}.json"


def partial_batch_output_path(batch: Batch) -> Path:
    return BATCH_DIR / f"{batch.batch_id}.partial.json"


def translate_batch(batch: Batch, model: str, api_key: str, base_url: str, limiter: RateLimiter) -> dict[str, str]:
    output_path = batch_output_path(batch)
    if output_path.exists():
        data = json.loads(output_path.read_text(encoding="utf-8"))
        return {row["id"]: row["translated"] for row in data["items"]}
    payload = {"items": [{"id": item.id, "text": item.original} for item in batch.items]}
    messages = [
        {"role": "system", "content": build_prompt()},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    limiter.acquire()
    response = call_openai_json(messages, model, api_key, base_url)
    translations, missing = parse_response(response, {item.id for item in batch.items})
    if not translations:
        raise ValueError(f"Response missing {len(missing)} ids")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path = output_path if not missing else partial_batch_output_path(batch)
    cache_items = [item for item in batch.items if item.id in translations]
    cache_path.write_text(
        json.dumps(
            {"batch_id": batch.batch_id, "complete": not missing, "missing": len(missing), "items": [{"id": item.id, "original": item.original, "translated": translations[item.id]} for item in cache_items]},
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
    if format_tokens(original) != format_tokens(translated):
        issues.append("printf placeholders mismatch")
    if Counter(COLOR_RE.findall(original)) != Counter(COLOR_RE.findall(translated)):
        issues.append("color codes mismatch")
    return issues


def format_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for match in FORMAT_RE.finditer(text):
        token = match.group(0)
        next_char = text[match.end(): match.end() + 1]
        if " " in token and token != "% d":
            continue
        if token.startswith("% ") and len(token) == 3 and token[2].isalpha() and next_char.isalpha():
            continue
        tokens.append(token)
    return tokens


def replace_line_segment(line: str, item: ClientItem, translated: str) -> str:
    name = Path(item.file).name.lower()
    if item.kind == "line_hash_suffix":
        return translated + "#"
    if item.kind == "line":
        return translated
    if item.kind == "indented_line":
        indent = line[: len(line) - len(line.lstrip())]
        return indent + translated
    if item.kind == "hash_field":
        parts = line.split("#")
        parts[item.segment_index] = translated
        return "#".join(parts)
    if item.kind == "lua_string":
        current = -1
        pieces = []
        last = 0
        for match in LUA_STRING_RE.finditer(line):
            current += 1
            if current != item.segment_index:
                continue
            pieces.append(line[last:match.start(1)])
            pieces.append(lua_escape(translated))
            last = match.end(1)
            break
        if pieces:
            pieces.append(line[last:])
            return "".join(pieces)
    if item.kind == "xml_text":
        current = -1
        pieces = []
        last = 0
        for match in XML_TEXT_RE.finditer(line):
            current += 1
            if current != item.segment_index:
                continue
            original = match.group(1)
            prefix_len = len(original) - len(original.lstrip())
            suffix_len = len(original) - len(original.rstrip())
            pieces.append(line[last:match.start(1)])
            pieces.append(original[:prefix_len])
            pieces.append(translated)
            pieces.append(original[len(original) - suffix_len:] if suffix_len else "")
            last = match.end(1)
            break
        if pieces:
            pieces.append(line[last:])
            return "".join(pieces)
    raise ValueError(f"unsupported replacement for {name}: {item.kind}")


def backup_files(client_dir: Path, paths: list[Path]) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_root = Path(r"D:\rag_cn_backup") / stamp
    for path in paths:
        if not path.exists():
            continue
        rel = path.relative_to(client_dir)
        dest = backup_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    return backup_root


def apply_memory(client_dir: Path, paths: list[Path], memory: dict[str, str], dry_run: bool, no_backup: bool) -> dict:
    items = extract_items(client_dir, paths)
    by_file: dict[str, list[ClientItem]] = {}
    for item in items:
        if item.original in memory:
            by_file.setdefault(item.file, []).append(item)
    stats = {"files": 0, "replaced": 0, "missing": 0, "errors": 0, "dry_run": dry_run, "backup": None}
    errors = []
    if not dry_run and not no_backup:
        stats["backup"] = str(backup_files(client_dir, [client_dir / item.file for item in items]))
    for rel, file_items in sorted(by_file.items()):
        path = client_dir / rel
        lines = read_text(path).splitlines()
        by_line: dict[int, list[ClientItem]] = {}
        for item in file_items:
            by_line.setdefault(item.line_index, []).append(item)
        changed = False
        for line_index, line_items in by_line.items():
            line = lines[line_index]
            for item in sorted(line_items, key=lambda x: x.segment_index, reverse=True):
                translated = memory[item.original]
                issues = validate_pair(item.original, translated)
                if issues:
                    errors.append({"item": asdict(item), "translated": translated, "issues": issues})
                    stats["errors"] += len(issues)
                    continue
                line = replace_line_segment(line, item, translated)
                stats["replaced"] += 1
                changed = True
            lines[line_index] = line
        if changed:
            stats["files"] += 1
            if not dry_run:
                path.write_text("\n".join(lines) + "\n", encoding="cp936", errors="replace")
    stats["missing"] = sum(1 for item in items if item.original not in memory)
    report = {"stats": stats, "errors": errors}
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def command_plan(args: argparse.Namespace) -> None:
    client_dir = Path(args.client_dir)
    paths = client_files(client_dir, args.files)
    items = extract_items(client_dir, paths)
    memory = load_memory()
    seeded = seed_memory(memory) if args.seed else 0
    merged = merge_batch_outputs(memory)
    if seeded or merged:
        save_memory(memory)
    pending = unique_pending(items, memory)
    batches = pack_batches(pending, args.max_chars)
    by_file = {}
    for item in pending:
        by_file[item.file] = by_file.get(item.file, 0) + 1
    print(json.dumps({
        "client_dir": str(client_dir),
        "files": [str(path) for path in paths],
        "items": len(items),
        "memory_entries": len(memory),
        "seeded": seeded,
        "merged": merged,
        "unique_pending": len(pending),
        "batches": len(batches),
        "top_pending_files": sorted(by_file.items(), key=lambda row: row[1], reverse=True),
    }, ensure_ascii=False, indent=2))


def command_translate(args: argparse.Namespace) -> None:
    load_api_config()
    api_key = os.environ["OPENAI_API_KEY"]
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    client_dir = Path(args.client_dir)
    items = extract_items(client_dir, client_files(client_dir, args.files))
    memory = load_memory()
    seed_memory(memory)
    merge_batch_outputs(memory)
    pending = unique_pending(items, memory)
    batches = pack_batches(pending, args.max_chars)
    if args.limit_batches:
        batches = batches[: args.limit_batches]
    limiter = RateLimiter(args.rpm)
    print(f"items={len(items)} memory={len(memory)} pending={len(pending)} batches={len(batches)} workers={args.workers}")
    completed = 0
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_batch = {executor.submit(translate_batch, batch, model, api_key, base_url, limiter): batch for batch in batches}
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                translations = future.result()
                for item in batch.items:
                    if item.id not in translations:
                        continue
                    memory[item.original] = translations[item.id]
                missing = len(batch.items) - len(translations)
                if missing:
                    failures.append(f"{batch.batch_id}: Response missing {missing} ids")
                    print(f"[partial] {batch.batch_id} items={len(translations)} missing={missing}")
                else:
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
    client_dir = Path(args.client_dir)
    memory = load_memory()
    seed_memory(memory)
    merge_batch_outputs(memory)
    report = apply_memory(client_dir, client_files(client_dir, args.files), memory, args.dry_run, args.no_backup)
    print(json.dumps(report["stats"], ensure_ascii=False, indent=2))
    if report["stats"]["errors"] or report["stats"]["missing"]:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "translate", "apply"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--client-dir", default=r"D:\rag")
        cmd.add_argument("--file", dest="files", action="append", help="client-relative file path")
        if name in {"plan", "translate"}:
            cmd.add_argument("--max-chars", type=int, default=1200)
        if name == "plan":
            cmd.add_argument("--seed", action="store_true")
        if name == "translate":
            cmd.add_argument("--workers", type=int, default=8)
            cmd.add_argument("--rpm", type=int, default=120)
            cmd.add_argument("--limit-batches", type=int)
            cmd.add_argument("--save-every", type=int, default=10)
        if name == "apply":
            cmd.add_argument("--dry-run", action="store_true")
            cmd.add_argument("--no-backup", action="store_true")
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
