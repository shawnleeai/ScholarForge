"""
Team Management Models V2
团队管理模型V2 - 层级权限、年费订阅、团队空间
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class TeamTier(str, Enum):
    """团队等级"""
    STARTUP = "startup"         # 初创团队(≤10人)
    GROWING = "growing"         # 成长团队(≤30人)
    PROFESSIONAL = "professional"  # 专业团队(≤100人)
    ENTERPRISE = "enterprise"   # 企业团队(>100人)


class TeamRole(str, Enum):
    """团队角色"""
    OWNER = "owner"             # 大老板 - 全部权限
    ADMIN = "admin"             # 小老板 - 管理权限
    ADVISOR = "advisor"         # 导师 - 指导权限
    SENIOR = "senior"           # 师兄师姐 - 高级成员
    MEMBER = "member"           # 学生/成员 - 普通权限
    GUEST = "guest"             # 访客 - 只读权限


class TeamStatus(str, Enum):
    """团队状态"""
    PENDING = "pending"         # 待审核
    ACTIVE = "active"           # 正常运营
    SUSPENDED = "suspended"     # 暂停
    EXPIRED = "expired"         # 订阅过期


class SubscriptionPlan(str, Enum):
    """订阅计划"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class Team:
    """团队实体V2"""
    id: str
    name: str
    description: str
    owner_id: str

    # 团队等级
    tier: TeamTier = TeamTier.STARTUP
    status: TeamStatus = TeamStatus.PENDING

    # 认证信息
    is_verified: bool = False
    verification_documents: List[str] = field(default_factory=list)
    institution: Optional[str] = None
    department: Optional[str] = None
    website: Optional[str] = None

    # 订阅信息
    subscription_plan: SubscriptionPlan = SubscriptionPlan.YEARLY
    subscription_start: datetime = field(default_factory=datetime.utcnow)
    subscription_end: Optional[datetime] = None
    auto_renew: bool = True

    # 品牌
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    color_theme: str = "#1890ff"

    # 统计
    member_count: int = 0
    max_members: int = 10
    paper_count: int = 0
    project_count: int = 0
    storage_used_gb: float = 0.0
    storage_limit_gb: float = 10.0

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TeamMember:
    """团队成员V2"""
    id: str
    team_id: str
    user_id: str
    role: TeamRole

    # 入团信息
    invited_by: Optional[str] = None
    joined_at: datetime = field(default_factory=datetime.utcnow)

    # 状态
    is_active: bool = True
    last_active_at: Optional[datetime] = None

    # 个人信息（团队内）
    display_name: Optional[str] = None
    title: Optional[str] = None  # 职称/职位
    research_area: Optional[str] = None

    # 权限覆盖
    permissions_override: Dict[str, bool] = field(default_factory=dict)


@dataclass
class TeamPermission:
    """团队权限定义"""
    resource_type: str      # paper/project/file/calendar等
    action: str             # view/edit/delete/admin等

    # 各角色是否有权限
    owner: bool = True
    admin: bool = True
    advisor: bool = True
    senior: bool = True
    member: bool = True
    guest: bool = False


@dataclass
class TeamResource:
    """团队资源"""
    id: str
    team_id: str
    resource_type: str      # paper/project/file/folder等
    resource_id: str

    # 权限设置
    visibility: str = "team"  # public/team/private
    allowed_roles: List[str] = field(default_factory=list)
    allowed_members: List[str] = field(default_factory=list)

    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TeamSpace:
    """团队空间"""
    id: str
    team_id: str
    space_type: str         # files/knowledge/calendar/achievements
    name: str
    description: str = ""

    # 设置
    is_public: bool = False
    allowed_roles: List[str] = field(default_factory=lambda: ["owner", "admin", "advisor", "senior", "member"])

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TeamAnnouncement:
    """团队公告"""
    id: str
    team_id: str
    author_id: str
    title: str
    content: str

    # 可见性
    visible_to_roles: List[str] = field(default_factory=lambda: ["owner", "admin", "advisor", "senior", "member"])
    is_pinned: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TeamActivity:
    """团队活动记录"""
    id: str
    team_id: str
    user_id: str
    action: str             # join/leave/create/update等
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


# 团队等级配置
TEAM_TIER_CONFIG = {
    TeamTier.STARTUP: {
        "name": "初创团队",
        "max_members": 10,
        "storage_gb": 50,
        "yearly_price_cny": 2999,
        "features": ["basic_collaboration", "shared_storage", "team_calendar"]
    },
    TeamTier.GROWING: {
        "name": "成长团队",
        "max_members": 30,
        "storage_gb": 200,
        "yearly_price_cny": 7999,
        "features": ["advanced_collaboration", "knowledge_base", "priority_support"]
    },
    TeamTier.PROFESSIONAL: {
        "name": "专业团队",
        "max_members": 100,
        "storage_gb": 1000,
        "yearly_price_cny": 19999,
        "features": ["full_features", "custom_branding", "dedicated_support", "api_access"]
    },
    TeamTier.ENTERPRISE: {
        "name": "企业团队",
        "max_members": 999999,
        "storage_gb": 10000,
        "yearly_price_cny": 49999,
        "features": ["all_features", "sso", "sla", "custom_development"]
    }
}


# 角色权限矩阵
ROLE_PERMISSIONS = {
    TeamRole.OWNER: {
        "description": "大老板 - 团队所有者",
        "can_manage_team": True,
        "can_manage_members": True,
        "can_manage_billing": True,
        "can_delete_team": True,
        "can_access_all": True,
        "can_announce": True,
    },
    TeamRole.ADMIN: {
        "description": "小老板 - 团队管理员",
        "can_manage_team": True,
        "can_manage_members": True,
        "can_manage_billing": False,
        "can_delete_team": False,
        "can_access_all": True,
        "can_announce": True,
    },
    TeamRole.ADVISOR: {
        "description": "导师 - 学术指导",
        "can_manage_team": False,
        "can_manage_members": False,
        "can_manage_billing": False,
        "can_delete_team": False,
        "can_access_all": True,
        "can_announce": True,
    },
    TeamRole.SENIOR: {
        "description": "师兄师姐 - 高级成员",
        "can_manage_team": False,
        "can_manage_members": False,
        "can_manage_billing": False,
        "can_delete_team": False,
        "can_access_all": False,
        "can_announce": False,
    },
    TeamRole.MEMBER: {
        "description": "学生/成员 - 普通成员",
        "can_manage_team": False,
        "can_manage_members": False,
        "can_manage_billing": False,
        "can_delete_team": False,
        "can_access_all": False,
        "can_announce": False,
    },
    TeamRole.GUEST: {
        "description": "访客 - 只读访问",
        "can_manage_team": False,
        "can_manage_members": False,
        "can_manage_billing": False,
        "can_delete_team": False,
        "can_access_all": False,
        "can_announce": False,
    }
}
