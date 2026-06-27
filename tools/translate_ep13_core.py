#!/usr/bin/env python3
"""
EP13.2 核心任务链 NPC 对话翻译引擎
逐行处理 rAthena NPC 脚本，将英文对话翻译为中文

使用方法: python tools/translate_ep13_core.py [--dry-run] [--file FILE]
"""

import re
import os
import sys
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPC_DIR = os.path.join(BASE_DIR, 'npc')
BACKUP_DIR = os.path.join(BASE_DIR, 'npc_backup_en')

# ============================================================
# 翻译引擎核心
# ============================================================

def read_file(path):
    """读取文件，自动检测编码"""
    with open(path, 'rb') as f:
        data = f.read()
    try:
        return data.decode('gbk'), 'gbk'
    except:
        return data.decode('utf-8', errors='replace'), 'utf-8'

def backup_file(path):
    """备份原文件到 npc_backup_en/"""
    rel = os.path.relpath(path, NPC_DIR)
    backup = os.path.join(BACKUP_DIR, rel)
    os.makedirs(os.path.dirname(backup), exist_ok=True)
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
        return True
    return False

def write_gbk(path, text):
    """写入GBK编码文件"""
    with open(path, 'wb') as f:
        f.write(text.encode('gbk', errors='replace'))

def extract_mes_content(line):
    """提取 mes "..." 中的内容"""
    m = re.match(r'^(\s*mes\s+)"(.*)"(\s*;?\s*)$', line)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return None, None, None

def extract_select_content(line):
    """提取 select("...") 中的内容"""
    m = re.search(r'select\("([^"]+)"\)', line)
    if m:
        return m.group(1)
    return None

def has_chinese(text):
    """检查是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def is_english_text(text):
    """检查是否是需要翻译的英文文本"""
    # 跳过纯颜色代码、纯符号、纯空格
    clean = re.sub(r'\^[0-9a-fA-F]{6}', '', text)
    return bool(re.search(r'[a-zA-Z]{2,}', clean)) and not has_chinese(text)

def translate_line(line, trans_dict):
    """翻译单行，返回翻译后的行和是否翻译了"""
    # 跳过注释行
    if line.strip().startswith('//'):
        return line, False
    
    translated = False
    new_line = line
    
    # 处理 mes "..." 
    prefix, content, suffix = extract_mes_content(line)
    if prefix is not None and content is not None:
        if content in trans_dict:
            new_line = f'{prefix}"{trans_dict[content]}"{suffix}'
            translated = True
        return new_line, translated
    
    # 处理 select("...")
    sel = extract_select_content(line)
    if sel and sel in trans_dict:
        new_line = line.replace(f'select("{sel}")', f'select("{trans_dict[sel]}")')
        translated = True
    
    return new_line, translated

def process_file(filepath, trans_dict, dry_run=False):
    """处理单个文件"""
    text, enc = read_file(filepath)
    lines = text.split('\n')
    
    result_lines = []
    count = 0
    
    for line in lines:
        new_line, did = translate_line(line, trans_dict)
        if did:
            count += 1
        result_lines.append(new_line)
    
    if not dry_run and count > 0:
        backup_file(filepath)
        output = '\n'.join(result_lines)
        write_gbk(filepath, output)
    
    return count

# ============================================================
# 加载翻译字典
# ============================================================

def load_translations(name):
    """从翻译数据文件加载字典"""
    trans_file = os.path.join(BASE_DIR, 'tools', 'translations', f'{name}.py')
    if os.path.exists(trans_file):
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, trans_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.TRANSLATIONS
    return {}

# ============================================================
# 主程序
# ============================================================

# EP13.2 核心文件列表
EP13_FILES = [
    ('quests_morocc', 'npc/quests/quests_morocc.txt'),
    ('quests_13_1', 'npc/quests/quests_13_1.txt'),
    ('quests_13_2', 'npc/quests/quests_13_2.txt'),
    ('cities_splendide', 'npc/cities/splendide.txt'),
    ('cities_manuk', 'npc/cities/manuk.txt'),
    ('cities_morocc', 'npc/cities/morocc.txt'),
    ('instances_nydhogg', 'npc/instances/NydhoggsNest.txt'),
    ('instances_sealed', 'npc/instances/SealedShrine.txt'),
    ('other_dim_gap', 'npc/re/other/dimensional_gap.txt'),
    ('pre_re_morocc', 'npc/pre-re/quests/quests_morocc.txt'),
]

def main():
    dry_run = '--dry-run' in sys.argv
    target_file = None
    for i, arg in enumerate(sys.argv):
        if arg == '--file' and i + 1 < len(sys.argv):
            target_file = sys.argv[i + 1]
    
    total = 0
    for name, rel_path in EP13_FILES:
        if target_file and name != target_file:
            continue
        
        filepath = os.path.join(BASE_DIR, rel_path)
        if not os.path.exists(filepath):
            print(f"  SKIP {rel_path} (not found)")
            continue
        
        trans = load_translations(name)
        if not trans:
            print(f"  SKIP {rel_path} (no translations)")
            continue
        
        count = process_file(filepath, trans, dry_run)
        total += count
        mode = "DRY-RUN" if dry_run else "DONE"
        print(f"  {mode} {rel_path}: {count} strings translated")
    
    print(f"\nTotal: {total} strings translated")

if __name__ == '__main__':
    main()
