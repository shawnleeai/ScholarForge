"""
WebSocket 路由
协作编辑实时同步
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional

from shared.dependencies import get_current_user_id
from .websocket_server import handle_websocket, collaboration_manager

router = APIRouter()


@router.websocket("/ws/collaborate/{document_id}")
async def collaboration_websocket(
    websocket: WebSocket,
    document_id: str,
    token: str = Query(..., description="JWT token"),
):
    """
    协作编辑 WebSocket 连接

    - **document_id**: 文档ID
    - **token**: JWT认证token
    """
    # 验证token并获取用户信息
    from shared.security import verify_token
    from shared.config import settings
    from jose import jwt, JWTError

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # 获取用户信息（简化版，实际应从数据库获取）
    user_info = {
        "name": f"User {user_id[:8]}",
        "user_id": user_id,
    }

    # 处理WebSocket连接
    await handle_websocket(websocket, document_id, user_id, user_info)


@router.get("/collaboration/stats", summary="获取协作统计")
async def get_collaboration_stats(
    user_id: str = Depends(get_current_user_id),
):
    """获取协作服务器统计信息"""
    return collaboration_manager.get_stats()


@router.post("/collaboration/cleanup", summary="清理不活跃房间")
async def cleanup_inactive_rooms(
    timeout_seconds: int = 3600,
    user_id: str = Depends(get_current_user_id),
):
    """手动触发清理不活跃房间"""
    await collaboration_manager.cleanup_inactive_rooms(timeout_seconds)
    return {"message": "Cleanup completed"}
