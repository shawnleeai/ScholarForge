"""
每日论文推荐API路由
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from .paper_feed_models import (
    DailyFeedRequest, DailyFeedResponse, DailyRecommendationResponse,
    RecommendationFeedback, InterestSettingsResponse, UserPreferenceUpdate,
    TrendingPapersRequest, TrendingPaper
)
from .paper_fetcher import PaperFetcher
from .interest_engine import HybridRecommender, InterestProfiler

router = APIRouter(prefix="/api/v1/daily", tags=["daily-recommendation"])


class GenerateRecommendationsRequest(BaseModel):
    """生成推荐请求"""
    user_id: str
    target_date: Optional[date] = None


# 模拟数据存储 (实际项目中使用数据库)
class MockDatabase:
    """模拟数据库 - 实际使用时替换为真实数据库操作"""

    def __init__(self):
        self.users = {}
        self.interests = {}
        self.recommendations = {}
        self.papers = {}
        self.feedback = []

    async def get_user_interest(self, user_id: str):
        from .paper_feed_models import UserInterest
        return self.interests.get(user_id, UserInterest(user_id=user_id))

    async def save_user_interest(self, interest):
        self.interests[interest.user_id] = interest

    async def get_daily_recommendations(self, user_id: str, rec_date: date):
        key = f"{user_id}:{rec_date.isoformat()}"
        return self.recommendations.get(key, [])

    async def save_recommendations(self, user_id: str, rec_date: date, recs):
        key = f"{user_id}:{rec_date.isoformat()}"
        self.recommendations[key] = recs

    async def get_candidate_papers(self, limit: int = 1000):
        return list(self.papers.values())[:limit]

    async def save_papers(self, papers):
        for paper in papers:
            self.papers[paper.id] = paper

    async def get_paper(self, paper_id: str):
        return self.papers.get(paper_id)


mock_db = MockDatabase()
fetcher = PaperFetcher()
recommender = HybridRecommender()
profiler = InterestProfiler()


@router.get("/feed", response_model=DailyFeedResponse)
async def get_daily_feed(
    date: Optional[date] = Query(default=None, description="推荐日期，默认今天"),
    limit: int = Query(default=10, le=50),
    offset: int = Query(default= 0),
    user_id: str = Query(..., description="用户ID")
):
    """获取每日论文推荐"""
    target_date = date or date.today()

    # 获取推荐记录
    recommendations = await mock_db.get_daily_recommendations(user_id, target_date)

    # 如果没有推荐，生成新的
    if not recommendations:
        recommendations = await generate_for_user(user_id, target_date)

    # 应用分页
    total = len(recommendations)
    paged_recommendations = recommendations[offset:offset + limit]

    # 构建响应
    response_items = []
    for rec in paged_recommendations:
        paper = await mock_db.get_paper(rec.paper_id)
        if paper:
            response_items.append(DailyRecommendationResponse(
                id=rec.id,
                paper=paper,
                score=rec.score,
                reason=rec.reason,
                reason_detail=rec.reason_detail,
                rank=rec.rank,
                is_new=not rec.is_clicked and not rec.is_saved
            ))

    return DailyFeedResponse(
        date=target_date,
        total=total,
        recommendations=response_items,
        has_more=offset + len(paged_recommendations) < total
    )


@router.post("/feedback")
async def submit_feedback(
    feedback: RecommendationFeedback
):
    """提交推荐反馈"""
    mock_db.feedback.append(feedback)

    # 更新推荐记录状态
    # 实际项目中应该更新数据库

    return {"success": True, "message": "反馈已记录"}


@router.get("/interests", response_model=InterestSettingsResponse)
async def get_interest_settings(
    user_id: str = Query(..., description="用户ID")
):
    """获取用户兴趣设置"""
    interest = await mock_db.get_user_interest(user_id)

    return InterestSettingsResponse(
        keywords=[k["word"] for k in interest.keywords],
        categories=[c["category"] for c in interest.categories],
        authors=[a["author"] for a in interest.authors],
        excluded_keywords=[],
        min_year=None,
        preferred_sources=[],
        email_frequency="daily",
        last_updated=interest.updated_at
    )


@router.put("/interests")
async def update_interest_settings(
    preferences: UserPreferenceUpdate,
    user_id: str = Query(..., description="用户ID")
):
    """更新用户兴趣设置"""
    interest = await mock_db.get_user_interest(user_id)

    # 更新关键词
    if preferences.keywords is not None:
        for kw in preferences.keywords:
            if not any(k["word"] == kw for k in interest.keywords):
                interest.keywords.append({
                    "word": kw,
                    "weight": 1.0,
                    "source": "explicit"
                })

    # 更新类别
    if preferences.categories is not None:
        for cat in preferences.categories:
            if not any(c["category"] == cat for c in interest.categories):
                interest.categories.append({
                    "category": cat,
                    "weight": 1.0
                })

    # 更新作者
    if preferences.authors is not None:
        for author in preferences.authors:
            if not any(a["author"] == author for a in interest.authors):
                interest.authors.append({
                    "author": author,
                    "weight": 1.0
                })

    interest.updated_at = datetime.now()
    await mock_db.save_user_interest(interest)

    return {"success": True, "message": "兴趣设置已更新"}


@router.get("/trending", response_model=List[TrendingPaper])
async def get_trending_papers(
    category: Optional[str] = Query(None, description="论文类别"),
    days: int = Query(default=7, le=30),
    limit: int = Query(default=10, le=50)
):
    """获取热门论文"""
    # 实际项目中应该基于引用增长、社交媒体提及等计算热度
    # 这里返回模拟数据

    trending = []
    papers = await mock_db.get_candidate_papers(limit=100)

    for i, paper in enumerate(papers[:limit]):
        trending.append(TrendingPaper(
            paper=paper,
            trending_score=1.0 - (i * 0.05),
            mention_count=100 - (i * 5),
            social_media_count=50 - (i * 2)
        ))

    return trending


@router.post("/generate")
async def generate_recommendations(
    request: GenerateRecommendationsRequest,
    background_tasks: BackgroundTasks
):
    """手动触发生成推荐 (管理接口)"""
    target_date = request.target_date or date.today()

    # 后台生成推荐
    background_tasks.add_task(
        generate_for_user,
        request.user_id,
        target_date
    )

    return {
        "success": True,
        "message": f"推荐生成任务已提交，目标日期: {target_date}"
    }


@router.post("/refresh")
async def refresh_recommendations(
    user_id: str = Query(..., description="用户ID")
):
    """刷新今日推荐 (用户主动刷新)"""
    today = date.today()

    # 重新生成
    recommendations = await generate_for_user(user_id, today, force=True)

    return {
        "success": True,
        "count": len(recommendations),
        "message": "推荐已刷新"
    }


async def generate_for_user(
    user_id: str,
    target_date: date,
    force: bool = False
) -> list:
    """为用户生成推荐"""
    # 检查是否已生成
    if not force:
        existing = await mock_db.get_daily_recommendations(user_id, target_date)
        if existing:
            return existing

    # 获取用户兴趣
    user_interest = await mock_db.get_user_interest(user_id)

    # 如果没有兴趣数据，先构建
    if not user_interest.keywords:
        # 从阅读历史等构建兴趣
        # 这里使用模拟数据
        user_interest = await profiler.build_profile(
            user_id=user_id,
            reading_history=[],
            saved_papers=[],
            search_queries=["machine learning", "natural language processing"]
        )
        await mock_db.save_user_interest(user_interest)

    # 获取候选论文
    candidate_papers = await mock_db.get_candidate_papers(limit=1000)

    # 如果候选论文不足，采集新的
    if len(candidate_papers) < 100:
        # 从arXiv采集
        from .paper_fetcher import FetchConfig
        from .paper_feed_models import PaperSource

        config = FetchConfig(
            source=PaperSource.ARXIV,
            categories=["cs.AI", "cs.CL", "cs.LG"],
            keywords=["machine learning", "deep learning", "NLP"],
            max_results=100,
            days_back=7
        )

        _, new_papers = await fetcher.fetch_all(config)
        await mock_db.save_papers(new_papers)

        # 重新获取候选
        candidate_papers = await mock_db.get_candidate_papers(limit=1000)

    # 生成推荐
    recommendations = await recommender.recommend(
        user_id=user_id,
        user_interest=user_interest,
        candidate_papers=candidate_papers,
        top_k=10
    )

    # 保存推荐
    await mock_db.save_recommendations(user_id, target_date, recommendations)

    return recommendations


@router.get("/categories")
async def get_categories():
    """获取支持的论文类别"""
    return {
        "computer_science": [
            {"id": "cs.AI", "name": "Artificial Intelligence", "zh_name": "人工智能"},
            {"id": "cs.CL", "name": "Computation and Language", "zh_name": "计算语言学/NLP"},
            {"id": "cs.CV", "name": "Computer Vision", "zh_name": "计算机视觉"},
            {"id": "cs.LG", "name": "Machine Learning", "zh_name": "机器学习"},
            {"id": "cs.IR", "name": "Information Retrieval", "zh_name": "信息检索"},
            {"id": "cs.DB", "name": "Databases", "zh_name": "数据库"},
            {"id": "cs.SE", "name": "Software Engineering", "zh_name": "软件工程"},
            {"id": "cs.HC", "name": "Human-Computer Interaction", "zh_name": "人机交互"},
        ],
        "statistics": [
            {"id": "stat.ML", "name": "Machine Learning (Statistics)", "zh_name": "机器学习(统计)"},
            {"id": "stat.AP", "name": "Applications", "zh_name": "统计应用"},
        ],
        "biology": [
            {"id": "q-bio.BM", "name": "Biomolecules", "zh_name": "生物分子"},
            {"id": "q-bio.GN", "name": "Genomics", "zh_name": "基因组学"},
            {"id": "q-bio.MN", "name": "Molecular Networks", "zh_name": "分子网络"},
        ]
    }
