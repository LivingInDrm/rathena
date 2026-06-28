import urllib.request
import json
import os
import re

API_KEY = ""
with open(r"D:\Projects\rathena\tools\ai_translate\api_config.txt") as f:
    for line in f:
        if line.startswith("OPENAI_API_KEY="):
            API_KEY = line.strip().split("=", 1)[1]

def translate_batch(texts, context="RO game system messages"):
    url = "https://api.openai.com/v1/chat/completions"
    prompt = f"""Translate the following Ragnarok Online {context} from English to Chinese.
Rules:
- Output one translation per line, matching input order exactly
- Keep # at end of each line if present
- Keep %s, %d, %lu, %u, %ld format specifiers unchanged
- Keep color codes like ^xxxxxx unchanged
- Game terms: Zeny=金币, Kafra=卡普拉, Prontera=普隆德拉, Geffen=吉芬, Payon=裴扬
- Use GBK-compatible characters only
- If a line is just a symbol or number, keep it as-is

Input ({len(texts)} lines):
"""
    for i, t in enumerate(texts):
        prompt += f"{i+1}. {t}\n"

    data = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.3
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    req = urllib.request.Request(url, headers=headers, data=data)
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    content = result["choices"][0]["message"]["content"]

    lines = []
    for line in content.strip().split("\n"):
        line = line.strip()
        line = re.sub(r'^\d+\.\s*', '', line)
        if line:
            lines.append(line)
    return lines

def translate_file(input_path, output_path, context, batch_size=30):
    with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    translatable = []
    indices = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and stripped != '#' and not stripped.startswith('//') and len(stripped) > 1:
            translatable.append(stripped)
            indices.append(i)

    print(f"Total lines: {len(lines)}, translatable: {len(translatable)}")

    translated = [''] * len(translatable)
    for batch_start in range(0, len(translatable), batch_size):
        batch_end = min(batch_start + batch_size, len(translatable))
        batch = translatable[batch_start:batch_end]
        print(f"  Translating {batch_start+1}-{batch_end}/{len(translatable)}...")
        try:
            results = translate_batch(batch, context)
            for j, r in enumerate(results):
                if batch_start + j < len(translated):
                    translated[batch_start + j] = r
        except Exception as e:
            print(f"  ERROR: {e}, keeping original for this batch")
            for j in range(len(batch)):
                if batch_start + j < len(translated):
                    translated[batch_start + j] = batch[j]

    output_lines = list(lines)
    for i, idx in enumerate(indices):
        if translated[i]:
            output_lines[idx] = translated[i] + '\n'

    with open(output_path, 'w', encoding='gbk', errors='replace') as f:
        f.writelines(output_lines)
    print(f"Written to {output_path} (GBK)")

print("=== Translating msgstringtable.txt ===")
translate_file(
    r"D:\rag\data\msgstringtable.txt",
    r"D:\rag\data\msgstringtable.txt",
    "system messages",
    batch_size=40
)

print("\n=== Translating mapnametable.txt ===")
translate_file(
    r"D:\rag\data\mapnametable.txt",
    r"D:\rag\data\mapnametable.txt",
    "map/location names",
    batch_size=40
)

print("\nDone!")
