@echo off
setlocal
cd /d "%~dp0\..\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\ai_translate\run_client_runtime_validation.ps1" %*
echo.
echo Press any key to close this window.
pause >nul
exit /b %ERRORLEVEL%
