#!/usr/bin/env python3
"""
NPC AI Translation Pipeline
=============================
One-command pipeline: extract → translate → validate → apply.

Usage:
    python tools/ai_translate/pipeline.py --dir quests --dry-run
    python tools/ai_translate/pipeline.py --dir jobs --model gpt-4o-mini
    python tools/ai_translate/pipeline.py --all --validate-only

Environment:
    OPENAI_API_KEY  - Required for translation (not needed for extract/validate-only).
    OPENAI_BASE_URL - Optional. Custom API base URL.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add tools dir to path
TOOLS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))

from ai_translate.extract import (
    extract_directory, RATHENA_NPC, TRANSLATABLE_DIRS
)
from ai_translate.translate import translate_task_file, DEFAULT_MODEL, DEFAULT_RPM
from ai_translate.validate import validate_result_file
from ai_translate.apply import apply_result_file

# ─── Configuration ──────────────────────────────────────────────────────────

RATHENA_ROOT = Path(__file__).resolve().parent.parent.parent
TASKS_DIR = RATHENA_ROOT / "tmp" / "ai_translate" / "tasks"
RESULTS_DIR = RATHENA_ROOT / "tmp" / "ai_translate" / "results"
REPORTS_DIR = RATHENA_ROOT / "tmp" / "ai_translate" / "reports"


def run_pipeline(dirs: list, model: str, rpm: int, api_key: str,
                 base_url: str, dry_run: bool = False,
                 validate_only: bool = False, skip_translated: bool = True,
                 no_backup: bool = False, auto_apply: bool = False):
    """Run the full translation pipeline for specified directories."""

    print("=" * 60)
    print("NPC AI Translation Pipeline")
    print("=" * 60)
    print(f"  Directories:    {', '.join(dirs)}")
    print(f"  Model:          {model}")
    print(f"  RPM:            {rpm}")
    print(f"  Dry run:        {dry_run}")
    print(f"  Validate only:  {validate_only}")
    print(f"  Skip translated:{skip_translated}")
    print(f"  Auto apply:     {auto_apply}")
    print()

    all_stats = {
        'extract': {'files': 0, 'texts': 0},
        'translate': {'texts': 0, 'api_calls': 0},
        'validate': {'errors': 0, 'warnings': 0, 'passed': 0},
        'apply': {'files': 0, 'mes': 0, 'select': 0},
    }

    for dir_name in dirs:
        print(f"\n{'='*60}")
        print(f"Processing: {dir_name}")
        print(f"{'='*60}")

        task_file = TASKS_DIR / f"{dir_name.replace('/', '_')}.json"
        result_file = RESULTS_DIR / f"{dir_name.replace('/', '_')}.json"

        # ── Step 1: Extract ──────────────────────────────────────────────
        if not validate_only:
            print(f"\n--- Step 1: Extract ---")
            TASKS_DIR.mkdir(parents=True, exist_ok=True)
            stats = extract_directory(
                dir_name, RATHENA_NPC, TASKS_DIR, skip_translated)
            all_stats['extract']['files'] += stats['files_with_text']
            all_stats['extract']['texts'] += stats['total_texts']

            if stats['files_with_text'] == 0:
                print(f"  No untranslated files found in {dir_name}, skipping.")
                continue

        # ── Step 2: Translate ────────────────────────────────────────────
        if not validate_only:
            if not task_file.exists():
                print(f"  No task file found: {task_file}")
                continue

            print(f"\n--- Step 2: Translate ---")
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            stats = translate_task_file(
                task_file, result_file, model,
                api_key, base_url, rpm, dry_run)
            all_stats['translate']['texts'] += stats['total_translated']
            all_stats['translate']['api_calls'] += stats['total_api_calls']

        # ── Step 3: Validate ─────────────────────────────────────────────
        val_stats = {'errors': 0, 'warnings': 0, 'passed': 0}
        if result_file.exists():
            print(f"\n--- Step 3: Validate ---")
            issues, val_stats = validate_result_file(result_file)
            all_stats['validate']['errors'] += val_stats['errors']
            all_stats['validate']['warnings'] += val_stats['warnings']
            all_stats['validate']['passed'] += val_stats['passed']

            print(f"  Passed: {val_stats['passed']}, "
                  f"Errors: {val_stats['errors']}, "
                  f"Warnings: {val_stats['warnings']}")

            # Save report
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            report_file = REPORTS_DIR / f"{dir_name.replace('/', '_')}_report.json"
            report = {
                "stats": val_stats,
                "issues": [i.to_dict() for i in issues],
            }
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            if val_stats['errors'] > 0:
                print(f"  !! {val_stats['errors']} errors found. "
                      f"Review report: {report_file}")
                if not auto_apply:
                    print(f"  Skipping apply due to validation errors.")
                    continue
        else:
            print(f"  No result file found: {result_file}")
            continue

        # ── Step 4: Apply ────────────────────────────────────────────────
        if not validate_only and (auto_apply or val_stats['errors'] == 0):
            print(f"\n--- Step 4: Apply ---")
            apply_stats = apply_result_file(
                result_file, RATHENA_NPC, dry_run, no_backup)
            all_stats['apply']['files'] += apply_stats['files_processed']
            all_stats['apply']['mes'] += apply_stats['mes_replaced']
            all_stats['apply']['select'] += apply_stats['select_replaced']

    # ── Final Summary ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Pipeline Complete")
    print(f"{'='*60}")
    print(f"  Extract:   {all_stats['extract']['files']} files, "
          f"{all_stats['extract']['texts']} texts")
    print(f"  Translate: {all_stats['translate']['texts']} texts, "
          f"{all_stats['translate']['api_calls']} API calls")
    print(f"  Validate:  {all_stats['validate']['passed']} passed, "
          f"{all_stats['validate']['errors']} errors, "
          f"{all_stats['validate']['warnings']} warnings")
    print(f"  Apply:     {all_stats['apply']['files']} files, "
          f"{all_stats['apply']['mes']} mes, "
          f"{all_stats['apply']['select']} select")


def main():
    parser = argparse.ArgumentParser(description="NPC AI Translation Pipeline")
    parser.add_argument("--dir", type=str, default=None,
                        help="Specific directory to process (e.g., quests, jobs)")
    parser.add_argument("--all", action="store_true",
                        help="Process all translatable directories")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        help=f"OpenAI model (default: {DEFAULT_MODEL})")
    parser.add_argument("--rpm", type=int, default=DEFAULT_RPM,
                        help=f"Max requests per minute (default: {DEFAULT_RPM})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't call API or write files")
    parser.add_argument("--validate-only", action="store_true",
                        help="Only validate existing results, don't translate")
    parser.add_argument("--include-translated", action="store_true",
                        help="Include files that already contain Chinese text")
    parser.add_argument("--no-backup", action="store_true",
                        help="Skip backing up original files")
    parser.add_argument("--auto-apply", action="store_true",
                        help="Apply even if validation has errors")
    parser.add_argument("--base-url", type=str, default=None,
                        help="Custom OpenAI API base URL")
    args = parser.parse_args()

    if args.include_translated:
        skip_translated = False
    else:
        skip_translated = True

    # Determine directories
    if args.dir:
        dirs = [args.dir]
    elif args.all:
        dirs = TRANSLATABLE_DIRS
    else:
        print("ERROR: Specify --dir <name> or --all")
        sys.exit(1)

    # API key
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = (args.base_url or
                os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))

    if not args.dry_run and not args.validate_only and not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("Set it with: set OPENAI_API_KEY=sk-...")
        sys.exit(1)

    run_pipeline(
        dirs=dirs,
        model=args.model,
        rpm=args.rpm,
        api_key=api_key,
        base_url=base_url,
        dry_run=args.dry_run,
        validate_only=args.validate_only,
        skip_translated=skip_translated,
        no_backup=args.no_backup,
        auto_apply=args.auto_apply,
    )


if __name__ == '__main__':
    main()
