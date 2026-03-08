#!/bin/bash
# ScholarForge Docker 启动脚本

set -e

echo "==================================="
echo "  ScholarForge Docker 启动脚本"
echo "==================================="
echo ""

# 检查环境
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✅ Docker 环境检查通过"
echo ""

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在，复制 .env.example"
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置必要参数"
fi

# 创建必要目录
echo "📁 创建数据目录..."
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/elasticsearch
mkdir -p data/neo4j
mkdir -p data/minio

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d --build

echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker-compose ps

echo ""
echo "==================================="
echo "✅ ScholarForge 启动完成!"
echo "==================================="
echo ""
echo "访问地址:"
echo "  前端界面: http://localhost:3000"
echo "  API文档:  http://localhost:8000/docs"
echo "  Kong管理: http://localhost:8001"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
