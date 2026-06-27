#!/usr/bin/env python3
"""
NPC Translation Text Extractor
===============================
Scans rAthena NPC files and extracts untranslated mes/select/caption text
into structured JSON task files for AI translation.

Usage:
    python tools/ai_translate/extract.py [--dir quests] [--output tmp/ai_translate/tasks/]
    python tools/ai_translate/extract.py --all
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Add parent tools dir to path for importing npc_cn_translate parser
TOOLS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))
from npc_cn_translate import parse_blocks, NPC_SCRIPT_RE, read_npc_file

# ─── Configuration ──────────────────────────────────────────────────────────

RATHENA_ROOT = Path(__file__).resolve().parent.parent.parent
RATHENA_NPC = RATHENA_ROOT / "npc"
DEFAULT_OUTPUT = RATHENA_ROOT / "tmp" / "ai_translate" / "tasks"

# Directories that contain no translatable dialogue
SKIP_DIRS = {"mapflag", "warps", "mobs", "test"}

# All translatable directories (relative to npc/)
TRANSLATABLE_DIRS = [
    "cities", "airports", "battleground", "events", "guild", "guild2",
    "instances", "jobs", "kafras", "merchants", "other", "quests", "custom",
    "pre-re", "re",
]

# Chinese character range for detecting already-translated text
CN_CHAR_RE = re.compile(r'[\u4e00-\u9fff]')


def has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(CN_CHAR_RE.search(text))


def is_file_translated(filepath: Path) -> bool:
    """Check if a file already contains Chinese characters."""
    try:
        content = read_npc_file(filepath)
        return has_chinese(content)
    except Exception:
        return False


def extract_npc_name(header_line: str) -> str:
    """Extract display name from NPC header line."""
    m = NPC_SCRIPT_RE.match(header_line)
    if m:
        full_name = m.group(1)
        # Remove ::label and #id parts for display
        name = full_name.split('::')[0]
        name = name.split('#')[0]
        return name
    return ""


def extract_file(filepath: Path, npc_dir: Path, skip_translated: bool = True) -> dict:
    """Extract untranslated text from a single NPC file.

    Returns a task dict or None if nothing to translate.
    """
    rel_path = filepath.relative_to(npc_dir).as_posix()

    # Skip already-translated files if requested
    if skip_translated and is_file_translated(filepath):
        return None

    content = read_npc_file(filepath)
    blocks = parse_blocks(content)
    lines = content.splitlines()

    if not blocks:
        return None

    npc_blocks = []
    for blk in blocks:
        # Skip blocks with no translatable text
        if not blk.mes_list and not blk.select_list and not blk.caption_list:
            continue

        # Check if block already has Chinese text
        all_texts = blk.mes_list + blk.select_list + blk.caption_list
        if skip_translated and any(has_chinese(t) for t in all_texts):
            continue

        # Extract NPC name from header line
        npc_name = extract_npc_name(lines[blk.start]) if blk.start < len(lines) else ""

        texts = []
        for i, mes in enumerate(blk.mes_list):
            if mes.strip():  # Skip empty mes
                texts.append({
                    "type": "mes",
                    "index": i,
                    "original": mes,
                })
        for i, sel in enumerate(blk.select_list):
            if sel.strip():
                texts.append({
                    "type": "select",
                    "index": i,
                    "original": sel,
                })
        for i, cap in enumerate(blk.caption_list):
            if cap.strip():
                texts.append({
                    "type": "caption",
                    "index": i,
                    "original": cap,
                })

        if texts:
            npc_blocks.append({
                "npc_label": blk.ident,
                "npc_name": npc_name,
                "block_index": blk.pos_idx,
                "line_start": blk.start + 1,  # 1-based
                "line_end": blk.end + 1,
                "texts": texts,
            })

    if not npc_blocks:
        return None

    total_texts = sum(len(b["texts"]) for b in npc_blocks)
    return {
        "source_file": rel_path,
        "total_blocks": len(npc_blocks),
        "total_texts": total_texts,
        "npc_blocks": npc_blocks,
    }


def extract_directory(dir_name: str, npc_dir: Path, output_dir: Path,
                      skip_translated: bool = True) -> dict:
    """Extract all untranslated text from a directory.

    Returns stats dict.
    """
    target_dir = npc_dir / dir_name
    if not target_dir.exists():
        return {"dir": dir_name, "files_scanned": 0, "files_with_text": 0,
                "total_texts": 0, "skipped_translated": 0}

    tasks = []
    files_scanned = 0
    skipped = 0

    for filepath in sorted(target_dir.rglob("*.txt")):
        # Skip files in SKIP_DIRS subdirectories
        rel_parts = filepath.relative_to(npc_dir).parts
        if any(p in SKIP_DIRS for p in rel_parts):
            continue

        files_scanned += 1
        task = extract_file(filepath, npc_dir, skip_translated)
        if task is None:
            if is_file_translated(filepath):
                skipped += 1
            continue
        tasks.append(task)

    if not tasks:
        return {"dir": dir_name, "files_scanned": files_scanned,
                "files_with_text": 0, "total_texts": 0,
                "skipped_translated": skipped}

    # Write task file
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{dir_name.replace('/', '_')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    total_texts = sum(t["total_texts"] for t in tasks)
    print(f"  [{dir_name}] {len(tasks)} files, {total_texts} texts -> {output_file.name}")

    return {
        "dir": dir_name,
        "files_scanned": files_scanned,
        "files_with_text": len(tasks),
        "total_texts": total_texts,
        "skipped_translated": skipped,
        "output_file": str(output_file),
    }


def main():
    parser = argparse.ArgumentParser(description="Extract untranslated NPC text")
    parser.add_argument("--dir", type=str, default=None,
                        help="Specific directory to extract (e.g., quests, jobs)")
    parser.add_argument("--all", action="store_true",
                        help="Extract all translatable directories")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT),
                        help="Output directory for task JSON files")
    parser.add_argument("--include-translated", action="store_true",
                        help="Include files that already contain Chinese text")
    args = parser.parse_args()

    npc_dir = RATHENA_NPC
    output_dir = Path(args.output)
    skip_translated = not args.include_translated

    if not npc_dir.exists():
        print(f"ERROR: NPC directory not found: {npc_dir}")
        sys.exit(1)

    print(f"NPC Translation Text Extractor")
    print(f"  NPC dir:    {npc_dir}")
    print(f"  Output:     {output_dir}")
    print(f"  Skip translated: {skip_translated}")
    print()

    # Determine which directories to process
    if args.dir:
        dirs = [args.dir]
    elif args.all:
        dirs = TRANSLATABLE_DIRS
    else:
        print("ERROR: Specify --dir <name> or --all")
        sys.exit(1)

    all_stats = []
    for d in dirs:
        stats = extract_directory(d, npc_dir, output_dir, skip_translated)
        all_stats.append(stats)

    # Summary
    print()
    print("=== Extraction Summary ===")
    total_files = sum(s["files_with_text"] for s in all_stats)
    total_texts = sum(s["total_texts"] for s in all_stats)
    total_scanned = sum(s["files_scanned"] for s in all_stats)
    total_skipped = sum(s["skipped_translated"] for s in all_stats)
    print(f"  Directories:     {len(dirs)}")
    print(f"  Files scanned:   {total_scanned}")
    print(f"  Files to translate: {total_files}")
    print(f"  Texts to translate: {total_texts}")
    print(f"  Already translated: {total_skipped}")

    # Write summary
    summary_file = output_dir / "_summary.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_files": total_files,
            "total_texts": total_texts,
            "total_scanned": total_scanned,
            "skipped_translated": total_skipped,
            "directories": all_stats,
        }, f, ensure_ascii=False, indent=2)
    print(f"  Summary: {summary_file}")


if __name__ == '__main__':
    main()
