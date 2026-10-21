@echo off
REM BankViz one-command launcher: backend (port 8000) + frontend dev server (port 5173)
title BankViz launcher

echo [1/2] Starting backend...
start "BankViz backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python -m uvicorn app.main:app --port 8000"

echo [2/2] Starting frontend...
start "BankViz frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 4 >nul
start http://localhost:5173
echo BankViz is starting at http://localhost:5173 (both servers opened in separate windows).
