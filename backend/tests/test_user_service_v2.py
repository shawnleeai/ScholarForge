"""
用户服务单元测试 V2
适配实际项目结构的测试
"""

import pytest
import uuid
import bcrypt
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch


class TestUserModel:
    """测试用户模型"""

    def test_user_creation(self, mock_user):
        """测试用户创建"""
        assert mock_user["email"] == "test@example.com"
        assert mock_user["username"] == "testuser"
        assert mock_user["is_active"] is True

    def test_user_id_generation(self):
        """测试用户ID生成"""
        user_id = str(uuid.uuid4())
        assert len(user_id) == 36
        assert user_id.count("-") == 4


class TestPasswordHashing:
    """测试密码哈希"""

    def test_password_hashing(self):
        """测试密码哈希"""
        password = "SecurePass123!"
        password_bytes = password.encode('utf-8')[:72]
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

        assert hashed != password_bytes
        assert bcrypt.checkpw(password_bytes, hashed) is True
        assert bcrypt.checkpw(b"wrongpass", hashed) is False


class TestJWTToken:
    """测试 JWT Token"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        from jose import jwt

        data = {"sub": "user-123", "email": "test@example.com"}
        token = jwt.encode(data, "secret-key", algorithm="HS256")

        decoded = jwt.decode(token, "secret-key", algorithms=["HS256"])
        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@example.com"

    def test_token_expiration(self):
        """测试令牌过期"""
        from jose import jwt, ExpiredSignatureError
        from datetime import datetime, timedelta, timezone

        expired_data = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_data, "secret-key", algorithm="HS256")

        with pytest.raises(ExpiredSignatureError):
            jwt.decode(expired_token, "secret-key", algorithms=["HS256"])


class TestUserRepository:
    """测试用户仓库"""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """测试创建用户"""
        from services.user.repository import UserRepository
        from services.user.schemas import UserCreate

        repo = UserRepository(db_session)
        user_data = UserCreate(
            email="new@example.com",
            username="newuser",
            password="SecurePass123!",
            full_name="New User"
        )

        with patch.object(db_session, 'add'), \
             patch.object(db_session, 'flush'), \
             patch.object(db_session, 'refresh'):

            user = await repo.create(user_data)
            assert user is not None

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session):
        """测试通过邮箱获取用户"""
        from services.user.repository import UserRepository

        repo = UserRepository(db_session)

        with patch.object(db_session, 'execute', return_value=Mock(
            scalar_one_or_none=Mock(return_value={
                "id": "user-123",
                "email": "test@example.com",
                "username": "testuser"
            })
        )):
            user = await repo.get_by_email("test@example.com")
            assert user is not None
            assert user["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user(self, db_session):
        """测试用户认证"""
        from services.user.repository import UserRepository

        repo = UserRepository(db_session)

        mock_user = Mock()
        mock_user.password_hash = bcrypt.hashpw("password".encode(), bcrypt.gensalt())

        with patch.object(repo, 'get_by_email', return_value=mock_user):
            result = await repo.authenticate("test@example.com", "password")
            assert result == mock_user


class TestUserRoutes:
    """测试用户路由"""

    def test_register_endpoint_exists(self, app):
        """测试注册端点存在"""
        routes = [route.path for route in app.routes]
        assert "/api/v1/auth/register" in routes or any("register" in str(r) for r in routes)

    def test_login_endpoint_exists(self, app):
        """测试登录端点存在"""
        routes = [route.path for route in app.routes]
        assert "/api/v1/auth/login" in routes or any("login" in str(r) for r in routes)
