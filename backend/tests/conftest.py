"""
Pytest 配置文件
提供测试 fixtures 和配置
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from shared.database import DatabaseConfig, DatabaseType, db_manager
from shared.database.base import Base


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator:
    """创建测试数据库会话"""
    # 使用 SQLite 内存数据库进行测试
    config = DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        database=":memory:",
    )
    db_manager.initialize(config)

    # 创建所有表
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建会话
    async for session in db_manager.session_factory():
        yield session
        break

    # 清理
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await db_manager.close()


@pytest.fixture
def app() -> FastAPI:
    """创建测试应用"""
    from gateway.main import app
    return app


@pytest.fixture
def client(app: FastAPI) -> Generator:
    """创建同步测试客户端"""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator:
    """创建异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_user():
    """模拟用户数据"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "is_active": True,
    }


@pytest.fixture
def mock_paper():
    """模拟论文数据"""
    return {
        "id": "test-paper-id",
        "title": "Test Paper Title",
        "abstract": "Test abstract",
        "content": "Test content",
        "status": "draft",
        "owner_id": "test-user-id",
    }


@pytest.fixture
def mock_article():
    """模拟文献数据"""
    return {
        "id": "test-article-id",
        "title": "Test Article",
        "authors": [{"name": "Author One"}],
        "year": 2024,
        "source": "arxiv",
    }
