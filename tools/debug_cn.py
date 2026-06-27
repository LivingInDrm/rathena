"""Debug CN cache content."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import npc_cn_translate as t

t.build_file_mappings()
t.download_repo_zip()

cn = t.fetch_cn_file('jobs/2-1/assassin.txt')
print('cn found:', cn is not None)
if cn:
    print('cn length:', len(cn))
    print('cn first 500 chars:')
    print(repr(cn[:500]))
    has_cn = any(ord(c) > 0x80 for c in cn)
    print('has_cn_chars:', has_cn)
