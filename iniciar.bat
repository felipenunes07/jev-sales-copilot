@echo off
REM Abre o Sales Copilot em http://localhost:8000 (feche esta janela para parar).
REM Precisa do uv (https://docs.astral.sh/uv/) e de um arquivo .env com OPENROUTER_API_KEY (copie de .env.example).
cd /d "%~dp0"
where uv >nul 2>nul || (echo Instale o uv: https://docs.astral.sh/uv/getting-started/installation/ & pause & exit /b 1)
if not exist .env (echo Crie o arquivo .env a partir de .env.example e coloque sua OPENROUTER_API_KEY. & pause & exit /b 1)
uv sync --quiet
start "" http://localhost:8000
uv run uvicorn copilot.server:app --host 127.0.0.1 --port 8000
pause
