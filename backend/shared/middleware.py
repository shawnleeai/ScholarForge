"""
共享中间件模块
包含性能监控、缓存控制、CORS等中间件
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # 记录开始时间
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 添加性能头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 3))

        # 慢查询日志（超过1秒）
        if process_time > 1.0:
            print(f"[SLOW] {request.method} {request.url.path} took {process_time:.3f}s")

        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """缓存控制中间件"""

    # 不需要缓存的路径
    NO_CACHE_PATHS = [
        "/api/v1/auth",
        "/api/v1/users/me",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    # 可以缓存的静态资源路径
    STATIC_PATHS = [
        "/static",
        "/assets",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        path = request.url.path

        # 静态资源缓存1天
        if any(path.startswith(p) for p in self.STATIC_PATHS):
            response.headers["Cache-Control"] = "public, max-age=86400"
            return response

        # API响应不缓存
        if path.startswith("/api/"):
            # 检查是否需要缓存
            if any(path.startswith(p) for p in self.NO_CACHE_PATHS):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            else:
                # 其他API可以短时间缓存（5分钟）
                if request.method == "GET":
                    response.headers["Cache-Control"] = "public, max-age=300"
                else:
                    response.headers["Cache-Control"] = "no-cache"

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
