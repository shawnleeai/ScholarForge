"""
数据库模块
提供统一的数据库访问接口
"""

from .base import Base, BaseModel, TimestampMixin
from .connection import DatabaseManager, get_db_session, get_db, db_manager
from .config import DatabaseConfig, DatabaseType

# 兼容旧版API - 提供init_db和close_db
async def init_db():
    """初始化数据库（创建表）"""
    # 如果数据库管理器未初始化，则先初始化
    if db_manager._engine is None:
        # 使用SQLite配置（无需外部数据库服务器）
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            database="./scholarforge_ai.db",
        )
        db_manager.initialize(config)
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """关闭数据库连接"""
    await db_manager.close()

__all__ = [
    "Base",
    "BaseModel",
    "TimestampMixin",
    "DatabaseManager",
    "db_manager",
    "get_db_session",
    "get_db",
    "DatabaseConfig",
    "DatabaseType",
    "init_db",
    "close_db",
]
