"""
Research News Service
科研新闻服务 - 聚合学术动态、行业新闻、热点追踪
"""

import asyncio
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class NewsCategory(str, Enum):
    """新闻分类"""
    BREAKTHROUGH = "breakthrough"      # 重大突破
    PUBLICATION = "publication"        # 论文发表
    CONFERENCE = "conference"          # 会议动态
    FUNDING = "funding"                # 科研资助
    POLICY = "policy"                  # 政策变化
    INDUSTRY = "industry"              # 产业动态
    TREND = "trend"                    # 研究趋势
    PEOPLE = "people"                  # 人物动态


class NewsSource(str, Enum):
    """新闻来源"""
    ARXIV = "arxiv"
    NATURE = "nature"
    SCIENCE = "science"
    CELL = "cell"
    IEEE = "ieee"
    ACM = "acm"
    GOOGLE_SCHOLAR = "google_scholar"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    RESEARCH_GATE = "research_gate"
    CUSTOM = "custom"


@dataclass
class ResearchNews:
    """科研新闻"""
    id: str
    title: str
    content: str
    summary: str
    category: NewsCategory
    source: NewsSource
    source_url: str
    published_at: datetime
    authors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    related_papers: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    impact_score: float = 0.0
    view_count: int = 0
    like_count: int = 0
    share_count: int = 0
    image_url: Optional[str] = None


@dataclass
class UserNewsPreference:
    """用户新闻偏好"""
    user_id: str
    followed_categories: List[NewsCategory] = field(default_factory=list)
    followed_keywords: List[str] = field(default_factory=list)
    followed_authors: List[str] = field(default_factory=list)
    followed_venues: List[str] = field(default_factory=list)
    blocked_keywords: List[str] = field(default_factory=list)
    notification_enabled: bool = True
    digest_frequency: str = "daily"  # realtime/daily/weekly


@dataclass
class ResearchTrend:
    """研究趋势"""
    concept: str
    growth_rate: float
    paper_count: int
    citation_count: int
    trending_papers: List[str]
    related_concepts: List[str]
    time_period: str
    last_updated: datetime


class ResearchNewsService:
    """科研新闻服务"""

    def __init__(self):
        self._news: List[ResearchNews] = []
        self._user_preferences: Dict[str, UserNewsPreference] = {}
        self._trends: Dict[str, ResearchTrend] = {}

    # ==================== 新闻管理 ====================

    def add_news(self, news: ResearchNews):
        """添加新闻"""
        # 生成ID
        if not news.id:
            news.id = hashlib.md5(
                f"{news.title}{news.published_at}".encode()
            ).hexdigest()[:16]

        # 检查重复
        existing = next((n for n in self._news if n.id == news.id), None)
        if not existing:
            self._news.append(news)
            # 按时间排序
            self._news.sort(key=lambda x: x.published_at, reverse=True)

    def get_news(
        self,
        category: Optional[NewsCategory] = None,
        source: Optional[NewsSource] = None,
        keywords: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[ResearchNews]:
        """获取新闻列表"""
        filtered = self._news

        if category:
            filtered = [n for n in filtered if n.category == category]

        if source:
            filtered = [n for n in filtered if n.source == source]

        if keywords:
            filtered = [
                n for n in filtered
                if any(kw.lower() in n.title.lower() or kw.lower() in n.content.lower()
                       for kw in keywords)
            ]

        if start_date:
            filtered = [n for n in filtered if n.published_at >= start_date]

        if end_date:
            filtered = [n for n in filtered if n.published_at <= end_date]

        return filtered[offset:offset + limit]

    def get_news_by_id(self, news_id: str) -> Optional[ResearchNews]:
        """获取单条新闻"""
        news = next((n for n in self._news if n.id == news_id), None)
        if news:
            news.view_count += 1
        return news

    # ==================== 个性化推荐 ====================

    def set_user_preference(self, user_id: str, preference: UserNewsPreference):
        """设置用户偏好"""
        self._user_preferences[user_id] = preference

    def get_personalized_news(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[ResearchNews]:
        """获取个性化新闻推荐"""
        preference = self._user_preferences.get(user_id)
        if not preference:
            # 返回热门新闻
            return sorted(
                self._news,
                key=lambda x: x.impact_score,
                reverse=True
            )[:limit]

        scored_news = []
        for news in self._news:
            score = 0.0

            # 分类匹配
            if news.category in preference.followed_categories:
                score += 10.0

            # 关键词匹配
            for keyword in preference.followed_keywords:
                if keyword.lower() in news.title.lower():
                    score += 5.0
                if keyword.lower() in news.tags:
                    score += 3.0

            # 作者匹配
            for author in preference.followed_authors:
                if author in news.authors:
                    score += 4.0

            # 排除屏蔽词
            for blocked in preference.blocked_keywords:
                if blocked.lower() in news.title.lower():
                    score = -100
                    break

            # 基础热度
            score += news.impact_score * 0.5

            if score > 0:
                scored_news.append((news, score))

        # 按分数排序
        scored_news.sort(key=lambda x: x[1], reverse=True)
        return [n for n, s in scored_news[:limit]]

    def get_daily_digest(self, user_id: str) -> Dict[str, Any]:
        """生成每日摘要"""
        preference = self._user_preferences.get(user_id)

        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_news = [
            n for n in self._news
            if n.published_at >= yesterday
        ]

        if preference:
            # 过滤相关新闻
            relevant_news = []
            for news in recent_news:
                is_relevant = (
                    news.category in preference.followed_categories or
                    any(kw in news.title.lower() for kw in preference.followed_keywords)
                )
                if is_relevant:
                    relevant_news.append(news)
            recent_news = relevant_news

        # 分类汇总
        by_category = {}
        for news in recent_news:
            cat = news.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(news)

        # 热点追踪
        trending = sorted(
            recent_news,
            key=lambda x: x.impact_score,
            reverse=True
        )[:5]

        return {
            "date": datetime.utcnow().isoformat(),
            "total_count": len(recent_news),
            "by_category": {
                k: [{"id": n.id, "title": n.title} for n in v[:3]]
                for k, v in by_category.items()
            },
            "trending": [
                {"id": n.id, "title": n.title, "category": n.category.value}
                for n in trending
            ],
            "recommendations": [
                {"id": n.id, "title": n.title, "summary": n.summary}
                for n in self.get_personalized_news(user_id, limit=3)
            ]
        }

    # ==================== 趋势分析 ====================

    def update_trends(self):
        """更新研究趋势（模拟）"""
        # 从新闻中提取概念
        concept_counts = {}
        for news in self._news[-100:]:  # 最近100条
            for concept in news.related_concepts:
                if concept not in concept_counts:
                    concept_counts[concept] = {
                        "count": 0,
                        "citations": 0,
                        "papers": []
                    }
                concept_counts[concept]["count"] += 1
                concept_counts[concept]["papers"].extend(news.related_papers)

        # 生成趋势数据
        for concept, data in concept_counts.items():
            if data["count"] >= 3:  # 至少3次提及
                self._trends[concept] = ResearchTrend(
                    concept=concept,
                    growth_rate=random.uniform(0.1, 0.5),
                    paper_count=len(set(data["papers"])),
                    citation_count=data["citations"],
                    trending_papers=list(set(data["papers"]))[:5],
                    related_concepts=[],  # 简化处理
                    time_period="7d",
                    last_updated=datetime.utcnow()
                )

    def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门研究主题"""
        trends = sorted(
            self._trends.values(),
            key=lambda x: x.growth_rate * x.paper_count,
            reverse=True
        )

        return [
            {
                "concept": t.concept,
                "growth_rate": round(t.growth_rate, 2),
                "paper_count": t.paper_count,
                "citation_count": t.citation_count,
                "trending_papers": t.trending_papers,
                "last_updated": t.last_updated.isoformat()
            }
            for t in trends[:limit]
        ]

    def get_concept_timeline(
        self,
        concept: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取概念时间线"""
        start_date = datetime.utcnow() - timedelta(days=days)

        timeline = []
        for news in self._news:
            if news.published_at < start_date:
                continue
            if concept.lower() in news.title.lower() or concept in news.related_concepts:
                timeline.append({
                    "date": news.published_at.isoformat(),
                    "title": news.title,
                    "category": news.category.value,
                    "id": news.id
                })

        return sorted(timeline, key=lambda x: x["date"])

    # ==================== 行业动态 ====================

    def get_industry_updates(self, sector: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取行业动态"""
        updates = [
            n for n in self._news
            if n.category in [NewsCategory.INDUSTRY, NewsCategory.FUNDING]
        ]

        if sector:
            updates = [
                n for n in updates
                if sector.lower() in n.title.lower() or sector in n.tags
            ]

        return [
            {
                "id": n.id,
                "title": n.title,
                "summary": n.summary,
                "published_at": n.published_at.isoformat(),
                "source": n.source.value
            }
            for n in sorted(updates, key=lambda x: x.published_at, reverse=True)[:20]
        ]

    def get_policy_updates(self) -> List[Dict[str, Any]]:
        """获取政策更新"""
        policies = [n for n in self._news if n.category == NewsCategory.POLICY]

        return [
            {
                "id": n.id,
                "title": n.title,
                "summary": n.summary,
                "published_at": n.published_at.isoformat(),
                "impact_level": "high" if n.impact_score > 8 else "medium"
            }
            for n in sorted(policies, key=lambda x: x.published_at, reverse=True)[:10]
        ]


# 单例
_news_service: Optional[ResearchNewsService] = None


def get_news_service() -> ResearchNewsService:
    """获取新闻服务单例"""
    global _news_service
    if _news_service is None:
        _news_service = ResearchNewsService()
    return _news_service


import random  # 用于模拟数据
