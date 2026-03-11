"""
文献综述生成服务 - 数据模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ReviewLength(str, Enum):
    """综述长度"""
    SHORT = "short"      # 短篇 (~1000字)
    MEDIUM = "medium"    # 中篇 (~3000字)
    LONG = "long"        # 长篇 (~5000字)


class ReviewFocus(str, Enum):
    """综述聚焦领域"""
    GENERAL = "general"           # 综合
    METHODOLOGY = "methodology"   # 方法论
    FINDINGS = "findings"         # 研究发现
    TRENDS = "trends"             # 研究趋势
    GAPS = "gaps"                 # 研究空白


class LiteratureReviewRequest(BaseModel):
    """文献综述生成请求"""
    article_ids: List[str] = Field(..., min_items=2, max_items=50, description="文献ID列表")
    focus_area: ReviewFocus = Field(default=ReviewFocus.GENERAL, description="综述聚焦领域")
    output_length: ReviewLength = Field(default=ReviewLength.MEDIUM, description="输出长度")
    language: str = Field(default="zh", description="输出语言")
    include_citations: bool = Field(default=True, description="是否包含引用")
    include_references: bool = Field(default=True, description="是否包含参考文献列表")
    custom_prompt: Optional[str] = Field(default=None, description="自定义提示词")


class ArticleSummary(BaseModel):
    """文献摘要信息"""
    id: str
    title: str
    authors: List[str]
    year: Optional[int]
    abstract: str
    key_findings: List[str]
    methodology: Optional[str]
    relevance_score: float = Field(ge=0, le=1)


class ThemeAnalysis(BaseModel):
    """主题分析"""
    theme: str
    description: str
    related_articles: List[str]  # 文章ID列表
    key_points: List[str]


class ComparisonPoint(BaseModel):
    """对比点"""
    aspect: str
    comparisons: Dict[str, str]  # {文章ID: 描述}
    consensus: Optional[str]
    differences: List[str]


class LiteratureReviewSection(BaseModel):
    """综述章节"""
    title: str
    content: str
    subsections: List["LiteratureReviewSection"] = Field(default_factory=list)
    cited_articles: List[str] = Field(default_factory=list)


class LiteratureReview(BaseModel):
    """文献综述结果"""
    id: str
    title: str
    abstract: str
    sections: List[LiteratureReviewSection]
    themes: List[ThemeAnalysis]
    comparisons: List[ComparisonPoint]
    research_gaps: List[str]
    future_directions: List[str]
    references: List[Dict[str, Any]]
    generated_at: datetime
    word_count: int
    metadata: Dict[str, Any]


class ReviewGenerationTask(BaseModel):
    """综述生成任务"""
    task_id: str
    status: str = "pending"  # pending | processing | completed | failed
    request: LiteratureReviewRequest
    result: Optional[LiteratureReview] = None
    progress: int = Field(ge=0, le=100, default=0)
    current_step: str = ""
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ReviewOutline(BaseModel):
    """综述大纲"""
    title: str
    sections: List[Dict[str, Any]]
    estimated_word_count: int
    key_themes: List[str]


class QuickReviewRequest(BaseModel):
    """快速综述请求"""
    topic: str
    keywords: List[str] = Field(default_factory=list)
    max_articles: int = Field(default=10, ge=1, le=20)
    focus_area: ReviewFocus = ReviewFocus.GENERAL
    output_length: ReviewLength = ReviewLength.MEDIUM
