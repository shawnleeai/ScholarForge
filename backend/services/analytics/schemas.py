"""
学术分析数据模型
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CitationMetrics(BaseModel):
    """引用指标"""
    total_citations: int = 0
    citations_per_year: float = 0.0
    h_index: int = 0
    i10_index: int = 0  # 被引用10次以上的论文数
    g_index: int = 0  # g指数


class PublicationMetrics(BaseModel):
    """发表指标"""
    total_publications: int = 0
    first_author_count: int = 0
    corresponding_author_count: int = 0
    solo_author_count: int = 0
    collaborative_count: int = 0
    publications_by_year: Dict[int, int] = Field(default_factory=dict)
    publications_by_type: Dict[str, int] = Field(default_factory=dict)


class ImpactMetrics(BaseModel):
    """影响力指标"""
    average_citations_per_paper: float = 0.0
    highly_cited_papers: int = 0  # 引用超过平均值2倍的论文
    hot_papers: int = 0  # 近期高引用论文
    citation_velocity: float = 0.0  # 引用增长速度
    field_weighted_citation_impact: float = 0.0  # 领域加权引用影响力


class ResearchTrend(BaseModel):
    """研究趋势"""
    year: int
    publication_count: int
    citation_count: int
    h_index: int
    top_keywords: List[str]


class CollaborationNetwork(BaseModel):
    """合作网络"""
    author_name: str
    collaboration_count: int
    first_collaboration_year: Optional[int]
    last_collaboration_year: Optional[int]
    joint_publications: List[str]  # 论文标题列表


class VenueMetrics(BaseModel):
    """期刊/会议指标"""
    venue_name: str
    publication_count: int
    total_citations: int
    average_citations: float
    impact_factor: Optional[float]
    h_index: int


class AcademicImpactAnalysis(BaseModel):
    """学术影响力分析结果"""
    author_id: str
    author_name: str
    analysis_date: datetime

    # 各项指标
    citations: CitationMetrics
    publications: PublicationMetrics
    impact: ImpactMetrics

    # 历史趋势
    yearly_trends: List[ResearchTrend]

    # 合作网络
    top_collaborators: List[CollaborationNetwork]

    # 发表 venues
    venue_distribution: List[VenueMetrics]

    # 研究领域
    research_fields: List[Dict[str, Any]]

    # 全球排名（估算）
    estimated_percentile: Optional[float]

    # 与领域平均值对比
    comparison_with_field: Dict[str, Any]


class PaperAnalytics(BaseModel):
    """单篇论文分析"""
    paper_id: str
    title: str
    citation_count: int
    citation_trend: List[Dict[str, Any]]  # 每年的引用数
    relative_citation_ratio: float  # 相对于同年同领域论文的引用比
    altmetrics_score: Optional[float]  # 替代计量分数
    social_mentions: int = 0
    download_count: Optional[int]


class ResearcherProfile(BaseModel):
    """研究者档案"""
    author_id: str
    name: str
    institution: Optional[str]
    research_interests: List[str]
    career_start_year: Optional[int]

    # 汇总指标
    metrics: CitationMetrics
    total_publications: int

    # 代表性论文
    top_papers: List[PaperAnalytics]

    # 活跃程度
    recent_activity_score: float  # 近期活跃度分数
    collaboration_diversity: float  # 合作多样性


class TrendAnalysisRequest(BaseModel):
    """趋势分析请求"""
    keywords: List[str]
    start_year: int = Field(default=2015)
    end_year: int = Field(default_factory=lambda: datetime.now().year)
    fields: Optional[List[str]] = None


class TrendAnalysisResult(BaseModel):
    """趋势分析结果"""
    keywords: List[str]
    yearly_data: List[Dict[str, Any]]  # 每年的论文数、引用数等
    emerging_topics: List[str]
    declining_topics: List[str]
    hot_researchers: List[Dict[str, Any]]
    hot_papers: List[Dict[str, Any]]


class ComparativeAnalysis(BaseModel):
    """对比分析"""
    base_author: str
    comparison_authors: List[str]
    metrics_comparison: Dict[str, Dict[str, float]]  # {指标: {作者: 值}}
    relative_performance: Dict[str, float]  # 相对于基准的表现
