@echo off
chcp 65001 >nul
echo ============================================
echo ScholarForge 配置文件设置工具
echo ============================================
echo.

:: 检查.env文件是否存在
if not exist ".env" (
    echo [错误] 未找到 .env 文件
    echo 请确保此脚本在项目根目录下运行
    pause
    exit /b 1
)

:: 备份原配置
echo [1/2] 备份原配置文件...
copy .env .env.backup >nul 2>&1
echo 已备份为 .env.backup
echo.

:: 提示用户输入
echo [2/2] 请输入API Key（直接回车跳过）
echo.

set /p STEPFUN_KEY="阶跃星辰 API Key: "
set /p DEEPSEEK_KEY="DeepSeek API Key: "
set /p MOONSHOT_KEY="Moonshot API Key: "
set /p OPENAI_KEY="OpenAI API Key: "

:: 替换配置
echo.
echo 正在更新配置文件...

if not "%STEPFUN_KEY%"=="" (
    powershell -Command "(Get-Content .env) -replace 'STEPFUN_API_KEY=your-stepfun-api-key-here', 'STEPFUN_API_KEY=%STEPFUN_KEY%' | Set-Content .env"
    echo [✓] 已配置阶跃星辰
)

if not "%DEEPSEEK_KEY%"=="" (
    powershell -Command "(Get-Content .env) -replace 'DEEPSEEK_API_KEY=your-deepseek-api-key-here', 'DEEPSEEK_API_KEY=%DEEPSEEK_KEY%' | Set-Content .env"
    echo [✓] 已配置 DeepSeek
)

if not "%MOONSHOT_KEY%"=="" (
    powershell -Command "(Get-Content .env) -replace 'MOONSHOT_API_KEY=your-moonshot-api-key-here', 'MOONSHOT_API_KEY=%MOONSHOT_KEY%' | Set-Content .env"
    echo [✓] 已配置 Moonshot
)

if not "%OPENAI_KEY%"=="" (
    powershell -Command "(Get-Content .env) -replace 'OPENAI_API_KEY=your-openai-api-key-here', 'OPENAI_API_KEY=%OPENAI_KEY%' | Set-Content .env"
    echo [✓] 已配置 OpenAI
)

echo.
echo ============================================
echo 配置完成！
echo ============================================
echo.
echo 接下来请：
echo 1. 编辑 .env 文件修改数据库密码等其他配置
echo 2. 启动后端服务: python run.py ai
echo 3. 启动前端服务: npm run dev
echo.
pause
