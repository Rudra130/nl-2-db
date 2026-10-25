# NL2DB Frontend Runner for PowerShell
Write-Host "========================================================" -ForegroundColor Magenta
Write-Host "  Starting NL2DB Frontend Client (React + Vite)         " -ForegroundColor Magenta
Write-Host "========================================================" -ForegroundColor Magenta

Set-Location "$PSScriptRoot\frontend"

# 1. Check for node_modules
if (-not (Test-Path "node_modules")) {
    Write-Host "[*] node_modules not found. Running npm install..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "npm install failed. Ensure Node.js (v18+) is installed."
        exit 1
    }
}

# 2. Start Vite Dev Server
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Frontend running at: http://localhost:5173            " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

npm run dev
