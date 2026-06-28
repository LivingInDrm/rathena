import os

npc_dir = r"D:\Projects\rathena\npc"
dry_run = []
chinese = []
english = []

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
            dry_run.append(path)
        elif any(b > 0x80 for b in data[:3000]):
            chinese.append(path)
        else:
            english.append(path)

print(f"DRY-RUN files: {len(dry_run)}")
print(f"Chinese files: {len(chinese)}")
print(f"English-only files: {len(english)}")
print()
print("=== DRY-RUN files ===")
for f in dry_run[:30]:
    print(f"  {os.path.relpath(f, npc_dir)}")
if len(dry_run) > 30:
    print(f"  ... and {len(dry_run)-30} more")
