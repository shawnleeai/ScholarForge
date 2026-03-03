"""
进度管理服务主入口
FastAPI 应用定义
"""

import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

# 配置
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app = FastAPI(
    title="ScholarForge Progress Management Service",
    description="论文写作进度管理与预警系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "progress-management-service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.on_event("startup")
async def startup_event():
    """应用启动"""
    print("[Progress Management Service] Starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    print("[Progress Management Service] Shutting down...")
