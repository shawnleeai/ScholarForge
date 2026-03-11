"""
Team Management Service V2
团队管理服务V2 - 层级权限、年费订阅、团队空间
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .models import (
    Team, TeamMember, TeamRole, TeamTier, TeamStatus,
    SubscriptionPlan, TeamResource, TeamSpace, TeamAnnouncement,
    TeamActivity, TEAM_TIER_CONFIG, ROLE_PERMISSIONS
)


class TeamServiceV2:
    """团队管理服务V2"""

    def __init__(self):
        self._teams: Dict[str, Team] = {}
        self._members: Dict[str, TeamMember] = {}
        self._resources: Dict[str, TeamResource] = {}
        self._spaces: Dict[str, TeamSpace] = {}
        self._announcements: Dict[str, List[TeamAnnouncement]] = {}
        self._activities: Dict[str, List[TeamActivity]] = {}

    # ==================== 团队管理 ====================

    def create_team(
        self,
        name: str,
        description: str,
        owner_id: str,
        tier: TeamTier = TeamTier.STARTUP,
        institution: Optional[str] = None,
        **kwargs
    ) -> Team:
        """创建团队"""
        config = TEAM_TIER_CONFIG[tier]

        team = Team(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            owner_id=owner_id,
            tier=tier,
            status=TeamStatus.PENDING,
            institution=institution,
            max_members=config["max_members"],
            storage_limit_gb=config["storage_gb"],
            **kwargs
        )

        # 设置默认订阅结束时间（1年）
        team.subscription_end = datetime.utcnow() + timedelta(days=365)

        self._teams[team.id] = team

        # 创建者自动成为Owner
        self.add_member(team.id, owner_id, TeamRole.OWNER, invited_by=None)

        # 创建默认团队空间
        self._create_default_spaces(team.id)

        return team

    def get_team(self, team_id: str) -> Optional[Team]:
        """获取团队"""
        return self._teams.get(team_id)

    def update_team(
        self,
        team_id: str,
        updater_id: str,
        **updates
    ) -> Optional[Team]:
        """更新团队信息"""
        team = self._teams.get(team_id)
        if not team:
            return None

        # 检查权限
        if not self.has_permission(team_id, updater_id, "manage_team"):
            return None

        for key, value in updates.items():
            if hasattr(team, key):
                setattr(team, key, value)

        team.updated_at = datetime.utcnow()
        return team

    def upgrade_tier(
        self,
        team_id: str,
        new_tier: TeamTier,
        admin_id: str
    ) -> Optional[Team]:
        """升级团队等级"""
        team = self._teams.get(team_id)
        if not team:
            return None

        # 检查权限
        if not self.has_permission(team_id, admin_id, "manage_billing"):
            return None

        config = TEAM_TIER_CONFIG[new_tier]
        team.tier = new_tier
        team.max_members = config["max_members"]
        team.storage_limit_gb = config["storage_gb"]

        return team

    def renew_subscription(
        self,
        team_id: str,
        plan: SubscriptionPlan,
        admin_id: str
    ) -> Optional[Team]:
        """续订订阅"""
        team = self._teams.get(team_id)
        if not team:
            return None

        if not self.has_permission(team_id, admin_id, "manage_billing"):
            return None

        # 计算新的结束日期
        if plan == SubscriptionPlan.MONTHLY:
            extension = timedelta(days=30)
        elif plan == SubscriptionPlan.QUARTERLY:
            extension = timedelta(days=90)
        else:
            extension = timedelta(days=365)

        if team.subscription_end and team.subscription_end > datetime.utcnow():
            team.subscription_end += extension
        else:
            team.subscription_end = datetime.utcnow() + extension

        team.subscription_plan = plan
        team.status = TeamStatus.ACTIVE

        return team

    def _create_default_spaces(self, team_id: str):
        """创建默认团队空间"""
        default_spaces = [
            ("files", "共享文件", "团队共享文件存储"),
            ("knowledge", "知识库", "团队知识积累"),
            ("calendar", "团队日历", "会议和活动安排"),
            ("achievements", "成果墙", "团队成果展示"),
        ]

        for space_type, name, description in default_spaces:
            space = TeamSpace(
                id=str(uuid.uuid4()),
                team_id=team_id,
                space_type=space_type,
                name=name,
                description=description
            )
            self._spaces[space.id] = space

    # ==================== 成员管理 ====================

    def add_member(
        self,
        team_id: str,
        user_id: str,
        role: TeamRole,
        invited_by: Optional[str] = None,
        **kwargs
    ) -> TeamMember:
        """添加成员"""
        team = self._teams.get(team_id)
        if not team:
            raise ValueError("Team not found")

        # 检查人数限制
        if team.member_count >= team.max_members:
            raise ValueError("Team member limit reached")

        # 检查是否已在团队中
        existing = self.get_team_member(team_id, user_id)
        if existing:
            raise ValueError("User already in team")

        member = TeamMember(
            id=str(uuid.uuid4()),
            team_id=team_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by,
            **kwargs
        )

        self._members[member.id] = member
        team.member_count += 1

        # 记录活动
        self._log_activity(team_id, user_id, "join", details={"role": role.value})

        return member

    def remove_member(
        self,
        team_id: str,
        user_id: str,
        removed_by: str
    ) -> bool:
        """移除成员"""
        team = self._teams.get(team_id)
        if not team:
            return False

        # 检查权限
        remover = self.get_team_member(team_id, removed_by)
        if not remover or remover.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
            return False

        member = self.get_team_member(team_id, user_id)
        if not member:
            return False

        # 不能移除Owner
        if member.role == TeamRole.OWNER:
            return False

        # 不能移除比自己级别高的
        role_hierarchy = [TeamRole.GUEST, TeamRole.MEMBER, TeamRole.SENIOR,
                         TeamRole.ADVISOR, TeamRole.ADMIN, TeamRole.OWNER]
        if role_hierarchy.index(member.role) >= role_hierarchy.index(remover.role):
            return False

        member.is_active = False
        team.member_count -= 1

        self._log_activity(team_id, user_id, "leave", details={"removed_by": removed_by})

        return True

    def update_member_role(
        self,
        team_id: str,
        user_id: str,
        new_role: TeamRole,
        updated_by: str
    ) -> Optional[TeamMember]:
        """更新成员角色"""
        # 检查权限
        updater = self.get_team_member(team_id, updated_by)
        if not updater or updater.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
            return None

        member = self.get_team_member(team_id, user_id)
        if not member:
            return None

        # 不能修改Owner
        if member.role == TeamRole.OWNER:
            return None

        member.role = new_role
        return member

    def get_team_member(
        self,
        team_id: str,
        user_id: str
    ) -> Optional[TeamMember]:
        """获取团队成员"""
        for member in self._members.values():
            if member.team_id == team_id and member.user_id == user_id and member.is_active:
                return member
        return None

    def get_team_members(
        self,
        team_id: str,
        role: Optional[TeamRole] = None
    ) -> List[TeamMember]:
        """获取团队成员列表"""
        members = [
            m for m in self._members.values()
            if m.team_id == team_id and m.is_active
        ]

        if role:
            members = [m for m in members if m.role == role]

        # 按角色排序
        role_order = [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.ADVISOR,
                      TeamRole.SENIOR, TeamRole.MEMBER, TeamRole.GUEST]
        members.sort(key=lambda x: role_order.index(x.role))

        return members

    # ==================== 权限管理 ====================

    def has_permission(
        self,
        team_id: str,
        user_id: str,
        permission: str
    ) -> bool:
        """检查用户权限"""
        member = self.get_team_member(team_id, user_id)
        if not member:
            return False

        # 获取角色权限
        role_perms = ROLE_PERMISSIONS.get(member.role, {})

        # 检查是否有权限覆盖
        if permission in member.permissions_override:
            return member.permissions_override[permission]

        return role_perms.get(permission, False)

    def can_access_resource(
        self,
        team_id: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "view"
    ) -> bool:
        """检查资源访问权限"""
        member = self.get_team_member(team_id, user_id)
        if not member:
            return False

        # Owner和Admin可以访问所有资源
        if member.role in [TeamRole.OWNER, TeamRole.ADMIN]:
            return True

        # 查找资源
        resource = None
        for r in self._resources.values():
            if r.team_id == team_id and r.resource_type == resource_type and r.resource_id == resource_id:
                resource = r
                break

        if not resource:
            # 资源未设置权限，使用默认权限
            return self._check_default_permission(member.role, resource_type, action)

        # 检查可见性
        if resource.visibility == "public":
            return True

        if resource.visibility == "private":
            return resource.created_by == user_id

        # team可见性，检查角色
        if member.role.value in resource.allowed_roles:
            return True

        if user_id in resource.allowed_members:
            return True

        return False

    def _check_default_permission(
        self,
        role: TeamRole,
        resource_type: str,
        action: str
    ) -> bool:
        """检查默认权限"""
        # 默认权限矩阵
        default_perms = {
            "paper": {
                "view": [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.ADVISOR,
                        TeamRole.SENIOR, TeamRole.MEMBER],
                "edit": [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.ADVISOR, TeamRole.SENIOR],
                "delete": [TeamRole.OWNER, TeamRole.ADMIN]
            },
            "project": {
                "view": [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.ADVISOR,
                        TeamRole.SENIOR, TeamRole.MEMBER],
                "edit": [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.SENIOR],
                "delete": [TeamRole.OWNER, TeamRole.ADMIN]
            },
            "file": {
                "view": [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.ADVISOR,
                        TeamRole.SENIOR, TeamRole.MEMBER],
                "edit": [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.SENIOR, TeamRole.MEMBER],
                "delete": [TeamRole.OWNER, TeamRole.ADMIN, TeamRole.SENIOR]
            }
        }

        resource_perms = default_perms.get(resource_type, {})
        action_perms = resource_perms.get(action, [])

        return role in action_perms

    # ==================== 团队空间 ====================

    def get_team_spaces(self, team_id: str) -> List[TeamSpace]:
        """获取团队空间"""
        return [
            s for s in self._spaces.values()
            if s.team_id == team_id
        ]

    def can_access_space(
        self,
        space_id: str,
        user_id: str
    ) -> bool:
        """检查空间访问权限"""
        space = self._spaces.get(space_id)
        if not space:
            return False

        member = self.get_team_member(space.team_id, user_id)
        if not member:
            return False

        if space.is_public:
            return True

        return member.role.value in space.allowed_roles

    # ==================== 公告管理 ====================

    def create_announcement(
        self,
        team_id: str,
        author_id: str,
        title: str,
        content: str,
        visible_to_roles: Optional[List[str]] = None
    ) -> Optional[TeamAnnouncement]:
        """创建公告"""
        # 检查权限
        if not self.has_permission(team_id, author_id, "can_announce"):
            return None

        announcement = TeamAnnouncement(
            id=str(uuid.uuid4()),
            team_id=team_id,
            author_id=author_id,
            title=title,
            content=content,
            visible_to_roles=visible_to_roles or ["owner", "admin", "advisor", "senior", "member"]
        )

        if team_id not in self._announcements:
            self._announcements[team_id] = []

        self._announcements[team_id].append(announcement)

        return announcement

    def get_announcements(
        self,
        team_id: str,
        user_id: str
    ) -> List[TeamAnnouncement]:
        """获取可见公告"""
        member = self.get_team_member(team_id, user_id)
        if not member:
            return []

        announcements = self._announcements.get(team_id, [])

        # 过滤可见公告
        visible = [
            a for a in announcements
            if member.role.value in a.visible_to_roles
        ]

        # 按置顶和时间排序
        visible.sort(key=lambda x: (not x.is_pinned, x.created_at), reverse=True)

        return visible

    # ==================== 活动记录 ====================

    def _log_activity(
        self,
        team_id: str,
        user_id: str,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """记录团队活动"""
        activity = TeamActivity(
            id=str(uuid.uuid4()),
            team_id=team_id,
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {}
        )

        if team_id not in self._activities:
            self._activities[team_id] = []

        self._activities[team_id].append(activity)

    def get_team_activities(
        self,
        team_id: str,
        limit: int = 20
    ) -> List[TeamActivity]:
        """获取团队活动"""
        activities = self._activities.get(team_id, [])
        activities.sort(key=lambda x: x.created_at, reverse=True)
        return activities[:limit]

    # ==================== 邀请管理 ====================

    def invite_member(
        self,
        team_id: str,
        email: str,
        role: TeamRole,
        invited_by: str
    ) -> Dict[str, Any]:
        """邀请成员"""
        team = self._teams.get(team_id)
        if not team:
            return {"success": False, "error": "Team not found"}

        # 检查权限
        if not self.has_permission(team_id, invited_by, "can_manage_members"):
            return {"success": False, "error": "No permission"}

        # 检查人数限制
        if team.member_count >= team.max_members:
            return {"success": False, "error": "Member limit reached"}

        # 生成邀请码
        invite_code = str(uuid.uuid4())[:8].upper()

        return {
            "success": True,
            "invite_code": invite_code,
            "email": email,
            "role": role.value,
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }


# 单例
_team_service_v2 = None


def get_team_service_v2() -> TeamServiceV2:
    """获取团队服务V2单例"""
    global _team_service_v2
    if _team_service_v2 is None:
        _team_service_v2 = TeamServiceV2()
    return _team_service_v2
