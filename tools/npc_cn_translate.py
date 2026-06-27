#!/usr/bin/env python3
"""
rAthena NPC Chinese Translation Tool
=====================================
Safely applies Chinese NPC dialogue from najoast/rathena_npc_translate to the
CURRENT rAthena NPC files, preserving all structural content (NPC positions,
sprite IDs, game logic) from the current version.

Key design decisions:
  - NEVER overwrite NPC coordinates/sprites/logic (version compat)
  - Only replace mes"..." and select("...") dialogue strings
  - Output in GBK encoding (required by RO client display)
  - Match NPC blocks by ::label (exact) or sequential position (fallback)
  - Backup originals before modifying
  - pre-re/cities/ reuses cities/ translations (same NPCs, different era)

Usage:
    python npc_cn_translate.py [--dry-run] [--no-backup] [--force-download]

Options:
    --dry-run         Show what would be changed without writing files
    --no-backup       Skip backing up original files
    --force-download  Re-download CN translation zip even if cache exists

Coverage (najoast/rathena_npc_translate zh-CN/npc/):
    cities, airports, battleground, events, guild, guild2, instances,
    jobs, kafras, merchants, mobs, other, quests, warps, custom,
    pre-re/{airports,guides,jobs,kafras,merchants,mobs,other,quests,warps},
    re/{airports,guides,guild,instances,jobs,kafras,merchants,mobs,other,quests,warps,custom}
"""

import re
import os
import sys
import shutil
import urllib.request
import urllib.error
import zipfile
import io
from pathlib import Path
from typing import Optional

# ─── Configuration ──────────────────────────────────────────────────────────

GITHUB_BASE  = "https://raw.githubusercontent.com/najoast/rathena_npc_translate/master/zh-CN/npc/"
GITHUB_ZIP   = "https://github.com/najoast/rathena_npc_translate/archive/refs/heads/master.zip"
RATHENA_NPC  = Path(r"D:\Projects\rathena\npc")
BACKUP_DIR   = Path(r"D:\Projects\rathena\npc_backup_en")
CN_CACHE_DIR = Path(r"D:\Projects\rathena\tmp\cn_cache")

# In-memory cache populated by download_repo_zip()
_CN_CACHE: dict = {}   # cn_relative_path -> str content

# (english_relative_path, chinese_relative_path)
# english path is relative to RATHENA_NPC
# chinese path is relative to GITHUB_BASE
FILE_MAPPINGS = []

def build_file_mappings():
    global FILE_MAPPINGS
    mappings = []

    def add_dir(en_dir, cn_dir):
        en_path = RATHENA_NPC / en_dir
        if not en_path.exists():
            return
        for f in sorted(en_path.rglob("*.txt")):
            rel = f.relative_to(RATHENA_NPC / en_dir)
            cn_rel = (Path(cn_dir) / rel).as_posix()
            en_rel = str(Path(en_dir) / rel)
            mappings.append((en_rel, cn_rel))

    # ── Shared (non-RE) directories ──────────────────────────────────────────
    add_dir("cities",        "cities")
    add_dir("airports",      "airports")
    add_dir("battleground",  "battleground")
    add_dir("events",        "events")
    add_dir("guild",         "guild")
    add_dir("guild2",        "guild2")
    add_dir("instances",     "instances")
    add_dir("jobs",          "jobs")
    add_dir("kafras",        "kafras")
    add_dir("merchants",     "merchants")
    add_dir("mobs",          "mobs")
    add_dir("other",         "other")
    add_dir("quests",        "quests")
    add_dir("warps",         "warps")
    add_dir("custom",        "custom")

    # ── pre-re directories ────────────────────────────────────────────────────
    # pre-re/cities → reuse cities/ translations
    add_dir("pre-re/cities",     "cities")
    add_dir("pre-re/airports",   "pre-re/airports")
    add_dir("pre-re/guides",     "pre-re/guides")
    add_dir("pre-re/jobs",       "pre-re/jobs")
    add_dir("pre-re/kafras",     "pre-re/kafras")
    add_dir("pre-re/merchants",  "pre-re/merchants")
    add_dir("pre-re/mobs",       "pre-re/mobs")
    add_dir("pre-re/other",      "pre-re/other")
    add_dir("pre-re/quests",     "pre-re/quests")
    add_dir("pre-re/warps",      "pre-re/warps")

    # ── re/ directories ───────────────────────────────────────────────────────
    # re/cities → reuse cities/ translations
    add_dir("re/cities",         "cities")
    add_dir("re/airports",       "re/airports")
    add_dir("re/guides",         "re/guides")
    add_dir("re/guild",          "re/guild")
    add_dir("re/instances",      "re/instances")
    add_dir("re/jobs",           "re/jobs")
    add_dir("re/kafras",         "re/kafras")
    add_dir("re/merchants",      "re/merchants")
    add_dir("re/mobs",           "re/mobs")
    add_dir("re/other",          "re/other")
    add_dir("re/quests",         "re/quests")
    add_dir("re/warps",          "re/warps")
    add_dir("re/custom",         "re/custom")

    FILE_MAPPINGS = mappings

# ─── NPC Script Parser ───────────────────────────────────────────────────────

# Matches: optional_map_coords  script  NPCName::label  sprite[,w,h],{
# Group 1: full NPC name (e.g. Guard#pront::prtguard)
# Handles sprite formats: 105,{ and 45,1,1,{ (custom size NPCs)
NPC_SCRIPT_RE = re.compile(
    r'^(?:[^\s,]+(?:,[^\s,]+){3}|-)\s+script\s+(\S+)\s+[-\d]+(?:,[-\d]+)*\s*,\s*\{',
    re.MULTILINE
)

# mes "string"  OR  mes "[name]"
MES_RE   = re.compile(r'^(\s*mes\s+)"([^"]*)"(;.*)?$')
# select("opt1:opt2")  —  the whole option string in one arg
SELECT_RE = re.compile(r'(\bselect\s*\(\s*")((?:[^"\\]|\\.)*?)(")')
# input prompt: input .@v, 0, 100; — no translatable string usually
# caption (NPC window title): caption "Name"; — treat like mes
CAPTION_RE = re.compile(r'^(\s*caption\s+)"([^"]*)"(;.*)?$')


def _strip_line_comment(line: str) -> str:
    """Remove // line comment, being careful of strings."""
    in_str = False
    i = 0
    while i < len(line):
        c = line[i]
        if c == '"':
            in_str = not in_str
        elif not in_str and c == '/' and i + 1 < len(line) and line[i+1] == '/':
            return line[:i]
        i += 1
    return line


def _count_braces(line: str) -> int:
    """Count net brace delta (open - close) in a line, ignoring strings and comments."""
    line = _strip_line_comment(line)
    delta = 0
    in_str = False
    for c in line:
        if c == '"':
            in_str = not in_str
        elif not in_str:
            if c == '{':
                delta += 1
            elif c == '}':
                delta -= 1
    return delta


class NpcBlock:
    """Represents a parsed NPC script block."""
    def __init__(self, ident: str, pos_idx: int, start: int, end: int,
                 mes_list: list, select_list: list, caption_list: list):
        self.ident       = ident        # ::label string, or None
        self.pos_idx     = pos_idx      # sequential index among non-labeled blocks
        self.start       = start        # inclusive line index in file
        self.end         = end          # inclusive line index in file
        self.mes_list    = mes_list     # ordered list of mes string values
        self.select_list = select_list  # ordered list of select option strings
        self.caption_list= caption_list

    def key(self):
        return self.ident if self.ident else ('pos', self.pos_idx)


def parse_blocks(content: str) -> list:
    """Parse content into NpcBlock list."""
    lines = content.splitlines()
    blocks = []
    pos_counter = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        m = NPC_SCRIPT_RE.match(line)
        if m:
            npc_name = m.group(1)
            # Extract identifier
            if '::' in npc_name:
                ident = '::' + npc_name.split('::')[1]
            else:
                ident = None

            # Scan to find closing brace
            depth = _count_braces(line)
            start = i
            mes_list     = []
            select_list  = []
            caption_list = []

            # depth==0 after first line means inline empty block {} on same line
            # Most blocks span multiple lines; depth should be >0 after opening line
            while i < len(lines):
                l = lines[i]
                # Extract mes
                mm = MES_RE.match(l)
                if mm:
                    mes_list.append(mm.group(2))
                # Extract caption
                cm = CAPTION_RE.match(l)
                if cm:
                    caption_list.append(cm.group(2))
                # Extract select
                sm = SELECT_RE.search(l)
                if sm:
                    select_list.append(sm.group(2))
                if i > start:
                    depth += _count_braces(l)
                i += 1
                if depth <= 0:
                    break

            blocks.append(NpcBlock(
                ident=ident,
                pos_idx=pos_counter,
                start=start,
                end=i - 1,
                mes_list=mes_list,
                select_list=select_list,
                caption_list=caption_list,
            ))
            if ident is None:
                pos_counter += 1
        else:
            i += 1

    return blocks


# ─── Translation Engine ──────────────────────────────────────────────────────

def build_cn_lookup(cn_blocks: list) -> tuple:
    """Returns (label_map, pos_list).
    label_map: {::label -> NpcBlock}
    pos_list:  [NpcBlock, ...] for blocks without ::label (in order)
    """
    label_map = {}
    pos_list  = []
    for blk in cn_blocks:
        if blk.ident:
            label_map[blk.ident] = blk
        else:
            pos_list.append(blk)
    return label_map, pos_list


def apply_translation(en_content: str, cn_content: str) -> tuple:
    """
    Apply Chinese mes/select/caption to English structure.
    Returns (translated_str, stats_dict).
    """
    en_lines  = en_content.splitlines(keepends=False)
    en_blocks = parse_blocks(en_content)
    cn_blocks = parse_blocks(cn_content)

    label_map, pos_list = build_cn_lookup(cn_blocks)

    result = list(en_lines)
    stats  = {'blocks_matched': 0, 'mes_replaced': 0,
              'select_replaced': 0, 'caption_replaced': 0,
              'blocks_skipped': 0}
    pos_counter = 0

    for en_blk in en_blocks:
        # Find matching Chinese block
        if en_blk.ident and en_blk.ident in label_map:
            cn_blk = label_map[en_blk.ident]
        elif en_blk.ident is None:
            if pos_counter < len(pos_list):
                cn_blk = pos_list[pos_counter]
                pos_counter += 1
            else:
                pos_counter += 1
                stats['blocks_skipped'] += 1
                continue
        else:
            # Labeled block but no Chinese counterpart
            stats['blocks_skipped'] += 1
            continue

        stats['blocks_matched'] += 1

        # Replace mes strings
        cn_mes_q      = list(cn_blk.mes_list)
        cn_select_q   = list(cn_blk.select_list)
        cn_caption_q  = list(cn_blk.caption_list)

        for i in range(en_blk.start, en_blk.end + 1):
            line = result[i]

            # mes replacement
            mm = MES_RE.match(line)
            if mm:
                if cn_mes_q:
                    cn_text = cn_mes_q.pop(0)
                    result[i] = mm.group(1) + '"' + cn_text + '"' + (mm.group(3) or ';')
                    stats['mes_replaced'] += 1
                continue

            # caption replacement
            cm = CAPTION_RE.match(line)
            if cm:
                if cn_caption_q:
                    cn_text = cn_caption_q.pop(0)
                    result[i] = cm.group(1) + '"' + cn_text + '"' + (cm.group(3) or ';')
                    stats['caption_replaced'] += 1
                continue

            # select replacement (may appear inside if/switch)
            sm = SELECT_RE.search(line)
            if sm:
                if cn_select_q:
                    cn_opts = cn_select_q.pop(0)
                    result[i] = line[:sm.start(1)] + sm.group(1) + cn_opts + sm.group(3) + line[sm.end():]
                    stats['select_replaced'] += 1

    return '\n'.join(result), stats


# ─── File I/O ─────────────────────────────────────────────────────────────────

def download_repo_zip(force: bool = False):
    """Download the entire najoast repo as a zip and populate _CN_CACHE.
    Uses CN_CACHE_DIR as a disk cache so subsequent runs are instant.
    Set force=True to re-download even if cache exists.
    """
    global _CN_CACHE
    marker = CN_CACHE_DIR / ".done"

    if not force and marker.exists():
        # Load from disk cache
        print("  Loading CN translations from disk cache...")
        count = 0
        for f in CN_CACHE_DIR.rglob("*.txt"):
            rel = f.relative_to(CN_CACHE_DIR).as_posix()
            try:
                _CN_CACHE[rel] = f.read_text(encoding='utf-8')
                count += 1
            except Exception:
                pass
        print(f"  Loaded {count} cached files.")
        return

    print(f"  Downloading CN translation repo zip from GitHub...")
    CN_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        req = urllib.request.Request(GITHUB_ZIP, headers={'User-Agent': 'rAthena-translate/1.0'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except Exception as e:
        print(f"  ERROR downloading zip: {e}")
        print("  Falling back to per-file HTTP fetching.")
        return

    print(f"  Downloaded {len(data)//1024} KB, extracting...")
    count = 0
    prefix = "rathena_npc_translate-master/zh-CN/npc/"
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if name.startswith(prefix) and name.endswith('.txt'):
                rel = name[len(prefix):]
                if not rel:
                    continue
                raw = zf.read(name)
                try:
                    content = raw.decode('utf-8-sig')
                except UnicodeDecodeError:
                    content = raw.decode('latin-1')
                _CN_CACHE[rel] = content
                # Write to disk cache
                dst = CN_CACHE_DIR / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(content, encoding='utf-8')
                count += 1

    marker.write_text("ok")
    print(f"  Extracted {count} CN translation files to cache.")


def fetch_cn_file(cn_relative: str) -> Optional[str]:
    """Return Chinese translation file content (UTF-8 string).
    Uses in-memory cache if available, otherwise falls back to HTTP.
    """
    # Normalize path separators
    key = cn_relative.replace('\\', '/')
    if key in _CN_CACHE:
        return _CN_CACHE[key]

    # Fallback: per-file HTTP fetch (used when zip download failed)
    url = GITHUB_BASE + key
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'rAthena-translate/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return raw.decode('utf-8-sig')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"    HTTP {e.code} fetching {url}")
        return None
    except Exception as e:
        print(f"    Error fetching {url}: {e}")
        return None


def backup_file(src: Path):
    """Copy src to BACKUP_DIR preserving relative path structure."""
    rel = src.relative_to(RATHENA_NPC)
    dst = BACKUP_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():  # don't overwrite existing backup
        shutil.copy2(src, dst)


def write_gbk(path: Path, content: str):
    """Write content to path in GBK encoding with Unix line endings."""
    encoded = content.encode('gbk', errors='replace')
    path.write_bytes(encoded)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    dry_run        = '--dry-run'        in sys.argv
    no_backup      = '--no-backup'      in sys.argv
    force_download = '--force-download' in sys.argv

    build_file_mappings()

    print(f"rAthena NPC Chinese Translation Tool")
    print(f"  NPC dir:  {RATHENA_NPC}")
    print(f"  Backup:   {BACKUP_DIR}")
    print(f"  Dry run:  {dry_run}")
    print(f"  Total mappings: {len(FILE_MAPPINGS)}")
    print()

    # Download / load CN translation cache (one zip instead of 928 HTTP requests)
    download_repo_zip(force=force_download)
    print()

    total_files  = 0
    ok_files     = 0
    skip_files   = 0
    total_mes    = 0
    total_select = 0

    for en_rel, cn_rel in FILE_MAPPINGS:
        en_path = RATHENA_NPC / en_rel
        if not en_path.exists():
            continue

        print(f"[{en_rel}]")

        # Fetch Chinese translation
        cn_content = fetch_cn_file(cn_rel)
        if cn_content is None:
            print(f"  -> No Chinese translation found, skipping.")
            skip_files += 1
            continue

        # Read English file (try UTF-8 first, fall back to latin-1)
        try:
            en_content = en_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            en_content = en_path.read_text(encoding='latin-1')

        # Apply translation
        translated, stats = apply_translation(en_content, cn_content)

        print(f"  matched={stats['blocks_matched']} skipped={stats['blocks_skipped']} "
              f"mes={stats['mes_replaced']} select={stats['select_replaced']} "
              f"caption={stats['caption_replaced']}")

        if not dry_run:
            if not no_backup:
                backup_file(en_path)
            write_gbk(en_path, translated)
            print(f"  -> Written (GBK)")
        else:
            print(f"  -> Dry run, not written")

        total_files  += 1
        ok_files     += 1
        total_mes    += stats['mes_replaced']
        total_select += stats['select_replaced']

    print()
    print(f"=== Summary ===")
    print(f"  Files processed: {ok_files}")
    print(f"  Files skipped:   {skip_files}")
    print(f"  mes replaced:    {total_mes}")
    print(f"  select replaced: {total_select}")
    if not dry_run:
        print(f"  Backups in:      {BACKUP_DIR}")


if __name__ == '__main__':
    main()
