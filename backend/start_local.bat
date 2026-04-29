@echo off
setlocal

cd /d "%~dp0"

echo Starting OmniHealthAI on http://127.0.0.1:5000
start "" http://127.0.0.1:5000
python app.py

endlocal
