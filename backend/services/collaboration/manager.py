"""
协作服务管理器
连接管理、房间管理、消息广播
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class User:
    """用户连接"""
    id: str
    name: str
    color: str
    websocket: Optional[object] = None
    paper_id: str = ""
    section_id: Optional[str] = None
    cursor_position: Optional[dict] = None
    last_active: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)


@dataclass
class PaperRoom:
    """论文房间"""
    paper_id: str
    users: Dict[str, User] = field(default_factory=dict)
    content: str = ""
    history: list = field(default_factory=list)

    def add_user(self, user: User):
        self.users[user.id] = user

    def remove_user(self, user_id: str):
        if user_id in self.users:
            del self.users[user_id]

    def get_user_list(self):
        return [
            {
                "id": u.id,
                "name": u.name,
                "color": u.color,
                "section_id": u.section_id,
            }
            for u in self.users.values()
        ]


class ConnectionManager:
    """连接管理器"""

    def __init__(self):
        # paper_id -> PaperRoom
        self.rooms: Dict[str, PaperRoom] = {}
        # 活跃连接跟踪
        self._heartbeat_task = None

    async def start_heartbeat_checker(self, interval: int = 30, timeout: int = 60):
        """启动心跳检测任务"""
        self._heartbeat_task = asyncio.create_task(
            self._check_heartbeats(interval, timeout)
        )

    async def _check_heartbeats(self, interval: int, timeout: int):
        """定期检查心跳超时的连接"""
        while True:
            await asyncio.sleep(interval)
            now = datetime.now()
            timeout_users = []

            for room in self.rooms.values():
                for user in room.users.values():
                    elapsed = (now - user.last_heartbeat).total_seconds()
                    if elapsed > timeout:
                        timeout_users.append((room.paper_id, user.id))

            # 断开超时用户
            for paper_id, user_id in timeout_users:
                await self.disconnect_user(paper_id, user_id, reason="heartbeat_timeout")

    async def connect(self, websocket, paper_id: str):
        await websocket.accept()
        # 创建房间（如果不存在）
        if paper_id not in self.rooms:
            self.rooms[paper_id] = PaperRoom(paper_id=paper_id)

    def disconnect(self, paper_id: str, user_id: str):
        if paper_id in self.rooms:
            self.rooms[paper_id].remove_user(user_id)
            # 如果房间为空，删除房间
            if not self.rooms[paper_id].users:
                del self.rooms[paper_id]

    async def disconnect_user(self, paper_id: str, user_id: str, reason: str = "disconnected"):
        """断开指定用户"""
        room = self.get_room(paper_id)
        if room and user_id in room.users:
            user = room.users[user_id]
            try:
                if user.websocket:
                    await user.websocket.close(code=1000, reason=reason)
            except:
                pass
            self.disconnect(paper_id, user_id)
            # 通知其他用户
            await self.broadcast(paper_id, {
                "type": "user_left",
                "user_id": user_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            })

    def get_room(self, paper_id: str) -> Optional[PaperRoom]:
        return self.rooms.get(paper_id)

    async def broadcast(self, paper_id: str, message: dict, exclude_user: Optional[str] = None):
        """广播消息到房间内所有用户"""
        room = self.get_room(paper_id)
        if not room:
            return

        for user in room.users.values():
            if user.id != exclude_user and user.websocket:
                try:
                    await user.websocket.send_json(message)
                except:
                    pass


# 全局管理器实例
manager = ConnectionManager()
