import re

# Test MES_RE
MES_RE = re.compile(r'^(\s*mes\s+)"([^"]*)"(;.*)?$')
line = '\tmes "hello";'
print(f"line: {repr(line)}")
print(f"pattern: {MES_RE.pattern}")
m = MES_RE.match(line)
print(f"match: {m}")
if m:
    print(f"groups: {m.groups()}")

# Test with actual file content
from pathlib import Path
content = Path(r"D:\Projects\rathena\npc_backup_en\re\jobs\1-1\mage.txt").read_text(encoding='utf-8')
lines = content.splitlines()
total = 0
matched = 0
unmatched = []
for i, l in enumerate(lines):
    if 'mes ' in l and '"' in l and not l.strip().startswith('//'):
        mm = MES_RE.match(l)
        if mm:
            matched += 1
        else:
            # Check if it's a mes line
            if l.strip().startswith('mes '):
                total += 1
                unmatched.append(f"  {i+1}: {l.strip()[:80]}")

print(f"\nmage.txt: regex matched={matched}, unmatched mes={total}")
for u in unmatched[:5]:
    print(u)
