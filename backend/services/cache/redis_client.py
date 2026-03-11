"""
Redis Cache Service
Redis缓存服务 - 提供高性能数据缓存
"""

import json
import pickle
import hashlib
import functools
from typing import Any, Optional, Union, List, Callable
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio import Redis

from backend.shared.config import settings


class RedisCache:
    """Redis缓存客户端"""

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._default_ttl = 3600  # 默认1小时

    async def connect(self):
        """建立Redis连接"""
        if self._redis is None:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST or 'localhost',
                port=settings.REDIS_PORT or 6379,
                db=settings.REDIS_DB or 0,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=False,  # 使用二进制序列化
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )

    async def disconnect(self):
        """断开Redis连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def ping(self) -> bool:
        """检查连接状态"""
        try:
            return await self._redis.ping()
        except Exception:
            return False

    # ==================== 基础操作 ====================

    async def get(self, key: str) -> Any:
        """获取缓存值"""
        if not self._redis:
            await self.connect()

        data = await self._redis.get(key)
        if data:
            try:
                return pickle.loads(data)
            except Exception:
                return data.decode('utf-8')
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        nx: bool = False  # Only set if key does not exist
    ) -> bool:
        """设置缓存值"""
        if not self._redis:
            await self.connect()

        try:
            serialized = pickle.dumps(value)
            ttl = expire or self._default_ttl

            if nx:
                result = await self._redis.setnx(key, serialized)
                if result and ttl:
                    await self._redis.expire(key, ttl)
                return result
            else:
                await self._redis.setex(key, ttl, serialized)
                return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._redis:
            await self.connect()

        result = await self._redis.delete(key)
        return result > 0

    async def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存"""
        if not self._redis:
            await self.connect()

        keys = await self._redis.keys(pattern)
        if keys:
            return await self._redis.delete(*keys)
        return 0

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._redis:
            await self.connect()

        return await self._redis.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self._redis:
            await self.connect()

        return await self._redis.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        if not self._redis:
            await self.connect()

        return await self._redis.ttl(key)

    # ==================== 哈希操作 ====================

    async def hget(self, name: str, key: str) -> Any:
        """获取哈希字段"""
        if not self._redis:
            await self.connect()

        data = await self._redis.hget(name, key)
        if data:
            try:
                return pickle.loads(data)
            except Exception:
                return data.decode('utf-8')
        return None

    async def hset(self, name: str, key: str, value: Any) -> bool:
        """设置哈希字段"""
        if not self._redis:
            await self.connect()

        try:
            serialized = pickle.dumps(value)
            await self._redis.hset(name, key, serialized)
            return True
        except Exception as e:
            print(f"Hash set error: {e}")
            return False

    async def hgetall(self, name: str) -> dict:
        """获取所有哈希字段"""
        if not self._redis:
            await self.connect()

        data = await self._redis.hgetall(name)
        result = {}
        for key, value in data.items():
            try:
                result[key.decode('utf-8')] = pickle.loads(value)
            except Exception:
                result[key.decode('utf-8')] = value.decode('utf-8')
        return result

    async def hdel(self, name: str, *keys) -> int:
        """删除哈希字段"""
        if not self._redis:
            await self.connect()

        return await self._redis.hdel(name, *keys)

    # ==================== 列表操作 ====================

    async def lpush(self, name: str, *values) -> int:
        """向列表左侧添加元素"""
        if not self._redis:
            await self.connect()

        serialized = [pickle.dumps(v) for v in values]
        return await self._redis.lpush(name, *serialized)

    async def rpush(self, name: str, *values) -> int:
        """向列表右侧添加元素"""
        if not self._redis:
            await self.connect()

        serialized = [pickle.dumps(v) for v in values]
        return await self._redis.rpush(name, *serialized)

    async def lpop(self, name: str) -> Any:
        """从列表左侧弹出元素"""
        if not self._redis:
            await self.connect()

        data = await self._redis.lpop(name)
        if data:
            return pickle.loads(data)
        return None

    async def lrange(self, name: str, start: int, end: int) -> List[Any]:
        """获取列表范围"""
        if not self._redis:
            await self.connect()

        data = await self._redis.lrange(name, start, end)
        return [pickle.loads(d) for d in data]

    # ==================== 集合操作 ====================

    async def sadd(self, name: str, *values) -> int:
        """向集合添加元素"""
        if not self._redis:
            await self.connect()

        serialized = [pickle.dumps(v) for v in values]
        return await self._redis.sadd(name, *serialized)

    async def smembers(self, name: str) -> set:
        """获取集合所有元素"""
        if not self._redis:
            await self.connect()

        data = await self._redis.smembers(name)
        return {pickle.loads(d) for d in data}

    async def sismember(self, name: str, value: Any) -> bool:
        """检查元素是否在集合中"""
        if not self._redis:
            await self.connect()

        serialized = pickle.dumps(value)
        return await self._redis.sismember(name, serialized)

    # ==================== 有序集合操作 ====================

    async def zadd(self, name: str, mapping: dict) -> int:
        """向有序集合添加元素"""
        if not self._redis:
            await self.connect()

        serialized_mapping = {
            pickle.dumps(member): score
            for member, score in mapping.items()
        }
        return await self._redis.zadd(name, serialized_mapping)

    async def zrange(self, name: str, start: int, end: int, withscores: bool = False) -> list:
        """获取有序集合范围"""
        if not self._redis:
            await self.connect()

        data = await self._redis.zrange(name, start, end, withscores=withscores)
        if withscores:
            return [(pickle.loads(member), score) for member, score in data]
        return [pickle.loads(d) for d in data]

    # ==================== 分布式锁 ====================

    async def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """获取分布式锁"""
        if not self._redis:
            await self.connect()

        identifier = f"lock:{hashlib.md5(str(time.time()).encode()).hexdigest()}"
        lock_key = f"lock:{lock_name}"

        result = await self._redis.set(lock_key, identifier, nx=True, ex=timeout)
        return result is not None

    async def release_lock(self, lock_name: str) -> bool:
        """释放分布式锁"""
        if not self._redis:
            await self.connect()

        lock_key = f"lock:{lock_name}"
        return await self._redis.delete(lock_key) > 0

    # ==================== 发布订阅 ====================

    async def publish(self, channel: str, message: Any) -> int:
        """发布消息"""
        if not self._redis:
            await self.connect()

        serialized = json.dumps(message) if isinstance(message, (dict, list)) else str(message)
        return await self._redis.publish(channel, serialized)


# ==================== 缓存装饰器 ====================

def cached(
    expire: int = 3600,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None,
    condition: Optional[Callable] = None
):
    """
    缓存装饰器

    Args:
        expire: 过期时间（秒）
        key_prefix: 缓存键前缀
        key_builder: 自定义键生成函数
        condition: 缓存条件函数，返回False时不缓存

    Example:
        @cached(expire=600, key_prefix="paper")
        async def get_paper(paper_id: UUID):
            return await db.get(paper_id)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 默认键生成
                func_name = func.__name__
                args_str = str(args[1:]) if args and hasattr(args[0], '__class__') else str(args)
                kwargs_str = str(sorted(kwargs.items()))
                key_hash = hashlib.md5(f"{args_str}:{kwargs_str}".encode()).hexdigest()
                cache_key = f"{key_prefix}:{func_name}:{key_hash}" if key_prefix else f"{func_name}:{key_hash}"

            # 检查条件
            if condition and not condition(*args, **kwargs):
                return await func(*args, **kwargs)

            # 尝试从缓存获取
            cache = RedisCache()
            cached_value = await cache.get(cache_key)

            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 写入缓存
            if result is not None:
                await cache.set(cache_key, result, expire)

            return result

        # 添加清除缓存方法
        async def invalidate(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                func_name = func.__name__
                args_str = str(args[1:]) if args and hasattr(args[0], '__class__') else str(args)
                kwargs_str = str(sorted(kwargs.items()))
                key_hash = hashlib.md5(f"{args_str}:{kwargs_str}".encode()).hexdigest()
                cache_key = f"{key_prefix}:{func_name}:{key_hash}" if key_prefix else f"{func_name}:{key_hash}"

            cache = RedisCache()
            await cache.delete(cache_key)

        wrapper.invalidate = invalidate
        return wrapper
    return decorator


def cache_evict(key_prefix: str = "", key_pattern: str = None):
    """
    缓存清除装饰器

    Example:
        @cache_evict(key_prefix="paper", key_pattern="paper:list:*")
        async def update_paper(paper_id: UUID, data: dict):
            return await db.update(paper_id, data)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # 清除缓存
            cache = RedisCache()
            if key_pattern:
                await cache.delete_pattern(key_pattern)
            else:
                pattern = f"{key_prefix}:*" if key_prefix else "*"
                await cache.delete_pattern(pattern)

            return result
        return wrapper
    return decorator


# 单例实例
_cache_instance = None

def get_cache() -> RedisCache:
    """获取缓存单例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance
