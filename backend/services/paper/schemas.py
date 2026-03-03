"""
论文数据模式
Pydantic 模型用于请求/响应验证
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ============== 基础模式 ==============

class PaperBase(BaseModel):
    """论文基础模式"""

    title: str = Field(..., min_length=1, max_length=500)
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    paper_type: str = Field(default="thesis")
    language: str = Field(default="zh")


class PaperCreate(PaperBase):
    """创建论文"""

    team_id: Optional[uuid.UUID] = None
    template_id: Optional[uuid.UUID] = None
    citation_style: str = Field(default="gb-t-7714-2015")


class PaperUpdate(BaseModel):
    """更新论文"""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    paper_type: Optional[str] = None
    status: Optional[str] = None
    language: Optional[str] = None
    template_id: Optional[uuid.UUID] = None
    citation_style: Optional[str] = None


class PaperResponse(BaseModel):
    """论文响应模式"""

    id: uuid.UUID
    title: str
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    paper_type: str
    status: str
    language: str
    owner_id: uuid.UUID
    team_id: Optional[uuid.UUID] = None
    template_id: Optional[uuid.UUID] = None
    citation_style: str

    # 统计信息
    word_count: int = 0
    page_count: int = 0
    figure_count: int = 0
    table_count: int = 0
    reference_count: int = 0

    # 时间戳
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaperBrief(BaseModel):
    """论文简要信息"""

    id: uuid.UUID
    title: str
    status: str
    paper_type: str
    word_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============== 章节模式 ==============

class SectionBase(BaseModel):
    """章节基础模式"""

    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    section_type: Optional[str] = None


class SectionCreate(SectionBase):
    """创建章节"""

    parent_id: Optional[uuid.UUID] = None
    order_index: int = Field(default=0, ge=0)


class SectionUpdate(BaseModel):
    """更新章节"""

    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    section_type: Optional[str] = None
    status: Optional[str] = None


class SectionResponse(SectionBase):
    """章节响应"""

    id: uuid.UUID
    paper_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    order_index: int
    word_count: int = 0
    status: str = "draft"
    created_at: datetime
    updated_at: datetime
    children: Optional[List["SectionResponse"]] = None

    model_config = {"from_attributes": True}


# ============== 协作者模式 ==============

class CollaboratorAdd(BaseModel):
    """添加协作者"""

    user_email: str = Field(..., description="用户邮箱")
    role: str = Field(default="viewer")  # owner, editor, reviewer, viewer
    can_edit: bool = False
    can_comment: bool = True
    can_share: bool = False


class CollaboratorUpdate(BaseModel):
    """更新协作者权限"""

    role: Optional[str] = None
    can_edit: Optional[bool] = None
    can_comment: Optional[bool] = None
    can_share: Optional[bool] = None


class CollaboratorResponse(BaseModel):
    """协作者响应"""

    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    can_edit: bool
    can_comment: bool
    can_share: bool
    invited_at: datetime
    accepted_at: Optional[datetime] = None

    # 用户信息（需要join查询）
    user: Optional[dict] = None

    model_config = {"from_attributes": True}


# ============== 版本模式 ==============

class VersionResponse(BaseModel):
    """版本响应"""

    id: uuid.UUID
    paper_id: uuid.UUID
    version_number: int
    title: Optional[str] = None
    change_summary: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VersionCreate(BaseModel):
    """创建版本"""

    change_summary: Optional[str] = None


# ============== 模板模式 ==============

class TemplateResponse(BaseModel):
    """模板响应"""

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    source_type: str
    source_id: Optional[str] = None
    config: dict
    preview_url: Optional[str] = None
    is_public: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ============== 导出模式 ==============

class ExportRequest(BaseModel):
    """导出请求"""

    format: str = Field(default="docx")  # docx, pdf, latex, markdown
    include_comments: bool = False
    include_references: bool = True


class ExportResponse(BaseModel):
    """导出响应"""

    download_url: str
    format: str
    file_size: int
    expires_at: datetime


# ============== 评论模式 ==============

class CommentPosition(BaseModel):
    """评论位置"""
    from_: int = Field(alias="from", default=0)
    to: int = Field(default=0)
    sectionId: Optional[str] = None
    selectedText: Optional[str] = None

    model_config = {"populate_by_name": True}


class CommentCreate(BaseModel):
    """创建评论"""

    paper_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    content: str = Field(..., min_length=1)
    position: CommentPosition = Field(default_factory=CommentPosition)


class CommentUpdate(BaseModel):
    """更新评论"""

    content: Optional[str] = Field(None, min_length=1)
    resolved: Optional[bool] = None


class CommentReplyCreate(BaseModel):
    """创建评论回复"""

    content: str = Field(..., min_length=1)


class CommentReplyResponse(BaseModel):
    """评论回复响应"""

    id: uuid.UUID
    comment_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    created_at: datetime

    # 用户信息（需要join查询）
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


class CommentResponse(BaseModel):
    """评论响应"""

    id: uuid.UUID
    paper_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    content: str
    position: dict
    resolved: bool
    resolved_by: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # 关联数据
    replies: List[CommentReplyResponse] = []

    # 用户信息（需要join查询）
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


# ============== 批注模式 ==============

class AnnotationPosition(BaseModel):
    """批注位置"""
    from_: int = Field(alias="from", default=0)
    to: int = Field(default=0)
    sectionId: Optional[str] = None
    selectedText: Optional[str] = None

    model_config = {"populate_by_name": True}


class AnnotationStyle(BaseModel):
    """批注样式"""
    color: Optional[str] = None
    bgColor: Optional[str] = None


class AnnotationCreate(BaseModel):
    """创建批注"""

    paper_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    annotation_type: str = Field(default="comment")  # comment, highlight, question, suggestion
    content: Optional[str] = None
    position: AnnotationPosition = Field(default_factory=AnnotationPosition)
    style: AnnotationStyle = Field(default_factory=AnnotationStyle)
    priority: str = Field(default="normal")  # low, normal, high


class AnnotationUpdate(BaseModel):
    """更新批注"""

    content: Optional[str] = None
    style: Optional[AnnotationStyle] = None
    status: Optional[str] = None  # open, resolved, dismissed
    priority: Optional[str] = None


class AnnotationResponse(BaseModel):
    """批注响应"""

    id: uuid.UUID
    paper_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    annotation_type: str
    content: Optional[str] = None
    position: dict
    style: dict
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

    # 用户信息（需要join查询）
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None

    model_config = {"from_attributes": True}


# 更新forward reference
SectionResponse.model_rebuild()


# ============== 评论模式 ==============

class CommentPosition(BaseModel):
    """评论位置"""
    from_: int = Field(default=0, alias="from")
    to: int = Field(default=0)
    section_id: Optional[uuid.UUID] = None
    selected_text: Optional[str] = None

    model_config = {"populate_by_name": True}


class CommentCreate(BaseModel):
    """创建评论"""
    paper_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    content: str = Field(..., min_length=1)
    position: CommentPosition


class CommentUpdate(BaseModel):
    """更新评论"""
    content: Optional[str] = None
    resolved: Optional[bool] = None


class CommentReplyCreate(BaseModel):
    """创建评论回复"""
    content: str = Field(..., min_length=1)


class CommentReplyResponse(BaseModel):
    """评论回复响应"""
    id: uuid.UUID
    comment_id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentResponse(BaseModel):
    """评论响应"""
    id: uuid.UUID
    paper_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    content: str
    position: dict
    resolved: bool
    resolved_by: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    replies: List[CommentReplyResponse] = []

    model_config = {"from_attributes": True}


# ============== 批注模式 ==============

class AnnotationStyle(BaseModel):
    """批注样式"""
    color: Optional[str] = None
    bg_color: Optional[str] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None


class AnnotationCreate(BaseModel):
    """创建批注"""
    paper_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    annotation_type: str = Field(default="comment")  # comment, highlight, question, suggestion
    content: Optional[str] = None
    position: CommentPosition
    style: Optional[AnnotationStyle] = None
    priority: str = Field(default="normal")  # low, normal, high


class AnnotationUpdate(BaseModel):
    """更新批注"""
    content: Optional[str] = None
    style: Optional[AnnotationStyle] = None
    status: Optional[str] = None  # open, resolved, dismissed
    priority: Optional[str] = None


class AnnotationResponse(BaseModel):
    """批注响应"""
    id: uuid.UUID
    paper_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    annotation_type: str
    content: Optional[str] = None
    position: dict
    style: dict
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
