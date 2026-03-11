"""
ScholarForge Chart Service
图表生成服务主入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import settings
from shared.database import init_db, close_db
from shared.exceptions import AppException

from .routes import router


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
    title=f"{settings.app_name} - Chart Service",
    description="图表生成服务",
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
    """处理应用异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.error_code, "message": exc.message, "data": None},
    )


# 注册路由
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "chart"}
