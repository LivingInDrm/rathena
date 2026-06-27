#!/usr/bin/env python3
"""Debug wrapper - print errors to console."""
import os
import sys
import traceback
from pathlib import Path

config_path = Path(__file__).resolve().parent / "api_config.txt"
print(f"Config path: {config_path}")
print(f"Config exists: {config_path.exists()}")

with open(config_path, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()
            print(f"Set {key.strip()} = {value.strip()[:10]}...")

print(f"OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")
print(f"OPENAI_MODEL: {os.environ.get('OPENAI_MODEL', 'not set')}")

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ai_translate.extract import extract_directory, RATHENA_NPC, TRANSLATABLE_DIRS
    print(f"Import OK, NPC dir: {RATHENA_NPC}")
    print(f"NPC dir exists: {RATHENA_NPC.exists()}")
except Exception:
    traceback.print_exc()
