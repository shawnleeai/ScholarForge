"""
Events Models
科研活动模型 - 学术会议、研讨会、讲座、竞赛
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class EventType(str, Enum):
    """活动类型"""
    CONFERENCE = "conference"      # 学术会议
    SEMINAR = "seminar"            # 研讨会
    WORKSHOP = "workshop"          # 工作坊
    LECTURE = "lecture"            # 学术讲座
    COMPETITION = "competition"    # 学术竞赛
    HACKATHON = "hackathon"        # 黑客松
    SYMPOSIUM = "symposium"        # 专题研讨会
    SUMMER_SCHOOL = "summer_school"  # 暑期学校
    WEBINAR = "webinar"            # 网络研讨会


class EventFormat(str, Enum):
    """活动形式"""
    IN_PERSON = "in_person"        # 线下
    ONLINE = "online"              # 线上
    HYBRID = "hybrid"              # 混合


class EventStatus(str, Enum):
    """活动状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    REGISTRATION_OPEN = "registration_open"
    REGISTRATION_CLOSED = "registration_closed"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Event:
    """科研活动"""
    id: str
    title: str
    description: str
    event_type: EventType
    format: EventFormat
    status: EventStatus

    # 时间
    start_date: datetime
    end_date: datetime
    timezone: str = "UTC"

    # 地点
    venue: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    online_url: Optional[str] = None

    # 组织者
    organizer_id: str = ""
    organizer_name: str = ""
    co_organizers: List[str] = field(default_factory=list)

    # 参与者
    max_participants: Optional[int] = None
    registered_participants: List[str] = field(default_factory=list)
    speakers: List[Dict[str, Any]] = field(default_factory=list)

    # 内容
    agenda: List[Dict[str, Any]] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # 注册
    registration_deadline: Optional[datetime] = None
    registration_fee: float = 0.0
    currency: str = "CNY"

    # 元数据
    cover_image: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    # 统计
    view_count: int = 0
    like_count: int = 0


@dataclass
class EventRegistration:
    """活动注册"""
    id: str
    event_id: str
    user_id: str
    status: str = "pending"  # pending/confirmed/cancelled/attended
    registered_at: datetime = field(default_factory=datetime.utcnow)
    payment_status: str = "pending"  # pending/paid/refunded
    payment_amount: float = 0.0
    dietary_requirements: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class CallForPapers:
    """征文通知"""
    id: str
    event_id: str
    title: str
    description: str
    important_dates: Dict[str, datetime] = field(default_factory=dict)
    topics: List[str] = field(default_factory=list)
    submission_url: Optional[str] = None
    guidelines: str = ""
    is_active: bool = True
