#!/usr/bin/env python3
"""Run AI translation pipeline for job change quest NPC scripts."""
import os
import sys
from pathlib import Path

RATHENA_ROOT = Path(__file__).resolve().parent.parent

# Read API config
config_file = RATHENA_ROOT / "tools" / "ai_translate" / "api_config.txt"
with open(config_file, 'r') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

# Add tools dir to path
sys.path.insert(0, str(RATHENA_ROOT / "tools"))

from ai_translate.pipeline import run_pipeline

# Directories to translate
job_dirs = sys.argv[1:] if len(sys.argv) > 1 else ["jobs", "pre-re/jobs", "re/jobs"]

model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

run_pipeline(
    dirs=job_dirs,
    model=model,
    rpm=20,
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    dry_run=False,
    validate_only=False,
    skip_translated=True,
    no_backup=False,
    auto_apply=True,
)
