"""
智能推荐服务增强版
基于多维度因素的推荐系统
"""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import random

from .models import Article, Recommendation, UserProfile
from ..ai.llm_provider_v2 import LLMService


class EnhancedRecommendationService:
    """增强版推荐服务"""

    def __init__(self, db_session=None, llm_service: Optional[LLMService] = None):
        self.db = db_session
        self.llm = llm_service

    async def get_personalized_recommendations(
        self,
        user_id: str,
        user_profile: UserProfile,
        context: Optional[Dict] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取个性化推荐

        综合多种推荐策略:
        1. 基于阅读历史的协同过滤
        2. 基于研究兴趣的内容推荐
        3. 热门论文推荐
        4. 相关论文推荐
        5. 趋势论文推荐
        """
        recommendations = []

        # 并行获取各种推荐
        tasks = [
            self._get_content_based_recommendations(user_profile, limit // 2),
            self._get_collaborative_recommendations(user_id, user_profile, limit // 3),
            self._get_trending_papers(limit // 4),
            self._get_recent_papers_from_interests(user_profile, limit // 4),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                recommendations.extend(result)

        # 去重并排序
        seen_ids = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec.get("id") not in seen_ids:
                seen_ids.add(rec.get("id"))
                unique_recommendations.append(rec)

        # 使用AI进行重排序
        if self.llm and unique_recommendations:
            unique_recommendations = await self._rerank_with_ai(
                unique_recommendations, user_profile, limit
            )

        return unique_recommendations[:limit]

    async def _get_content_based_recommendations(
        self,
        user_profile: UserProfile,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """基于内容的推荐（根据研究兴趣）"""
        interests = user_profile.research_interests or []

        if not interests:
            return []

        # 这里应该查询数据库或外部API
        # 简化版本返回模拟数据
        recommendations = []
        for i, interest in enumerate(interests[:3]):
            recommendations.append({
                "id": f"content_rec_{i}",
                "title": f"Recent advances in {interest}",
                "authors": [{"name": "Researcher et al."}],
                "abstract": f"This paper discusses recent developments in {interest}...",
                "source_name": "arXiv",
                "publication_year": 2024,
                "relevance_score": 0.85 - i * 0.05,
                "recommendation_reason": f"匹配您的研究兴趣: {interest}",
                "recommendation_type": "content_based",
            })

        return recommendations[:limit]

    async def _get_collaborative_recommendations(
        self,
        user_id: str,
        user_profile: UserProfile,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """协同过滤推荐（基于相似用户）"""
        # 这里应该查询相似用户的阅读历史
        # 简化版本返回模拟数据
        return [
            {
                "id": f"collab_rec_{i}",
                "title": f"Collaborative filtering recommendation {i+1}",
                "authors": [{"name": "Author et al."}],
                "abstract": "This paper is popular among researchers with similar interests...",
                "source_name": "Semantic Scholar",
                "publication_year": 2024,
                "relevance_score": 0.80,
                "recommendation_reason": "与您兴趣相似的研究者正在阅读",
                "recommendation_type": "collaborative",
            }
            for i in range(min(limit, 3))
        ]

    async def _get_trending_papers(self, limit: int) -> List[Dict[str, Any]]:
        """获取热门论文"""
        # 这里应该查询数据库获取热门论文
        trending = [
            {
                "id": "trending_1",
                "title": "Large Language Models: A Survey",
                "authors": [{"name": "Zhang et al."}],
                "abstract": "A comprehensive survey of large language models...",
                "source_name": "arXiv",
                "publication_year": 2024,
                "citation_count": 1200,
                "relevance_score": 0.95,
                "recommendation_reason": "本周热门论文，引用快速增长",
                "recommendation_type": "trending",
            },
            {
                "id": "trending_2",
                "title": "Vision Transformers: An Overview",
                "authors": [{"name": "Li et al."}],
                "abstract": "Overview of vision transformer architectures...",
                "source_name": "IEEE",
                "publication_year": 2024,
                "citation_count": 800,
                "relevance_score": 0.90,
                "recommendation_reason": "领域内高关注度",
                "recommendation_type": "trending",
            },
        ]
        return trending[:limit]

    async def _get_recent_papers_from_interests(
        self,
        user_profile: UserProfile,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """获取研究兴趣相关的最新论文"""
        interests = user_profile.research_interests or ["AI", "Machine Learning"]

        # 这里应该查询arXiv或Semantic Scholar的最新论文
        recent = []
        for i, interest in enumerate(interests[:2]):
            recent.append({
                "id": f"recent_{i}",
                "title": f"Latest Research on {interest} (2024)",
                "authors": [{"name": "Recent Author"}],
                "abstract": f"Recent developments in {interest}...",
                "source_name": "arXiv",
                "publication_year": 2024,
                "publication_date": (datetime.now() - timedelta(days=i*7)).isoformat(),
                "relevance_score": 0.88,
                "recommendation_reason": f"{interest}领域的最新研究",
                "recommendation_type": "recent",
            })

        return recent[:limit]

    async def _rerank_with_ai(
        self,
        recommendations: List[Dict[str, Any]],
        user_profile: UserProfile,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """使用AI进行重排序"""
        if not self.llm or len(recommendations) <= limit:
            return recommendations

        # 构建提示
        papers_text = "\n".join([
            f"{i+1}. {rec['title']} - 原因: {rec.get('recommendation_reason', '')}"
            for i, rec in enumerate(recommendations[:20])
        ])

        interests_text = ", ".join(user_profile.research_interests or [])

        prompt = f"""请为以下论文推荐进行排序，选择最符合研究者兴趣的{limit}篇。

研究者兴趣: {interests_text}

候选论文:
{papers_text}

请返回排序后的序号列表，格式: [1, 3, 2, 5, ...]"""

        try:
            result = await self.llm.generate(prompt=prompt, max_tokens=200, temperature=0.3)
            content = result.content if hasattr(result, "content") else str(result)

            # 解析序号
            import json
            indices = json.loads(content)
            if isinstance(indices, list):
                reranked = []
                for idx in indices[:limit]:
                    if 1 <= idx <= len(recommendations):
                        reranked.append(recommendations[idx - 1])
                return reranked if reranked else recommendations[:limit]

        except Exception as e:
            print(f"AI重排序失败: {e}")

        return recommendations[:limit]

    async def get_related_papers(
        self,
        paper_id: str,
        paper_title: str,
        paper_abstract: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取相关论文"""
        # 这里应该调用Semantic Scholar的related papers API
        # 简化版本返回模拟数据
        return [
            {
                "id": f"related_{i}",
                "title": f"Related paper to '{paper_title[:30]}...' ({i+1})",
                "authors": [{"name": "Related Author"}],
                "abstract": "This paper is related to your current reading...",
                "source_name": "Semantic Scholar",
                "publication_year": 2024,
                "relevance_score": 0.75 - i * 0.05,
                "recommendation_reason": "与您正在阅读的论文高度相关",
                "recommendation_type": "related",
            }
            for i in range(min(limit, 5))
        ]

    async def explain_recommendation(
        self,
        recommendation_id: str,
        user_profile: UserProfile,
    ) -> str:
        """解释推荐原因"""
        if not self.llm:
            return "基于您的研究兴趣推荐"

        prompt = f"""请解释为什么向具有以下研究兴趣的用户推荐这篇论文:

用户兴趣: {', '.join(user_profile.research_interests or [])}
论文ID: {recommendation_id}

请用一句话简洁解释推荐原因。"""

        try:
            result = await self.llm.generate(prompt=prompt, max_tokens=100, temperature=0.5)
            return result.content if hasattr(result, "content") else str(result)
        except:
            return "基于您的研究兴趣推荐"

    async def get_feedback_based_recommendations(
        self,
        user_id: str,
        positive_feedback: List[str],  # 用户喜欢的论文ID
        negative_feedback: List[str],   # 用户不喜欢的论文ID
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """基于反馈的推荐"""
        # 这里应该使用机器学习模型进行推荐
        # 简化版本返回基于正反馈的相似论文
        return await self._get_content_based_recommendations(
            UserProfile(research_interests=["Based on feedback"]),
            limit,
        )

    async def get_citation_based_recommendations(
        self,
        paper_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """基于引用的推荐（引用该论文的文献 + 该论文引用的文献）"""
        # 这里应该查询Semantic Scholar的citations和references
        return [
            {
                "id": f"citation_{i}",
                "title": f"Citation-based recommendation {i+1}",
                "authors": [{"name": "Cited Author"}],
                "abstract": "This paper is connected through citation network...",
                "source_name": "Semantic Scholar",
                "publication_year": 2024,
                "relevance_score": 0.82,
                "recommendation_reason": "通过引用网络关联",
                "recommendation_type": "citation_based",
            }
            for i in range(min(limit, 5))
        ]
