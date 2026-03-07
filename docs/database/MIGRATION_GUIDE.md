# 数据库迁移指南

## 概述

本项目使用 **Alembic** 进行数据库迁移管理。

## 快速开始

### 1. 初始化数据库

```bash
cd backend

# 自动创建数据库和表
python scripts/init_database.py

# 创建数据库并插入演示数据
python scripts/init_database.py --seed
```

### 2. 创建新迁移

当你修改了模型后，创建新的迁移脚本：

```bash
cd backend

# 自动生成迁移脚本
alembic revision --autogenerate -m "描述修改内容"

# 示例
alembic revision --autogenerate -m "add_user_preferences_table"
```

### 3. 运行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade 0001

# 降级一个版本
alembic downgrade -1

# 降级到指定版本
alembic downgrade 0001
```

### 4. 查看迁移历史

```bash
# 查看当前版本
alembic current

# 查看历史
alembic history

# 查看历史（详细）
alembic history --verbose
```

## 项目结构

```
backend/
├── alembic/
│   ├── versions/          # 迁移脚本目录
│   │   ├── 0001_initial.py
│   │   └── ...
│   ├── env.py            # 迁移环境配置
│   └── script.py.mako    # 迁移脚本模板
├── alembic.ini           # Alembic 配置文件
└── scripts/
    └── init_database.py  # 数据库初始化脚本
```

## 编写迁移脚本

### 基本结构

```python
"""Migration description

Revision ID: xxxx
Revises: yyyy
Create Date: 2026-03-08 xx:xx:xx.xxxxxx

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0002'
down_revision = '0001'

def upgrade():
    # 创建表
    op.create_table(
        'new_table',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
    )

def downgrade():
    # 删除表
    op.drop_table('new_table')
```

### 常用操作

```python
# 创建表
op.create_table('users', ...)

# 删除表
op.drop_table('users')

# 添加列
op.add_column('users', sa.Column('age', sa.Integer()))

# 删除列
op.drop_column('users', 'age')

# 创建索引
op.create_index('idx_name', 'users', ['name'])

# 删除索引
op.drop_index('idx_name', 'users')

# 执行原始SQL
op.execute("INSERT INTO users (name) VALUES ('admin')")
```

## 最佳实践

1. **始终编写 downgrade**：确保可以回滚
2. **测试迁移**：在生产环境运行前先在测试环境验证
3. **不要修改已应用的迁移**：已应用的迁移不应再修改
4. **保持迁移原子性**：一个迁移只做一件事
5. **提交迁移脚本**：迁移脚本应该提交到版本控制

## 故障排查

### 迁移失败

```bash
# 查看当前版本
alembic current

# 手动标记为已应用（谨慎使用）
alembic stamp head

# 重置到空状态
alembic stamp base
```

### 数据库锁定

```sql
-- 查看锁
SELECT * FROM pg_locks WHERE NOT granted;

-- 终止连接
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'your_db';
```

## 环境配置

### 开发环境

```bash
# 使用 SQLite（无需配置）
export DB_TYPE=sqlite
export DATABASE_URL=sqlite+aiosqlite:///./dev.db
```

### 生产环境

```bash
# 使用 PostgreSQL
export DB_TYPE=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=scholarforge
export DB_USER=scholarforge
export DB_PASSWORD=your_password
```
