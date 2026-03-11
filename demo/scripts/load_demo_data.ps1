# ScholarForge 演示数据加载脚本 (Windows PowerShell)
# 用法: .\load_demo_data.ps1 [数据库连接字符串]

param(
    [string]$DbUrl = "postgresql://postgres:password@localhost:5432/scholarforge"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ScholarForge 演示数据加载工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "数据库连接: $DbUrl" -ForegroundColor Yellow
Write-Host ""

# 检查 psql 是否可用
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue
if (-not $psqlPath) {
    Write-Host "错误: 未找到 psql 命令，请安装 PostgreSQL 客户端并将其添加到 PATH" -ForegroundColor Red
    exit 1
}

# 检查数据库连接
Write-Host "检查数据库连接..." -ForegroundColor Yellow
try {
    $result = psql $DbUrl -c "SELECT 1;" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "连接失败"
    }
} catch {
    Write-Host "错误: 无法连接到数据库，请检查连接字符串" -ForegroundColor Red
    exit 1
}
Write-Host "数据库连接成功" -ForegroundColor Green
Write-Host ""

# 加载演示数据
Write-Host "加载演示数据..." -ForegroundColor Yellow
psql $DbUrl -f demo/scripts/demo_scenario.sql

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "演示数据加载完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "演示用户信息:" -ForegroundColor Cyan
    Write-Host "  用户名: 王小明"
    Write-Host "  邮箱: xiaoming.wang@example.edu"
    Write-Host "  学校: 浙江大学"
    Write-Host "  专业: 工程管理（MEM）"
    Write-Host ""
    Write-Host "演示论文:" -ForegroundColor Cyan
    Write-Host "  标题: 基于多Agent协同的智能科研论文写作系统项目管理研究"
    Write-Host "  进度: 40% (第1、2章已完成)"
    Write-Host ""
    Write-Host "访问系统:" -ForegroundColor Cyan
    Write-Host "  演示模式已启用，访问 http://localhost:3000 将自动加载演示数据"
    Write-Host ""
} else {
    Write-Host "错误: 演示数据加载失败" -ForegroundColor Red
    exit 1
}
