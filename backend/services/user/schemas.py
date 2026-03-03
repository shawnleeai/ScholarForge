"""
用户数据模式
Pydantic 模型用于请求/响应验证
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============== 基础模式 ==============

class UserBase(BaseModel):
    """用户基础模式"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=200)


class UserCreate(BaseModel):
    """用户注册模式"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)

    # 学术信息（可选）
    university: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    major: Optional[str] = Field(None, max_length=200)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum() and "_" not in v:
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        # 可添加更多密码强度验证
        return v


class UserUpdate(BaseModel):
    """用户更新模式"""

    full_name: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=1000)
    university: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=200)
    major: Optional[str] = Field(None, max_length=200)
    research_interests: Optional[List[str]] = None
    orcid_id: Optional[str] = Field(None, max_length=50)
    preferences: Optional[dict] = None
    notification_settings: Optional[dict] = None
    avatar_url: Optional[str] = Field(None, max_length=500)


class UserResponse(BaseModel):
    """用户响应模式"""

    id: uuid.UUID
    email: str
    username: str
    role: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    university: Optional[str] = None
    department: Optional[str] = None
    major: Optional[str] = None
    research_interests: Optional[List[str]] = None
    orcid_id: Optional[str] = None
    subscription_tier: str = "free"
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    """用户简要信息（用于列表展示）"""

    id: uuid.UUID
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    university: Optional[str] = None

    model_config = {"from_attributes": True}


# ============== 认证模式 ==============

class LoginRequest(BaseModel):
    """登录请求模式"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """令牌响应模式"""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # 秒


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str


class PasswordChange(BaseModel):
    """修改密码"""

    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        return v


# ============== 团队模式 ==============

class TeamCreate(BaseModel):
    """创建团队"""

    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    """更新团队"""

    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    avatar_url: Optional[str] = None


class TeamMemberAdd(BaseModel):
    """添加团队成员"""

    user_email: EmailStr
    role: str = Field(default="member")  # owner, admin, member


class TeamResponse(BaseModel):
    """团队响应"""

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    plan_type: str
    max_members: int
    owner_id: uuid.UUID
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}


class TeamMemberResponse(BaseModel):
    """团队成员响应"""

    id: uuid.UUID
    user: UserBrief
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


# ============== 用户画像模式 ==============

class UserProfile(BaseModel):
    """用户画像（用于推荐系统）"""

    id: uuid.UUID
    major: Optional[str] = None
    university: Optional[str] = None
    research_interests: Optional[List[str]] = None
    preferences: dict = {}

    # 统计信息
    paper_count: int = 0
    library_count: int = 0
    collaboration_count: int = 0

    model_config = {"from_attributes": True}
