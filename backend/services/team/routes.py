"""
Team Management API Routes V2
团队管理API路由V2 - 层级权限、年费订阅、团队空间
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from .service import get_team_service_v2, TeamTier, TeamRole

router = APIRouter(prefix="/teams-v2", tags=["team-v2"])


# ==================== 请求/响应模型 ====================

class CreateTeamRequest(BaseModel):
    """创建团队请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    institution: Optional[str] = Field(None)
    department: Optional[str] = Field(None)
    website: Optional[str] = Field(None)


class InviteMemberRequest(BaseModel):
    """邀请成员请求"""
    email: str = Field(...)
    role: str = Field("member", description="owner/admin/advisor/senior/member/guest")


class UpdateRoleRequest(BaseModel):
    """更新角色请求"""
    role: str = Field(..., description="owner/admin/advisor/senior/member/guest")


class CreateAnnouncementRequest(BaseModel):
    """创建公告请求"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    visible_to_roles: Optional[List[str]] = Field(None)
    is_pinned: bool = Field(False)


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== 团队管理API ====================

@router.post("")
async def create_team(
    request: CreateTeamRequest,
    user_id: str = Depends(get_current_user)
):
    """创建团队"""
    service = get_team_service_v2()

    team = service.create_team(
        name=request.name,
        description=request.description,
        owner_id=user_id,
        institution=request.institution,
        department=request.department,
        website=request.website
    )

    return {
        "message": "Team created successfully",
        "team": {
            "id": team.id,
            "name": team.name,
            "status": team.status.value,
            "invite_code": f"TEAM{team.id[:6].upper()}"
        }
    }


@router.get("/my")
async def get_my_teams(user_id: str = Depends(get_current_user)):
    """获取我的团队"""
    service = get_team_service_v2()

    teams = []
    for team in service._teams.values():
        member = service.get_team_member(team.id, user_id)
        if member:
            teams.append({
                "team_id": team.id,
                "name": team.name,
                "role": member.role.value,
                "tier": team.tier.value,
                "member_count": team.member_count,
                "status": team.status.value
            })

    return {"teams": teams}


@router.get("/{team_id}")
async def get_team_detail(team_id: str):
    """获取团队详情"""
    service = get_team_service_v2()
    team = service.get_team(team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "tier": team.tier.value,
        "status": team.status.value,
        "is_verified": team.is_verified,
        "institution": team.institution,
        "department": team.department,
        "website": team.website,
        "logo_url": team.logo_url,
        "banner_url": team.banner_url,
        "subscription": {
            "plan": team.subscription_plan.value,
            "start": team.subscription_start.isoformat(),
            "end": team.subscription_end.isoformat() if team.subscription_end else None,
            "auto_renew": team.auto_renew
        },
        "limits": {
            "members": {"current": team.member_count, "max": team.max_members},
            "storage": {"used": team.storage_used_gb, "limit": team.storage_limit_gb}
        },
        "created_at": team.created_at.isoformat()
    }


@router.post("/{team_id}/upgrade")
async def upgrade_team_tier(
    team_id: str,
    tier: str,
    user_id: str = Depends(get_current_user)
):
    """升级团队等级"""
    service = get_team_service_v2()

    try:
        new_tier = TeamTier(tier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tier")

    team = service.upgrade_tier(team_id, new_tier, user_id)

    if not team:
        raise HTTPException(status_code=403, detail="No permission or team not found")

    return {
        "message": "Team upgraded successfully",
        "team_id": team.id,
        "new_tier": team.tier.value,
        "max_members": team.max_members,
        "storage_limit": team.storage_limit_gb
    }


@router.post("/{team_id}/renew")
async def renew_subscription(
    team_id: str,
    plan: str,
    user_id: str = Depends(get_current_user)
):
    """续订订阅"""
    service = get_team_service_v2()

    try:
        sub_plan = SubscriptionPlan(plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan")

    team = service.renew_subscription(team_id, sub_plan, user_id)

    if not team:
        raise HTTPException(status_code=403, detail="No permission or team not found")

    return {
        "message": "Subscription renewed successfully",
        "team_id": team.id,
        "new_end_date": team.subscription_end.isoformat() if team.subscription_end else None
    }


# ==================== 成员管理API ====================

@router.get("/{team_id}/members")
async def get_team_members(team_id: str):
    """获取团队成员"""
    service = get_team_service_v2()
    members = service.get_team_members(team_id)

    return {
        "members": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "role": m.role.value,
                "display_name": m.display_name,
                "title": m.title,
                "research_area": m.research_area,
                "joined_at": m.joined_at.isoformat(),
                "is_active": m.is_active
            }
            for m in members
        ]
    }


@router.post("/{team_id}/invite")
async def invite_member(
    team_id: str,
    request: InviteMemberRequest,
    user_id: str = Depends(get_current_user)
):
    """邀请成员"""
    service = get_team_service_v2()

    try:
        role = TeamRole(request.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    result = service.invite_member(team_id, request.email, role, user_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/{team_id}/members/{member_user_id}/role")
async def update_member_role(
    team_id: str,
    member_user_id: str,
    request: UpdateRoleRequest,
    user_id: str = Depends(get_current_user)
):
    """更新成员角色"""
    service = get_team_service_v2()

    try:
        new_role = TeamRole(request.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    member = service.update_member_role(team_id, member_user_id, new_role, user_id)

    if not member:
        raise HTTPException(status_code=403, detail="No permission or member not found")

    return {
        "message": "Role updated successfully",
        "user_id": member_user_id,
        "new_role": member.role.value
    }


@router.delete("/{team_id}/members/{member_user_id}")
async def remove_member(
    team_id: str,
    member_user_id: str,
    user_id: str = Depends(get_current_user)
):
    """移除成员"""
    service = get_team_service_v2()

    success = service.remove_member(team_id, member_user_id, user_id)

    if not success:
        raise HTTPException(status_code=403, detail="No permission or cannot remove this member")

    return {"message": "Member removed successfully"}


# ==================== 权限检查API ====================

@router.get("/{team_id}/permissions")
async def get_my_permissions(
    team_id: str,
    user_id: str = Depends(get_current_user)
):
    """获取我的权限"""
    service = get_team_service_v2()

    member = service.get_team_member(team_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Not a team member")

    from .models import ROLE_PERMISSIONS
    permissions = ROLE_PERMISSIONS.get(member.role, {})

    return {
        "user_id": user_id,
        "role": member.role.value,
        "permissions": permissions
    }


@router.get("/{team_id}/check-permission")
async def check_permission(
    team_id: str,
    permission: str,
    user_id: str = Depends(get_current_user)
):
    """检查特定权限"""
    service = get_team_service_v2()

    has_perm = service.has_permission(team_id, user_id, permission)

    return {
        "user_id": user_id,
        "permission": permission,
        "has_permission": has_perm
    }


# ==================== 团队空间API ====================

@router.get("/{team_id}/spaces")
async def get_team_spaces(team_id: str):
    """获取团队空间"""
    service = get_team_service_v2()
    spaces = service.get_team_spaces(team_id)

    return {
        "spaces": [
            {
                "id": s.id,
                "type": s.space_type,
                "name": s.name,
                "description": s.description,
                "is_public": s.is_public
            }
            for s in spaces
        ]
    }


@router.get("/spaces/{space_id}/access")
async def check_space_access(
    space_id: str,
    user_id: str = Depends(get_current_user)
):
    """检查空间访问权限"""
    service = get_team_service_v2()

    can_access = service.can_access_space(space_id, user_id)

    return {
        "space_id": space_id,
        "user_id": user_id,
        "can_access": can_access
    }


# ==================== 公告API ====================

@router.get("/{team_id}/announcements")
async def get_announcements(
    team_id: str,
    user_id: str = Depends(get_current_user)
):
    """获取公告"""
    service = get_team_service_v2()
    announcements = service.get_announcements(team_id, user_id)

    return {
        "announcements": [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "author_id": a.author_id,
                "is_pinned": a.is_pinned,
                "created_at": a.created_at.isoformat()
            }
            for a in announcements
        ]
    }


@router.post("/{team_id}/announcements")
async def create_announcement(
    team_id: str,
    request: CreateAnnouncementRequest,
    user_id: str = Depends(get_current_user)
):
    """创建公告"""
    service = get_team_service_v2()

    announcement = service.create_announcement(
        team_id=team_id,
        author_id=user_id,
        title=request.title,
        content=request.content,
        visible_to_roles=request.visible_to_roles,
        is_pinned=request.is_pinned
    )

    if not announcement:
        raise HTTPException(status_code=403, detail="No permission to create announcement")

    return {
        "message": "Announcement created",
        "announcement_id": announcement.id
    }


# ==================== 活动记录API ====================

@router.get("/{team_id}/activities")
async def get_team_activities(
    team_id: str,
    limit: int = 20
):
    """获取团队活动"""
    service = get_team_service_v2()
    activities = service.get_team_activities(team_id, limit)

    return {
        "activities": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "action": a.action,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "details": a.details,
                "created_at": a.created_at.isoformat()
            }
            for a in activities
        ]
    }


# ==================== 团队等级信息API ====================

@router.get("/tiers/info")
async def get_tier_info():
    """获取团队等级信息"""
    from .models import TEAM_TIER_CONFIG

    return {
        "tiers": [
            {
                "id": tier.value,
                "name": config["name"],
                "max_members": config["max_members"],
                "storage_gb": config["storage_gb"],
                "yearly_price_cny": config["yearly_price"],
                "features": config["features"]
            }
            for tier, config in TEAM_TIER_CONFIG.items()
        ]
    }


@router.get("/roles/info")
async def get_role_info():
    """获取角色信息"""
    from .models import ROLE_PERMISSIONS

    return {
        "roles": [
            {
                "id": role.value,
                "description": perms["description"],
                "permissions": {k: v for k, v in perms.items() if k != "description"}
            }
            for role, perms in ROLE_PERMISSIONS.items()
        ]
    }
