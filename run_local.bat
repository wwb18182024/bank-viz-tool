@echo off
setlocal
REM BankViz one-command launcher: backend (port 8000) + frontend dev server (port 5173)
title BankViz launcher

if not exist "backend\requirements.txt" (
    echo [ERROR] Please run this from inside the bank-viz-tool folder.
    echo         If you have not run setup_local.bat yet, do that first.
    pause & exit /b 1
)

echo [1/2] Starting backend...
cd /d "%~dp0backend"
start "BankViz backend" cmd /k ".venv\Scripts\python -m uvicorn app.main:app --port 8000"

echo [2/2] Starting frontend...
cd /d "%~dp0frontend"
start "BankViz frontend" cmd /k "call npm run dev"

timeout /t 4 >nul
start http://localhost:5173
echo BankViz is starting at http://localhost:5173 (both servers opened in separate windows).
