"""
协作服务数据模型
Pydantic 模型定义
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class CollabRole(str, Enum):
    """协作角色"""
    OWNER = "owner"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    IDLE = "idle"
    CLOSED = "closed"


# ============== 请求模型 ==============

class JoinSessionRequest(BaseModel):
    """加入协作会话请求"""
    user_name: Optional[str] = Field(None, description="用户显示名称")
    color: Optional[str] = Field(None, description="用户颜色")


class InviteCollaboratorRequest(BaseModel):
    """邀请协作者请求"""
    user_email: str = Field(..., description="被邀请用户邮箱")
    role: CollabRole = Field(CollabRole.EDITOR, description="协作角色")
    message: Optional[str] = Field(None, description="邀请消息")


class UpdateCursorPositionRequest(BaseModel):
    """更新光标位置请求"""
    section_id: Optional[str] = Field(None, description="章节ID")
    position: int = Field(0, description="光标位置")
    selection: Optional[Dict[str, int]] = Field(None, description="选区范围")


# ============== 响应模型 ==============

class CollaboratorInfo(BaseModel):
    """协作者信息"""
    id: str
    name: str
    color: str
    role: CollabRole
    section_id: Optional[str] = None
    cursor_position: Optional[Dict[str, Any]] = None
    joined_at: datetime
    last_active: datetime
    is_online: bool = True


class SessionInfo(BaseModel):
    """协作会话信息"""
    paper_id: str
    status: SessionStatus
    collaborator_count: int
    collaborators: List[CollaboratorInfo]
    created_at: datetime
    updated_at: datetime


class SessionCreateResponse(BaseModel):
    """创建会话响应"""
    session_id: str
    paper_id: str
    ws_url: str
    token: str
    expires_at: datetime


class InvitationResponse(BaseModel):
    """邀请响应"""
    invitation_id: str
    paper_id: str
    paper_title: str
    inviter_name: str
    role: CollabRole
    message: Optional[str]
    created_at: datetime
    expires_at: datetime


class CollaborationStats(BaseModel):
    """协作统计"""
    total_sessions: int
    active_sessions: int
    total_collaborators: int
    total_edits_today: int
    average_session_duration_minutes: float


# ============== WebSocket 消息模型 ==============

class WSMessageBase(BaseModel):
    """WebSocket 消息基类"""
    type: str
    timestamp: datetime = Field(default_factory=datetime.now)


class WSJoinMessage(WSMessageBase):
    """加入消息"""
    type: str = "join"
    name: str
    color: str


class WSUserJoinedMessage(WSMessageBase):
    """用户加入通知"""
    type: str = "user_joined"
    user: CollaboratorInfo


class WSUserLeftMessage(WSMessageBase):
    """用户离开通知"""
    type: str = "user_left"
    user_id: str
    reason: Optional[str] = None


class WSCursorUpdateMessage(WSMessageBase):
    """光标更新消息"""
    type: str = "cursor_update"
    user_id: str
    position: Dict[str, Any]
    section_id: Optional[str] = None


class WSTextUpdateMessage(WSMessageBase):
    """文本更新消息"""
    type: str = "text_update"
    section_id: str
    changes: List[Any]
    user_id: str


class WSChatMessage(WSMessageBase):
    """聊天消息"""
    type: str = "chat_message"
    user_id: str
    user_name: str
    message: str


class WSRoomStateMessage(WSMessageBase):
    """房间状态消息"""
    type: str = "room_state"
    users: List[Dict[str, Any]]
    content: Optional[str] = None


class WSHeartbeatMessage(WSMessageBase):
    """心跳消息"""
    type: str = "heartbeat"


class WSHeartbeatAckMessage(WSMessageBase):
    """心跳响应"""
    type: str = "heartbeat_ack"


class WSSyncRequestMessage(WSMessageBase):
    """同步请求"""
    type: str = "sync_request"


class WSSyncStateMessage(WSMessageBase):
    """同步状态"""
    type: str = "sync_state"
    state: Any
