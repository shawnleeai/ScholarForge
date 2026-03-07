#!/usr/bin/env python3
"""
数据库初始化脚本

功能：
1. 创建数据库（如果不存在）
2. 运行 Alembic 迁移
3. 初始化基础数据（可选）

使用方法：
    python scripts/init_database.py [--seed]

环境变量：
    DATABASE_URL: 数据库连接URL
    DB_TYPE: 数据库类型 (postgresql/sqlite)
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from shared.database import db_manager, DatabaseConfig, DatabaseType
from shared.database.base import Base


async def create_database_if_not_exists():
    """如果数据库不存在则创建"""
    config = DatabaseConfig.from_env()

    if config.db_type == DatabaseType.SQLITE:
        # SQLite 不需要创建数据库
        print("SQLite mode: database file will be created automatically")
        return True

    if config.db_type == DatabaseType.POSTGRESQL:
        # 连接到默认数据库创建新数据库
        import asyncpg

        # 连接到 postgres 数据库
        conn_str = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/postgres"

        try:
            conn = await asyncpg.connect(conn_str)

            # 检查数据库是否存在
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                config.database
            )

            if not result:
                # 创建数据库
                await conn.execute(f"CREATE DATABASE {config.database}")
                print(f"Database '{config.database}' created successfully")
            else:
                print(f"Database '{config.database}' already exists")

            await conn.close()
            return True

        except Exception as e:
            print(f"Error creating database: {e}")
            return False

    return True


async def run_migrations():
    """运行 Alembic 迁移"""
    import subprocess

    backend_dir = Path(__file__).parent.parent

    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            check=True
        )
        print("Migrations applied successfully")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e}")
        print(e.stderr)
        return False


async def init_database():
    """初始化数据库连接"""
    config = DatabaseConfig.from_env()
    db_manager.initialize(config)

    # 创建表
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created")


async def seed_demo_data():
    """插入演示数据"""
    print("Seeding demo data...")

    # 这里可以调用 seed_demo_data.py
    try:
        from seed_demo_data import seed_all
        await seed_all()
        print("Demo data seeded successfully")
    except Exception as e:
        print(f"Warning: Failed to seed demo data: {e}")


async def main():
    parser = argparse.ArgumentParser(description="Initialize database")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed demo data after initialization"
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip running migrations"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("Database Initialization")
    print("=" * 50)

    # 1. 创建数据库
    print("\n1. Creating database if not exists...")
    if not await create_database_if_not_exists():
        print("Failed to create database")
        return 1

    # 2. 初始化数据库
    print("\n2. Initializing database...")
    await init_database()

    # 3. 运行迁移
    if not args.skip_migrations:
        print("\n3. Running migrations...")
        if not await run_migrations():
            print("Warning: Migration failed, but tables may still be created")

    # 4. 插入演示数据
    if args.seed:
        print("\n4. Seeding demo data...")
        await seed_demo_data()

    print("\n" + "=" * 50)
    print("Database initialization completed!")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
