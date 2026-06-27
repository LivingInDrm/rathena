"""Check which CN files actually have Chinese characters."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
import npc_cn_translate as t

t.build_file_mappings()
t.download_repo_zip()

total = 0
has_cn = 0
no_cn = []
for key, content in sorted(t._CN_CACHE.items()):
    total += 1
    if any(ord(c) > 0x80 for c in content):
        has_cn += 1
    else:
        no_cn.append(key)

print(f'Total CN files: {total}')
print(f'Files WITH Chinese: {has_cn}')
print(f'Files WITHOUT Chinese: {len(no_cn)}')
print()
print('Sample files WITHOUT Chinese:')
for f in no_cn[:20]:
    print(' ', f)
