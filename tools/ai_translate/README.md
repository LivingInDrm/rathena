# rAthena NPC AI Translation Toolchain

AI-powered translation pipeline for rAthena NPC dialogue files. Extracts untranslated text, translates via OpenAI API, validates quality, and applies translations with GBK encoding.

## Prerequisites

- Python 3.8+
- OpenAI API key (set `OPENAI_API_KEY` environment variable)
- No additional pip packages required (uses only Python standard library + OpenAI REST API)

## Quick Start

```bash
# Set API key
set OPENAI_API_KEY=sk-your-key-here

# Translate a specific directory (e.g., jobs)
python tools/ai_translate/pipeline.py --dir jobs

# Dry run (no API calls, no file writes)
python tools/ai_translate/pipeline.py --dir quests --dry-run

# Translate all untranslated directories
python tools/ai_translate/pipeline.py --all

# Only validate existing translations
python tools/ai_translate/pipeline.py --dir jobs --validate-only
```

## Pipeline Steps

```
extract → translate → validate → apply
```

### 1. Extract (`extract.py`)

Scans NPC files and extracts untranslated `mes`/`select`/`caption` text into JSON task files.

```bash
python tools/ai_translate/extract.py --dir quests
python tools/ai_translate/extract.py --all
```

Output: `tmp/ai_translate/tasks/<dir>.json`

### 2. Translate (`translate.py`)

Sends extracted text to OpenAI API for translation. Supports batch processing, rate limiting, retry, and resume.

```bash
python tools/ai_translate/translate.py --input tmp/ai_translate/tasks/quests.json
python tools/ai_translate/translate.py --input tmp/ai_translate/tasks/quests.json --model gpt-4o-mini --rpm 30
```

Output: `tmp/ai_translate/results/<dir>.json`

Features:
- **Batch translation**: Sends one NPC block at a time for context coherence
- **Resume support**: Skips already-translated blocks on re-run
- **Checkpoint saves**: Saves progress every 5 files for crash recovery
- **Rate limiting**: Configurable RPM (requests per minute)
- **Retry**: 3 retries with exponential backoff

### 3. Validate (`validate.py`)

Multi-dimensional quality checks on translation results.

```bash
python tools/ai_translate/validate.py --input tmp/ai_translate/results/quests.json
python tools/ai_translate/validate.py --input tmp/ai_translate/results/quests.json --errors-only
```

Checks:
- **GBK encoding**: All text must be GBK-encodable (RO client requirement)
- **Color codes**: `^RRGGBB` codes must be preserved
- **Select separators**: `:` count must match original (option count unchanged)
- **Empty translation**: No empty/whitespace-only results
- **Length ratio**: Flags translations >3x or <0.1x original length
- **Script references**: Variables/functions must be preserved
- **Chinese presence**: Warns if translation contains no Chinese characters

Output: `tmp/ai_translate/reports/<dir>_report.json`

### 4. Apply (`apply.py`)

Writes translated text back into NPC files with GBK encoding.

```bash
python tools/ai_translate/apply.py --input tmp/ai_translate/results/quests.json
python tools/ai_translate/apply.py --input tmp/ai_translate/results/quests.json --dry-run
```

Safety guarantees (same as `npc_cn_translate.py`):
- Never modifies NPC coordinates, sprite IDs, or script logic
- Only replaces `mes "..."`, `select("...")`, `caption "..."` string content
- Outputs GBK encoding with Unix line endings
- Backs up originals to `npc_backup_en/`

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_BASE_URL` | No | Custom API base URL (for proxies/compatible APIs) |

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | `gpt-4o-mini` | OpenAI model to use |
| `--rpm` | `20` | Max API requests per minute |
| `--dry-run` | off | Preview mode, no API calls or file writes |
| `--validate-only` | off | Only validate existing results |
| `--no-backup` | off | Skip backing up original files |
| `--auto-apply` | off | Apply even if validation has errors |
| `--include-translated` | off | Re-translate files that already have Chinese |
| `--base-url` | OpenAI | Custom API endpoint |

## Glossary

`glossary.json` contains RO-specific terminology mappings:
- **Cities**: Prontera→普隆德拉, Geffen→吉芬, Payon→斐扬...
- **Jobs**: Knight→骑士, Wizard→巫师, Hunter→猎人...
- **NPCs**: Kafra→卡普拉, Guard→卫兵...
- **Items**: Zeny→金币, Red Potion→红色药水...
- **Game terms**: Base Level→基本等级, Guild→公会...
- **UI phrases**: Yes→是, No→否, Cancel→取消...

Edit `glossary.json` to add/modify terminology.

## File Structure

```
tools/ai_translate/
├── __init__.py          # Package init
├── extract.py           # Text extractor
├── translate.py         # AI translator
├── apply.py             # Translation applier
├── validate.py          # Quality validator
├── pipeline.py          # Full pipeline orchestrator
├── glossary.json        # RO terminology glossary
└── README.md            # This file

tmp/ai_translate/        # Runtime data (gitignored)
├── tasks/               # Extracted text (JSON)
├── results/             # Translation results (JSON)
└── reports/             # Validation reports (JSON)
```

## Design Decisions

- **Reuses `npc_cn_translate.py` parser**: Proven NPC block parser, avoids duplication
- **JSON intermediate format**: Structured, supports resume/checkpoint, easy to inspect
- **Per-block translation**: Maintains dialogue context coherence
- **GBK output**: Hard requirement from RO client
- **No pip dependencies**: Uses only Python stdlib + OpenAI REST API via urllib
