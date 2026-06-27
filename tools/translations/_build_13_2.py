#!/usr/bin/env python3
"""Build the quests_13_2.py translation dictionary."""
import re, os

with open('npc/quests/quests_13_2.txt', 'rb') as f:
    data = f.read()
text = data.decode('gbk', errors='replace')
lines = text.split('\n')

ms = []
ss = []
for l in lines:
    s = l.strip()
    m = re.match(r'^mes\s+"(.*)";\s*$', s)
    if m:
        ms.append(m.group(1))
    m = re.search(r'select\("(.*?)"\)', s)
    if m:
        ss.append(m.group(1))

seen = set()
ums = []
for x in ms:
    if x not in seen:
        seen.add(x)
        ums.append(x)
seen2 = set()
uss = []
for x in ss:
    if x not in seen2:
        seen2.add(x)
        uss.append(x)

def has_chinese(s):
    return any('\u4e00' <= c <= '\u9fff' for c in s)

# Filter to English-only strings
en_mes = [s for s in ums if not has_chinese(s)]
en_sel = [s for s in uss if not has_chinese(s)]

print(f"English mes to translate: {len(en_mes)}")
print(f"English sel to translate: {len(en_sel)}")

# Write them out for reference
with open(os.path.join(os.path.dirname(__file__), '_en_strings.txt'), 'w', encoding='utf-8') as f:
    for i, s in enumerate(en_mes):
        f.write(f"MES|{i}|{s}\n")
    for i, s in enumerate(en_sel):
        f.write(f"SEL|{i}|{s}\n")

print("Written to _en_strings.txt")
