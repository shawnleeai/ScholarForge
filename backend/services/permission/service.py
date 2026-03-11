"""
Permission Service
权限服务核心逻辑
"""

from typing import Optional, List, Set
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from functools import wraps
import inspect

from .models import (
    Role, Permission, ResourcePermission, PermissionAuditLog,
    role_permissions, user_roles
)
from backend.services.user.models import User
from backend.shared.database import get_db


class PermissionService:
    """权限服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 角色管理 ====================

    async def create_role(
        self,
        name: str,
        description: str = None,
        permission_codes: List[str] = None,
        is_system: bool = False
    ) -> Role:
        """创建角色"""
        # 检查是否已存在
        existing = self.db.query(Role).filter(Role.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Role {name} already exists")

        role = Role(
            name=name,
            description=description,
            is_system=is_system
        )

        # 关联权限
        if permission_codes:
            permissions = self.db.query(Permission).filter(
                Permission.resource.in_([p.split(':')[0] for p in permission_codes]),
                Permission.action.in_([p.split(':')[1] for p in permission_codes])
            ).all()
            role.permissions = permissions

        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    async def get_role(self, role_id: UUID) -> Optional[Role]:
        """获取角色"""
        return self.db.query(Role).filter(Role.id == role_id).first()

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """通过名称获取角色"""
        return self.db.query(Role).filter(Role.name == name).first()

    async def list_roles(self, include_system: bool = True) -> List[Role]:
        """列出所有角色"""
        query = self.db.query(Role)
        if not include_system:
            query = query.filter(Role.is_system == False)
        return query.all()

    async def update_role(
        self,
        role_id: UUID,
        description: str = None,
        permission_codes: List[str] = None
    ) -> Role:
        """更新角色"""
        role = await self.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        if role.is_system:
            raise HTTPException(status_code=403, detail="Cannot modify system role")

        if description:
            role.description = description

        if permission_codes is not None:
            permissions = self.db.query(Permission).filter(
                Permission.resource.in_([p.split(':')[0] for p in permission_codes]),
                Permission.action.in_([p.split(':')[1] for p in permission_codes])
            ).all()
            role.permissions = permissions

        self.db.commit()
        self.db.refresh(role)
        return role

    async def delete_role(self, role_id: UUID) -> bool:
        """删除角色"""
        role = await self.get_role(role_id)
        if not role:
            return False

        if role.is_system:
            raise HTTPException(status_code=403, detail="Cannot delete system role")

        self.db.delete(role)
        self.db.commit()
        return True

    # ==================== 权限管理 ====================

    async def create_permission(
        self,
        resource: str,
        action: str,
        description: str = None,
        conditions: dict = None
    ) -> Permission:
        """创建权限"""
        existing = self.db.query(Permission).filter(
            Permission.resource == resource,
            Permission.action == action
        ).first()

        if existing:
            return existing

        permission = Permission(
            resource=resource,
            action=action,
            description=description,
            conditions=conditions or {}
        )
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission

    async def get_permission(self, resource: str, action: str) -> Optional[Permission]:
        """获取权限"""
        return self.db.query(Permission).filter(
            Permission.resource == resource,
            Permission.action == action
        ).first()

    async def list_permissions(self, resource: str = None) -> List[Permission]:
        """列出权限"""
        query = self.db.query(Permission)
        if resource:
            query = query.filter(Permission.resource == resource)
        return query.all()

    # ==================== 用户角色管理 ====================

    async def assign_role_to_user(self, user_id: UUID, role_id: UUID) -> bool:
        """为用户分配角色"""
        user = self.db.query(User).filter(User.id == user_id).first()
        role = await self.get_role(role_id)

        if not user or not role:
            raise HTTPException(status_code=404, detail="User or role not found")

        if role not in user.roles:
            user.roles.append(role)
            self.db.commit()

        return True

    async def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        """移除用户角色"""
        user = self.db.query(User).filter(User.id == user_id).first()
        role = await self.get_role(role_id)

        if not user or not role:
            return False

        if role in user.roles:
            user.roles.remove(role)
            self.db.commit()

        return True

    async def get_user_roles(self, user_id: UUID) -> List[Role]:
        """获取用户所有角色"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        return user.roles

    async def get_user_permissions(self, user_id: UUID) -> Set[str]:
        """获取用户的所有权限代码"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return set()

        permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                permissions.add(f"{perm.resource}:{perm.action}")

        return permissions

    # ==================== 权限检查 ====================

    async def check_permission(
        self,
        user_id: UUID,
        resource: str,
        action: str,
        resource_id: UUID = None,
        **context
    ) -> bool:
        """
        检查用户权限

        检查顺序：
        1. 超级管理员直接通过
        2. 角色权限检查
        3. 资源级权限检查
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 1. 检查是否是超级管理员
        user_roles = await self.get_user_roles(user_id)
        role_names = [r.name for r in user_roles]

        if Role.SUPER_ADMIN in role_names:
            await self._log_permission_check(user_id, resource, action, resource_id, True, context)
            return True

        # 2. 检查角色权限
        required_perm = f"{resource}:{action}"
        user_permissions = await self.get_user_permissions(user_id)

        if required_perm in user_permissions:
            await self._log_permission_check(user_id, resource, action, resource_id, True, context)
            return True

        # 3. 检查资源级权限
        if resource_id:
            has_resource_perm = await self.check_resource_permission(
                user_id, resource, resource_id, action
            )
            if has_resource_perm:
                await self._log_permission_check(user_id, resource, action, resource_id, True, context)
                return True

        await self._log_permission_check(user_id, resource, action, resource_id, False, context)
        return False

    async def check_resource_permission(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action: str
    ) -> bool:
        """检查资源级权限"""
        # 查询资源权限记录
        resource_perm = self.db.query(ResourcePermission).filter(
            ResourcePermission.user_id == user_id,
            ResourcePermission.resource_type == resource_type,
            ResourcePermission.resource_id == resource_id
        ).first()

        if not resource_perm:
            return False

        # 检查是否过期
        if resource_perm.expires_at and resource_perm.expires_at < datetime.utcnow():
            return False

        # 权限映射
        permission_map = {
            'owner': ['create', 'read', 'update', 'delete', 'share', 'comment'],
            'collaborator': ['read', 'update', 'comment'],
            'viewer': ['read', 'comment']
        }

        allowed_actions = permission_map.get(resource_perm.permission, [])
        return action in allowed_actions

    async def grant_resource_permission(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        permission: str,
        granted_by: UUID,
        expires_at: datetime = None
    ) -> ResourcePermission:
        """授予资源级权限"""
        # 检查是否已有权限
        existing = self.db.query(ResourcePermission).filter(
            ResourcePermission.user_id == user_id,
            ResourcePermission.resource_type == resource_type,
            ResourcePermission.resource_id == resource_id
        ).first()

        if existing:
            existing.permission = permission
            existing.granted_by = granted_by
            existing.expires_at = expires_at
            self.db.commit()
            return existing

        resource_perm = ResourcePermission(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=permission,
            granted_by=granted_by,
            expires_at=expires_at
        )
        self.db.add(resource_perm)
        self.db.commit()
        self.db.refresh(resource_perm)
        return resource_perm

    async def revoke_resource_permission(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID
    ) -> bool:
        """撤销资源级权限"""
        resource_perm = self.db.query(ResourcePermission).filter(
            ResourcePermission.user_id == user_id,
            ResourcePermission.resource_type == resource_type,
            ResourcePermission.resource_id == resource_id
        ).first()

        if resource_perm:
            self.db.delete(resource_perm)
            self.db.commit()
            return True
        return False

    # ==================== 审计日志 ====================

    async def _log_permission_check(
        self,
        user_id: UUID,
        resource: str,
        action: str,
        resource_id: UUID,
        result: bool,
        context: dict
    ):
        """记录权限检查日志"""
        log = PermissionAuditLog(
            user_id=user_id,
            action='check',
            resource_type=resource,
            resource_id=resource_id,
            permission=f"{resource}:{action}",
            result=result,
            context=context
        )
        self.db.add(log)
        self.db.commit()

    # ==================== 初始化 ====================

    async def init_system_roles_and_permissions(self):
        """初始化系统角色和权限"""
        # 创建所有权限
        all_permissions = []
        for code, desc in Permission.PERMISSIONS.items():
            resource, action = code.split(':')
            perm = await self.create_permission(resource, action, desc)
            all_permissions.append(perm)

        # 创建系统角色并分配权限
        role_permissions_map = {
            Role.SUPER_ADMIN: list(Permission.PERMISSIONS.keys()),
            Role.INSTITUTION_ADMIN: [
                'team:create', 'team:manage', 'team:invite',
                'user:manage', 'system:monitor'
            ],
            Role.ADVISOR: [
                'paper:read', 'paper:comment', 'paper:share',
                'ai:use', 'ai:advanced'
            ],
            Role.STUDENT: [
                'paper:create', 'paper:read', 'paper:update', 'paper:delete',
                'paper:share', 'paper:export', 'paper:submit',
                'ai:use', 'dataset:upload'
            ],
            Role.REVIEWER: [
                'paper:read', 'paper:comment'
            ],
            Role.GUEST: [
                'paper:read'
            ]
        }

        for role_name, perm_codes in role_permissions_map.items():
            role = await self.create_role(
                name=role_name,
                description=Role.SYSTEM_ROLES.get(role_name),
                permission_codes=perm_codes,
                is_system=True
            )

        print("System roles and permissions initialized")


# ==================== 装饰器 ====================

def require_permission(resource: str, action: str):
    """
    权限检查装饰器

    用法:
        @app.post("/papers")
        @require_permission("paper", "create")
        async def create_paper(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取 current_user 和 db
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')

            if not current_user or not db:
                # 尝试从参数中解析
                for arg in args:
                    if hasattr(arg, 'id') and hasattr(arg, 'email'):
                        current_user = arg
                    elif isinstance(arg, Session):
                        db = arg

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            # 检查权限
            permission_service = PermissionService(db)

            # 从路径参数或查询参数获取 resource_id
            resource_id = kwargs.get('paper_id') or kwargs.get('resource_id')

            has_permission = await permission_service.check_permission(
                user_id=current_user.id,
                resource=resource,
                action=action,
                resource_id=resource_id
            )

            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {resource}:{action}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 便捷装饰器
def require_login(func):
    """要求登录装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if not current_user:
            raise HTTPException(status_code=401, detail="Login required")
        return await func(*args, **kwargs)
    return wrapper
