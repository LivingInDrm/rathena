@echo off
for /f "tokens=1,* delims==" %%a in (tools\ai_translate\api_config.txt) do set "%%a=%%b"
python tools/ai_translate/pipeline.py %*
