"""
批注服务数据模型
Pydantic 模型定义
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class AnnotationType(str, Enum):
    """批注类型"""
    COMMENT = "comment"          # 普通评论
    SUGGESTION = "suggestion"    # 修改建议
    QUESTION = "question"        # 问题
    CORRECTION = "correction"    # 纠正
    APPROVAL = "approval"        # 认可/通过


class AnnotationStatus(str, Enum):
    """批注状态"""
    PENDING = "pending"          # 待处理
    ACCEPTED = "accepted"        # 已接受
    REJECTED = "rejected"        # 已拒绝
    RESOLVED = "resolved"        # 已解决


class AnnotationPriority(str, Enum):
    """批注优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ============== 请求模型 ==============

class AnnotationCreate(BaseModel):
    """创建批注请求"""
    paper_id: uuid.UUID = Field(..., description="论文ID")
    section_id: Optional[uuid.UUID] = Field(None, description="章节ID")
    annotation_type: AnnotationType = Field(AnnotationType.COMMENT, description="批注类型")
    content: str = Field(..., min_length=1, max_length=5000, description="批注内容")
    position: Optional[Dict[str, Any]] = Field(None, description="位置信息")
    priority: AnnotationPriority = Field(AnnotationPriority.MEDIUM, description="优先级")
    parent_id: Optional[uuid.UUID] = Field(None, description="父批注ID（用于回复）")


class AnnotationUpdate(BaseModel):
    """更新批注请求"""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    status: Optional[AnnotationStatus] = None
    priority: Optional[AnnotationPriority] = None


class AnnotationReply(BaseModel):
    """批注回复请求"""
    content: str = Field(..., min_length=1, max_length=2000, description="回复内容")


class AnnotationResolve(BaseModel):
    """解决批注请求"""
    resolution_note: Optional[str] = Field(None, max_length=500, description="解决说明")


class AnnotationFilter(BaseModel):
    """批注筛选条件"""
    paper_id: Optional[uuid.UUID] = None
    section_id: Optional[uuid.UUID] = None
    author_id: Optional[uuid.UUID] = None
    annotation_type: Optional[AnnotationType] = None
    status: Optional[AnnotationStatus] = None
    priority: Optional[AnnotationPriority] = None


# ============== 响应模型 ==============

class AuthorInfo(BaseModel):
    """作者信息"""
    id: str
    name: str
    avatar_url: Optional[str] = None
    role: str = "student"


class AnnotationPosition(BaseModel):
    """批注位置"""
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    start_selector: Optional[str] = None
    end_selector: Optional[str] = None
    quoted_text: Optional[str] = None


class AnnotationResponse(BaseModel):
    """批注响应"""
    id: str
    paper_id: str
    section_id: Optional[str] = None
    author: AuthorInfo
    annotation_type: AnnotationType
    content: str
    position: Optional[AnnotationPosition] = None
    status: AnnotationStatus
    priority: AnnotationPriority
    parent_id: Optional[str] = None
    reply_count: int = 0
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[AuthorInfo] = None


class AnnotationThread(BaseModel):
    """批注线程（包含回复）"""
    annotation: AnnotationResponse
    replies: List[AnnotationResponse] = []


class AnnotationStats(BaseModel):
    """批注统计"""
    total_count: int
    pending_count: int
    accepted_count: int
    rejected_count: int
    resolved_count: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    recent_count: int  # 最近7天新增


class AnnotationListResponse(BaseModel):
    """批注列表响应"""
    items: List[AnnotationResponse]
    total: int
    page: int
    page_size: int


# ============== 批注导出 ==============

class AnnotationExport(BaseModel):
    """批注导出格式"""
    paper_id: str
    paper_title: str
    export_time: datetime
    annotations: List[AnnotationResponse]
    summary: AnnotationStats
