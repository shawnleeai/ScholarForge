"""
ScholarForge API Gateway
统一API网关 - 聚合所有微服务到单一入口
"""

import logging
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from shared.csrf_middleware import CSRFMiddleware
from shared.audit_middleware import AuditMiddleware, setup_audit_logging

# 配置审计日志
setup_audit_logging()
logger = logging.getLogger(__name__)

# 服务配置
SERVICES = {
    "/api/v1/auth": "http://localhost:8001",
    "/api/v1/users": "http://localhost:8001",
    "/api/v1/teams": "http://localhost:8001",
    "/api/v1/articles": "http://localhost:8002",
    "/api/v1/library": "http://localhost:8002",
    "/api/v1/pdf": "http://localhost:8002",  # PDF解析服务（在article服务中）
    "/api/v1/papers": "http://localhost:8003",
    "/api/v1/templates": "http://localhost:8003",
    "/api/v1/ai": "http://localhost:8004",
    "/api/v1/recommendations": "http://localhost:8005",
    "/api/v1/topic": "http://localhost:8003",
    "/api/v1/progress": "http://localhost:8003",
    "/api/v1/journal": "http://localhost:8003",
    "/api/v1/knowledge": "http://localhost:8003",
    "/api/v1/reference": "http://localhost:8003",
    "/api/v1/plagiarism": "http://localhost:8003",
    "/api/v1/format": "http://localhost:8003",
    "/api/v1/defense": "http://localhost:8003",
    "/api/v1/ai-agent": "http://localhost:8004",  # AI Agent服务
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    简单的速率限制中间件
    基于IP地址限制请求频率
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._requests = {}  # {ip: [timestamp1, timestamp2, ...]}

    async def dispatch(self, request: Request, call_next):
        import time
        from collections import deque

        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"

        # 健康检查不受限制
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        current_time = time.time()

        # 初始化或清理过期记录
        if client_ip not in self._requests:
            self._requests[client_ip] = deque()

        # 清理超过1分钟的记录
        while self._requests[client_ip] and current_time - self._requests[client_ip][0] > 60:
            self._requests[client_ip].popleft()

        # 检查是否超过限制
        if len(self._requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "message": "请求过于频繁，请稍后再试"
                },
                headers={"Retry-After": "60"}
            )

        # 记录本次请求
        self._requests[client_ip].append(current_time)

        return await call_next(request)


app = FastAPI(
    title="ScholarForge API Gateway",
    description="统一API网关 - 聚合所有微服务",
    version="1.0.0",
)

# 添加速率限制中间件 (每分钟60次请求)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# 添加安全头中间件
app.add_middleware(SecurityHeadersMiddleware)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-CSRF-Token"],
)

# CSRF保护中间件
app.add_middleware(CSRFMiddleware)

# 审计日志中间件
app.add_middleware(AuditMiddleware)

# HTTP客户端
http_client = httpx.AsyncClient(timeout=60.0)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "ScholarForge API Gateway",
        "version": "1.0.0",
        "endpoints": list(SERVICES.keys()),
    }


def get_service_url(path: str) -> tuple[str, str]:
    """根据路径获取目标服务URL"""
    for prefix, url in SERVICES.items():
        if path.startswith(prefix):
            return url, path
    return None, path


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(request: Request, path: str):
    """代理请求到对应微服务"""
    service_url, matched_path = get_service_url(f"/{path}")

    if not service_url:
        return JSONResponse(
            status_code=404,
            content={"code": 404, "message": f"未找到匹配的服务: /{path}"}
        )

    # 构建目标URL - 保持完整路径
    target_url = f"{service_url}/{path}"

    # 获取请求体
    body = await request.body()

    # 复制请求头
    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        # 转发请求
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params,
        )

        # 返回响应
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except httpx.ConnectError as e:
        logger.error(f"Service unavailable: {service_url}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"code": 503, "message": "服务暂时不可用，请稍后重试"}
        )
    except Exception as e:
        logger.error(f"Gateway error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "网关错误，请稍后重试"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
