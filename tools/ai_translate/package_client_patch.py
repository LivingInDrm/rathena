#!/usr/bin/env python3
"""Package modified external client files into a distributable overlay patch."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def modified_relpaths(backup_dir: Path) -> list[str]:
    rels: set[str] = set()
    if not backup_dir.exists():
        return []
    for backup_root in sorted(path for path in backup_dir.iterdir() if path.is_dir()):
        for path in backup_root.rglob("*"):
            if path.is_file():
                rels.add(str(path.relative_to(backup_root)).replace("/", "\\"))
    return sorted(rels, key=str.lower)


def copy_patch_files(client_dir: Path, backup_dir: Path, output_dir: Path, clean: bool) -> dict:
    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    files_dir = output_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    missing = []
    total_size = 0
    for rel in modified_relpaths(backup_dir):
        source = client_dir / rel
        if not source.exists():
            missing.append(rel)
            continue
        destination = files_dir / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        size = destination.stat().st_size
        total_size += size
        entries.append({"path": rel, "size": size, "sha256": sha256(destination)})

    manifest = {
        "client_dir": str(client_dir),
        "backup_dir": str(backup_dir),
        "file_count": len(entries),
        "missing_count": len(missing),
        "total_size": total_size,
        "files_root": "files",
        "files": entries,
        "missing": missing,
        "install": "Copy the contents of the files directory into the client root, preserving relative paths.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "README.txt").write_text(
        "\n".join(
            [
                "rAthena Chinese localization client overlay",
                "",
                "Install:",
                "1. Close the game client.",
                "2. Copy everything under the files directory into the client root.",
                "3. Keep the directory structure unchanged.",
                "4. Start 2021-11-03_Ragexe_patched.exe.",
                "",
                "The manifest.json file records file paths, sizes, and SHA-256 checksums.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def write_zip(output_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(output_dir.rglob("*")):
            if path == zip_path or not path.is_file():
                continue
            archive.write(path, path.relative_to(output_dir))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-dir", default=r"D:\rag")
    parser.add_argument("--backup-dir", default=r"D:\rag_cn_backup")
    parser.add_argument("--output-dir", default=str(Path("tmp") / "rathena_cn_client_patch"))
    parser.add_argument("--zip", dest="zip_path", default=str(Path("tmp") / "rathena_cn_client_patch.zip"))
    parser.add_argument("--no-zip", action="store_true")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    manifest = copy_patch_files(Path(args.client_dir), Path(args.backup_dir), output_dir, args.clean)
    zip_path = None
    if not args.no_zip:
        zip_path = Path(args.zip_path)
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        write_zip(output_dir, zip_path)

    summary = {
        "output_dir": str(output_dir),
        "zip": str(zip_path) if zip_path else None,
        "file_count": manifest["file_count"],
        "missing_count": manifest["missing_count"],
        "total_size": manifest["total_size"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if manifest["missing_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
