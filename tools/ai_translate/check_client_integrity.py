#!/usr/bin/env python3
"""Check translated Ragnarok client files for structural breakage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_EXTS = {".lua", ".lub"}
INTERNAL_MARKERS = (
    "ResourceName =",
    "BaseItem =",
    "ResultItem =",
    "Material =",
    "RandomOptionCode =",
    "AddTargetItem(",
    "SetRequire(",
    "SetReset(",
    "AddUpgradeEnchant(",
    "AddPerfectEnchant(",
)
VISIBLE_INTERNAL_EXCEPTIONS = ("NeedSource_String", "SetCaution(")
ENTRY_RE = re.compile(r"^\s*\[(\d+)\]\s*=\s*\{")
RESOURCE_RE = re.compile(r'^(\s*)(unidentifiedResourceName|identifiedResourceName)\s*=\s*"([^"]*)"(,?)\s*$')
LIST_KEY_RE = re.compile(r'^\s*(?:\["[^"]+"\]\s*=\s*\{|\{\s*"[^"]+"\s*,\s*\d+)')
ASSIGN_WITHOUT_COMMA_RE = re.compile(r'^\s*\[[^\]]+\]\s*=\s*"[^"]*"\s*$')
ITEMDB_KEY_RELS = (
    r"data\luafiles514\lua files\ItemReform\ItemReformSystem.lub",
    r"data\luafiles514\lua files\datainfo\LapineUpgradeBox.lub",
    r"data\luafiles514\lua files\datainfo\lapineddukddakbox.lub",
    r"data\luafiles514\lua files\Enchant\EnchantList.lub",
)
ITEMDB_ASSIGN_RE = re.compile(
    rb"(?P<field>BaseItem|ResultItem|ItemName|ItemDBName)\s*=\s*"
    rb'"(?P<value>(?:\\.|[^"\\])*)"'
)
ITEMDB_MATERIAL_BLOCK_RE = re.compile(rb"Material\s*=\s*\{(?P<body>[^\r\n]*)\}")
ITEMDB_BRACKET_KEY_RE = re.compile(rb'\[\s*"(?P<value>(?:\\.|[^"\\])*)"\s*\]\s*=')
ITEMDB_FUNCTION_ARG_RE = re.compile(
    rb":(?:AddTargetItem|SetEnchant)\s*\([^\"\r\n]*"
    rb'"(?P<value>(?:\\.|[^"\\])*)"'
)
ITEMDB_SET_REQUIRE_RE = re.compile(
    rb":(?:SetRequire|SetReset)\s*\([^\r\n]*\{\s*"
    rb'"(?P<value>(?:\\.|[^"\\])*)"\s*,'
)
ITEMDB_ARRAY_ITEM_RE = re.compile(rb'\{\s*"(?P<value>(?:\\.|[^"\\])*)"\s*,\s*\d+\s*\}')
MODEL_RESOURCE_RELS = (
    r"data\luafiles514\lua files\datainfo\jobname.lub",
)
PETINFO_RESOURCE_RELS = (
    r"data\luafiles514\lua files\datainfo\petinfo.lub",
)
JOBNAME_MODEL_RE = re.compile(
    r'^(\s*\[jobtbl\.(?P<key>[^\]]+)\]\s*=\s*")(?P<value>[^"]+\.gr2)(",?\s*)$',
    re.MULTILINE,
)
JOBNAME_RESOURCE_RE = re.compile(
    r'^(\s*\[jobtbl\.(?P<key>[^\]]+)\]\s*=\s*")(?P<value>[^"]*)(",?\s*)$',
    re.MULTILINE,
)
PETINFO_RESOURCE_RE = re.compile(r'"(?P<value>[^"]*\.(?:act|bmp|spr|wav|str|gr2))"', re.IGNORECASE)
MAP_BACKGROUND_RELS = (
    r"System\mapInfo_sak.lub",
    r"SystemEN\mapInfo.lub",
)
MAP_BACKGROUND_RE = re.compile(r'backgroundBmp\s*=\s*"(?P<value>[^"]*)"')
TIPBOX_RELS = (
    r"System\tipbox.lub",
    r"SystemEN\tipbox.lub",
)
TIPBOX_IMAGE_RE = re.compile(rb'Image\s*=\s*"(?P<value>(?:\\.|[^"\\])*)"')


def read_text_file(path: Path) -> str | None:
    raw = path.read_bytes()
    if b"\0" in raw[:200000]:
        return None
    return raw.decode("cp936", errors="replace")


def preview_bytes(value: bytes) -> str:
    return value.decode("cp936", errors="replace")


def count_unescaped_quotes(line: str) -> int:
    escaped = False
    count = 0
    for char in line:
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            count += 1
    return count


def backup_index(backup_dir: Path) -> dict[str, Path]:
    backups: dict[str, Path] = {}
    if not backup_dir.exists():
        return backups
    for backup_root in sorted(path for path in backup_dir.iterdir() if path.is_dir()):
        for path in backup_root.rglob("*"):
            if path.is_file():
                backups.setdefault(str(path.relative_to(backup_root)).replace("/", "\\"), path)
    return backups


def is_risky_internal_line(line: str) -> bool:
    if any(marker in line for marker in INTERNAL_MARKERS):
        return not any(exception in line for exception in VISIBLE_INTERNAL_EXCEPTIONS)
    return bool(LIST_KEY_RE.search(line))


def resource_map(text: str) -> dict[int, dict[str, str]]:
    current_id: int | None = None
    resources: dict[int, dict[str, str]] = {}
    for line in text.splitlines():
        entry = ENTRY_RE.match(line)
        if entry:
            current_id = int(entry.group(1))
            resources.setdefault(current_id, {})
            continue
        if current_id is None:
            continue
        resource = RESOURCE_RE.match(line)
        if resource:
            resources[current_id][resource.group(2)] = resource.group(3)
    return resources


def iter_client_lua_files(client_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for base in [client_dir / "data" / "luafiles514", client_dir / "System", client_dir / "SystemEN"]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_EXTS:
                paths.append(path)
    return sorted(paths)


def check_odd_quotes(paths: list[Path]) -> list[dict]:
    issues = []
    for path in paths:
        text = read_text_file(path)
        if text is None:
            continue
        rows = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if count_unescaped_quotes(line) % 2:
                rows.append({"line": line_number, "text": line[:240]})
                if len(rows) >= 10:
                    break
        if rows:
            issues.append({"file": str(path), "rows": rows})
    return issues


def check_risky_diffs(client_dir: Path, backups: dict[str, Path]) -> list[dict]:
    issues = []
    for rel, backup_path in backups.items():
        current_path = client_dir / rel
        if not current_path.exists() or current_path.suffix.lower() not in TEXT_EXTS:
            continue
        current_text = read_text_file(current_path)
        backup_text = read_text_file(backup_path)
        if current_text is None or backup_text is None:
            continue
        current_lines = current_text.splitlines()
        backup_lines = backup_text.splitlines()
        if len(current_lines) != len(backup_lines):
            continue
        diffs = []
        for line_number, (current, original) in enumerate(zip(current_lines, backup_lines), 1):
            if current == original or not (is_risky_internal_line(current) or is_risky_internal_line(original)):
                continue
            if rel.endswith(r"dressroom\jobdresslist.lub"):
                continue
            diffs.append({"line": line_number, "current": current[:220], "backup": original[:220]})
            if len(diffs) >= 50:
                break
        if diffs:
            issues.append({"file": str(current_path), "backup": str(backup_path), "diffs": diffs})
    return issues


def check_iteminfo_resources(client_dir: Path, backups: dict[str, Path]) -> list[dict]:
    candidates = [
        r"System\LuaFiles514\itemInfo.lua",
        r"SystemEN\LuaFiles514\itemInfo.lua",
    ]
    issues = []
    for rel in candidates:
        current_path = client_dir / rel
        backup_path = backups.get(rel)
        if not current_path.exists() or backup_path is None:
            continue
        current_text = read_text_file(current_path)
        backup_text = read_text_file(backup_path)
        if current_text is None or backup_text is None:
            continue
        current_resources = resource_map(current_text)
        backup_resources = resource_map(backup_text)
        diffs = []
        for item_id, fields in current_resources.items():
            original_fields = backup_resources.get(item_id)
            if not original_fields:
                continue
            for field, value in fields.items():
                original_value = original_fields.get(field)
                if original_value is not None and value != original_value:
                    diffs.append({"item_id": item_id, "field": field, "current": value, "backup": original_value})
                    if len(diffs) >= 50:
                        break
            if len(diffs) >= 50:
                break
        if diffs:
            issues.append({"file": str(current_path), "backup": str(backup_path), "diffs": diffs})
    return issues


def itemdb_key_tokens(data: bytes, rel: str) -> list[dict]:
    tokens: list[dict] = []
    for match in ITEMDB_ASSIGN_RE.finditer(data):
        tokens.append(
            {
                "offset": match.start(),
                "context": match.group("field").decode("ascii"),
                "value": match.group("value"),
            }
        )
    for match in ITEMDB_MATERIAL_BLOCK_RE.finditer(data):
        for key_match in ITEMDB_BRACKET_KEY_RE.finditer(match.group("body")):
            tokens.append(
                {
                    "offset": match.start() + key_match.start(),
                    "context": "Material",
                    "value": key_match.group("value"),
                }
            )
    for match in ITEMDB_FUNCTION_ARG_RE.finditer(data):
        tokens.append(
            {
                "offset": match.start(),
                "context": "itemdb_function_arg",
                "value": match.group("value"),
            }
        )
    for match in ITEMDB_SET_REQUIRE_RE.finditer(data):
        tokens.append(
            {
                "offset": match.start(),
                "context": "require_material",
                "value": match.group("value"),
            }
        )
    rel_lower = rel.lower()
    if "lapineupgradebox.lub" in rel_lower or "lapineddukddakbox.lub" in rel_lower:
        for match in ITEMDB_ARRAY_ITEM_RE.finditer(data):
            tokens.append(
                {
                    "offset": match.start(),
                    "context": "array_item",
                    "value": match.group("value"),
                }
            )
    return sorted(tokens, key=lambda token: token["offset"])


def check_itemdb_key_diffs(client_dir: Path, backups: dict[str, Path]) -> list[dict]:
    issues = []
    for rel in ITEMDB_KEY_RELS:
        current_path = client_dir / rel
        backup_path = backups.get(rel)
        if not current_path.exists() or backup_path is None:
            continue
        current_data = current_path.read_bytes()
        backup_data = backup_path.read_bytes()
        current_tokens = itemdb_key_tokens(current_data, rel)
        backup_tokens = itemdb_key_tokens(backup_data, rel)
        diffs = []
        if len(current_tokens) != len(backup_tokens):
            diffs.append(
                {
                    "kind": "token_count",
                    "current": len(current_tokens),
                    "backup": len(backup_tokens),
                }
            )
        for current, original in zip(current_tokens, backup_tokens):
            if current["context"] == original["context"] and current["value"] == original["value"]:
                continue
            diffs.append(
                {
                    "kind": "value",
                    "line": current_data.count(b"\n", 0, current["offset"]) + 1,
                    "context": current["context"],
                    "current": preview_bytes(current["value"]),
                    "backup": preview_bytes(original["value"]),
                    "current_hex": current["value"].hex(),
                    "backup_hex": original["value"].hex(),
                }
            )
            if len(diffs) >= 50:
                break
        if diffs:
            issues.append({"file": str(current_path), "backup": str(backup_path), "diffs": diffs})
    return issues


def model_resource_map(text: str) -> dict[str, str]:
    return {match.group("key"): match.group("value") for match in JOBNAME_MODEL_RE.finditer(text)}


def jobname_resource_map(text: str) -> dict[str, dict]:
    resources = {}
    for match in JOBNAME_RESOURCE_RE.finditer(text):
        resources[match.group("key")] = {
            "line": text.count("\n", 0, match.start()) + 1,
            "value": match.group("value"),
        }
    return resources


def check_model_resource_diffs(client_dir: Path, backups: dict[str, Path]) -> list[dict]:
    issues = []
    for rel in MODEL_RESOURCE_RELS:
        current_path = client_dir / rel
        backup_path = backups.get(rel)
        if not current_path.exists() or backup_path is None:
            continue
        current_text = read_text_file(current_path)
        backup_text = read_text_file(backup_path)
        if current_text is None or backup_text is None:
            continue
        current_resources = model_resource_map(current_text)
        backup_resources = model_resource_map(backup_text)
        diffs = []
        for key, current_value in current_resources.items():
            backup_value = backup_resources.get(key)
            if backup_value is not None and current_value != backup_value:
                line = current_text[: current_text.find(f"[jobtbl.{key}]")].count("\n") + 1
                diffs.append({"line": line, "key": key, "current": current_value, "backup": backup_value})
                if len(diffs) >= 50:
                    break
        if diffs:
            issues.append({"file": str(current_path), "backup": str(backup_path), "diffs": diffs})
    return issues


def check_jobname_resource_diffs(client_dir: Path, backups: dict[str, Path]) -> list[dict]:
    issues = []
    for rel in MODEL_RESOURCE_RELS:
        current_path = client_dir / rel
        backup_path = backups.get(rel)
        if not current_path.exists() or backup_path is None:
            continue
        current_text = read_text_file(current_path)
        backup_text = read_text_file(backup_path)
        if current_text is None or backup_text is None:
            continue
        current_resources = jobname_resource_map(current_text)
        backup_resources = jobname_resource_map(backup_text)
        diffs = []
        if len(current_resources) != len(backup_resources):
            diffs.append(
                {
                    "kind": "value_count",
                    "current": len(current_resources),
                    "backup": len(backup_resources),
                }
            )
        for key, current in current_resources.items():
            backup = backup_resources.get(key)
            if backup is None or current["value"] == backup["value"]:
                continue
            diffs.append({"line": current["line"], "key": key, "current": current["value"], "backup": backup["value"]})
            if len(diffs) >= 50:
                break
        if diffs:
            issues.append({"file": str(current_path), "backup": str(backup_path), "diffs": diffs})
    return issues


def petinfo_resource_values(text: str) -> list[dict]:
    return [
        {
            "line": text.count("\n", 0, match.start()) + 1,
            "value": match.group("value"),
        }
        for match in PETINFO_RESOURCE_RE.finditer(text)
    ]


def check_petinfo_resource_diffs(client_dir: Path, backups: dict[str, Path]) -> list[dict]:
    issues = []
    for rel in PETINFO_RESOURCE_RELS:
        current_path = client_dir / rel
        backup_path = backups.get(rel)
        if not current_path.exists() or backup_path is None:
            continue
        current_text = read_text_file(current_path)
        backup_text = read_text_file(backup_path)
        if current_text is None or backup_text is None:
            continue
        current_values = petinfo_resource_values(current_text)
        backup_values = petinfo_resource_values(backup_text)
        diffs = []
        if len(current_values) != len(backup_values):
            diffs.append(
                {
                    "kind": "value_count",
                    "current": len(current_values),
                    "backup": len(backup_values),
                }
            )
        for current, backup in zip(current_values, backup_values):
            if current["value"] == backup["value"]:
                continue
            diffs.append({"line": current["line"], "current": current["value"], "backup": backup["value"]})
            if len(diffs) >= 50:
                break
        if diffs:
            issues.append({"file": str(current_path), "backup": str(backup_path), "diffs": diffs})
    return issues


def map_background_values(text: str) -> list[dict]:
    values = []
    for match in MAP_BACKGROUND_RE.finditer(text):
        values.append(
            {
                "line": text.count("\n", 0, match.start()) + 1,
                "value": match.group("value"),
            }
        )
    return values


def check_map_background_diffs(client_dir: Path, backups: dict[str, Path]) -> list[dict]:
    issues = []
    for rel in MAP_BACKGROUND_RELS:
        current_path = client_dir / rel
        backup_path = backups.get(rel)
        if not current_path.exists() or backup_path is None:
            continue
        current_text = read_text_file(current_path)
        backup_text = read_text_file(backup_path)
        if current_text is None or backup_text is None:
            continue
        current_values = map_background_values(current_text)
        backup_values = map_background_values(backup_text)
        diffs = []
        if len(current_values) != len(backup_values):
            diffs.append(
                {
                    "kind": "value_count",
                    "current": len(current_values),
                    "backup": len(backup_values),
                }
            )
        for current, original in zip(current_values, backup_values):
            has_non_ascii = any(ord(char) > 127 for char in current["value"])
            if current["value"] == original["value"] and not has_non_ascii:
                continue
            diffs.append(
                {
                    "kind": "value",
                    "line": current["line"],
                    "current": current["value"],
                    "backup": original["value"],
                }
            )
            if len(diffs) >= 50:
                break
        if diffs:
            issues.append({"file": str(current_path), "backup": str(backup_path), "diffs": diffs})
    return issues


def tipbox_image_values(data: bytes) -> list[dict]:
    values = []
    for match in TIPBOX_IMAGE_RE.finditer(data):
        values.append(
            {
                "line": data.count(b"\n", 0, match.start()) + 1,
                "value": match.group("value"),
            }
        )
    return values


def check_tipbox_image_diffs(client_dir: Path, backups: dict[str, Path]) -> list[dict]:
    issues = []
    for rel in TIPBOX_RELS:
        current_path = client_dir / rel
        backup_path = backups.get(rel)
        if not current_path.exists() or backup_path is None:
            continue
        current_values = tipbox_image_values(current_path.read_bytes())
        backup_values = tipbox_image_values(backup_path.read_bytes())
        diffs = []
        if len(current_values) != len(backup_values):
            diffs.append(
                {
                    "kind": "value_count",
                    "current": len(current_values),
                    "backup": len(backup_values),
                }
            )
        for current, backup in zip(current_values, backup_values):
            if current["value"] == backup["value"]:
                continue
            diffs.append(
                {
                    "line": current["line"],
                    "current": preview_bytes(current["value"]),
                    "backup": preview_bytes(backup["value"]),
                    "current_hex": current["value"].hex(),
                    "backup_hex": backup["value"].hex(),
                }
            )
            if len(diffs) >= 50:
                break
        if diffs:
            issues.append({"file": str(current_path), "backup": str(backup_path), "diffs": diffs})
    return issues


def check_missing_commas(paths: list[Path]) -> list[dict]:
    issues = []
    for path in paths:
        text = read_text_file(path)
        if text is None:
            continue
        lines = text.splitlines()
        rows = []
        for index in range(len(lines) - 1):
            if ASSIGN_WITHOUT_COMMA_RE.match(lines[index]) and lines[index + 1].lstrip().startswith("["):
                rows.append({"line": index + 1, "text": lines[index][:220], "next": lines[index + 1][:220]})
                if len(rows) >= 20:
                    break
        if rows:
            issues.append({"file": str(path), "rows": rows})
    return issues


def build_report(client_dir: Path, backup_dir: Path) -> dict:
    paths = iter_client_lua_files(client_dir)
    backups = backup_index(backup_dir)
    return {
        "client_dir": str(client_dir),
        "backup_dir": str(backup_dir),
        "checked_files": len(paths),
        "odd_quote": check_odd_quotes(paths),
        "risky_diffs": check_risky_diffs(client_dir, backups),
        "iteminfo_resource_diffs": check_iteminfo_resources(client_dir, backups),
        "itemdb_key_diffs": check_itemdb_key_diffs(client_dir, backups),
        "model_resource_diffs": check_model_resource_diffs(client_dir, backups),
        "jobname_resource_diffs": check_jobname_resource_diffs(client_dir, backups),
        "petinfo_resource_diffs": check_petinfo_resource_diffs(client_dir, backups),
        "map_background_diffs": check_map_background_diffs(client_dir, backups),
        "tipbox_image_diffs": check_tipbox_image_diffs(client_dir, backups),
        "missing_commas": check_missing_commas(paths),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-dir", default=r"D:\rag")
    parser.add_argument("--backup-dir", default=r"D:\rag_cn_backup")
    parser.add_argument("--output", default=str(Path("tmp") / "client_integrity_check.json"))
    args = parser.parse_args()

    report = build_report(Path(args.client_dir), Path(args.backup_dir))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "checked_files": report["checked_files"],
        "odd_quote": len(report["odd_quote"]),
        "risky_diffs": len(report["risky_diffs"]),
        "iteminfo_resource_diffs": len(report["iteminfo_resource_diffs"]),
        "itemdb_key_diffs": len(report["itemdb_key_diffs"]),
        "model_resource_diffs": len(report["model_resource_diffs"]),
        "jobname_resource_diffs": len(report["jobname_resource_diffs"]),
        "petinfo_resource_diffs": len(report["petinfo_resource_diffs"]),
        "map_background_diffs": len(report["map_background_diffs"]),
        "tipbox_image_diffs": len(report["tipbox_image_diffs"]),
        "missing_commas": len(report["missing_commas"]),
        "output": str(output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    issue_keys = (
        "odd_quote",
        "risky_diffs",
        "iteminfo_resource_diffs",
        "itemdb_key_diffs",
        "model_resource_diffs",
        "jobname_resource_diffs",
        "petinfo_resource_diffs",
        "map_background_diffs",
        "tipbox_image_diffs",
        "missing_commas",
    )
    return 1 if any(summary[key] for key in issue_keys) else 0


if __name__ == "__main__":
    sys.exit(main())
