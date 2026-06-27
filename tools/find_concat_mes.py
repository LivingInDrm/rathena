import re
from pathlib import Path

MES_RE = re.compile(r'^(\s*mes\s+)"([^"]*)"(;.*)?$')
backup = Path(r"D:\Projects\rathena\npc_backup_en\re\jobs")

for f in sorted(backup.rglob("*.txt")):
    content = f.read_text(encoding="utf-8")
    for i, line in enumerate(content.splitlines()):
        stripped = line.strip()
        if stripped.startswith("mes ") and '"' in stripped and not MES_RE.match(line):
            rel = f.relative_to(backup)
            print(f"{rel}:{i+1}: {stripped[:120]}")
