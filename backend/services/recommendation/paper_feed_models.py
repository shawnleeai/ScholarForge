"""
每日论文推荐系统数据模型
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PaperSource(str, Enum):
    """论文来源"""
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    PUBMED = "pubmed"
    IEEE = "ieee"
    CNKI = "cnki"


class RecommendationReason(str, Enum):
    """推荐理由类型"""
    BASED_ON_INTEREST = "based_on_interest"  # 基于兴趣
    BASED_ON_READING = "based_on_reading"    # 基于阅读历史
    TRENDING = "trending"                     # 热门趋势
    FOLLOW_AUTHOR = "follow_author"          # 关注作者
    SIMILAR_TO_SAVED = "similar_to_saved"    # 类似收藏
    KEYWORD_MATCH = "keyword_match"          # 关键词匹配


class PaperBase(BaseModel):
    """论文基础信息"""
    title: str
    abstract: Optional[str] = None
    authors: List[Dict[str, str]] = []  # [{"name": "", "affiliation": ""}]
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pmid: Optional[str] = None


class PaperCreate(PaperBase):
    """创建论文"""
    source: PaperSource
    source_id: str  # 源系统ID
    published_at: Optional[date] = None
    updated_at: Optional[datetime] = None
    categories: List[str] = []
    primary_category: Optional[str] = None
    keywords: List[str] = []
    journal: Optional[str] = None
    year: Optional[int] = None
    citation_count: int = 0
    raw_data: Optional[Dict] = None


class Paper(PaperCreate):
    """论文完整模型"""
    id: str
    fetched_at: datetime
    embedding: Optional[List[float]] = None

    class Config:
        from_attributes = True


class UserInterest(BaseModel):
    """用户兴趣模型"""
    user_id: str
    keywords: List[Dict] = []  # [{"word": "", "weight": 0.5, "source": ""}]
    categories: List[Dict] = []  # [{"category": "", "weight": 0.5}]
    authors: List[Dict] = []  # [{"author": "", "weight": 0.5}]
    journals: List[Dict] = []  # [{"journal": "", "weight": 0.5}]
    reading_patterns: Dict = {}  # 阅读模式分析
    updated_at: datetime = Field(default_factory=datetime.now)


class PaperSourceConfig(BaseModel):
    """论文源配置"""
    source: PaperSource
    enabled: bool = True
    fetch_interval_hours: int = 6  # 采集间隔
    categories: List[str] = []  # 关注类别
    keywords: List[str] = []  # 关注关键词
    max_papers_per_fetch: int = 100
    rate_limit_per_minute: int = 30
    last_fetch_at: Optional[datetime] = None


class DailyRecommendationCreate(BaseModel):
    """创建每日推荐"""
    user_id: str
    paper_id: str
    score: float = Field(..., ge=0, le=1)
    reason: RecommendationReason
    reason_detail: str  # 推荐理由描述
    rank: int  # 排名
    recommend_date: date


class DailyRecommendation(DailyRecommendationCreate):
    """每日推荐记录"""
    id: str
    created_at: datetime

    # 用户反馈
    is_sent: bool = False  # 是否已发送邮件
    sent_at: Optional[datetime] = None
    is_clicked: bool = False
    clicked_at: Optional[datetime] = None
    is_saved: bool = False
    saved_at: Optional[datetime] = None
    is_dismissed: bool = False
    dismissed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DailyRecommendationResponse(BaseModel):
    """每日推荐响应"""
    id: str
    paper: Paper
    score: float
    reason: RecommendationReason
    reason_detail: str
    rank: int
    is_new: bool  # 是否新推荐


class RecommendationFeedback(BaseModel):
    """推荐反馈"""
    recommendation_id: str
    action: str  # click, save, dismiss, share
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Optional[Dict] = None  # 额外上下文


class UserPreferenceUpdate(BaseModel):
    """用户偏好更新"""
    keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    min_year: Optional[int] = None
    preferred_sources: Optional[List[PaperSource]] = None
    email_frequency: str = "daily"  # daily, weekly, never


class InterestSettingsResponse(BaseModel):
    """兴趣设置响应"""
    keywords: List[str]
    categories: List[str]
    authors: List[str]
    excluded_keywords: List[str]
    min_year: Optional[int]
    preferred_sources: List[PaperSource]
    email_frequency: str
    last_updated: datetime


class DailyFeedRequest(BaseModel):
    """每日订阅请求"""
    user_id: str
    date: Optional[date] = None  # 默认今天
    limit: int = Field(default=10, le=50)
    offset: int = 0


class DailyFeedResponse(BaseModel):
    """每日订阅响应"""
    date: date
    total: int
    recommendations: List[DailyRecommendationResponse]
    has_more: bool


class TrendingPapersRequest(BaseModel):
    """热门论文请求"""
    category: Optional[str] = None
    days: int = Field(default=7, le=30)
    limit: int = Field(default=10, le=50)


class TrendingPaper(BaseModel):
    """热门论文"""
    paper: Paper
    trending_score: float
    mention_count: int
    social_media_count: int


class FetchResult(BaseModel):
    """采集结果"""
    source: PaperSource
    fetched_count: int
    new_count: int
    updated_count: int
    failed_count: int
    duration_seconds: float
    timestamp: datetime
