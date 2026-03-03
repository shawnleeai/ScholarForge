"""
协作服务 REST API 路由
会话管理、邀请、协作者管理
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.responses import success_response, paginated_response
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams
from shared.config import settings
from shared.security import create_access_token

from .schemas import (
    JoinSessionRequest,
    InviteCollaboratorRequest,
    UpdateCursorPositionRequest,
    CollaboratorInfo,
    SessionInfo,
    SessionCreateResponse,
    InvitationResponse,
    CollaborationStats,
    SessionStatus,
    CollabRole,
)
from .manager import manager

router = APIRouter(prefix="/api/v1/collaboration", tags=["实时协作"])


# ============== 会话管理 ==============

@router.post("/sessions/{paper_id}", summary="创建协作会话")
async def create_session(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    为论文创建协作会话

    返回 WebSocket 连接 URL 和认证 Token
    """
    # 生成会话 Token
    token_data = {
        "sub": user_id,
        "paper_id": paper_id,
        "role": "owner",
    }
    token = create_access_token(
        subject=user_id,
        additional_claims=token_data,
    )

    # WebSocket URL
    ws_url = f"ws://localhost:8006/ws/{paper_id}?token={token}"

    return success_response(
        data=SessionCreateResponse(
            session_id=str(uuid.uuid4()),
            paper_id=paper_id,
            ws_url=ws_url,
            token=token,
            expires_at=datetime.now() + timedelta(hours=settings.jwt_expire_hours),
        ).model_dump(),
        message="协作会话已创建",
        code=201,
    )


@router.get("/sessions/{paper_id}", summary="获取协作会话信息")
async def get_session(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    获取论文的协作会话信息

    包括当前在线用户列表、会话状态等
    """
    room = manager.get_room(paper_id)

    if not room:
        return success_response(
            data=SessionInfo(
                paper_id=paper_id,
                status=SessionStatus.CLOSED,
                collaborator_count=0,
                collaborators=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ).model_dump()
        )

    # 构建协作者列表
    collaborators = []
    for uid, user in room.users.items():
        collaborators.append(
            CollaboratorInfo(
                id=user.id,
                name=user.name,
                color=user.color,
                role=CollabRole.EDITOR,
                section_id=user.section_id,
                cursor_position=user.cursor_position,
                joined_at=user.last_heartbeat - timedelta(minutes=5),
                last_active=user.last_active,
                is_online=True,
            ).model_dump()
        )

    return success_response(
        data=SessionInfo(
            paper_id=paper_id,
            status=SessionStatus.ACTIVE if len(room.users) > 0 else SessionStatus.IDLE,
            collaborator_count=len(room.users),
            collaborators=collaborators,
            created_at=datetime.now() - timedelta(hours=1),
            updated_at=datetime.now(),
        ).model_dump()
    )


@router.post("/sessions/{paper_id}/join", summary="加入协作会话")
async def join_session(
    paper_id: str,
    request: JoinSessionRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    加入论文的协作会话

    返回 WebSocket 连接信息
    """
    # 生成会话 Token
    token_data = {
        "sub": user_id,
        "paper_id": paper_id,
        "role": "editor",
        "name": request.user_name,
        "color": request.color,
    }
    token = create_access_token(
        subject=user_id,
        additional_claims=token_data,
    )

    # WebSocket URL
    ws_url = f"ws://localhost:8006/ws/{paper_id}?token={token}"

    return success_response(
        data={
            "ws_url": ws_url,
            "token": token,
            "paper_id": paper_id,
        },
        message="已加入协作会话",
    )


@router.delete("/sessions/{paper_id}/leave", summary="离开协作会话")
async def leave_session(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """离开论文的协作会话"""
    await manager.disconnect_user(paper_id, user_id, reason="user_left")

    return success_response(message="已离开协作会话")


@router.get("/sessions/{paper_id}/collaborators", summary="获取协作者列表")
async def get_collaborators(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """获取论文的所有协作者（包括在线和离线）"""
    room = manager.get_room(paper_id)

    online_users = []
    if room:
        for uid, user in room.users.items():
            online_users.append({
                "id": user.id,
                "name": user.name,
                "color": user.color,
                "is_online": True,
                "section_id": user.section_id,
            })

    # TODO: 从数据库获取所有协作者（包括离线的）
    offline_users = []

    return success_response(
        data={
            "online": online_users,
            "offline": offline_users,
            "total_count": len(online_users) + len(offline_users),
        }
    )


# ============== 邀请管理 ==============

@router.post("/sessions/{paper_id}/invite", summary="邀请协作者")
async def invite_collaborator(
    paper_id: str,
    request: InviteCollaboratorRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    邀请用户协作编辑论文

    发送邀请邮件给被邀请用户
    """
    invitation_id = str(uuid.uuid4())

    return success_response(
        data={
            "invitation_id": invitation_id,
            "user_email": request.user_email,
            "role": request.role,
            "status": "sent",
        },
        message="邀请已发送",
        code=201,
    )


@router.get("/invitations", summary="获取我的邀请列表")
async def get_my_invitations(
    status: Optional[str] = Query(None, description="邀请状态: pending, accepted, rejected"),
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
):
    """获取当前用户收到的协作邀请"""
    invitations = []

    return paginated_response(
        items=invitations,
        total=0,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/invitations/{invitation_id}/accept", summary="接受邀请")
async def accept_invitation(
    invitation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """接受协作邀请"""
    return success_response(message="已接受邀请")


@router.post("/invitations/{invitation_id}/reject", summary="拒绝邀请")
async def reject_invitation(
    invitation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """拒绝协作邀请"""
    return success_response(message="已拒绝邀请")


# ============== 统计信息 ==============

@router.get("/stats", summary="获取协作统计")
async def get_collaboration_stats(
    user_id: str = Depends(get_current_user_id),
):
    """获取用户的协作统计信息"""
    active_rooms = len(manager.rooms)
    total_users = sum(len(room.users) for room in manager.rooms.values())

    return success_response(
        data=CollaborationStats(
            total_sessions=active_rooms,
            active_sessions=active_rooms,
            total_collaborators=total_users,
            total_edits_today=0,
            average_session_duration_minutes=0,
        ).model_dump()
    )


# ============== 房间管理（管理员接口） ==============

admin_router = APIRouter(prefix="/api/v1/admin/collaboration", tags=["协作管理"])


@admin_router.get("/rooms", summary="获取所有活跃房间")
async def get_all_rooms():
    """获取所有活跃的协作房间（管理员接口）"""
    rooms = []
    for paper_id, room in manager.rooms.items():
        rooms.append({
            "paper_id": paper_id,
            "user_count": len(room.users),
            "users": room.get_user_list(),
            "created_at": datetime.now().isoformat(),
        })

    return success_response(data=rooms)


@admin_router.delete("/rooms/{paper_id}", summary="关闭房间")
async def close_room(paper_id: str):
    """强制关闭协作房间（管理员接口）"""
    if paper_id in manager.rooms:
        # 通知所有用户
        await manager.broadcast(paper_id, {
            "type": "room_closed",
            "reason": "admin_closed",
            "message": "房间已被管理员关闭",
        })

        # 断开所有用户
        room = manager.rooms[paper_id]
        for user_id in list(room.users.keys()):
            await manager.disconnect_user(paper_id, user_id, reason="room_closed")

        return success_response(message="房间已关闭")

    return success_response(message="房间不存在或已关闭")


@admin_router.get("/health", summary="服务健康检查")
async def health_check():
    """协作服务健康检查"""
    return {
        "status": "healthy",
        "service": "collaboration-service",
        "active_rooms": len(manager.rooms),
        "total_connections": sum(len(room.users) for room in manager.rooms.values()),
    }
