#!/usr/bin/env python3
"""Run EP13.2 AI translation pipeline - minimal version."""
import os
import sys
import json
import traceback
from pathlib import Path

RATHENA_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = RATHENA_ROOT / "tmp" / "ep13_translate.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Open log file
logf = open(str(LOG_FILE), 'w', encoding='utf-8', buffering=1)

def log(msg):
    logf.write(str(msg) + '\n')
    logf.flush()

sys.path.insert(0, str(RATHENA_ROOT / "tools"))

# Load API key from config
config_path = RATHENA_ROOT / "tools" / "ai_translate" / "api_config.txt"
for line in config_path.read_text().strip().splitlines():
    if "=" in line:
        key, val = line.strip().split("=", 1)
        os.environ[key] = val

log(f"API key loaded: {'yes' if os.environ.get('OPENAI_API_KEY') else 'no'}")

from ai_translate.translate import (
    translate_batch, load_glossary, build_glossary_prompt,
    SYSTEM_PROMPT_TEMPLATE, MAX_TEXTS_PER_BATCH
)
import time

api_key = os.environ["OPENAI_API_KEY"]
model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

glossary = load_glossary()
glossary_text = build_glossary_prompt(glossary)
system_prompt = SYSTEM_PROMPT_TEMPLATE.format(glossary=glossary_text)

TASKS_DIR = RATHENA_ROOT / "tmp" / "ai_translate" / "tasks"
RESULTS_DIR = RATHENA_ROOT / "tmp" / "ai_translate" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

rpm = 20
min_interval = 60.0 / rpm

task_files = [
    ("ep13_quests.json", "ep13_quests.json"),
    ("ep13_instances.json", "ep13_instances.json"),
]

for task_name, result_name in task_files:
    task_path = TASKS_DIR / task_name
    result_path = RESULTS_DIR / result_name
    
    if not task_path.exists():
        log(f"SKIP: {task_path} not found")
        continue
    
    log(f"=== Translating: {task_name} ===")
    
    with open(task_path, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    # Load existing results for resume
    existing_results = {}
    if result_path.exists():
        with open(result_path, 'r', encoding='utf-8') as f:
            for t in json.load(f):
                existing_results[t["source_file"]] = t
    
    results = []
    total_api_calls = 0
    last_call_time = 0
    
    for task_idx, task in enumerate(tasks):
        source_file = task["source_file"]
        log(f"  [{task_idx+1}/{len(tasks)}] {source_file}")
        
        # Resume support
        if source_file in existing_results:
            existing_task = existing_results[source_file]
            all_done = all(
                "translated" in t
                for blk in existing_task.get("npc_blocks", [])
                for t in blk.get("texts", [])
            )
            if all_done:
                log(f"    -> Already translated, skipping")
                results.append(existing_task)
                continue
        
        result_task = {
            "source_file": source_file,
            "total_blocks": task["total_blocks"],
            "total_texts": task["total_texts"],
            "npc_blocks": [],
        }
        
        for blk in task["npc_blocks"]:
            result_blk = {
                "npc_label": blk["npc_label"],
                "npc_name": blk["npc_name"],
                "block_index": blk["block_index"],
                "line_start": blk["line_start"],
                "line_end": blk["line_end"],
                "texts": [],
            }
            
            originals = [t["original"] for t in blk["texts"]]
            all_translated = []
            
            for batch_start in range(0, len(originals), MAX_TEXTS_PER_BATCH):
                batch = originals[batch_start:batch_start + MAX_TEXTS_PER_BATCH]
                
                # Rate limiting
                now = time.time()
                elapsed = now - last_call_time
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                
                try:
                    translated = translate_batch(
                        batch, model, api_key, base_url, system_prompt)
                    last_call_time = time.time()
                    total_api_calls += 1
                    all_translated.extend(translated)
                    log(f"    API call {total_api_calls}: {len(batch)} texts translated")
                except Exception as ex:
                    log(f"    ERROR in API call: {ex}")
                    traceback.print_exc(file=logf)
                    # Use originals as fallback
                    all_translated.extend(batch)
            
            for i, t in enumerate(blk["texts"]):
                translated_text = all_translated[i] if i < len(all_translated) else t["original"]
                result_blk["texts"].append({**t, "translated": translated_text})
            
            result_task["npc_blocks"].append(result_blk)
        
        results.append(result_task)
        
        # Checkpoint every 5 files
        if (task_idx + 1) % 5 == 0:
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            log(f"    -> Checkpoint saved ({task_idx+1}/{len(tasks)})")
    
    # Final save
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    log(f"  Total API calls: {total_api_calls}")
    log(f"  Results saved to: {result_path}")

log("\n=== All EP13 translations complete ===")
logf.close()
