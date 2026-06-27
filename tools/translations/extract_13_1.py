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
        # Check if English: has ASCII alpha chars and no non-ASCII chars
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

print(f"Total lines: {len(lines)}")
print(f"English mes lines found: {len(eng_mes)}")
print(f"English select lines found: {len(eng_select)}")
print(f"Unique English mes: {len(unique_mes)}")
print(f"Unique English select: {len(unique_sel)}")

# Print first 20 unique mes
print("\n--- First 20 unique mes ---")
for t in unique_mes[:20]:
    print(f"  {repr(t)}")

print("\n--- First 20 unique select ---")
for t in unique_sel[:20]:
    print(f"  {repr(t)}")

# Print last 20 unique mes
print("\n--- Last 20 unique mes ---")
for t in unique_mes[-20:]:
    print(f"  {repr(t)}")
