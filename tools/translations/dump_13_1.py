import re
import os

# Read the file with GBK encoding
with open(os.path.join(os.path.dirname(__file__), '..', '..', 'npc', 'quests', 'quests_13_1.txt'), 'rb') as f:
    raw = f.read()

content = raw.decode('gbk', errors='replace')
lines = content.split('\n')

eng_mes = []
eng_select = []

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Match mes lines: mes "...";
    mes_match = re.match(r'^\s*mes\s+"(.+)"\s*;', stripped)
    if mes_match:
        text = mes_match.group(1)
        ascii_alpha = sum(1 for c in text if c.isascii() and c.isalpha())
        non_ascii = sum(1 for c in text if ord(c) > 127)
        if ascii_alpha > 2 and non_ascii == 0:
            eng_mes.append(text)
    
    # Match select lines
    sel_matches = re.findall(r'select\("(.+?)"\)', stripped)
    for text in sel_matches:
        ascii_alpha = sum(1 for c in text if c.isascii() and c.isalpha())
        non_ascii = sum(1 for c in text if ord(c) > 127)
        if ascii_alpha > 2 and non_ascii == 0:
            eng_select.append(text)

# Get unique preserving order
unique_mes = list(dict.fromkeys(eng_mes))
unique_sel = list(dict.fromkeys(eng_select))

# Write all unique strings to a dump file
with open('dump_13_1.txt', 'w', encoding='utf-8') as f:
    f.write(f"=== UNIQUE MES STRINGS ({len(unique_mes)}) ===\n\n")
    for i, t in enumerate(unique_mes):
        f.write(f"{i+1}. {t}\n")
    f.write(f"\n=== UNIQUE SELECT STRINGS ({len(unique_sel)}) ===\n\n")
    for i, t in enumerate(unique_sel):
        f.write(f"{i+1}. {t}\n")

print(f"Dumped {len(unique_mes)} mes + {len(unique_sel)} select to dump_13_1.txt")
