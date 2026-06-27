"""Check kafras CN content."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import npc_cn_translate as t

t.build_file_mappings()
t.download_repo_zip()

cn = t.fetch_cn_file('kafras/kafras.txt')
print('cn found:', cn is not None)
if cn:
    has_cn = any(ord(c) > 0x80 for c in cn)
    print('has_cn_chars:', has_cn)
    print('first 300:', repr(cn[:300]))
