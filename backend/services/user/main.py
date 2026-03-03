"""
ScholarForge User Service
用户认证与管理服务主入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import settings
from shared.database import init_db, close_db
from shared.exceptions import AppException

from .routes import router, team_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    await init_db()
    yield
    # 关闭时
    await close_db()


# 创建 FastAPI 应用
app = FastAPI(
    title=f"{settings.app_name} - User Service",
    description="用户认证与管理服务",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 异常处理
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """应用异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.error_code.value,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "code": "1000",
            "message": "服务器内部错误",
            "details": str(exc) if settings.debug else None,
        },
    )


# 注册路由
app.include_router(router)
app.include_router(team_router)


# 健康检查
@app.get("/health", tags=["健康检查"])
async def health_check():
    """服务健康检查"""
    return {"status": "healthy", "service": "user-service"}


# 根路径
@app.get("/", tags=["根路径"])
async def root():
    """服务根路径"""
    return {
        "service": "ScholarForge User Service",
        "version": settings.app_version,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=settings.debug,
    )
