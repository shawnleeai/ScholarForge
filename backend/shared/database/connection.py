"""
数据库连接管理
提供异步数据库会话管理
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from .config import DatabaseConfig


class DatabaseManager:
    """数据库管理器"""

    _instance: Optional["DatabaseManager"] = None
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker] = None
    _config: Optional[DatabaseConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, config: DatabaseConfig) -> "DatabaseManager":
        """初始化数据库连接"""
        instance = cls()
        instance._config = config

        # 创建异步引擎
        engine_options = config.get_engine_options()
        instance._engine = create_async_engine(
            config.async_dsn,
            **engine_options,
        )

        # 创建会话工厂
        instance._session_factory = async_sessionmaker(
            instance._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        return instance

    @classmethod
    async def close(cls):
        """关闭数据库连接"""
        instance = cls._instance
        if instance and instance._engine:
            await instance._engine.dispose()
            instance._engine = None
            instance._session_factory = None

    @property
    def engine(self) -> AsyncEngine:
        """获取数据库引擎"""
        if self._engine is None:
            raise RuntimeError("数据库未初始化，请先调用 initialize()")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker:
        """获取会话工厂"""
        if self._session_factory is None:
            raise RuntimeError("数据库未初始化，请先调用 initialize()")
        return self._session_factory

    async def create_tables(self):
        """创建所有表 (仅用于开发和测试)"""
        from .base import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """删除所有表 (仅用于开发和测试)"""
        from .base import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话 (用于依赖注入)

    使用示例:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    session = db_manager.session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# 别名，用于FastAPI依赖注入
get_db = get_db_session


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    上下文管理器方式获取数据库会话

    使用示例:
        async with get_db_context() as db:
            result = await db.execute(select(Item))
            items = result.scalars().all()
    """
    session = db_manager.session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


class Transaction:
    """
    事务上下文管理器

    使用示例:
        async with Transaction() as tx:
            tx.add(user)
            tx.add(profile)
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
        self._own_session = session is None

    async def __aenter__(self) -> AsyncSession:
        if self._own_session:
            self._session = db_manager.session_factory()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self._session.commit()
        else:
            await self._session.rollback()

        if self._own_session:
            await self._session.close()


# 依赖注入快捷函数 - get_db 作为别名指向 get_db_session
# 这样 get_db 可以同时用于 Depends() 和 async with
get_db = get_db_session
