#!/usr/bin/env python3
"""Apply small deterministic client UI text polish fixes."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


TEXT_REPLACEMENTS: dict[str, list[tuple[bytes, bytes]]] = {
    r"System\LuaFiles514\itemInfo_f.lua": [
        (b"^0000CCServer: ", "^0000CC服务器：".encode("cp936")),
        (b"^0000CCItem ID:^000000 ", "^0000CC物品ID：^000000 ".encode("cp936")),
    ],
    r"SystemEN\LuaFiles514\itemInfo_f.lua": [
        (b"^0000CCServer: ", "^0000CC服务器：".encode("cp936")),
        (b"^0000CCItem ID:^000000 ", "^0000CC物品ID：^000000 ".encode("cp936")),
    ],
    r"System\itemInfo.lua": [
        (b'Name = "Database"', 'Name = "数据库"'.encode("cp936")),
    ],
    r"SystemEN\itemInfo.lua": [
        (b'Name = "Database"', 'Name = "数据库"'.encode("cp936")),
    ],
    r"System\itemInfo_C.lua": [
        (b'Unknown Item', "未知物品".encode("cp936")),
        (b'identifiedDisplayName = "Item"', 'identifiedDisplayName = "物品"'.encode("cp936")),
        (b'"Line 1"', '"第1行"'.encode("cp936")),
        (b'"Line 2"', '"第2行"'.encode("cp936")),
    ],
    r"SystemEN\itemInfo_C.lua": [
        (b'Unknown Item', "未知物品".encode("cp936")),
        (b'identifiedDisplayName = "Item"', 'identifiedDisplayName = "物品"'.encode("cp936")),
        (b'"Line 1"', '"第1行"'.encode("cp936")),
        (b'"Line 2"', '"第2行"'.encode("cp936")),
    ],
    r"data\luafiles514\lua files\skillinfoz\skilltreeview.lub": [
        (b'"1st"', '"一转"'.encode("cp936")),
        (b'"2nd"', '"二转"'.encode("cp936")),
        (b'"3rd"', '"三转"'.encode("cp936")),
        (b'"4th"', '"四转"'.encode("cp936")),
        (b'"Ninja"', '"忍者"'.encode("cp936")),
        (b'"Gunslinger"', '"神枪手"'.encode("cp936")),
        (b'"Novice"', '"初心者"'.encode("cp936")),
        (b'"Taekwon"', '"跆拳道"'.encode("cp936")),
        (b'"Summoner"', '"召唤师"'.encode("cp936")),
    ],
}


def backup_files(client_dir: Path, backup_dir: Path, relpaths: list[str]) -> Path:
    backup_root = backup_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
    for rel in relpaths:
        source = client_dir / rel
        if not source.exists():
            continue
        destination = backup_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return backup_root


def apply_replacements(client_dir: Path, dry_run: bool, backup_root: Path | None) -> dict:
    results = []
    total_replacements = 0
    for rel, replacements in TEXT_REPLACEMENTS.items():
        path = client_dir / rel
        if not path.exists():
            results.append({"file": rel, "exists": False, "replacements": 0})
            continue
        data = path.read_bytes()
        changed = data
        count = 0
        for old, new in replacements:
            occurrences = changed.count(old)
            if occurrences:
                changed = changed.replace(old, new)
                count += occurrences
        total_replacements += count
        if count and not dry_run:
            path.write_bytes(changed)
        results.append({"file": rel, "exists": True, "replacements": count})
    return {
        "client_dir": str(client_dir),
        "dry_run": dry_run,
        "backup": str(backup_root) if backup_root else None,
        "total_replacements": total_replacements,
        "files": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-dir", default=r"D:\rag")
    parser.add_argument("--backup-dir", default=r"D:\rag_cn_backup")
    parser.add_argument("--output", default=str(Path("tmp") / "client_visible_polish.json"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    client_dir = Path(args.client_dir)
    backup_root = None
    if not args.dry_run and not args.no_backup:
        backup_root = backup_files(client_dir, Path(args.backup_dir), list(TEXT_REPLACEMENTS))

    report = apply_replacements(client_dir, args.dry_run, backup_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
