"""Check which CN files have Chinese characters, grouped by directory."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import npc_cn_translate as t
from collections import defaultdict

t.build_file_mappings()
t.download_repo_zip()

dirs_cn = defaultdict(int)
dirs_total = defaultdict(int)
for key, content in sorted(t._CN_CACHE.items()):
    top = key.split('/')[0]
    dirs_total[top] += 1
    if any(ord(c) > 0x80 for c in content):
        dirs_cn[top] += 1

print('Directory coverage (files with Chinese / total):')
for d in sorted(dirs_total.keys()):
    cn = dirs_cn.get(d, 0)
    total = dirs_total[d]
    pct = cn * 100 // total if total > 0 else 0
    print(f'  {d}: {cn}/{total} ({pct}%)')
