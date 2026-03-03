"""
文献数据模式
Pydantic 模型用于请求/响应验证
"""

import uuid
from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, Field


# ============== 基础模式 ==============

class AuthorInfo(BaseModel):
    """作者信息"""

    name: str
    orcid: Optional[str] = None
    affiliation: Optional[str] = None


class ArticleBase(BaseModel):
    """文献基础模式"""

    title: str
    authors: Optional[List[AuthorInfo]] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None


class ArticleResponse(BaseModel):
    """文献响应模式"""

    id: uuid.UUID
    doi: Optional[str] = None
    title: str
    authors: Optional[List[dict]] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None

    # 来源信息
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    source_db: Optional[str] = None

    # 出版信息
    publication_year: Optional[int] = None
    publication_date: Optional[date] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    issn: Optional[str] = None
    isbn: Optional[str] = None

    # 指标
    citation_count: int = 0
    impact_factor: Optional[float] = None

    # 链接
    pdf_url: Optional[str] = None
    source_url: Optional[str] = None

    # 时间戳
    indexed_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArticleBrief(BaseModel):
    """文献简要信息（用于列表展示）"""

    id: uuid.UUID
    doi: Optional[str] = None
    title: str
    authors: Optional[List[dict]] = None
    source_name: Optional[str] = None
    publication_year: Optional[int] = None
    citation_count: int = 0
    source_db: Optional[str] = None

    model_config = {"from_attributes": True}


# ============== 搜索模式 ==============

class SearchRequest(BaseModel):
    """搜索请求"""

    query: str = Field(..., min_length=1, max_length=500)
    sources: Optional[List[str]] = Field(
        default=["cnki", "wos", "ieee"],
        description="数据源列表",
    )
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    source_type: Optional[str] = None  # journal, conference, thesis
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchFilters(BaseModel):
    """搜索过滤器"""

    sources: Optional[List[str]] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    source_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    authors: Optional[List[str]] = None


# ============== 文献库模式 ==============

class LibraryItemCreate(BaseModel):
    """添加到文献库"""

    article_id: uuid.UUID
    folder_id: Optional[uuid.UUID] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class LibraryItemUpdate(BaseModel):
    """更新文献库项"""

    is_favorite: Optional[bool] = None
    is_read: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None


class LibraryItemResponse(BaseModel):
    """文献库项响应"""

    id: uuid.UUID
    article: ArticleBrief
    is_favorite: bool = False
    is_read: bool = False
    read_at: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    folder_id: Optional[uuid.UUID] = None
    added_at: datetime

    model_config = {"from_attributes": True}


# ============== 文件夹模式 ==============

class FolderCreate(BaseModel):
    """创建文件夹"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class FolderUpdate(BaseModel):
    """更新文件夹"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class FolderResponse(BaseModel):
    """文件夹响应"""

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    color: Optional[str] = None
    created_at: datetime
    article_count: int = 0

    model_config = {"from_attributes": True}


# ============== 推荐模式 ==============

class RecommendationRequest(BaseModel):
    """推荐请求"""

    user_id: uuid.UUID
    research_interests: Optional[List[str]] = None
    recent_keywords: Optional[List[str]] = None
    limit: int = Field(default=5, ge=1, le=20)


class RecommendationResponse(BaseModel):
    """推荐响应"""

    article: ArticleBrief
    score: float
    reason: Optional[str] = None


# ============== 分析模式 ==============

class ArticleAnalysis(BaseModel):
    """文献分析结果"""

    article_id: uuid.UUID
    research_background: Optional[str] = None
    core_findings: Optional[List[str]] = None
    methodology: Optional[str] = None
    key_figures: Optional[List[str]] = None
    references_style: Optional[str] = None
    writing_suggestions: Optional[List[str]] = None
