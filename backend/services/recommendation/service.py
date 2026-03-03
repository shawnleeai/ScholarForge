"""
推荐服务
智能文献推荐
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from .models import UserPreference, ArticleFeature, Recommendation, UserBehavior
from .algorithm import RecommendationAlgorithm, HybridRecommender


class RecommendationService:
    """推荐服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.algorithm = RecommendationAlgorithm()
        self.hybrid_recommender = HybridRecommender()

    async def get_user_preferences(self, user_id: uuid.UUID) -> Optional[UserPreference]:
        """获取用户偏好"""
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user_preferences(
        self,
        user_id: uuid.UUID,
        research_interests: Dict[str, float],
    ) -> UserPreference:
        """更新用户偏好"""
        pref = await self.get_user_preferences(user_id)

        if not pref:
            pref = UserPreference(
                user_id=user_id,
                research_interests=json.dumps(research_interests),
            )
            self.db.add(pref)
        else:
            pref.research_interests = json.dumps(research_interests)
            pref.updated_at = datetime.utcnow()

        await self.db.flush()
        return pref

    async def record_behavior(
        self,
        user_id: uuid.UUID,
        article_id: uuid.UUID,
        behavior_type: str,
        duration: int = 0,
    ):
        """记录用户行为"""
        behavior = UserBehavior(
            user_id=user_id,
            article_id=article_id,
            behavior_type=behavior_type,
            duration=duration,
        )
        self.db.add(behavior)
        await self.db.flush()

    async def get_daily_recommendations(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
    ) -> List[Dict]:
        """
        获取每日推荐

        基于用户兴趣和历史行为
        """
        # 获取用户偏好
        pref = await self.get_user_preferences(user_id)
        interests = json.loads(pref.research_interests) if pref and pref.research_interests else {}

        # 获取用户已读文献
        result = await self.db.execute(
            select(UserBehavior.article_id).where(
                UserBehavior.user_id == user_id,
                UserBehavior.behavior_type.in_(['view', 'save']),
            )
        )
        read_articles = [str(row[0]) for row in result.fetchall()]

        # 获取候选文献
        result = await self.db.execute(
            select(ArticleFeature).order_by(
                desc(ArticleFeature.recency_score)
            ).limit(100)
        )
        candidates = result.scalars().all()

        # 计算推荐分数
        recommendations = []
        for article in candidates:
            if str(article.article_id) in read_articles:
                continue

            keywords = json.loads(article.keywords) if article.keywords else []

            # 计算各维度分数
            relevance = self.algorithm.calculate_relevance_score(
                interests,
                keywords,
            )

            timeliness = article.recency_score or 0.5
            authority = article.authority_score or 0.5

            total, scores = self.algorithm.calculate_total_score(
                relevance=relevance,
                timeliness=timeliness,
                authority=authority,
            )

            explanation = self.algorithm.generate_explanation(
                scores,
                article.article_id,
            )

            recommendations.append({
                'article_id': str(article.article_id),
                'score': total,
                'scores': scores,
                'explanation': explanation,
            })

        # 按分数排序
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        return recommendations[:limit]

    async def get_similar_articles(
        self,
        article_id: uuid.UUID,
        limit: int = 5,
    ) -> List[Dict]:
        """获取相似文献"""
        # 获取目标文献特征
        result = await self.db.execute(
            select(ArticleFeature).where(ArticleFeature.article_id == article_id)
        )
        target = result.scalar_one_or_none()

        if not target:
            return []

        target_keywords = set(
            json.loads(target.keywords) if target.keywords else []
        )

        # 查找相似文献
        result = await self.db.execute(
            select(ArticleFeature).where(
                ArticleFeature.article_id != article_id,
            ).limit(50)
        )
        candidates = result.scalars().all()

        similar = []
        for article in candidates:
            article_keywords = set(
                json.loads(article.keywords) if article.keywords else []
            )

            # Jaccard 相似度
            if target_keywords and article_keywords:
                intersection = len(target_keywords & article_keywords)
                union = len(target_keywords | article_keywords)
                similarity = intersection / union if union > 0 else 0
            else:
                similarity = 0

            if similarity > 0.1:  # 相似度阈值
                similar.append({
                    'article_id': str(article.article_id),
                    'similarity': similarity,
                })

        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:limit]

    async def get_trending_articles(
        self,
        days: int = 7,
        limit: int = 10,
    ) -> List[Dict]:
        """获取热门文献"""
        since = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(UserBehavior.article_id,
                   UserBehavior.behavior_type).where(
                UserBehavior.created_at >= since,
                UserBehavior.behavior_type.in_(['view', 'save', 'cite']),
            )
        )

        # 统计热度
        popularity = Counter()
        for row in result:
            article_id = str(row[0])
            behavior = row[1]
            weight = {'view': 1, 'save': 3, 'cite': 5}.get(behavior, 1)
            popularity[article_id] += weight

        trending = [
            {'article_id': aid, 'popularity': pop}
            for aid, pop in popularity.most_common(limit)
        ]

        return trending

    async def update_user_interests_from_behavior(
        self,
        user_id: uuid.UUID,
    ):
        """根据用户行为更新兴趣偏好"""
        # 获取用户最近30天的行为
        since = datetime.utcnow() - timedelta(days=30)

        result = await self.db.execute(
            select(UserBehavior, ArticleFeature).join(
                ArticleFeature,
                UserBehavior.article_id == ArticleFeature.article_id,
            ).where(
                UserBehavior.user_id == user_id,
                UserBehavior.created_at >= since,
                UserBehavior.behavior_type.in_(['save', 'cite']),
            )
        )

        # 统计关键词频率
        keyword_weights = Counter()
        for behavior, feature in result:
            keywords = json.loads(feature.keywords) if feature.keywords else []
            weight = {'save': 2.0, 'cite': 3.0}.get(behavior.behavior_type, 1.0)
            for kw in keywords:
                keyword_weights[kw] += weight

        # 归一化
        if keyword_weights:
            max_weight = max(keyword_weights.values())
            interests = {
                k: round(v / max_weight, 3)
                for k, v in keyword_weights.most_common(50)
            }
            await self.update_user_preferences(user_id, interests)
