"""
缓存管理模块
支持内存缓存和Redis缓存
"""

import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
from datetime import datetime, timedelta
import asyncio

# 内存缓存存储
_memory_cache: dict = {}
_memory_cache_ttl: dict = {}


class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._memory_cache = _memory_cache
        self._memory_cache_ttl = _memory_cache_ttl

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        # 先检查内存缓存
        if key in self._memory_cache:
            if self._is_memory_cache_valid(key):
                return self._memory_cache[key]
            else:
                # 清理过期缓存
                self._clear_memory_cache(key)

        # 检查Redis缓存
        if self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    # 同步到内存缓存
                    data = json.loads(value)
                    self._set_memory_cache(key, data, ttl=300)  # 内存缓存5分钟
                    return data
            except Exception:
                pass

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        use_memory: bool = True
    ) -> bool:
        """设置缓存"""
        try:
            # 设置内存缓存
            if use_memory:
                self._set_memory_cache(key, value, ttl=min(ttl, 300))

            # 设置Redis缓存
            if self.redis:
                await self.redis.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )

            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            self._clear_memory_cache(key)
            if self.redis:
                await self.redis.delete(key)
            return True
        except Exception:
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """按模式删除缓存"""
        count = 0
        try:
            # 清理内存缓存
            keys_to_delete = [
                k for k in self._memory_cache.keys()
                if pattern.replace('*', '') in k
            ]
            for key in keys_to_delete:
                self._clear_memory_cache(key)
                count += 1

            # 清理Redis缓存
            if self.redis:
                redis_keys = await self.redis.keys(pattern)
                if redis_keys:
                    await self.redis.delete(*redis_keys)
                    count += len(redis_keys)

            return count
        except Exception:
            return count

    def _set_memory_cache(self, key: str, value: Any, ttl: int = 300):
        """设置内存缓存"""
        self._memory_cache[key] = value
        self._memory_cache_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)

    def _is_memory_cache_valid(self, key: str) -> bool:
        """检查内存缓存是否有效"""
        if key not in self._memory_cache_ttl:
            return False
        return datetime.utcnow() < self._memory_cache_ttl[key]

    def _clear_memory_cache(self, key: str):
        """清理内存缓存"""
        self._memory_cache.pop(key, None)
        self._memory_cache_ttl.pop(key, None)


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存键"""
    key_parts = [prefix]

    if args:
        key_parts.append(str(args))
    if kwargs:
        key_parts.append(str(sorted(kwargs.items())))

    raw_key = ':'.join(key_parts)
    return f"{prefix}:{hashlib.md5(raw_key.encode()).hexdigest()}"


def cached(prefix: str, ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = generate_cache_key(prefix, *args, **kwargs)

            # 尝试获取缓存
            cache_manager = CacheManager()
            cached_value = await cache_manager.get(cache_key)

            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 设置缓存
            await cache_manager.set(cache_key, result, ttl)

            return result

        return async_wrapper
    return decorator


def invalidate_cache(pattern: str):
    """缓存失效装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 执行函数
            result = await func(*args, **kwargs)

            # 清除相关缓存
            cache_manager = CacheManager()
            await cache_manager.delete_pattern(pattern)

            return result
        return async_wrapper
    return decorator


# 全局缓存管理器实例
_cache_instance: Optional[CacheManager] = None


def get_cache_manager(redis_client=None) -> CacheManager:
    """获取缓存管理器实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager(redis_client)
    return _cache_instance
