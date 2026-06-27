#!/usr/bin/env python3
"""
NPC Translation Applier
========================
Applies AI-translated text back into NPC source files, preserving all
structural content and outputting GBK-encoded files.

Usage:
    python tools/ai_translate/apply.py --input tmp/ai_translate/results/quests.json
    python tools/ai_translate/apply.py --input tmp/ai_translate/results/quests.json --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent tools dir to path
TOOLS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))
from npc_cn_translate import (
    parse_blocks, MES_RE, SELECT_RE, CAPTION_RE, write_gbk,
    read_npc_file, backup_file
)

# ─── Configuration ──────────────────────────────────────────────────────────

RATHENA_ROOT = Path(__file__).resolve().parent.parent.parent
RATHENA_NPC = RATHENA_ROOT / "npc"
BACKUP_DIR = RATHENA_ROOT / "npc_backup_en"


def apply_translations(content: str, npc_blocks_data: list) -> tuple:
    """Apply translated texts to NPC file content.

    Args:
        content: Original file content (string)
        npc_blocks_data: List of block dicts from translation result JSON

    Returns:
        (translated_content, stats_dict)
    """
    lines = content.splitlines(keepends=False)
    parsed_blocks = parse_blocks(content)

    stats = {
        'blocks_matched': 0,
        'mes_replaced': 0,
        'select_replaced': 0,
        'caption_replaced': 0,
        'blocks_skipped': 0,
    }

    # Build lookup from translation data
    label_map = {}  # ::label -> block_data
    index_map = {}  # block_index -> block_data
    for blk_data in npc_blocks_data:
        if blk_data.get("npc_label"):
            label_map[blk_data["npc_label"]] = blk_data
        else:
            index_map[blk_data["block_index"]] = blk_data

    result = list(lines)

    for parsed_blk in parsed_blocks:
        # Find matching translation data
        blk_data = None
        if parsed_blk.ident and parsed_blk.ident in label_map:
            blk_data = label_map[parsed_blk.ident]
        elif parsed_blk.ident is None and parsed_blk.pos_idx in index_map:
            blk_data = index_map[parsed_blk.pos_idx]

        if blk_data is None:
            stats['blocks_skipped'] += 1
            continue

        stats['blocks_matched'] += 1

        # Build queues of translated texts by type
        mes_queue = []
        select_queue = []
        caption_queue = []
        for t in blk_data.get("texts", []):
            translated = t.get("translated", t.get("original", ""))
            if t["type"] == "mes":
                mes_queue.append(translated)
            elif t["type"] == "select":
                select_queue.append(translated)
            elif t["type"] == "caption":
                caption_queue.append(translated)

        # Apply replacements within the block's line range
        mes_idx = 0
        select_idx = 0
        caption_idx = 0

        for i in range(parsed_blk.start, min(parsed_blk.end + 1, len(result))):
            line = result[i]

            # mes replacement
            mm = MES_RE.match(line)
            if mm:
                if mes_idx < len(mes_queue):
                    cn_text = mes_queue[mes_idx]
                    result[i] = mm.group(1) + '"' + cn_text + '"' + (mm.group(3) or ';')
                    stats['mes_replaced'] += 1
                mes_idx += 1
                continue

            # caption replacement
            cm = CAPTION_RE.match(line)
            if cm:
                if caption_idx < len(caption_queue):
                    cn_text = caption_queue[caption_idx]
                    result[i] = cm.group(1) + '"' + cn_text + '"' + (cm.group(3) or ';')
                    stats['caption_replaced'] += 1
                caption_idx += 1
                continue

            # select replacement
            sm = SELECT_RE.search(line)
            if sm:
                if select_idx < len(select_queue):
                    cn_opts = select_queue[select_idx]
                    result[i] = (line[:sm.start(1)] + sm.group(1) +
                                 cn_opts + sm.group(3) + line[sm.end():])
                    stats['select_replaced'] += 1
                select_idx += 1

    return '\n'.join(result), stats


def apply_result_file(input_path: Path, npc_dir: Path,
                      dry_run: bool = False, no_backup: bool = False) -> dict:
    """Apply translations from a result JSON file.

    Returns stats dict.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    total_stats = {
        'files_processed': 0,
        'files_skipped': 0,
        'mes_replaced': 0,
        'select_replaced': 0,
        'caption_replaced': 0,
    }

    for task in results:
        source_file = task["source_file"]
        filepath = npc_dir / source_file

        if not filepath.exists():
            print(f"  WARN: File not found: {filepath}")
            total_stats['files_skipped'] += 1
            continue

        print(f"  [{source_file}]")

        content = read_npc_file(filepath)
        translated, stats = apply_translations(content, task["npc_blocks"])

        print(f"    matched={stats['blocks_matched']} "
              f"mes={stats['mes_replaced']} "
              f"select={stats['select_replaced']} "
              f"caption={stats['caption_replaced']}")

        if not dry_run:
            if not no_backup:
                backup_file(filepath)
            write_gbk(filepath, translated)
            print(f"    -> Written (GBK)")
        else:
            print(f"    -> Dry run, not written")

        total_stats['files_processed'] += 1
        total_stats['mes_replaced'] += stats['mes_replaced']
        total_stats['select_replaced'] += stats['select_replaced']
        total_stats['caption_replaced'] += stats['caption_replaced']

    return total_stats


def main():
    parser = argparse.ArgumentParser(description="Apply AI translations to NPC files")
    parser.add_argument("--input", type=str, required=True,
                        help="Input result JSON file from translate.py")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be changed without writing files")
    parser.add_argument("--no-backup", action="store_true",
                        help="Skip backing up original files")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    print(f"NPC Translation Applier")
    print(f"  Input:     {input_path}")
    print(f"  NPC dir:   {RATHENA_NPC}")
    print(f"  Backup:    {BACKUP_DIR}")
    print(f"  Dry run:   {args.dry_run}")
    print()

    stats = apply_result_file(input_path, RATHENA_NPC, args.dry_run, args.no_backup)

    print()
    print("=== Apply Summary ===")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Files skipped:   {stats['files_skipped']}")
    print(f"  mes replaced:    {stats['mes_replaced']}")
    print(f"  select replaced: {stats['select_replaced']}")
    print(f"  caption replaced:{stats['caption_replaced']}")


if __name__ == '__main__':
    main()
