# ScholarForge PowerShell Startup Script
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PROJECT_DIR

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   ScholarForge Start Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (-not (Test-Path "backend\venv\Scripts\activate.bat")) {
    Write-Host "[Error] Python virtual environment not found" -ForegroundColor Red
    pause
    exit 1
}

# Check npm
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "[Error] npm not found, please install Node.js" -ForegroundColor Red
    pause
    exit 1
}

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

Write-Host "[1/3] Starting AI Service (port 8004)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd '$PROJECT_DIR\backend'; .\venv\Scripts\activate; python -m uvicorn services.ai.main:app --host 0.0.0.0 --port 8004 --reload" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "[2/3] Starting API Gateway (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd '$PROJECT_DIR\backend'; .\venv\Scripts\activate; python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "[3/3] Starting Frontend Service..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd '$PROJECT_DIR\frontend'; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   All services started successfully!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:"
Write-Host "  - Frontend: http://localhost:5173"
Write-Host "  - API Gateway: http://localhost:8000"
Write-Host "  - API Docs: http://localhost:8000/docs"
Write-Host ""

pause
Start-Process "http://localhost:5173"
