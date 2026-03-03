"""
推荐服务 API 路由
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.responses import success_response
from shared.dependencies import get_current_user_id

from .service import RecommendationService

router = APIRouter(prefix="/api/v1/recommendations", tags=["智能推荐"])


@router.get("/daily", summary="获取每日推荐")
async def get_daily_recommendations(
    limit: int = 10,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取每日个性化推荐

    基于用户研究兴趣和阅读历史
    """
    service = RecommendationService(db)
    recommendations = await service.get_daily_recommendations(
        user_id=uuid.UUID(user_id),
        limit=limit,
    )

    return success_response(data=recommendations)


@router.get("/similar/{article_id}", summary="获取相似文献")
async def get_similar_articles(
    article_id: uuid.UUID,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """获取与指定文献相似的文章"""
    service = RecommendationService(db)
    similar = await service.get_similar_articles(article_id, limit)

    return success_response(data=similar)


@router.get("/trending", summary="获取热门文献")
async def get_trending_articles(
    days: int = 7,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """获取热门文献"""
    service = RecommendationService(db)
    trending = await service.get_trending_articles(days, limit)

    return success_response(data=trending)


@router.post("/behavior", summary="记录用户行为")
async def record_behavior(
    article_id: uuid.UUID,
    behavior_type: str,
    duration: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    记录用户行为

    behavior_type: view, save, cite, download
    """
    service = RecommendationService(db)
    await service.record_behavior(
        user_id=uuid.UUID(user_id),
        article_id=article_id,
        behavior_type=behavior_type,
        duration=duration,
    )
    await db.commit()

    return success_response(message="行为已记录")


@router.get("/interests", summary="获取用户兴趣")
async def get_user_interests(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户研究兴趣"""
    import json
    from .models import UserPreference

    result = await db.execute(
        select(UserPreference).where(
            UserPreference.user_id == uuid.UUID(user_id)
        )
    )
    pref = result.scalar_one_or_none()

    if not pref or not pref.research_interests:
        return success_response(data={'interests': {}})

    interests = json.loads(pref.research_interests)

    return success_response(data={'interests': interests})


@router.put("/interests", summary="更新用户兴趣")
async def update_user_interests(
    interests: dict[str, float],
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """手动更新用户研究兴趣"""
    service = RecommendationService(db)
    await service.update_user_preferences(
        user_id=uuid.UUID(user_id),
        research_interests=interests,
    )
    await db.commit()

    return success_response(message="兴趣已更新")


from sqlalchemy import select
