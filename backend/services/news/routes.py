"""
Research News API Routes
科研新闻API路由
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from .service import get_news_service, NewsCategory, NewsSource, UserNewsPreference

router = APIRouter(prefix="/news", tags=["news"])


# ==================== 请求/响应模型 ====================

class NewsPreferenceRequest(BaseModel):
    """新闻偏好设置"""
    followed_categories: List[str] = Field(default_factory=list)
    followed_keywords: List[str] = Field(default_factory=list)
    followed_authors: List[str] = Field(default_factory=list)
    notification_enabled: bool = True
    digest_frequency: str = "daily"


class NewsResponse(BaseModel):
    """新闻响应"""
    id: str
    title: str
    summary: str
    category: str
    source: str
    published_at: str
    authors: List[str]
    tags: List[str]
    impact_score: float
    view_count: int


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== API端点 ====================

@router.get("/latest")
async def get_latest_news(
    category: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """获取最新新闻"""
    service = get_news_service()

    category_enum = None
    if category:
        try:
            category_enum = NewsCategory(category)
        except ValueError:
            pass

    source_enum = None
    if source:
        try:
            source_enum = NewsSource(source)
        except ValueError:
            pass

    news_list = service.get_news(
        category=category_enum,
        source=source_enum,
        limit=limit,
        offset=offset
    )

    return {
        "total": len(news_list),
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "summary": n.summary,
                "category": n.category.value,
                "source": n.source.value,
                "published_at": n.published_at.isoformat(),
                "authors": n.authors,
                "tags": n.tags,
                "impact_score": n.impact_score,
                "view_count": n.view_count
            }
            for n in news_list
        ]
    }


@router.get("/{news_id}")
async def get_news_detail(news_id: str):
    """获取新闻详情"""
    service = get_news_service()
    news = service.get_news_by_id(news_id)

    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    return {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "summary": news.summary,
        "category": news.category.value,
        "source": news.source.value,
        "source_url": news.source_url,
        "published_at": news.published_at.isoformat(),
        "authors": news.authors,
        "tags": news.tags,
        "related_papers": news.related_papers,
        "related_concepts": news.related_concepts,
        "impact_score": news.impact_score,
        "view_count": news.view_count,
        "like_count": news.like_count,
        "image_url": news.image_url
    }


@router.get("/personalized/feed")
async def get_personalized_feed(
    user_id: str = Depends(get_current_user),
    limit: int = 20
):
    """获取个性化新闻推荐"""
    service = get_news_service()
    news_list = service.get_personalized_news(user_id, limit)

    return {
        "user_id": user_id,
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "summary": n.summary,
                "category": n.category.value,
                "published_at": n.published_at.isoformat(),
                "tags": n.tags,
                "reason": "Based on your interests"  # 推荐原因
            }
            for n in news_list
        ]
    }


@router.post("/preferences")
async def set_news_preferences(
    request: NewsPreferenceRequest,
    user_id: str = Depends(get_current_user)
):
    """设置新闻偏好"""
    service = get_news_service()

    # 转换分类
    categories = []
    for cat in request.followed_categories:
        try:
            categories.append(NewsCategory(cat))
        except ValueError:
            continue

    preference = UserNewsPreference(
        user_id=user_id,
        followed_categories=categories,
        followed_keywords=request.followed_keywords,
        followed_authors=request.followed_authors,
        notification_enabled=request.notification_enabled,
        digest_frequency=request.digest_frequency
    )

    service.set_user_preference(user_id, preference)

    return {"message": "Preferences updated successfully"}


@router.get("/digest/daily")
async def get_daily_digest(user_id: str = Depends(get_current_user)):
    """获取每日摘要"""
    service = get_news_service()
    digest = service.get_daily_digest(user_id)
    return digest


@router.get("/trends/hot")
async def get_trending_topics(limit: int = 10):
    """获取热门研究主题"""
    service = get_news_service()
    service.update_trends()  # 更新趋势
    trends = service.get_trending_topics(limit)

    return {
        "trends": trends,
        "updated_at": datetime.utcnow().isoformat()
    }


@router.get("/trends/timeline/{concept}")
async def get_concept_timeline(
    concept: str,
    days: int = 30
):
    """获取概念时间线"""
    service = get_news_service()
    timeline = service.get_concept_timeline(concept, days)

    return {
        "concept": concept,
        "period_days": days,
        "events": timeline
    }


@router.get("/industry/updates")
async def get_industry_updates(sector: Optional[str] = None):
    """获取行业动态"""
    service = get_news_service()
    updates = service.get_industry_updates(sector)

    return {
        "sector": sector,
        "updates": updates
    }


@router.get("/policy/updates")
async def get_policy_updates():
    """获取政策更新"""
    service = get_news_service()
    policies = service.get_policy_updates()

    return {
        "policies": policies
    }


@router.get("/categories")
async def get_news_categories():
    """获取新闻分类列表"""
    return {
        "categories": [
            {"id": "breakthrough", "name": "重大突破", "description": "重要科研突破"},
            {"id": "publication", "name": "论文发表", "description": "顶级期刊论文"},
            {"id": "conference", "name": "会议动态", "description": "学术会议信息"},
            {"id": "funding", "name": "科研资助", "description": "基金项目动态"},
            {"id": "policy", "name": "政策变化", "description": "科研政策更新"},
            {"id": "industry", "name": "产业动态", "description": "产学研合作"},
            {"id": "trend", "name": "研究趋势", "description": "新兴研究方向"},
            {"id": "people", "name": "人物动态", "description": "学者动态"}
        ]
    }
