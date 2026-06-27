#!/usr/bin/env python3
"""
Pre-Renewal 专属 NPC 脚本中文翻译工具

逐文件处理 npc/pre-re/ 下的英文对话，翻译为中文。
仅替换 mes "..." 和 select("...") 对话字符串，保留所有脚本结构。
输出使用 GBK 编码。

此脚本读取 translations/ 目录下的翻译数据文件来执行替换。
"""

import os
import re
import sys
import shutil
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NPC_PRE_RE = PROJECT_ROOT / "npc" / "pre-re"
BACKUP_DIR = PROJECT_ROOT / "npc_backup_en" / "pre-re"


def backup_file(src_path):
    """备份原文件"""
    rel_path = src_path.relative_to(NPC_PRE_RE)
    backup_path = BACKUP_DIR / rel_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(src_path, backup_path)


def write_gbk(path, content):
    """以 GBK 编码写入文件"""
    encoded = content.encode('gbk', errors='replace')
    with open(path, 'wb') as f:
        f.write(encoded)


def read_file(path):
    """读取文件内容"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='gbk') as f:
            return f.read()


def translate_and_write(src_path, translated_content):
    """备份原文件并写入翻译后的内容"""
    backup_file(src_path)
    write_gbk(src_path, translated_content)


if __name__ == '__main__':
    print("此脚本由 translate_pre_re_all.py 调用，不直接运行。")
