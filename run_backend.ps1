# NL2DB Backend Runner for PowerShell
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting NL2DB Backend Server (FastAPI + LangGraph)   " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot

# 1. Check for Virtual Environment
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[!] Virtual environment not found. Creating .venv..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment. Ensure Python is installed."
        exit 1
    }
    Write-Host "[*] Installing backend dependencies..." -ForegroundColor Green
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
}

# 2. Check for .env file
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "[*] Copying .env.example to .env..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
    }
}

# 3. Seed sample SQLite database if missing
if (-not (Test-Path "data\nl2db_sample.db")) {
    Write-Host "[*] Seeding sample SQLite database..." -ForegroundColor Yellow
    .\.venv\Scripts\python.exe backend\scripts\seed_local_dbs.py
}

# 4. Start Uvicorn Server
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Backend running at: http://localhost:8000            " -ForegroundColor Green
Write-Host "  Swagger Docs:       http://localhost:8000/docs       " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

& ".\.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
