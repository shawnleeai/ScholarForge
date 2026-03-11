"""
Notification API Routes
通知系统API路由
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from backend.shared.database import get_db
from backend.services.user.auth import get_current_user
from backend.services.user.models import User

from .service import NotificationService, NotificationType, NotificationChannel
from .websocket_manager import manager, websocket_endpoint


router = APIRouter(prefix="/notifications", tags=["notifications"])


# ==================== REST API ====================

@router.get("/", response_model=dict)
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户通知列表"""
    service = NotificationService(db)
    notifications = await service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )

    unread_count = await service.get_unread_count(current_user.id)

    return {
        'items': notifications,
        'unread_count': unread_count,
        'limit': limit,
        'offset': offset
    }


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取未读通知数量"""
    service = NotificationService(db)
    count = await service.get_unread_count(current_user.id)

    return {'unread_count': count}


@router.post("/{notification_id}/read", response_model=dict)
async def mark_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记通知为已读"""
    service = NotificationService(db)
    success = await service.mark_as_read(current_user.id, notification_id)

    return {'success': success}


@router.post("/read-all", response_model=dict)
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记所有通知为已读"""
    service = NotificationService(db)
    success = await service.mark_as_read(current_user.id)

    return {'success': success}


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知"""
    service = NotificationService(db)
    success = await service.delete_notification(current_user.id, notification_id)

    return {'success': success}


@router.delete("/", response_model=dict)
async def clear_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清空所有通知"""
    service = NotificationService(db)
    success = await service.clear_all_notifications(current_user.id)

    return {'success': success}


# ==================== 通知偏好设置 ====================

@router.get("/preferences", response_model=dict)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """获取用户通知偏好设置"""
    # 从缓存或数据库获取用户偏好
    # 简化实现，返回默认设置
    return {
        'user_id': str(current_user.id),
        'channels': {
            'in_app': True,
            'email': True,
            'web_push': False,
            'sms': False
        },
        'preferences': {
            'paper_comment': ['in_app', 'email'],
            'collab_invite': ['in_app', 'email'],
            'ai_analysis_complete': ['in_app'],
            'system_maintenance': ['in_app', 'email']
        }
    }


@router.put("/preferences", response_model=dict)
async def update_notification_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_user)
):
    """更新用户通知偏好设置"""
    # 保存用户偏好到数据库
    return {
        'user_id': str(current_user.id),
        'preferences': preferences,
        'updated': True
    }


# ==================== WebSocket ====================

@router.websocket("/ws/{user_id}")
async def notification_websocket(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(None)
):
    """
    WebSocket实时通知端点

    连接后实时接收:
    - 新通知推送
    - 系统消息
    - 在线状态更新
    """
    await websocket_endpoint(websocket, user_id, token)


# ==================== 测试/开发端点 ====================

@router.post("/test", response_model=dict)
async def send_test_notification(
    type: str = "welcome",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送测试通知（仅用于开发测试）"""
    service = NotificationService(db)
    service.set_websocket_manager(manager)

    notification_type = NotificationType.WELCOME

    if type == "welcome":
        await service.notify_welcome(current_user.id, current_user.name or "用户")
    elif type == "ai_complete":
        notification_type = NotificationType.AI_ANALYSIS_COMPLETE
        await service.send_notification(
            user_id=current_user.id,
            type=notification_type,
            title="AI分析完成",
            content="您的论文分析已完成，点击查看结果",
            data={'paper_id': 'test', 'paper_title': '测试论文'}
        )
    elif type == "comment":
        notification_type = NotificationType.PAPER_COMMENT
        await service.notify_paper_comment(
            paper_author_id=current_user.id,
            commenter_name="测试用户",
            paper_title="测试论文",
            paper_id=UUID(int=0)
        )

    return {'message': f'Test notification sent: {type}'}


@router.get("/online-users", response_model=dict)
async def get_online_users(
    current_user: User = Depends(get_current_user)
):
    """获取在线用户列表（仅管理员）"""
    # 检查管理员权限
    users = manager.get_online_users()

    return {
        'count': len(users),
        'users': users
    }

