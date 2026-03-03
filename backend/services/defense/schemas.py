"""
答辩准备服务数据模型
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# 检查清单模型
class ChecklistItem(BaseModel):
    id: str
    category: str
    content: str
    completed: bool = False
    order: int


class ChecklistResponse(BaseModel):
    id: str
    paper_id: str
    items: List[Dict[str, Any]]
    progress: float
    created_at: datetime
    updated_at: datetime


class ChecklistUpdateRequest(BaseModel):
    items: List[Dict[str, Any]]


# PPT模型
class PPTSlide(BaseModel):
    id: str
    type: str  # title, content, thanks, etc.
    title: str
    content: str
    order: int
    duration: Optional[int] = None  # 建议演讲时长（秒）


class PPTOutline(BaseModel):
    title: str
    slides: List[PPTSlide]


class PPTOutlineResponse(BaseModel):
    id: str
    paper_id: str
    template: str
    outline: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


class PPTUpdateRequest(BaseModel):
    outline: Dict[str, Any]


# 问答模型
class QAResponse(BaseModel):
    id: str
    question: str
    answer: str
    category: str
    difficulty: str
    paper_id: Optional[str] = None


class QAListRequest(BaseModel):
    paper_id: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    limit: int = 20


# 模拟答辩模型
class MockQuestion(BaseModel):
    id: str
    question: str
    difficulty: str


class MockSessionResponse(BaseModel):
    id: str
    paper_id: str
    status: str
    questions: List[MockQuestion]
    created_at: datetime


class MockAnswerRequest(BaseModel):
    question_id: str
    question: str
    answer: str


class MockResultResponse(BaseModel):
    session_id: str
    total_score: float
    grade: str
    suggestions: List[str]
