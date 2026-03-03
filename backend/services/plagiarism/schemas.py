"""
查重服务数据模型
Pydantic 模型定义
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    """检测状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SeverityLevel(str, Enum):
    """重复严重程度"""
    LOW = "low"           # < 10%
    MEDIUM = "medium"     # 10-20%
    HIGH = "high"         # 20-30%
    CRITICAL = "critical" # > 30%


class SuggestionType(str, Enum):
    """建议类型"""
    REPHRASE = "rephrase"       # 改写
    REWRITE = "rewrite"         # 重写
    CITE = "cite"               # 添加引用
    STRUCTURE = "structure"     # 调整结构
    REPLACE = "replace"         # 替换词汇
    EXPAND = "expand"           # 扩展内容


# ============== 查重结果 ==============

class SimilarityMatch(BaseModel):
    """相似片段"""
    text: str
    start_index: int
    end_index: int
    similarity: float
    source_id: str
    source_title: Optional[str] = None
    source_url: Optional[str] = None


class SimilaritySource(BaseModel):
    """相似来源"""
    id: str
    title: str
    type: str
    url: Optional[str] = None
    similarity: float = 0.0
    match_count: int = 0


class PlagiarismCheckResult(BaseModel):
    """查重结果"""
    overall_similarity: float
    internet_similarity: float
    publications_similarity: float
    student_papers_similarity: float
    matches: List[SimilarityMatch]
    sources: List[SimilaritySource]
    report_url: Optional[str] = None


# ============== 检测请求 ==============

class PlagiarismCheckRequest(BaseModel):
    """查重检测请求"""
    paper_id: Optional[uuid.UUID] = Field(None, description="论文ID")
    text: Optional[str] = Field(None, description="待检测文本")
    section_ids: Optional[List[uuid.UUID]] = Field(None, description="指定章节ID列表")
    check_type: str = Field("full", description="检测类型: full/fulltext/paragraph")
    exclude_references: bool = Field(True, description="排除参考文献")
    exclude_quotes: bool = Field(True, description="排除引用")


class PlagiarismCheckCreate(BaseModel):
    """创建查重任务"""
    paper_id: Optional[str] = None
    task_name: Optional[str] = None
    engine: str = Field(default="local", pattern="^(local|turnitin|paperpass|mock)$")


class PlagiarismCheckResponse(BaseModel):
    """查重检测响应"""
    id: str
    user_id: str
    paper_id: Optional[str] = None
    task_name: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    status: CheckStatus
    engine: str
    overall_similarity: Optional[float]
    internet_similarity: Optional[float]
    publications_similarity: Optional[float]
    student_papers_similarity: Optional[float]
    matches: Optional[List[Dict[str, Any]]]
    sources: Optional[List[Dict[str, Any]]]
    report_url: Optional[str]
    error_message: Optional[str]
    submitted_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: int = 0

    class Config:
        from_attributes = True


class PlagiarismCheckListResponse(BaseModel):
    """查重任务列表响应"""
    items: List[PlagiarismCheckResponse]
    total: int


# ============== 相似段落 ==============

class SimilaritySegment(BaseModel):
    """相似段落"""
    id: str
    source_text: str = Field(..., description="原文内容")
    similar_text: str = Field(..., description="相似内容")
    similarity: float = Field(..., ge=0, le=1, description="相似度")
    source_title: Optional[str] = None
    source_author: Optional[str] = None
    source_url: Optional[str] = None
    position: Dict[str, int] = Field(default_factory=dict, description="位置信息")
    section_id: Optional[str] = None


# ============== 章节报告 ==============

class SectionReport(BaseModel):
    """章节报告"""
    section_id: str
    section_title: str
    word_count: int
    similarity_rate: float
    similar_segments: List[SimilaritySegment] = []


# ============== 查重报告 ==============

class PlagiarismReport(BaseModel):
    """查重报告"""
    check_id: str
    paper_id: Optional[str] = None
    overall_similarity: float = Field(..., ge=0, le=1, description="总体相似度")
    severity: SeverityLevel
    total_words: int
    checked_words: int
    similar_word_count: int
    section_reports: List[SectionReport] = []
    similar_sources: List[Dict[str, Any]] = []
    created_at: datetime
    expires_at: Optional[datetime] = None


# ============== 降重建议 ==============

class RewordSuggestion(BaseModel):
    """改写建议"""
    original_text: str
    suggested_text: str
    suggestion_type: SuggestionType
    confidence: float = Field(..., ge=0, le=1)
    reason: str
    alternatives: List[str] = []


class SegmentSuggestions(BaseModel):
    """段落降重建议"""
    segment_id: str
    original_text: str
    suggestions: List[RewordSuggestion] = []


class ReducePlagiarismRequest(BaseModel):
    """降重请求"""
    check_id: str
    segment_ids: Optional[List[str]] = Field(None, description="指定段落ID")
    max_suggestions: int = Field(3, description="每段最大建议数")


class ReducePlagiarismResponse(BaseModel):
    """降重响应"""
    check_id: str
    total_segments: int
    processed_segments: int
    suggestions: List[SegmentSuggestions] = []
    tips: List[str] = []


# ============== 白名单 ==============

class WhitelistCreate(BaseModel):
    """创建白名单条目"""
    paper_id: Optional[str] = None
    content: str = Field(..., min_length=10)
    reason: Optional[str] = None
    source: Optional[str] = None


class WhitelistResponse(BaseModel):
    """白名单响应"""
    id: str
    user_id: str
    paper_id: Optional[str]
    content: str
    content_hash: str
    reason: Optional[str]
    source: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 设置 ==============

class PlagiarismSettings(BaseModel):
    """查重设置"""
    default_engine: str = Field(default="local", pattern="^(local|turnitin|paperpass|mock)$")
    exclude_bibliography: bool = True
    exclude_quotes: bool = False
    exclude_small_sources: bool = True
    small_source_threshold: int = Field(default=8, ge=5, le=50)
    sensitivity: str = Field(default="medium", pattern="^(low|medium|high)$")
    notify_on_complete: bool = True
    notify_threshold: int = Field(default=30, ge=0, le=100)


class PlagiarismSettingsUpdate(BaseModel):
    """更新查重设置"""
    default_engine: Optional[str] = Field(default=None, pattern="^(local|turnitin|paperpass|mock)$")
    exclude_bibliography: Optional[bool] = None
    exclude_quotes: Optional[bool] = None
    exclude_small_sources: Optional[bool] = None
    small_source_threshold: Optional[int] = Field(default=None, ge=5, le=50)
    sensitivity: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")
    notify_on_complete: Optional[bool] = None
    notify_threshold: Optional[int] = Field(default=None, ge=0, le=100)


# ============== 历史记录 ==============

class PlagiarismHistoryResponse(BaseModel):
    """查重历史响应"""
    id: str
    check_id: str
    user_id: str
    paper_id: Optional[str]
    version: int
    similarity: float
    report_url: Optional[str]
    task_name: Optional[str]
    engine: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CheckHistory(BaseModel):
    """检测历史"""
    check_id: str
    paper_id: str
    paper_title: Optional[str] = None
    similarity_rate: float
    status: CheckStatus
    created_at: datetime


class CheckHistoryList(BaseModel):
    """检测历史列表"""
    items: List[CheckHistory]
    total: int
    page: int
    page_size: int


# ============== 统计 ==============

class PlagiarismStatistics(BaseModel):
    """查重统计"""
    total_checks: int
    completed_checks: int
    failed_checks: int
    average_similarity: float
    max_similarity: float
    min_similarity: float
    recent_trend: List[Dict[str, Any]]


# ============== 学术规范检查 ==============

class AcademicIssue(BaseModel):
    """学术规范问题"""
    id: str
    issue_type: str  # colloquial, informal, structure, citation
    position: Dict[str, int]
    original_text: str
    issue_description: str
    suggestion: str
    severity: str  # low, medium, high


class AcademicCheckResult(BaseModel):
    """学术规范检查结果"""
    paper_id: str
    issues: List[AcademicIssue] = []
    score: float = Field(..., ge=0, le=100)
    summary: Dict[str, int] = {}
