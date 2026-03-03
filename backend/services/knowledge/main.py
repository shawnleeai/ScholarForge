"""
知识图谱服务主入口
Neo4j 集成与图谱可视化
"""

import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

# 配置
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app = FastAPI(
    title="ScholarForge Knowledge Graph Service",
    description="知识图谱构建与可视化服务",
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
        "service": "knowledge-graph-service",
        "version": "1.0.0",
        "neo4j_status": "connected",  # TODO: 实际检查 Neo4j 连接
        "timestamp": datetime.now().isoformat(),
    }


@app.on_event("startup")
async def startup_event():
    """应用启动"""
    print("[Knowledge Graph Service] Starting up...")
    # TODO: 初始化 Neo4j 连接


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    print("[Knowledge Graph Service] Shutting down...")
    # TODO: 关闭 Neo4j 连接
