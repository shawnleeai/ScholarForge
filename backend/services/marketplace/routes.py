"""
AI Tools Marketplace API Routes
AI科研工具商店API路由
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from .service import get_marketplace_service, ToolType, PricingType

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# ==================== 请求/响应模型 ====================

class CreateToolRequest(BaseModel):
    """创建工具请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    tool_type: str = Field(..., description="类型: plugin/script/template/workflow/dataset/model/extension")
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    pricing_type: str = Field("free", description="free/paid/subscription/freemium")
    price: float = Field(0.0)
    compatible_platforms: List[str] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    """评价请求"""
    rating: int = Field(..., ge=1, le=5)
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=10, max_length=2000)
    is_recommended: bool = Field(False)


class DeveloperProfileRequest(BaseModel):
    """开发者主页请求"""
    display_name: str = Field(..., min_length=1, max_length=50)
    bio: str = Field(default="")
    website: Optional[str] = Field(None)


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== 工具浏览API ====================

@router.get("/tools")
async def list_tools(
    tool_type: Optional[str] = None,
    category: Optional[str] = None,
    pricing: Optional[str] = None,
    sort_by: str = "popular",
    limit: int = 20
):
    """列出工具"""
    service = get_marketplace_service()

    tool_type_enum = None
    if tool_type:
        try:
            tool_type_enum = ToolType(tool_type)
        except ValueError:
            pass

    pricing_enum = None
    if pricing:
        try:
            pricing_enum = PricingType(pricing)
        except ValueError:
            pass

    tools = service.list_tools(
        tool_type=tool_type_enum,
        category=category,
        pricing=pricing_enum,
        sort_by=sort_by,
        limit=limit
    )

    return {
        "tools": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description[:100] + "..." if len(t.description) > 100 else t.description,
                "tool_type": t.tool_type.value,
                "pricing_type": t.pricing_type.value,
                "price": t.price,
                "currency": t.currency,
                "rating": round(t.rating, 1),
                "rating_count": t.rating_count,
                "download_count": t.download_count,
                "icon_url": t.icon_url,
                "categories": t.categories,
                "tags": t.tags,
                "version": t.version,
                "published_at": t.published_at.isoformat() if t.published_at else None
            }
            for t in tools
        ]
    }


@router.get("/tools/search")
async def search_tools(query: str, limit: int = 20):
    """搜索工具"""
    service = get_marketplace_service()
    tools = service.search_tools(query, limit)

    return {
        "query": query,
        "results": [
            {
                "id": t.id,
                "name": t.name,
                "tool_type": t.tool_type.value,
                "pricing_type": t.pricing_type.value,
                "price": t.price,
                "rating": round(t.rating, 1),
                "download_count": t.download_count,
                "icon_url": t.icon_url
            }
            for t in tools
        ]
    }


@router.get("/tools/{tool_id}")
async def get_tool_detail(tool_id: str):
    """获取工具详情"""
    service = get_marketplace_service()
    tool = service.get_tool(tool_id)

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "tool_type": tool.tool_type.value,
        "developer_id": tool.developer_id,
        "icon_url": tool.icon_url,
        "screenshots": tool.screenshots,
        "demo_video_url": tool.demo_video_url,
        "documentation_url": tool.documentation_url,
        "readme": tool.readme,
        "categories": tool.categories,
        "tags": tool.tags,
        "compatible_platforms": tool.compatible_platforms,
        "pricing_type": tool.pricing_type.value,
        "price": tool.price,
        "currency": tool.currency,
        "trial_days": tool.trial_days,
        "version": tool.version,
        "changelog": tool.changelog,
        "file_size": tool.file_size,
        "stats": {
            "download_count": tool.download_count,
            "rating": round(tool.rating, 1),
            "rating_count": tool.rating_count,
            "review_count": tool.review_count
        },
        "published_at": tool.published_at.isoformat() if tool.published_at else None
    }


@router.post("/tools/{tool_id}/purchase")
async def purchase_tool(
    tool_id: str,
    user_id: str = Depends(get_current_user)
):
    """购买工具"""
    service = get_marketplace_service()
    purchase = service.purchase_tool(tool_id, user_id)

    if not purchase:
        raise HTTPException(status_code=400, detail="Purchase failed")

    return {
        "message": "Purchase successful",
        "purchase_id": purchase.id,
        "amount": purchase.amount,
        "currency": purchase.currency,
        "license_key": purchase.license_key if purchase.license_key else None,
        "expires_at": purchase.expires_at.isoformat() if purchase.expires_at else None
    }


@router.get("/tools/{tool_id}/reviews")
async def get_tool_reviews(tool_id: str, limit: int = 20):
    """获取工具评价"""
    service = get_marketplace_service()
    reviews = service.get_reviews(tool_id, limit)

    return {
        "reviews": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "rating": r.rating,
                "title": r.title,
                "content": r.content,
                "is_recommended": r.is_recommended,
                "helpful_count": r.helpful_count,
                "created_at": r.created_at.isoformat()
            }
            for r in reviews
        ]
    }


@router.post("/tools/{tool_id}/reviews")
async def add_review(
    tool_id: str,
    request: ReviewRequest,
    user_id: str = Depends(get_current_user)
):
    """添加评价"""
    service = get_marketplace_service()
    review = service.add_review(
        tool_id=tool_id,
        user_id=user_id,
        rating=request.rating,
        title=request.title,
        content=request.content,
        is_recommended=request.is_recommended
    )

    if not review:
        raise HTTPException(status_code=403, detail="Must purchase tool before reviewing")

    return {
        "message": "Review added successfully",
        "review_id": review.id
    }


# ==================== 开发者API ====================

@router.post("/developer/profile")
async def create_developer_profile(
    request: DeveloperProfileRequest,
    user_id: str = Depends(get_current_user)
):
    """创建开发者主页"""
    service = get_marketplace_service()
    profile = service.create_developer_profile(
        user_id=user_id,
        display_name=request.display_name,
        bio=request.bio,
        website=request.website
    )

    return {
        "message": "Developer profile created",
        "user_id": profile.user_id
    }


@router.get("/developer/profile/{developer_id}")
async def get_developer_profile(developer_id: str):
    """获取开发者主页"""
    service = get_marketplace_service()
    profile = service.get_developer_profile(developer_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Developer not found")

    # 获取开发者的工具
    tools = service.get_developer_tools(developer_id)
    published_tools = [t for t in tools if t.status.value == "published"]

    return {
        "user_id": profile.user_id,
        "display_name": profile.display_name,
        "bio": profile.bio,
        "avatar_url": profile.avatar_url,
        "website": profile.website,
        "verified": profile.verified,
        "stats": {
            "total_tools": profile.total_tools,
            "total_downloads": profile.total_downloads,
            "average_rating": round(profile.average_rating, 1),
            "follower_count": len(profile.followers)
        },
        "tools": [
            {
                "id": t.id,
                "name": t.name,
                "tool_type": t.tool_type.value,
                "rating": round(t.rating, 1),
                "download_count": t.download_count
            }
            for t in published_tools
        ]
    }


@router.post("/developer/tools")
async def create_tool(
    request: CreateToolRequest,
    user_id: str = Depends(get_current_user)
):
    """创建新工具"""
    service = get_marketplace_service()

    try:
        tool_type = ToolType(request.tool_type)
        pricing_type = PricingType(request.pricing_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    tool = service.create_tool(
        name=request.name,
        description=request.description,
        tool_type=tool_type,
        developer_id=user_id,
        categories=request.categories,
        tags=request.tags,
        pricing_type=pricing_type,
        price=request.price,
        compatible_platforms=request.compatible_platforms
    )

    return {
        "message": "Tool created successfully",
        "tool": {
            "id": tool.id,
            "name": tool.name,
            "status": tool.status.value
        }
    }


@router.post("/developer/tools/{tool_id}/publish")
async def publish_tool(
    tool_id: str,
    user_id: str = Depends(get_current_user)
):
    """发布工具"""
    service = get_marketplace_service()
    success = service.publish_tool(tool_id, user_id)

    if not success:
        raise HTTPException(status_code=403, detail="Only tool developer can publish")

    return {"message": "Tool published successfully"}


@router.get("/developer/revenue")
async def get_developer_revenue(user_id: str = Depends(get_current_user)):
    """获取开发者收入统计"""
    service = get_marketplace_service()
    revenue = service.get_developer_revenue(user_id)

    return revenue


# ==================== 用户API ====================

@router.get("/my/purchases")
async def get_my_purchases(user_id: str = Depends(get_current_user)):
    """获取我的购买记录"""
    service = get_marketplace_service()
    purchases = service.get_user_purchases(user_id)

    return {
        "purchases": purchases
    }


@router.get("/recommended")
async def get_recommended_tools(
    user_id: str = Depends(get_current_user),
    limit: int = 10
):
    """获取推荐工具"""
    service = get_marketplace_service()
    tools = service.get_recommended_tools(user_id, limit)

    return {
        "recommendations": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description[:100] + "..." if len(t.description) > 100 else t.description,
                "tool_type": t.tool_type.value,
                "rating": round(t.rating, 1),
                "icon_url": t.icon_url
            }
            for t in tools
        ]
    }


@router.get("/categories")
async def get_categories():
    """获取工具分类"""
    return {
        "categories": [
            {"id": "data_analysis", "name": "数据分析", "icon": "📊"},
            {"id": "visualization", "name": "可视化", "icon": "📈"},
            {"id": "writing", "name": "学术写作", "icon": "✍️"},
            {"id": "citation", "name": "文献引用", "icon": "📚"},
            {"id": "translation", "name": "翻译", "icon": "🌐"},
            {"id": "formatting", "name": "格式排版", "icon": "📄"},
            {"id": "collaboration", "name": "协作工具", "icon": "👥"},
            {"id": "automation", "name": "自动化", "icon": "🤖"},
            {"id": "ml_models", "name": "机器学习模型", "icon": "🧠"},
            {"id": "datasets", "name": "数据集", "icon": "💾"}
        ]
    }
