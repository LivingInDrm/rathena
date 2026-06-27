"""Debug script to test translation of a single file."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import npc_cn_translate as t

t.build_file_mappings()
t.download_repo_zip()

from pathlib import Path
en_path = t.RATHENA_NPC / 'jobs/2-1/assassin.txt'
print('en_path:', en_path)
print('exists:', en_path.exists())
cn = t.fetch_cn_file('jobs/2-1/assassin.txt')
print('cn found:', cn is not None)
if cn:
    en = en_path.read_text(encoding='utf-8')
    translated, stats = t.apply_translation(en, cn)
    print('stats:', stats)
    has_cn = any(ord(c) > 0x80 for c in translated[:5000])
    print('has_cn_in_result:', has_cn)
    t.write_gbk(en_path, translated)
    print('written')
    d = en_path.read_bytes()
    print('has_cn_in_file:', any(b > 0x80 for b in d[:2000]))
