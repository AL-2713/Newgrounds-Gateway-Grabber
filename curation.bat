@echo off
set /p "app_id=Enter app_id or swf URL:"
python mainGate.py %app_id% savefiles seperateData exportJson downloadThumbs
pause
