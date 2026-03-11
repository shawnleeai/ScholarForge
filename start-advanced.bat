@echo off
chcp 65001 >nul
title ScholarForge 高级启动工具
cls

echo ============================================
echo   ScholarForge 高级启动工具
echo ============================================
echo.

:: 设置项目路径
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

:MENU
cls
echo ============================================
echo   ScholarForge 高级启动工具
echo ============================================
echo.
echo  [1] 启动所有服务（完整模式）
echo  [2] 仅启动后端服务（AI + 网关）
echo  [3] 仅启动前端服务
echo  [4] 启动单个微服务（选择）
echo  [5] 停止所有服务
echo  [6] 检查服务状态
echo  [7] 查看日志
echo  [8] 退出
echo.
echo ============================================
set /p CHOICE="请选择操作 [1-8]: "

if "%CHOICE%"=="1" goto START_ALL
if "%CHOICE%"=="2" goto START_BACKEND
if "%CHOICE%"=="3" goto START_FRONTEND
if "%CHOICE%"=="4" goto START_SINGLE
if "%CHOICE%"=="5" goto STOP_ALL
if "%CHOICE%"=="6" goto CHECK_STATUS
if "%CHOICE%"=="7" goto VIEW_LOGS
if "%CHOICE%"=="8" exit /b 0
goto MENU

:START_ALL
echo.
echo [模式] 启动所有服务（完整模式）
echo.
call :CHECK_ENV
call :CREATE_LOGS_DIR

set "LOG_TIME=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "LOG_TIME=%LOG_TIME: =0%"

echo [1/3] 正在启动AI服务 (端口8004)...
start "SF-AI" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn services.ai.main:app --host 0.0.0.0 --port 8004 --reload 2^>^&1 ^| tee ..\logs\ai-%LOG_TIME%.log"

echo [2/3] 正在启动API网关 (端口8000)...
timeout /t 3 >nul
start "SF-Gateway" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload 2^>^&1 ^| tee ..\logs\gateway-%LOG_TIME%.log"

echo [3/3] 正在启动前端服务...
timeout /t 3 >nul
start "SF-Frontend" cmd /k "cd /d "%PROJECT_DIR%\frontend" && npm run dev 2^>^&1 ^| tee ..\logs\frontend-%LOG_TIME%.log"

call :SHOW_SUCCESS
pause
goto MENU

:START_BACKEND
echo.
echo [模式] 仅启动后端服务
echo.
call :CHECK_ENV
call :CREATE_LOGS_DIR

echo [1/2] 正在启动AI服务 (端口8004)...
start "SF-AI" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn services.ai.main:app --host 0.0.0.0 --port 8004 --reload"

echo [2/2] 正在启动API网关 (端口8000)...
timeout /t 3 >nul
start "SF-Gateway" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo ============================================
echo   后端服务已启动！
echo ============================================
echo.
echo API地址:
echo   - API网关:  http://localhost:8000
echo   - API文档:  http://localhost:8000/docs
echo.
pause
goto MENU

:START_FRONTEND
echo.
echo [模式] 仅启动前端服务
echo.
call :CHECK_NPM
start "SF-Frontend" cmd /k "cd /d "%PROJECT_DIR%\frontend" && npm run dev"
call :SHOW_SUCCESS
pause
goto MENU

:START_SINGLE
cls
echo ============================================
echo   启动单个微服务
echo ============================================
echo.
echo  [1] 用户服务 (端口8001)
echo  [2] 文献服务 (端口8002)
echo  [3] 论文服务 (端口8003)
echo  [4] AI服务 (端口8004) - 已配置阶跃星辰
echo  [5] 推荐服务 (端口8005)
echo  [6] 返回上级菜单
echo.
set /p SVC="请选择服务 [1-6]: "

if "%SVC%"=="1" start "SF-User" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn services.user.main:app --host 0.0.0.0 --port 8001 --reload"
if "%SVC%"=="2" start "SF-Article" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn services.article.main:app --host 0.0.0.0 --port 8002 --reload"
if "%SVC%"=="3" start "SF-Paper" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn services.paper.main:app --host 0.0.0.0 --port 8003 --reload"
if "%SVC%"=="4" start "SF-AI" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn services.ai.main:app --host 0.0.0.0 --port 8004 --reload"
if "%SVC%"=="5" start "SF-Recommend" cmd /k "cd /d "%PROJECT_DIR%\backend" && call venv\Scripts\activate && python -m uvicorn services.recommendation.main:app --host 0.0.0.0 --port 8005 --reload"
if "%SVC%"=="6" goto MENU

echo.
echo 服务已启动！
pause
goto MENU

:STOP_ALL
call stop-all.bat
goto MENU

:CHECK_STATUS
call check-status.bat
goto MENU

:VIEW_LOGS
cls
echo ============================================
echo   查看日志文件
echo ============================================
echo.
if exist "logs" (
    dir /b /o-d logs\*.log 2>nul | head -10
    if errorlevel 1 echo 暂无日志文件
) else (
    echo 日志目录不存在
)
echo.
pause
goto MENU

:: ========== 子程序 ==========

:CHECK_ENV
if not exist "backend\venv\Scripts\activate.bat" (
    echo [错误] 未找到Python虚拟环境
    pause
    goto MENU
)
exit /b 0

:CHECK_NPM
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到npm，请安装Node.js
    pause
    goto MENU
)
exit /b 0

:CREATE_LOGS_DIR
if not exist "logs" mkdir logs
exit /b 0

:SHOW_SUCCESS
echo.
echo ============================================
echo   所有服务已启动！
echo ============================================
echo.
echo 访问地址:
echo   - 前端界面: http://localhost:5173
echo   - API网关:  http://localhost:8000
echo   - API文档:  http://localhost:8000/docs
echo.
echo 按任意键打开浏览器...
timeout /t 3 >nul
start http://localhost:5173
exit /b 0
