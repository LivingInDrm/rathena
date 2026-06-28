import os
import shutil

npc_dir = r"D:\Projects\rathena\npc"
backup_dir = r"D:\Projects\rathena\npc_backup_en"
restored = 0
missing = 0

for root, dirs, files in os.walk(npc_dir):
    for f in files:
        if not f.endswith(".txt"):
            continue
        path = os.path.join(root, f)
        try:
            data = open(path, "rb").read()
        except:
            continue
        if b"DRY-RUN" in data:
            rel = os.path.relpath(path, npc_dir)
            backup_path = os.path.join(backup_dir, rel)
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, path)
                restored += 1
            else:
                print(f"  MISSING backup: {rel}")
                missing += 1

print(f"Restored {restored} files from backup")
if missing:
    print(f"Missing backups: {missing}")
