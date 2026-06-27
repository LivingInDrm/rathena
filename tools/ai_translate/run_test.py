#!/usr/bin/env python3
"""Test runner: translate battleground only (8 texts) to verify API works."""

import os
import sys
import traceback
from pathlib import Path

RATHENA_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = RATHENA_ROOT / "tmp" / "ai_translate_test.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Read API config
config_path = Path(__file__).resolve().parent / "api_config.txt"
with open(config_path, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

# Print to both console and log
class TeeWriter:
    def __init__(self, *writers):
        self.writers = writers
    def write(self, text):
        for w in self.writers:
            w.write(text)
            w.flush()
    def flush(self):
        for w in self.writers:
            w.flush()

log_fh = open(LOG_FILE, 'w', encoding='utf-8', buffering=1)
tee = TeeWriter(sys.stdout, log_fh)
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = tee
sys.stderr = tee

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ai_translate.pipeline import run_pipeline

    run_pipeline(
        dirs=["battleground"],
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        rpm=30,
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        dry_run=False,
        validate_only=False,
        skip_translated=True,
        no_backup=False,
        auto_apply=False,  # Don't auto-apply, just translate and validate
    )
    print("=== TEST COMPLETED SUCCESSFULLY ===", flush=True)
except Exception:
    traceback.print_exc()
    print("=== TEST FAILED ===", flush=True)
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    log_fh.close()
