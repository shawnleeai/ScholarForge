"""
Events Service
科研活动服务 - 会议管理、注册、征文
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .models import Event, EventType, EventFormat, EventStatus, EventRegistration, CallForPapers


class EventsService:
    """科研活动服务"""

    def __init__(self):
        self._events: Dict[str, Event] = {}
        self._registrations: Dict[str, EventRegistration] = {}
        self._cfps: Dict[str, CallForPapers] = {}

    # ==================== 活动管理 ====================

    def create_event(
        self,
        title: str,
        description: str,
        event_type: EventType,
        format: EventFormat,
        start_date: datetime,
        end_date: datetime,
        organizer_id: str,
        **kwargs
    ) -> Event:
        """创建活动"""
        event = Event(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            event_type=event_type,
            format=format,
            status=EventStatus.DRAFT,
            start_date=start_date,
            end_date=end_date,
            organizer_id=organizer_id,
            **kwargs
        )
        self._events[event.id] = event
        return event

    def get_event(self, event_id: str) -> Optional[Event]:
        """获取活动详情"""
        event = self._events.get(event_id)
        if event:
            event.view_count += 1
        return event

    def update_event(
        self,
        event_id: str,
        organizer_id: str,
        **updates
    ) -> Optional[Event]:
        """更新活动"""
        event = self._events.get(event_id)
        if not event or event.organizer_id != organizer_id:
            return None

        for key, value in updates.items():
            if hasattr(event, key):
                setattr(event, key, value)

        return event

    def publish_event(self, event_id: str, organizer_id: str) -> bool:
        """发布活动"""
        event = self._events.get(event_id)
        if not event or event.organizer_id != organizer_id:
            return False

        event.status = EventStatus.PUBLISHED
        return True

    def list_events(
        self,
        event_type: Optional[EventType] = None,
        format: Optional[EventFormat] = None,
        status: Optional[EventStatus] = None,
        upcoming: bool = False,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Event]:
        """列出活动"""
        events = list(self._events.values())

        # 只返回已发布或进行中的活动
        events = [e for e in events if e.status in [
            EventStatus.PUBLISHED,
            EventStatus.REGISTRATION_OPEN,
            EventStatus.ONGOING
        ]]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if format:
            events = [e for e in events if e.format == format]

        if status:
            events = [e for e in events if e.status == status]

        if upcoming:
            now = datetime.utcnow()
            events = [e for e in events if e.start_date > now]
            events.sort(key=lambda x: x.start_date)

        if tags:
            events = [
                e for e in events
                if any(tag in e.tags for tag in tags)
            ]

        return events[:limit]

    def search_events(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Event]:
        """搜索活动"""
        events = list(self._events.values())

        # 按关键词过滤
        query_lower = query.lower()
        events = [
            e for e in events
            if query_lower in e.title.lower()
            or query_lower in e.description.lower()
            or any(query_lower in t.lower() for t in e.topics)
        ]

        if location:
            events = [
                e for e in events
                if e.city and location.lower() in e.city.lower()
                or e.country and location.lower() in e.country.lower()
            ]

        # 按时间排序
        events.sort(key=lambda x: x.start_date)

        return events[:limit]

    def get_my_events(self, user_id: str) -> Dict[str, List[Event]]:
        """获取用户相关活动"""
        organized = [
            e for e in self._events.values()
            if e.organizer_id == user_id
        ]

        registered = [
            self._events[r.event_id]
            for r in self._registrations.values()
            if r.user_id == user_id and r.event_id in self._events
        ]

        return {
            "organized": organized,
            "registered": registered
        }

    # ==================== 注册管理 ====================

    def register_for_event(
        self,
        event_id: str,
        user_id: str,
        **kwargs
    ) -> Optional[EventRegistration]:
        """活动注册"""
        event = self._events.get(event_id)
        if not event:
            return None

        # 检查是否已满
        if event.max_participants and len(event.registered_participants) >= event.max_participants:
            return None

        # 检查是否已注册
        existing = self._get_registration(event_id, user_id)
        if existing:
            return existing

        registration = EventRegistration(
            id=str(uuid.uuid4()),
            event_id=event_id,
            user_id=user_id,
            payment_amount=event.registration_fee,
            **kwargs
        )

        self._registrations[registration.id] = registration
        event.registered_participants.append(user_id)

        # 更新活动状态
        if event.max_participants and len(event.registered_participants) >= event.max_participants:
            event.status = EventStatus.REGISTRATION_CLOSED

        return registration

    def cancel_registration(self, registration_id: str, user_id: str) -> bool:
        """取消注册"""
        registration = self._registrations.get(registration_id)
        if not registration or registration.user_id != user_id:
            return False

        registration.status = "cancelled"

        # 从活动参与者列表移除
        event = self._events.get(registration.event_id)
        if event and user_id in event.registered_participants:
            event.registered_participants.remove(user_id)

        return True

    def _get_registration(self, event_id: str, user_id: str) -> Optional[EventRegistration]:
        """获取注册记录"""
        for reg in self._registrations.values():
            if reg.event_id == event_id and reg.user_id == user_id:
                return reg
        return None

    def get_event_registrations(self, event_id: str) -> List[EventRegistration]:
        """获取活动注册列表"""
        return [
            r for r in self._registrations.values()
            if r.event_id == event_id
        ]

    # ==================== 征文管理 ====================

    def create_cfp(
        self,
        event_id: str,
        title: str,
        description: str,
        **kwargs
    ) -> CallForPapers:
        """创建征文通知"""
        cfp = CallForPapers(
            id=str(uuid.uuid4()),
            event_id=event_id,
            title=title,
            description=description,
            **kwargs
        )
        self._cfps[cfp.id] = cfp
        return cfp

    def get_active_cfps(self) -> List[CallForPapers]:
        """获取活跃征文"""
        now = datetime.utcnow()
        cfps = [c for c in self._cfps.values() if c.is_active]

        # 按截稿日期排序
        def get_deadline(cfp):
            return cfp.important_dates.get("submission_deadline", datetime.max)

        cfps.sort(key=get_deadline)

        return cfps

    def get_cfp_by_event(self, event_id: str) -> Optional[CallForPapers]:
        """获取活动征文"""
        for cfp in self._cfps.values():
            if cfp.event_id == event_id:
                return cfp
        return None

    # ==================== 推荐 ====================

    def get_recommended_events(
        self,
        user_id: str,
        interests: List[str],
        limit: int = 10
    ) -> List[Event]:
        """推荐活动"""
        now = datetime.utcnow()

        # 获取未来活动
        upcoming = [
            e for e in self._events.values()
            if e.start_date > now
            and e.status in [EventStatus.PUBLISHED, EventStatus.REGISTRATION_OPEN]
        ]

        # 按兴趣匹配度排序
        def relevance_score(event: Event) -> float:
            score = 0.0

            # 主题匹配
            for interest in interests:
                if interest.lower() in [t.lower() for t in event.topics]:
                    score += 10
                if interest.lower() in [t.lower() for t in event.tags]:
                    score += 5

            # 时间因素（越早的活动分数越高）
            days_until = (event.start_date - now).days
            score += max(0, 30 - days_until)

            # 热度因素
            score += event.view_count * 0.01

            return score

        upcoming.sort(key=relevance_score, reverse=True)

        return upcoming[:limit]


# 单例
_events_service = None


def get_events_service() -> EventsService:
    """获取活动服务单例"""
    global _events_service
    if _events_service is None:
        _events_service = EventsService()
    return _events_service
