import urllib.request
import urllib.error
import json
import os
from pathlib import Path

# Load API key from config file
config_path = Path(__file__).resolve().parent / "ai_translate" / "api_config.txt"
if config_path.exists():
    for line in config_path.read_text().strip().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

API_KEY = os.environ.get("OPENAI_API_KEY", "")
print(f"API key length: {len(API_KEY)}")
print(f"API key prefix: {API_KEY[:15]}...")

url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}
data = json.dumps({
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Translate to Chinese: Hello adventurer, welcome to Prontera."}],
    "max_tokens": 50
}).encode()

try:
    req = urllib.request.Request(url, headers=headers, data=data)
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    print("SUCCESS!")
    print("Response:", result["choices"][0]["message"]["content"])
    print("Model:", result["model"])
    print("Tokens used:", result["usage"])
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print(f"HTTP ERROR {e.code}: {body[:300]}")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
