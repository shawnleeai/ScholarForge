"""
推荐服务模块
包含每日论文推荐、兴趣建模、推荐算法
"""

from .main import app
from .paper_fetcher import PaperFetcher, ArXivFetcher, SemanticScholarFetcher, PubMedFetcher
from .interest_engine import (
    HybridRecommender,
    ContentBasedRecommender,
    CollaborativeFilteringRecommender,
    InterestProfiler
)
from .paper_feed_models import (
    Paper,
    PaperCreate,
    UserInterest,
    DailyRecommendation,
    DailyRecommendationCreate,
    RecommendationReason,
    PaperSource
)

__all__ = [
    "app",
    # 采集器
    'PaperFetcher',
    'ArXivFetcher',
    'SemanticScholarFetcher',
    'PubMedFetcher',
    # 推荐引擎
    'HybridRecommender',
    'ContentBasedRecommender',
    'CollaborativeFilteringRecommender',
    'InterestProfiler',
    # 模型
    'Paper',
    'PaperCreate',
    'UserInterest',
    'DailyRecommendation',
    'DailyRecommendationCreate',
    'RecommendationReason',
    'PaperSource',
]
