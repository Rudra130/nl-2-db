@echo off
title NL2DB Backend Server
echo ========================================================
echo   Starting NL2DB Backend Server (FastAPI + LangGraph)
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Check for Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Creating .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Ensure Python 3.10+ is installed and on your PATH.
        pause
        exit /b 1
    )
    echo [*] Installing backend dependencies...
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
)

:: 2. Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo [*] No .env found. Copying .env.example to .env...
        copy .env.example .env
    )
)

:: 3. Seed sample SQLite database if missing
if not exist "data\nl2db_sample.db" (
    echo [*] Seeding initial sample database...
    .\.venv\Scripts\python.exe backend\scripts\seed_local_dbs.py
)

:: 4. Start Uvicorn Server
echo.
echo ========================================================
echo   Backend starting at: http://localhost:8000
echo   API Documentation:   http://localhost:8000/docs
echo ========================================================
echo.

.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
pause
