@echo off
REM Start your Flask app and then run ngrok in a separate terminal.
echo 1. Open a terminal in %~dp0
echo 2. Run: python app.py
echo 3. Open another terminal and run: ngrok http 5000
echo 4. Share the generated ngrok URL with your friend.
echo.
echo If ngrok is not installed, download it from https://ngrok.com/download and add it to PATH.
pause