"""
研究团队数据模型
定义团队、成员、角色等数据模型
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TeamRole(str, Enum):
    """团队角色"""
    OWNER = "owner"           # 所有者
    ADMIN = "admin"           # 管理员
    MEMBER = "member"         # 成员
    GUEST = "guest"           # 访客


class JoinStatus(str, Enum):
    """加入状态"""
    PENDING = "pending"       # 待审核
    APPROVED = "approved"     # 已通过
    REJECTED = "rejected"     # 已拒绝
    INVITED = "invited"       # 已邀请


class TeamPermission(str, Enum):
    """团队权限"""
    MANAGE_MEMBERS = "manage_members"      # 管理成员
    MANAGE_PROJECTS = "manage_projects"    # 管理项目
    MANAGE_PUBLICATIONS = "manage_publications"  # 管理发表
    MANAGE_RESOURCES = "manage_resources"  # 管理资源
    VIEW_ANALYTICS = "view_analytics"      # 查看统计
    INVITE_MEMBERS = "invite_members"      # 邀请成员


ROLE_PERMISSIONS: Dict[TeamRole, List[TeamPermission]] = {
    TeamRole.OWNER: [
        TeamPermission.MANAGE_MEMBERS,
        TeamPermission.MANAGE_PROJECTS,
        TeamPermission.MANAGE_PUBLICATIONS,
        TeamPermission.MANAGE_RESOURCES,
        TeamPermission.VIEW_ANALYTICS,
        TeamPermission.INVITE_MEMBERS,
    ],
    TeamRole.ADMIN: [
        TeamPermission.MANAGE_PROJECTS,
        TeamPermission.MANAGE_PUBLICATIONS,
        TeamPermission.MANAGE_RESOURCES,
        TeamPermission.VIEW_ANALYTICS,
        TeamPermission.INVITE_MEMBERS,
    ],
    TeamRole.MEMBER: [
        TeamPermission.MANAGE_PROJECTS,
        TeamPermission.MANAGE_PUBLICATIONS,
    ],
    TeamRole.GUEST: [],
}


class TeamMember(BaseModel):
    """团队成员"""
    user_id: str
    username: str
    email: str
    avatar_url: Optional[str] = None
    role: TeamRole = TeamRole.MEMBER
    join_status: JoinStatus = JoinStatus.APPROVED
    join_date: datetime = Field(default_factory=datetime.now)
    contributions: int = 0                    # 贡献数
    last_active: Optional[datetime] = None
    research_interests: List[str] = []        # 研究兴趣
    bio: Optional[str] = None                 # 简介


class ResearchProject(BaseModel):
    """研究项目"""
    id: str
    name: str
    description: Optional[str] = None
    status: str = "active"                    # active, completed, paused
    start_date: datetime
    end_date: Optional[datetime] = None
    leader_id: str                            # 项目负责人
    members: List[str] = []                   # 参与成员ID列表
    publications: List[str] = []              # 相关论文ID
    progress: int = 0                         # 进度百分比
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TeamResource(BaseModel):
    """团队资源"""
    id: str
    name: str
    type: str                                 # dataset, code, document, tool
    description: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    uploaded_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    downloads: int = 0
    tags: List[str] = []


class ResearchTeam(BaseModel):
    """研究团队"""
    id: str
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    institution: Optional[str] = None         # 所属机构
    research_fields: List[str] = []           # 研究领域
    created_by: str                           # 创建者ID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 成员
    members: List[TeamMember] = []

    # 内容
    projects: List[ResearchProject] = []
    publications: List[str] = []              # 论文ID列表
    resources: List[TeamResource] = []

    # 设置
    is_public: bool = False                   # 是否公开
    join_type: str = "invite"                 # invite, application, open
    max_members: int = 50

    # 统计
    stats: Dict[str, Any] = Field(default_factory=dict)


class TeamInvitation(BaseModel):
    """团队邀请"""
    id: str
    team_id: str
    inviter_id: str
    invitee_email: str
    role: TeamRole = TeamRole.MEMBER
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    status: str = "pending"                   # pending, accepted, declined, expired


class JoinApplication(BaseModel):
    """加入申请"""
    id: str
    team_id: str
    applicant_id: str
    applicant_name: str
    message: Optional[str] = None
    research_interests: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"                   # pending, approved, rejected


class TeamActivity(BaseModel):
    """团队活动"""
    id: str
    team_id: str
    user_id: str
    username: str
    action: str                               # join, leave, publish, complete_project, etc.
    target_type: Optional[str] = None         # project, publication, resource
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)


# ============ API 请求/响应模型 ============

class CreateTeamRequest(BaseModel):
    """创建团队请求"""
    name: str
    description: Optional[str] = None
    institution: Optional[str] = None
    research_fields: List[str] = []
    is_public: bool = False
    join_type: str = "invite"


class UpdateTeamRequest(BaseModel):
    """更新团队请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    institution: Optional[str] = None
    research_fields: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    is_public: Optional[bool] = None
    join_type: Optional[str] = None
    max_members: Optional[int] = None


class InviteMemberRequest(BaseModel):
    """邀请成员请求"""
    email: str
    role: TeamRole = TeamRole.MEMBER
    message: Optional[str] = None


class UpdateMemberRoleRequest(BaseModel):
    """更新成员角色请求"""
    user_id: str
    role: TeamRole


class CreateProjectRequest(BaseModel):
    """创建项目请求"""
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    leader_id: Optional[str] = None


class TeamSearchRequest(BaseModel):
    """团队搜索请求"""
    query: Optional[str] = None
    institution: Optional[str] = None
    research_field: Optional[str] = None
    is_public: Optional[bool] = None
    page: int = 1
    page_size: int = 20


class TeamSearchResponse(BaseModel):
    """团队搜索响应"""
    teams: List[ResearchTeam]
    total: int
    page: int
    page_size: int


class TeamDetailResponse(BaseModel):
    """团队详情响应"""
    team: ResearchTeam
    is_member: bool = False
    is_owner: bool = False
    member_count: int = 0
    can_manage: bool = False
