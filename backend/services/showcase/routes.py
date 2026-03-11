"""
Research Showcase API Routes
科研成果展示API路由
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from pydantic import BaseModel, Field

from .service import get_showcase_service, ShowcaseType, Visibility

router = APIRouter(prefix="/showcase", tags=["showcase"])


# ==================== 请求/响应模型 ====================

class CreateShowcaseRequest(BaseModel):
    """创建展示请求"""
    type: str = Field(..., description="类型: paper/project/dataset/code/patent/presentation")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    visibility: str = Field("public", description="public/team/private")
    tags: List[str] = Field(default_factory=list)
    team_id: Optional[str] = Field(None)
    paper_id: Optional[str] = Field(None)
    external_url: Optional[str] = Field(None)


class CreateTeamRequest(BaseModel):
    """创建团队请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    institution: Optional[str] = Field(None)
    department: Optional[str] = Field(None)
    location: Optional[str] = Field(None)
    website: Optional[str] = Field(None)
    email: Optional[str] = Field(None)


class UpdateProfileRequest(BaseModel):
    """更新主页请求"""
    display_name: Optional[str] = Field(None)
    bio: Optional[str] = Field(None)
    title: Optional[str] = Field(None)
    institution: Optional[str] = Field(None)
    department: Optional[str] = Field(None)
    research_interests: Optional[List[str]] = Field(None)
    skills: Optional[List[str]] = Field(None)


class CommentRequest(BaseModel):
    """评论请求"""
    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[str] = Field(None)


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== 展示项目API ====================

@router.post("/items")
async def create_showcase(
    request: CreateShowcaseRequest,
    user_id: str = Depends(get_current_user)
):
    """创建展示项目"""
    service = get_showcase_service()

    try:
        item_type = ShowcaseType(request.type)
        visibility = Visibility(request.visibility)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    item = service.create_showcase(
        item_type=item_type,
        title=request.title,
        description=request.description,
        owner_id=user_id,
        visibility=visibility,
        tags=request.tags,
        team_id=request.team_id,
        paper_id=request.paper_id,
        external_url=request.external_url
    )

    return {
        "message": "Showcase created successfully",
        "item": {
            "id": item.id,
            "type": item.type.value,
            "title": item.title,
            "created_at": item.created_at.isoformat()
        }
    }


@router.get("/items")
async def list_showcases(
    type: Optional[str] = None,
    owner_id: Optional[str] = None,
    team_id: Optional[str] = None,
    tags: Optional[str] = None,
    sort_by: str = "created",
    limit: int = 20
):
    """列出展示项目"""
    service = get_showcase_service()

    item_type = None
    if type:
        try:
            item_type = ShowcaseType(type)
        except ValueError:
            pass

    tag_list = tags.split(",") if tags else None

    items = service.list_showcases(
        item_type=item_type,
        owner_id=owner_id,
        team_id=team_id,
        tags=tag_list,
        sort_by=sort_by,
        limit=limit
    )

    return {
        "items": [
            {
                "id": item.id,
                "type": item.type.value,
                "title": item.title,
                "description": item.description[:200] + "..." if len(item.description) > 200 else item.description,
                "owner_id": item.owner_id,
                "tags": item.tags,
                "thumbnail_url": item.thumbnail_url,
                "stats": {
                    "views": item.view_count,
                    "likes": item.like_count,
                    "citations": item.citation_count
                },
                "created_at": item.created_at.isoformat()
            }
            for item in items
        ]
    }


@router.get("/items/{item_id}")
async def get_showcase_detail(item_id: str):
    """获取展示详情"""
    service = get_showcase_service()
    item = service.get_showcase(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Showcase not found")

    return {
        "id": item.id,
        "type": item.type.value,
        "title": item.title,
        "description": item.description,
        "owner_id": item.owner_id,
        "team_id": item.team_id,
        "visibility": item.visibility.value,
        "tags": item.tags,
        "categories": item.categories,
        "files": item.files,
        "external_url": item.external_url,
        "thumbnail_url": item.thumbnail_url,
        "stats": {
            "views": item.view_count,
            "likes": item.like_count,
            "downloads": item.download_count,
            "citations": item.citation_count
        },
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat()
    }


@router.post("/items/{item_id}/like")
async def like_showcase(item_id: str, user_id: str = Depends(get_current_user)):
    """点赞展示项目"""
    service = get_showcase_service()
    success = service.like_showcase(item_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Showcase not found")

    return {"message": "Liked successfully"}


# ==================== 团队主页API ====================

@router.post("/teams")
async def create_team(
    request: CreateTeamRequest,
    user_id: str = Depends(get_current_user)
):
    """创建团队主页"""
    service = get_showcase_service()

    team = service.create_team_profile(
        name=request.name,
        description=request.description,
        creator_id=user_id,
        institution=request.institution,
        department=request.department,
        location=request.location,
        website=request.website,
        email=request.email
    )

    return {
        "message": "Team profile created successfully",
        "team": {
            "id": team.id,
            "name": team.name,
            "member_count": len(team.members)
        }
    }


@router.get("/teams")
async def search_teams(
    query: Optional[str] = None,
    institution: Optional[str] = None,
    limit: int = 20
):
    """搜索团队"""
    service = get_showcase_service()
    teams = service.search_teams(query, institution, limit)

    return {
        "teams": [
            {
                "id": team.id,
                "name": team.name,
                "description": team.description[:150] + "..." if len(team.description) > 150 else team.description,
                "institution": team.institution,
                "member_count": len(team.members),
                "total_papers": team.total_papers,
                "total_citations": team.total_citations,
                "logo_url": team.logo_url
            }
            for team in teams
        ]
    }


@router.get("/teams/{team_id}")
async def get_team_detail(team_id: str):
    """获取团队详情"""
    service = get_showcase_service()
    team = service.get_team_profile(team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "institution": team.institution,
        "department": team.department,
        "location": team.location,
        "website": team.website,
        "email": team.email,
        "logo_url": team.logo_url,
        "banner_url": team.banner_url,
        "members": [
            {"user_id": uid, "is_admin": uid in team.admins}
            for uid in team.members
        ],
        "stats": {
            "total_papers": team.total_papers,
            "total_citations": team.total_citations,
            "h_index": team.h_index,
            "follower_count": len(team.followers)
        },
        "created_at": team.created_at.isoformat()
    }


@router.post("/teams/{team_id}/join")
async def join_team(team_id: str, user_id: str = Depends(get_current_user)):
    """加入团队"""
    service = get_showcase_service()
    success = service.join_team(team_id, user_id)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to join team")

    return {"message": "Joined team successfully"}


# ==================== 个人主页API ====================

@router.get("/profile/{user_id}")
async def get_researcher_profile(user_id: str):
    """获取研究者主页"""
    service = get_showcase_service()
    profile = service.get_researcher_profile(user_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "user_id": profile.user_id,
        "display_name": profile.display_name,
        "bio": profile.bio,
        "title": profile.title,
        "institution": profile.institution,
        "department": profile.department,
        "avatar_url": profile.avatar_url,
        "banner_url": profile.banner_url,
        "email": profile.email,
        "personal_website": profile.personal_website,
        "orcid": profile.orcid,
        "google_scholar": profile.google_scholar,
        "github": profile.github,
        "research_interests": profile.research_interests,
        "skills": profile.skills,
        "stats": {
            "total_papers": profile.total_papers,
            "total_citations": profile.total_citations,
            "h_index": profile.h_index,
            "i10_index": profile.i10_index,
            "follower_count": len(profile.followers),
            "following_count": len(profile.following)
        },
        "teams": profile.teams
    }


@router.put("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    user_id: str = Depends(get_current_user)
):
    """更新个人主页"""
    service = get_showcase_service()

    updates = {k: v for k, v in request.dict().items() if v is not None}
    profile = service.update_researcher_profile(user_id, **updates)

    if not profile:
        # 创建新主页
        profile = service.create_researcher_profile(
            user_id=user_id,
            display_name=request.display_name or user_id,
            **updates
        )

    return {"message": "Profile updated successfully", "user_id": user_id}


@router.post("/profile/{target_user_id}/follow")
async def follow_researcher(
    target_user_id: str,
    user_id: str = Depends(get_current_user)
):
    """关注研究者"""
    service = get_showcase_service()
    success = service.follow_researcher(user_id, target_user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Followed successfully"}


@router.get("/researchers/search")
async def search_researchers(
    query: Optional[str] = None,
    interests: Optional[str] = None,
    institution: Optional[str] = None,
    limit: int = 20
):
    """搜索研究者"""
    service = get_showcase_service()

    interest_list = interests.split(",") if interests else None
    profiles = service.search_researchers(query, interest_list, institution, limit)

    return {
        "researchers": [
            {
                "user_id": p.user_id,
                "display_name": p.display_name,
                "title": p.title,
                "institution": p.institution,
                "research_interests": p.research_interests[:3],  # 只显示前3个
                "avatar_url": p.avatar_url,
                "stats": {
                    "total_papers": p.total_papers,
                    "h_index": p.h_index
                }
            }
            for p in profiles
        ]
    }


# ==================== 评论API ====================

@router.post("/items/{item_id}/comments")
async def add_comment(
    item_id: str,
    request: CommentRequest,
    user_id: str = Depends(get_current_user)
):
    """添加评论"""
    service = get_showcase_service()
    comment = service.add_comment(item_id, user_id, request.content, request.parent_id)

    return {
        "message": "Comment added successfully",
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat()
        }
    }


@router.get("/items/{item_id}/comments")
async def get_comments(item_id: str):
    """获取评论列表"""
    service = get_showcase_service()
    comments = service.get_comments(item_id)

    return {
        "comments": [
            {
                "id": c.id,
                "author_id": c.author_id,
                "content": c.content,
                "parent_id": c.parent_id,
                "created_at": c.created_at.isoformat()
            }
            for c in comments
        ]
    }


# ==================== 排行榜API ====================

@router.get("/leaderboard")
async def get_leaderboard(metric: str = "citations", limit: int = 10):
    """获取排行榜"""
    service = get_showcase_service()
    leaderboard = service.get_leaderboard(metric, limit)

    return {
        "metric": metric,
        "items": leaderboard
    }
