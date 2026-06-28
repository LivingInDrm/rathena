#!/usr/bin/env python3
"""Aggregate server/client localization verification checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent.parent
sys.path.insert(0, str(TOOLS_DIR))

import audit_client_pending  # noqa: E402
import check_client_integrity  # noqa: E402


REPRESENTATIVE_CLIENT_FILES = [
    r"data\msgstringtable.txt",
    r"data\questid2display.txt",
    r"data\luafiles514\lua files\skillinfoz\skilldescript.lub",
    r"System\OngoingQuests.lub",
    r"SystemEN\OngoingQuests.lub",
    r"System\LuaFiles514\itemInfo.lua",
    r"SystemEN\LuaFiles514\itemInfo.lua",
    r"System\spopup.lua",
]

REPRESENTATIVE_REPO_FILES = [
    r"conf\msg_conf\map_msg.conf",
    r"conf\msg_conf\char_msg.conf",
    r"conf\msg_conf\login_msg.conf",
    r"db\re\item_db_usable.yml",
    r"db\re\quest_db.yml",
]


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp936", "euc_kr", "latin1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def chinese_ratio(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "chinese_chars": 0, "size": 0}
    text = read_text(path)
    chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    return {
        "exists": True,
        "chinese_chars": chinese_chars,
        "size": path.stat().st_size,
        "has_chinese": chinese_chars > 0,
    }


def summarize_integrity(report: dict) -> dict:
    keys = ["odd_quote", "risky_diffs", "iteminfo_resource_diffs", "missing_commas"]
    return {key: len(report.get(key, [])) for key in keys}


def build_report(client_dir: Path, backup_dir: Path) -> dict:
    integrity = check_client_integrity.build_report(client_dir, backup_dir)
    pending = audit_client_pending.build_report(client_dir)

    client_files = {rel: chinese_ratio(client_dir / rel) for rel in REPRESENTATIVE_CLIENT_FILES}
    repo_files = {rel: chinese_ratio(ROOT / rel) for rel in REPRESENTATIVE_REPO_FILES}

    data_ini = client_dir / "DATA.ini"
    executable = client_dir / "2021-11-03_Ragexe_patched.exe"
    actionable_pending = pending.get("categories", {}).get("actionable", 0)
    integrity_summary = summarize_integrity(integrity)

    gates = {
        "client_dir_exists": client_dir.exists(),
        "client_exe_exists": executable.exists(),
        "data_ini_exists": data_ini.exists(),
        "client_integrity_clean": all(value == 0 for value in integrity_summary.values()),
        "no_actionable_pending": actionable_pending == 0,
        "representative_client_files_have_chinese": all(item.get("has_chinese") for item in client_files.values()),
        "representative_repo_files_have_chinese": all(item.get("has_chinese") for item in repo_files.values()),
    }

    return {
        "git_head": git_output(["rev-parse", "--short", "HEAD"]),
        "git_status_short": git_output(["status", "--short"]),
        "client_dir": str(client_dir),
        "backup_dir": str(backup_dir),
        "data_ini": read_text(data_ini).splitlines() if data_ini.exists() else [],
        "integrity_summary": integrity_summary,
        "pending_summary": {
            "pending_items": pending.get("pending_items", 0),
            "categories": pending.get("categories", {}),
        },
        "representative_client_files": client_files,
        "representative_repo_files": repo_files,
        "gates": gates,
        "passed_file_level_verification": all(gates.values()),
        "runtime_verification_required": True,
        "runtime_verification_note": "Manual launch of D:\\rag\\2021-11-03_Ragexe_patched.exe is still required to prove no runtime popups or visible untranslated UI remain.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-dir", default=r"D:\rag")
    parser.add_argument("--backup-dir", default=r"D:\rag_cn_backup")
    parser.add_argument("--output", default=str(Path("tmp") / "localization_state_verification.json"))
    args = parser.parse_args()

    report = build_report(Path(args.client_dir), Path(args.backup_dir))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "passed_file_level_verification": report["passed_file_level_verification"],
        "gates": report["gates"],
        "integrity_summary": report["integrity_summary"],
        "pending_summary": report["pending_summary"],
        "output": str(output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if report["passed_file_level_verification"] else 1


if __name__ == "__main__":
    sys.exit(main())
