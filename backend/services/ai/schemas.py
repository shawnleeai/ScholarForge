"""
AI 服务数据模式
Pydantic 模型用于请求/响应验证
"""

import uuid
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class WritingTaskType(str, Enum):
    """写作任务类型"""

    CONTINUE = "continue"  # 续写
    REWRITE = "rewrite"    # 改写
    POLISH = "polish"      # 润色
    EXPAND = "expand"      # 扩写
    SUMMARIZE = "summarize"  # 总结
    TRANSLATE = "translate"  # 翻译


class LLMProvider(str, Enum):
    """LLM 提供商"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CHATGLM = "chatglm"


# ============== 写作助手模式 ==============

class WritingRequest(BaseModel):
    """写作请求"""

    task_type: WritingTaskType
    text: Optional[str] = Field(None, description="输入文本（续写时为前文）")
    context: Optional[str] = Field(None, description="上下文信息")
    paper_id: Optional[uuid.UUID] = None
    section_id: Optional[uuid.UUID] = None

    # 生成参数
    max_tokens: int = Field(default=500, ge=50, le=4000)
    temperature: float = Field(default=0.7, ge=0, le=1)
    provider: Optional[LLMProvider] = None

    # 翻译参数
    source_language: Optional[str] = None
    target_language: Optional[str] = None


class WritingResponse(BaseModel):
    """写作响应"""

    generated_text: str
    task_type: WritingTaskType
    provider: str
    tokens_used: int
    suggestions: Optional[List[str]] = None


class ContinueWritingRequest(BaseModel):
    """续写请求"""

    context: str = Field(..., description="前文内容")
    style: Optional[str] = Field(default="academic", description="写作风格")
    max_tokens: int = Field(default=500, ge=50, le=2000)


class PolishRequest(BaseModel):
    """润色请求"""

    text: str = Field(..., description="待润色文本")
    style: str = Field(default="academic")  # academic, formal, casual
    language: str = Field(default="zh")  # zh, en


class TranslateRequest(BaseModel):
    """翻译请求"""

    text: str = Field(..., description="待翻译文本")
    source_language: str = Field(default="zh")
    target_language: str = Field(default="en")


class TranslateResponse(BaseModel):
    """翻译响应"""

    translated_text: str
    source_language: str
    target_language: str


# ============== 智能问答模式 ==============

class QARequest(BaseModel):
    """问答请求"""

    question: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = None
    paper_id: Optional[uuid.UUID] = None


class QAResponse(BaseModel):
    """问答响应"""

    answer: str
    confidence: float
    sources: Optional[List[str]] = None


# ============== 文献分析模式 ==============

class ArticleAnalysisRequest(BaseModel):
    """文献分析请求"""

    article_id: uuid.UUID
    analysis_type: str = Field(default="full")  # full, methodology, findings, references


class ArticleAnalysisResponse(BaseModel):
    """文献分析响应"""

    article_id: uuid.UUID
    research_background: Optional[str] = None
    core_findings: Optional[List[str]] = None
    methodology: Optional[str] = None
    key_figures: Optional[List[str]] = None
    writing_suggestions: Optional[List[str]] = None


# ============== 图表生成模式 ==============

class ChartGenerationRequest(BaseModel):
    """图表生成请求"""

    data: List[dict] = Field(..., description="数据列表")
    chart_type: str = Field(..., description="图表类型")  # bar, line, pie, scatter, etc.
    title: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    options: Optional[dict] = None


class ChartGenerationResponse(BaseModel):
    """图表生成响应"""

    chart_config: dict  # ECharts 配置
    code_snippet: Optional[str] = None  # Python/R 代码
    description: Optional[str] = None


# ============== 协作模式 ==============

class CollaborationMessage(BaseModel):
    """协作消息"""

    type: str  # cursor_move, text_change, selection_change
    paper_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    data: dict
    timestamp: str


class CursorPosition(BaseModel):
    """光标位置"""

    section_id: uuid.UUID
    offset: int
    user_id: uuid.UUID
    user_name: Optional[str] = None
    color: Optional[str] = None


class TextOperation(BaseModel):
    """文本操作"""

    type: str  # insert, delete, replace
    section_id: uuid.UUID
    position: int
    length: Optional[int] = None
    text: Optional[str] = None
    user_id: uuid.UUID
