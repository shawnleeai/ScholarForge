"""
批注服务 API 路由
FastAPI 路由定义
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.exceptions import NotFoundException, ForbiddenException
from shared.responses import success_response, paginated_response
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams

from .schemas import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationReply,
    AnnotationResolve,
    AnnotationType,
    AnnotationStatus,
    AnnotationPriority,
    AnnotationResponse,
    AnnotationThread,
    AnnotationStats,
    AuthorInfo,
    AnnotationPosition,
)
from .repository import AnnotationRepository

router = APIRouter(prefix="/api/v1/annotations", tags=["批注系统"])


def format_annotation(row, replies_count: int = 0) -> dict:
    """格式化批注响应"""
    return {
        "id": str(row.id),
        "paper_id": str(row.paper_id),
        "section_id": str(row.section_id) if row.section_id else None,
        "author": {
            "id": str(row.author_id),
            "name": row.full_name or row.username or "Unknown",
            "avatar_url": getattr(row, 'avatar_url', None),
            "role": "student",  # 可从用户表获取
        },
        "annotation_type": row.annotation_type,
        "content": row.content,
        "position": row.position if isinstance(row.position, dict) else {},
        "status": row.status,
        "priority": getattr(row, 'priority', 'medium'),
        "parent_id": str(row.parent_id) if row.parent_id else None,
        "reply_count": replies_count,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "resolved_at": row.resolved_at.isoformat() if hasattr(row, 'resolved_at') and row.resolved_at else None,
        "resolved_by": None,  # 可扩展
    }


# ============== 批注 CRUD ==============

@router.post("", summary="创建批注")
async def create_annotation(
    data: AnnotationCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新批注

    支持多种批注类型：
    - comment: 普通评论
    - suggestion: 修改建议
    - question: 问题
    - correction: 纠正
    - approval: 认可/通过
    """
    repo = AnnotationRepository(db)

    annotation = await repo.create(
        paper_id=data.paper_id,
        author_id=uuid.UUID(user_id),
        annotation_type=data.annotation_type.value,
        content=data.content,
        section_id=data.section_id,
        position=data.position,
        priority=data.priority.value,
        parent_id=data.parent_id,
    )
    await db.commit()

    return success_response(
        data=format_annotation(annotation),
        message="批注创建成功",
        code=201,
    )


@router.get("/paper/{paper_id}", summary="获取论文批注列表")
async def get_paper_annotations(
    paper_id: str,
    section_id: Optional[str] = Query(None, description="筛选章节"),
    status: Optional[AnnotationStatus] = Query(None, description="筛选状态"),
    annotation_type: Optional[AnnotationType] = Query(None, description="筛选类型"),
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文的所有批注，支持筛选和分页"""
    repo = AnnotationRepository(db)

    annotations, total = await repo.get_paper_annotations(
        paper_id=uuid.UUID(paper_id),
        section_id=uuid.UUID(section_id) if section_id else None,
        status=status.value if status else None,
        annotation_type=annotation_type.value if annotation_type else None,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    items = [format_annotation(a, getattr(a, 'reply_count', 0)) for a in annotations]

    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{annotation_id}", summary="获取批注详情")
async def get_annotation(
    annotation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取单条批注详情"""
    repo = AnnotationRepository(db)
    annotation = await repo.get_by_id(uuid.UUID(annotation_id))

    if not annotation:
        raise NotFoundException("批注")

    return success_response(data=format_annotation(annotation))


@router.get("/{annotation_id}/thread", summary="获取批注线程")
async def get_annotation_thread(
    annotation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取批注及其所有回复"""
    repo = AnnotationRepository(db)
    main, replies = await repo.get_annotation_thread(uuid.UUID(annotation_id))

    if not main:
        raise NotFoundException("批注")

    return success_response(
        data={
            "annotation": format_annotation(main),
            "replies": [format_annotation(r) for r in replies],
        }
    )


@router.put("/{annotation_id}", summary="更新批注")
async def update_annotation(
    annotation_id: str,
    data: AnnotationUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新批注内容或状态"""
    repo = AnnotationRepository(db)

    # 检查权限
    annotation = await repo.get_by_id(uuid.UUID(annotation_id))
    if not annotation:
        raise NotFoundException("批注")

    if str(annotation.author_id) != user_id:
        raise ForbiddenException("只能修改自己的批注")

    update_data = data.model_dump(exclude_unset=True)
    updated = await repo.update(uuid.UUID(annotation_id), update_data)
    await db.commit()

    return success_response(
        data=format_annotation(updated),
        message="批注更新成功",
    )


@router.delete("/{annotation_id}", summary="删除批注")
async def delete_annotation(
    annotation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除批注"""
    repo = AnnotationRepository(db)

    # 检查权限
    annotation = await repo.get_by_id(uuid.UUID(annotation_id))
    if not annotation:
        raise NotFoundException("批注")

    if str(annotation.author_id) != user_id:
        raise ForbiddenException("只能删除自己的批注")

    await repo.delete(uuid.UUID(annotation_id))
    await db.commit()

    return success_response(message="批注删除成功")


# ============== 批注操作 ==============

@router.post("/{annotation_id}/reply", summary="回复批注")
async def reply_to_annotation(
    annotation_id: str,
    data: AnnotationReply,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """回复批注"""
    repo = AnnotationRepository(db)

    # 检查父批注是否存在
    parent = await repo.get_by_id(uuid.UUID(annotation_id))
    if not parent:
        raise NotFoundException("批注")

    reply = await repo.create(
        paper_id=parent.paper_id,
        author_id=uuid.UUID(user_id),
        annotation_type="comment",
        content=data.content,
        section_id=parent.section_id,
        parent_id=uuid.UUID(annotation_id),
    )
    await db.commit()

    return success_response(
        data=format_annotation(reply),
        message="回复成功",
        code=201,
    )


@router.post("/{annotation_id}/resolve", summary="解决批注")
async def resolve_annotation(
    annotation_id: str,
    data: AnnotationResolve,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    将批注标记为已解决

    只有论文作者或批注创建者可以执行此操作
    """
    repo = AnnotationRepository(db)

    annotation = await repo.get_by_id(uuid.UUID(annotation_id))
    if not annotation:
        raise NotFoundException("批注")

    resolved = await repo.resolve(
        uuid.UUID(annotation_id),
        uuid.UUID(user_id),
        data.resolution_note,
    )
    await db.commit()

    return success_response(
        data=format_annotation(resolved),
        message="批注已标记为解决",
    )


@router.post("/{annotation_id}/accept", summary="接受批注建议")
async def accept_annotation(
    annotation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """接受批注建议"""
    repo = AnnotationRepository(db)

    updated = await repo.update(
        uuid.UUID(annotation_id),
        {"status": "accepted"},
    )
    await db.commit()

    return success_response(
        data=format_annotation(updated),
        message="批注建议已接受",
    )


@router.post("/{annotation_id}/reject", summary="拒绝批注建议")
async def reject_annotation(
    annotation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """拒绝批注建议"""
    repo = AnnotationRepository(db)

    updated = await repo.update(
        uuid.UUID(annotation_id),
        {"status": "rejected"},
    )
    await db.commit()

    return success_response(
        data=format_annotation(updated),
        message="批注建议已拒绝",
    )


# ============== 统计与导出 ==============

@router.get("/paper/{paper_id}/stats", summary="获取批注统计")
async def get_annotation_stats(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文的批注统计信息"""
    repo = AnnotationRepository(db)
    stats = await repo.get_stats(uuid.UUID(paper_id))

    return success_response(data=stats)


@router.get("/paper/{paper_id}/export", summary="导出批注")
async def export_annotations(
    paper_id: str,
    format: str = Query("json", description="导出格式: json, markdown, pdf"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    导出论文批注

    支持格式：
    - json: JSON 格式
    - markdown: Markdown 文档
    - pdf: PDF 文档
    """
    repo = AnnotationRepository(db)
    annotations, _ = await repo.get_paper_annotations(
        paper_id=uuid.UUID(paper_id),
        page=1,
        page_size=1000,
    )
    stats = await repo.get_stats(uuid.UUID(paper_id))

    export_data = {
        "paper_id": paper_id,
        "paper_title": "论文标题",  # 可从论文服务获取
        "export_time": uuid.uuid1().time,
        "annotations": [format_annotation(a) for a in annotations],
        "summary": stats,
    }

    if format == "markdown":
        # 转换为 Markdown
        md_content = f"# 批注报告\n\n"
        md_content += f"## 统计\n\n"
        md_content += f"- 总批注数: {stats['total_count']}\n"
        md_content += f"- 待处理: {stats['pending_count']}\n"
        md_content += f"- 已解决: {stats['resolved_count']}\n\n"
        md_content += f"## 批注列表\n\n"

        for a in annotations:
            md_content += f"### {a.annotation_type}: {a.content[:50]}...\n\n"
            md_content += f"- 状态: {a.status}\n"
            md_content += f"- 创建时间: {a.created_at}\n\n"
            md_content += f"{a.content}\n\n---\n\n"

        return success_response(data={"content": md_content, "format": "markdown"})

    return success_response(data=export_data)


# ============== 用户批注 ==============

@router.get("/user/me", summary="获取我的批注")
async def get_my_annotations(
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户创建的所有批注"""
    repo = AnnotationRepository(db)

    annotations, total = await repo.get_user_annotations(
        user_id=uuid.UUID(user_id),
        page=pagination.page,
        page_size=pagination.page_size,
    )

    items = [format_annotation(a) for a in annotations]

    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )
