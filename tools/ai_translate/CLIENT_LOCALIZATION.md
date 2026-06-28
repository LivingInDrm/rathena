# Client Localization Delivery Notes

This document records the current delivery workflow for the installed Ragnarok client at `D:\rag`.

## Scope

- Client root: `D:\rag`
- Client executable: `D:\rag\2021-11-03_Ragexe_patched.exe`
- Client overlay package: `tmp\rathena_cn_client_patch.zip`
- Overlay manifest: `tmp\rathena_cn_client_patch\manifest.json`
- Server-side translations are tracked in git commits.
- Client-side translations are applied directly to the installed client and packaged as an overlay.

## Verification Commands

Run from the repository root:

```powershell
python tools\ai_translate\verify_localization_state.py --client-dir D:\rag --backup-dir D:\rag_cn_backup --output tmp\localization_state_verification_latest.json
```

Expected file-level result:

- `passed_file_level_verification=true`
- `client_integrity_clean=true`
- `no_actionable_pending=true`
- `representative_client_files_have_chinese=true`
- `representative_repo_files_have_chinese=true`

For lower-level checks:

```powershell
python tools\ai_translate\check_client_integrity.py --client-dir D:\rag --backup-dir D:\rag_cn_backup --output tmp\client_integrity_check_final.json
python tools\ai_translate\audit_client_pending.py --client-dir D:\rag --output tmp\client_pending_classified_final.json --fail-on-actionable
```

To reapply deterministic visible UI polish such as item tooltip labels and skill-tab names:

```powershell
python tools\ai_translate\polish_client_visible_text.py --client-dir D:\rag --backup-dir D:\rag_cn_backup --output tmp\client_visible_polish.json
```

## Runtime Verification

File-level verification is not sufficient to declare the whole localization complete. The client must also be launched manually and checked for error popups or visibly untranslated UI.

1. Start `D:\rag\2021-11-03_Ragexe_patched.exe` manually.
2. After the client window appears, run:

```powershell
python tools\ai_translate\probe_client_runtime.py --output tmp\client_runtime_probe.json
```

Or use the wrapper after manual launch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ai_translate\run_client_runtime_validation.ps1 -WaitSeconds 0 -Output tmp\client_runtime_probe.json
```

The wrapper does not auto-start the client by default. It can also attempt to start the client when explicitly requested, but this is less reliable from non-interactive shells:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ai_translate\run_client_runtime_validation.ps1 -AutoStart -StartTimeoutSeconds 5 -WaitSeconds 20 -Output tmp\client_runtime_probe.json
```

Expected runtime probe result:

- `client_running=true`
- `runtime_probe_passed=true`
- `suspicious_count=0`

The runtime probe only checks visible process/window/popup text. Manual visual inspection is still required for screenshots, login flow, item tooltips, quest windows, and NPC dialogue.

## Packaging

To rebuild the client overlay patch:

```powershell
python tools\ai_translate\package_client_patch.py --client-dir D:\rag --backup-dir D:\rag_cn_backup --output-dir tmp\rathena_cn_client_patch --zip tmp\rathena_cn_client_patch.zip --clean
```

Expected package result:

- `file_count=142`
- `missing_count=0`
- `tmp\rathena_cn_client_patch.zip` exists

Install the overlay by copying everything under `tmp\rathena_cn_client_patch\files` into the client root while preserving relative paths.

## Rollback

Backups are stored under `D:\rag_cn_backup\<timestamp>`.

Recent important backup roots:

- `D:\rag_cn_backup\20260628_194627`
- `D:\rag_cn_backup\20260628_195143`
- `D:\rag_cn_backup\20260628_195159`

Rollback is file-based: copy the corresponding files from the backup root back into `D:\rag`, preserving relative paths. Close the game client before restoring files.

## Known Ignored Residuals

The pending audit intentionally ignores these categories:

- Client/service configuration values such as `korea`, `primary`, loading image names, and URLs.
- Internal helper paths, Lua module names, resource filenames, and audio filenames.
- Formula/stat strings already usable as-is, such as `RES +3，MRES +3.`
- Template comments in custom item placeholder files.
- Korean anniversary/player-name book pages and mojibake-heavy historical text that is unsafe to machine translate.

These ignored residuals are tracked in `tmp\client_pending_classified_final.json` when the audit is run.

## Completion Criteria

The localization can be marked complete only when all of the following are true:

1. `verify_localization_state.py` passes.
2. `check_client_integrity.py` reports zero structural issues.
3. `audit_client_pending.py --fail-on-actionable` exits successfully.
4. The client launches manually without localization-related popups.
5. Manual visual inspection finds no major untranslated visible UI in the target gameplay paths.
