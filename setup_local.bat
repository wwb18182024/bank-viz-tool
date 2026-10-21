@echo off
REM BankViz first-time setup: creates Python venv, installs backend deps, installs frontend deps.
REM Run this ONCE on a new machine, before run_local.bat. Requires: Python 3.11+, Node.js 20+.
title BankViz setup

where python >nul 2>nul || (echo [ERROR] Python not found in PATH. Install Python 3.11+ first. & pause & exit /b 1)
where npm >nul 2>nul || (echo [ERROR] npm not found in PATH. Install Node.js 20+ first. & pause & exit /b 1)

echo [1/3] Creating Python virtual environment (backend\.venv)...
cd /d %~dp0backend
if not exist .venv python -m venv .venv
call .venv\Scripts\python -m pip install --upgrade pip -q
call .venv\Scripts\python -m pip install -q -r requirements.txt || (echo [ERROR] backend install failed & pause & exit /b 1)

echo [2/3] Installing frontend dependencies (npm)...
cd /d %~dp0frontend
call npm install --no-fund --no-audit || (echo [ERROR] npm install failed & pause & exit /b 1)

echo [3/3] Checking Ollama...
where ollama >nul 2>nul && (ollama list | findstr /c:"qwen2.5:3b" >nul && echo Ollama + qwen2.5:3b found. || echo [NOTE] Ollama found but qwen2.5:3b missing - run: ollama pull qwen2.5:3b) || echo [NOTE] Ollama not found - install from https://ollama.com then run: ollama pull qwen2.5:3b

echo.
echo Setup complete. Start the app with run_local.bat
pause
