@echo off
set /p "app_id=Enter app_id:"
python mainGate.py %app_id% savefiles seperateData exportJson
pause