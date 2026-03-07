"""
用户服务单元测试
测试用户注册、登录、认证等功能
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch


class TestUserModel:
    """测试用户模型"""

    def test_user_creation(self, mock_user):
        """测试用户创建"""
        assert mock_user["email"] == "test@example.com"
        assert mock_user["username"] == "testuser"
        assert mock_user["is_active"] is True

    def test_user_id_generation(self):
        """测试用户ID生成"""
        import uuid
        user_id = str(uuid.uuid4())
        assert len(user_id) == 36
        assert user_id.count("-") == 4


class TestUserRegistration:
    """测试用户注册"""

    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """测试成功注册用户"""
        from services.user.service import UserService

        service = UserService()

        user_data = {
            "email": "new@example.com",
            "username": "newuser",
            "password": "SecurePass123!",
        }

        # 模拟数据库操作
        with patch.object(service, "_hash_password", return_value="hashed_pass"):
            result = await service.register_user(user_data)

        assert result["email"] == user_data["email"]
        assert result["username"] == user_data["username"]
        assert "password" not in result

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self):
        """测试重复邮箱注册"""
        from services.user.service import UserService

        service = UserService()

        with patch.object(
            service, "_check_email_exists", return_value=True
        ), pytest.raises(ValueError, match="Email already exists"):
            await service.register_user({
                "email": "existing@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
            })


class TestUserAuthentication:
    """测试用户认证"""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """测试成功登录"""
        from services.user.service import UserService

        service = UserService()

        with patch.object(service, "_verify_password", return_value=True), \
             patch.object(service, "_get_user_by_email", return_value={
                 "id": "user-123",
                 "email": "test@example.com",
                 "hashed_password": "hashed",
                 "is_active": True,
             }), \
             patch.object(service, "_create_access_token", return_value="token123"):

            result = await service.authenticate_user("test@example.com", "password")

        assert result["access_token"] == "token123"
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self):
        """测试密码错误"""
        from services.user.service import UserService

        service = UserService()

        with patch.object(service, "_verify_password", return_value=False), \
             patch.object(service, "_get_user_by_email", return_value={
                 "id": "user-123",
                 "email": "test@example.com",
                 "hashed_password": "hashed",
                 "is_active": True,
             }), pytest.raises(ValueError, match="Invalid credentials"):

            await service.authenticate_user("test@example.com", "wrongpass")

    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        """测试用户不存在"""
        from services.user.service import UserService

        service = UserService()

        with patch.object(
            service, "_get_user_by_email", return_value=None
        ), pytest.raises(ValueError, match="User not found"):
            await service.authenticate_user("nonexistent@example.com", "password")


class TestPasswordHashing:
    """测试密码哈希"""

    def test_password_hashing(self):
        """测试密码哈希"""
        import bcrypt

        password = "SecurePass123!"
        # bcrypt密码不能超过72字节
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

        # 创建一个过期的token
        expired_data = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_data, "secret-key", algorithm="HS256")

        # 验证过期
        with pytest.raises(ExpiredSignatureError):
            jwt.decode(expired_token, "secret-key", algorithms=["HS256"])
