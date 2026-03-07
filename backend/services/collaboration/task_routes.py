"""
Collaboration Task API Routes
协同任务API路由 - 任务管理、协作推送、日程管理
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from .service import get_collaboration_task_service, TaskType, TaskPriority, TaskStatus

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


# ==================== 请求/响应模型 ====================

class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    task_type: str = Field(..., description="类型: paper_writing/paper_review/experiment/data_collection/literature_review/code_development/analysis/discussion")
    priority: str = Field("medium", description="urgent/high/medium/low")
    assignee_id: Optional[str] = Field(None)
    due_date: Optional[datetime] = Field(None)
    estimated_hours: Optional[float] = Field(None)
    team_id: Optional[str] = Field(None)
    project_id: Optional[str] = Field(None)
    paper_id: Optional[str] = Field(None)


class UpdateTaskStatusRequest(BaseModel):
    """更新任务状态请求"""
    status: str = Field(..., description="todo/in_progress/review/done/cancelled")


class TaskCommentRequest(BaseModel):
    """任务评论请求"""
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[str] = Field(None)


class CreateScheduleRequest(BaseModel):
    """创建日程请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    schedule_type: str = Field(..., description="meeting/deadline/milestone/reminder")
    start_time: datetime
    end_time: Optional[datetime] = Field(None)
    attendees: List[str] = Field(default_factory=list)
    meeting_link: Optional[str] = Field(None)
    location: Optional[str] = Field(None)


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== 任务管理API ====================

@router.post("/tasks")
async def create_task(
    request: CreateTaskRequest,
    user_id: str = Depends(get_current_user)
):
    """创建协同任务"""
    service = get_collaboration_task_service()

    try:
        task_type = TaskType(request.task_type)
        priority = TaskPriority(request.priority)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    task = service.create_task(
        title=request.title,
        description=request.description,
        task_type=task_type,
        creator_id=user_id,
        priority=priority,
        assignee_id=request.assignee_id,
        due_date=request.due_date,
        estimated_hours=request.estimated_hours,
        team_id=request.team_id,
        project_id=request.project_id,
        paper_id=request.paper_id
    )

    return {
        "message": "Task created successfully",
        "task": {
            "id": task.id,
            "title": task.title,
            "status": task.status.value,
            "assignee_id": task.assignee_id
        }
    }


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    task_type: Optional[str] = None,
    team_id: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user)
):
    """列出任务"""
    service = get_collaboration_task_service()

    status_enum = None
    if status:
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            pass

    priority_enum = None
    if priority:
        try:
            priority_enum = TaskPriority(priority)
        except ValueError:
            pass

    task_type_enum = None
    if task_type:
        try:
            task_type_enum = TaskType(task_type)
        except ValueError:
            pass

    tasks = service.list_tasks(
        user_id=user_id,
        team_id=team_id,
        status=status_enum,
        priority=priority_enum,
        task_type=task_type_enum,
        limit=limit
    )

    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description[:100] + "..." if len(t.description) > 100 else t.description,
                "task_type": t.task_type.value,
                "priority": t.priority.value,
                "status": t.status.value,
                "assignee_id": t.assignee_id,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "progress": f"{t.actual_hours}/{t.estimated_hours}h" if t.estimated_hours else None
            }
            for t in tasks
        ]
    }


@router.get("/tasks/my")
async def get_my_tasks(user_id: str = Depends(get_current_user)):
    """获取我的任务"""
    service = get_collaboration_task_service()
    tasks = service.get_user_tasks(user_id)

    return {
        "assigned": [
            {"id": t.id, "title": t.title, "status": t.status.value, "due_date": t.due_date.isoformat() if t.due_date else None}
            for t in tasks["assigned"]
        ],
        "created": [
            {"id": t.id, "title": t.title, "status": t.status.value}
            for t in tasks["created"]
        ],
        "completed": [
            {"id": t.id, "title": t.title, "completed_at": t.completed_at.isoformat() if t.completed_at else None}
            for t in tasks["completed"]
        ]
    }


@router.get("/tasks/{task_id}")
async def get_task_detail(task_id: str):
    """获取任务详情"""
    service = get_collaboration_task_service()
    task = service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type.value,
        "priority": task.priority.value,
        "status": task.status.value,
        "creator_id": task.creator_id,
        "assignee_id": task.assignee_id,
        "participants": task.participants,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "estimated_hours": task.estimated_hours,
        "actual_hours": task.actual_hours,
        "checklist": task.checklist,
        "deliverables": task.deliverables,
        "created_at": task.created_at.isoformat()
    }


@router.post("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    request: UpdateTaskStatusRequest,
    user_id: str = Depends(get_current_user)
):
    """更新任务状态"""
    service = get_collaboration_task_service()

    try:
        status = TaskStatus(request.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")

    task = service.update_task(task_id, user_id, status=status)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "message": "Status updated successfully",
        "task_id": task.id,
        "new_status": task.status.value
    }


@router.post("/tasks/{task_id}/comments")
async def add_task_comment(
    task_id: str,
    request: TaskCommentRequest,
    user_id: str = Depends(get_current_user)
):
    """添加任务评论"""
    service = get_collaboration_task_service()

    comment = service.add_task_comment(
        task_id=task_id,
        author_id=user_id,
        content=request.content,
        parent_id=request.parent_id
    )

    return {
        "message": "Comment added",
        "comment_id": comment.id,
        "mentions": comment.mentions
    }


@router.get("/tasks/{task_id}/comments")
async def get_task_comments(task_id: str):
    """获取任务评论"""
    service = get_collaboration_task_service()
    comments = service._comments.get(task_id, [])

    return {
        "comments": [
            {
                "id": c.id,
                "author_id": c.author_id,
                "content": c.content,
                "created_at": c.created_at.isoformat(),
                "mentions": c.mentions
            }
            for c in comments
        ]
    }


# ==================== 推送通知API ====================

@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    user_id: str = Depends(get_current_user)
):
    """获取通知"""
    service = get_collaboration_task_service()
    pushes = service.get_user_pushes(user_id, unread_only, limit)

    return {
        "notifications": [
            {
                "id": p.id,
                "type": p.push_type,
                "title": p.title,
                "content": p.content,
                "is_read": p.is_read,
                "created_at": p.created_at.isoformat()
            }
            for p in pushes
        ]
    }


@router.post("/notifications/{push_id}/read")
async def mark_notification_read(
    push_id: str,
    user_id: str = Depends(get_current_user)
):
    """标记通知已读"""
    service = get_collaboration_task_service()
    success = service.mark_push_read(push_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Marked as read"}


# ==================== 日程管理API ====================

@router.post("/schedules")
async def create_schedule(
    request: CreateScheduleRequest,
    user_id: str = Depends(get_current_user)
):
    """创建日程"""
    service = get_collaboration_task_service()

    schedule = service.create_schedule(
        title=request.title,
        description=request.description,
        schedule_type=request.schedule_type,
        organizer_id=user_id,
        start_time=request.start_time,
        end_time=request.end_time,
        attendees=request.attendees,
        meeting_link=request.meeting_link,
        location=request.location
    )

    return {
        "message": "Schedule created",
        "schedule": {
            "id": schedule.id,
            "title": schedule.title,
            "start_time": schedule.start_time.isoformat()
        }
    }


@router.get("/schedules")
async def get_schedules(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: str = Depends(get_current_user)
):
    """获取日程"""
    service = get_collaboration_task_service()
    schedules = service.get_schedules(user_id, start_date, end_date)

    return {
        "schedules": [
            {
                "id": s.id,
                "title": s.title,
                "type": s.schedule_type,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "meeting_link": s.meeting_link,
                "location": s.location
            }
            for s in schedules
        ]
    }


# ==================== 论文协作API ====================

@router.post("/papers/{paper_id}/collaboration")
async def create_paper_collaboration(
    paper_id: str,
    target_journal: Optional[str] = None,
    target_deadline: Optional[datetime] = None,
    user_id: str = Depends(get_current_user)
):
    """创建论文协作"""
    service = get_collaboration_task_service()

    collab = service.create_paper_collaboration(
        paper_id=paper_id,
        lead_author=user_id,
        target_journal=target_journal,
        target_deadline=target_deadline
    )

    return {
        "message": "Paper collaboration created",
        "collaboration_id": collab.id
    }


@router.post("/papers/collaboration/{collab_id}/members")
async def add_paper_collaborator(
    collab_id: str,
    user_id: str,
    role: str,  # co_author/reviewer/viewer
    requester_id: str = Depends(get_current_user)
):
    """添加论文协作者"""
    service = get_collaboration_task_service()

    collab = service.add_paper_collaborator(collab_id, user_id, role)

    if not collab:
        raise HTTPException(status_code=404, detail="Collaboration not found")

    return {
        "message": f"Added as {role}",
        "collaboration_id": collab.id,
        "added_user": user_id
    }


# ==================== 工作负载API ====================

@router.get("/workload")
async def get_workload(
    team_id: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """获取工作负载"""
    service = get_collaboration_task_service()
    stats = service.get_workload_stats(user_id, team_id)

    return {
        "user_id": user_id,
        "total_tasks": stats.total_tasks,
        "by_status": {
            "todo": stats.todo_count,
            "in_progress": stats.in_progress_count,
            "review": stats.review_count,
            "done": stats.done_count
        },
        "time_distribution": {
            "this_week": stats.tasks_due_this_week,
            "next_week": stats.tasks_due_next_week,
            "overdue": stats.overdue_tasks
        },
        "efficiency": {
            "completion_rate": round(stats.completion_rate, 2),
            "on_time_rate": round(stats.on_time_rate, 2),
            "estimated_hours": stats.total_estimated_hours,
            "actual_hours": stats.total_actual_hours
        }
    }
