#!/usr/bin/env python3
"""Wrapper to run AI translation pipeline for pre-re directory."""

import os
import sys
import traceback
from pathlib import Path

RATHENA_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_FILE = RATHENA_ROOT / "tmp" / "ai_translate_pre_re.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Read API config first (before redirecting output)
config_path = Path(__file__).resolve().parent / "api_config.txt"
with open(config_path, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

# Redirect stdout/stderr to log file
log_fh = open(LOG_FILE, 'w', encoding='utf-8', buffering=1)  # line-buffered
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = log_fh
sys.stderr = log_fh

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ai_translate.pipeline import run_pipeline

    run_pipeline(
        dirs=["pre-re"],
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
    print("=== PIPELINE COMPLETED SUCCESSFULLY ===", flush=True)
except Exception:
    traceback.print_exc()
    print("=== PIPELINE FAILED ===", flush=True)
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    log_fh.close()
    sys.exit(1)
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    log_fh.close()
