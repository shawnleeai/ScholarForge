"""
选题助手数据模型
Pydantic 模型定义
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class FeasibilityLevel(str, Enum):
    """可行性等级"""
    HIGH = "high"         # 高可行性
    MEDIUM = "medium"     # 中等可行性
    LOW = "low"           # 低可行性
    RISKY = "risky"       # 风险较高


class ResearchGapType(str, Enum):
    """研究空白类型"""
    METHOD = "method"             # 方法空白
    APPLICATION = "application"   # 应用空白
    THEORY = "theory"             # 理论空白
    CONTEXT = "context"           # 情境空白
    POPULATION = "population"     # 人群空白


# ============== 选题请求 ==============

class TopicSuggestionRequest(BaseModel):
    """选题建议请求"""
    field: str = Field(..., description="研究领域")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    interests: Optional[List[str]] = Field(None, description="研究兴趣")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")
    degree_level: str = Field("master", description="学位级别: bachelor/master/doctor")
    time_limit_months: Optional[int] = Field(None, description="时间限制（月）")


class TopicAnalysisRequest(BaseModel):
    """选题分析请求"""
    topic: str = Field(..., description="选题标题")
    description: Optional[str] = Field(None, description="选题描述")
    field: Optional[str] = Field(None, description="所属领域")


class ProposalGenerateRequest(BaseModel):
    """开题报告生成请求"""
    topic: str = Field(..., description="选题")
    field: str = Field(..., description="研究领域")
    degree_level: str = Field("master", description="学位级别")
    university: Optional[str] = Field(None, description="学校")
    supervisor: Optional[str] = Field(None, description="导师姓名")


# ============== 选题建议 ==============

class ResearchGap(BaseModel):
    """研究空白"""
    gap_type: ResearchGapType
    description: str
    significance: str
    supporting_evidence: List[str] = []


class TopicIdea(BaseModel):
    """选题想法"""
    id: str
    title: str
    description: str
    keywords: List[str]
    field: str
    sub_field: Optional[str] = None

    # 可行性
    feasibility_level: FeasibilityLevel
    feasibility_score: float = Field(..., ge=0, le=100)

    # 研究空白
    research_gaps: List[ResearchGap] = []

    # 资源需求
    required_methods: List[str] = []
    required_data: List[str] = []
    required_tools: List[str] = []

    # 时间估算
    estimated_duration_months: int

    # 风险
    risks: List[str] = []
    mitigation_strategies: List[str] = []

    # 参考
    related_papers: List[str] = []
    recent_trends: List[str] = []


class TopicSuggestionResponse(BaseModel):
    """选题建议响应"""
    suggestions: List[TopicIdea]
    total_count: int
    generated_at: datetime


# ============== 可行性分析 ==============

class ResourceRequirement(BaseModel):
    """资源需求"""
    resource_type: str
    description: str
    availability: str  # easy/medium/hard
    estimated_cost: Optional[str] = None


class TimelineMilestone(BaseModel):
    """时间线里程碑"""
    phase: str
    tasks: List[str]
    duration_weeks: int
    dependencies: List[str] = []


class FeasibilityAnalysis(BaseModel):
    """可行性分析结果"""
    topic: str
    overall_score: float = Field(..., ge=0, le=100)
    level: FeasibilityLevel

    # 各维度评分
    academic_value_score: float
    innovation_score: float
    resource_availability_score: float
    time_feasibility_score: float
    risk_score: float

    # 详细分析
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]

    # 资源需求
    resource_requirements: List[ResourceRequirement]

    # 时间规划
    timeline: List[TimelineMilestone]

    # 建议
    recommendations: List[str]
    alternative_topics: List[str] = []

    # 研究空白
    research_gaps: List[ResearchGap]


# ============== 开题报告 ==============

class ResearchQuestion(BaseModel):
    """研究问题"""
    id: str
    question: str
    sub_questions: List[str] = []


class ResearchMethod(BaseModel):
    """研究方法"""
    method_type: str
    description: str
    data_source: Optional[str] = None
    analysis_approach: Optional[str] = None


class ProposalSection(BaseModel):
    """开题报告章节"""
    title: str
    content: str
    word_count: int


class ProposalDocument(BaseModel):
    """开题报告文档"""
    topic: str
    field: str
    degree_level: str

    # 各章节
    sections: List[ProposalSection]

    # 研究框架
    research_questions: List[ResearchQuestion]
    research_methods: List[ResearchMethod]

    # 时间规划
    gantt_chart_data: Optional[Dict[str, Any]] = None

    # 参考文献
    references: List[str] = []

    # 元信息
    generated_at: datetime
    total_words: int


class ProposalOutline(BaseModel):
    """开题报告大纲"""
    title: str
    background: str
    objectives: str
    research_questions: List[ResearchQuestion]
    research_methods: List[ResearchMethod]
    expected_outcomes: List[str]
    innovation_points: List[str]
    timeline: List[Dict[str, Any]]
    references: List[str]
    generated_at: datetime
    total_words: int = 0


# ============== 趋势分析 ==============

class TrendData(BaseModel):
    """趋势数据点"""
    year: int
    count: int
    growth_rate: Optional[float] = None


class ResearchTrend(BaseModel):
    """研究趋势"""
    keyword: str
    trend_data: List[TrendData]
    current_hotness: float
    predicted_trend: str  # rising/stable/declining
    related_keywords: List[str]


class TrendAnalysisResponse(BaseModel):
    """趋势分析响应"""
    field: str
    trends: List[ResearchTrend]
    hot_topics: List[str]
    emerging_topics: List[str]
    declining_topics: List[str]
    analyzed_at: datetime


# ============== 研究计划 ==============

class ResearchTask(BaseModel):
    """研究任务"""
    id: str
    title: str
    description: str
    phase: str
    start_week: int
    end_week: int
    dependencies: List[str] = []
    status: str = "pending"
    priority: str = "medium"


class ResearchPlan(BaseModel):
    """研究计划"""
    topic: str
    total_weeks: int
    phases: List[Dict[str, Any]]
    tasks: List[ResearchTask]
    milestones: List[Dict[str, Any]]
    gantt_chart: Optional[Dict[str, Any]] = None
