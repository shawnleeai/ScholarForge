"""
参考文献服务数据模型
Pydantic 模型定义
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============== 基础模型 ==============

class AuthorInfo(BaseModel):
    """作者信息"""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    orcid: Optional[str] = None


class ReferenceBase(BaseModel):
    """参考文献基础模型"""
    title: str = Field(..., min_length=1, max_length=500)
    authors: List[str] = Field(default_factory=list)
    publication_year: Optional[int] = None
    journal_name: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    publication_type: str = Field(default="journal", pattern="^(journal|conference|book|thesis|report|online|other)$")
    language: str = Field(default="zh", pattern="^(zh|en|other)$")
    pdf_url: Optional[str] = None
    citation_count: int = Field(default=0, ge=0)


class ReferenceCreate(ReferenceBase):
    """创建参考文献请求"""
    paper_id: Optional[str] = None
    folder_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    is_important: bool = False
    source_db: Optional[str] = None
    source_id: Optional[str] = None


class ReferenceUpdate(BaseModel):
    """更新参考文献请求"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    authors: Optional[List[str]] = None
    publication_year: Optional[int] = None
    journal_name: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    publisher: Optional[str] = None
    publication_type: Optional[str] = Field(default=None, pattern="^(journal|conference|book|thesis|report|online|other)$")
    pdf_url: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    is_important: Optional[bool] = None
    is_read: Optional[bool] = None
    category: Optional[str] = None


class ReferenceResponse(ReferenceBase):
    """参考文献响应"""
    id: str
    user_id: str
    paper_id: Optional[str] = None
    folder_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    rating: Optional[int] = None
    is_important: bool = False
    is_read: bool = False
    cited_times: int = Field(default=0)
    category: Optional[str] = None
    source_db: Optional[str] = None
    added_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReferenceBrief(BaseModel):
    """参考文献简要信息"""
    id: str
    title: str
    authors: List[str]
    publication_year: Optional[int]
    journal_name: Optional[str]
    doi: Optional[str]
    is_important: bool
    is_read: bool


# ============== 搜索和筛选 ==============

class ReferenceFilters(BaseModel):
    """参考文献筛选条件"""
    paper_id: Optional[str] = None
    folder_id: Optional[str] = None
    publication_type: Optional[str] = None
    is_important: Optional[bool] = None
    is_read: Optional[bool] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    order_by: str = Field(default="added_at DESC", pattern="^(added_at|publication_year|citation_count|title)_(ASC|DESC)$")


class ReferenceSearchRequest(BaseModel):
    """搜索参考文献请求"""
    query: Optional[str] = None
    filters: ReferenceFilters = Field(default_factory=ReferenceFilters)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ReferenceListResponse(BaseModel):
    """参考文献列表响应"""
    items: List[ReferenceResponse]
    total: int
    page: int
    page_size: int


# ============== 标签管理 ==============

class TagAddRequest(BaseModel):
    """添加标签请求"""
    tags: List[str] = Field(..., min_length=1)


class TagRemoveRequest(BaseModel):
    """移除标签请求"""
    tags: List[str] = Field(..., min_length=1)


class TagsListResponse(BaseModel):
    """标签列表响应"""
    tags: List[str]


# ============== 引用关系 ==============

class CitationCreate(BaseModel):
    """创建引用请求"""
    citing_ref_id: str
    citing_position: Optional[str] = None
    citation_text: Optional[str] = None
    citation_style: str = Field(default="gb7714", pattern="^(apa|mla|chicago|gb7714|ieee|harvard)$")


class CitationUpdate(BaseModel):
    """更新引用请求"""
    citing_position: Optional[str] = None
    citation_text: Optional[str] = None
    citation_style: Optional[str] = Field(default=None, pattern="^(apa|mla|chicago|gb7714|ieee|harvard)$")
    formatted_citation: Optional[str] = None


class CitationResponse(BaseModel):
    """引用关系响应"""
    id: str
    paper_id: str
    citing_ref_id: str
    citing_ref: Optional[ReferenceBrief] = None
    cited_ref_id: Optional[str] = None
    citing_position: Optional[str]
    citation_text: Optional[str]
    citation_style: str
    formatted_citation: Optional[str]
    citation_number: int
    created_at: datetime

    class Config:
        from_attributes = True


class CitationFormatRequest(BaseModel):
    """格式化引用请求"""
    reference_ids: List[str]
    style: str = Field(default="gb7714", pattern="^(apa|mla|chicago|gb7714|ieee|harvard|vancouver)$")


class CitationFormatResponse(BaseModel):
    """格式化引用响应"""
    style: str
    citations: List[Dict[str, Any]]


# ============== 文件夹 ==============

class FolderBase(BaseModel):
    """文件夹基础模型"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#1890ff", pattern="^#[0-9a-fA-F]{6}$")
    parent_id: Optional[str] = None


class FolderCreate(FolderBase):
    """创建文件夹请求"""
    sort_order: int = Field(default=0, ge=0)


class FolderUpdate(BaseModel):
    """更新文件夹请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(default=None, pattern="^#[0-9a-fA-F]{6}$")
    parent_id: Optional[str] = None
    sort_order: Optional[int] = Field(default=None, ge=0)


class FolderResponse(FolderBase):
    """文件夹响应"""
    id: str
    user_id: str
    sort_order: int
    item_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FolderListResponse(BaseModel):
    """文件夹列表响应"""
    items: List[FolderResponse]


class MoveToFolderRequest(BaseModel):
    """移动到文件夹请求"""
    folder_id: Optional[str] = None
    reference_ids: List[str]


# ============== 导入/导出 ==============

class ImportRequest(BaseModel):
    """导入文献请求"""
    paper_id: Optional[str] = None
    folder_id: Optional[str] = None
    source_type: str = Field(..., pattern="^(zotero|endnote|mendeley|noteexpress|bibtex|ris|csv|json)$")
    file_path: str
    import_settings: Dict[str, Any] = Field(default_factory=dict)


class ImportPreviewRequest(BaseModel):
    """导入预览请求"""
    source_type: str
    paper_id: Optional[str] = None
    folder_id: Optional[str] = None


class ImportPreviewResponse(BaseModel):
    """导入预览响应"""
    total: int
    valid: int
    duplicates: int
    invalid: int
    sample: List[Dict[str, Any]]
    duplicates_detail: List[Dict[str, Any]]


class ImportTaskResponse(BaseModel):
    """导入任务响应"""
    id: str
    user_id: str
    paper_id: Optional[str]
    source_type: str
    file_name: Optional[str]
    status: str
    total_count: int
    success_count: int
    failed_count: int
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    """导出文献请求"""
    reference_ids: Optional[List[str]] = None
    folder_id: Optional[str] = None
    paper_id: Optional[str] = None
    format: str = Field(..., pattern="^(bibtex|ris|endnote|csv|json)$")
    options: Dict[str, Any] = Field(default_factory=dict)


class ExportResponse(BaseModel):
    """导出响应"""
    format: str
    file_url: str
    file_name: str
    record_count: int


# ============== 统计 ==============

class ReferenceStatistics(BaseModel):
    """参考文献统计"""
    total: int
    read_count: int
    unread_count: int
    important_count: int
    by_type: Dict[str, int]
    with_year_count: int
    avg_rating: Optional[float]
    year_distribution: List[Dict[str, Any]]
    top_authors: List[Dict[str, Any]]
    top_journals: List[Dict[str, Any]]


# ============== 元数据提取 ==============

class MetadataExtractRequest(BaseModel):
    """元数据提取请求"""
    identifier: Optional[str] = None  # DOI/PMID/URL
    identifier_type: Optional[str] = Field(default=None, pattern="^(doi|pmid|url|isbn)$")
    text: Optional[str] = None  # 引用文本或标题


class MetadataExtractResponse(BaseModel):
    """元数据提取响应"""
    success: bool
    confidence: float
    reference: Optional[ReferenceCreate] = None
    message: Optional[str] = None


# ============== 智能推荐 ==============

class ReferenceRecommendationRequest(BaseModel):
    """文献推荐请求"""
    paper_id: Optional[str] = None
    reference_id: Optional[str] = None
    keywords: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=50)


class ReferenceRecommendation(BaseModel):
    """推荐文献"""
    reference: ReferenceResponse
    relevance_score: float
    reason: str


class ReferenceRecommendationResponse(BaseModel):
    """文献推荐响应"""
    recommendations: List[ReferenceRecommendation]
