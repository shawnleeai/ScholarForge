# ScholarForge Docker 部署指南

## 前提条件

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ 内存
- 50GB+ 磁盘空间

## 快速部署

### 1. 环境准备

```bash
# 复制环境变量配置
cp .env.example .env

# 编辑 .env 文件，配置必要参数
vim .env
```

### 2. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 访问服务

- 前端界面: http://localhost:3000
- API 文档: http://localhost:8000/docs
- Kong 管理: http://localhost:8001

### 4. 数据库初始化

```bash
# 运行数据库迁移
docker-compose exec backend python scripts/init_database.py --seed
```

### 5. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v
```

## 生产部署

### 使用 Docker Swarm

```bash
# 初始化 Swarm
docker swarm init

# 部署服务栈
docker stack deploy -c docker-compose.yml scholarforge

# 查看服务状态
docker stack ps scholarforge
```

### 使用 Kubernetes

```bash
# 应用配置
kubectl apply -f deploy/k8s/

# 查看 Pod 状态
kubectl get pods -n scholarforge
```

## 故障排查

```bash
# 查看服务日志
docker-compose logs [service-name]

# 进入容器
docker-compose exec [service-name] /bin/sh

# 重启服务
docker-compose restart [service-name]
```

## 备份和恢复

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U scholarforge scholarforge > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U scholarforge scholarforge < backup.sql
```
