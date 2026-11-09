@echo off
setlocal
REM BankViz first-time setup: creates Python venv, installs backend deps, installs frontend deps.
REM Run this ONCE on a new machine, before run_local.bat. Requires: Python 3.11+, Node.js 20+.
title BankViz setup

REM Relaunch inside a persistent console so that even a hard crash keeps the
REM window open and the error visible (double-click batch windows close on crash).
if not defined BANKVIZ_SETUP_INNER (
    set "BANKVIZ_SETUP_INNER=1"
    cmd /k "%~f0"
    exit /b
)

cd /d "%~dp0"

echo Project folder: %CD%
echo.

echo [0/3] Checking prerequisites...
REM Prefer the "py" launcher - installed with python.org Python, immune to
REM the Windows Store stub shadowing "python" in PATH.
set "PYCMD="
where py >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"
if not defined PYCMD (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python not found. Install Python 3.11+ from https://www.python.org/downloads/
        echo         and tick "Add Python to PATH" during installation.
        pause & exit /b 1
    )
    set "PYCMD=python"
)
%PYCMD% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No usable Python 3 found. Reinstall Python and tick "Add Python to PATH",
    echo         or disable the App execution aliases for python.exe.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('%PYCMD% --version 2^>^&1') do echo Found %%v

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] npm not found in PATH. Install Node.js 20+ LTS from https://nodejs.org
    pause & exit /b 1
)

if not exist "backend\requirements.txt" (
    echo [ERROR] backend\requirements.txt not found in:
    echo         %CD%
    echo         Make sure you copied the WHOLE bank-viz-tool folder and are running
    echo         setup_local.bat from inside it.
    pause & exit /b 1
)
echo All prerequisites OK.
echo.

echo [1/3] Python virtual environment backend\.venv
cd /d "%~dp0backend"
REM Clean up a broken/partial .venv - e.g. left by PyCharm with a different Python
if exist ".venv" if not exist ".venv\Scripts\python.exe" (
    echo       Step 1a: removing incomplete .venv left by another tool...
    rmdir /s /q ".venv"
)
if exist ".venv\Scripts\python.exe" (
    echo       Step 1a: existing .venv found - reusing it.
) else (
    echo       Step 1a: creating venv - this can take up to 1-2 minutes with no output, please wait...
    %PYCMD% -m venv ".venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment. See message above.
        pause & exit /b 1
    )
    echo       Step 1a: venv created.
)
echo       Step 1b: upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
echo       Step 1b: pip ready.
if exist "%~dp0wheels" (
    echo       Step 1c: offline wheels found - installing backend packages WITHOUT internet, 1-3 min...
    ".venv\Scripts\python.exe" -m pip install --no-index --find-links "%~dp0wheels" -r "requirements.txt"
    if errorlevel 1 (
        echo       Step 1c: offline wheels did not match this Python version - falling back to online install...
        ".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
    )
) else (
    echo       Step 1c: installing backend packages online: pandas, fastapi, etc - takes 1-3 minutes...
    ".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
)
if errorlevel 1 goto :backend_fail
echo       Backend OK.
echo.

echo [2/3] Installing frontend dependencies with npm...
cd /d "%~dp0frontend"
if not exist "package.json" (
    echo [ERROR] frontend\package.json not found - copy the whole project folder.
    pause & exit /b 1
)
echo       npm install - takes 1-5 minutes...
call npm install --no-fund --no-audit
if errorlevel 1 (
    echo [ERROR] npm install failed. Check your internet connection and retry.
    pause & exit /b 1
)
echo       Frontend OK.
echo.

echo [3/3] Checking Ollama - optional, for LLM plan generation...
where ollama >nul 2>nul
if errorlevel 1 (
    echo [NOTE] Ollama not installed. The tool still works in degraded mode without it.
    echo        To enable the LLM later: install from https://ollama.com/download
    echo        then run:  ollama pull qwen2.5:3b
) else (
    ollama list 2>nul | findstr /c:"qwen2.5:3b" >nul
    if errorlevel 1 (
        echo [NOTE] Ollama found, but model qwen2.5:3b is missing.
        echo        Run:  ollama pull qwen2.5:3b
    ) else (
        echo       Ollama + qwen2.5:3b found.
    )
)

echo.
echo ================================================
echo   Setup complete! Start the app with run_local.bat
echo ================================================
echo You can close this window now.
pause
exit /b 0

:backend_fail
echo [ERROR] Backend dependency installation failed. Common causes:
echo         - No internet connection
echo         - Python is the Windows Store stub instead of a real install
echo         - Corporate proxy blocking pypi.org
echo         - Antivirus blocking pip - check Defender protection history
pause
exit /b 1
