"""
Permission API Routes
权限管理API路由
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.shared.database import get_db
from backend.services.user.auth import get_current_user
from backend.services.user.models import User

from .models import Role, Permission
from .service import PermissionService, require_permission


router = APIRouter(prefix="/permissions", tags=["permissions"])


# ==================== 角色管理 ====================

@router.get("/roles", response_model=dict)
async def list_roles(
    include_system: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色列表"""
    service = PermissionService(db)
    roles = await service.list_roles(include_system=include_system)

    return {
        'items': [
            {
                'id': str(role.id),
                'name': role.name,
                'description': role.description,
                'is_system': role.is_system,
                'is_active': role.is_active,
                'permissions_count': len(role.permissions),
                'users_count': len(role.users),
                'created_at': role.created_at.isoformat() if role.created_at else None
            }
            for role in roles
        ],
        'total': len(roles)
    }


@router.post("/roles", response_model=dict, status_code=status.HTTP_201_CREATED)
@require_permission("system", "configure")
async def create_role(
    name: str,
    description: str = None,
    permission_codes: List[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新角色"""
    service = PermissionService(db)
    role = await service.create_role(
        name=name,
        description=description,
        permission_codes=permission_codes,
        is_system=False
    )

    return {
        'id': str(role.id),
        'name': role.name,
        'description': role.description,
        'is_system': role.is_system,
        'permissions': [f"{p.resource}:{p.action}" for p in role.permissions]
    }


@router.get("/roles/{role_id}", response_model=dict)
async def get_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色详情"""
    service = PermissionService(db)
    role = await service.get_role(role_id)

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return {
        'id': str(role.id),
        'name': role.name,
        'description': role.description,
        'is_system': role.is_system,
        'is_active': role.is_active,
        'permissions': [
            {
                'id': str(p.id),
                'resource': p.resource,
                'action': p.action,
                'description': p.description
            }
            for p in role.permissions
        ],
        'users': [
            {
                'id': str(u.id),
                'email': u.email,
                'name': u.name
            }
            for u in role.users
        ],
        'created_at': role.created_at.isoformat() if role.created_at else None,
        'updated_at': role.updated_at.isoformat() if role.updated_at else None
    }


@router.put("/roles/{role_id}", response_model=dict)
@require_permission("system", "configure")
async def update_role(
    role_id: UUID,
    description: str = None,
    permission_codes: List[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新角色"""
    service = PermissionService(db)
    role = await service.update_role(
        role_id=role_id,
        description=description,
        permission_codes=permission_codes
    )

    return {
        'id': str(role.id),
        'name': role.name,
        'description': role.description,
        'permissions': [f"{p.resource}:{p.action}" for p in role.permissions]
    }


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("system", "configure")
async def delete_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除角色"""
    service = PermissionService(db)
    success = await service.delete_role(role_id)

    if not success:
        raise HTTPException(status_code=404, detail="Role not found")


# ==================== 权限管理 ====================

@router.get("/permissions", response_model=dict)
async def list_permissions(
    resource: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限列表"""
    service = PermissionService(db)
    permissions = await service.list_permissions(resource=resource)

    # 按资源分组
    grouped = {}
    for perm in permissions:
        if perm.resource not in grouped:
            grouped[perm.resource] = []
        grouped[perm.resource].append({
            'id': str(perm.id),
            'resource': perm.resource,
            'action': perm.action,
            'code': perm.code,
            'description': perm.description
        })

    return {
        'grouped': grouped,
        'items': [
            {
                'id': str(perm.id),
                'resource': perm.resource,
                'action': perm.action,
                'code': perm.code,
                'description': perm.description
            }
            for perm in permissions
        ],
        'total': len(permissions)
    }


@router.post("/permissions", response_model=dict, status_code=status.HTTP_201_CREATED)
@require_permission("system", "configure")
async def create_permission(
    resource: str,
    action: str,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新权限"""
    service = PermissionService(db)
    permission = await service.create_permission(
        resource=resource,
        action=action,
        description=description
    )

    return {
        'id': str(permission.id),
        'resource': permission.resource,
        'action': permission.action,
        'code': permission.code,
        'description': permission.description
    }


# ==================== 用户角色管理 ====================

@router.get("/users/{user_id}/roles", response_model=dict)
async def get_user_roles(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的角色"""
    # 只能查看自己的角色，或者有管理权限
    if current_user.id != user_id:
        service = PermissionService(db)
        has_perm = await service.check_permission(
            current_user.id, "user", "manage"
        )
        if not has_perm:
            raise HTTPException(status_code=403, detail="Permission denied")

    service = PermissionService(db)
    roles = await service.get_user_roles(user_id)

    return {
        'user_id': str(user_id),
        'roles': [
            {
                'id': str(role.id),
                'name': role.name,
                'description': role.description,
                'is_system': role.is_system
            }
            for role in roles
        ]
    }


@router.post("/users/{user_id}/roles", response_model=dict)
@require_permission("user", "manage")
async def assign_role_to_user(
    user_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为用户分配角色"""
    service = PermissionService(db)
    success = await service.assign_role_to_user(user_id, role_id)

    return {'success': success}


@router.delete("/users/{user_id}/roles/{role_id}", response_model=dict)
@require_permission("user", "manage")
async def remove_role_from_user(
    user_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除用户的角色"""
    service = PermissionService(db)
    success = await service.remove_role_from_user(user_id, role_id)

    return {'success': success}


# ==================== 权限检查 ====================

@router.get("/users/{user_id}/permissions", response_model=dict)
async def get_user_permissions(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的所有权限代码"""
    # 只能查看自己的权限，或者有管理权限
    if current_user.id != user_id:
        service = PermissionService(db)
        has_perm = await service.check_permission(
            current_user.id, "user", "manage"
        )
        if not has_perm:
            raise HTTPException(status_code=403, detail="Permission denied")

    service = PermissionService(db)
    permissions = await service.get_user_permissions(user_id)

    return {
        'user_id': str(user_id),
        'permissions': list(permissions)
    }


@router.post("/check", response_model=dict)
async def check_permission_endpoint(
    resource: str,
    action: str,
    resource_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查当前用户是否有指定权限"""
    service = PermissionService(db)
    has_permission = await service.check_permission(
        user_id=current_user.id,
        resource=resource,
        action=action,
        resource_id=resource_id
    )

    return {
        'user_id': str(current_user.id),
        'resource': resource,
        'action': action,
        'resource_id': str(resource_id) if resource_id else None,
        'has_permission': has_permission
    }


# ==================== 资源权限管理 ====================

@router.post("/resource-permissions", response_model=dict)
async def grant_resource_permission(
    user_id: UUID,
    resource_type: str,
    resource_id: UUID,
    permission: str,  # owner, collaborator, viewer
    expires_at: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """授予资源级权限"""
    from datetime import datetime

    service = PermissionService(db)

    # 检查当前用户是否有权限授予此资源的权限
    has_perm = await service.check_permission(
        current_user.id, resource_type, 'share', resource_id
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Permission denied")

    expires = None
    if expires_at:
        expires = datetime.fromisoformat(expires_at)

    resource_perm = await service.grant_resource_permission(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        permission=permission,
        granted_by=current_user.id,
        expires_at=expires
    )

    return {
        'id': str(resource_perm.id),
        'user_id': str(resource_perm.user_id),
        'resource_type': resource_perm.resource_type,
        'resource_id': str(resource_perm.resource_id),
        'permission': resource_perm.permission,
        'granted_by': str(resource_perm.granted_by),
        'granted_at': resource_perm.granted_at.isoformat() if resource_perm.granted_at else None,
        'expires_at': resource_perm.expires_at.isoformat() if resource_perm.expires_at else None
    }


@router.delete("/resource-permissions", response_model=dict)
async def revoke_resource_permission(
    user_id: UUID,
    resource_type: str,
    resource_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """撤销资源级权限"""
    service = PermissionService(db)

    # 检查权限
    has_perm = await service.check_permission(
        current_user.id, resource_type, 'share', resource_id
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Permission denied")

    success = await service.revoke_resource_permission(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id
    )

    return {'success': success}


# ==================== 系统初始化 ====================

@router.post("/init", response_model=dict)
async def init_system_roles_and_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """初始化系统角色和权限（仅超级管理员）"""
    service = PermissionService(db)

    # 检查是否是超级管理员
    roles = await service.get_user_roles(current_user.id)
    role_names = [r.name for r in roles]

    if Role.SUPER_ADMIN not in role_names:
        raise HTTPException(status_code=403, detail="Only super admin can initialize")

    await service.init_system_roles_and_permissions()

    return {'message': 'System roles and permissions initialized successfully'}

