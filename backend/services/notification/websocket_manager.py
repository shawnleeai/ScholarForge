"""
WebSocket Manager for Notifications
WebSocket连接管理器 - 支持实时通知推送
"""

import json
from typing import Dict, Set, Optional, Callable
from fastapi import WebSocket, WebSocketDisconnect
from uuid import UUID
import asyncio


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> user_id mapping
        self.connection_users: Dict[WebSocket, str] = {}
        # 用户在线状态
        self.user_status: Dict[str, dict] = {}
        # 消息处理器
        self.message_handlers: Dict[str, Callable] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """建立WebSocket连接"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.connection_users[websocket] = user_id

        # 更新用户在线状态
        self.user_status[user_id] = {
            'online': True,
            'connections': len(self.active_connections[user_id]),
            'last_seen': None
        }

        # 发送连接成功消息
        await websocket.send_json({
            'type': 'connection_established',
            'data': {
                'user_id': user_id,
                'message': 'Connected to notification service'
            }
        })

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        user_id = self.connection_users.get(websocket)

        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # 如果没有连接了，更新状态为离线
            if not self.active_connections[user_id]:
                self.user_status[user_id] = {
                    'online': False,
                    'connections': 0,
                    'last_seen': asyncio.get_event_loop().time()
                }
                del self.active_connections[user_id]

        if websocket in self.connection_users:
            del self.connection_users[websocket]

    async def send_to_user(self, user_id: str, message: dict):
        """发送消息给指定用户"""
        if user_id not in self.active_connections:
            return False

        disconnected = set()
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)

        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect(websocket)

        return len(disconnected) < len(self.active_connections.get(user_id, set()))

    async def broadcast(self, message: dict, exclude_user: str = None):
        """广播消息给所有连接的用户"""
        disconnected = set()

        for user_id, connections in self.active_connections.items():
            if user_id == exclude_user:
                continue

            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.add(websocket)

        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_to_role(self, role: str, message: dict):
        """广播给特定角色的用户"""
        # 这里需要从数据库查询角色对应的用户
        # 简化实现，实际应该查询用户服务
        pass

    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    def get_user_connections_count(self, user_id: str) -> int:
        """获取用户的连接数"""
        return len(self.active_connections.get(user_id, set()))

    def get_online_users(self) -> list:
        """获取所有在线用户"""
        return [
            {
                'user_id': user_id,
                'connections': len(connections),
                'status': self.user_status.get(user_id, {})
            }
            for user_id, connections in self.active_connections.items()
        ]

    def register_message_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler

    async def handle_message(self, websocket: WebSocket, user_id: str, message: dict):
        """处理收到的消息"""
        message_type = message.get('type')
        handler = self.message_handlers.get(message_type)

        if handler:
            await handler(websocket, user_id, message.get('data', {}))
        else:
            # 默认处理：回显消息
            await websocket.send_json({
                'type': 'echo',
                'data': message
            })


# 全局连接管理器实例
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = None):
    """
    WebSocket端点处理函数

    用法:
        @app.websocket("/ws/notifications/{user_id}")
        async def notifications_ws(websocket: WebSocket, user_id: str, token: str = None):
            await websocket_endpoint(websocket, user_id, token)
    """
    # 这里应该验证token
    # if not await verify_token(token):
    #     await websocket.close(code=4001, reason="Unauthorized")
    #     return

    await manager.connect(websocket, user_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await manager.handle_message(websocket, user_id, message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    'type': 'error',
                    'data': {'message': 'Invalid JSON format'}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        raise e


# ==================== 快捷方法 ====================

async def notify_user(user_id: str, notification_type: str, data: dict):
    """快捷方法：发送通知给用户"""
    await manager.send_to_user(user_id, {
        'type': notification_type,
        'data': data,
        'timestamp': asyncio.get_event_loop().time()
    })


async def broadcast_system_message(message: str, level: str = 'info'):
    """广播系统消息"""
    await manager.broadcast({
        'type': 'system_message',
        'data': {
            'message': message,
            'level': level  # info, warning, error
        }
    })


async def notify_paper_collaborators(paper_id: str, exclude_user_id: str, event_type: str, data: dict):
    """通知论文的所有协作者"""
    # 这里需要查询论文的协作者列表
    # 简化实现，实际应该查询论文服务
    # collaborators = await get_paper_collaborators(paper_id)
    # for user_id in collaborators:
    #     if user_id != exclude_user_id:
    #         await notify_user(user_id, event_type, data)
    pass

