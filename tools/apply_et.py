import shutil, os

filepath = 'D:/Projects/rathena/npc/instances/EndlessTower.txt'
backup_path = 'D:/Projects/rathena/npc_backup_en/instances/EndlessTower.txt'

os.makedirs(os.path.dirname(backup_path), exist_ok=True)
if not os.path.exists(backup_path):
    shutil.copy2(filepath, backup_path)
    print('Backed up original')

with open(filepath, 'rb') as f:
    raw = f.read()

# Normalize line endings first
raw = raw.replace(b'\r\n', b'\n')
lines = raw.split(b'\n')

print(f'Total lines: {len(lines)}')

# Find the actual lines to translate by content matching
translations_by_content = {
    b'mes "Destroy the Purification Stone immediately";': '\t\t\tmes "立即摧毁净化之石";',
    b'mes "You have canceled it.";': '\t\t\tmes "你已经取消了。";',
    b"mes \"I see. I guess you aren't as greedy or ambitious as those other adventurers.\";": '\t\t\t\tmes "我明白了。我猜你不像那些其他冒险者那样贪婪或野心勃勃。";',
}

changes = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    for pattern, replacement in translations_by_content.items():
        if stripped == pattern:
            lines[i] = replacement.encode('gbk', errors='replace')
            changes += 1
            print(f'  Translated L{i+1}: {stripped!r}')
            break

# Write back with Unix line endings
result = b'\n'.join(lines)
with open(filepath, 'wb') as f:
    f.write(result)

print(f'Applied {changes} translations to EndlessTower.txt')
