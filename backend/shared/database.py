"""
数据库连接模块
SQLAlchemy 数据库配置（支持 SQLite 用于测试）
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import MetaData, create_engine, event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# 命名约定
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """声明式基类"""
    metadata = metadata


# 检测是否为测试模式（通过环境变量或数据库URL判断）
TESTING = os.getenv("TESTING", "true").lower() == "true"
SQLITE_URL = "sqlite+aiosqlite:///./test.db"


def get_async_database_url(url: str) -> str:
    """转换数据库URL为异步格式"""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# 创建异步引擎
if TESTING:
    engine = create_async_engine(
        SQLITE_URL,
        echo=settings.debug,
    )
else:
    # 生产环境配置优化
    engine = create_async_engine(
        get_async_database_url(settings.database_url),
        pool_size=settings.database_pool_size or 10,
        max_overflow=settings.database_max_overflow or 20,
        pool_pre_ping=True,  # 连接前ping检测
        pool_recycle=3600,   # 连接1小时后回收
        pool_timeout=30,     # 连接池超时
        echo=settings.debug,
        # 执行选项优化
        execution_options={
            "isolation_level": "READ_COMMITTED",
        },
    )

# 创建会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（依赖注入）"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """数据库会话上下文管理器"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
