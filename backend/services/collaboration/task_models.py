"""
Collaboration Task Models
协同任务模型 - 论文协作、科研任务、推送通知
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class TaskType(str, Enum):
    """任务类型"""
    PAPER_WRITING = "paper_writing"      # 论文写作
    PAPER_REVIEW = "paper_review"        # 论文审阅
    EXPERIMENT = "experiment"            # 实验任务
    DATA_COLLECTION = "data_collection"  # 数据收集
    LITERATURE_REVIEW = "literature_review"  # 文献综述
    CODE_DEVELOPMENT = "code_development"    # 代码开发
    ANALYSIS = "analysis"                # 数据分析
    DISCUSSION = "discussion"            # 讨论任务


class TaskPriority(str, Enum):
    """任务优先级"""
    URGENT = "urgent"      # 紧急
    HIGH = "high"          # 高
    MEDIUM = "medium"      # 中
    LOW = "low"            # 低


class TaskStatus(str, Enum):
    """任务状态"""
    TODO = "todo"          # 待办
    IN_PROGRESS = "in_progress"  # 进行中
    REVIEW = "review"      # 审核中
    DONE = "done"          # 已完成
    CANCELLED = "cancelled"  # 已取消


class AssignmentType(str, Enum):
    """分配类型"""
    ASSIGNED = "assigned"      # 指定分配
    VOLUNTEER = "volunteer"    # 自愿领取
    ROTATION = "rotation"      # 轮流分配
    AUTO = "auto"              # 自动分配


@dataclass
class CollaborationTask:
    """协同任务"""
    id: str
    title: str
    description: str
    task_type: TaskType

    # 所属项目/论文
    project_id: Optional[str] = None
    paper_id: Optional[str] = None
    team_id: Optional[str] = None

    # 任务设置
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    assignment_type: AssignmentType = AssignmentType.ASSIGNED

    # 负责人
    creator_id: str = ""
    assignee_id: Optional[str] = None
    reviewers: List[str] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)

    # 时间
    created_at: datetime = field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 依赖
    depends_on: List[str] = field(default_factory=list)  # 依赖的任务ID
    blocks: List[str] = field(default_factory=list)      # 阻塞的任务ID

    # 内容
    deliverables: List[str] = field(default_factory=list)  # 交付物要求
    checklist: List[Dict[str, Any]] = field(default_factory=list)  # 检查清单
    attachments: List[str] = field(default_factory=list)

    # 统计
    estimated_hours: Optional[float] = None
    actual_hours: float = 0.0


@dataclass
class TaskComment:
    """任务评论"""
    id: str
    task_id: str
    author_id: str
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_id: Optional[str] = None  # 回复的评论ID
    mentions: List[str] = field(default_factory=list)  # @提到的用户


@dataclass
class TaskPush:
    """任务推送"""
    id: str
    task_id: str
    user_id: str
    push_type: str         # assign/remind/due/overdue/update
    title: str
    content: str

    # 推送设置
    channels: List[str] = field(default_factory=lambda: ["app", "email"])
    is_read: bool = False
    is_sent: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None


@dataclass
class PaperCollaboration:
    """论文协作"""
    id: str
    paper_id: str
    team_id: Optional[str] = None

    # 协作设置
    collaboration_type: str = "writing"  # writing/review/discussion
    is_public: bool = False

    # 参与者
    lead_author: str = ""
    co_authors: List[str] = field(default_factory=list)
    reviewers: List[str] = field(default_factory=list)

    # 权限
    can_edit: List[str] = field(default_factory=list)
    can_comment: List[str] = field(default_factory=list)
    can_view: List[str] = field(default_factory=list)

    # 状态
    current_section: Optional[str] = None
    progress_percentage: float = 0.0

    created_at: datetime = field(default_factory=datetime.utcnow)
    target_journal: Optional[str] = None
    target_deadline: Optional[datetime] = None


@dataclass
class CollaborationSchedule:
    """协作日程"""
    id: str
    title: str
    description: str
    schedule_type: str     # meeting/deadline/milestone/reminder

    # 关联
    team_id: Optional[str] = None
    project_id: Optional[str] = None
    paper_id: Optional[str] = None

    # 时间
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    timezone: str = "UTC"

    # 参与者
    organizer_id: str = ""
    attendees: List[str] = field(default_factory=list)
    optional_attendees: List[str] = field(default_factory=list)

    # 会议设置
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None  # RRULE格式

    # 提醒
    reminders: List[int] = field(default_factory=lambda: [15])  # 提前分钟数


@dataclass
class WorkloadStats:
    """工作负载统计"""
    user_id: str
    team_id: Optional[str] = None

    # 任务统计
    total_tasks: int = 0
    todo_count: int = 0
    in_progress_count: int = 0
    review_count: int = 0
    done_count: int = 0

    # 工作量
    total_estimated_hours: float = 0.0
    total_actual_hours: float = 0.0

    # 时间分布
    tasks_due_this_week: int = 0
    tasks_due_next_week: int = 0
    overdue_tasks: int = 0

    # 效率
    completion_rate: float = 0.0
    on_time_rate: float = 0.0

    updated_at: datetime = field(default_factory=datetime.utcnow)
