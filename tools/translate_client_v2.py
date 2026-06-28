import urllib.request
import json
import re
import time

API_KEY = ""
with open(r"D:\Projects\rathena\tools\ai_translate\api_config.txt") as f:
    for line in f:
        if line.startswith("OPENAI_API_KEY="):
            API_KEY = line.strip().split("=", 1)[1]

def call_api(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    data = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": "You are a Ragnarok Online game translator. Translate English to Simplified Chinese. Output ONLY the translations, one per line, numbered to match input. Keep format specifiers (%s,%d,%u,%lu,%ld), color codes (^xxxxxx), and # at end of lines unchanged."},
                     {"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.2
    }).encode()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers, data=data)
            resp = urllib.request.urlopen(req, timeout=120)
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"    Retry {attempt+1}: {e}")
            time.sleep(5)
    raise RuntimeError("API failed after 3 retries")

def parse_response(content, count):
    lines = []
    for line in content.strip().split("\n"):
        line = line.strip()
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        if line:
            lines.append(line)
    while len(lines) < count:
        lines.append("")
    return lines[:count]

def translate_file(path, context, batch_size=50):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Find translatable lines (has English letters, not comments)
    to_translate = []
    for i, line in enumerate(lines):
        s = line.strip()
        if s and not s.startswith('//') and re.search(r'[a-zA-Z]{2,}', s) and s != '#':
            to_translate.append((i, s))

    print(f"  {path}: {len(lines)} total, {len(to_translate)} to translate")

    results = {}
    for batch_start in range(0, len(to_translate), batch_size):
        batch = to_translate[batch_start:batch_start+batch_size]
        prompt = f"Translate these {context} to Chinese (keep # at line end, keep %s/%d etc):\n"
        for j, (idx, text) in enumerate(batch):
            prompt += f"{j+1}. {text}\n"

        print(f"  Batch {batch_start//batch_size+1}/{(len(to_translate)+batch_size-1)//batch_size} ({len(batch)} lines)...")
        try:
            content = call_api(prompt)
            translated = parse_response(content, len(batch))
            for j, (idx, _) in enumerate(batch):
                if translated[j]:
                    results[idx] = translated[j] + '\n'
        except Exception as e:
            print(f"  ERROR: {e}")
        time.sleep(0.5)

    for idx, text in results.items():
        lines[idx] = text

    with open(path, 'w', encoding='gbk', errors='replace') as f:
        f.writelines(lines)
    print(f"  Written (GBK), {len(results)} lines translated")

print("=== msgstringtable.txt ===")
translate_file(r"D:\rag\data\msgstringtable.txt", "Ragnarok Online system messages")
print("\n=== mapnametable.txt ===")
translate_file(r"D:\rag\data\mapnametable.txt", "Ragnarok Online map names")
print("\nAll done!")
