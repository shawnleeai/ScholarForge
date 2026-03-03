"""
进度管理数据模型
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class MilestoneStatus(str, Enum):
    """里程碑状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    AT_RISK = "at_risk"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============== 里程碑 ==============

class MilestoneBase(BaseModel):
    """里程碑基础"""
    title: str
    description: Optional[str] = None
    planned_date: date
    paper_id: str


class MilestoneCreate(MilestoneBase):
    """创建里程碑"""
    pass


class Milestone(MilestoneBase):
    """里程碑"""
    id: str
    status: MilestoneStatus = MilestoneStatus.PENDING
    actual_date: Optional[date] = None
    completion_percentage: int = 0
    created_at: datetime
    updated_at: datetime


class MilestoneUpdate(BaseModel):
    """更新里程碑"""
    status: Optional[MilestoneStatus] = None
    actual_date: Optional[date] = None
    completion_percentage: Optional[int] = None


# ============== 任务 ==============

class TaskBase(BaseModel):
    """任务基础"""
    title: str
    description: Optional[str] = None
    milestone_id: str
    assignee_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    planned_start: date
    planned_end: date


class TaskCreate(TaskBase):
    """创建任务"""
    pass


class Task(TaskBase):
    """任务"""
    id: str
    paper_id: str
    status: str = "pending"
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    progress: int = 0
    dependencies: List[str] = []
    created_at: datetime
    updated_at: datetime


class TaskUpdate(BaseModel):
    """更新任务"""
    status: Optional[str] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    progress: Optional[int] = None


# ============== 甘特图 ==============

class GanttItem(BaseModel):
    """甘特图项"""
    id: str
    name: str
    start: date
    end: date
    progress: int = 0
    status: str
    dependencies: List[str] = []


class GanttChart(BaseModel):
    """甘特图"""
    paper_id: str
    items: List[GanttItem]
    milestones: List[Dict[str, Any]]
    start_date: date
    end_date: date
    generated_at: datetime


# ============== 预警 ==============

class Alert(BaseModel):
    """预警"""
    id: str
    paper_id: str
    type: str  # deadline_risk, progress_delay quality_issue
    severity: RiskLevel
    title: str
    description: str
    affected_items: List[str] = []
    suggestions: List[str] = []
    created_at: datetime
    is_read: bool = False
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertCreate(BaseModel):
    """创建预警"""
    type: str
    severity: RiskLevel
    title: str
    description: str
    affected_items: List[str] = []
    suggestions: List[str] = []


# ============== 进度报告 ==============

class ProgressStats(BaseModel):
    """进度统计"""
    total_milestones: int
    completed_milestones: int
    in_progress_milestones: int
    delayed_milestones: int
    at_risk_milestones: int
    total_tasks: int
    completed_tasks: int
    overall_progress: float
    days_remaining: int
    on_track: bool


class ProgressReport(BaseModel):
    """进度报告"""
    paper_id: str
    paper_title: str
    generated_at: datetime
    stats: ProgressStats
    milestones: List[Milestone]
    alerts: List[Alert]
    recommendations: List[str]
    next_actions: List[str]


class WeeklyReport(ProgressReport):
    """周报告"""
    week_number: int
    period_start: date
    period_end: date
    completed_this_week: List[str]
    planned_next_week: List[str]
    blockers: List[str]


# ============== 设置 ==============

class ProgressSettings(BaseModel):
    """进度设置"""
    paper_id: str
    start_date: date
    target_completion_date: date
    working_days_per_week: int = 5
    reminder_enabled: bool = True
    reminder_days_before: int = 3
    auto_alert_enabled: bool = True
