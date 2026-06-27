#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract dialogue strings from rAthena NPC scripts and write to files."""

import re
import sys
import os

def extract_mes_strings(filepath):
    """Extract all mes '...' strings from a file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    results = []
    for line in lines:
        stripped = line.strip()
        m = re.match(r'^mes\s+"(.+)"\s*;', stripped)
        if m:
            text = m.group(1)
            results.append(text)
    
    return results

def extract_select_strings(filepath):
    """Extract all select('...') strings from a file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    results = []
    for m in re.finditer(r'select\("([^"]+)"\)', content):
        results.append(m.group(1))
    
    return results

def get_unique_ordered(items):
    """Return unique items preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def main():
    files = [
        ('npc/instances/NydhoggsNest.txt', 'nydhogg'),
        ('npc/instances/SealedShrine.txt', 'sealed'),
        ('npc/pre-re/quests/quests_morocc.txt', 'morocc'),
    ]
    
    outfile = 'tools/translations/extracted_all.txt'
    with open(outfile, 'w', encoding='utf-8') as out:
        for filepath, label in files:
            mes = extract_mes_strings(filepath)
            sel = extract_select_strings(filepath)
            unique_mes = get_unique_ordered(mes)
            unique_sel = get_unique_ordered(sel)
            
            out.write(f"=== {label} ===\n")
            out.write(f"Total mes: {len(mes)}, unique: {len(unique_mes)}\n")
            out.write(f"Total select: {len(sel)}, unique: {len(unique_sel)}\n\n")
            
            out.write(f"--- MES ---\n")
            for i, s in enumerate(unique_mes):
                out.write(f"M{i+1}: {s}\n")
            
            out.write(f"\n--- SELECT ---\n")
            for i, s in enumerate(unique_sel):
                out.write(f"S{i+1}: {s}\n")
            
            out.write(f"\n\n")
    
    print(f"Written to {outfile}")
    
    # Also print counts
    for filepath, label in files:
        mes = extract_mes_strings(filepath)
        sel = extract_select_strings(filepath)
        unique_mes = get_unique_ordered(mes)
        unique_sel = get_unique_ordered(sel)
        print(f"{label}: {len(mes)} mes ({len(unique_mes)} unique), {len(sel)} select ({len(unique_sel)} unique)")

if __name__ == '__main__':
    main()
