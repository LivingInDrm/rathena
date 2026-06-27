import re, os, sys

with open('npc/quests/quests_13_2.txt','rb') as f:
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

outpath = os.path.join(os.path.dirname(__file__), '_all_strings.txt')
with open(outpath, 'w', encoding='utf-8') as out:
    for i, s in enumerate(ums):
        out.write(f'MES|{i}|{s}\n')
    for i, s in enumerate(uss):
        out.write(f'SEL|{i}|{s}\n')

sys.stderr.write(f'Written: {len(ums)} mes, {len(uss)} select to {outpath}\n')
sys.stderr.write(f'File size: {os.path.getsize(outpath)}\n')
