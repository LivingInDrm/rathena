#!/usr/bin/env python3
"""Probe a running Ragnarok client for runtime localization error windows."""

from __future__ import annotations

import argparse
import ctypes
import json
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path


ERROR_KEYWORDS = (
    "error",
    "not found",
    "unfinished string",
    "itemdbnametbl",
    "querymaptable",
    "queryfieldtable",
    "init",
    "cluainstance",
    "ctemlinfomgr",
)


user32 = ctypes.WinDLL("user32", use_last_error=True)

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.EnumChildWindows.argtypes = [wintypes.HWND, EnumWindowsProc, wintypes.LPARAM]
user32.EnumChildWindows.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL


def window_text(hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(1024)
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value


def class_name(hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value


def window_rect(hwnd: int) -> dict:
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return {}
    return {
        "left": rect.left,
        "top": rect.top,
        "right": rect.right,
        "bottom": rect.bottom,
        "width": rect.right - rect.left,
        "height": rect.bottom - rect.top,
    }


def process_rows() -> list[dict]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "Get-Process | Where-Object { $_.ProcessName -like '*Ragexe*' -or $_.ProcessName -like '*rAthena*' } | "
            "Select-Object Id,ProcessName,Responding,MainWindowTitle,MainWindowHandle,StartTime | ConvertTo-Json -Compress"
        ),
    ]
    try:
        output = subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return []
    if not output:
        return []
    data = json.loads(output)
    if isinstance(data, dict):
        return [data]
    return data if isinstance(data, list) else []


def enum_windows_for_pids(pids: set[int]) -> list[dict]:
    windows: list[dict] = []

    def enum_child(parent_hwnd: int) -> list[dict]:
        children: list[dict] = []

        @EnumWindowsProc
        def child_proc(hwnd: int, _lparam: int) -> bool:
            text = window_text(hwnd)
            cls = class_name(hwnd)
            if text or cls:
                children.append({"handle": hwnd, "class": cls, "text": text, "visible": bool(user32.IsWindowVisible(hwnd))})
            return True

        user32.EnumChildWindows(parent_hwnd, child_proc, 0)
        return children

    @EnumWindowsProc
    def enum_proc(hwnd: int, _lparam: int) -> bool:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) in pids:
            windows.append(
                {
                    "handle": hwnd,
                    "pid": int(pid.value),
                    "class": class_name(hwnd),
                    "text": window_text(hwnd),
                    "visible": bool(user32.IsWindowVisible(hwnd)),
                    "rect": window_rect(hwnd),
                    "children": enum_child(hwnd),
                }
            )
        return True

    user32.EnumWindows(enum_proc, 0)
    return windows


def suspicious_texts(windows: list[dict]) -> list[dict]:
    hits = []
    for window in windows:
        rows = [{"source": "window", "class": window.get("class", ""), "text": window.get("text", "")}]
        rows.extend({"source": "child", "class": child.get("class", ""), "text": child.get("text", "")} for child in window.get("children", []))
        for row in rows:
            text = row.get("text", "")
            cls = row.get("class", "")
            haystack = f"{cls}\n{text}".lower()
            matched = [keyword for keyword in ERROR_KEYWORDS if keyword in haystack]
            if matched:
                hits.append({"pid": window.get("pid"), "window": window.get("text", ""), "class": cls, "text": text, "matched": matched})
    return hits


def build_report(wait_seconds: int) -> dict:
    if wait_seconds:
        time.sleep(wait_seconds)
    processes = process_rows()
    pids = {int(row["Id"]) for row in processes if "Id" in row}
    windows = enum_windows_for_pids(pids) if pids else []
    suspicious = suspicious_texts(windows)
    return {
        "processes": processes,
        "windows": windows,
        "suspicious": suspicious,
        "client_running": bool(processes),
        "runtime_probe_passed": bool(processes) and not suspicious,
        "note": "runtime_probe_passed only proves no known error popup text was visible at probe time.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-seconds", type=int, default=0)
    parser.add_argument("--output", default=str(Path("tmp") / "client_runtime_probe.json"))
    args = parser.parse_args()

    report = build_report(args.wait_seconds)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "client_running": report["client_running"],
                "runtime_probe_passed": report["runtime_probe_passed"],
                "process_count": len(report["processes"]),
                "window_count": len(report["windows"]),
                "suspicious_count": len(report["suspicious"]),
                "output": str(output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["runtime_probe_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
