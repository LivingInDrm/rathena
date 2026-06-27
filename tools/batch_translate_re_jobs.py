#!/usr/bin/env python3
"""
Batch translate Renewal Job Quest NPC scripts to Chinese.

This script processes all files in npc/re/jobs/ and translates
mes "..." and select("...") dialogue strings to Chinese.

Output: GBK encoded files (required by RO client)
Backup: originals saved to npc_backup_en/re/jobs/

Usage:
    python tools/batch_translate_re_jobs.py [--dry-run]
"""

import re
import os
import sys
import shutil
from pathlib import Path

RATHENA_ROOT = Path(r"D:\Projects\rathena")
NPC_DIR      = RATHENA_ROOT / "npc"
BACKUP_DIR   = RATHENA_ROOT / "npc_backup_en"

MES_RE     = re.compile(r'^(\s*mes\s+)"([^"]*)"(;.*)?$')
SELECT_RE  = re.compile(r'(\bselect\s*\(\s*")((?:[^"\\]|\\.)*?)(")')


def backup_file(src: Path):
    rel = src.relative_to(NPC_DIR)
    dst = BACKUP_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)


def write_gbk(path: Path, content: str):
    encoded = content.encode('gbk', errors='replace')
    path.write_bytes(encoded)


def read_file(filepath: Path) -> str:
    for enc in ['utf-8', 'gbk', 'latin-1']:
        try:
            return filepath.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return filepath.read_text(encoding='latin-1')


def translate_file(filepath: Path, mes_dict: dict, select_dict: dict, dry_run=False):
    """Translate using exact-match dictionaries."""
    content = read_file(filepath)
    lines = content.splitlines(keepends=False)
    result = list(lines)
    stats = {'mes': 0, 'select': 0, 'mes_total': 0, 'sel_total': 0}

    for i, line in enumerate(lines):
        mm = MES_RE.match(line)
        if mm:
            stats['mes_total'] += 1
            en = mm.group(2)
            if en in mes_dict:
                result[i] = mm.group(1) + '"' + mes_dict[en] + '"' + (mm.group(3) or ';')
                stats['mes'] += 1
            continue
        sm = SELECT_RE.search(line)
        if sm:
            stats['sel_total'] += 1
            en = sm.group(2)
            if en in select_dict:
                result[i] = line[:sm.start(1)] + sm.group(1) + select_dict[en] + sm.group(3) + line[sm.end():]
                stats['select'] += 1

    rel = filepath.relative_to(NPC_DIR)
    changed = stats['mes'] + stats['select']
    print(f"[{rel}] mes={stats['mes']}/{stats['mes_total']} sel={stats['select']}/{stats['sel_total']}")

    if not dry_run and changed > 0:
        backup_file(filepath)
        write_gbk(filepath, '\n'.join(result))
        print(f"  -> Written (GBK)")

    return stats


def main():
    dry_run = '--dry-run' in sys.argv
    target_file = None
    for arg in sys.argv[1:]:
        if arg.startswith('--file='):
            target_file = arg[7:]

    print("Batch Translate: Renewal Job Quest NPCs")
    print(f"  Dry run: {dry_run}")
    if target_file:
        print(f"  Target: {target_file}")
    print()

    # Import translation data
    from translate_re_jobs_data import TRANSLATIONS

    total = {'mes': 0, 'select': 0, 'files': 0}

    for rel_path, (mes_dict, select_dict) in TRANSLATIONS.items():
        if target_file and target_file not in rel_path:
            continue
        filepath = NPC_DIR / rel_path.replace('/', os.sep)
        if not filepath.exists():
            print(f"  SKIP (not found): {rel_path}")
            continue
        stats = translate_file(filepath, mes_dict, select_dict, dry_run)
        total['mes'] += stats['mes']
        total['select'] += stats['select']
        total['files'] += 1

    print(f"\n=== Summary ===")
    print(f"  Files: {total['files']}")
    print(f"  mes:   {total['mes']}")
    print(f"  select:{total['select']}")


if __name__ == '__main__':
    main()
