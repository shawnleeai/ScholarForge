"""
AI科研助手Agent API路由
提供Agent会话管理、对话、任务执行、主动建议等API
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import asyncio

from .service import get_ai_agent_service, TaskType, AgentStatus

router = APIRouter(prefix="/ai-agent", tags=["ai-agent"])


# ==================== 请求/响应模型 ====================

class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    title: str = Field(..., min_length=1, max_length=200)
    task_type: str = Field(..., description="research/writing/analysis/coding/planning/review/brainstorming")
    context: Optional[dict] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., min_length=1, max_length=5000)
    stream: bool = Field(default=True)


class CreatePlanRequest(BaseModel):
    """创建研究计划请求"""
    title: str = Field(..., min_length=1, max_length=200)
    objectives: List[str] = Field(..., min_items=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class UpdateProgressRequest(BaseModel):
    """更新进度请求"""
    milestone_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str = Field(default="completed")


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== 会话管理API ====================

@router.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    user_id: str = Depends(get_current_user)
):
    """创建Agent会话"""
    service = get_ai_agent_service()

    try:
        task_type = TaskType(request.task_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task type")

    session = service.create_session(
        user_id=user_id,
        title=request.title,
        task_type=task_type,
        context=request.context
    )

    return {
        "message": "Session created successfully",
        "session": {
            "id": session.id,
            "title": session.title,
            "task_type": session.task_type.value,
            "status": session.status.value,
            "created_at": session.created_at.isoformat()
        }
    }


@router.get("/sessions")
async def list_sessions(
    task_type: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """列出用户会话"""
    service = get_ai_agent_service()

    task_type_enum = None
    if task_type:
        try:
            task_type_enum = TaskType(task_type)
        except ValueError:
            pass

    sessions = service.list_sessions(user_id, task_type_enum)

    return {
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "task_type": s.task_type.value,
                "status": s.status.value,
                "message_count": len(s.messages),
                "updated_at": s.updated_at.isoformat()
            }
            for s in sessions
        ]
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, user_id: str = Depends(get_current_user)):
    """获取会话详情"""
    service = get_ai_agent_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": session.id,
        "title": session.title,
        "task_type": session.task_type.value,
        "status": session.status.value,
        "context": session.context,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content[:200] + "..." if len(m.content) > 200 else m.content,
                "created_at": m.created_at.isoformat(),
                "metadata": m.metadata
            }
            for m in session.messages
        ],
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str = Depends(get_current_user)):
    """删除会话"""
    service = get_ai_agent_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    del service._sessions[session_id]

    return {"message": "Session deleted successfully"}


# ==================== 对话API ====================

@router.post("/sessions/{session_id}/chat")
async def chat(
    session_id: str,
    request: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    """与Agent对话（流式）"""
    service = get_ai_agent_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    async def event_generator():
        async for chunk in service.chat(session_id, request.message, stream=True):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/sessions/{session_id}/chat/sync")
async def chat_sync(
    session_id: str,
    request: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    """与Agent对话（非流式）"""
    service = get_ai_agent_service()
    session = service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    response_parts = []
    async for chunk in service.chat(session_id, request.message, stream=False):
        data = json.loads(chunk)
        if data.get("type") == "complete":
            response_parts.append(data.get("content", ""))

    return {
        "message": "Chat completed",
        "response": "".join(response_parts)
    }


# ==================== 研究计划API ====================

@router.post("/plans")
async def create_research_plan(
    request: CreatePlanRequest,
    user_id: str = Depends(get_current_user)
):
    """创建研究计划"""
    service = get_ai_agent_service()

    plan = service.create_research_plan(
        user_id=user_id,
        title=request.title,
        objectives=request.objectives,
        start_date=request.start_date,
        end_date=request.end_date
    )

    return {
        "message": "Research plan created",
        "plan": {
            "id": plan.id,
            "title": plan.title,
            "objectives": plan.objectives,
            "milestones": plan.milestones,
            "tasks": plan.tasks,
            "created_at": plan.created_at.isoformat()
        }
    }


@router.get("/plans")
async def list_research_plans(user_id: str = Depends(get_current_user)):
    """列出研究计划"""
    service = get_ai_agent_service()
    plans = service.list_research_plans(user_id)

    return {
        "plans": [
            {
                "id": p.id,
                "title": p.title,
                "objectives_count": len(p.objectives),
                "milestones_count": len(p.milestones),
                "tasks_count": len(p.tasks),
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "end_date": p.end_date.isoformat() if p.end_date else None,
                "created_at": p.created_at.isoformat()
            }
            for p in plans
        ]
    }


@router.get("/plans/{plan_id}")
async def get_research_plan(plan_id: str, user_id: str = Depends(get_current_user)):
    """获取研究计划详情"""
    service = get_ai_agent_service()
    plan = service.get_research_plan(plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": plan.id,
        "title": plan.title,
        "objectives": plan.objectives,
        "milestones": plan.milestones,
        "tasks": plan.tasks,
        "risks": plan.risks,
        "start_date": plan.start_date.isoformat() if plan.start_date else None,
        "end_date": plan.end_date.isoformat() if plan.end_date else None,
        "created_at": plan.created_at.isoformat(),
        "updated_at": plan.updated_at.isoformat()
    }


@router.post("/plans/{plan_id}/progress")
async def update_plan_progress(
    plan_id: str,
    request: UpdateProgressRequest,
    user_id: str = Depends(get_current_user)
):
    """更新计划进度"""
    service = get_ai_agent_service()
    plan = service.get_research_plan(plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    updated_plan = service.update_plan_progress(
        plan_id=plan_id,
        milestone_id=request.milestone_id,
        task_id=request.task_id,
        status=request.status
    )

    return {
        "message": "Progress updated",
        "plan_id": updated_plan.id
    }


# ==================== 主动建议API ====================

@router.get("/suggestions")
async def get_suggestions(
    include_dismissed: bool = False,
    user_id: str = Depends(get_current_user)
):
    """获取主动建议"""
    service = get_ai_agent_service()

    # 先生成新建议
    service.generate_proactive_suggestions(user_id)

    # 获取建议
    suggestions = service.get_suggestions(user_id, include_dismissed)

    return {
        "suggestions": [
            {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "action_type": s.action_type,
                "is_accepted": s.is_accepted,
                "is_dismissed": s.is_dismissed,
                "created_at": s.created_at.isoformat()
            }
            for s in suggestions
        ]
    }


@router.post("/suggestions/{suggestion_id}/accept")
async def accept_suggestion(
    suggestion_id: str,
    user_id: str = Depends(get_current_user)
):
    """接受建议"""
    service = get_ai_agent_service()
    success = service.accept_suggestion(suggestion_id)

    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    return {"message": "Suggestion accepted"}


@router.post("/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(
    suggestion_id: str,
    user_id: str = Depends(get_current_user)
):
    """忽略建议"""
    service = get_ai_agent_service()
    success = service.dismiss_suggestion(suggestion_id)

    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    return {"message": "Suggestion dismissed"}


# ==================== 任务执行API ====================

@router.post("/tasks")
async def create_task(
    session_id: str,
    description: str,
    user_id: str = Depends(get_current_user)
):
    """创建Agent任务"""
    service = get_ai_agent_service()

    session = service.get_session(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    task = service.create_task(
        session_id=session_id,
        description=description
    )

    return {
        "message": "Task created",
        "task": {
            "id": task.id,
            "description": task.description,
            "status": task.status,
            "created_at": task.created_at.isoformat()
        }
    }


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, user_id: str = Depends(get_current_user)):
    """获取任务状态"""
    service = get_ai_agent_service()
    task = service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": task.id,
        "description": task.description,
        "status": task.status,
        "progress": task.progress,
        "current_step": task.current_step_index,
        "total_steps": len(task.steps),
        "result": task.result,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None
    }


@router.post("/tasks/{task_id}/execute")
async def execute_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """执行任务"""
    service = get_ai_agent_service()
    task = service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        async for update in service.execute_task(task_id):
            yield f"data: {json.dumps(update)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# ==================== 快捷入口API ====================

@router.post("/quick/research")
async def quick_research(
    topic: str,
    user_id: str = Depends(get_current_user)
):
    """快速研究入口 - 一键开始文献调研"""
    service = get_ai_agent_service()

    # 创建会话
    session = service.create_session(
        user_id=user_id,
        title=f"调研：{topic[:30]}",
        task_type=TaskType.RESEARCH,
        context={"topic": topic}
    )

    # 创建研究计划
    plan = service.create_research_plan(
        user_id=user_id,
        title=f"研究计划：{topic}",
        objectives=[f"深入研究{topic}", "撰写综述论文"],
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + datetime.resolution * 90  # 90天后
    )

    return {
        "message": "Quick research session created",
        "session_id": session.id,
        "plan_id": plan.id,
        "suggested_actions": [
            "搜索相关文献",
            "生成研究大纲",
            "创建文献综述"
        ]
    }


@router.post("/quick/writing")
async def quick_writing(
    title: str,
    section: str = "introduction",
    user_id: str = Depends(get_current_user)
):
    """快速写作入口 - 一键开始论文写作"""
    service = get_ai_agent_service()

    session = service.create_session(
        user_id=user_id,
        title=f"写作：{title[:30]}",
        task_type=TaskType.WRITING,
        context={"paper_title": title, "section": section}
    )

    return {
        "message": "Quick writing session created",
        "session_id": session.id,
        "suggested_outline": [
            "1. 研究背景与动机",
            "2. 问题陈述",
            "3. 主要贡献",
            "4. 论文结构"
        ]
    }


@router.get("/capabilities")
async def get_capabilities():
    """获取Agent能力列表"""
    return {
        "task_types": [
            {"id": "research", "name": "文献调研", "description": "帮助搜索和分析学术文献"},
            {"id": "writing", "name": "写作辅助", "description": "协助撰写和润色论文"},
            {"id": "analysis", "name": "数据分析", "description": "分析实验数据并提供建议"},
            {"id": "coding", "name": "代码辅助", "description": "编写和调试研究代码"},
            {"id": "planning", "name": "研究规划", "description": "制定研究计划和时间安排"},
            {"id": "review", "name": "论文审阅", "description": "审阅论文并提供改进建议"},
            {"id": "brainstorming", "name": "头脑风暴", "description": "激发研究灵感和创意"}
        ],
        "features": [
            "多轮对话记忆",
            "工具调用",
            "主动建议",
            "研究计划管理",
            "流式响应"
        ],
        "supported_tools": [
            "search_papers",
            "read_paper",
            "generate_content",
            "check_grammar",
            "format_references",
            "create_outline",
            "summarize",
            "translate"
        ]
    }
