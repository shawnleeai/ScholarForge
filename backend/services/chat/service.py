"""
Chat Service
聊天服务 - 支持科研群组、私聊、WebSocket实时通信
"""

import uuid
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from collections import defaultdict

from .models import (
    ChatUser, ChatMessage, ChatGroup, DirectChat, ChatReadStatus,
    MessageType, ChatType, GroupType, ChatInvitation
)


class ChatService:
    """聊天服务"""

    def __init__(self):
        # 内存存储
        self._users: Dict[str, ChatUser] = {}
        self._messages: Dict[str, List[ChatMessage]] = defaultdict(list)
        self._groups: Dict[str, ChatGroup] = {}
        self._direct_chats: Dict[str, DirectChat] = {}
        self._read_status: Dict[str, Dict[str, ChatReadStatus]] = defaultdict(dict)
        self._invitations: Dict[str, ChatInvitation] = {}

        # WebSocket连接管理
        self._connections: Dict[str, Any] = {}  # user_id -> websocket

    # ==================== 用户管理 ====================

    def register_user(self, user_id: str, nickname: str, avatar_url: Optional[str] = None) -> ChatUser:
        """注册用户"""
        user = ChatUser(
            user_id=user_id,
            nickname=nickname,
            avatar_url=avatar_url,
            status="offline"
        )
        self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> Optional[ChatUser]:
        """获取用户信息"""
        return self._users.get(user_id)

    def update_user_status(self, user_id: str, status: str):
        """更新用户状态"""
        if user_id in self._users:
            self._users[user_id].status = status
            self._users[user_id].last_seen = datetime.utcnow()

    def set_user_connection(self, user_id: str, websocket):
        """设置用户WebSocket连接"""
        self._connections[user_id] = websocket
        self.update_user_status(user_id, "online")

    def remove_user_connection(self, user_id: str):
        """移除用户WebSocket连接"""
        if user_id in self._connections:
            del self._connections[user_id]
        self.update_user_status(user_id, "offline")

    async def broadcast_to_users(self, user_ids: List[str], message: Dict[str, Any]):
        """向多个用户广播消息"""
        for user_id in user_ids:
            if user_id in self._connections:
                try:
                    await self._connections[user_id].send_json(message)
                except Exception as e:
                    print(f"Error sending message to {user_id}: {e}")

    # ==================== 群组管理 ====================

    def create_group(
        self,
        name: str,
        description: str,
        group_type: GroupType,
        creator_id: str,
        is_public: bool = False,
        tags: List[str] = None
    ) -> ChatGroup:
        """创建群组"""
        group = ChatGroup(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            group_type=group_type,
            creator_id=creator_id,
            members=[creator_id],
            admins=[creator_id],
            is_public=is_public,
            tags=tags or []
        )
        self._groups[group.id] = group
        return group

    def get_group(self, group_id: str) -> Optional[ChatGroup]:
        """获取群组信息"""
        return self._groups.get(group_id)

    def join_group(self, group_id: str, user_id: str) -> bool:
        """加入群组"""
        group = self._groups.get(group_id)
        if not group:
            return False

        if user_id not in group.members:
            group.members.append(user_id)
            return True
        return False

    def leave_group(self, group_id: str, user_id: str) -> bool:
        """离开群组"""
        group = self._groups.get(group_id)
        if not group:
            return False

        if user_id in group.members:
            group.members.remove(user_id)
            if user_id in group.admins:
                group.admins.remove(user_id)
            return True
        return False

    def get_user_groups(self, user_id: str) -> List[ChatGroup]:
        """获取用户加入的所有群组"""
        return [
            g for g in self._groups.values()
            if user_id in g.members
        ]

    def search_groups(
        self,
        query: Optional[str] = None,
        group_type: Optional[GroupType] = None,
        tags: Optional[List[str]] = None
    ) -> List[ChatGroup]:
        """搜索群组"""
        results = [g for g in self._groups.values() if g.is_public]

        if query:
            results = [
                g for g in results
                if query.lower() in g.name.lower() or query.lower() in g.description.lower()
            ]

        if group_type:
            results = [g for g in results if g.group_type == group_type]

        if tags:
            results = [
                g for g in results
                if any(tag in g.tags for tag in tags)
            ]

        return results

    # ==================== 私聊管理 ====================

    def get_or_create_direct_chat(self, user1_id: str, user2_id: str) -> DirectChat:
        """获取或创建私聊"""
        # 查找已有会话
        for chat in self._direct_chats.values():
            if (chat.user1_id == user1_id and chat.user2_id == user2_id) or \
               (chat.user1_id == user2_id and chat.user2_id == user1_id):
                return chat

        # 创建新会话
        chat = DirectChat(
            id=str(uuid.uuid4()),
            user1_id=user1_id,
            user2_id=user2_id
        )
        self._direct_chats[chat.id] = chat
        return chat

    def get_direct_chat(self, chat_id: str) -> Optional[DirectChat]:
        """获取私聊信息"""
        return self._direct_chats.get(chat_id)

    # ==================== 消息管理 ====================

    async def send_message(
        self,
        chat_id: str,
        sender_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """发送消息"""
        message = ChatMessage(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            reply_to=reply_to,
            metadata=metadata or {}
        )

        self._messages[chat_id].append(message)

        # 更新私聊最后消息时间
        if chat_id in self._direct_chats:
            self._direct_chats[chat_id].last_message_at = datetime.utcnow()

        # 广播消息
        recipients = self._get_chat_recipients(chat_id)
        await self.broadcast_to_users(recipients, {
            "type": "new_message",
            "data": self._message_to_dict(message)
        })

        return message

    def get_messages(
        self,
        chat_id: str,
        before_message_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ChatMessage]:
        """获取消息历史"""
        messages = self._messages.get(chat_id, [])

        # 过滤已删除的消息
        messages = [m for m in messages if not m.is_deleted]

        if before_message_id:
            # 找到指定消息的位置
            for i, m in enumerate(messages):
                if m.id == before_message_id:
                    messages = messages[:i]
                    break

        return messages[-limit:]

    def edit_message(
        self,
        message_id: str,
        sender_id: str,
        new_content: str
    ) -> bool:
        """编辑消息"""
        for chat_messages in self._messages.values():
            for message in chat_messages:
                if message.id == message_id and message.sender_id == sender_id:
                    message.content = new_content
                    message.edited_at = datetime.utcnow()
                    return True
        return False

    def delete_message(self, message_id: str, sender_id: str) -> bool:
        """删除消息"""
        for chat_messages in self._messages.values():
            for message in chat_messages:
                if message.id == message_id and message.sender_id == sender_id:
                    message.is_deleted = True
                    return True
        return False

    def add_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """添加表情反应"""
        for chat_messages in self._messages.values():
            for message in chat_messages:
                if message.id == message_id:
                    if emoji not in message.reactions:
                        message.reactions[emoji] = []
                    if user_id not in message.reactions[emoji]:
                        message.reactions[emoji].append(user_id)
                    return True
        return False

    # ==================== 已读状态 ====================

    def mark_as_read(self, chat_id: str, user_id: str, message_id: str):
        """标记已读"""
        status = ChatReadStatus(
            chat_id=chat_id,
            user_id=user_id,
            last_read_message_id=message_id,
            last_read_at=datetime.utcnow()
        )
        self._read_status[chat_id][user_id] = status

        # 计算未读数
        messages = self._messages.get(chat_id, [])
        unread = sum(1 for m in messages if m.id > message_id and m.sender_id != user_id)
        status.unread_count = unread

    def get_unread_count(self, chat_id: str, user_id: str) -> int:
        """获取未读消息数"""
        status = self._read_status[chat_id].get(user_id)
        if not status:
            return len(self._messages.get(chat_id, []))
        return status.unread_count

    def get_total_unread(self, user_id: str) -> int:
        """获取用户总未读数"""
        total = 0
        for chat_id, statuses in self._read_status.items():
            if user_id in statuses:
                total += statuses[user_id].unread_count
        return total

    # ==================== 邀请管理 ====================

    def create_invitation(
        self,
        chat_id: str,
        inviter_id: str,
        invitee_id: str,
        message: Optional[str] = None
    ) -> ChatInvitation:
        """创建邀请"""
        invitation = ChatInvitation(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            message=message
        )
        self._invitations[invitation.id] = invitation
        return invitation

    def respond_invitation(
        self,
        invitation_id: str,
        accept: bool
    ) -> bool:
        """响应邀请"""
        invitation = self._invitations.get(invitation_id)
        if not invitation or invitation.status != "pending":
            return False

        invitation.status = "accepted" if accept else "rejected"

        if accept:
            self.join_group(invitation.chat_id, invitation.invitee_id)

        return True

    def get_pending_invitations(self, user_id: str) -> List[ChatInvitation]:
        """获取待处理邀请"""
        return [
            i for i in self._invitations.values()
            if i.invitee_id == user_id and i.status == "pending"
        ]

    # ==================== 辅助方法 ====================

    def _get_chat_recipients(self, chat_id: str) -> List[str]:
        """获取聊天接收者列表"""
        recipients = []

        # 检查是否是群组
        if chat_id in self._groups:
            recipients = self._groups[chat_id].members

        # 检查是否是私聊
        if chat_id in self._direct_chats:
            chat = self._direct_chats[chat_id]
            recipients = [chat.user1_id, chat.user2_id]

        return recipients

    def _message_to_dict(self, message: ChatMessage) -> Dict[str, Any]:
        """消息转字典"""
        return {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "content": message.content,
            "message_type": message.message_type.value,
            "created_at": message.created_at.isoformat(),
            "reply_to": message.reply_to,
            "reactions": message.reactions,
            "metadata": message.metadata,
            "is_deleted": message.is_deleted
        }


# 单例
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取聊天服务单例"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
