#!/usr/bin/env python3
"""Classify remaining untranslated client strings after safe extraction."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

import translate_client_core as core  # noqa: E402


TEXT_EXTS = {".txt", ".xml", ".lua", ".lub"}
LOW_VALUE_BOOK_RE = re.compile(r"^data\\book\\1000(?:89[7-9]|9(?:0[0-9]|1[0-9]|20))\.txt$", re.IGNORECASE)
ASCII_RESOURCE_RE = re.compile(r"^[A-Za-z0-9_./\\:-]+\.(?:wav|bmp|jpg|tga|spr|act|rsw|gat|gnd|lua|lub)$", re.IGNORECASE)
PATH_OR_MODULE_RE = re.compile(r"^(?:System|SystemEN|data|LuaFiles514|tbl_|itemInfo|[A-Za-z0-9_./\\:-]+)$")
URL_RE = re.compile(r"^(?:https?://|www\.)", re.IGNORECASE)
ORDINAL_RE = re.compile(r"^\d+(?:st|nd|rd|th)$", re.IGNORECASE)
STAT_FORMULA_RE = re.compile(r"^(?:[A-Z]{2,5}\s*[+-]\d+[，,]?\s*)+\.?$")
MOJIBAKE_MARKERS = set("?㊣﹞～赤迄車芍邦谷豕足那¯℅∫")
CONFIG_VALUE_FILES = (
    r"clientinfo.xml",
    r"sclientinfo.xml",
    r"service_korea\externalsettings_kr.lub",
    r"service_korea\externalsettings_kr_qm.lub",
    r"service_korea\externalsettings_kr_sak.lub",
    r"service_korea\externalsettings_kr_sak_qm.lub",
)
INTERNAL_HELPER_SUFFIXES = (
    "_f.lua",
    "_f.lub",
    r"skillinfoz\test.lub",
    r"skillinfoz\jobinheritlist.lub",
    r"stateicon\efstids.lub",
)


def read_bytes_if_text(path: Path) -> bytes | None:
    raw = path.read_bytes()
    if b"\0" in raw[:200000]:
        return None
    return raw


def candidate_files(client_dir: Path) -> list[Path]:
    bases = [
        client_dir / "data",
        client_dir / "System",
        client_dir / "SystemEN",
        client_dir / "data" / "luafiles514" / "lua files",
        client_dir / "System" / "LuaFiles514",
        client_dir / "SystemEN" / "LuaFiles514",
    ]
    paths: set[Path] = set()
    for base in bases:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_EXTS and read_bytes_if_text(path) is not None:
                paths.add(path)
    return sorted(paths)


def mojibake_score(text: str) -> float:
    stripped = text.strip()
    if not stripped:
        return 0.0
    marked = sum(1 for char in stripped if char in MOJIBAKE_MARKERS)
    replacement = stripped.count("?")
    return (marked + replacement) / max(len(stripped), 1)


def mostly_names_or_symbols(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if len(stripped) > 60 and "," in stripped:
        alpha = sum(1 for char in stripped if char.isascii() and char.isalpha())
        separators = sum(1 for char in stripped if char in ",*[]()_-+:/ .")
        return alpha + separators > len(stripped) * 0.55
    return False


def classify(item: core.ClientItem) -> tuple[str, str]:
    rel = item.file
    rel_lower = rel.lower()
    text = item.original.strip()

    if rel_lower.endswith(CONFIG_VALUE_FILES):
        return "ignored_config_value", "Client/service configuration value."
    if rel_lower.endswith("iteminfo_c.lua"):
        return "ignored_template_comment", "Custom item template comment."
    if rel_lower.endswith("accname_eng.lub"):
        return "ignored_internal_helper", "Accessory ID helper table."
    if text == "iRO Wiki":
        return "ignored_proper_noun", "Source/proper-name attribution."
    if STAT_FORMULA_RE.match(text):
        return "ignored_formula", "Already-localized stat formula."
    if text.strip('"').endswith("？") and len(text) <= 32:
        return "ignored_proper_noun", "Proper-name title already has localized punctuation."
    if URL_RE.match(text):
        return "ignored_url", "URL or website value."
    if ASCII_RESOURCE_RE.match(text) or "\\" in text or "/" in text:
        return "ignored_internal_resource", "Path or resource filename."
    if rel_lower.endswith(INTERNAL_HELPER_SUFFIXES):
        return "ignored_internal_helper", "Lua helper/debug/template file."
    if LOW_VALUE_BOOK_RE.match(rel):
        return "ignored_low_value_book_credits", "Korean anniversary/player-name book pages; mostly names or mojibake."
    if rel_lower.endswith("skilltreeview.lub") and ORDINAL_RE.match(text):
        return "ignored_ui_ordinal", "Skill tree ordinal label."
    if rel_lower.endswith("iteminfo.lua") and PATH_OR_MODULE_RE.match(text):
        return "ignored_internal_loader", "Lua loader/module path."
    if mojibake_score(text) >= 0.20:
        return "ignored_mojibake", "High mojibake marker density; unsafe to machine-translate."
    if mostly_names_or_symbols(text):
        return "ignored_name_list", "Mostly player names, handles, or symbolic list data."
    if len(text) <= 3 and not any(char.isalpha() for char in text):
        return "ignored_too_short", "Too short or symbolic."
    return "actionable", "Readable UI text candidate."


def build_report(client_dir: Path) -> dict:
    memory = core.load_memory()
    by_category: dict[str, list[dict]] = defaultdict(list)
    category_counts: Counter[str] = Counter()
    by_file: Counter[str] = Counter()
    total_items = 0

    for path in candidate_files(client_dir):
        try:
            items = core.extract_file(client_dir, path)
        except Exception as exc:
            by_category["extract_error"].append({"file": str(path), "error": str(exc)})
            continue
        for item in items:
            if item.original in memory:
                continue
            total_items += 1
            category, reason = classify(item)
            category_counts[category] += 1
            by_file[item.file] += 1
            bucket = by_category[category]
            if len(bucket) < 200:
                bucket.append(
                    {
                        "file": item.file,
                        "line": item.line_index + 1,
                        "kind": item.kind,
                        "text": item.original,
                        "reason": reason,
                    }
                )

    return {
        "client_dir": str(client_dir),
        "pending_items": total_items,
        "categories": dict(sorted(category_counts.items())),
        "top_pending_files": by_file.most_common(80),
        "samples": dict(sorted(by_category.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-dir", default=r"D:\rag")
    parser.add_argument("--output", default=str(Path("tmp") / "client_pending_classified.json"))
    parser.add_argument("--fail-on-actionable", action="store_true")
    args = parser.parse_args()

    report = build_report(Path(args.client_dir))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "pending_items": report["pending_items"],
        "categories": report["categories"],
        "output": str(output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if args.fail_on_actionable and report["categories"].get("actionable", 0) else 0


if __name__ == "__main__":
    sys.exit(main())
