"""
Chat API Routes
聊天API路由 - 群组、私聊、WebSocket
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .service import get_chat_service
from .models import MessageType, GroupType

router = APIRouter(prefix="/chat", tags=["chat"])


# ==================== 请求/响应模型 ====================

class CreateGroupRequest(BaseModel):
    """创建群组请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    group_type: str = Field("topic", description="research_group/lab/course/conference/project/topic")
    is_public: bool = Field(False)
    tags: List[str] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(..., min_length=1)
    message_type: str = Field("text", description="text/image/file/code/reference")
    reply_to: Optional[str] = Field(None)


class GroupResponse(BaseModel):
    """群组响应"""
    id: str
    name: str
    description: str
    group_type: str
    creator_id: str
    member_count: int
    is_public: bool
    tags: List[str]


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== WebSocket ====================

@router.websocket("/ws/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket实时通信

    连接后支持:
    - 实时消息接收
    - 正在输入状态
    - 在线状态更新
    """
    service = get_chat_service()
    await websocket.accept()

    # 注册用户连接
    service.set_user_connection(user_id, websocket)

    # 发送未读消息数
    unread_count = service.get_total_unread(user_id)
    await websocket.send_json({
        "type": "unread_count",
        "data": {"total_unread": unread_count}
    })

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()

            action = data.get("action")

            if action == "send_message":
                # 发送消息
                chat_id = data.get("chat_id")
                content = data.get("content")
                message_type = MessageType(data.get("message_type", "text"))
                reply_to = data.get("reply_to")

                await service.send_message(
                    chat_id=chat_id,
                    sender_id=user_id,
                    content=content,
                    message_type=message_type,
                    reply_to=reply_to
                )

            elif action == "typing":
                # 正在输入状态
                chat_id = data.get("chat_id")
                recipients = service._get_chat_recipients(chat_id)
                recipients.remove(user_id)

                await service.broadcast_to_users(recipients, {
                    "type": "typing",
                    "data": {
                        "chat_id": chat_id,
                        "user_id": user_id
                    }
                })

            elif action == "mark_read":
                # 标记已读
                chat_id = data.get("chat_id")
                message_id = data.get("message_id")
                service.mark_as_read(chat_id, user_id, message_id)

            elif action == "join_group":
                # 加入群组
                group_id = data.get("group_id")
                service.join_group(group_id, user_id)

    except WebSocketDisconnect:
        service.remove_user_connection(user_id)


# ==================== 群组API ====================

@router.post("/groups")
async def create_group(
    request: CreateGroupRequest,
    user_id: str = Depends(get_current_user)
):
    """创建科研群组"""
    service = get_chat_service()

    try:
        group_type = GroupType(request.group_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid group type")

    group = service.create_group(
        name=request.name,
        description=request.description,
        group_type=group_type,
        creator_id=user_id,
        is_public=request.is_public,
        tags=request.tags
    )

    return {
        "message": "Group created successfully",
        "group": {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "group_type": group.group_type.value,
            "creator_id": group.creator_id,
            "invite_code": group.id[:8]  # 邀请码
        }
    }


@router.get("/groups")
async def list_groups(user_id: str = Depends(get_current_user)):
    """获取用户加入的群组"""
    service = get_chat_service()
    groups = service.get_user_groups(user_id)

    return {
        "groups": [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "group_type": g.group_type.value,
                "member_count": len(g.members),
                "is_public": g.is_public,
                "tags": g.tags,
                "unread_count": service.get_unread_count(g.id, user_id)
            }
            for g in groups
        ]
    }


@router.get("/groups/search")
async def search_groups(
    query: Optional[str] = None,
    group_type: Optional[str] = None,
    tags: Optional[str] = None
):
    """搜索公开群组"""
    service = get_chat_service()

    group_type_enum = None
    if group_type:
        try:
            group_type_enum = GroupType(group_type)
        except ValueError:
            pass

    tag_list = tags.split(",") if tags else None

    groups = service.search_groups(query, group_type_enum, tag_list)

    return {
        "groups": [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description[:100] + "..." if len(g.description) > 100 else g.description,
                "group_type": g.group_type.value,
                "member_count": len(g.members),
                "tags": g.tags
            }
            for g in groups
        ]
    }


@router.post("/groups/{group_id}/join")
async def join_group(
    group_id: str,
    user_id: str = Depends(get_current_user)
):
    """加入群组"""
    service = get_chat_service()

    success = service.join_group(group_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")

    return {"message": "Joined group successfully"}


@router.post("/groups/{group_id}/leave")
async def leave_group(
    group_id: str,
    user_id: str = Depends(get_current_user)
):
    """离开群组"""
    service = get_chat_service()

    success = service.leave_group(group_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")

    return {"message": "Left group successfully"}


@router.get("/groups/{group_id}/members")
async def get_group_members(group_id: str):
    """获取群组成员"""
    service = get_chat_service()
    group = service.get_group(group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members = []
    for member_id in group.members:
        user = service.get_user(member_id)
        if user:
            members.append({
                "user_id": user.user_id,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "status": user.status,
                "is_admin": member_id in group.admins,
                "is_creator": member_id == group.creator_id
            })

    return {"members": members}


# ==================== 消息API ====================

@router.post("/groups/{group_id}/messages")
async def send_group_message(
    group_id: str,
    request: SendMessageRequest,
    user_id: str = Depends(get_current_user)
):
    """发送群组消息"""
    service = get_chat_service()

    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if user_id not in group.members:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    try:
        message_type = MessageType(request.message_type)
    except ValueError:
        message_type = MessageType.TEXT

    message = await service.send_message(
        chat_id=group_id,
        sender_id=user_id,
        content=request.content,
        message_type=message_type,
        reply_to=request.reply_to
    )

    return {
        "message": "Message sent successfully",
        "message_id": message.id
    }


@router.get("/groups/{group_id}/messages")
async def get_group_messages(
    group_id: str,
    before: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user)
):
    """获取群组消息历史"""
    service = get_chat_service()

    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    messages = service.get_messages(group_id, before, limit)

    return {
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "content": m.content,
                "message_type": m.message_type.value,
                "created_at": m.created_at.isoformat(),
                "reply_to": m.reply_to,
                "reactions": m.reactions
            }
            for m in messages
        ]
    }


# ==================== 私聊API ====================

@router.post("/direct/{target_user_id}")
async def start_direct_chat(
    target_user_id: str,
    user_id: str = Depends(get_current_user)
):
    """发起私聊"""
    service = get_chat_service()

    chat = service.get_or_create_direct_chat(user_id, target_user_id)

    return {
        "chat_id": chat.id,
        "user1_id": chat.user1_id,
        "user2_id": chat.user2_id
    }


@router.get("/direct/{chat_id}/messages")
async def get_direct_messages(
    chat_id: str,
    before: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user)
):
    """获取私聊消息"""
    service = get_chat_service()

    chat = service.get_direct_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if user_id not in [chat.user1_id, chat.user2_id]:
        raise HTTPException(status_code=403, detail="Not authorized")

    messages = service.get_messages(chat_id, before, limit)

    return {
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "content": m.content,
                "message_type": m.message_type.value,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }


@router.post("/messages/{message_id}/reaction")
async def add_reaction(
    message_id: str,
    emoji: str,
    user_id: str = Depends(get_current_user)
):
    """添加表情反应"""
    service = get_chat_service()
    success = service.add_reaction(message_id, user_id, emoji)

    if not success:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"message": "Reaction added"}


# ==================== 邀请API ====================

@router.post("/groups/{group_id}/invite")
async def invite_to_group(
    group_id: str,
    invitee_id: str,
    message: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """邀请用户加入群组"""
    service = get_chat_service()

    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if user_id not in group.members:
        raise HTTPException(status_code=403, detail="Not a member")

    invitation = service.create_invitation(group_id, user_id, invitee_id, message)

    return {
        "invitation_id": invitation.id,
        "status": invitation.status
    }


@router.get("/invitations/pending")
async def get_pending_invitations(user_id: str = Depends(get_current_user)):
    """获取待处理邀请"""
    service = get_chat_service()
    invitations = service.get_pending_invitations(user_id)

    return {
        "invitations": [
            {
                "id": i.id,
                "chat_id": i.chat_id,
                "inviter_id": i.inviter_id,
                "message": i.message,
                "created_at": i.created_at.isoformat()
            }
            for i in invitations
        ]
    }


@router.post("/invitations/{invitation_id}/respond")
async def respond_invitation(
    invitation_id: str,
    accept: bool,
    user_id: str = Depends(get_current_user)
):
    """响应邀请"""
    service = get_chat_service()
    success = service.respond_invitation(invitation_id, accept)

    if not success:
        raise HTTPException(status_code=404, detail="Invitation not found")

    return {
        "message": "Invitation accepted" if accept else "Invitation rejected"
    }


# ==================== 用户状态 ====================

@router.get("/users/online")
async def get_online_users():
    """获取在线用户列表"""
    service = get_chat_service()
    online_users = [
        {
            "user_id": uid,
            "nickname": service.get_user(uid).nickname if service.get_user(uid) else uid
        }
        for uid in service._connections.keys()
    ]

    return {"online_users": online_users}
