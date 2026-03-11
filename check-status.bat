@echo off
chcp 65001 >nul
cls

echo ============================================
echo   ScholarForge Service Status Check
echo ============================================
echo.

set "ALL_READY=true"

echo [1/3] Checking AI Service (port 8004)...
curl -s http://localhost:8004/health >nul 2>nul
if %errorlevel% equ 0 (
    echo   [OK] AI Service is running
) else (
    echo   [X] AI Service is not running
    set "ALL_READY=false"
)

echo [2/3] Checking API Gateway (port 8000)...
curl -s http://localhost:8000/health >nul 2>nul
if %errorlevel% equ 0 (
    echo   [OK] API Gateway is running
) else (
    echo   [X] API Gateway is not running
    set "ALL_READY=false"
)

echo [3/3] Checking Frontend (port 5173)...
curl -s http://localhost:5173 >nul 2>nul
if %errorlevel% equ 0 (
    echo   [OK] Frontend is running
) else (
    echo   [X] Frontend is not running
    set "ALL_READY=false"
)

echo.
echo ============================================

if "%ALL_READY%"=="true" (
    echo   [OK] All services are running!
    echo ============================================
    echo.
    echo Access URLs:
    echo   - Frontend: http://localhost:5173
    echo   - API Gateway: http://localhost:8000
    echo   - API Docs: http://localhost:8000/docs
) else (
    echo   [X] Some services are not running
    echo ============================================
    echo.
    echo Please run start-all.bat to start services
)

echo.
pause
