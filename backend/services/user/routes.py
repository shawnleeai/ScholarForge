"""
用户服务 API 路由
FastAPI 路由定义
"""

import uuid
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.exceptions import ConflictException, NotFoundException, UnauthorizedException
from shared.responses import success_response, paginated_response
from shared.config import settings
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams
from shared.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    revoke_token,
)

from .schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserBrief,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChange,
    UserProfile,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamMemberAdd,
    TeamMemberResponse,
)
from .repository import UserRepository, TeamRepository

router = APIRouter(prefix="/api/v1", tags=["用户认证"])


# ============== 认证路由 ==============

@router.post("/auth/register", summary="用户注册")
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """用户注册"""
    user_repo = UserRepository(db)

    # 检查邮箱是否已存在
    if await user_repo.exists_by_email(user_data.email):
        raise ConflictException("该邮箱已被注册")

    # 检查用户名是否已存在
    if await user_repo.exists_by_username(user_data.username):
        raise ConflictException("该用户名已被使用")

    # 创建用户
    user = await user_repo.create(user_data)
    await db.commit()

    # 生成令牌
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return success_response(
        data={
            "user": UserResponse.model_validate(user).model_dump(),
            "token": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": settings.jwt_expire_hours * 3600,
            },
        },
        message="注册成功",
        code=201,
    )


@router.post("/auth/login", summary="用户登录")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录

    Token 会同时通过以下两种方式返回：
    1. 响应体中（向后兼容）
    2. httpOnly Cookie（推荐，更安全）
    """
    import json
    from fastapi.responses import JSONResponse

    user_repo = UserRepository(db)

    # 验证用户
    user = await user_repo.authenticate(login_data.email, login_data.password)
    if not user:
        raise UnauthorizedException("邮箱或密码错误")

    # 更新最后登录时间
    await user_repo.update_last_login(user.id)
    await db.commit()

    # 生成令牌
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    # 构建响应数据（确保 UUID 转换为字符串）
    user_data = UserResponse.model_validate(user).model_dump()
    # 将 UUID 转换为字符串
    if 'id' in user_data and hasattr(user_data['id'], 'hex'):
        user_data['id'] = str(user_data['id'])

    response_data = {
        "code": 200,
        "message": "登录成功",
        "data": {
            "user": user_data,
            "token": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": settings.jwt_expire_hours * 3600,
            },
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # 创建 JSONResponse 并设置 Cookie
    response = JSONResponse(content=response_data)

    # 设置 httpOnly Cookie（更安全）
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.debug,  # 生产环境使用 HTTPS
        samesite="lax",
        max_age=settings.jwt_expire_hours * 3600,
        path="/",
    )

    # Refresh Token Cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.jwt_refresh_expire_days * 24 * 3600,
        path="/api/v1/auth",  # 仅用于刷新令牌的路径
    )

    return response


@router.post("/auth/refresh", summary="刷新令牌")
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """刷新访问令牌"""
    # 验证刷新令牌
    user_id = verify_token(token_data.refresh_token, token_type="refresh")
    if not user_id:
        raise UnauthorizedException("无效的刷新令牌")

    # 检查用户是否存在
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(uuid.UUID(user_id))
    if not user or not user.is_active:
        raise UnauthorizedException("用户不存在或已禁用")

    # 生成新令牌
    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.jwt_expire_hours * 3600,
        },
        message="令牌刷新成功",
    )


@router.post("/auth/logout", summary="用户登出")
async def logout(
    request: Request,
    response: Response,
    user_id: str = Depends(get_current_user_id),
):
    """
    用户登出

    - 将当前 Token 添加到黑名单
    - 清除 httpOnly Cookie
    """
    # 从请求头获取 Token 并添加到黑名单
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        revoke_token(token)

    # 清除 Cookie
    response.delete_cookie(
        key="access_token",
        path="/",
    )
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )

    return success_response(message="登出成功")


# ============== 用户路由 ==============

@router.get("/users/me", summary="获取当前用户信息")
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户信息"""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(uuid.UUID(user_id))

    if not user:
        raise NotFoundException("用户")

    return success_response(data=UserResponse.model_validate(user).model_dump())


@router.put("/users/me", summary="更新用户信息")
async def update_current_user(
    user_data: UserUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户信息"""
    user_repo = UserRepository(db)
    user = await user_repo.update(uuid.UUID(user_id), user_data)

    if not user:
        raise NotFoundException("用户")

    await db.commit()
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="更新成功",
    )


@router.post("/users/me/change-password", summary="修改密码")
async def change_password(
    password_data: PasswordChange,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    user_repo = UserRepository(db)
    success = await user_repo.change_password(
        uuid.UUID(user_id),
        password_data.old_password,
        password_data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )

    await db.commit()
    return success_response(message="密码修改成功")


@router.get("/users/me/profile", summary="获取用户画像")
async def get_user_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户画像（用于推荐系统）"""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(uuid.UUID(user_id))

    if not user:
        raise NotFoundException("用户")

    profile = UserProfile(
        id=user.id,
        major=user.major,
        university=user.university,
        research_interests=user.research_interests or [],
        preferences=user.preferences,
        paper_count=len(user.papers) if user.papers else 0,
        library_count=getattr(user, 'library_count', 0) or 0,  # 可通过文献服务API获取
        collaboration_count=getattr(user, 'collaboration_count', 0) or 0,  # 可通过协作服务API获取
    )

    return success_response(data=profile.model_dump())


@router.get("/users/search", summary="搜索用户")
async def search_users(
    q: str,
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """搜索用户"""
    user_repo = UserRepository(db)
    users, total = await user_repo.search(
        query=q,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    return paginated_response(
        items=[UserBrief.model_validate(u).model_dump() for u in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


# ============== 团队路由 ==============

team_router = APIRouter(prefix="/api/v1/teams", tags=["团队管理"])


@team_router.post("", summary="创建团队")
async def create_team(
    team_data: TeamCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建团队"""
    team_repo = TeamRepository(db)
    team = await team_repo.create(uuid.UUID(user_id), team_data)
    await db.commit()

    return success_response(
        data=TeamResponse(
            **team.__dict__,
            member_count=1,
        ).model_dump(),
        message="团队创建成功",
        code=201,
    )


@team_router.get("", summary="获取我的团队列表")
async def get_my_teams(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户所属团队列表"""
    team_repo = TeamRepository(db)
    teams = await team_repo.get_user_teams(uuid.UUID(user_id))

    return success_response(
        data=[
            TeamResponse(
                **team.__dict__,
                member_count=len(team.members),
            ).model_dump()
            for team in teams
        ]
    )


@team_router.get("/{team_id}", summary="获取团队详情")
async def get_team(
    team_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取团队详情"""
    team_repo = TeamRepository(db)
    team = await team_repo.get_by_id(team_id)

    if not team:
        raise NotFoundException("团队")

    # 检查权限
    if not await team_repo.is_member(team_id, uuid.UUID(user_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该团队成员",
        )

    return success_response(
        data=TeamResponse(
            **team.__dict__,
            member_count=len(team.members),
        ).model_dump()
    )


@team_router.post("/{team_id}/members", summary="添加团队成员")
async def add_team_member(
    team_id: uuid.UUID,
    member_data: TeamMemberAdd,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """添加团队成员"""
    team_repo = TeamRepository(db)
    user_repo = UserRepository(db)

    # 检查权限（只有owner和admin可以添加成员）
    role = await team_repo.get_member_role(team_id, uuid.UUID(user_id))
    if not role or role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限添加成员",
        )

    # 查找要添加的用户
    new_member = await user_repo.get_by_email(member_data.user_email)
    if not new_member:
        raise NotFoundException("用户")

    # 检查是否已是成员
    if await team_repo.is_member(team_id, new_member.id):
        raise ConflictException("该用户已是团队成员")

    # 添加成员
    await team_repo.add_member(team_id, new_member.id, member_data.role)
    await db.commit()

    return success_response(message="成员添加成功")


@team_router.delete("/{team_id}/members/{member_user_id}", summary="移除团队成员")
async def remove_team_member(
    team_id: uuid.UUID,
    member_user_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """移除团队成员"""
    team_repo = TeamRepository(db)

    # 检查权限
    role = await team_repo.get_member_role(team_id, uuid.UUID(user_id))
    if not role or role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限移除成员",
        )

    success = await team_repo.remove_member(team_id, member_user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法移除该成员",
        )

    await db.commit()
    return success_response(message="成员移除成功")
