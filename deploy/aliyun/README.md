# 阿里云部署指南

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        阿里云                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  SLB 负载均衡                        │   │
│  │              (HTTPS 终止, 流量分发)                   │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       │                                      │
│       ┌───────────────┼───────────────┐                    │
│       ▼               ▼               ▼                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                │
│  │  ECS-1  │    │  ECS-2  │    │  ECS-3  │   ECS 集群      │
│  │ (网关)   │    │ (AI服务) │    │(文献服务)│   (容器化部署)   │
│  └────┬────┘    └────┬────┘    └────┬────┘                │
│       └───────────────┴───────────────┘                    │
│                       │                                      │
│  ┌────────────────────┼────────────────────────────────┐   │
│  │                    ▼                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │   RDS       │  │   Redis     │  │    OSS      │  │   │
│  │  │ PostgreSQL  │  │  企业版      │  │  对象存储    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 部署组件

### 1. RDS PostgreSQL

创建RDS实例:
```bash
aliyun rds CreateDBInstance \
  --RegionId cn-hangzhou \
  --Engine PostgreSQL \
  --EngineVersion 16.0 \
  --DBInstanceClass rds.pg.s1.large \
  --DBInstanceStorage 100 \
  --DBInstanceNetType Intranet \
  --SecurityIPList "10.0.0.0/8"
```

连接信息环境变量:
```bash
DB_TYPE=postgresql
DB_HOST=your-rds-id.pg.rds.aliyuncs.com
DB_PORT=5432
DB_NAME=scholarforge
DB_USER=scholarforge
DB_PASSWORD=your-secure-password
DB_SSL_MODE=require
```

### 2. Redis 企业版

创建Redis实例:
```bash
aliyun r-kvstore CreateInstance \
  --RegionId cn-hangzhou \
  --InstanceType Redis \
  --EngineVersion 7.0 \
  --InstanceClass redis.shard.small.2.ce
```

连接信息:
```bash
REDIS_URL=rediss://:password@your-redis-id.redis.rds.aliyuncs.com:6379/0
```

### 3. OSS 对象存储

创建Bucket:
```bash
aliyun oss mb oss://scholarforge-data --region cn-hangzhou
```

配置跨域:
```bash
aliyun oss cors --method put oss://scholarforge-data \
  --cors-configuration file://cors-config.json
```

### 4. ECS 容器部署

使用Docker Compose部署:
```bash
# 登录阿里云容器镜像服务
docker login --username=your-name registry.cn-hangzhou.aliyuncs.com

# 拉取镜像
docker pull registry.cn-hangzhou.aliyuncs.com/scholarforge/gateway:latest

# 启动服务
docker-compose -f docker-compose.aliyun.yml up -d
```

## Terraform 部署

```bash
cd terraform/aliyun
terraform init
terraform plan
terraform apply
```

## 费用估算

| 组件 | 规格 | 月费用(元) |
|------|------|----------|
| RDS PostgreSQL | 2核4G, 100G | ~400 |
| Redis 企业版 | 1G | ~200 |
| OSS | 100G存储 | ~10 |
| ECS (3台) | 2核4G | ~600 |
| SLB | 标准型 | ~100 |
| **总计** | | **~1310/月** |
