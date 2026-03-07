"""
ScholarForge API Gateway
统一API网关 - 聚合所有微服务到单一入口
"""

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

app = FastAPI(
    title="ScholarForge API Gateway",
    description="统一API网关 - 聚合所有微服务",
    version="1.0.0",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP客户端
http_client = httpx.AsyncClient(timeout=60.0)


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
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={"code": 503, "message": f"服务不可用: {service_url}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"网关错误: {str(e)}"}
        )


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
