# ScholarForge 部署指南

本文档详细介绍如何在本地环境或阿里云服务器上部署 ScholarForge 学术协作平台。

## 目录
1. [环境准备](#环境准备)
2. [本地部署](#本地部署)
3. [阿里云部署](#阿里云部署)
4. [数据库配置](#数据库配置)
5. [环境变量说明](#环境变量说明)
6. [常见问题排查](#常见问题排查)

---

## 环境准备

### 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 50GB SSD | 100GB SSD |
| 操作系统 | Ubuntu 20.04+ / CentOS 7+ | Ubuntu 22.04 LTS |
| Node.js | 18.x | 20.x |
| Python | 3.10+ | 3.11+ |
| PostgreSQL | 14+ | 15+ |

### 必需软件安装

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git curl wget vim nginx

# 安装 Node.js (使用 nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

# 安装 Python
sudo apt install -y python3.11 python3.11-venv python3-pip

# 安装 PostgreSQL
sudo apt install -y postgresql-15 postgresql-contrib

# 安装 Redis (用于缓存和消息队列)
sudo apt install -y redis-server

# 安装 PM2 (进程管理)
npm install -g pm2
```

---

## 本地部署

### 1. 数据库配置

#### 创建数据库

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE scholarforge;
CREATE USER sf_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE scholarforge TO sf_user;

# 退出
\q
```

#### 初始化数据库表

```bash
cd /path/to/scholarforge/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 或使用 SQLAlchemy 自动创建（仅开发环境）
python -c "from shared.database import db_manager, DatabaseConfig; db_manager.initialize(DatabaseConfig()); import asyncio; asyncio.run(db_manager.create_tables())"
```

### 2. 后端服务配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
vim .env
```

`.env` 文件示例：
```env
# 应用配置
APP_NAME=ScholarForge
APP_VERSION=1.0.0
DEBUG=true
SECRET_KEY=your-secret-key-here

# 数据库配置 (本地 PostgreSQL)
DATABASE_URL=postgresql+asyncpg://sf_user:your_secure_password@localhost:5432/scholarforge

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 文件存储 (本地模式)
STORAGE_TYPE=local
UPLOAD_DIR=./uploads

# AI API Keys (可选，用于真实AI功能)
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
```

### 3. 启动后端服务

```bash
# 方式1: 使用 Python 直接启动（开发）
python -m services.gateway.main  # 网关服务，端口 8000

# 方式2: 使用 PM2 启动（生产）
pm2 start ecosystem.config.js
```

### 4. 前端配置

```bash
cd /path/to/scholarforge/frontend

# 安装依赖
npm install

# 复制环境变量
cp .env.development .env.local

# 开发模式启动
npm run dev

# 构建生产版本
npm run build
```

### 5. 访问应用

- 前端：http://localhost:5173
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

---

## 阿里云部署

### 1. 购买服务器

推荐配置：
- **ECS 实例**：ecs.c7.large（2核4G）或更高
- **系统盘**：100GB SSD
- **操作系统**：Ubuntu 22.04 LTS
- **带宽**：5Mbps 以上（用于文件上传下载）

### 2. 安全组配置

在阿里云控制台配置安全组规则：

| 端口 | 用途 | 授权对象 |
|------|------|---------|
| 22 | SSH | 你的IP |
| 80 | HTTP | 0.0.0.0/0 |
| 443 | HTTPS | 0.0.0.0/0 |
| 8000 | API服务 | 0.0.0.0/0 |
| 5173 | 开发前端 | 你的IP |

### 3. 数据库选择

#### 方案A: 阿里云 RDS PostgreSQL（推荐生产环境）

1. 创建 RDS 实例
   - 类型：PostgreSQL 15
   - 规格：1核2G（最低）
   - 存储：100GB SSD

2. 获取连接信息
   - 内网地址：`pgm-xxx.pg.rds.aliyuncs.com`
   - 端口：5432
   - 数据库：scholarforge
   - 用户名：sf_admin

3. 配置白名单
   - 将 ECS 实例的内网 IP 加入 RDS 白名单

#### 方案B: 本地 PostgreSQL（测试环境）

在 ECS 上直接安装 PostgreSQL（同本地部署）。

### 4. 域名和SSL配置

#### 购买域名并解析

在阿里云域名服务购买域名，添加 A 记录：
- `@` 指向 ECS 公网IP
- `api` 指向 ECS 公网IP（可选，用于API子域名）

#### 安装 SSL 证书

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自动续期
sudo systemctl enable certbot.timer
```

### 5. Nginx 配置

```bash
sudo vim /etc/nginx/sites-available/scholarforge
```

配置内容：
```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 前端配置
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # 前端静态文件
    location / {
        root /var/www/scholarforge/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location /assets {
        root /var/www/scholarforge/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# API 网关配置
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # 文件上传大小限制
        client_max_body_size 100M;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/scholarforge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. 部署脚本

创建自动化部署脚本：

```bash
vim /var/www/scholarforge/deploy.sh
```

```bash
#!/bin/bash

# 部署脚本

echo "🚀 开始部署 ScholarForge..."

# 拉取最新代码
cd /var/www/scholarforge
git pull origin main

# 部署后端
echo "📦 部署后端..."
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 重启服务
pm2 reload ecosystem.config.js

# 部署前端
echo "🎨 部署前端..."
cd ../frontend
npm install
npm run build

# 复制到 Nginx 目录
sudo cp -r dist/* /var/www/html/scholarforge/

echo "✅ 部署完成！"
```

赋予执行权限：
```bash
chmod +x /var/www/scholarforge/deploy.sh
```

### 7. PM2 配置

创建 `ecosystem.config.js`：

```javascript
module.exports = {
  apps: [
    {
      name: 'sf-gateway',
      script: './backend/gateway/main.py',
      interpreter: './backend/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PORT: 8000
      },
      log_file: './logs/gateway.log',
      out_file: './logs/gateway-out.log',
      error_file: './logs/gateway-error.log'
    }
  ]
};
```

### 8. 阿里云 OSS 配置（可选，用于文件存储）

```bash
# 安装阿里云 SDK
pip install oss2
```

在 `.env` 中配置：
```env
STORAGE_TYPE=oss
OSS_ACCESS_KEY_ID=your-access-key
OSS_ACCESS_KEY_SECRET=your-secret
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET=scholarforge-files
```

---

## 数据库配置

### 本地 PostgreSQL

```bash
# 优化 PostgreSQL 配置
sudo vim /etc/postgresql/15/main/postgresql.conf
```

推荐配置：
```conf
# 内存设置（根据服务器调整）
shared_buffers = 1GB
work_mem = 16MB
maintenance_work_mem = 256MB

# 连接设置
max_connections = 200

# WAL 设置
wal_buffers = 16MB
max_wal_size = 2GB
min_wal_size = 512MB

# 日志设置
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'mod'
```

### 阿里云 RDS

1. 在 RDS 控制台创建账号和数据库
2. 配置连接参数：

```env
# 内网连接（ECS 和 RDS 同地域）
DATABASE_URL=postgresql+asyncpg://sf_admin:password@pgm-xxx.pg.rds.aliyuncs.com:5432/scholarforge

# 外网连接（本地开发测试）
DATABASE_URL=postgresql+asyncpg://sf_admin:password@pgm-xxx.pg.rds.aliyuncs.com:5432/scholarforge
```

---

## 环境变量说明

### 后端环境变量 (.env)

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `APP_NAME` | 应用名称 | ScholarForge |
| `DEBUG` | 调试模式 | false |
| `SECRET_KEY` | JWT密钥 | random-string-32-chars |
| `DATABASE_URL` | 数据库连接 | postgresql+asyncpg://... |
| `REDIS_URL` | Redis连接 | redis://localhost:6379 |
| `STORAGE_TYPE` | 存储类型 | local/oss |
| `OPENAI_API_KEY` | OpenAI API | sk-... |
| `DEEPSEEK_API_KEY` | DeepSeek API | sk-... |

### 前端环境变量 (.env.production)

```env
# API 地址
VITE_API_BASE_URL=https://api.yourdomain.com

# WebSocket 地址
VITE_WS_URL=wss://api.yourdomain.com

# 是否启用 Mock
VITE_USE_MOCK=false

# 上传大小限制
VITE_MAX_UPLOAD_SIZE=50
```

---

## 常见问题排查

### 1. 数据库连接失败

**症状**: 后端启动报错 `Connection refused`

**排查步骤**:
```bash
# 1. 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 2. 检查端口监听
sudo netstat -tlnp | grep 5432

# 3. 检查防火墙
sudo ufw status
sudo ufw allow 5432

# 4. 检查 pg_hba.conf
sudo vim /etc/postgresql/15/main/pg_hba.conf
# 添加: host all all 0.0.0.0/0 md5
```

### 2. Nginx 502 错误

**症状**: 前端页面加载但 API 返回 502

**排查**:
```bash
# 检查后端是否运行
pm2 status
curl http://localhost:8000/health

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 3. 文件上传失败

**症状**: 上传 PDF 时超时或失败

**解决方案**:
```bash
# 1. 检查 Nginx 配置中的 client_max_body_size
# 2. 检查后端文件大小限制
# 3. 检查磁盘空间
df -h
```

### 4. WebSocket 连接失败

**症状**: 实时协作功能不工作

**检查**:
```bash
# Nginx 配置是否包含
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### 5. CORS 错误

**症状**: 浏览器控制台报 CORS 错误

**解决**: 检查后端 CORS 配置，确保包含前端域名：
```python
allow_origins=["https://yourdomain.com"]
```

---

## 监控与维护

### 查看日志

```bash
# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 应用日志
pm2 logs

# 数据库日志
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### 备份策略

```bash
# 数据库备份脚本
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump scholarforge > $BACKUP_DIR/sf_backup_$DATE.sql

# 保留最近30天的备份
find $BACKUP_DIR -name "sf_backup_*.sql" -mtime +30 -delete
```

### 系统监控

```bash
# 安装 htop 监控系统资源
sudo apt install htop

# 查看磁盘使用
df -h

# 查看内存使用
free -h
```

---

## 总结

按照以上步骤，你应该能够成功部署 ScholarForge：

1. **本地部署**: 适合开发测试，使用本地 PostgreSQL
2. **阿里云部署**: 适合生产环境，使用 RDS + ECS + OSS
3. **关键配置**: 数据库连接、Nginx 反向代理、SSL 证书

如有问题，请查看日志或提交 Issue。
