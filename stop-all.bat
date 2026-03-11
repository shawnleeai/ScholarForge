@echo off
chcp 65001 >nul
cls

echo ============================================
echo   ScholarForge Stop All Services
echo ============================================
echo.

echo Stopping services...
echo.

echo [1/3] Stopping AI Service...
taskkill /FI "WINDOWTITLE eq SF-AI*" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq *8004*" /F >nul 2>nul

echo [2/3] Stopping API Gateway...
taskkill /FI "WINDOWTITLE eq SF-Gateway*" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq *8000*" /F >nul 2>nul

echo [3/3] Stopping Frontend...
taskkill /FI "WINDOWTITLE eq SF-Frontend*" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Vite*" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq npm*" /F >nul 2>nul

timeout /t 1 >nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8004') do (
    taskkill /PID %%a /F >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /PID %%a /F >nul 2>nul
)

echo.
echo ============================================
echo   All services stopped
echo ============================================
echo.
pause
