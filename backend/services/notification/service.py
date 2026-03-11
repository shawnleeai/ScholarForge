"""
Notification Service
消息通知服务 - 支持站内信、邮件、WebSocket实时推送
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID
from sqlalchemy.orm import Session

from backend.services.cache.redis_client import get_cache


class NotificationType(str, Enum):
    """通知类型"""
    # 论文相关
    PAPER_COMMENT = "paper_comment"           # 新批注
    PAPER_MENTION = "paper_mention"           # 被@提及
    PAPER_SHARED = "paper_shared"             # 论文被分享
    PAPER_APPROVED = "paper_approved"         # 论文通过审核
    PAPER_REJECTED = "paper_rejected"         # 论文被拒绝

    # 协作相关
    COLLAB_INVITE = "collab_invite"           # 协作邀请
    COLLAB_JOINED = "collab_joined"           # 有人加入协作
    COLLAB_LEFT = "collab_left"               # 有人离开协作
    VERSION_UPDATED = "version_updated"       # 版本更新

    # AI 相关
    AI_SUGGESTION = "ai_suggestion"           # AI 建议
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"  # AI 分析完成
    AI_REVIEW_READY = "ai_review_ready"       # AI 审阅完成

    # 投稿相关
    SUBMISSION_SUBMITTED = "submission_submitted"  # 投稿提交
    SUBMISSION_REVIEWED = "submission_reviewed"    # 审稿意见
    SUBMISSION_ACCEPTED = "submission_accepted"    # 论文被接受

    # 系统相关
    SYSTEM_MAINTENANCE = "system_maintenance" # 系统维护
    SECURITY_ALERT = "security_alert"         # 安全提醒
    WELCOME = "welcome"                       # 欢迎消息


class NotificationChannel(str, Enum):
    """通知渠道"""
    IN_APP = "in_app"      # 站内信
    EMAIL = "email"        # 邮件
    SMS = "sms"            # 短信
    WEB_PUSH = "web_push"  # 浏览器推送
    WECHAT = "wechat"      # 微信


class NotificationService:
    """通知服务"""

    def __init__(self, db: Session = None):
        self.db = db
        self.cache = get_cache()
        self._websocket_manager = None

    def set_websocket_manager(self, manager):
        """设置WebSocket管理器"""
        self._websocket_manager = manager

    # ==================== 通知创建 ====================

    async def create_notification(
        self,
        user_id: UUID,
        type: NotificationType,
        title: str,
        content: str,
        data: Dict[str, Any] = None,
        sender_id: UUID = None,
        related_type: str = None,
        related_id: UUID = None
    ) -> dict:
        """创建通知"""
        notification = {
            'id': str(UUID(int=0)),  # 临时ID
            'user_id': str(user_id),
            'type': type.value,
            'title': title,
            'content': content,
            'data': data or {},
            'sender_id': str(sender_id) if sender_id else None,
            'related_type': related_type,
            'related_id': str(related_id) if related_id else None,
            'is_read': False,
            'created_at': datetime.utcnow().isoformat(),
            'read_at': None
        }

        # 保存到数据库
        if self.db:
            # 实际项目中保存到数据库
            pass

        # 添加到用户通知列表（Redis）
        await self._add_to_user_notifications(user_id, notification)

        return notification

    async def send_notification(
        self,
        user_id: UUID,
        type: NotificationType,
        title: str,
        content: str,
        data: Dict[str, Any] = None,
        channels: List[NotificationChannel] = None
    ) -> dict:
        """
        发送多渠道通知

        Args:
            user_id: 接收用户ID
            type: 通知类型
            title: 标题
            content: 内容
            data: 附加数据
            channels: 发送渠道，None则根据用户偏好
        """
        # 创建通知记录
        notification = await self.create_notification(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            data=data
        )

        # 获取用户通知偏好
        if channels is None:
            channels = await self._get_user_notification_channels(user_id, type)

        # 站内信（WebSocket）
        if NotificationChannel.IN_APP in channels:
            await self._send_websocket(user_id, notification)

        # 邮件通知
        if NotificationChannel.EMAIL in channels:
            await self._send_email(user_id, title, content, data)

        # 浏览器推送
        if NotificationChannel.WEB_PUSH in channels:
            await self._send_web_push(user_id, title, content, data)

        return notification

    async def send_bulk_notifications(
        self,
        user_ids: List[UUID],
        type: NotificationType,
        title: str,
        content: str,
        data: Dict[str, Any] = None
    ) -> List[dict]:
        """批量发送通知"""
        notifications = []
        for user_id in user_ids:
            notification = await self.send_notification(
                user_id=user_id,
                type=type,
                title=title,
                content=content,
                data=data
            )
            notifications.append(notification)
        return notifications

    # ==================== 通知获取 ====================

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[dict]:
        """获取用户通知列表"""
        cache_key = f"notifications:{user_id}"
        notifications = await self.cache.lrange(cache_key, offset, offset + limit - 1)

        if unread_only:
            notifications = [n for n in notifications if not n.get('is_read')]

        return notifications

    async def get_unread_count(self, user_id: UUID) -> int:
        """获取未读通知数量"""
        cache_key = f"notifications:{user_id}"
        notifications = await self.cache.lrange(cache_key, 0, -1)
        return sum(1 for n in notifications if not n.get('is_read'))

    async def get_notification(self, user_id: UUID, notification_id: str) -> Optional[dict]:
        """获取单个通知"""
        notifications = await self.get_user_notifications(user_id, limit=1000)
        for notification in notifications:
            if notification.get('id') == notification_id:
                return notification
        return None

    # ==================== 通知操作 ====================

    async def mark_as_read(self, user_id: UUID, notification_id: str = None) -> bool:
        """标记通知为已读"""
        cache_key = f"notifications:{user_id}"

        if notification_id:
            # 标记单个通知
            notifications = await self.cache.lrange(cache_key, 0, -1)
            for i, notification in enumerate(notifications):
                if notification.get('id') == notification_id:
                    notification['is_read'] = True
                    notification['read_at'] = datetime.utcnow().isoformat()
                    # 更新Redis（这里简化处理，实际应该先删除再插入）
                    break
        else:
            # 标记所有为已读
            notifications = await self.cache.lrange(cache_key, 0, -1)
            for notification in notifications:
                if not notification.get('is_read'):
                    notification['is_read'] = True
                    notification['read_at'] = datetime.utcnow().isoformat()

        return True

    async def delete_notification(self, user_id: UUID, notification_id: str) -> bool:
        """删除通知"""
        cache_key = f"notifications:{user_id}"
        # 实际实现需要从列表中删除指定元素
        # 这里简化处理
        return True

    async def clear_all_notifications(self, user_id: UUID) -> bool:
        """清空所有通知"""
        cache_key = f"notifications:{user_id}"
        await self.cache.delete(cache_key)
        return True

    # ==================== 内部方法 ====================

    async def _add_to_user_notifications(self, user_id: UUID, notification: dict):
        """添加通知到用户列表"""
        cache_key = f"notifications:{user_id}"

        # 使用列表存储，限制长度
        await self.cache.lpush(cache_key, notification)

        # 设置过期时间（30天）
        await self.cache.expire(cache_key, 30 * 24 * 3600)

    async def _get_user_notification_channels(
        self,
        user_id: UUID,
        type: NotificationType
    ) -> List[NotificationChannel]:
        """获取用户通知渠道偏好"""
        # 从缓存或数据库获取用户偏好
        # 默认返回站内信
        return [NotificationChannel.IN_APP, NotificationChannel.EMAIL]

    async def _send_websocket(self, user_id: UUID, notification: dict):
        """WebSocket实时推送"""
        if self._websocket_manager:
            await self._websocket_manager.send_to_user(
                str(user_id),
                {
                    'type': 'notification',
                    'data': notification
                }
            )

    async def _send_email(self, user_id: UUID, title: str, content: str, data: dict):
        """发送邮件通知"""
        # 调用邮件服务
        # 这里简化处理，实际应该使用邮件服务
        print(f"[Email] To: {user_id}, Title: {title}")

    async def _send_web_push(self, user_id: UUID, title: str, content: str, data: dict):
        """发送浏览器推送"""
        # 调用Web Push服务
        print(f"[WebPush] To: {user_id}, Title: {title}")

    # ==================== 快捷方法 ====================

    async def notify_paper_comment(
        self,
        paper_author_id: UUID,
        commenter_name: str,
        paper_title: str,
        paper_id: UUID
    ):
        """通知论文作者有新批注"""
        await self.send_notification(
            user_id=paper_author_id,
            type=NotificationType.PAPER_COMMENT,
            title=f"{commenter_name} 给你的论文添加了批注",
            content=f"论文《{paper_title}》收到新批注",
            data={
                'paper_id': str(paper_id),
                'paper_title': paper_title,
                'commenter_name': commenter_name
            }
        )

    async def notify_collab_invite(
        self,
        invitee_id: UUID,
        inviter_name: str,
        paper_title: str,
        paper_id: UUID
    ):
        """通知协作邀请"""
        await self.send_notification(
            user_id=invitee_id,
            type=NotificationType.COLLAB_INVITE,
            title=f"{inviter_name} 邀请你协作编辑论文",
            content=f"论文《{paper_title}》",
            data={
                'paper_id': str(paper_id),
                'paper_title': paper_title,
                'inviter_name': inviter_name
            }
        )

    async def notify_ai_analysis_complete(
        self,
        user_id: UUID,
        paper_title: str,
        paper_id: UUID
    ):
        """通知AI分析完成"""
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.AI_ANALYSIS_COMPLETE,
            title="AI 分析完成",
            content=f"论文《{paper_title}》的AI分析已完成",
            data={
                'paper_id': str(paper_id),
                'paper_title': paper_title
            }
        )

    async def notify_welcome(self, user_id: UUID, username: str):
        """发送欢迎通知"""
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.WELCOME,
            title="欢迎使用 ScholarForge",
            content=f"你好 {username}，开始你的学术写作之旅吧！",
            data={}
        )
