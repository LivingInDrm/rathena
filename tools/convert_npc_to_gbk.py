#!/usr/bin/env python3
"""
One-time script: convert all translated NPC files from UTF-8 to GBK encoding.
RO client (langtype=3, Simplified Chinese) expects GBK encoding.
"""
import re
import sys
from pathlib import Path

NPC_ROOT = Path(__file__).parent.parent / "npc"
# All directories that may contain translated (UTF-8 Chinese) files
DIRS = ["pre-re", "cities", "re", "kafras", "custom"]

def has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))

def main():
    count = 0
    skipped = 0
    errors = []
    for d in DIRS:
        target = NPC_ROOT / d
        if not target.exists():
            continue
        for f in sorted(target.rglob("*.txt")):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                if has_chinese(content):
                    f.write_text(content, encoding="gbk", errors="replace")
                    print(f"GBK: {f.relative_to(NPC_ROOT.parent)}")
                    count += 1
                else:
                    skipped += 1
            except Exception as e:
                errors.append(f"{f}: {e}")

    print()
    print(f"Converted to GBK : {count}")
    print(f"Skipped (no CJK) : {skipped}")
    if errors:
        print("Errors:")
        for e in errors:
            print(f"  {e}")

if __name__ == "__main__":
    main()
