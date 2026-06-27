#!/usr/bin/env python3
"""
Quick verification: check that translation produces correct Chinese mes strings
with structure preserved from English (coordinates, sprite IDs, logic intact).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from npc_cn_translate import fetch_cn_file, apply_translation

def check_file(en_path, cn_rel):
    en_content = open(en_path, encoding='utf-8').read()
    cn_content = fetch_cn_file(cn_rel)
    if not cn_content:
        print(f"  SKIP: no CN file")
        return

    translated, stats = apply_translation(en_content, cn_content)
    lines = translated.splitlines()

    # Find first script block
    in_block = False
    depth = 0
    block_lines = []
    for line in lines:
        if not in_block and 'script' in line and ',{' in line:
            in_block = True
        if in_block:
            block_lines.append(line)
            depth += line.count('{') - line.count('}')
            if depth <= 0 and len(block_lines) > 1:
                break

    print("  First NPC block (translated):")
    for l in block_lines[:15]:
        print(f"    {repr(l)}")

    # Count Chinese characters
    cn_chars = sum(1 for c in translated if '\u4e00' <= c <= '\u9fff')
    # Count mes lines
    mes_lines = [l for l in lines if l.strip().startswith('mes "')]

    print(f"  Chinese chars in output: {cn_chars}")
    print(f"  Total mes lines: {len(mes_lines)}")
    print(f"  Stats: {stats}")

    # Check GBK encodability
    try:
        enc = translated.encode('gbk', errors='strict')
        print(f"  GBK encoding: OK ({len(enc)} bytes)")
    except UnicodeEncodeError as e:
        # Show which character failed
        print(f"  GBK encoding: WARN - {e}")
        # Count replaceable chars
        enc = translated.encode('gbk', errors='replace')
        replaced = enc.count(b'?') - translated.count('?')
        print(f"    ({replaced} chars replaced with '?')")

    # Verify coordinates preserved (first 5 map,x,y,dir lines)
    print("  First 5 map coordinate lines:")
    coord_lines = [l for l in lines if ',' in l and l[0].isalpha() and 'script' in l or
                   ',' in l and l[0].isalpha() and 'duplicate' in l]
    for l in coord_lines[:5]:
        print(f"    {l[:80]}")

    print()


if __name__ == '__main__':
    print("=== Verifying cities/prontera.txt ===")
    check_file('npc/cities/prontera.txt', 'cities/prontera.txt')

    print("=== Verifying cities/lighthalzen.txt ===")
    check_file('npc/cities/lighthalzen.txt', 'cities/lighthalzen.txt')

    print("=== Verifying airports/airships.txt ===")
    check_file('npc/airports/airships.txt', 'airports/airships.txt')
