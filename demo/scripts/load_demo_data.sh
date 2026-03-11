#!/bin/bash
# ScholarForge 演示数据加载脚本
# 用法: ./load_demo_data.sh [数据库连接字符串]

set -e

echo "========================================"
echo "ScholarForge 演示数据加载工具"
echo "========================================"

# 默认数据库连接
DB_URL="${1:-postgresql://postgres:password@localhost:5432/scholarforge}"

echo ""
echo "数据库连接: $DB_URL"
echo ""

# 检查 psql 是否可用
if ! command -v psql &> /dev/null; then
    echo "错误: 未找到 psql 命令，请安装 PostgreSQL 客户端"
    exit 1
fi

# 检查数据库连接
echo "检查数据库连接..."
if ! psql "$DB_URL" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "错误: 无法连接到数据库，请检查连接字符串"
    exit 1
fi
echo "数据库连接成功"
echo ""

# 加载演示数据
echo "加载演示数据..."
psql "$DB_URL" -f demo/scripts/demo_scenario.sql

echo ""
echo "========================================"
echo "演示数据加载完成！"
echo "========================================"
echo ""
echo "演示用户信息:"
echo "  用户名: 王小明"
echo "  邮箱: xiaoming.wang@example.edu"
echo "  学校: 浙江大学"
echo "  专业: 工程管理（MEM）"
echo ""
echo "演示论文:"
echo "  标题: 基于多Agent协同的智能科研论文写作系统项目管理研究"
echo "  进度: 40% (第1、2章已完成)"
echo ""
echo "访问系统:"
echo "  演示模式已启用，访问 http://localhost:3000 将自动加载演示数据"
echo ""
