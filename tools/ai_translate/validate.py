#!/usr/bin/env python3
"""
NPC Translation Validator
==========================
Validates AI-translated text for quality, encoding compatibility, and
structural integrity before applying to NPC files.

Usage:
    python tools/ai_translate/validate.py --input tmp/ai_translate/results/quests.json
    python tools/ai_translate/validate.py --input tmp/ai_translate/results/quests.json --report tmp/ai_translate/reports/
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ─── Configuration ──────────────────────────────────────────────────────────

RATHENA_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REPORT_DIR = RATHENA_ROOT / "tmp" / "ai_translate" / "reports"

# Color code pattern: ^RRGGBB
COLOR_CODE_RE = re.compile(r'\^[0-9a-fA-F]{6}')

# Chinese character range
CN_CHAR_RE = re.compile(r'[\u4e00-\u9fff]')

# Script variable/function patterns that should NOT be translated
SCRIPT_PATTERNS = [
    re.compile(r'\.@\w+'),       # .@var (temporary NPC variable)
    re.compile(r'(?<!\.)@\w+'),  # @var (player variable, not .@var)
    re.compile(r'\$\w+'),        # $var (global variable)
    re.compile(r'(?<!\^)#\w+'),  # #var (account variable, not ^RRGGBB color codes)
    re.compile(r'\b(getarg|strcharinfo|countitem|getitem|callfunc|callsub)\b'),
]


class ValidationIssue:
    """Represents a single validation issue."""
    def __init__(self, severity: str, check: str, source_file: str,
                 npc_label: str, text_type: str, text_index: int,
                 original: str, translated: str, message: str):
        self.severity = severity  # "error" or "warning"
        self.check = check
        self.source_file = source_file
        self.npc_label = npc_label
        self.text_type = text_type
        self.text_index = text_index
        self.original = original
        self.translated = translated
        self.message = message

    def to_dict(self):
        return {
            "severity": self.severity,
            "check": self.check,
            "source_file": self.source_file,
            "npc_label": self.npc_label,
            "text_type": self.text_type,
            "text_index": self.text_index,
            "original": self.original,
            "translated": self.translated,
            "message": self.message,
        }


def check_gbk_encoding(text: str) -> list:
    """Check if text can be encoded in GBK. Reports all unencodable characters."""
    issues = []
    bad_chars = []
    for i, ch in enumerate(text):
        try:
            ch.encode('gbk')
        except UnicodeEncodeError:
            bad_chars.append(f"'{ch}' (U+{ord(ch):04X}) at pos {i}")
    if bad_chars:
        issues.append(f"GBK encoding failed for: {', '.join(bad_chars)}")
    return issues


def check_color_codes(original: str, translated: str) -> list:
    """Check that color codes are preserved in translation."""
    issues = []
    orig_codes = COLOR_CODE_RE.findall(original)
    trans_codes = COLOR_CODE_RE.findall(translated)

    if orig_codes != trans_codes:
        issues.append(
            f"Color codes mismatch: original has {orig_codes}, "
            f"translated has {trans_codes}")
    return issues


def check_select_separators(original: str, translated: str) -> list:
    """Check that select option count matches (same number of ':' separators)."""
    issues = []
    orig_count = original.count(':')
    trans_count = translated.count(':')

    if orig_count != trans_count:
        issues.append(
            f"Select separator count mismatch: original has {orig_count} ':', "
            f"translated has {trans_count} ':'")
    return issues


def check_empty_translation(translated: str) -> list:
    """Check for empty or whitespace-only translations."""
    issues = []
    if not translated or not translated.strip():
        issues.append("Translation is empty or whitespace-only")
    return issues


def check_length_ratio(original: str, translated: str) -> list:
    """Check for abnormal length ratios."""
    issues = []
    if len(original) < 3:
        return issues  # Skip very short strings

    ratio = len(translated) / len(original) if len(original) > 0 else 0
    if ratio > 3.0:
        issues.append(
            f"Translation is {ratio:.1f}x longer than original "
            f"({len(translated)} vs {len(original)} chars)")
    elif ratio < 0.1 and len(original) > 10:
        issues.append(
            f"Translation is suspiciously short: {ratio:.1f}x of original "
            f"({len(translated)} vs {len(original)} chars)")
    return issues


def check_untranslated(original: str, translated: str) -> list:
    """Check if translation is identical to original (not translated)."""
    issues = []
    if original == translated and len(original) > 5:
        # Check if it's a name header like [Guard] - those are OK if short
        if not (original.startswith('[') and original.endswith(']')):
            issues.append("Translation is identical to original (not translated?)")
    return issues


def check_script_references(original: str, translated: str) -> list:
    """Check that script variables/functions are preserved."""
    issues = []
    for pattern in SCRIPT_PATTERNS:
        orig_refs = set(pattern.findall(original))
        if orig_refs:
            trans_refs = set(pattern.findall(translated))
            missing = orig_refs - trans_refs
            if missing:
                issues.append(
                    f"Script references lost in translation: {missing}")
    return issues


def check_has_chinese(translated: str) -> list:
    """Check that translation actually contains Chinese characters."""
    issues = []
    # Skip if original is very short (like punctuation or numbers)
    if len(translated) > 3 and not CN_CHAR_RE.search(translated):
        # Allow pure punctuation/numbers/color codes
        stripped = COLOR_CODE_RE.sub('', translated).strip()
        if stripped and not all(c in '.,!?;:()[]{}0123456789 \t-+*/=<>@#$%^&_~`\'"\\|/' for c in stripped):
            issues.append("Translation contains no Chinese characters")
    return issues


def validate_result_file(input_path: Path) -> tuple:
    """Validate a translation result JSON file.

    Returns (issues_list, stats_dict).
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    all_issues = []
    stats = {
        'total_texts': 0,
        'errors': 0,
        'warnings': 0,
        'passed': 0,
    }

    for task in results:
        source_file = task["source_file"]

        for blk in task["npc_blocks"]:
            npc_label = blk.get("npc_label", "") or f"block_{blk['block_index']}"

            for t in blk["texts"]:
                stats['total_texts'] += 1
                original = t["original"]
                translated = t.get("translated", "")
                text_type = t["type"]
                text_index = t["index"]

                text_issues = []

                # Run all checks
                # Errors (must fix)
                for msg in check_gbk_encoding(translated):
                    text_issues.append(("error", "gbk_encoding", msg))

                for msg in check_empty_translation(translated):
                    text_issues.append(("error", "empty_translation", msg))

                if text_type == "select":
                    for msg in check_select_separators(original, translated):
                        text_issues.append(("error", "select_separators", msg))

                for msg in check_color_codes(original, translated):
                    text_issues.append(("error", "color_codes", msg))

                for msg in check_script_references(original, translated):
                    text_issues.append(("error", "script_references", msg))

                # Warnings (review recommended)
                for msg in check_length_ratio(original, translated):
                    text_issues.append(("warning", "length_ratio", msg))

                for msg in check_untranslated(original, translated):
                    text_issues.append(("warning", "untranslated", msg))

                for msg in check_has_chinese(translated):
                    text_issues.append(("warning", "no_chinese", msg))

                if text_issues:
                    for severity, check, message in text_issues:
                        issue = ValidationIssue(
                            severity=severity,
                            check=check,
                            source_file=source_file,
                            npc_label=npc_label,
                            text_type=text_type,
                            text_index=text_index,
                            original=original,
                            translated=translated,
                            message=message,
                        )
                        all_issues.append(issue)
                        if severity == "error":
                            stats['errors'] += 1
                        else:
                            stats['warnings'] += 1
                else:
                    stats['passed'] += 1

    return all_issues, stats


def main():
    parser = argparse.ArgumentParser(description="Validate NPC translations")
    parser.add_argument("--input", type=str, required=True,
                        help="Input result JSON file from translate.py")
    parser.add_argument("--report", type=str, default=str(DEFAULT_REPORT_DIR),
                        help="Output directory for validation reports")
    parser.add_argument("--errors-only", action="store_true",
                        help="Only show errors, not warnings")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    report_dir = Path(args.report)

    print(f"NPC Translation Validator")
    print(f"  Input:  {input_path}")
    print(f"  Report: {report_dir}")
    print()

    issues, stats = validate_result_file(input_path)

    # Print summary
    print(f"=== Validation Summary ===")
    print(f"  Total texts:  {stats['total_texts']}")
    print(f"  Passed:       {stats['passed']}")
    print(f"  Errors:       {stats['errors']}")
    print(f"  Warnings:     {stats['warnings']}")
    print()

    # Print issues
    if issues:
        # Group by check type
        by_check = {}
        for issue in issues:
            key = issue.check
            if key not in by_check:
                by_check[key] = []
            by_check[key].append(issue)

        for check, check_issues in sorted(by_check.items()):
            if args.errors_only and all(i.severity == "warning" for i in check_issues):
                continue
            print(f"--- {check} ({len(check_issues)} issues) ---")
            for issue in check_issues[:10]:  # Show first 10 per check
                if args.errors_only and issue.severity == "warning":
                    continue
                print(f"  [{issue.severity.upper()}] {issue.source_file} "
                      f"({issue.npc_label}) {issue.text_type}[{issue.text_index}]")
                print(f"    Original:   {issue.original[:80]}")
                print(f"    Translated: {issue.translated[:80]}")
                print(f"    Issue:      {issue.message}")
            if len(check_issues) > 10:
                print(f"  ... and {len(check_issues) - 10} more")
            print()

    # Save report
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"{input_path.stem}_report.json"
    report = {
        "input_file": str(input_path),
        "stats": stats,
        "issues": [i.to_dict() for i in issues],
    }
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved: {report_file}")

    # Exit with error code if there are errors
    if stats['errors'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
