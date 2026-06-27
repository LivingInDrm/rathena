#!/usr/bin/env python3
"""Show untranslated mes lines in job change scripts."""
import sys, re

sys.stdout.reconfigure(encoding='utf-8')

files = {
    'swordman': 'npc/pre-re/jobs/1-1/swordman.txt',
    'mage': 'npc/pre-re/jobs/1-1/mage.txt',
    'archer': 'npc/pre-re/jobs/1-1/archer.txt',
    'acolyte': 'npc/pre-re/jobs/1-1/acolyte.txt',
    'merchant': 'npc/pre-re/jobs/1-1/merchant.txt',
    'thief': 'npc/pre-re/jobs/1-1/thief.txt',
}

for name, fp in files.items():
    with open(fp, 'rb') as f:
        data = f.read()
    text = data.decode('gbk', errors='replace')
    lines = text.split('\n')

    en_lines = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('//'):
            continue
        # Check mes lines
        m = re.match(r'^\s*mes\s+"(.*)"', stripped)
        if m:
            content = m.group(1)
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in content)
            if not has_chinese and bool(re.search(r'[a-zA-Z]{3,}', content)):
                en_lines.append((i, 'mes', content))
            continue
        # Check select lines
        sel = re.search(r'select\("([^"]*)"\)', stripped)
        if sel:
            content = sel.group(1)
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in content)
            if not has_chinese and bool(re.search(r'[a-zA-Z]{3,}', content)):
                en_lines.append((i, 'sel', content))

    if en_lines:
        print(f'=== {name} ({len(en_lines)} untranslated) ===')
        for ln, typ, content in en_lines[:50]:
            print(f'  L{ln} [{typ}]: {content}')
        if len(en_lines) > 50:
            print(f'  ... and {len(en_lines)-50} more')
        print()
