"""
Generator script to create the complete quests_13_1.py translation file.
Reads all unique English strings from the source file and outputs them
with Chinese translations.
"""
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

print(f"Total unique mes: {len(unique_mes)}")
print(f"Total unique select: {len(unique_sel)}")
print(f"Grand total: {len(unique_mes) + len(unique_sel)}")

# Write all strings to a numbered file for reference
outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strings_numbered_13_1.txt')
with open(outpath, 'w', encoding='utf-8') as f:
    for i, t in enumerate(unique_mes):
        f.write(f"M{i+1:04d}|{t}\n")
    for i, t in enumerate(unique_sel):
        f.write(f"S{i+1:04d}|{t}\n")

print(f"Written to {outpath}")
