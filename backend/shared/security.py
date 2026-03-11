"""
安全模块
JWT Token 和密码处理
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import hashlib
import logging
import redis.asyncio as redis
from redis.exceptions import RedisError

import bcrypt
from jose import JWTError, jwt

from .config import settings

logger = logging.getLogger(__name__)

# Redis 键前缀
TOKEN_BLACKLIST_PREFIX = "scholarforge:token_blacklist:"

# Redis 客户端（延迟初始化）
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """获取 Redis 客户端（单例）"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # 测试连接
            await _redis_client.ping()
            logger.info("Redis connection established for token blacklist")
        except RedisError as e:
            logger.warning(f"Redis connection failed, falling back to memory: {e}")
            _redis_client = None
    return _redis_client


# 内存后备存储（Redis 不可用时使用）
_memory_blacklist: dict[str, float] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def _get_token_id(token: str) -> str:
    """获取令牌的唯一标识（用于黑名单）"""
    return hashlib.sha256(token.encode()).hexdigest()[:32]


async def add_token_to_blacklist(token: str, expires_in_seconds: int = 3600) -> bool:
    """
    将令牌添加到黑名单（支持 Redis 持久化）

    Args:
        token: 要撤销的令牌
        expires_in_seconds: 黑名单有效期（默认1小时，与访问令牌过期时间一致）

    Returns:
        bool: 是否成功添加
    """
    token_id = _get_token_id(token)
    redis_key = f"{TOKEN_BLACKLIST_PREFIX}{token_id}"

    try:
        client = await get_redis_client()
        if client:
            # 使用 Redis 存储，设置过期时间
            await client.setex(redis_key, expires_in_seconds, "1")
            logger.debug(f"Token added to Redis blacklist: {token_id[:8]}...")
            return True
    except RedisError as e:
        logger.warning(f"Redis error, using memory fallback: {e}")

    # 内存后备存储
    expires_at = datetime.now(timezone.utc).timestamp() + expires_in_seconds
    _memory_blacklist[token_id] = expires_at
    _cleanup_memory_blacklist()
    return True


async def is_token_blacklisted(token: str) -> bool:
    """
    检查令牌是否在黑名单中（支持 Redis 持久化）

    Args:
        token: 要检查的令牌

    Returns:
        bool: 是否在黑名单中
    """
    token_id = _get_token_id(token)
    redis_key = f"{TOKEN_BLACKLIST_PREFIX}{token_id}"

    try:
        client = await get_redis_client()
        if client:
            # 从 Redis 检查
            exists = await client.exists(redis_key)
            return bool(exists)
    except RedisError as e:
        logger.warning(f"Redis error, using memory fallback: {e}")

    # 内存后备检查
    if token_id not in _memory_blacklist:
        return False

    # 检查是否过期
    expires_at = _memory_blacklist[token_id]
    if datetime.now(timezone.utc).timestamp() > expires_at:
        del _memory_blacklist[token_id]
        return False

    return True


def _cleanup_memory_blacklist():
    """清理内存中过期的黑名单条目"""
    current_time = datetime.now(timezone.utc).timestamp()
    expired_tokens = [
        token_id for token_id, expires_at in _memory_blacklist.items()
        if current_time > expires_at
    ]
    for token_id in expired_tokens:
        del _memory_blacklist[token_id]


# 同步版本（用于向后兼容）
_token_blacklist: dict[str, float] = {}


def add_token_to_blacklist_sync(token: str, expires_in_seconds: int = 3600) -> bool:
    """同步版本的添加到黑名单（向后兼容）"""
    token_id = _get_token_id(token)
    expires_at = datetime.now(timezone.utc).timestamp() + expires_in_seconds
    _token_blacklist[token_id] = expires_at
    _cleanup_blacklist()
    return True


def is_token_blacklisted_sync(token: str) -> bool:
    """同步版本的检查黑名单（向后兼容）"""
    token_id = _get_token_id(token)

    if token_id not in _token_blacklist:
        return False

    expires_at = _token_blacklist[token_id]
    if datetime.now(timezone.utc).timestamp() > expires_at:
        del _token_blacklist[token_id]
        return False

    return True


def _cleanup_blacklist():
    """清理过期的黑名单条目"""
    current_time = datetime.now(timezone.utc).timestamp()
    expired_tokens = [
        token_id for token_id, expires_at in _token_blacklist.items()
        if current_time > expires_at
    ]
    for token_id in expired_tokens:
        del _token_blacklist[token_id]


def create_access_token(
    subject: str | dict,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None,
) -> str:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.jwt_expire_hours
        )

    if isinstance(subject, dict):
        to_encode = subject.copy()
    else:
        to_encode = {"sub": subject}

    to_encode.update({"exp": expire, "type": "access"})

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """创建刷新令牌"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_expire_days
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """解码令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


async def verify_token_async(token: str, token_type: str = "access") -> Optional[str]:
    """验证令牌并返回用户ID（异步版本，支持 Redis）"""
    # 检查黑名单
    if await is_token_blacklisted(token):
        return None

    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != token_type:
        return None

    return payload.get("sub")


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """验证令牌并返回用户ID（同步版本，向后兼容）"""
    # 检查黑名单
    if is_token_blacklisted_sync(token):
        return None

    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != token_type:
        return None

    return payload.get("sub")


async def revoke_token_async(token: str) -> bool:
    """
    撤销令牌（异步版本，支持 Redis）

    Args:
        token: 要撤销的令牌

    Returns:
        bool: 是否成功撤销
    """
    payload = decode_token(token)
    if payload is None:
        return False

    # 计算剩余有效时间
    exp = payload.get("exp", 0)
    current_time = datetime.now(timezone.utc).timestamp()
    remaining_seconds = max(0, int(exp - current_time))

    if remaining_seconds <= 0:
        return False  # 令牌已过期，无需撤销

    return await add_token_to_blacklist(token, remaining_seconds)


def revoke_token(token: str) -> bool:
    """
    撤销令牌（同步版本，向后兼容）

    Args:
        token: 要撤销的令牌

    Returns:
        bool: 是否成功撤销
    """
    payload = decode_token(token)
    if payload is None:
        return False

    # 计算剩余有效时间
    exp = payload.get("exp", 0)
    current_time = datetime.now(timezone.utc).timestamp()
    remaining_seconds = max(0, int(exp - current_time))

    if remaining_seconds <= 0:
        return False  # 令牌已过期，无需撤销

    return add_token_to_blacklist_sync(token, remaining_seconds)
