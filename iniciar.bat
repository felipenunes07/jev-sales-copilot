@echo off
REM Abre o Sales Copilot em http://localhost:8000 (feche esta janela para parar)
cd /d "%~dp0"
start "" http://localhost:8000
"C:\Program Files\Git\bin\bash.exe" run.sh
pause
