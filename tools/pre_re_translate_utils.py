#!/usr/bin/env python3
"""
Pre-Renewal NPC 中文翻译 - 批量处理脚本

读取 npc/pre-re/ 下所有含对话的 NPC 脚本，
将英文 mes/select 对话翻译为中文，保留脚本结构，
输出 GBK 编码。
"""

import os
import re
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NPC_PRE_RE = PROJECT_ROOT / "npc" / "pre-re"
BACKUP_DIR = PROJECT_ROOT / "npc_backup_en" / "pre-re"


def backup_file(src_path):
    """备份原文件到 npc_backup_en/pre-re/"""
    rel_path = src_path.relative_to(NPC_PRE_RE)
    backup_path = BACKUP_DIR / rel_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(src_path, backup_path)


def write_gbk(path, content):
    """以 GBK 编码写入"""
    encoded = content.encode('gbk', errors='replace')
    with open(path, 'wb') as f:
        f.write(encoded)


def read_file(path):
    """读取文件"""
    for enc in ['utf-8', 'gbk', 'latin-1']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def translate_file(src_path, translated_lines):
    """
    用翻译后的完整行列表替换文件内容。
    translated_lines 是翻译后的完整文件内容字符串。
    """
    backup_file(src_path)
    write_gbk(src_path, translated_lines)
    rel = src_path.relative_to(NPC_PRE_RE)
    print(f"  已翻译: {rel}")


if __name__ == '__main__':
    print("此模块提供翻译工具函数，由各翻译脚本调用。")
