"""
ScholarForge Paper Service
论文管理服务主入口
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import settings
from shared.database import init_db, close_db
from shared.exceptions import AppException
from shared.middleware import (
    PerformanceMonitorMiddleware,
    CacheControlMiddleware,
    SecurityHeadersMiddleware,
)

from .routes import router, template_router, comment_router, annotation_router
from services.defense.routes import router as defense_router
from services.topic.routes import router as topic_router
from services.progress.routes import router as progress_router
from services.journal.routes import router as journal_router
from services.knowledge.routes import router as knowledge_router
from services.reference.routes import router as reference_router
from services.plagiarism.routes import router as plagiarism_router
from services.format_engine.routes import router as format_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()
    yield
    await close_db()


# 创建 FastAPI 应用
app = FastAPI(
    title=f"{settings.app_name} - Paper Service",
    description="论文管理服务",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 性能监控中间件（最先添加，最后执行）
app.add_middleware(PerformanceMonitorMiddleware)

# 安全头中间件
app.add_middleware(SecurityHeadersMiddleware)

# 缓存控制中间件
app.add_middleware(CacheControlMiddleware)

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
app.include_router(template_router)
app.include_router(comment_router)
app.include_router(annotation_router)
app.include_router(defense_router, prefix="/defense", tags=["defense"])
app.include_router(topic_router, prefix="/topic", tags=["topic"])
app.include_router(progress_router, prefix="/progress", tags=["progress"])
app.include_router(journal_router, prefix="/journal", tags=["journal"])
app.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
app.include_router(reference_router, prefix="/reference", tags=["reference"])
app.include_router(plagiarism_router, prefix="/plagiarism", tags=["plagiarism"])
app.include_router(format_router, prefix="/format", tags=["format"])


# 健康检查
@app.get("/health", tags=["健康检查"])
async def health_check():
    """基础健康检查"""
    return {"status": "healthy", "service": "paper-service"}


@app.get("/health/detailed", tags=["健康检查"])
async def detailed_health_check():
    """详细健康检查（包含数据库连接）"""
    from shared.database import engine
    from sqlalchemy import text

    health_info = {
        "status": "healthy",
        "service": "paper-service",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # 检查数据库连接
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            health_info["checks"]["database"] = {
                "status": "healthy",
                "message": "Database connection is active"
            }
    except Exception as e:
        health_info["status"] = "unhealthy"
        health_info["checks"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }

    # 检查内存使用
    import psutil
    memory = psutil.virtual_memory()
    health_info["checks"]["memory"] = {
        "status": "healthy" if memory.percent < 80 else "warning",
        "used_percent": memory.percent,
        "available_mb": memory.available // (1024 * 1024)
    }

    return health_info


# 根路径
@app.get("/", tags=["根路径"])
async def root():
    return {
        "service": "ScholarForge Paper Service",
        "version": settings.app_version,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,  # 论文服务端口
        reload=settings.debug,
    )
