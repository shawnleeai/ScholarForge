"""
CSRF 保护中间件
防止跨站请求伪造攻击
"""

import secrets
import hashlib
import time
import logging
from typing import Optional, Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

# CSRF Token 存储器（生产环境应使用 Redis）
_csrf_tokens: dict[str, dict] = {}
CSRF_TOKEN_EXPIRY = 3600  # 1小时过期

# 配置常量
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"

# 不需要 CSRF 验证的安全方法
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# 不需要 CSRF 验证的路径
EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/csrf-token",
}


def generate_csrf_token() -> str:
    """生成CSRF Token"""
    token = secrets.token_urlsafe(32)
    timestamp = int(time.time() * 1000)
    return hashlib.sha256(f"{token}{timestamp}".encode()).hexdigest()


def store_csrf_token(token: str) -> None:
    """存储CSRF Token"""
    _csrf_tokens[token] = {
        'expires': time.time() + CSRF_TOKEN_EXPIRY
    }
    # 清理过期 Token
    _cleanup_expired_tokens()


def verify_csrf_token(token: str) -> bool:
    """验证CSRF Token"""
    if not token:
        return False

    token_data = _csrf_tokens.get(token)
    if not token_data:
        return False

    # 检查是否过期
    if token_data['expires'] < time.time():
        del _csrf_tokens[token]
        return False

    return True


def _cleanup_expired_tokens() -> None:
    """清理过期的 Token"""
    current_time = time.time()
    expired = [t for t, data in _csrf_tokens.items() if data['expires'] < current_time]
    for token in expired:
        del _csrf_tokens[token]


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF 保护中间件"""

    def __init__(
        self,
        app: ASGIApp,
        exempt_paths: Optional[Set[str]] = None,
    ):
        super().__init__(app)
        self.exempt_paths = exempt_paths or EXEMPT_PATHS

    async def dispatch(self, request: Request, call_next) -> Response:
        # 跳过豁免路径
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # 跳过安全方法
        if request.method in SAFE_METHODS:
            return await call_next(request)

        # 获取 CSRF Token
        csrf_token = request.headers.get(CSRF_HEADER_NAME)
        if not csrf_token:
            csrf_token = request.cookies.get(CSRF_COOKIE_NAME)

        # 验证 Token
        if not csrf_token or not verify_csrf_token(csrf_token):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={"code": 403, "message": "CSRF Token 验证失败"}
            )

        return await call_next(request)


async def get_csrf_token_endpoint(request: Request) -> dict:
    """获取 CSRF Token 的 API 端点"""
    token = generate_csrf_token()
    store_csrf_token(token)
    return {"csrf_token": token}
