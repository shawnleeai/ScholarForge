"""
PDF解析服务数据模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PDFMetadata(BaseModel):
    """PDF元数据"""
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    doi: Optional[str] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    pages: Optional[int] = None
    language: str = "zh"


class Reference(BaseModel):
    """参考文献"""
    id: str
    raw_text: str
    authors: List[str] = Field(default_factory=list)
    title: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    citation_count: Optional[int] = None


class Figure(BaseModel):
    """图表"""
    id: str
    type: str = "figure"  # "figure" | "table"
    caption: Optional[str] = None
    page_number: int
    bbox: Optional[Dict[str, float]] = None  # 边界框坐标
    ocr_text: Optional[str] = None
    description: Optional[str] = None


class Section(BaseModel):
    """章节"""
    title: str
    content: str
    level: int = 1  # 标题级别
    page_start: Optional[int] = None
    page_end: Optional[int] = None


class PDFContent(BaseModel):
    """PDF解析内容"""
    full_text: str
    sections: List[Section] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)
    figures: List[Figure] = Field(default_factory=list)
    metadata: PDFMetadata = Field(default_factory=PDFMetadata)


class AIAnalysisResult(BaseModel):
    """AI分析结果"""
    summary: str
    key_points: List[str] = Field(default_factory=list)
    methodology: Optional[Dict[str, Any]] = None
    research_gaps: List[str] = Field(default_factory=list)
    writing_suggestions: List[str] = Field(default_factory=list)
    keywords_extracted: List[str] = Field(default_factory=list)


class PDFParseTask(BaseModel):
    """PDF解析任务"""
    task_id: str
    status: str = "pending"  # pending | processing | completed | failed
    file_name: str
    file_size: int
    file_path: Optional[str] = None
    content: Optional[PDFContent] = None
    ai_analysis: Optional[AIAnalysisResult] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None


class PDFParseRequest(BaseModel):
    """PDF解析请求"""
    enable_ai_analysis: bool = True
    extract_references: bool = True
    extract_figures: bool = False
    language: str = "auto"


class PDFParseResponse(BaseModel):
    """PDF解析响应"""
    task_id: str
    status: str
    message: str
    estimated_seconds: int = 30
