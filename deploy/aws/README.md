# AWS 部署指南

## 架构概览

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                               AWS Cloud                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     Route 53 (DNS)                                    │   │
│  │                   CloudFront (CDN)                                    │   │
│  └───────────────────────────┬──────────────────────────────────────────┘   │
│                              │                                                │
│  ┌───────────────────────────┴──────────────────────────────────────────┐   │
│  │                    Application Load Balancer                          │   │
│  │                   (HTTPS, WebSocket支持)                               │   │
│  └───────────────────────┬──────────────────────────────────────────────┘   │
│                          │                                                    │
│      ┌───────────────────┼───────────────────┐                             │
│      ▼                   ▼                   ▼                             │
│ ┌────────────┐    ┌────────────┐    ┌────────────┐                        │
│ │   ECS      │    │   ECS      │    │   ECS      │   ECS Fargate 集群      │
│ │  Service 1 │    │  Service 2 │    │  Service 3 │   (容器编排)             │
│ └─────┬──────┘    └─────┬──────┘    └─────┬──────┘                        │
│       └───────────────────┴───────────────────┘                             │
│                           │                                                  │
│  ┌────────────────────────┼────────────────────────────────────────────┐   │
│  │                        ▼                                             │   │
│  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │ │   RDS       │  │  ElastiCache│  │     S3      │  │  OpenSearch │  │   │
│  │ │ PostgreSQL  │  │   Redis     │  │  对象存储    │  │ 搜索引擎    │  │   │
│  │ └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    CloudWatch (监控告警)                             │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
```

## 部署组件

### 1. RDS PostgreSQL

使用 AWS CLI 创建:
```bash
aws rds create-db-instance \
  --db-instance-identifier scholarforge-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16.1 \
  --allocated-storage 100 \
  --storage-type gp3 \
  --master-username postgres \
  --master-user-password your-secure-password \
  --vpc-security-group-ids sg-xxxxxx \
  --db-subnet-group-name scholarforge-db-subnet \
  --backup-retention-period 7 \
  --enable-performance-insights \
  --enable-cloudwatch-logs-exports 'postgresql'
```

环境变量:
```bash
DB_TYPE=postgresql
DB_HOST=scholarforge-db.xxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=scholarforge
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_SSL_MODE=require
```

### 2. ElastiCache Redis

创建Redis集群:
```bash
aws elasticache create-replication-group \
  --replication-group-id scholarforge-redis \
  --replication-group-description "ScholarForge Redis Cluster" \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-clusters 2 \
  --automatic-failover-enabled \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled
```

### 3. S3 对象存储

创建Bucket并配置:
```bash
aws s3 mb s3://scholarforge-data-us-east-1 --region us-east-1

# 配置CORS
aws s3api put-bucket-cors \
  --bucket scholarforge-data-us-east-1 \
  --cors-configuration file://cors-config.json

# 启用版本控制
aws s3api put-bucket-versioning \
  --bucket scholarforge-data-us-east-1 \
  --versioning-configuration Status=Enabled
```

### 4. ECS Fargate 部署

使用 AWS Copilot 简化部署:
```bash
# 初始化应用
copilot app init scholarforge

# 创建环境
copilot env init --name production --app scholarforge --region us-east-1

# 部署服务
copilot svc deploy --name gateway --env production
copilot svc deploy --name ai-service --env production
```

或使用 Terraform:
```bash
cd terraform/aws
terraform init
terraform plan
terraform apply
```

## Terraform 基础设施

主要资源:
- VPC (3个可用区)
- ECS Fargate 集群
- RDS PostgreSQL
- ElastiCache Redis
- S3 Bucket
- Application Load Balancer
- CloudWatch Logs & Alarms
- IAM Roles & Policies

## 费用估算

| 组件 | 规格 | 月费用($) |
|------|------|----------|
| RDS PostgreSQL | db.t3.medium, 100GB | ~50 |
| ElastiCache Redis | cache.t3.micro | ~15 |
| ECS Fargate | 2 vCPU, 4GB x 3 | ~100 |
| ALB | | ~20 |
| S3 | 100GB | ~3 |
| CloudWatch | | ~5 |
| **总计** | | **~193/月** |
