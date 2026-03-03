"""
协作服务
WebSocket 实时协作 + REST API
支持 JWT 认证、心跳检测、Yjs 同步
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Set, Optional
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import jwt

# 配置 - 从环境变量获取
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))  # 心跳间隔（秒）
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT", "60"))  # 心跳超时（秒）
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app = FastAPI(
    title="ScholarForge Collaboration Service",
    description="实时协作服务 - WebSocket + REST API",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入管理器
from .manager import manager, User

# 导入并注册 REST API 路由
from .routes import router as collab_router, admin_router

app.include_router(collab_router)
app.include_router(admin_router)


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    await manager.start_heartbeat_checker()


@app.websocket("/ws/{paper_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    paper_id: str,
    token: Optional[str] = Query(None),
):
    """WebSocket 连接端点"""
    await manager.connect(websocket, paper_id)

    # 验证 Token
    user_info = None
    if token:
        user_info = manager.verify_token(token)
        if not user_info:
            await websocket.close(code=4001, reason="Invalid or expired token")
            return

    # 使用 Token 中的用户信息或生成临时 ID
    user_id = user_info.get("sub", str(uuid.uuid4())) if user_info else str(uuid.uuid4())
    user_name = user_info.get("name", "Anonymous") if user_info else "Anonymous"

    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(websocket, paper_id, user_id, user_name, data)
    except WebSocketDisconnect:
        manager.disconnect(paper_id, user_id)
        # 通知其他用户
        await manager.broadcast(paper_id, {
            "type": "user_left",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(paper_id, user_id)


async def handle_message(
    websocket: WebSocket,
    paper_id: str,
    user_id: str,
    user_name: str,
    data: dict
):
    """处理消息"""
    message_type = data.get("type")
    room = manager.get_room(paper_id)

    if not room:
        return

    # 更新心跳时间
    if user_id in room.users:
        room.users[user_id].last_heartbeat = datetime.now()

    if message_type == "join":
        # 用户加入
        user = User(
            id=user_id,
            name=data.get("name", user_name),
            color=data.get("color", "#1890ff"),
            websocket=websocket,
            paper_id=paper_id,
        )
        room.add_user(user)

        # 发送当前状态给新用户
        await websocket.send_json({
            "type": "room_state",
            "users": room.get_user_list(),
            "content": room.content,
        })

        # 通知其他用户
        await manager.broadcast(paper_id, {
            "type": "user_joined",
            "user": {
                "id": user.id,
                "name": user.name,
                "color": user.color,
            },
        }, exclude_user=user_id)

    elif message_type == "heartbeat":
        # 心跳响应
        await websocket.send_json({
            "type": "heartbeat_ack",
            "timestamp": datetime.now().isoformat(),
        })

    elif message_type == "cursor_move":
        # 光标移动
        user = room.users.get(user_id)
        if user:
            user.cursor_position = data.get("position")
            user.section_id = data.get("section_id")
            user.last_active = datetime.now()

            await manager.broadcast(paper_id, {
                "type": "cursor_update",
                "user_id": user_id,
                "position": user.cursor_position,
                "section_id": user.section_id,
            }, exclude_user=user_id)

    elif message_type == "text_change":
        # 文本变更（Yjs 格式）
        changes = data.get("changes", [])
        section_id = data.get("section_id")

        # 广播变更
        await manager.broadcast(paper_id, {
            "type": "text_update",
            "section_id": section_id,
            "changes": changes,
            "user_id": user_id,
        }, exclude_user=user_id)

    elif message_type == "selection_change":
        # 选择变化
        await manager.broadcast(paper_id, {
            "type": "selection_update",
            "user_id": user_id,
            "selection": data.get("selection"),
        }, exclude_user=user_id)

    elif message_type == "chat":
        # 聊天消息
        await manager.broadcast(paper_id, {
            "type": "chat_message",
            "user_id": user_id,
            "user_name": room.users[user_id].name if user_id in room.users else "Unknown",
            "message": data.get("message"),
            "timestamp": datetime.now().isoformat(),
        })

    elif message_type == "sync_request":
        # Yjs 同步请求
        # 广播请求其他客户端发送最新状态
        await manager.broadcast(paper_id, {
            "type": "sync_request",
            "user_id": user_id,
        }, exclude_user=user_id)

    elif message_type == "sync_state":
        # Yjs 同步状态
        await manager.broadcast(paper_id, {
            "type": "sync_state",
            "user_id": user_id,
            "state": data.get("state"),
        }, exclude_user=user_id)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "collaboration-service"}


@app.get("/rooms/{paper_id}/users")
async def get_room_users(paper_id: str):
    room = manager.get_room(paper_id)
    if not room:
        return {"users": []}
    return {"users": room.get_user_list()}


@app.get("/rooms")
async def get_active_rooms():
    """获取所有活跃房间"""
    return {
        "rooms": [
            {
                "paper_id": paper_id,
                "user_count": len(room.users),
                "users": room.get_user_list(),
            }
            for paper_id, room in manager.rooms.items()
        ]
    }
