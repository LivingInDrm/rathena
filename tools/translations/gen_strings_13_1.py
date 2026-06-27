import re
import os

filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'npc', 'quests', 'quests_13_1.txt')

with open(filepath, 'rb') as f:
    raw = f.read()

content = raw.decode('gbk', errors='replace')
lines = content.split('\n')

eng_mes = []
eng_select = []

for i, line in enumerate(lines):
    stripped = line.strip()
    mes_match = re.match(r'^\s*mes\s+"(.+)"\s*;', stripped)
    if mes_match:
        text = mes_match.group(1)
        ascii_alpha = sum(1 for c in text if c.isascii() and c.isalpha())
        non_ascii = sum(1 for c in text if ord(c) > 127)
        if ascii_alpha > 2 and non_ascii == 0:
            eng_mes.append(text)
    
    sel_matches = re.findall(r'select\("(.+?)"\)', stripped)
    for text in sel_matches:
        ascii_alpha = sum(1 for c in text if c.isascii() and c.isalpha())
        non_ascii = sum(1 for c in text if ord(c) > 127)
        if ascii_alpha > 2 and non_ascii == 0:
            eng_select.append(text)

unique_mes = list(dict.fromkeys(eng_mes))
unique_sel = list(dict.fromkeys(eng_select))

outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'all_strings_13_1.txt')
with open(outpath, 'w', encoding='utf-8') as f:
    for t in unique_mes:
        f.write('MES|' + t + '\n')
    for t in unique_sel:
        f.write('SEL|' + t + '\n')

print(f'Written {len(unique_mes)} mes + {len(unique_sel)} select = {len(unique_mes)+len(unique_sel)} total')
print(f'Output: {outpath}')
