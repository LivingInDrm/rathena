"""Check which directories have Chinese translations."""
import sys
import os
from pathlib import Path
from collections import defaultdict

npc_dir = Path('D:/Projects/rathena/npc')
dirs_cn = defaultdict(int)
dirs_total = defaultdict(int)

for f in npc_dir.rglob('*.txt'):
    rel = f.relative_to(npc_dir)
    top = rel.parts[0]
    dirs_total[top] += 1
    data = f.read_bytes()
    if any(b > 0x80 for b in data):
        dirs_cn[top] += 1

print('Directory coverage (files with Chinese / total):')
for d in sorted(dirs_total.keys()):
    cn = dirs_cn.get(d, 0)
    total = dirs_total[d]
    pct = cn * 100 // total if total > 0 else 0
    bar = '#' * (pct // 5) + '.' * (20 - pct // 5)
    print(f'  {d:20s}: {cn:3d}/{total:3d} ({pct:3d}%) [{bar}]')
