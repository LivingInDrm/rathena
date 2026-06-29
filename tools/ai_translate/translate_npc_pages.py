#!/usr/bin/env python3
"""Page-level NPC dialogue translation, reflow, and QA helpers.

This script is intentionally separate from translate_fast.py. It extracts
consecutive mes/caption lines as one dialogue page, translates that page with
context, reflows the Chinese text back into mes lines, and validates structural
tokens before applying.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent.parent
DEFAULT_NPC_ROOT = ROOT / "npc"
WORK_DIR = ROOT / "tmp" / "ai_translate_npc_pages"
PAGES_FILE = WORK_DIR / "pages.json"
TRANSLATIONS_FILE = WORK_DIR / "translations.json"
QA_FILE = WORK_DIR / "qa_report.json"

sys.path.insert(0, str(TOOLS_DIR))
from translate_fast import RateLimiter, call_openai_json, load_api_config  # noqa: E402

CN_RE = re.compile(r"[\u4e00-\u9fff]")
EN_WORD_RE = re.compile(r"[A-Za-z]{2,}")
COLOR_RE = re.compile(r"\^[0-9A-Fa-f]{6}")
SCRIPT_TOKEN_RE = re.compile(r"[@#$]\w+|\.@\w+|</?(?:NAVI|INFO)>")
BREAK_PUNCTUATION = "\uFF0C\u3002\uFF01\uFF1F\uFF1B\uFF1A\u3001,.!?;:"
ASCII_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+'./-]*")
ALLOWED_MIXED_ASCII_WORDS = {
    "AGI",
    "Alt",
    "ASPD",
    "ATK",
    "A",
    "B",
    "BBQ",
    "C",
    "Ctrl",
    "DEX",
    "DEF",
    "E",
    "EXP",
    "F1",
    "F9",
    "F12",
    "GUI",
    "G",
    "G-",
    "GOD-POING",
    "HP",
    "INT",
    "JOB",
    "J",
    "JJ",
    "L",
    "LUK",
    "M",
    "Lv",
    "LV",
    "MATK",
    "MDEF",
    "NPC",
    "O",
    "Online",
    "POING",
    "Q",
    "RO",
    "Ragnarok",
    "S",
    "SP",
    "STR",
    "Shift",
    "Tab",
    "TM",
    "TMD",
    "VIP",
    "VIT",
    "V",
    "X",
    "XX",
    "Z",
    "Zeny",
    "Nyxltron",
    "p",
    "z",
    "bawi",
    "bo",
    "cobo",
    "ctrl",
    "emotion",
    "gawi",
    "http",
    "nc",
    "ns",
    "organize",
    "ragnarokonline",
    "shift",
    "spacer",
    "tab",
    "where",
}
MES_RE = re.compile(r'^(\s*mes\s+)"((?:\\.|[^"\\])*)"(.*)$')
CAPTION_RE = re.compile(r'^(\s*caption\s+)"((?:\\.|[^"\\])*)"(.*)$')
SELECT_RE = re.compile(r'(\bselect\s*\(\s*")((?:\\.|[^"\\])*)(")')
NPCTALK_RE = re.compile(r'(\bnpctalk\s+")((?:\\.|[^"\\])*)(")')
ANNOUNCE_RE = re.compile(r'(\b(?:announce|mapannounce|areaannounce)\s+")((?:\\.|[^"\\])*)(")')
BRACKET_NAME_RE = re.compile(r"^\[([^\]]+)\]$")
LOW_VALUE_RE = re.compile(r"^(?:[A-Z0-9_#.:/\\-]+|[a-z_]+(?:\.[a-z0-9_]+)?|[A-Za-z_]+#?\d*)$")
SCRIPT_DEF_RE = re.compile(r"^(?P<prefix>[^/\n].*?\bscript\s+)(?P<name>[^\t,]+)(?P<rest>\t[^\n]*)$")
DUPLICATE_DEF_RE = re.compile(r"^(?P<prefix>[^/\n].*?\bduplicate\((?P<source>[^)]+)\)\s+)(?P<name>[^\t,]+)(?P<rest>\t[^\n]*)$")
SKIP_DIRS = {"mapflag", "mobs", "test"}


@dataclass(frozen=True)
class SourceLine:
    line_index: int
    kind: str
    original: str


@dataclass(frozen=True)
class Page:
    id: str
    file: str
    kind: str
    start_line: int
    end_line: int
    speaker: str
    text: str
    lines: list[SourceLine]


@dataclass(frozen=True)
class Batch:
    batch_id: str
    pages: list[Page]


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gbk", "cp936", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def write_gbk(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("gbk", errors="replace"))


def lua_unescape(text: str) -> str:
    return text.replace(r"\"", '"').replace(r"\\", "\\")


def lua_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', r"\"")


def visible_text(text: str) -> str:
    return COLOR_RE.sub("", text).strip()


def has_chinese(text: str) -> bool:
    return bool(CN_RE.search(text))


def untranslated_ascii_words(text: str) -> list[str]:
    stripped = visible_text(text)
    words: list[str] = []
    for word in ASCII_WORD_RE.findall(stripped):
        normalized = word.strip("'\".。")
        if not normalized:
            continue
        if normalized in ALLOWED_MIXED_ASCII_WORDS:
            continue
        if re.fullmatch(r"F+|F\d+", normalized):
            continue
        if "." in normalized and re.fullmatch(r"[A-Za-z0-9./-]+", normalized):
            continue
        shortcut_parts = [part for part in re.split(r"\+", normalized) if part]
        if len(shortcut_parts) > 1 and all(part in ALLOWED_MIXED_ASCII_WORDS for part in shortcut_parts):
            continue
        words.append(word)
    return words


def should_translate(text: str) -> bool:
    stripped = visible_text(text)
    if not stripped:
        return False
    if "strcharinfo(" in stripped or "getarg(" in stripped or SCRIPT_TOKEN_RE.search(stripped):
        return False
    if has_chinese(stripped):
        return bool(untranslated_ascii_words(stripped))
    if not EN_WORD_RE.search(stripped):
        return False
    if LOW_VALUE_RE.fullmatch(stripped) and not BRACKET_NAME_RE.fullmatch(stripped):
        return False
    return True


def split_npc_name(name: str) -> tuple[str, str]:
    separators = [index for index in (name.find("#"), name.find("::")) if index >= 0]
    if not separators:
        return name, ""
    index = min(separators)
    return name[:index], name[index:]


def make_npc_name_page(file: str, line_index: int, full_name: str) -> Page | None:
    visible_name, _ = split_npc_name(full_name)
    if not visible_name.strip() or has_chinese(visible_name) or not EN_WORD_RE.search(visible_name):
        return None
    if "_" in visible_name and " " not in visible_name:
        return None
    if re.match(r"^\d+_", visible_name):
        return None
    if re.search(r"\d", visible_name) and " " not in visible_name:
        return None
    if visible_name.endswith("Warp") and " " not in visible_name:
        return None
    if visible_name.islower() and " " not in visible_name:
        return None
    return Page(
        id=stable_id(file, "npc_name", line_index, full_name),
        file=file,
        kind="npc_name",
        start_line=line_index,
        end_line=line_index,
        speaker="",
        text=visible_name,
        lines=[SourceLine(line_index, "npc_name", full_name)],
    )


def iter_files(npc_root: Path, files: list[str] | None, dirs: list[str] | None) -> list[Path]:
    if files:
        return [npc_root / value for value in files]
    roots = [npc_root / value for value in dirs] if dirs else [npc_root]
    paths: list[Path] = []
    for base in roots:
        if base.is_file():
            paths.append(base)
            continue
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.txt")):
            rel_parts = set(path.relative_to(npc_root).parts)
            if rel_parts & SKIP_DIRS:
                continue
            paths.append(path)
    return sorted(set(paths))


def stable_id(file: str, kind: str, start_line: int, text: str) -> str:
    raw = f"{file}\0{kind}\0{start_line}\0{text}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def make_dialogue_page(file: str, buffer: list[SourceLine]) -> Page | None:
    if not buffer or not any(should_translate(line.original) for line in buffer):
        return None
    speaker = ""
    text_parts: list[str] = []
    for index, line in enumerate(buffer):
        match = BRACKET_NAME_RE.fullmatch(line.original.strip())
        if index == 0 and match:
            speaker = match.group(1)
        else:
            text_parts.append(line.original.strip())
    merged = " ".join(part for part in text_parts if part)
    page_text = f"[{speaker}] {merged}" if speaker else merged
    return Page(
        id=stable_id(file, "dialogue", buffer[0].line_index, page_text),
        file=file,
        kind="dialogue",
        start_line=buffer[0].line_index,
        end_line=buffer[-1].line_index,
        speaker=speaker,
        text=merged,
        lines=list(buffer),
    )


def make_single_page(file: str, kind: str, line_index: int, original: str) -> Page | None:
    if not should_translate(original):
        return None
    return Page(
        id=stable_id(file, kind, line_index, original),
        file=file,
        kind=kind,
        start_line=line_index,
        end_line=line_index,
        speaker="",
        text=original,
        lines=[SourceLine(line_index, kind, original)],
    )


def extract_file(npc_root: Path, path: Path, include_npc_names: bool = False) -> list[Page]:
    rel = path.relative_to(npc_root).as_posix()
    lines = read_text(path).splitlines()
    pages: list[Page] = []
    buffer: list[SourceLine] = []

    def flush_dialogue() -> None:
        nonlocal buffer
        page = make_dialogue_page(rel, buffer)
        if page:
            pages.append(page)
        buffer = []

    for line_index, line in enumerate(lines):
        if line.lstrip().startswith("//"):
            continue
        if include_npc_names:
            script_match = SCRIPT_DEF_RE.match(line)
            duplicate_match = DUPLICATE_DEF_RE.match(line)
            if script_match or duplicate_match:
                match = script_match or duplicate_match
                page = make_npc_name_page(rel, line_index, match.group("name"))
                if page:
                    pages.append(page)
        mes_match = MES_RE.match(line)
        caption_match = CAPTION_RE.match(line)
        if mes_match or caption_match:
            match = mes_match or caption_match
            kind = "mes" if mes_match else "caption"
            buffer.append(SourceLine(line_index, kind, lua_unescape(match.group(2))))
            continue
        flush_dialogue()
        select_match = SELECT_RE.search(line)
        if select_match:
            page = make_single_page(rel, "select", line_index, lua_unescape(select_match.group(2)))
            if page:
                pages.append(page)
        npctalk_match = NPCTALK_RE.search(line)
        if npctalk_match:
            page = make_single_page(rel, "npctalk", line_index, lua_unescape(npctalk_match.group(2)))
            if page:
                pages.append(page)
        announce_match = ANNOUNCE_RE.search(line)
        if announce_match:
            page = make_single_page(rel, "announce", line_index, lua_unescape(announce_match.group(2)))
            if page:
                pages.append(page)
    flush_dialogue()
    return pages


def extract_pages(npc_root: Path, paths: list[Path], limit_pages: int | None = None, include_npc_names: bool = False) -> list[Page]:
    pages: list[Page] = []
    for path in paths:
        if path.exists():
            pages.extend(extract_file(npc_root, path, include_npc_names=include_npc_names))
        if limit_pages and len(pages) >= limit_pages:
            return pages[:limit_pages]
    return pages


def page_to_payload(page: Page) -> dict:
    payload = asdict(page)
    payload["lines"] = [asdict(line) for line in page.lines]
    return payload


def save_pages(pages: list[Page], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"pages": [page_to_payload(page) for page in pages]}, ensure_ascii=False, indent=2), encoding="utf-8")


def load_pages(path: Path) -> list[Page]:
    data = json.loads(path.read_text(encoding="utf-8"))
    pages = []
    for row in data.get("pages", []):
        lines = [SourceLine(**line) for line in row["lines"]]
        payload = dict(row)
        payload["lines"] = lines
        pages.append(Page(**payload))
    return pages


def pack_batches(pages: list[Page], max_chars: int) -> list[Batch]:
    batches: list[Batch] = []
    current: list[Page] = []
    current_chars = 0

    def flush() -> None:
        nonlocal current, current_chars
        if not current:
            return
        digest = hashlib.sha1("\n".join(page.id for page in current).encode()).hexdigest()[:16]
        batches.append(Batch(f"{len(batches):05d}-{digest}", current))
        current = []
        current_chars = 0

    for page in pages:
        estimate = len(page.text) + len(page.speaker) + 120
        if current and current_chars + estimate > max_chars:
            flush()
        current.append(page)
        current_chars += estimate
    flush()
    return batches


def build_prompt(line_width: int) -> str:
    return f"""You are localizing Ragnarok Online NPC dialogue to Simplified Chinese.

Return strict JSON only.
Rules:
- Preserve page ids exactly.
- Preserve color codes like ^RRGGBB, script variables, item constants, map names, and numbers.
- For dialogue pages, translate the full page naturally as one paragraph; do not keep awkward English line breaks.
- For speaker names, translate the visible name without brackets.
- For npc_name pages, translate only the visible hover/display name; do not include hidden suffixes such as #name or ::alias.
- For select pages, return the same number of options in the same order.
- Use GBK-compatible Simplified Chinese.
- Keep translated dialogue concise enough to reflow at roughly {line_width} display columns.
- Do not add explanations or markdown.

Output schema:
{{"pages":[{{"id":"...","speaker":"translated speaker or empty","text":"translated paragraph","options":["..."]}}]}}
"""


def parse_translation_response(response: str) -> dict[str, dict]:
    data = json.loads(response)
    rows = data.get("pages")
    if not isinstance(rows, list):
        raise ValueError("response does not contain pages array")
    result = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            result[row["id"]] = row
    return result


def translate_batch(batch: Batch, model: str, api_key: str, base_url: str, limiter: RateLimiter, line_width: int) -> dict[str, dict]:
    payload = {
        "pages": [
            {
                "id": page.id,
                "kind": page.kind,
                "speaker": page.speaker,
                "text": page.text,
                "options": page.text.split(":") if page.kind == "select" else [],
            }
            for page in batch.pages
        ]
    }
    messages = [
        {"role": "system", "content": build_prompt(line_width)},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    limiter.acquire()
    return parse_translation_response(call_openai_json(messages, model, api_key, base_url))


def display_width(text: str) -> int:
    width = 0
    index = 0
    while index < len(text):
        color = COLOR_RE.match(text, index)
        if color:
            index = color.end()
            continue
        char = text[index]
        width += 2 if "\u4e00" <= char <= "\u9fff" else 1
        index += 1
    return width


def reflow_text(text: str, width: int) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return [""]
    token_re = re.compile(
        r"<NAVI>.*?</NAVI>|<INFO>.*?</INFO>|<[^>]*>|\^[0-9A-Fa-f]{6}|[A-Za-z0-9_+~'./-]+|"
        rf"[{re.escape(BREAK_PUNCTUATION)}]+|\s+|."
    )
    lines: list[str] = []
    current = ""

    def append_current() -> None:
        nonlocal current
        if current.strip():
            lines.append(current.rstrip())
        current = ""

    def last_break_position(value: str) -> int | None:
        result = None
        for match in re.finditer(rf"[{re.escape(BREAK_PUNCTUATION)}]\s*", value):
            result = match.end()
        return result

    for match in token_re.finditer(text):
        token = match.group(0)
        token_width = 0 if COLOR_RE.fullmatch(token) else display_width(token)
        if current and display_width(current) + token_width > width and not token.isspace():
            break_position = last_break_position(current)
            if break_position and display_width(current[:break_position]) >= max(8, min(10, width // 4)):
                lines.append(current[:break_position].rstrip())
                current = current[break_position:].lstrip()
            if current and display_width(current) + token_width > width:
                append_current()
        if not current and token.isspace():
            continue
        current += token
    if current.strip():
        lines.append(current.rstrip())
    lines = merge_short_final_line(lines, width)
    return lines or [text]


def merge_short_final_line(lines: list[str], width: int, min_width: int = 14) -> list[str]:
    if len(lines) < 2:
        return lines
    target_width = min(min_width, max(1, width // 2))
    if display_width(lines[-1]) >= target_width:
        return lines
    previous = lines[-2]
    merged = f"{lines[-2]}{lines[-1]}"
    if display_width(merged) <= width and "<NAVI>" not in merged and "<INFO>" not in merged:
        return [*lines[:-2], merged]
    for match in reversed(list(re.finditer(rf"[{re.escape(BREAK_PUNCTUATION)}]\s*", previous))):
        split_at = match.end()
        if split_at >= len(previous):
            continue
        moved = previous[split_at:].lstrip()
        rebalanced = f"{moved}{lines[-1]}"
        if display_width(rebalanced) >= target_width and display_width(rebalanced) <= width:
            return [*lines[:-2], previous[:split_at].rstrip(), rebalanced]
    if "<NAVI>" not in merged and "<INFO>" not in merged:
        split_token_re = re.compile(
            r"<[^>]*>|\^[0-9A-Fa-f]{6}|[A-Za-z0-9_+~'./-]+|"
            rf"[{re.escape(BREAK_PUNCTUATION)}]+|\s+|."
        )
        split_positions = [match.start() for match in split_token_re.finditer(previous) if not match.group(0).isspace()]
        for split_at in reversed(split_positions):
            if split_at <= 0:
                continue
            moved = previous[split_at:].lstrip()
            rebalanced = f"{moved}{lines[-1]}"
            left = previous[:split_at].rstrip()
            if (
                display_width(left) >= min(16, width // 2)
                and display_width(rebalanced) >= target_width
                and display_width(rebalanced) <= width
            ):
                return [*lines[:-2], left, rebalanced]
    return lines


def extract_tokens(text: str) -> dict[str, list[str]]:
    return {
        "colors": [color.lower() for color in COLOR_RE.findall(text)],
        "script": SCRIPT_TOKEN_RE.findall(text),
    }


def gbk_ok(text: str) -> bool:
    try:
        text.encode("gbk")
        return True
    except UnicodeEncodeError:
        return False


def qa_pages(pages: list[Page], translations: dict[str, dict], line_width: int) -> dict:
    issues = []
    warnings = []
    for page in pages:
        row = translations.get(page.id)
        if not row:
            issues.append({"id": page.id, "file": page.file, "line": page.start_line + 1, "issue": "missing translation"})
            continue
        translated_text = row.get("text", "")
        translated_speaker = row.get("speaker", "")
        if page.kind == "select":
            options = row.get("options")
            if not isinstance(options, list):
                issues.append({"id": page.id, "file": page.file, "line": page.start_line + 1, "issue": "missing select options"})
            elif len(options) != len(page.text.split(":")):
                issues.append({"id": page.id, "file": page.file, "line": page.start_line + 1, "issue": "select option count mismatch"})
            translated_text = ":".join(str(option) for option in options or [])
        elif page.kind == "npc_name":
            if any(separator in translated_text for separator in ("#", "::")):
                issues.append({"id": page.id, "file": page.file, "line": page.start_line + 1, "issue": "npc name contains hidden suffix", "text": translated_text})
        original_tokens = extract_tokens(page.text)
        translated_tokens = extract_tokens(translated_text)
        if original_tokens["colors"] != translated_tokens["colors"]:
            issues.append({"id": page.id, "file": page.file, "line": page.start_line + 1, "issue": "color code mismatch"})
        missing_script = [token for token in original_tokens["script"] if token not in translated_text]
        if missing_script:
            issues.append({"id": page.id, "file": page.file, "line": page.start_line + 1, "issue": "script token missing", "tokens": missing_script})
        if not gbk_ok(translated_text) or not gbk_ok(translated_speaker):
            issues.append({"id": page.id, "file": page.file, "line": page.start_line + 1, "issue": "not GBK encodable"})
        if page.kind == "dialogue":
            for line in reflow_text(translated_text, line_width):
                if display_width(line) > line_width:
                    if "<NAVI>" in line or "<INFO>" in line:
                        warnings.append(
                            {
                                "id": page.id,
                                "file": page.file,
                                "line": page.start_line + 1,
                                "warning": "navigation tag kept unsplit despite width",
                                "text": line,
                            }
                        )
                    else:
                        issues.append({"id": page.id, "file": page.file, "line": page.start_line + 1, "issue": "reflow line too wide", "text": line})
        if EN_WORD_RE.search(translated_text) and not any(token in translated_text for token in original_tokens["script"]):
            warnings.append({"id": page.id, "file": page.file, "line": page.start_line + 1, "warning": "translated text still contains ASCII word", "text": translated_text})
    return {"issue_count": len(issues), "warning_count": len(warnings), "issues": issues, "warnings": warnings[:200]}


def load_translations(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["id"]: row for row in data.get("pages", [])}


def save_translations(rows: Iterable[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"pages": list(rows)}, ensure_ascii=False, indent=2), encoding="utf-8")


def mock_translation(page: Page) -> dict:
    speaker_map = {
        "Kafra Employee": "卡普拉职员",
        "Airship Crew": "飞艇乘务员",
    }
    text_map = {
        "Welcome to the Kafra Corporation. Here, let me open your Storage for you.": "欢迎来到卡普拉公司。现在，我来为你打开仓库。",
        "Welcome~! The Kafra Services are always on your side. So how can I help you?": "欢迎！卡普拉服务永远与你同在。请问需要什么帮助？",
        "If we've landed at your destination and you'd like to leave the Airship, please use the stairs up ahead. Thank you for your patronage.": "如果飞艇已经抵达你的目的地，而你想要下船，请使用前方的楼梯。感谢你的惠顾。",
    }
    option_map = {
        "Save": "保存",
        "Use Storage": "使用仓库",
        "Rent a Pushcart": "租用手推车",
        "Cancel": "取消",
    }
    if page.kind == "select":
        return {"id": page.id, "speaker": "", "text": "", "options": [option_map.get(option, option) for option in page.text.split(":")]}
    return {
        "id": page.id,
        "speaker": speaker_map.get(page.speaker, page.speaker),
        "text": text_map.get(page.text, f"测试译文：{page.text}"),
        "options": [],
    }


def apply_translations(npc_root: Path, pages: list[Page], translations: dict[str, dict], output_root: Path | None, line_width: int, dry_run: bool) -> dict:
    by_file: dict[str, list[Page]] = {}
    for page in pages:
        if page.id in translations:
            by_file.setdefault(page.file, []).append(page)
    stats = {"files": 0, "pages": 0, "dry_run": dry_run, "output_root": str(output_root) if output_root else None}
    previews = []
    for rel, file_pages in sorted(by_file.items()):
        source_path = npc_root / rel
        lines = read_text(source_path).splitlines()
        changed = False
        npc_name_replacements = {}
        for page in file_pages:
            if page.kind != "npc_name" or not page.lines:
                continue
            row = translations.get(page.id, {})
            translated_name = str(row.get("text", "")).strip()
            if not translated_name:
                continue
            original_full_name = page.lines[0].original
            _, suffix = split_npc_name(original_full_name)
            npc_name_replacements[original_full_name] = translated_name + suffix
        for page in sorted(file_pages, key=lambda item: item.start_line, reverse=True):
            row = translations[page.id]
            if page.kind == "npc_name":
                if not page.lines:
                    continue
                original_full_name = page.lines[0].original
                new_full_name = npc_name_replacements.get(original_full_name)
                if not new_full_name:
                    continue
                line = lines[page.start_line]
                name_match = SCRIPT_DEF_RE.match(line) or DUPLICATE_DEF_RE.match(line)
                if name_match and name_match.group("name") == original_full_name:
                    new_line = f'{name_match.group("prefix")}{new_full_name}{name_match.group("rest")}'
                else:
                    new_line = line.replace(original_full_name, new_full_name, 1)
                if new_line != line:
                    lines[page.start_line] = new_line
                    previews.append({"file": rel, "line": page.start_line + 1, "old": [line], "new": [new_line]})
                    changed = True
                    stats["pages"] += 1
            elif page.kind == "dialogue":
                speaker = str(row.get("speaker", page.speaker or ""))
                text = str(row.get("text", ""))
                new_lines = []
                indent = re.match(r"^(\s*)", lines[page.start_line]).group(1)
                if page.speaker:
                    new_lines.append(f'{indent}mes "{lua_escape("[" + speaker + "]")}";')
                if text.strip():
                    for chunk in reflow_text(text, line_width):
                        new_lines.append(f'{indent}mes "{lua_escape(chunk)}";')
                if not new_lines:
                    continue
                old_preview = lines[page.start_line : page.end_line + 1]
                lines[page.start_line : page.end_line + 1] = new_lines
                previews.append({"file": rel, "line": page.start_line + 1, "old": old_preview, "new": new_lines})
                changed = True
                stats["pages"] += 1
            elif page.kind == "select":
                options = row.get("options", [])
                if not isinstance(options, list):
                    continue
                line = lines[page.start_line]
                new_value = lua_escape(":".join(str(option) for option in options))
                lines[page.start_line] = SELECT_RE.sub(lambda m: m.group(1) + new_value + m.group(3), line, count=1)
                previews.append({"file": rel, "line": page.start_line + 1, "old": [line], "new": [lines[page.start_line]]})
                changed = True
                stats["pages"] += 1
            else:
                line = lines[page.start_line]
                text = lua_escape(str(row.get("text", "")))
                regex = NPCTALK_RE if page.kind == "npctalk" else ANNOUNCE_RE
                lines[page.start_line] = regex.sub(lambda m: m.group(1) + text + m.group(3), line, count=1)
                previews.append({"file": rel, "line": page.start_line + 1, "old": [line], "new": [lines[page.start_line]]})
                changed = True
                stats["pages"] += 1
        if changed:
            stats["files"] += 1
            if not dry_run:
                target = (output_root / rel) if output_root else source_path
                write_gbk(target, "\n".join(lines) + "\n")
    stats["previews"] = previews[:50]
    return stats


def command_extract(args: argparse.Namespace) -> None:
    npc_root = Path(args.npc_root)
    paths = iter_files(npc_root, args.file, args.dir)
    pages = extract_pages(npc_root, paths, args.limit_pages, include_npc_names=args.include_npc_names)
    save_pages(pages, Path(args.output))
    by_kind: dict[str, int] = {}
    by_file: dict[str, int] = {}
    for page in pages:
        by_kind[page.kind] = by_kind.get(page.kind, 0) + 1
        by_file[page.file] = by_file.get(page.file, 0) + 1
    print(json.dumps({"pages": len(pages), "by_kind": by_kind, "top_files": sorted(by_file.items(), key=lambda row: row[1], reverse=True)[:20], "output": args.output}, ensure_ascii=False, indent=2))


def command_mock(args: argparse.Namespace) -> None:
    pages = load_pages(Path(args.pages))
    save_translations((mock_translation(page) for page in pages), Path(args.output))
    print(json.dumps({"pages": len(pages), "output": args.output}, ensure_ascii=False, indent=2))


def command_translate(args: argparse.Namespace) -> None:
    load_api_config()
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")
    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    pages = load_pages(Path(args.pages))
    if args.limit_pages:
        pages = pages[: args.limit_pages]
    batches = pack_batches(pages, args.max_chars)
    limiter = RateLimiter(args.rpm)
    translations: dict[str, dict] = {}
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(translate_batch, batch, model, api_key, base_url, limiter, args.line_width): batch for batch in batches}
        for future in as_completed(futures):
            batch = futures[future]
            try:
                translations.update(future.result())
                print(f"[ok] {batch.batch_id} pages={len(batch.pages)}")
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{batch.batch_id}: {exc}")
                print(f"[fail] {batch.batch_id}: {exc}")
    rows = [translations[page.id] for page in pages if page.id in translations]
    save_translations(rows, Path(args.output))
    print(json.dumps({"pages": len(rows), "failures": failures, "output": args.output}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


def command_qa(args: argparse.Namespace) -> None:
    pages = load_pages(Path(args.pages))
    translations = load_translations(Path(args.translations))
    report = qa_pages(pages, translations, args.line_width)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"issue_count": report["issue_count"], "warning_count": report["warning_count"], "output": str(output)}, ensure_ascii=False, indent=2))
    if report["issue_count"]:
        raise SystemExit(1)


def command_apply(args: argparse.Namespace) -> None:
    pages = load_pages(Path(args.pages))
    translations = load_translations(Path(args.translations))
    stats = apply_translations(Path(args.npc_root), pages, translations, Path(args.output_root) if args.output_root else None, args.line_width, args.dry_run)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser("extract")
    extract.add_argument("--npc-root", default=str(DEFAULT_NPC_ROOT))
    extract.add_argument("--file", action="append", help="NPC-root-relative file")
    extract.add_argument("--dir", action="append", help="NPC-root-relative directory")
    extract.add_argument("--limit-pages", type=int)
    extract.add_argument("--include-npc-names", action="store_true", help="also extract NPC script/duplicate display names for hover-name localization")
    extract.add_argument("--output", default=str(PAGES_FILE))

    mock = sub.add_parser("mock")
    mock.add_argument("--pages", default=str(PAGES_FILE))
    mock.add_argument("--output", default=str(TRANSLATIONS_FILE))

    translate = sub.add_parser("translate")
    translate.add_argument("--pages", default=str(PAGES_FILE))
    translate.add_argument("--output", default=str(TRANSLATIONS_FILE))
    translate.add_argument("--line-width", type=int, default=52)
    translate.add_argument("--max-chars", type=int, default=5000)
    translate.add_argument("--workers", type=int, default=4)
    translate.add_argument("--rpm", type=int, default=120)
    translate.add_argument("--limit-pages", type=int)

    qa = sub.add_parser("qa")
    qa.add_argument("--pages", default=str(PAGES_FILE))
    qa.add_argument("--translations", default=str(TRANSLATIONS_FILE))
    qa.add_argument("--line-width", type=int, default=52)
    qa.add_argument("--output", default=str(QA_FILE))

    apply = sub.add_parser("apply")
    apply.add_argument("--npc-root", default=str(DEFAULT_NPC_ROOT))
    apply.add_argument("--pages", default=str(PAGES_FILE))
    apply.add_argument("--translations", default=str(TRANSLATIONS_FILE))
    apply.add_argument("--line-width", type=int, default=52)
    apply.add_argument("--output-root", help="write translated files under this root instead of in-place")
    apply.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    started = time.time()
    if args.command == "extract":
        command_extract(args)
    elif args.command == "mock":
        command_mock(args)
    elif args.command == "translate":
        command_translate(args)
    elif args.command == "qa":
        command_qa(args)
    elif args.command == "apply":
        command_apply(args)
    _ = started


if __name__ == "__main__":
    main()
