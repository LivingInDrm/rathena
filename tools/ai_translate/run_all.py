#!/usr/bin/env python3
"""
Run AI translation pipeline for ALL untranslated NPC directories.
Processes one directory at a time for better error recovery.
Reads API key from api_config.txt.
"""

import os
import sys
import traceback
from pathlib import Path

RATHENA_ROOT = Path(__file__).resolve().parent.parent.parent

# Read API config
config_path = Path(__file__).resolve().parent / "api_config.txt"
with open(config_path, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ai_translate.pipeline import run_pipeline

# Directories ordered from smallest to largest
DIRS_TO_TRANSLATE = [
    "battleground",   # 8 texts
    "instances",      # 14 texts
    "cities",         # 28 texts
    "merchants",      # 115 texts
    "custom",         # 1024 texts
    "events",         # 2053 texts
    "other",          # 2269 texts
    "pre-re",         # 4006 texts
    "jobs",           # 5408 texts
    "re",             # 7253 texts
    "quests",         # 50093 texts
]

completed = []
failed = []

for dir_name in DIRS_TO_TRANSLATE:
    log_file = RATHENA_ROOT / "tmp" / f"ai_translate_{dir_name.replace('/', '_')}.log"
    log_fh = open(log_file, 'w', encoding='utf-8', buffering=1)
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = log_fh
    sys.stderr = log_fh

    try:
        run_pipeline(
            dirs=[dir_name],
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            rpm=30,
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            dry_run=False,
            validate_only=False,
            skip_translated=True,
            no_backup=False,
            auto_apply=True,
        )
        print(f"=== {dir_name} COMPLETED ===", flush=True)
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        log_fh.close()
        completed.append(dir_name)
        print(f"[OK] {dir_name} completed. Log: {log_file}")
    except Exception as e:
        traceback.print_exc()
        print(f"=== {dir_name} FAILED: {e} ===", flush=True)
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        log_fh.close()
        failed.append((dir_name, str(e)))
        print(f"[FAIL] {dir_name}: {e}. Log: {log_file}")

print(f"\n=== SUMMARY ===")
print(f"Completed: {len(completed)} - {', '.join(completed)}")
print(f"Failed: {len(failed)} - {', '.join(d for d,_ in failed)}")
if failed:
    for d, e in failed:
        print(f"  {d}: {e}")
