"""Verify translation results - check how many NPC files now have Chinese."""
import sys
import os
from pathlib import Path

npc_dir = Path('D:/Projects/rathena/npc')
total = 0
has_cn = 0
no_cn_files = []

for f in npc_dir.rglob('*.txt'):
    total += 1
    data = f.read_bytes()
    if any(b > 0x80 for b in data):
        has_cn += 1
    else:
        no_cn_files.append(str(f.relative_to(npc_dir)))

print(f'Total NPC txt files: {total}')
print(f'Files WITH Chinese (GBK): {has_cn}')
print(f'Files WITHOUT Chinese: {total - has_cn}')
print()
print('Sample files still in English:')
for f in sorted(no_cn_files)[:30]:
    print(' ', f)
