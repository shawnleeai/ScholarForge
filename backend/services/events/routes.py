"""
Events API Routes
科研活动API路由
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from .service import get_events_service, EventType, EventFormat

router = APIRouter(prefix="/events", tags=["events"])


# ==================== 请求/响应模型 ====================

class CreateEventRequest(BaseModel):
    """创建活动请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    event_type: str = Field(..., description="类型: conference/seminar/workshop/lecture/competition/hackathon")
    format: str = Field(..., description="形式: in_person/online/hybrid")
    start_date: datetime
    end_date: datetime
    timezone: str = Field("UTC")
    venue: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    country: Optional[str] = Field(None)
    online_url: Optional[str] = Field(None)
    max_participants: Optional[int] = Field(None)
    registration_fee: float = Field(0.0)
    topics: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class RegisterEventRequest(BaseModel):
    """活动注册请求"""
    dietary_requirements: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== API端点 ====================

@router.post("")
async def create_event(
    request: CreateEventRequest,
    user_id: str = Depends(get_current_user)
):
    """创建科研活动"""
    service = get_events_service()

    try:
        event_type = EventType(request.event_type)
        event_format = EventFormat(request.format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    event = service.create_event(
        title=request.title,
        description=request.description,
        event_type=event_type,
        format=event_format,
        start_date=request.start_date,
        end_date=request.end_date,
        organizer_id=user_id,
        timezone=request.timezone,
        venue=request.venue,
        city=request.city,
        country=request.country,
        online_url=request.online_url,
        max_participants=request.max_participants,
        registration_fee=request.registration_fee,
        topics=request.topics,
        tags=request.tags
    )

    return {
        "message": "Event created successfully",
        "event": {
            "id": event.id,
            "title": event.title,
            "status": event.status.value
        }
    }


@router.get("")
async def list_events(
    event_type: Optional[str] = None,
    format: Optional[str] = None,
    upcoming: bool = True,
    limit: int = 20
):
    """列出活动"""
    service = get_events_service()

    event_type_enum = None
    if event_type:
        try:
            event_type_enum = EventType(event_type)
        except ValueError:
            pass

    format_enum = None
    if format:
        try:
            format_enum = EventFormat(format)
        except ValueError:
            pass

    events = service.list_events(
        event_type=event_type_enum,
        format=format_enum,
        upcoming=upcoming,
        limit=limit
    )

    return {
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description[:150] + "..." if len(e.description) > 150 else e.description,
                "event_type": e.event_type.value,
                "format": e.format.value,
                "start_date": e.start_date.isoformat(),
                "end_date": e.end_date.isoformat(),
                "city": e.city,
                "country": e.country,
                "online_url": e.online_url,
                "registration_fee": e.registration_fee,
                "registered_count": len(e.registered_participants),
                "max_participants": e.max_participants,
                "tags": e.tags,
                "cover_image": e.cover_image
            }
            for e in events
        ]
    }


@router.get("/{event_id}")
async def get_event_detail(event_id: str):
    """获取活动详情"""
    service = get_events_service()
    event = service.get_event(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type.value,
        "format": event.format.value,
        "status": event.status.value,
        "start_date": event.start_date.isoformat(),
        "end_date": event.end_date.isoformat(),
        "timezone": event.timezone,
        "venue": event.venue,
        "address": event.address,
        "city": event.city,
        "country": event.country,
        "online_url": event.online_url,
        "organizer_id": event.organizer_id,
        "organizer_name": event.organizer_name,
        "max_participants": event.max_participants,
        "registered_count": len(event.registered_participants),
        "registration_fee": event.registration_fee,
        "registration_deadline": event.registration_deadline.isoformat() if event.registration_deadline else None,
        "agenda": event.agenda,
        "topics": event.topics,
        "tags": event.tags,
        "speakers": event.speakers,
        "cover_image": event.cover_image,
        "view_count": event.view_count,
        "like_count": event.like_count
    }


@router.post("/{event_id}/register")
async def register_for_event(
    event_id: str,
    request: RegisterEventRequest,
    user_id: str = Depends(get_current_user)
):
    """注册参加活动"""
    service = get_events_service()

    registration = service.register_for_event(
        event_id=event_id,
        user_id=user_id,
        dietary_requirements=request.dietary_requirements,
        notes=request.notes
    )

    if not registration:
        raise HTTPException(status_code=400, detail="Registration failed (event full or not found)")

    return {
        "message": "Registration successful",
        "registration_id": registration.id,
        "payment_required": registration.payment_amount > 0,
        "payment_amount": registration.payment_amount
    }


@router.post("/{event_id}/cancel")
async def cancel_registration(
    event_id: str,
    user_id: str = Depends(get_current_user)
):
    """取消注册"""
    service = get_events_service()

    # 查找注册记录
    registrations = [
        r for r in service._registrations.values()
        if r.event_id == event_id and r.user_id == user_id
    ]

    if not registrations:
        raise HTTPException(status_code=404, detail="Registration not found")

    success = service.cancel_registration(registrations[0].id, user_id)

    if not success:
        raise HTTPException(status_code=400, detail="Cancellation failed")

    return {"message": "Registration cancelled successfully"}


@router.get("/{event_id}/registrations")
async def get_event_registrations(
    event_id: str,
    user_id: str = Depends(get_current_user)
):
    """获取活动注册列表（仅组织者）"""
    service = get_events_service()

    event = service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.organizer_id != user_id:
        raise HTTPException(status_code=403, detail="Only organizer can view registrations")

    registrations = service.get_event_registrations(event_id)

    return {
        "total": len(registrations),
        "confirmed": len([r for r in registrations if r.status == "confirmed"]),
        "pending": len([r for r in registrations if r.status == "pending"]),
        "registrations": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "status": r.status,
                "registered_at": r.registered_at.isoformat(),
                "payment_status": r.payment_status
            }
            for r in registrations
        ]
    }


@router.get("/search")
async def search_events(
    query: str,
    location: Optional[str] = None,
    limit: int = 20
):
    """搜索活动"""
    service = get_events_service()
    events = service.search_events(query, location, limit)

    return {
        "query": query,
        "results": [
            {
                "id": e.id,
                "title": e.title,
                "event_type": e.event_type.value,
                "start_date": e.start_date.isoformat(),
                "city": e.city,
                "tags": e.tags
            }
            for e in events
        ]
    }


@router.get("/my/events")
async def get_my_events(user_id: str = Depends(get_current_user)):
    """获取用户相关活动"""
    service = get_events_service()
    events = service.get_my_events(user_id)

    return {
        "organized": [
            {
                "id": e.id,
                "title": e.title,
                "start_date": e.start_date.isoformat(),
                "status": e.status.value
            }
            for e in events["organized"]
        ],
        "registered": [
            {
                "id": e.id,
                "title": e.title,
                "start_date": e.start_date.isoformat(),
                "format": e.format.value
            }
            for e in events["registered"]
        ]
    }


@router.get("/cfp/active")
async def get_active_cfps():
    """获取活跃征文"""
    service = get_events_service()
    cfps = service.get_active_cfps()

    return {
        "cfps": [
            {
                "id": c.id,
                "event_id": c.event_id,
                "title": c.title,
                "description": c.description[:150] + "..." if len(c.description) > 150 else c.description,
                "important_dates": {
                    k: v.isoformat() for k, v in c.important_dates.items()
                },
                "topics": c.topics,
                "submission_url": c.submission_url
            }
            for c in cfps
        ]
    }


@router.get("/types")
async def get_event_types():
    """获取活动类型列表"""
    return {
        "types": [
            {"id": "conference", "name": "学术会议", "description": "大型学术会议"},
            {"id": "seminar", "name": "研讨会", "description": "小型学术研讨"},
            {"id": "workshop", "name": "工作坊", "description": "实践工作坊"},
            {"id": "lecture", "name": "学术讲座", "description": "学术报告讲座"},
            {"id": "competition", "name": "学术竞赛", "description": "各类学术竞赛"},
            {"id": "hackathon", "name": "黑客松", "description": "编程马拉松"},
            {"id": "symposium", "name": "专题研讨会", "description": "特定主题研讨"},
            {"id": "summer_school", "name": "暑期学校", "description": "暑期课程"},
            {"id": "webinar", "name": "网络研讨会", "description": "线上研讨会"}
        ]
    }
