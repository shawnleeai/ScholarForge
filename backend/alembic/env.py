"""
Alembic 迁移环境配置
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入模型基类
from shared.database.base import Base
from shared.database.config import DatabaseConfig

# 自动导入所有模型以确保它们被注册到Base.metadata
from shared.database import models

# Alembic配置对象
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据
target_metadata = Base.metadata


def get_database_url() -> str:
    """获取数据库URL"""
    # 优先从环境变量读取
    db_config = DatabaseConfig.from_env()
    return db_config.sync_dsn


def run_migrations_offline() -> None:
    """
    离线运行迁移 (生成SQL脚本)
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # 比较列类型变更
        compare_server_default=True,  # 比较默认值
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步运行迁移"""
    # 创建配置
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在线运行迁移 (直接操作数据库)
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
