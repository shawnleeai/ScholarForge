"""
RBAC Permission Models
基于角色的权限控制系统
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Table, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from backend.shared.database import Base

# 角色-权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE')),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id', ondelete='CASCADE'))
)

# 用户-角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE')),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'))
)

# 团队-用户关联表（带角色）
class TeamMember(Base):
    __tablename__ = 'team_members'

    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role = Column(String(50), nullable=False, default='member')  # admin, member, guest
    joined_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


class Role(Base):
    """角色模型"""
    __tablename__ = 'roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    is_system = Column(Boolean, default=False)  # 系统内置角色不可删除
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

    # 预定义角色常量
    SUPER_ADMIN = 'super_admin'
    INSTITUTION_ADMIN = 'institution_admin'
    ADVISOR = 'advisor'
    STUDENT = 'student'
    REVIEWER = 'reviewer'
    GUEST = 'guest'

    SYSTEM_ROLES = {
        SUPER_ADMIN: '超级管理员',
        INSTITUTION_ADMIN: '机构管理员',
        ADVISOR: '导师',
        STUDENT: '学生',
        REVIEWER: '审稿人',
        GUEST: '访客'
    }

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base):
    """权限模型"""
    __tablename__ = 'permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource = Column(String(50), nullable=False, index=True)  # paper, team, dataset, ai
    action = Column(String(50), nullable=False, index=True)    # create, read, update, delete, share, comment
    description = Column(Text)
    conditions = Column(JSONB, default={})  # 额外条件，如 {"owner_only": false}
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    # 权限组合常量
    PERMISSIONS = {
        # 论文权限
        'paper:create': '创建论文',
        'paper:read': '查看论文',
        'paper:update': '编辑论文',
        'paper:delete': '删除论文',
        'paper:share': '分享论文',
        'paper:comment': '评论论文',
        'paper:export': '导出论文',
        'paper:submit': '提交审稿',

        # 团队权限
        'team:create': '创建团队',
        'team:manage': '管理团队',
        'team:invite': '邀请成员',
        'team:remove': '移除成员',

        # AI 权限
        'ai:use': '使用AI功能',
        'ai:advanced': '使用高级AI功能',

        # 数据权限
        'dataset:upload': '上传数据集',
        'dataset:share': '分享数据集',

        # 系统权限
        'system:configure': '系统配置',
        'system:monitor': '系统监控',
        'user:manage': '用户管理'
    }

    @property
    def code(self):
        return f"{self.resource}:{self.action}"

    def __repr__(self):
        return f"<Permission {self.code}>"


class ResourcePermission(Base):
    """资源级权限（针对特定资源的权限）"""
    __tablename__ = 'resource_permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    resource_type = Column(String(50), nullable=False, index=True)  # paper, dataset
    resource_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    permission = Column(String(50), nullable=False)  # owner, collaborator, viewer
    granted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ResourcePermission {self.user_id}:{self.resource_type}:{self.permission}>"


class PermissionAuditLog(Base):
    """权限审计日志"""
    __tablename__ = 'permission_audit_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    action = Column(String(50), nullable=False)  # grant, revoke, check
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    permission = Column(String(100))
    result = Column(Boolean)  # 检查是否通过
    context = Column(JSONB, default={})  # 上下文信息
    ip_address = Column(String(50))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PermissionAuditLog {self.action}:{self.permission}>"
