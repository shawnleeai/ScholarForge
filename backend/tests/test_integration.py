"""
集成测试
测试API端点和完整流程
"""

import pytest
from datetime import datetime


class TestUserFlow:
    """测试用户完整流程"""

    @pytest.mark.asyncio
    async def test_register_login_create_paper(self, async_client):
        """测试注册-登录-创建论文完整流程"""

        # 1. 注册用户
        register_data = {
            "email": "integration@test.com",
            "username": "integrationuser",
            "password": "SecurePass123!",
            "full_name": "Integration User"
        }

        response = await async_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        user_id = response.json()["id"]

        # 2. 登录
        login_data = {
            "email": "integration@test.com",
            "password": "SecurePass123!"
        }

        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"]

        # 3. 创建论文
        paper_data = {
            "title": "Integration Test Paper",
            "abstract": "This is an integration test"
        }

        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.post(
            "/api/v1/papers",
            json=paper_data,
            headers=headers
        )
        assert response.status_code == 201
        paper_id = response.json()["id"]

        # 4. 获取论文
        response = await async_client.get(
            f"/api/v1/papers/{paper_id}",
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == paper_data["title"]


class TestAPIEndpoints:
    """测试API端点"""

    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_get_users_unauthorized(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/users")
        # 应该返回401或403
        assert response.status_code in [401, 403, 404]


class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_invalid_json(self, async_client):
        """测试无效JSON"""
        response = await async_client.post(
            "/api/v1/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validation_error(self, async_client):
        """测试验证错误"""
        # 缺少必填字段
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "test@test.com"}  # 缺少password和username
        )
        assert response.status_code == 422


class TestConcurrentAccess:
    """测试并发访问"""

    @pytest.mark.asyncio
    async def test_concurrent_paper_reads(self, async_client):
        """测试并发读取论文"""
        import asyncio

        async def read_paper(paper_id):
            return await async_client.get(f"/api/v1/papers/{paper_id}")

        # 模拟并发请求
        tasks = [read_paper("paper-123") for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 检查没有异常
        for result in results:
            assert not isinstance(result, Exception)
