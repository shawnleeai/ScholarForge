"""
期刊匹配服务数据模型
Pydantic 模型定义
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class JournalType(str, Enum):
    """期刊类型"""
    JOURNAL = "journal"         # 期刊
    CONFERENCE = "conference"   # 会议
    WORKSHOP = "workshop"       # 研讨会
    SYMPOSIUM = "symposium"     # 专题讨论会


class JournalRanking(str, Enum):
    """期刊等级"""
    SCI = "sci"                 # SCI 期刊
    SSCI = "ssci"               # SSCI 期刊
    EI = "ei"                   # EI 期刊
    CSSCI = "cssci"             # CSSCI 期刊
    CORE = "core"               # 核心期刊
    ORDINARY = "ordinary"       # 普通期刊


class MatchStatus(str, Enum):
    """匹配状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============== 期刊模型 ==============

class JournalBase(BaseModel):
    """期刊基础信息"""
    id: str
    name: str
    issn: Optional[str] = None
    publisher: Optional[str] = None
    subject_areas: List[str] = []
    journal_type: JournalType = JournalType.JOURNAL
    ranking: Optional[JournalRanking] = None

    # 指标
    impact_factor: Optional[float] = None
    h_index: Optional[int] = None
    sjr: Optional[float] = None

    # 投稿信息
    submission_url: Optional[str] = None
    review_cycle_days: Optional[int] = None
    acceptance_rate: Optional[float] = None
    publication_fee: Optional[float] = None

    # 开放获取
    is_open_access: bool = False
    apc: Optional[float] = None


class JournalDetail(JournalBase):
    """期刊详细信息"""
    description: Optional[str] = None
    scope: Optional[str] = None
    language: str = "zh"
    keywords: List[str] = []
    indexed_in: List[str] = []

    # 附加信息
    publication_frequency: Optional[str] = None
    editorial_board: Optional[List[Dict]] = None
    recent_papers: Optional[List[Dict]] = None


# ============== 匹配请求 ==============

class MatchRequest(BaseModel):
    """期刊匹配请求"""
    paper_id: uuid.UUID = Field(..., description="论文ID")
    title: Optional[str] = Field(None, description="论文标题")
    abstract: Optional[str] = Field(None, description="摘要")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    field: Optional[str] = Field(None, description="研究领域")
    requirements: Optional[Dict[str, Any]] = Field(None, description="投稿要求")


class MatchResult(BaseModel):
    """单个匹配结果"""
    journal: JournalBase
    match_score: float = Field(..., ge=0, le=100, description="匹配分数 0-100")
    match_reasons: List[str] = []
    recommendations: List[str] = []
    estimated_acceptance_rate: Optional[float] = None
    estimated_review_time: Optional[int] = None  # 天数


class MatchResponse(BaseModel):
    """匹配响应"""
    match_id: str
    status: MatchStatus
    results: List[MatchResult] = []
    total_journals_analyzed: int = 0
    processing_time_ms: Optional[float] = None
    created_at: datetime


# ============== 投稿建议 ==============

class SubmissionSuggestion(BaseModel):
    """投稿建议"""
    top_journals: List[MatchResult]
    alternative_journals: List[MatchResult]
    tips: List[str]
    warnings: List[str] = []


class JournalComparison(BaseModel):
    """期刊对比"""
    journals: List[JournalBase]
    comparison_matrix: Dict[str, Dict[str, Any]]


# ============== 投稿记录 ==============

class SubmissionRecord(BaseModel):
    """投稿记录"""
    id: str
    paper_id: str
    journal_id: str
    journal_name: str
    status: str
    manuscript_id: Optional[str] = None
    submitted_at: Optional[datetime] = None
    first_decision_at: Optional[datetime] = None
    final_decision_at: Optional[datetime] = None
    decision: Optional[str] = None
    notes: Optional[str] = None


class SubmissionRecordCreate(BaseModel):
    """创建投稿记录"""
    paper_id: uuid.UUID
    journal_id: uuid.UUID
    manuscript_id: Optional[str] = None
    notes: Optional[str] = None


class SubmissionRecordUpdate(BaseModel):
    """更新投稿记录"""
    status: Optional[str] = None
    manuscript_id: Optional[str] = None
    first_decision_at: Optional[datetime] = None
    final_decision_at: Optional[datetime] = None
    decision: Optional[str] = None
    notes: Optional[str] = None


# ============== 期刊筛选 ==============

class JournalFilter(BaseModel):
    """期刊筛选条件"""
    subject_area: Optional[str] = None
    journal_type: Optional[JournalType] = None
    ranking: Optional[JournalRanking] = None
    min_impact_factor: Optional[float] = None
    max_impact_factor: Optional[float] = None
    min_acceptance_rate: Optional[float] = None
    max_acceptance_rate: Optional[float] = None
    max_publication_fee: Optional[float] = None
    open_access_only: bool = False
    search_query: Optional[str] = None


# ============== 统计 ==============

class JournalStats(BaseModel):
    """期刊统计"""
    total_journals: int
    by_type: Dict[str, int]
    by_ranking: Dict[str, int]
    by_subject: Dict[str, int]
    average_impact_factor: float
    average_acceptance_rate: float
