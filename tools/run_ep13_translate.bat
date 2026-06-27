@echo off
cd /d "D:\Projects\rathena"

REM Read API key from config
for /f "tokens=1,* delims==" %%a in ('findstr "OPENAI_API_KEY" tools\ai_translate\api_config.txt') do (
    set "%%a=%%b"
)

echo API key set (length check):
echo %OPENAI_API_KEY:~0,20%...

REM Translate EP13 quests
echo.
echo === Translating EP13 Quests ===
python tools/ai_translate/translate.py --input tmp/ai_translate/tasks/ep13_quests.json --output tmp/ai_translate/results/ep13_quests.json --model gpt-4o-mini --rpm 20

echo.
echo === Translating EP13 Instances (NydhoggsNest) ===
python tools/ai_translate/translate.py --input tmp/ai_translate/tasks/ep13_instances.json --output tmp/ai_translate/results/ep13_instances.json --model gpt-4o-mini --rpm 20

echo.
echo === Done ===
