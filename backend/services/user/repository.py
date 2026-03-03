"""
用户数据访问层
数据库 CRUD 操作
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import User, Team, TeamMember
from .schemas import UserCreate, UserUpdate, TeamCreate, TeamMemberAdd
from shared.security import get_password_hash, verify_password


class UserRepository:
    """用户数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_data: UserCreate) -> User:
        """创建用户"""
        user = User(
            email=user_data.email.lower(),
            username=user_data.username.lower(),
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            university=user_data.university,
            department=user_data.department,
            major=user_data.major,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """通过ID获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """更新用户"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """更新最后登录时间"""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await self.db.flush()

    async def change_password(
        self, user_id: uuid.UUID, old_password: str, new_password: str
    ) -> bool:
        """修改密码"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        if not verify_password(old_password, user.password_hash):
            return False

        user.password_hash = get_password_hash(new_password)
        await self.db.flush()
        return True

    async def delete(self, user_id: uuid.UUID) -> bool:
        """删除用户（软删除）"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        await self.db.flush()
        return True

    async def verify_email(self, user_id: uuid.UUID) -> bool:
        """验证邮箱"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_verified = True
        await self.db.flush()
        return True

    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        result = await self.db.execute(
            select(func.count()).where(User.email == email.lower())
        )
        return result.scalar() > 0

    async def exists_by_username(self, username: str) -> bool:
        """检查用户名是否已存在"""
        result = await self.db.execute(
            select(func.count()).where(User.username == username.lower())
        )
        return result.scalar() > 0

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """用户认证"""
        user = await self.get_by_email(email)
        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[User], int]:
        """搜索用户"""
        search_term = f"%{query}%"
        base_query = select(User).where(
            or_(
                User.username.ilike(search_term),
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
            ),
            User.is_active == True,
        )

        # 计算总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query) or 0

        # 分页查询
        result = await self.db.execute(
            base_query
            .order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        users = list(result.scalars().all())

        return users, total


class TeamRepository:
    """团队数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, owner_id: uuid.UUID, team_data: TeamCreate) -> Team:
        """创建团队"""
        team = Team(
            name=team_data.name,
            description=team_data.description,
            owner_id=owner_id,
        )
        self.db.add(team)
        await self.db.flush()

        # 添加创建者为成员
        member = TeamMember(
            team_id=team.id,
            user_id=owner_id,
            role="owner",
        )
        self.db.add(member)
        await self.db.flush()

        await self.db.refresh(team)
        return team

    async def get_by_id(self, team_id: uuid.UUID) -> Optional[Team]:
        """获取团队"""
        result = await self.db.execute(
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.id == team_id)
        )
        return result.scalar_one_or_none()

    async def get_user_teams(self, user_id: uuid.UUID) -> List[Team]:
        """获取用户所属团队"""
        result = await self.db.execute(
            select(Team)
            .join(TeamMember)
            .where(TeamMember.user_id == user_id)
            .options(selectinload(Team.members))
        )
        return list(result.scalars().all())

    async def add_member(
        self, team_id: uuid.UUID, user_id: uuid.UUID, role: str = "member"
    ) -> TeamMember:
        """添加成员"""
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_member(self, team_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """移除成员"""
        result = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if member and member.role != "owner":
            await self.db.delete(member)
            await self.db.flush()
            return True
        return False

    async def update_member_role(
        self, team_id: uuid.UUID, user_id: uuid.UUID, role: str
    ) -> bool:
        """更新成员角色"""
        result = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if member and member.role != "owner":
            member.role = role
            await self.db.flush()
            return True
        return False

    async def is_member(self, team_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """检查是否为团队成员"""
        result = await self.db.execute(
            select(func.count()).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        return (result.scalar() or 0) > 0

    async def get_member_role(
        self, team_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[str]:
        """获取成员角色"""
        result = await self.db.execute(
            select(TeamMember.role).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
