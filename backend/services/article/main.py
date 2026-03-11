"""
ScholarForge Article Service
文献检索与管理服务主入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import settings
from shared.database import init_db, close_db
from shared.exceptions import AppException

from .routes import router, library_router, folder_router

try:
    from services.pdf_parser.routes import router as pdf_router, initialize_parser
    PDF_PARSER_AVAILABLE = True
except ImportError:
    PDF_PARSER_AVAILABLE = False
    pdf_router = None
    initialize_parser = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()

    # 初始化PDF解析器（如果可用）
    if PDF_PARSER_AVAILABLE and initialize_parser:
        try:
            initialize_parser(ai_service=None)
            print("PDF解析服务初始化成功")
        except Exception as e:
            print(f"PDF解析服务初始化失败: {e}")

    yield
    await close_db()


# 创建 FastAPI 应用
app = FastAPI(
    title=f"{settings.app_name} - Article Service",
    description="文献检索与管理服务",
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
app.include_router(library_router)
app.include_router(folder_router)

# 注册PDF路由（如果可用）
if PDF_PARSER_AVAILABLE and pdf_router:
    app.include_router(pdf_router)
    print("PDF解析路由已注册")


# 健康检查
@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "healthy", "service": "article-service"}


# 根路径
@app.get("/", tags=["根路径"])
async def root():
    return {
        "service": "ScholarForge Article Service",
        "version": settings.app_version,
        "docs": "/docs",
        "sources": ["cnki", "wos", "ieee", "arxiv"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,  # 文献服务端口
        reload=settings.debug,
    )
