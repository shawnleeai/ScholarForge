"""
论文管理服务 API 路由
FastAPI 路由定义
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.exceptions import NotFoundException, ForbiddenException, ConflictException
from shared.responses import success_response, paginated_response
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams

from .schemas import (
    PaperCreate,
    PaperUpdate,
    PaperResponse,
    PaperBrief,
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    CollaboratorAdd,
    CollaboratorUpdate,
    CollaboratorResponse,
    VersionCreate,
    VersionResponse,
    TemplateResponse,
    ExportRequest,
    ExportResponse,
    # 评论相关
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentReplyCreate,
    CommentReplyResponse,
    # 批注相关
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
)
from .repository import (
    PaperRepository,
    SectionRepository,
    CollaboratorRepository,
    VersionRepository,
    TemplateRepository,
)

router = APIRouter(prefix="/api/v1/papers", tags=["论文管理"])


# ============== 论文路由 ==============

@router.post("", summary="创建论文")
async def create_paper(
    paper_data: PaperCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新论文"""
    paper_repo = PaperRepository(db)
    paper = await paper_repo.create(
        owner_id=uuid.UUID(user_id),
        paper_data=paper_data.model_dump(),
    )
    await db.commit()

    return success_response(
        data=PaperResponse.model_validate(paper).model_dump(),
        message="论文创建成功",
        code=201,
    )


@router.get("", summary="获取论文列表")
async def get_papers(
    status: Optional[str] = None,
    include_collab: bool = Query(False, description="包含协作的论文"),
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户论文列表"""
    paper_repo = PaperRepository(db)

    # 获取自己的论文
    papers, total = await paper_repo.get_user_papers(
        user_id=uuid.UUID(user_id),
        status=status,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    # 如果需要，也获取协作的论文
    if include_collab:
        collab_papers, collab_total = await paper_repo.get_collaborator_papers(
            user_id=uuid.UUID(user_id),
            page=pagination.page,
            page_size=pagination.page_size,
        )
        papers.extend(collab_papers)
        total += collab_total

    return paginated_response(
        items=[PaperBrief.model_validate(p).model_dump() for p in papers],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{paper_id}", summary="获取论文详情")
async def get_paper(
    paper_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文详情"""
    paper_repo = PaperRepository(db)
    collab_repo = CollaboratorRepository(db)

    paper = await paper_repo.get_by_id(paper_id, with_sections=True)
    if not paper:
        raise NotFoundException("论文")

    # 检查权限
    is_owner = paper.owner_id == uuid.UUID(user_id)
    is_collab = await collab_repo.is_collaborator(paper_id, uuid.UUID(user_id))

    if not is_owner and not is_collab:
        raise ForbiddenException("您没有权限查看此论文")

    return success_response(data=PaperResponse.model_validate(paper).model_dump())


@router.put("/{paper_id}", summary="更新论文")
async def update_paper(
    paper_id: uuid.UUID,
    paper_data: PaperUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新论文信息"""
    paper_repo = PaperRepository(db)
    collab_repo = CollaboratorRepository(db)

    paper = await paper_repo.get_by_id(paper_id)
    if not paper:
        raise NotFoundException("论文")

    # 检查权限
    is_owner = paper.owner_id == uuid.UUID(user_id)

    if not is_owner:
        # 检查是否有编辑权限
        # 这里简化处理，实际需要查询collaborator的can_edit权限
        raise ForbiddenException("您没有权限编辑此论文")

    updated_paper = await paper_repo.update(
        paper_id=paper_id,
        update_data=paper_data.model_dump(exclude_unset=True),
    )
    await db.commit()

    return success_response(
        data=PaperResponse.model_validate(updated_paper).model_dump(),
        message="更新成功",
    )


@router.delete("/{paper_id}", summary="删除论文")
async def delete_paper(
    paper_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除论文"""
    paper_repo = PaperRepository(db)

    paper = await paper_repo.get_by_id(paper_id)
    if not paper:
        raise NotFoundException("论文")

    # 只有所有者可以删除
    if paper.owner_id != uuid.UUID(user_id):
        raise ForbiddenException("只有论文所有者可以删除")

    await paper_repo.delete(paper_id)
    await db.commit()

    return success_response(message="删除成功")


# ============== 章节路由 ==============

@router.get("/{paper_id}/sections", summary="获取论文章节")
async def get_sections(
    paper_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文章节列表"""
    section_repo = SectionRepository(db)
    sections = await section_repo.get_paper_sections(paper_id)

    return success_response(
        data=[SectionResponse.model_validate(s).model_dump() for s in sections]
    )


@router.post("/{paper_id}/sections", summary="创建章节")
async def create_section(
    paper_id: uuid.UUID,
    section_data: SectionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新章节"""
    section_repo = SectionRepository(db)
    section = await section_repo.create(
        paper_id=paper_id,
        section_data=section_data.model_dump(),
    )
    await db.commit()

    return success_response(
        data=SectionResponse.model_validate(section).model_dump(),
        message="章节创建成功",
        code=201,
    )


@router.put("/sections/{section_id}", summary="更新章节")
async def update_section(
    section_id: uuid.UUID,
    section_data: SectionUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新章节内容"""
    section_repo = SectionRepository(db)
    section = await section_repo.update(
        section_id=section_id,
        update_data=section_data.model_dump(exclude_unset=True),
    )

    if not section:
        raise NotFoundException("章节")

    await db.commit()

    return success_response(
        data=SectionResponse.model_validate(section).model_dump(),
        message="更新成功",
    )


@router.delete("/sections/{section_id}", summary="删除章节")
async def delete_section(
    section_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除章节"""
    section_repo = SectionRepository(db)
    success = await section_repo.delete(section_id)

    if not success:
        raise NotFoundException("章节")

    await db.commit()
    return success_response(message="删除成功")


# ============== 协作者路由 ==============

@router.get("/{paper_id}/collaborators", summary="获取协作者列表")
async def get_collaborators(
    paper_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文协作者"""
    collab_repo = CollaboratorRepository(db)
    collaborators = await collab_repo.get_paper_collaborators(paper_id)

    return success_response(
        data=[CollaboratorResponse.model_validate(c).model_dump() for c in collaborators]
    )


@router.post("/{paper_id}/collaborators", summary="添加协作者")
async def add_collaborator(
    paper_id: uuid.UUID,
    collab_data: CollaboratorAdd,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """添加协作者"""
    # 这里需要从user服务获取用户ID（通过邮箱）
    # 简化处理，假设user_id直接提供
    # 实际应该调用user服务或使用消息队列

    collab_repo = CollaboratorRepository(db)

    # 模拟：生成一个临时UUID
    # 实际应该: user = await user_service.get_by_email(collab_data.user_email)
    temp_user_id = uuid.uuid4()  # TODO: 替换为实际用户ID

    collaborator = await collab_repo.add(
        paper_id=paper_id,
        user_id=temp_user_id,
        role=collab_data.role,
        permissions={
            "can_edit": collab_data.can_edit,
            "can_comment": collab_data.can_comment,
            "can_share": collab_data.can_share,
        },
        invited_by=uuid.UUID(user_id),
    )
    await db.commit()

    return success_response(
        data=CollaboratorResponse.model_validate(collaborator).model_dump(),
        message="协作者添加成功",
        code=201,
    )


@router.delete("/{paper_id}/collaborators/{collab_user_id}", summary="移除协作者")
async def remove_collaborator(
    paper_id: uuid.UUID,
    collab_user_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """移除协作者"""
    collab_repo = CollaboratorRepository(db)
    success = await collab_repo.remove(paper_id, collab_user_id)

    if not success:
        raise NotFoundException("协作者")

    await db.commit()
    return success_response(message="移除成功")


# ============== 版本路由 ==============

@router.get("/{paper_id}/versions", summary="获取版本历史")
async def get_versions(
    paper_id: uuid.UUID,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文版本历史"""
    version_repo = VersionRepository(db)
    versions = await version_repo.get_paper_versions(paper_id, limit)

    return success_response(
        data=[VersionResponse.model_validate(v).model_dump() for v in versions]
    )


@router.post("/{paper_id}/versions", summary="创建版本")
async def create_version(
    paper_id: uuid.UUID,
    version_data: VersionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新版本（快照）"""
    version_repo = VersionRepository(db)
    paper_repo = PaperRepository(db)

    # 获取当前最新版本号
    latest_version = await version_repo.get_latest_version_number(paper_id)
    new_version_number = latest_version + 1

    # 获取论文当前内容
    paper = await paper_repo.get_by_id(paper_id, with_sections=True)
    if not paper:
        raise NotFoundException("论文")

    # 创建内容快照
    content_snapshot = {
        "title": paper.title,
        "abstract": paper.abstract,
        "sections": [
            {
                "id": str(s.id),
                "title": s.title,
                "content": s.content,
            }
            for s in paper.sections
        ],
    }

    version = await version_repo.create(
        paper_id=paper_id,
        version_number=new_version_number,
        content_snapshot=content_snapshot,
        change_summary=version_data.change_summary,
        created_by=uuid.UUID(user_id),
    )
    await db.commit()

    return success_response(
        data=VersionResponse.model_validate(version).model_dump(),
        message="版本创建成功",
        code=201,
    )


# ============== 模板路由 ==============

template_router = APIRouter(prefix="/api/v1/templates", tags=["论文模板"])


@template_router.get("", summary="获取模板列表")
async def get_templates(
    db: AsyncSession = Depends(get_db),
):
    """获取公开的论文模板"""
    template_repo = TemplateRepository(db)
    templates = await template_repo.get_public_templates()

    return success_response(
        data=[TemplateResponse.model_validate(t).model_dump() for t in templates]
    )


@template_router.get("/{template_id}", summary="获取模板详情")
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取模板详情"""
    template_repo = TemplateRepository(db)
    template = await template_repo.get_by_id(template_id)

    if not template:
        raise NotFoundException("模板")

    return success_response(data=TemplateResponse.model_validate(template).model_dump())


# ============== 导出路由 ==============

@router.post("/{paper_id}/export", summary="导出论文")
async def export_paper(
    paper_id: uuid.UUID,
    export_data: ExportRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """导出论文为指定格式"""
    from datetime import datetime, timedelta

    paper_repo = PaperRepository(db)
    paper = await paper_repo.get_by_id(paper_id, with_sections=True)

    if not paper:
        raise NotFoundException("论文")

    # TODO: 实际的导出逻辑
    # 1. 根据format生成对应格式的文件
    # 2. 上传到存储服务
    # 3. 返回下载链接

    # 模拟响应
    return success_response(
        data={
            "download_url": f"https://storage.scholarforge.cn/exports/{paper_id}.{export_data.format}",
            "format": export_data.format,
            "file_size": 1024000,
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        },
        message="导出成功",
    )


# ============== 评论路由 ==============

from .models import Comment, CommentReply
from datetime import datetime

comment_router = APIRouter(prefix="/api/v1/papers", tags=["评论管理"])


@comment_router.get("/{paper_id}/comments", summary="获取评论列表")
async def get_comments(
    paper_id: uuid.UUID,
    section_id: Optional[uuid.UUID] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文或章节的评论列表"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    query = select(Comment).where(Comment.paper_id == paper_id).options(selectinload(Comment.replies))

    if section_id:
        query = query.where(Comment.section_id == section_id)

    query = query.order_by(Comment.created_at.desc())

    result = await db.execute(query)
    comments = result.scalars().all()

    # 获取用户信息
    from services.user.models import User
    user_ids = list(set([c.user_id for c in comments] + [r.user_id for c in comments for r in c.replies]))
    user_query = select(User).where(User.id.in_(user_ids))
    user_result = await db.execute(user_query)
    users = {str(u.id): u for u in user_result.scalars().all()}

    # 构建响应
    response_data = []
    for comment in comments:
        comment_dict = {
            "id": comment.id,
            "paper_id": comment.paper_id,
            "section_id": comment.section_id,
            "user_id": comment.user_id,
            "user_name": users.get(str(comment.user_id), {}).get("full_name", "未知用户"),
            "user_avatar": users.get(str(comment.user_id), {}).get("avatar"),
            "content": comment.content,
            "position": comment.position,
            "resolved": comment.resolved,
            "resolved_by": comment.resolved_by,
            "resolved_at": comment.resolved_at,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "replies": [
                {
                    "id": reply.id,
                    "comment_id": reply.comment_id,
                    "user_id": reply.user_id,
                    "user_name": users.get(str(reply.user_id), {}).get("full_name", "未知用户"),
                    "user_avatar": users.get(str(reply.user_id), {}).get("avatar"),
                    "content": reply.content,
                    "created_at": reply.created_at,
                }
                for reply in comment.replies
            ],
        }
        response_data.append(comment_dict)

    return success_response(data=response_data)


@comment_router.post("/{paper_id}/comments", summary="创建评论")
async def create_comment(
    paper_id: uuid.UUID,
    comment_data: CommentCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新评论"""
    comment = Comment(
        paper_id=paper_id,
        section_id=comment_data.section_id,
        user_id=uuid.UUID(user_id),
        content=comment_data.content,
        position=comment_data.position.model_dump(),
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return success_response(
        data=CommentResponse.model_validate(comment).model_dump(),
        message="评论创建成功",
        code=201,
    )


@comment_router.put("/{paper_id}/comments/{comment_id}", summary="更新评论")
async def update_comment(
    paper_id: uuid.UUID,
    comment_id: uuid.UUID,
    comment_data: CommentUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新评论"""
    from sqlalchemy import select

    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise NotFoundException("评论")

    # 只有评论作者可以修改
    if str(comment.user_id) != user_id:
        raise ForbiddenException("只有评论作者可以修改")

    if comment_data.content is not None:
        comment.content = comment_data.content
    if comment_data.resolved is not None:
        comment.resolved = comment_data.resolved
        if comment_data.resolved:
            comment.resolved_by = uuid.UUID(user_id)
            comment.resolved_at = datetime.utcnow()

    comment.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(comment)

    return success_response(
        data=CommentResponse.model_validate(comment).model_dump(),
        message="更新成功",
    )


@comment_router.delete("/{paper_id}/comments/{comment_id}", summary="删除评论")
async def delete_comment(
    paper_id: uuid.UUID,
    comment_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除评论"""
    from sqlalchemy import select

    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise NotFoundException("评论")

    # 只有评论作者或论文所有者可以删除
    paper_repo = PaperRepository(db)
    paper = await paper_repo.get_by_id(paper_id)

    if str(comment.user_id) != user_id and str(paper.owner_id) != user_id:
        raise ForbiddenException("没有权限删除此评论")

    await db.delete(comment)
    await db.commit()

    return success_response(message="删除成功")


@comment_router.post("/{paper_id}/comments/{comment_id}/replies", summary="创建回复")
async def create_comment_reply(
    paper_id: uuid.UUID,
    comment_id: uuid.UUID,
    reply_data: CommentReplyCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建评论回复"""
    from sqlalchemy import select

    # 检查评论是否存在
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise NotFoundException("评论")

    reply = CommentReply(
        comment_id=comment_id,
        user_id=uuid.UUID(user_id),
        content=reply_data.content,
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)

    return success_response(
        data=CommentReplyResponse.model_validate(reply).model_dump(),
        message="回复创建成功",
        code=201,
    )


@comment_router.delete("/{paper_id}/comments/{comment_id}/replies/{reply_id}", summary="删除回复")
async def delete_comment_reply(
    paper_id: uuid.UUID,
    comment_id: uuid.UUID,
    reply_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除评论回复"""
    from sqlalchemy import select

    result = await db.execute(select(CommentReply).where(CommentReply.id == reply_id))
    reply = result.scalar_one_or_none()

    if not reply:
        raise NotFoundException("回复")

    if str(reply.user_id) != user_id:
        raise ForbiddenException("只有回复作者可以删除")

    await db.delete(reply)
    await db.commit()

    return success_response(message="删除成功")


# ============== 批注路由 ==============

from .models import Annotation

annotation_router = APIRouter(prefix="/api/v1/papers", tags=["批注管理"])


@annotation_router.get("/{paper_id}/annotations", summary="获取批注列表")
async def get_annotations(
    paper_id: uuid.UUID,
    section_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文批注列表"""
    from sqlalchemy import select
    from services.user.models import User

    query = select(Annotation).where(Annotation.paper_id == paper_id)

    if section_id:
        query = query.where(Annotation.section_id == section_id)
    if status:
        query = query.where(Annotation.status == status)

    query = query.order_by(Annotation.created_at.desc())

    result = await db.execute(query)
    annotations = result.scalars().all()

    # 获取用户信息
    user_ids = list(set([a.user_id for a in annotations]))
    user_query = select(User).where(User.id.in_(user_ids))
    user_result = await db.execute(user_query)
    users = {str(u.id): u for u in user_result.scalars().all()}

    response_data = []
    for annotation in annotations:
        annotation_dict = {
            "id": annotation.id,
            "paper_id": annotation.paper_id,
            "section_id": annotation.section_id,
            "user_id": annotation.user_id,
            "user_name": users.get(str(annotation.user_id), {}).get("full_name", "未知用户"),
            "user_avatar": users.get(str(annotation.user_id), {}).get("avatar"),
            "annotation_type": annotation.annotation_type,
            "content": annotation.content,
            "position": annotation.position,
            "style": annotation.style,
            "status": annotation.status,
            "priority": annotation.priority,
            "created_at": annotation.created_at,
            "updated_at": annotation.updated_at,
        }
        response_data.append(annotation_dict)

    return success_response(data=response_data)


@annotation_router.post("/{paper_id}/annotations", summary="创建批注")
async def create_annotation(
    paper_id: uuid.UUID,
    annotation_data: AnnotationCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新批注"""
    annotation = Annotation(
        paper_id=paper_id,
        section_id=annotation_data.section_id,
        user_id=uuid.UUID(user_id),
        annotation_type=annotation_data.annotation_type,
        content=annotation_data.content,
        position=annotation_data.position.model_dump(),
        style=annotation_data.style.model_dump() if annotation_data.style else {},
        priority=annotation_data.priority,
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)

    return success_response(
        data=AnnotationResponse.model_validate(annotation).model_dump(),
        message="批注创建成功",
        code=201,
    )


@annotation_router.put("/{paper_id}/annotations/{annotation_id}", summary="更新批注")
async def update_annotation(
    paper_id: uuid.UUID,
    annotation_id: uuid.UUID,
    annotation_data: AnnotationUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新批注"""
    from sqlalchemy import select

    result = await db.execute(select(Annotation).where(Annotation.id == annotation_id))
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise NotFoundException("批注")

    # 只有批注作者可以修改
    if str(annotation.user_id) != user_id:
        raise ForbiddenException("只有批注作者可以修改")

    if annotation_data.content is not None:
        annotation.content = annotation_data.content
    if annotation_data.style is not None:
        annotation.style = annotation_data.style.model_dump()
    if annotation_data.status is not None:
        annotation.status = annotation_data.status
    if annotation_data.priority is not None:
        annotation.priority = annotation_data.priority

    annotation.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(annotation)

    return success_response(
        data=AnnotationResponse.model_validate(annotation).model_dump(),
        message="更新成功",
    )


@annotation_router.delete("/{paper_id}/annotations/{annotation_id}", summary="删除批注")
async def delete_annotation(
    paper_id: uuid.UUID,
    annotation_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除批注"""
    from sqlalchemy import select

    result = await db.execute(select(Annotation).where(Annotation.id == annotation_id))
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise NotFoundException("批注")

    # 只有批注作者或论文所有者可以删除
    paper_repo = PaperRepository(db)
    paper = await paper_repo.get_by_id(paper_id)

    if str(annotation.user_id) != user_id and str(paper.owner_id) != user_id:
        raise ForbiddenException("没有权限删除此批注")

    await db.delete(annotation)
    await db.commit()

    return success_response(message="删除成功")
