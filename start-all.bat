@echo off
chcp 65001 >nul
cls

echo ============================================
echo   ScholarForge Start Script
echo ============================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist "backend\venv\Scripts\activate.bat" (
    echo [Error] Python virtual environment not found
    echo Please create it first: cd backend && python -m venv venv
    pause
    exit /b 1
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [Error] npm not found, please install Node.js
    pause
    exit /b 1
)

if not exist "logs" mkdir logs

echo [1/3] Starting AI Service (port 8004)...
start "SF-AI" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn services.ai.main:app --host 0.0.0.0 --port 8004 --reload"

echo [2/3] Starting API Gateway (port 8000)...
timeout /t 2 >nul
start "SF-Gateway" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/3] Starting Frontend Service...
timeout /t 2 >nul
start "SF-Frontend" cmd /k "cd /d "%PROJECT_DIR%\frontend" && npm run dev"

echo.
echo ============================================
echo   All services started successfully!
echo ============================================
echo.
echo Access URLs:
echo   - Frontend: http://localhost:5173
echo   - API Gateway: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
pause

start http://localhost:5173
