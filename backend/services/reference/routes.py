"""
参考文献服务 API 路由
FastAPI 路由定义
"""

import os
import uuid
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.exceptions import NotFoundException, ConflictException, ValidationException
from shared.responses import success_response, paginated_response
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams

from .schemas import (
    ReferenceCreate, ReferenceUpdate, ReferenceResponse, ReferenceListResponse,
    ReferenceFilters, ReferenceSearchRequest, TagAddRequest, TagRemoveRequest,
    TagsListResponse, CitationCreate, CitationUpdate, CitationResponse,
    CitationFormatRequest, CitationFormatResponse, FolderCreate, FolderUpdate,
    FolderResponse, FolderListResponse, MoveToFolderRequest, ImportRequest,
    ImportTaskResponse, ExportRequest, ExportResponse, ReferenceStatistics,
    MetadataExtractRequest, MetadataExtractResponse
)
from .repository import (
    ReferenceRepository, CitationRepository, ReferenceFolderRepository, ImportTaskRepository
)
from .parsers import (
    parse_bibtex, parse_ris, parse_endnote, parse_noteexpress,
    export_bibtex, export_ris, export_csv, export_json
)
from .citation_formatter import CitationFormatter

router = APIRouter(prefix="/api/v1/references", tags=["参考文献管理"])


# ============== 参考文献 CRUD ==============

@router.get("", summary="获取参考文献列表")
async def get_references(
    paper_id: Optional[str] = Query(None),
    folder_id: Optional[str] = Query(None),
    publication_type: Optional[str] = Query(None),
    is_important: Optional[bool] = Query(None),
    is_read: Optional[bool] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    tags: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    order_by: str = Query("added_at DESC"),
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的参考文献列表"""
    ref_repo = ReferenceRepository(db)

    filters = ReferenceFilters(
        paper_id=paper_id,
        folder_id=folder_id,
        publication_type=publication_type,
        is_important=is_important,
        is_read=is_read,
        year_from=year_from,
        year_to=year_to,
        tags=tags.split(",") if tags else None,
        search=search,
        order_by=order_by
    )

    references, total = await ref_repo.get_user_references(
        user_id=user_id,
        filters=filters.model_dump(exclude_none=True),
        page=pagination.page,
        page_size=pagination.page_size
    )

    return paginated_response(
        items=[ReferenceResponse(**ref).model_dump() for ref in references],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post("", summary="添加参考文献")
async def create_reference(
    ref_data: ReferenceCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """添加新的参考文献"""
    ref_repo = ReferenceRepository(db)

    # 检查DOI是否已存在
    if ref_data.doi:
        existing = await ref_repo.get_by_doi(user_id, ref_data.doi)
        if existing:
            raise ConflictException("该DOI的文献已存在")

    # 创建参考文献
    ref_dict = ref_data.model_dump()
    ref_dict['user_id'] = user_id

    reference = await ref_repo.create(ref_dict)
    await db.commit()

    return success_response(
        data=ReferenceResponse(**reference).model_dump(),
        message="添加成功",
        code=201
    )


@router.get("/{reference_id}", summary="获取参考文献详情")
async def get_reference(
    reference_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取参考文献详情"""
    ref_repo = ReferenceRepository(db)
    reference = await ref_repo.get_by_id(reference_id)

    if not reference or reference['user_id'] != user_id:
        raise NotFoundException("参考文献")

    return success_response(data=ReferenceResponse(**reference).model_dump())


@router.put("/{reference_id}", summary="更新参考文献")
async def update_reference(
    reference_id: str,
    ref_data: ReferenceUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新参考文献信息"""
    ref_repo = ReferenceRepository(db)

    reference = await ref_repo.update(
        reference_id=reference_id,
        user_id=user_id,
        update_data=ref_data.model_dump(exclude_unset=True)
    )

    if not reference:
        raise NotFoundException("参考文献")

    await db.commit()
    return success_response(
        data=ReferenceResponse(**reference).model_dump(),
        message="更新成功"
    )


@router.delete("/{reference_id}", summary="删除参考文献")
async def delete_reference(
    reference_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除参考文献"""
    ref_repo = ReferenceRepository(db)
    success = await ref_repo.delete(reference_id, user_id)

    if not success:
        raise NotFoundException("参考文献")

    await db.commit()
    return success_response(message="删除成功")


# ============== 标签管理 ==============

@router.get("/tags/list", summary="获取所有标签")
async def get_all_tags(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的所有标签"""
    ref_repo = ReferenceRepository(db)
    tags = await ref_repo.get_user_tags(user_id)
    return success_response(data=TagsListResponse(tags=tags).model_dump())


@router.post("/{reference_id}/tags", summary="添加标签")
async def add_tags(
    reference_id: str,
    tag_data: TagAddRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """为参考文献添加标签"""
    ref_repo = ReferenceRepository(db)

    # 检查文献是否存在
    ref = await ref_repo.get_by_id(reference_id)
    if not ref or ref['user_id'] != user_id:
        raise NotFoundException("参考文献")

    success = await ref_repo.add_tags(reference_id, user_id, tag_data.tags)
    if not success:
        raise ValidationException("添加标签失败")

    await db.commit()
    return success_response(message="标签添加成功")


@router.delete("/{reference_id}/tags", summary="移除标签")
async def remove_tags(
    reference_id: str,
    tag_data: TagRemoveRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """从参考文献移除标签"""
    ref_repo = ReferenceRepository(db)
    success = await ref_repo.remove_tags(reference_id, user_id, tag_data.tags)

    if not success:
        raise NotFoundException("参考文献")

    await db.commit()
    return success_response(message="标签移除成功")


# ============== 阅读状态 ==============

@router.patch("/{reference_id}/read", summary="标记为已读/未读")
async def mark_read_status(
    reference_id: str,
    is_read: bool = Query(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """标记参考文献的阅读状态"""
    ref_repo = ReferenceRepository(db)
    success = await ref_repo.update_read_status(reference_id, user_id, is_read)

    if not success:
        raise NotFoundException("参考文献")

    await db.commit()
    return success_response(message="状态更新成功")


# ============== 文件夹管理 ==============

folder_router = APIRouter(prefix="/api/v1/reference-folders", tags=["文献文件夹"])


@folder_router.get("", summary="获取文件夹列表")
async def get_folders(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的文献文件夹列表"""
    folder_repo = ReferenceFolderRepository(db)
    folders = await folder_repo.get_user_folders(user_id)

    return success_response(
        data=FolderListResponse(
            items=[FolderResponse(**f).model_dump() for f in folders]
        ).model_dump()
    )


@folder_router.post("", summary="创建文件夹")
async def create_folder(
    folder_data: FolderCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建文献文件夹"""
    folder_repo = ReferenceFolderRepository(db)

    folder_dict = folder_data.model_dump()
    folder_dict['user_id'] = user_id

    folder = await folder_repo.create(folder_dict)
    await db.commit()

    return success_response(
        data=FolderResponse(**folder).model_dump(),
        message="创建成功",
        code=201
    )


@folder_router.put("/{folder_id}", summary="更新文件夹")
async def update_folder(
    folder_id: str,
    folder_data: FolderUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新文献文件夹"""
    folder_repo = ReferenceFolderRepository(db)

    folder = await folder_repo.update(
        folder_id=folder_id,
        user_id=user_id,
        update_data=folder_data.model_dump(exclude_unset=True)
    )

    if not folder:
        raise NotFoundException("文件夹")

    await db.commit()
    return success_response(
        data=FolderResponse(**folder).model_dump(),
        message="更新成功"
    )


@folder_router.delete("/{folder_id}", summary="删除文件夹")
async def delete_folder(
    folder_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除文献文件夹"""
    folder_repo = ReferenceFolderRepository(db)

    # 检查文件夹是否存在
    folder = await folder_repo.get_by_id(folder_id)
    if not folder or folder['user_id'] != user_id:
        raise NotFoundException("文件夹")

    success = await folder_repo.delete(folder_id, user_id)
    if not success:
        raise NotFoundException("文件夹")

    await db.commit()
    return success_response(message="删除成功")


@router.post("/move-to-folder", summary="批量移动到文件夹")
async def move_to_folder(
    move_data: MoveToFolderRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """批量移动文献到文件夹"""
    ref_repo = ReferenceRepository(db)

    # 更新每个参考文献的文件夹
    for ref_id in move_data.reference_ids:
        await ref_repo.update(
            reference_id=ref_id,
            user_id=user_id,
            update_data={"folder_id": move_data.folder_id}
        )

    await db.commit()
    return success_response(message=f"成功移动 {len(move_data.reference_ids)} 篇文献")


# ============== 引用管理 ==============

citation_router = APIRouter(prefix="/api/v1/papers/{paper_id}/citations", tags=["论文引用管理"])


@citation_router.get("", summary="获取论文引用列表")
async def get_paper_citations(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文的所有引用"""
    citation_repo = CitationRepository(db)
    citations = await citation_repo.get_paper_citations(paper_id)

    return success_response(
        data=[CitationResponse(**c).model_dump() for c in citations]
    )


@citation_router.post("", summary="添加引用")
async def add_citation(
    paper_id: str,
    citation_data: CitationCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """为论文添加引用"""
    citation_repo = CitationRepository(db)
    ref_repo = ReferenceRepository(db)

    # 获取参考文献信息
    ref = await ref_repo.get_by_id(citation_data.citing_ref_id)
    if not ref:
        raise NotFoundException("参考文献")

    # 获取下一个引用序号
    next_number = await citation_repo.get_next_citation_number(paper_id)

    # 格式化引用
    formatter = CitationFormatter()
    formatted = formatter.format(ref, citation_data.citation_style)

    # 创建引用关系
    citation_dict = {
        'paper_id': paper_id,
        'citing_ref_id': citation_data.citing_ref_id,
        'citing_position': citation_data.citing_position,
        'citation_text': citation_data.citation_text,
        'citation_style': citation_data.citation_style,
        'formatted_citation': formatted,
        'citation_number': next_number
    }

    citation = await citation_repo.create(citation_dict)

    # 更新参考文献的被引用次数
    await ref_repo.update(
        reference_id=citation_data.citing_ref_id,
        user_id=user_id,
        update_data={"cited_times": ref.get('cited_times', 0) + 1}
    )

    await db.commit()

    return success_response(
        data=CitationResponse(**citation).model_dump(),
        message="引用添加成功",
        code=201
    )


@citation_router.delete("/{citation_id}", summary="删除引用")
async def delete_citation(
    paper_id: str,
    citation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除论文的引用"""
    citation_repo = CitationRepository(db)
    success = await citation_repo.delete(citation_id)

    if not success:
        raise NotFoundException("引用")

    await db.commit()
    return success_response(message="引用删除成功")


@router.post("/format-citations", summary="格式化引用")
async def format_citations(
    format_data: CitationFormatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """批量格式化引用"""
    ref_repo = ReferenceRepository(db)
    formatter = CitationFormatter()

    citations = []
    for ref_id in format_data.reference_ids:
        ref = await ref_repo.get_by_id(ref_id)
        if ref and ref['user_id'] == user_id:
            formatted = formatter.format(ref, format_data.style)
            citations.append({
                "id": ref_id,
                "formatted": formatted,
                "in_text": formatter.format_in_text(ref, format_data.style)
            })

    return success_response(
        data=CitationFormatResponse(
            style=format_data.style,
            citations=citations
        ).model_dump()
    )


# ============== 导入/导出 ==============

class ImportPreviewRequest(BaseModel):
    """导入预览请求"""
    source_type: str
    paper_id: Optional[str] = None
    folder_id: Optional[str] = None


class ImportPreviewResponse(BaseModel):
    """导入预览响应"""
    total: int
    valid: int
    duplicates: int
    invalid: int
    sample: List[Dict[str, Any]]
    duplicates_detail: List[Dict[str, Any]]


@router.post("/import/preview", summary="预览导入")
async def preview_import(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    user_id: str = Depends(get_current_user_id),
):
    """预览导入文件内容，不实际导入"""
    from .import_adapters import ImportAdapterFactory

    try:
        content = await file.read()

        # 获取适配器
        adapter = ImportAdapterFactory.get_adapter(source_type, user_id)

        # 解析文件
        result = await adapter.import_from_file(content)

        return success_response(
            data=ImportPreviewResponse(
                total=result.total_count,
                valid=result.success_count,
                duplicates=len(result.duplicates),
                invalid=result.failed_count,
                sample=result.references[:5],
                duplicates_detail=result.duplicates[:5]
            ).model_dump()
        )

    except Exception as e:
        raise ValidationException(f"预览失败: {str(e)}")


@router.post("/import", summary="导入文献")
async def import_references(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    paper_id: Optional[str] = Form(None),
    folder_id: Optional[str] = Form(None),
    skip_duplicates: bool = Form(True),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """从文件导入文献"""
    import_task_repo = ImportTaskRepository(db)
    ref_repo = ReferenceRepository(db)

    # 保存上传的文件
    upload_dir = "uploads/imports"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 创建导入任务
    task = await import_task_repo.create({
        'user_id': user_id,
        'paper_id': paper_id,
        'source_type': source_type,
        'file_name': file.filename,
        'file_path': file_path,
        'status': 'processing'
    })

    # 使用新的导入适配器
    from .import_adapters import ImportAdapterFactory

    try:
        # 读取文件内容
        with open(file_path, 'rb') as f:
            content = f.read()

        # 获取适配器并导入
        adapter = ImportAdapterFactory.get_adapter(source_type, user_id)
        result = await adapter.import_from_file(content)

        # 导入文献到数据库
        success_count = 0
        failed_items = []

        for ref in result.references:
            try:
                ref['user_id'] = user_id
                ref['paper_id'] = paper_id
                ref['folder_id'] = folder_id
                ref['source_db'] = source_type

                # 检查DOI是否已存在
                if ref.get('doi'):
                    existing = await ref_repo.get_by_doi(user_id, ref['doi'])
                    if existing:
                        if not skip_duplicates:
                            failed_items.append({
                                'title': ref.get('title', 'Unknown'),
                                'error': 'DOI 已存在'
                            })
                        continue

                await ref_repo.create(ref)
                success_count += 1
            except Exception as e:
                failed_items.append({
                    'title': ref.get('title', 'Unknown'),
                    'error': str(e)
                })

        # 更新任务状态
        await import_task_repo.update_status(
            task['id'],
            'completed',
            {
                'total_count': result.total_count,
                'success_count': success_count,
                'failed_count': len(failed_items) + len(result.errors),
                'failed_items': failed_items + result.errors,
                'duplicates_count': len(result.duplicates)
            }
        )
        await db.commit()

        return success_response(
            data=ImportTaskResponse(**task).model_dump(),
            message=f"成功导入 {success_count}/{result.total_count} 篇文献"
        )

    except Exception as e:
        await import_task_repo.update_status(
            task['id'],
            'failed',
            {'error_message': str(e)}
        )
        await db.commit()
        raise ValidationException(f"导入失败: {str(e)}")


@router.post("/import/zotero", summary="从 Zotero 导入")
async def import_from_zotero(
    credentials: Dict[str, str],
    collection_key: Optional[str] = None,
    paper_id: Optional[str] = None,
    folder_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """直接从 Zotero API 导入文献"""
    import_task_repo = ImportTaskRepository(db)
    ref_repo = ReferenceRepository(db)

    from .import_adapters import ZoteroAdapter

    # 创建导入任务
    task = await import_task_repo.create({
        'user_id': user_id,
        'paper_id': paper_id,
        'source_type': 'zotero',
        'status': 'processing'
    })

    try:
        # 使用 Zotero 适配器
        adapter = ZoteroAdapter(user_id)
        result = await adapter.import_from_api(credentials, collection_key)

        if not result.success:
            await import_task_repo.update_status(
                task['id'],
                'failed',
                {'error_message': result.errors[0]['error'] if result.errors else '未知错误'}
            )
            await db.commit()
            raise ValidationException("Zotero 导入失败")

        # 导入文献
        success_count = 0
        for ref in result.references:
            try:
                ref['user_id'] = user_id
                ref['paper_id'] = paper_id
                ref['folder_id'] = folder_id

                # 检查DOI是否已存在
                if ref.get('doi'):
                    existing = await ref_repo.get_by_doi(user_id, ref['doi'])
                    if existing:
                        continue

                await ref_repo.create(ref)
                success_count += 1
            except Exception:
                continue

        # 更新任务状态
        await import_task_repo.update_status(
            task['id'],
            'completed',
            {
                'total_count': result.total_count,
                'success_count': success_count,
                'failed_count': result.failed_count,
                'duplicates_count': len(result.duplicates)
            }
        )
        await db.commit()

        return success_response(
            data=ImportTaskResponse(**task).model_dump(),
            message=f"成功从 Zotero 导入 {success_count}/{result.total_count} 篇文献"
        )

    except Exception as e:
        await import_task_repo.update_status(
            task['id'],
            'failed',
            {'error_message': str(e)}
        )
        await db.commit()
        raise ValidationException(f"Zotero 导入失败: {str(e)}")


@router.post("/export", summary="导出文献")
async def export_references(
    export_data: ExportRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """导出文献到文件"""
    ref_repo = ReferenceRepository(db)

    # 获取要导出的文献
    if export_data.reference_ids:
        references = []
        for ref_id in export_data.reference_ids:
            ref = await ref_repo.get_by_id(ref_id)
            if ref and ref['user_id'] == user_id:
                references.append(ref)
    else:
        filters = {}
        if export_data.folder_id:
            filters['folder_id'] = export_data.folder_id
        if export_data.paper_id:
            filters['paper_id'] = export_data.paper_id

        references, _ = await ref_repo.get_user_references(
            user_id=user_id,
            filters=filters,
            page=1,
            page_size=10000
        )

    # 导出为指定格式
    exporter_map = {
        'bibtex': export_bibtex,
        'ris': export_ris,
        'csv': export_csv,
        'json': export_json,
    }

    exporter = exporter_map.get(export_data.format)
    if not exporter:
        raise ValidationException(f"不支持的导出格式: {export_data.format}")

    # 生成导出文件
    export_dir = "uploads/exports"
    os.makedirs(export_dir, exist_ok=True)
    file_name = f"references_{uuid.uuid4().hex[:8]}.{export_data.format}"
    file_path = os.path.join(export_dir, file_name)

    content = exporter(references, export_data.options)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return success_response(
        data=ExportResponse(
            format=export_data.format,
            file_url=f"/uploads/exports/{file_name}",
            file_name=file_name,
            record_count=len(references)
        ).model_dump()
    )


# ============== 统计分析 ==============

@router.get("/statistics/overview", summary="获取统计概览")
async def get_statistics(
    paper_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取参考文献统计信息"""
    ref_repo = ReferenceRepository(db)
    stats = await ref_repo.get_statistics(user_id, paper_id)

    return success_response(data=ReferenceStatistics(**stats).model_dump())


# ============== 元数据提取 ==============

@router.post("/extract-metadata", summary="提取文献元数据")
async def extract_metadata(
    extract_data: MetadataExtractRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """从DOI/PMID/URL或文本提取文献元数据"""
    from .metadata_extractor import MetadataExtractor

    extractor = MetadataExtractor()

    if extract_data.identifier and extract_data.identifier_type == 'doi':
        result = await extractor.extract_from_doi(extract_data.identifier)
    elif extract_data.identifier and extract_data.identifier_type == 'pmid':
        result = await extractor.extract_from_pmid(extract_data.identifier)
    elif extract_data.text:
        result = await extractor.extract_from_text(extract_data.text)
    else:
        raise ValidationException("请提供DOI、PMID或文本")

    return success_response(data=result.model_dump())


# 合并路由
__all__ = ['router', 'folder_router', 'citation_router']
