"""
模板推荐服务
基于用户行为和论文内容推荐合适的模板
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

from .models import PaperTemplate, TemplateType, TemplateUsage
from .search_service import TemplateSearchService


@dataclass
class RecommendationContext:
    """推荐上下文"""
    user_id: Optional[str] = None
    paper_title: Optional[str] = None
    paper_abstract: Optional[str] = None
    paper_keywords: List[str] = None
    target_journal: Optional[str] = None
    discipline: Optional[str] = None
    language: Optional[str] = None


@dataclass
class RecommendationResult:
    """推荐结果"""
    template: PaperTemplate
    score: float
    reason: str
    confidence: float


class TemplateRecommendation:
    """
    模板推荐服务
    支持个性化推荐、热门推荐、相似推荐
    """

    def __init__(self):
        self.search_service = TemplateSearchService()
        # 模拟用户使用历史
        self._usage_history: Dict[str, List[TemplateUsage]] = {}
        # 模拟用户收藏的模板
        self._user_favorites: Dict[str, List[str]] = {}

    async def recommend(
        self,
        context: RecommendationContext,
        limit: int = 5,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[RecommendationResult]:
        """
        获取推荐模板

        Args:
            context: 推荐上下文
            limit: 返回数量
            exclude_ids: 排除的模板ID

        Returns:
            推荐结果列表
        """
        candidates = []

        # 基于上下文的推荐
        context_recommendations = await self._recommend_by_context(context, exclude_ids)
        candidates.extend(context_recommendations)

        # 基于用户历史的推荐
        if context.user_id:
            history_recommendations = await self._recommend_by_history(
                context.user_id, exclude_ids
            )
            candidates.extend(history_recommendations)

        # 热门推荐
        popular_recommendations = await self._recommend_popular(
            limit=3, exclude_ids=exclude_ids
        )
        candidates.extend(popular_recommendations)

        # 去重并排序
        seen_ids = set()
        unique_candidates = []
        for rec in candidates:
            if rec.template.id not in seen_ids:
                seen_ids.add(rec.template.id)
                unique_candidates.append(rec)

        # 按分数排序
        unique_candidates.sort(key=lambda r: r.score, reverse=True)

        return unique_candidates[:limit]

    async def _recommend_by_context(
        self,
        context: RecommendationContext,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[RecommendationResult]:
        """基于上下文推荐"""
        results = []
        exclude_ids = exclude_ids or []

        # 分析论文标题和摘要
        content = ""
        if context.paper_title:
            content += context.paper_title + " "
        if context.paper_abstract:
            content += context.paper_abstract

        # 根据目标期刊推荐
        if context.target_journal:
            search_result = await self.search_service.search(
                query=context.target_journal,
                limit=10,
            )
            for item in search_result["items"]:
                if item["id"] not in exclude_ids:
                    template = await self.search_service.get_template(item["id"])
                    if template:
                        score = 0.9 if context.target_journal.lower() in (
                            template.institution or "").lower() else 0.7
                        results.append(RecommendationResult(
                            template=template,
                            score=score,
                            reason=f"匹配目标期刊: {context.target_journal}",
                            confidence=0.8,
                        ))

        # 根据学科推荐
        if context.discipline:
            search_result = await self.search_service.search(
                query="",
                limit=10,
            )
            for item in search_result["items"]:
                if item["id"] not in exclude_ids and item.get("discipline") == context.discipline:
                    template = await self.search_service.get_template(item["id"])
                    if template and template.id not in [r.template.id for r in results]:
                        results.append(RecommendationResult(
                            template=template,
                            score=0.75,
                            reason=f"匹配学科领域: {context.discipline}",
                            confidence=0.7,
                        ))

        # 根据关键词推荐
        if context.paper_keywords:
            keyword_query = " ".join(context.paper_keywords[:3])
            search_result = await self.search_service.search(
                query=keyword_query,
                limit=10,
            )
            for item in search_result["items"]:
                if item["id"] not in exclude_ids:
                    template = await self.search_service.get_template(item["id"])
                    if template and template.id not in [r.template.id for r in results]:
                        # 计算关键词匹配度
                        matched_keywords = sum(
                            1 for kw in context.paper_keywords
                            if kw.lower() in template.searchable_content or
                            any(kw.lower() in tag.lower() for tag in template.tags)
                        )
                        score = min(0.5 + matched_keywords * 0.1, 0.9)
                        results.append(RecommendationResult(
                            template=template,
                            score=score,
                            reason=f"匹配关键词: {', '.join(context.paper_keywords[:2])}",
                            confidence=0.6 + matched_keywords * 0.05,
                        ))

        return results

    async def _recommend_by_history(
        self,
        user_id: str,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[RecommendationResult]:
        """基于用户历史推荐"""
        results = []
        exclude_ids = exclude_ids or []

        # 获取用户使用过的模板
        usage_history = self._usage_history.get(user_id, [])

        if not usage_history:
            return results

        # 分析用户偏好
        used_template_ids = set(u.template_id for u in usage_history)
        used_types = set()
        used_institutions = set()

        for usage in usage_history:
            template = await self.search_service.get_template(usage.template_id)
            if template:
                used_types.add(template.type)
                if template.institution:
                    used_institutions.add(template.institution)

        # 推荐相似类型
        search_result = await self.search_service.search(
            query="",
            limit=20,
        )

        for item in search_result["items"]:
            if item["id"] in exclude_ids or item["id"] in used_template_ids:
                continue

            template = await self.search_service.get_template(item["id"])
            if not template:
                continue

            # 计算相似度
            score = 0.0
            reasons = []

            if template.type in used_types:
                score += 0.4
                reasons.append(f"您经常使用{template.type.value}类模板")

            if template.institution in used_institutions:
                score += 0.3
                reasons.append(f"您关注{template.institution}的模板")

            # 获取用户收藏的模板标签
            favorite_ids = self._user_favorites.get(user_id, [])
            favorite_tags = set()
            for fid in favorite_ids:
                ft = await self.search_service.get_template(fid)
                if ft:
                    favorite_tags.update(ft.tags)

            matched_tags = set(template.tags) & favorite_tags
            if matched_tags:
                score += len(matched_tags) * 0.1
                reasons.append(f"与您收藏的模板标签相似")

            if score > 0:
                results.append(RecommendationResult(
                    template=template,
                    score=min(score, 0.85),
                    reason="; ".join(reasons[:2]),
                    confidence=0.6,
                ))

        return results

    async def _recommend_popular(
        self,
        limit: int = 5,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[RecommendationResult]:
        """推荐热门模板"""
        results = []
        exclude_ids = exclude_ids or []

        search_result = await self.search_service.search(
            query="",
            sort_by="downloads",
            limit=limit + len(exclude_ids),
        )

        for item in search_result["items"]:
            if item["id"] not in exclude_ids:
                template = await self.search_service.get_template(item["id"])
                if template:
                    score = min(template.stats.download_count / 5000, 0.7)
                    results.append(RecommendationResult(
                        template=template,
                        score=score,
                        reason=f"热门模板 ({template.stats.download_count}次下载)",
                        confidence=0.5,
                    ))

        return results[:limit]

    async def recommend_for_paper(
        self,
        paper_title: str,
        paper_abstract: Optional[str] = None,
        paper_keywords: Optional[List[str]] = None,
        target_type: Optional[TemplateType] = None,
        limit: int = 3,
    ) -> List[RecommendationResult]:
        """
        为特定论文推荐模板

        Args:
            paper_title: 论文标题
            paper_abstract: 论文摘要
            paper_keywords: 论文关键词
            target_type: 目标模板类型
            limit: 返回数量

        Returns:
            推荐结果列表
        """
        context = RecommendationContext(
            paper_title=paper_title,
            paper_abstract=paper_abstract,
            paper_keywords=paper_keywords or [],
        )

        # 如果指定了类型，添加过滤
        candidates = await self.recommend(context, limit=limit * 2)

        if target_type:
            candidates = [
                c for c in candidates
                if c.template.type == target_type
            ]

        return candidates[:limit]

    async def get_similar_templates(
        self,
        template_id: str,
        limit: int = 5,
    ) -> List[RecommendationResult]:
        """
        获取相似模板

        Args:
            template_id: 参考模板ID
            limit: 返回数量

        Returns:
            相似模板列表
        """
        reference = await self.search_service.get_template(template_id)
        if not reference:
            return []

        results = []
        search_result = await self.search_service.search(
            query=reference.name,
            limit=20,
        )

        for item in search_result["items"]:
            if item["id"] == template_id:
                continue

            template = await self.search_service.get_template(item["id"])
            if not template:
                continue

            # 计算相似度
            score = 0.0
            reasons = []

            # 类型相同
            if template.type == reference.type:
                score += 0.3
                reasons.append("相同类型")

            # 机构相同
            if template.institution and reference.institution:
                if template.institution == reference.institution:
                    score += 0.3
                    reasons.append("相同机构")

            # 标签相似
            common_tags = set(template.tags) & set(reference.tags)
            if common_tags:
                score += len(common_tags) * 0.15
                reasons.append(f"共享标签: {', '.join(list(common_tags)[:2])}")

            # 学科相同
            if template.discipline and reference.discipline:
                if template.discipline == reference.discipline:
                    score += 0.2
                    reasons.append("相同学科")

            if score > 0:
                results.append(RecommendationResult(
                    template=template,
                    score=min(score, 0.95),
                    reason="; ".join(reasons[:2]),
                    confidence=min(score + 0.1, 0.9),
                ))

        # 排序并限制
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    async def get_trending_templates(
        self,
        days: int = 7,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取趋势模板

        Args:
            days: 统计天数
            limit: 返回数量

        Returns:
            趋势模板列表
        """
        # 模拟趋势数据
        search_result = await self.search_service.search(
            query="",
            sort_by="downloads",
            limit=limit,
        )

        trending = []
        for item in search_result["items"]:
            template = await self.search_service.get_template(item["id"])
            if template:
                # 模拟增长率
                growth_rate = random.uniform(0.05, 0.3)
                trending.append({
                    "template": template.to_dict(),
                    "growth_rate": round(growth_rate, 2),
                    "recent_downloads": int(template.stats.download_count * growth_rate),
                })

        # 按增长率排序
        trending.sort(key=lambda x: x["growth_rate"], reverse=True)
        return trending[:limit]

    async def record_usage(
        self,
        user_id: str,
        template_id: str,
        paper_id: Optional[str] = None,
    ):
        """记录模板使用"""
        usage = TemplateUsage(
            id=f"{user_id}_{template_id}_{datetime.now().timestamp()}",
            template_id=template_id,
            user_id=user_id,
            paper_id=paper_id,
            created_at=datetime.now(),
        )

        if user_id not in self._usage_history:
            self._usage_history[user_id] = []

        self._usage_history[user_id].append(usage)

        # 限制历史记录数量
        self._usage_history[user_id] = self._usage_history[user_id][-50:]

    async def add_favorite(self, user_id: str, template_id: str):
        """添加收藏"""
        if user_id not in self._user_favorites:
            self._user_favorites[user_id] = []

        if template_id not in self._user_favorites[user_id]:
            self._user_favorites[user_id].append(template_id)

    async def remove_favorite(self, user_id: str, template_id: str):
        """移除收藏"""
        if user_id in self._user_favorites:
            if template_id in self._user_favorites[user_id]:
                self._user_favorites[user_id].remove(template_id)

    async def get_favorites(self, user_id: str) -> List[str]:
        """获取用户收藏"""
        return self._user_favorites.get(user_id, [])
