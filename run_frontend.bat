@echo off
title NL2DB Frontend Server
echo ========================================================
echo   Starting NL2DB Frontend Client (React + Vite)
echo ========================================================
echo.

cd /d "%~dp0frontend"

:: 1. Check for node_modules
if not exist "node_modules" (
    echo [*] node_modules not found. Running npm install...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Make sure Node.js v18 or higher is installed.
        pause
        exit /b 1
    )
)

:: 2. Start Vite Dev Server
echo.
echo ========================================================
echo   Frontend starting at: http://localhost:5173
echo ========================================================
echo.

call npm run dev
pause
