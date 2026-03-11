"""
Chat Models
聊天模型 - 科研群组、即时通信
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    CODE = "code"
    REFERENCE = "reference"  # 文献引用
    SYSTEM = "system"


class ChatType(str, Enum):
    """聊天类型"""
    DIRECT = "direct"      # 私聊
    GROUP = "group"        # 群聊
    CHANNEL = "channel"    # 频道


class GroupType(str, Enum):
    """群组类型"""
    RESEARCH_GROUP = "research_group"    # 研究小组
    LAB = "lab"                          # 实验室
    COURSE = "course"                    # 课程群
    CONFERENCE = "conference"            # 会议群
    PROJECT = "project"                  # 项目群
    TOPIC = "topic"                      # 话题群


@dataclass
class ChatUser:
    """聊天用户"""
    user_id: str
    nickname: str
    avatar_url: Optional[str] = None
    status: str = "offline"  # online/offline/away/busy
    last_seen: Optional[datetime] = None
    current_chat: Optional[str] = None


@dataclass
class ChatMessage:
    """聊天消息"""
    id: str
    chat_id: str
    sender_id: str
    content: str
    message_type: MessageType
    created_at: datetime = field(default_factory=datetime.utcnow)
    reply_to: Optional[str] = None  # 回复的消息ID
    edited_at: Optional[datetime] = None
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> user_ids
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_deleted: bool = False


@dataclass
class ChatGroup:
    """聊天群组"""
    id: str
    name: str
    description: str
    group_type: GroupType
    creator_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    avatar_url: Optional[str] = None
    members: List[str] = field(default_factory=list)
    admins: List[str] = field(default_factory=list)
    is_public: bool = False
    tags: List[str] = field(default_factory=list)
    related_papers: List[str] = field(default_factory=list)
    announcement: Optional[str] = None


@dataclass
class DirectChat:
    """私聊会话"""
    id: str
    user1_id: str
    user2_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None


@dataclass
class ChatReadStatus:
    """聊天已读状态"""
    chat_id: str
    user_id: str
    last_read_message_id: Optional[str] = None
    last_read_at: Optional[datetime] = None
    unread_count: int = 0


@dataclass
class ChatInvitation:
    """聊天邀请"""
    id: str
    chat_id: str
    inviter_id: str
    invitee_id: str
    status: str = "pending"  # pending/accepted/rejected
    created_at: datetime = field(default_factory=datetime.utcnow)
    message: Optional[str] = None
