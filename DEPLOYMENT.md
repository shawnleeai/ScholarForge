# ScholarForge 部署指南

## 快速开始

### 使用 Docker Compose 部署

```bash
# 1. 克隆项目
git clone https://github.com/your-org/scholarforge.git
cd scholarforge

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必要配置

# 3. 启动服务
docker-compose up -d

# 4. 检查状态
docker-compose ps
```

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 8GB 内存
- 至少 50GB 磁盘空间

## 生产环境部署

### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 配置域名和 SSL

使用 Nginx Proxy Manager 或 Traefik 处理反向代理和 SSL。

### 3. 数据库备份

```bash
# 备份 PostgreSQL
docker exec scholarforge-postgres pg_dump -U scholarforge scholarforge > backup.sql

# 恢复 PostgreSQL
docker exec -i scholarforge-postgres psql -U scholarforge scholarforge < backup.sql
```

## 监控

- 使用 Prometheus + Grafana 监控
- 日志收集：使用 ELK Stack 或 Loki

## 故障排查

```bash
# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f ai-service

# 重启服务
docker-compose restart

# 重新构建
docker-compose up -d --build
```
