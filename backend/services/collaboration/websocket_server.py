"""
WebSocket协作服务器
基于Yjs的实时协作编辑
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime

import y_py as Y
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class CollaborationRoom:
    """协作房间"""

    def __init__(self, room_id: str, document_id: str):
        self.room_id = room_id
        self.document_id = document_id
        self.clients: Dict[str, WebSocket] = {}  # user_id -> websocket
        self.user_info: Dict[str, dict] = {}  # user_id -> user info
        self.ydoc = Y.YDoc()
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.update_buffer = bytearray()

    async def join(self, user_id: str, user_info: dict, websocket: WebSocket):
        """用户加入房间"""
        self.clients[user_id] = websocket
        self.user_info[user_id] = {
            **user_info,
            "joined_at": datetime.now().isoformat(),
            "cursor_position": None,
        }
        self.last_activity = datetime.now()

        # 广播用户加入消息
        await self.broadcast({
            "type": "user_joined",
            "user_id": user_id,
            "user_name": user_info.get("name", "Unknown"),
            "users_count": len(self.clients),
        }, exclude_user=user_id)

        # 发送当前在线用户列表给新用户
        await websocket.send_json({
            "type": "users_list",
            "users": [
                {
                    "user_id": uid,
                    "user_name": info.get("name", "Unknown"),
                    "avatar": info.get("avatar"),
                    "cursor_position": info.get("cursor_position"),
                }
                for uid, info in self.user_info.items()
            ],
        })

        logger.info(f"User {user_id} joined room {self.room_id}")

    async def leave(self, user_id: str):
        """用户离开房间"""
        if user_id in self.clients:
            del self.clients[user_id]
        if user_id in self.user_info:
            del self.user_info[user_id]

        self.last_activity = datetime.now()

        # 广播用户离开消息
        await self.broadcast({
            "type": "user_left",
            "user_id": user_id,
            "users_count": len(self.clients),
        })

        logger.info(f"User {user_id} left room {self.room_id}")

    async def handle_message(self, user_id: str, message: dict):
        """处理客户端消息"""
        msg_type = message.get("type")

        if msg_type == "yjs_update":
            # Yjs文档更新
            update_data = message.get("data")
            if update_data:
                # 应用到本地YDoc
                try:
                    update_bytes = bytes(update_data)
                    Y.apply_update(self.ydoc, update_bytes)

                    # 广播给其他客户端
                    await self.broadcast({
                        "type": "yjs_update",
                        "data": update_data,
                        "user_id": user_id,
                    }, exclude_user=user_id)
                except Exception as e:
                    logger.error(f"Yjs update error: {e}")

        elif msg_type == "cursor_position":
            # 光标位置更新
            position = message.get("position")
            if user_id in self.user_info:
                self.user_info[user_id]["cursor_position"] = position

            # 广播光标位置
            await self.broadcast({
                "type": "cursor_update",
                "user_id": user_id,
                "user_name": self.user_info.get(user_id, {}).get("name", "Unknown"),
                "position": position,
            }, exclude_user=user_id)

        elif msg_type == "selection_change":
            # 选区变化
            selection = message.get("selection")
            await self.broadcast({
                "type": "selection_update",
                "user_id": user_id,
                "user_name": self.user_info.get(user_id, {}).get("name", "Unknown"),
                "selection": selection,
            }, exclude_user=user_id)

        elif msg_type == "chat_message":
            # 聊天消息
            content = message.get("content")
            await self.broadcast({
                "type": "chat_message",
                "user_id": user_id,
                "user_name": self.user_info.get(user_id, {}).get("name", "Unknown"),
                "content": content,
                "timestamp": datetime.now().isoformat(),
            })

        elif msg_type == "awareness":
            # Yjs awareness 状态
            awareness_data = message.get("data")
            await self.broadcast({
                "type": "awareness",
                "user_id": user_id,
                "data": awareness_data,
            }, exclude_user=user_id)

        self.last_activity = datetime.now()

    async def broadcast(self, message: dict, exclude_user: Optional[str] = None):
        """广播消息给所有客户端"""
        disconnected = []

        for user_id, websocket in self.clients.items():
            if user_id == exclude_user:
                continue

            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(user_id)

        # 清理断开的连接
        for user_id in disconnected:
            await self.leave(user_id)

    def get_document_state(self) -> bytes:
        """获取文档当前状态"""
        return Y.encode_state_as_update(self.ydoc)

    def is_empty(self) -> bool:
        """检查房间是否为空"""
        return len(self.clients) == 0

    def is_inactive(self, timeout_seconds: int = 3600) -> bool:
        """检查房间是否不活跃"""
        return (datetime.now() - self.last_activity).total_seconds() > timeout_seconds


class CollaborationManager:
    """协作管理器"""

    def __init__(self):
        self.rooms: Dict[str, CollaborationRoom] = {}  # room_id -> room
        self.document_to_room: Dict[str, str] = {}  # document_id -> room_id

    def get_or_create_room(self, document_id: str) -> CollaborationRoom:
        """获取或创建协作房间"""
        if document_id in self.document_to_room:
            room_id = self.document_to_room[document_id]
            return self.rooms[room_id]

        room_id = f"room_{document_id}_{datetime.now().timestamp()}"
        room = CollaborationRoom(room_id, document_id)
        self.rooms[room_id] = room
        self.document_to_room[document_id] = room_id

        return room

    def get_room(self, room_id: str) -> Optional[CollaborationRoom]:
        """获取房间"""
        return self.rooms.get(room_id)

    def get_room_by_document(self, document_id: str) -> Optional[CollaborationRoom]:
        """通过文档ID获取房间"""
        room_id = self.document_to_room.get(document_id)
        if room_id:
            return self.rooms.get(room_id)
        return None

    async def cleanup_inactive_rooms(self, timeout_seconds: int = 3600):
        """清理不活跃的房间"""
        to_remove = []

        for room_id, room in self.rooms.items():
            if room.is_inactive(timeout_seconds):
                # 通知所有客户端房间关闭
                await room.broadcast({
                    "type": "room_closed",
                    "reason": "inactive",
                })
                to_remove.append(room_id)

        for room_id in to_remove:
            room = self.rooms.pop(room_id, None)
            if room:
                self.document_to_room.pop(room.document_id, None)
                logger.info(f"Cleaned up inactive room: {room_id}")

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_rooms": len(self.rooms),
            "total_users": sum(len(room.clients) for room in self.rooms.values()),
            "rooms": [
                {
                    "room_id": room.room_id,
                    "document_id": room.document_id,
                    "users_count": len(room.clients),
                    "users": list(room.user_info.keys()),
                    "created_at": room.created_at.isoformat(),
                    "last_activity": room.last_activity.isoformat(),
                }
                for room in self.rooms.values()
            ],
        }


# 全局协作管理器实例
collaboration_manager = CollaborationManager()


async def handle_websocket(websocket: WebSocket, document_id: str, user_id: str, user_info: dict):
    """处理WebSocket连接"""
    await websocket.accept()

    room = collaboration_manager.get_or_create_room(document_id)
    await room.join(user_id, user_info, websocket)

    try:
        # 发送当前文档状态
        state = room.get_document_state()
        await websocket.send_json({
            "type": "sync",
            "state": list(state),  # 转换为列表以便JSON序列化
        })

        while True:
            # 接收消息
            data = await websocket.receive()
            msg_type = data.get("type")

            # 处理文本消息
            if msg_type == "text" and "text" in data:
                try:
                    message = json.loads(data["text"])
                    await room.handle_message(user_id, message)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from {user_id}")
            # 处理二进制消息
            elif msg_type == "bytes" and "bytes" in data:
                binary_data = data["bytes"]
                try:
                    Y.apply_update(room.ydoc, binary_data)
                    await room.broadcast({
                        "type": "yjs_update",
                        "data": list(binary_data),
                        "user_id": user_id,
                    }, exclude_user=user_id)
                except Exception as e:
                    logger.error(f"Yjs binary update error: {e}")
            # 处理断开连接消息
            elif msg_type == "websocket.disconnect":
                logger.info(f"Client {user_id} sent disconnect message")
                break

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from room {room.room_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
    finally:
        # 确保用户离开房间并清理资源
        try:
            await room.leave(user_id)
        except Exception as e:
            logger.warning(f"Error during room leave for {user_id}: {e}")

        # 尝试关闭WebSocket连接
        try:
            await websocket.close()
        except Exception:
            pass  # 连接可能已关闭

        # 如果房间为空，清理房间
        if room.is_empty():
            collaboration_manager.rooms.pop(room.room_id, None)
            collaboration_manager.document_to_room.pop(document_id, None)
            logger.info(f"Cleaned up empty room: {room.room_id}")
