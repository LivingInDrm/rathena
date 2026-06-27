#!/usr/bin/env python3
"""
EP13.2 Large Quest File Translation Tool
=========================================
Translates English NPC dialogue in large rAthena quest scripts to Chinese.
Uses content-matching approach (not line numbers) for robustness.
Outputs in GBK encoding as required by RO client.

Usage: python tools/translate_quest.py <quest_file_relative_path>
Example: python tools/translate_quest.py quests/quests_juperos.txt
"""

import re
import os
import sys
import shutil
from pathlib import Path

RATHENA_NPC = Path(r"D:\Projects\rathena\npc")
BACKUP_DIR = Path(r"D:\Projects\rathena\npc_backup_en")

# ─── RO-specific terminology ────────────────────────────────────────────────
RO_TERMS = {
    # Cities
    "Prontera": "普隆德拉",
    "Geffen": "吉芬",
    "Morroc": "梦罗克",
    "Payon": "斐扬",
    "Alberta": "艾尔贝塔",
    "Aldebaran": "阿尔德巴兰",
    "Yuno": "朱诺",
    "Juno": "朱诺",
    "Lighthalzen": "利希塔尔岑",
    "Einbroch": "艾因布罗克",
    "Einbech": "艾因贝赫",
    "Hugel": "胡格尔",
    "Rachel": "拉赫尔",
    "Veins": "维纳斯",
    "Manuk": "马努克",
    "Splendide": "斯普兰蒂德",
    "Juperos": "朱庇洛斯",
    "Niflheim": "尼芙海姆",
    "Amatsu": "天津",
    "Louyang": "龙之城",
    "Gonryun": "昆仑",
    "Izlude": "伊斯鲁德",
    "Comodo": "科莫多",
    "Umbala": "乌姆巴拉",
    "Nameless Island": "无名岛",
    "Thor's Volcano": "托尔火山",
    "Abyss Lake": "深渊之湖",
    "Bio Lab": "生物实验室",
    "Biolabs": "生物实验室",
    "Thanatos Tower": "塔纳托斯之塔",
    "Endless Tower": "无尽之塔",
    "Sealed Shrine": "封印神殿",
    
    # Characters/NPCs
    "King Tristram III": "特里斯坦三世国王",
    "King Tristram": "特里斯坦国王",
    
    # Game terms
    "Zeny": "金币",
    "adventurer": "冒险者",
    "Adventurer": "冒险者",
    "guild": "公会",
    "Guild": "公会",
    "party": "队伍",
    "Party": "队伍",
    "Kafra": "卡普拉",
    "Warp Portal": "传送之阵",
    
    # Classes
    "Swordman": "剑士",
    "Magician": "魔法师",
    "Archer": "弓箭手",
    "Acolyte": "服事",
    "Merchant": "商人",
    "Thief": "盗贼",
    "Knight": "骑士",
    "Crusader": "十字军",
    "Wizard": "巫师",
    "Sage": "贤者",
    "Hunter": "猎人",
    "Bard": "吟游诗人",
    "Dancer": "舞娘",
    "Priest": "牧师",
    "Monk": "武僧",
    "Blacksmith": "铁匠",
    "Alchemist": "炼金术师",
    "Assassin": "刺客",
    "Rogue": "流氓",
    
    # Races
    "Sapha": "萨法",
    "Saphas": "萨法族",
    "Laphine": "拉斐尼",
    "Fairy": "精灵",
    "Fairies": "精灵族",
}


def backup_file(filepath: Path):
    """Backup original file before modification."""
    rel = filepath.relative_to(RATHENA_NPC)
    backup_path = BACKUP_DIR / rel
    if not backup_path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, backup_path)
        print(f"  Backed up: {rel}")


def read_file(filepath: Path) -> tuple:
    """Read file and return (lines_as_bytes, encoding_used)."""
    with open(filepath, 'rb') as f:
        raw = f.read()
    # Normalize line endings
    raw = raw.replace(b'\r\n', b'\n')
    lines = raw.split(b'\n')
    return lines


def write_file(filepath: Path, lines: list):
    """Write lines back in GBK encoding."""
    result = b'\n'.join(lines)
    with open(filepath, 'wb') as f:
        f.write(result)


def is_english_dialogue(line_bytes: bytes) -> bool:
    """Check if a line contains English dialogue that needs translation."""
    stripped = line_bytes.strip()
    # Must be a mes or select line
    if not (stripped.startswith(b'mes "') or stripped.startswith(b'select(') or 
            stripped.startswith(b'switch(select(')):
        return False
    # Must not already contain Chinese (high bytes)
    if any(0x80 <= b for b in stripped):
        return False
    # Must contain actual English text (not just punctuation/variables)
    # Skip lines that are just player name references
    if stripped == b'mes "["+strcharinfo(0)+"]";':
        return False
    if stripped == b'mes "["+.@name$+"]";':
        return False
    # Skip lines that are just dots or ellipsis
    if stripped in (b'mes ".";', b'mes "..";', b'mes "...";', b'mes "....";',
                    b'mes ".....";', b'mes "......";', b'mes ".......";',
                    b'mes "........";', b'mes ".........";', b'mes "..........";',
                    b'mes "...........";'):
        return False
    # Must have some alphabetic content
    text = stripped.decode('ascii', errors='replace')
    if not any(c.isalpha() for c in text):
        return False
    return True


def extract_mes_text(line_bytes: bytes) -> str:
    """Extract the text content from a mes line."""
    stripped = line_bytes.strip().decode('ascii', errors='replace')
    if stripped.startswith('mes "') and stripped.endswith('";'):
        return stripped[5:-2]
    return None


def count_english_dialogue(filepath: Path) -> int:
    """Count English dialogue lines in a file."""
    lines = read_file(filepath)
    count = sum(1 for l in lines if is_english_dialogue(l))
    return count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python translate_quest.py <relative_path>")
        print("Example: python translate_quest.py quests/quests_juperos.txt")
        sys.exit(1)
    
    rel_path = sys.argv[1]
    filepath = RATHENA_NPC / rel_path
    
    if not filepath.exists():
        print(f"File not found: {filepath}")
        sys.exit(1)
    
    lines = read_file(filepath)
    en_count = sum(1 for l in lines if is_english_dialogue(l))
    total_mes = sum(1 for l in lines if b'mes "' in l)
    
    print(f"File: {filepath}")
    print(f"Total lines: {len(lines)}")
    print(f"Total mes lines: {total_mes}")
    print(f"English dialogue lines needing translation: {en_count}")
    
    # Print first 20 English dialogue lines as sample
    print("\nSample English dialogue lines:")
    count = 0
    for i, l in enumerate(lines):
        if is_english_dialogue(l) and count < 20:
            text = extract_mes_text(l)
            if text:
                print(f"  L{i+1}: {text[:80]}")
            count += 1
