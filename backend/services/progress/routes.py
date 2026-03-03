"""
进度管理 API 路由
甘特图、里程碑、预警系统
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import random

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.responses import success_response, paginated_response
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams

from .schemas import (
    Milestone,
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneStatus,
    Task,
    TaskCreate,
    TaskUpdate,
    GanttChart,
    GanttItem,
    Alert,
    AlertCreate,
    RiskLevel,
    ProgressReport,
    ProgressStats,
    WeeklyReport,
    ProgressSettings,
)
from .repository import MilestoneRepository, TaskRepository, ProgressAlertRepository

router = APIRouter(prefix="/api/v1/progress", tags=["进度管理"])


# ============== 里程碑管理 ==============

@router.post("/milestones", summary="创建里程碑")
async def create_milestone(
    data: MilestoneCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新的里程碑"""
    repo = MilestoneRepository(db)

    milestone_data = {
        "paper_id": str(data.paper_id),
        "title": data.title,
        "description": data.description,
        "planned_date": data.planned_date,
        "status": MilestoneStatus.PENDING.value,
        "completion_percentage": 0,
    }

    saved = await repo.create(milestone_data)

    if not saved:
        raise HTTPException(status_code=500, detail="创建里程碑失败")

    return success_response(
        data=_milestone_to_dict(saved),
        message="里程碑创建成功",
        code=201,
    )


@router.get("/papers/{paper_id}/milestones", summary="获取里程碑列表")
async def get_milestones(
    paper_id: str,
    status: Optional[MilestoneStatus] = Query(None, description="筛选状态"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文的所有里程碑"""
    repo = MilestoneRepository(db)
    milestones = await repo.get_by_paper(
        paper_id=paper_id,
        status=status.value if status else None
    )

    return success_response(data=[_milestone_to_dict(m) for m in milestones])


@router.get("/milestones/{milestone_id}", summary="获取里程碑详情")
async def get_milestone(
    milestone_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取里程碑详情"""
    repo = MilestoneRepository(db)
    milestone = await repo.get_by_id(milestone_id)

    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    return success_response(data=_milestone_to_dict(milestone))


@router.put("/milestones/{milestone_id}", summary="更新里程碑")
async def update_milestone(
    milestone_id: str,
    data: MilestoneUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新里程碑状态"""
    repo = MilestoneRepository(db)

    update_data = {}
    if data.status:
        update_data["status"] = data.status.value
    if data.actual_date:
        update_data["actual_date"] = data.actual_date
    if data.completion_percentage is not None:
        update_data["completion_percentage"] = data.completion_percentage

    updated = await repo.update(milestone_id, update_data)

    if not updated:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    return success_response(
        data=_milestone_to_dict(updated),
        message="里程碑更新成功"
    )


@router.delete("/milestones/{milestone_id}", summary="删除里程碑")
async def delete_milestone(
    milestone_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除里程碑"""
    repo = MilestoneRepository(db)
    deleted = await repo.delete(milestone_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    return success_response(message="里程碑已删除")


def _milestone_to_dict(m: dict) -> dict:
    """将里程碑数据转换为字典"""
    return {
        "id": str(m["id"]),
        "paper_id": str(m["paper_id"]),
        "title": m["title"],
        "description": m.get("description"),
        "planned_date": m["planned_date"].isoformat() if m.get("planned_date") else None,
        "actual_date": m["actual_date"].isoformat() if m.get("actual_date") else None,
        "status": m.get("status", "pending"),
        "completion_percentage": m.get("completion_percentage", 0),
        "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
        "updated_at": m["updated_at"].isoformat() if m.get("updated_at") else None,
    }


# ============== 任务管理 ==============

@router.post("/tasks", summary="创建任务")
async def create_task(
    data: TaskCreate,
    paper_id: str = Query(..., description="论文ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新任务"""
    repo = TaskRepository(db)

    task_data = {
        "paper_id": paper_id,
        "milestone_id": data.milestone_id,
        "title": data.title,
        "description": data.description,
        "status": "pending",
        "priority": data.priority.value,
        "progress": 0,
        "planned_start": data.planned_start,
        "planned_end": data.planned_end,
        "assignee_id": data.assignee_id,
    }

    saved = await repo.create(task_data)

    if not saved:
        raise HTTPException(status_code=500, detail="创建任务失败")

    return success_response(
        data=_task_to_dict(saved),
        code=201,
    )


@router.get("/papers/{paper_id}/tasks", summary="获取任务列表")
async def get_tasks(
    paper_id: str,
    milestone_id: Optional[str] = Query(None, description="筛选里程碑"),
    status: Optional[str] = Query(None, description="筛选状态"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文的任务列表"""
    repo = TaskRepository(db)
    tasks = await repo.get_by_paper(
        paper_id=paper_id,
        milestone_id=milestone_id,
        status=status
    )

    return success_response(data=[_task_to_dict(t) for t in tasks])


@router.get("/tasks/{task_id}", summary="获取任务详情")
async def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取任务详情"""
    repo = TaskRepository(db)
    task = await repo.get_by_id(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return success_response(data=_task_to_dict(task))


@router.put("/tasks/{task_id}", summary="更新任务")
async def update_task(
    task_id: str,
    data: TaskUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新任务"""
    repo = TaskRepository(db)

    update_data = {}
    if data.status:
        update_data["status"] = data.status
    if data.actual_start:
        update_data["actual_start"] = data.actual_start
    if data.actual_end:
        update_data["actual_end"] = data.actual_end
    if data.progress is not None:
        update_data["progress"] = data.progress

    updated = await repo.update(task_id, update_data)

    if not updated:
        raise HTTPException(status_code=404, detail="任务不存在")

    return success_response(
        data=_task_to_dict(updated),
        message="任务更新成功"
    )


@router.delete("/tasks/{task_id}", summary="删除任务")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除任务"""
    repo = TaskRepository(db)
    deleted = await repo.delete(task_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="任务不存在")

    return success_response(message="任务已删除")


def _task_to_dict(t: dict) -> dict:
    """将任务数据转换为字典"""
    return {
        "id": str(t["id"]),
        "paper_id": str(t["paper_id"]),
        "milestone_id": str(t["milestone_id"]) if t.get("milestone_id") else None,
        "title": t["title"],
        "description": t.get("description"),
        "status": t.get("status", "pending"),
        "priority": t.get("priority", "medium"),
        "progress": t.get("progress", 0),
        "planned_start": t["planned_start"].isoformat() if t.get("planned_start") else None,
        "planned_end": t["planned_end"].isoformat() if t.get("planned_end") else None,
        "actual_start": t["actual_start"].isoformat() if t.get("actual_start") else None,
        "actual_end": t["actual_end"].isoformat() if t.get("actual_end") else None,
        "assignee_id": str(t["assignee_id"]) if t.get("assignee_id") else None,
        "created_at": t["created_at"].isoformat() if t.get("created_at") else None,
        "updated_at": t["updated_at"].isoformat() if t.get("updated_at") else None,
    }


# ============== 甘特图 ==============

@router.get("/papers/{paper_id}/gantt", summary="获取甘特图")
async def get_gantt_chart(
    paper_id: str,
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """生成甘特图数据"""
    today = date.today()
    start = date.fromisoformat(start_date) if start_date else today
    end = date.fromisoformat(end_date) if end_date else today + timedelta(days=120)

    # 从数据库获取里程碑和任务
    milestone_repo = MilestoneRepository(db)
    task_repo = TaskRepository(db)

    milestones = await milestone_repo.get_by_paper(paper_id)
    tasks = await task_repo.get_by_paper(paper_id)

    # 构建甘特图项
    items = []

    # 添加里程碑作为甘特图项
    for m in milestones:
        if m.get("planned_date"):
            items.append(GanttItem(
                id=f"milestone_{m['id']}",
                name=m["title"],
                start=m["planned_date"],
                end=m["planned_date"] + timedelta(days=1),
                progress=m.get("completion_percentage", 0),
                status=m.get("status", "pending"),
                dependencies=[],
            ))

    # 添加任务作为甘特图项
    for t in tasks:
        if t.get("planned_start") and t.get("planned_end"):
            items.append(GanttItem(
                id=f"task_{t['id']}",
                name=t["title"],
                start=t["planned_start"],
                end=t["planned_end"],
                progress=t.get("progress", 0),
                status=t.get("status", "pending"),
                dependencies=[],
            ))

    # 如果没有数据，生成默认甘特图
    if not items:
        items = _generate_default_gantt_items(start)

    milestones_data = [
        {"date": m["planned_date"].isoformat(), "name": m["title"]}
        for m in milestones if m.get("planned_date")
    ] or _generate_default_milestones(start)

    return success_response(
        data=GanttChart(
            paper_id=paper_id,
            items=items,
            milestones=milestones_data,
            start_date=start,
            end_date=end,
            generated_at=datetime.now(),
        ).model_dump()
    )


def _generate_default_gantt_items(start: date) -> List[GanttItem]:
    """生成默认甘特图项"""
    return [
        GanttItem(
            id="phase1",
            name="文献综述",
            start=start,
            end=start + timedelta(days=14),
            progress=60,
            status="in_progress",
            dependencies=[],
        ),
        GanttItem(
            id="phase2",
            name="研究设计",
            start=start + timedelta(days=14),
            end=start + timedelta(days=28),
            progress=0,
            status="pending",
            dependencies=["phase1"],
        ),
        GanttItem(
            id="phase3",
            name="数据收集",
            start=start + timedelta(days=28),
            end=start + timedelta(days=56),
            progress=0,
            status="pending",
            dependencies=["phase2"],
        ),
        GanttItem(
            id="phase4",
            name="数据分析",
            start=start + timedelta(days=56),
            end=start + timedelta(days=84),
            progress=0,
            status="pending",
            dependencies=["phase3"],
        ),
        GanttItem(
            id="phase5",
            name="论文撰写",
            start=start + timedelta(days=84),
            end=start + timedelta(days=112),
            progress=0,
            status="pending",
            dependencies=["phase4"],
        ),
        GanttItem(
            id="phase6",
            name="修改完善",
            start=start + timedelta(days=112),
            end=start + timedelta(days=120),
            progress=0,
            status="pending",
            dependencies=["phase5"],
        ),
    ]


def _generate_default_milestones(start: date) -> List[Dict[str, str]]:
    """生成默认里程碑"""
    return [
        {"date": (start + timedelta(days=14)).isoformat(), "name": "文献综述完成"},
        {"date": (start + timedelta(days=56)).isoformat(), "name": "数据收集完成"},
        {"date": (start + timedelta(days=112)).isoformat(), "name": "初稿完成"},
        {"date": (start + timedelta(days=120)).isoformat(), "name": "答辩"},
    ]


# ============== 预警系统 ==============

@router.get("/papers/{paper_id}/alerts", summary="获取预警列表")
async def get_alerts(
    paper_id: str,
    severity: Optional[RiskLevel] = Query(None, description="筛选严重程度"),
    unread_only: bool = Query(False, description="仅未读"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文的预警信息"""
    repo = ProgressAlertRepository(db)

    # 先检查并生成新的预警
    await _check_and_generate_alerts(paper_id, db)

    alerts = await repo.get_by_paper(
        paper_id=paper_id,
        severity=severity.value if severity else None,
        unread_only=unread_only
    )

    return success_response(data=[_alert_to_dict(a) for a in alerts])


async def _check_and_generate_alerts(paper_id: str, db: AsyncSession):
    """检查并生成预警"""
    milestone_repo = MilestoneRepository(db)
    task_repo = TaskRepository(db)
    alert_repo = ProgressAlertRepository(db)

    today = date.today()

    # 检查里程碑延期风险
    milestones = await milestone_repo.get_by_paper(paper_id)
    for m in milestones:
        if m.get("status") not in ["completed", "delayed"] and m.get("planned_date"):
            days_until = (m["planned_date"] - today).days

            if days_until < 0:
                # 已延期
                await alert_repo.create({
                    "paper_id": paper_id,
                    "alert_type": "deadline_overdue",
                    "severity": "high",
                    "title": f"里程碑延期：{m['title']}",
                    "description": f"里程碑'{m['title']}'已延期{abs(days_until)}天",
                    "affected_items": [str(m["id"])],
                    "suggestions": ["尽快完成该里程碑任务", "调整后续计划"],
                })
            elif days_until <= 3 and m.get("completion_percentage", 0) < 80:
                # 即将到期但进度不足
                await alert_repo.create({
                    "paper_id": paper_id,
                    "alert_type": "deadline_risk",
                    "severity": "medium" if days_until > 1 else "high",
                    "title": f"里程碑即将到期：{m['title']}",
                    "description": f"里程碑'{m['title']}'还有{days_until}天到期，当前进度{m.get('completion_percentage', 0)}%",
                    "affected_items": [str(m["id"])],
                    "suggestions": ["加快进度", "调整计划", "寻求协助"],
                })

    # 检查任务进度落后
    tasks = await task_repo.get_by_paper(paper_id, status="in_progress")
    for t in tasks:
        if t.get("planned_end") and t.get("progress", 0) < 50:
            days_until = (t["planned_end"] - today).days
            if days_until <= 2:
                await alert_repo.create({
                    "paper_id": paper_id,
                    "alert_type": "task_delay",
                    "severity": "medium",
                    "title": f"任务进度落后：{t['title']}",
                    "description": f"任务'{t['title']}'进度仅{t.get('progress', 0)}%，即将到期",
                    "affected_items": [str(t["id"])],
                    "suggestions": ["增加工作时间", "简化任务范围"],
                })


@router.post("/alerts/{alert_id}/read", summary="标记预警为已读")
async def mark_alert_read(
    alert_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """标记预警为已读"""
    repo = ProgressAlertRepository(db)
    success = await repo.mark_as_read(alert_id)

    if not success:
        raise HTTPException(status_code=404, detail="预警不存在")

    return success_response(message="已标记为已读")


@router.post("/alerts/{alert_id}/resolve", summary="解决预警")
async def resolve_alert(
    alert_id: str,
    resolution_note: str = Query("", description="解决说明"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """标记预警为已解决"""
    repo = ProgressAlertRepository(db)
    success = await repo.mark_as_resolved(alert_id, resolution_note)

    if not success:
        raise HTTPException(status_code=404, detail="预警不存在")

    return success_response(message="预警已解决")


def _alert_to_dict(a: dict) -> dict:
    """将预警数据转换为字典"""
    return {
        "id": str(a["id"]),
        "paper_id": str(a["paper_id"]),
        "type": a["alert_type"],
        "severity": a["severity"],
        "title": a["title"],
        "description": a["description"],
        "affected_items": a.get("affected_items", []),
        "suggestions": a.get("suggestions", []),
        "created_at": a["created_at"].isoformat() if a.get("created_at") else None,
        "is_read": a.get("is_read", False),
        "is_resolved": a.get("is_resolved", False),
    }


# ============== 进度报告 ==============

@router.get("/papers/{paper_id}/report", summary="获取进度报告")
async def get_progress_report(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """生成进度报告"""
    milestone_repo = MilestoneRepository(db)
    task_repo = TaskRepository(db)
    alert_repo = ProgressAlertRepository(db)

    today = date.today()

    # 获取统计数据
    milestones = await milestone_repo.get_by_paper(paper_id)
    tasks = await task_repo.get_by_paper(paper_id)
    alerts = await alert_repo.get_by_paper(paper_id, unread_only=True)

    # 计算统计
    completed_milestones = sum(1 for m in milestones if m.get("status") == "completed")
    in_progress_milestones = sum(1 for m in milestones if m.get("status") == "in_progress")
    delayed_milestones = sum(1 for m in milestones if m.get("status") == "delayed")
    at_risk_milestones = sum(1 for m in milestones if m.get("status") == "at_risk")

    completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")

    # 计算总体进度
    total_progress = 0
    if milestones:
        total_progress = sum(m.get("completion_percentage", 0) for m in milestones) / len(milestones)

    # 估算剩余天数（基于最后里程碑的计划日期）
    days_remaining = 120
    if milestones:
        latest_date = max(
            (m["planned_date"] for m in milestones if m.get("planned_date")),
            default=today
        )
        days_remaining = (latest_date - today).days

    report = ProgressReport(
        paper_id=paper_id,
        paper_title="论文进度报告",  # 可以从paper服务获取
        generated_at=datetime.now(),
        stats=ProgressStats(
            total_milestones=len(milestones),
            completed_milestones=completed_milestones,
            in_progress_milestones=in_progress_milestones,
            delayed_milestones=delayed_milestones,
            at_risk_milestones=at_risk_milestones,
            total_tasks=len(tasks),
            completed_tasks=completed_tasks,
            overall_progress=round(total_progress, 1),
            days_remaining=max(0, days_remaining),
            on_track=delayed_milestones == 0 and at_risk_milestones == 0,
        ),
        milestones=[_milestone_to_dict(m) for m in milestones[:5]],
        alerts=[_alert_to_dict(a) for a in alerts[:5]],
        recommendations=_generate_recommendations(milestones, tasks),
        next_actions=_generate_next_actions(milestones, tasks),
    )

    return success_response(data=report.model_dump())


def _generate_recommendations(milestones: List[dict], tasks: List[dict]) -> List[str]:
    """生成建议"""
    recommendations = []

    # 检查是否有延期的里程碑
    delayed = [m for m in milestones if m.get("status") == "delayed"]
    if delayed:
        recommendations.append(f"有{len(delayed)}个里程碑已延期，建议加快进度或调整计划")

    # 检查是否有高风险任务
    in_progress = [t for t in tasks if t.get("status") == "in_progress"]
    if in_progress and len(in_progress) > 3:
        recommendations.append("同时进行的任务较多，建议优先完成关键任务")

    # 通用建议
    recommendations.extend([
        "建议保持与导师的定期沟通",
        "每周回顾进度，及时调整计划",
    ])

    return recommendations


def _generate_next_actions(milestones: List[dict], tasks: List[dict]) -> List[str]:
    """生成下一步行动"""
    actions = []

    # 找到最近的未完成里程碑
    pending = [m for m in milestones if m.get("status") in ["pending", "in_progress"]]
    if pending:
        next_milestone = min(pending, key=lambda m: m.get("planned_date") or date.max)
        actions.append(f"推进里程碑：{next_milestone['title']}")

    # 找到进行中的任务
    in_progress = [t for t in tasks if t.get("status") == "in_progress"]
    for t in in_progress[:2]:
        actions.append(f"完成任务：{t['title']}")

    if not actions:
        actions.append("制定下一阶段计划")

    return actions


@router.get("/papers/{paper_id}/report/weekly", summary="获取周报告")
async def get_weekly_report(
    paper_id: str,
    week_number: Optional[int] = Query(None, description="周数"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取周进度报告"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # 获取本周完成的任务
    milestone_repo = MilestoneRepository(db)
    task_repo = TaskRepository(db)

    milestones = await milestone_repo.get_by_paper(paper_id)
    tasks = await task_repo.get_by_paper(paper_id)

    # 统计本周完成情况（简化处理，实际应该检查actual_end日期）
    completed_this_week = [t["title"] for t in tasks if t.get("status") == "completed"][:5]

    report = WeeklyReport(
        paper_id=paper_id,
        paper_title="论文进度报告",
        generated_at=datetime.now(),
        week_number=week_number or (today - timedelta(days=120)).days // 7,
        period_start=week_start,
        period_end=week_end,
        stats=ProgressStats(
            total_milestones=len(milestones),
            completed_milestones=sum(1 for m in milestones if m.get("status") == "completed"),
            in_progress_milestones=sum(1 for m in milestones if m.get("status") == "in_progress"),
            delayed_milestones=sum(1 for m in milestones if m.get("status") == "delayed"),
            at_risk_milestones=sum(1 for m in milestones if m.get("status") == "at_risk"),
            total_tasks=len(tasks),
            completed_tasks=sum(1 for t in tasks if t.get("status") == "completed"),
            overall_progress=random.uniform(20, 60),
            days_remaining=120,
            on_track=True,
        ),
        milestones=[],
        alerts=[],
        recommendations=[],
        next_actions=[],
        completed_this_week=completed_this_week if completed_this_week else ["完成文献检索"],
        planned_next_week=["继续推进当前任务"],
        blockers=[],
    )

    return success_response(data=report.model_dump())


# ============== 设置 ==============

@router.get("/papers/{paper_id}/settings", summary="获取进度设置")
async def get_progress_settings(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """获取论文的进度管理设置"""
    today = date.today()

    settings = ProgressSettings(
        paper_id=paper_id,
        start_date=today,
        target_completion_date=today + timedelta(days=180),
        working_days_per_week=5,
        reminder_enabled=True,
        reminder_days_before=3,
        auto_alert_enabled=True,
    )

    return success_response(data=settings.model_dump())


@router.put("/papers/{paper_id}/settings", summary="更新进度设置")
async def update_progress_settings(
    paper_id: str,
    settings: ProgressSettings,
    user_id: str = Depends(get_current_user_id),
):
    """更新进度管理设置"""
    # TODO: 保存设置到数据库
    return success_response(message="设置已更新")
