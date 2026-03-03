"""
文献服务 API 路由
FastAPI 路由定义
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.exceptions import NotFoundException, ConflictException
from shared.responses import success_response, paginated_response
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams
from shared.config import settings

from .schemas import (
    ArticleResponse,
    ArticleBrief,
    SearchRequest,
    LibraryItemCreate,
    LibraryItemUpdate,
    LibraryItemResponse,
    FolderCreate,
    FolderUpdate,
    FolderResponse,
)
from .repository import ArticleRepository, UserLibraryRepository, FolderRepository
from .adapters import CNKIAdapter, WoSAdapter, IEEEAdapter, ArxivAdapter

router = APIRouter(prefix="/api/v1", tags=["文献检索"])

# 数据源适配器映射
ADAPTERS = {
    "cnki": CNKIAdapter(
        api_key=settings.cnki_api_key,
        api_secret=settings.cnki_api_secret,
    ),
    "wos": WoSAdapter(api_key=settings.wos_api_key),
    "ieee": IEEEAdapter(api_key=settings.ieee_api_key),
    "arxiv": ArxivAdapter(),
}


# ============== 搜索路由 ==============

@router.get("/articles/search", summary="多源文献搜索")
async def search_articles(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    sources: Optional[str] = Query(None, description="数据源，逗号分隔"),
    year_from: Optional[int] = Query(None, description="起始年份"),
    year_to: Optional[int] = Query(None, description="结束年份"),
    source_type: Optional[str] = Query(None, description="文献类型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
):
    """
    多源文献搜索

    支持的数据源：cnki, wos, ieee, arxiv
    """
    # 解析数据源
    source_list = sources.split(",") if sources else ["cnki", "wos", "ieee"]
    source_list = [s.strip() for s in source_list if s.strip() in ADAPTERS]

    if not source_list:
        source_list = ["cnki", "wos", "ieee"]

    filters = {
        "year_from": year_from,
        "year_to": year_to,
        "source_type": source_type,
    }

    all_articles = []
    total_count = 0

    # 并行搜索多个数据源
    for source in source_list:
        adapter = ADAPTERS.get(source)
        if not adapter:
            continue

        try:
            result = await adapter.search(
                query=q,
                page=page,
                page_size=page_size // len(source_list) + 5,  # 分配每源数量
                filters=filters,
            )
            all_articles.extend(result.articles)
            total_count += result.total
        except Exception:
            continue

    # 按引用数排序
    all_articles.sort(
        key=lambda x: x.get("citation_count", 0),
        reverse=True,
    )

    # 分页
    start = (page - 1) * page_size
    paginated_articles = all_articles[start:start + page_size]

    return paginated_response(
        items=paginated_articles,
        total=min(total_count, len(all_articles)),  # 实际返回的数量
        page=page,
        page_size=page_size,
    )


@router.get("/articles/{article_id}", summary="获取文献详情")
async def get_article(
    article_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取文献详情"""
    article_repo = ArticleRepository(db)
    article = await article_repo.get_by_id(article_id)

    if not article:
        raise NotFoundException("文献")

    return success_response(data=ArticleResponse.model_validate(article).model_dump())


@router.get("/articles/doi/{doi}", summary="通过DOI获取文献")
async def get_article_by_doi(
    doi: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """通过DOI获取文献"""
    article_repo = ArticleRepository(db)
    article = await article_repo.get_by_doi(doi)

    if not article:
        # 尝试从外部数据源获取
        for adapter in ADAPTERS.values():
            try:
                raw_article = await adapter.get_by_doi(doi)
                if raw_article:
                    article = await article_repo.upsert(raw_article)
                    break
            except Exception:
                continue

    if not article:
        raise NotFoundException("文献")

    return success_response(data=ArticleResponse.model_validate(article).model_dump())


# ============== 文献库路由 ==============

library_router = APIRouter(prefix="/api/v1/library", tags=["我的文献库"])


@library_router.get("", summary="获取我的文献库")
async def get_my_library(
    folder_id: Optional[uuid.UUID] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户文献库"""
    library_repo = UserLibraryRepository(db)
    items, total = await library_repo.get_user_library(
        user_id=uuid.UUID(user_id),
        folder_id=folder_id,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    return paginated_response(
        items=[LibraryItemResponse.model_validate(item).model_dump() for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@library_router.post("", summary="添加到文献库")
async def add_to_library(
    item_data: LibraryItemCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """添加文献到个人文献库"""
    library_repo = UserLibraryRepository(db)

    # 检查是否已存在
    if await library_repo.exists(uuid.UUID(user_id), item_data.article_id):
        raise ConflictException("该文献已在您的文献库中")

    item = await library_repo.add(
        user_id=uuid.UUID(user_id),
        article_id=item_data.article_id,
        folder_id=item_data.folder_id,
        tags=item_data.tags,
        notes=item_data.notes,
    )
    await db.commit()

    return success_response(
        data=LibraryItemResponse.model_validate(item).model_dump(),
        message="添加成功",
        code=201,
    )


@library_router.put("/{article_id}", summary="更新文献库项")
async def update_library_item(
    article_id: uuid.UUID,
    item_data: LibraryItemUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新文献库项"""
    library_repo = UserLibraryRepository(db)
    item = await library_repo.update(
        user_id=uuid.UUID(user_id),
        article_id=article_id,
        update_data=item_data.model_dump(exclude_unset=True),
    )

    if not item:
        raise NotFoundException("文献库项")

    await db.commit()
    return success_response(
        data=LibraryItemResponse.model_validate(item).model_dump(),
        message="更新成功",
    )


@library_router.delete("/{article_id}", summary="从文献库移除")
async def remove_from_library(
    article_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """从文献库移除文献"""
    library_repo = UserLibraryRepository(db)
    success = await library_repo.remove(uuid.UUID(user_id), article_id)

    if not success:
        raise NotFoundException("文献库项")

    await db.commit()
    return success_response(message="移除成功")


# ============== 文件夹路由 ==============

folder_router = APIRouter(prefix="/api/v1/library/folders", tags=["文献文件夹"])


@folder_router.get("", summary="获取文件夹列表")
async def get_folders(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户所有文件夹"""
    folder_repo = FolderRepository(db)
    folders = await folder_repo.get_user_folders(uuid.UUID(user_id))

    return success_response(
        data=[FolderResponse.model_validate(f).model_dump() for f in folders]
    )


@folder_router.post("", summary="创建文件夹")
async def create_folder(
    folder_data: FolderCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建文件夹"""
    folder_repo = FolderRepository(db)
    folder = await folder_repo.create(
        user_id=uuid.UUID(user_id),
        name=folder_data.name,
        description=folder_data.description,
        parent_id=folder_data.parent_id,
        color=folder_data.color,
    )
    await db.commit()

    return success_response(
        data=FolderResponse.model_validate(folder).model_dump(),
        message="创建成功",
        code=201,
    )


@folder_router.put("/{folder_id}", summary="更新文件夹")
async def update_folder(
    folder_id: uuid.UUID,
    folder_data: FolderUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新文件夹"""
    folder_repo = FolderRepository(db)
    folder = await folder_repo.update(
        folder_id=folder_id,
        update_data=folder_data.model_dump(exclude_unset=True),
    )

    if not folder:
        raise NotFoundException("文件夹")

    await db.commit()
    return success_response(
        data=FolderResponse.model_validate(folder).model_dump(),
        message="更新成功",
    )


@folder_router.delete("/{folder_id}", summary="删除文件夹")
async def delete_folder(
    folder_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除文件夹"""
    folder_repo = FolderRepository(db)

    # 检查文件夹是否存在且属于当前用户
    folder = await folder_repo.get_by_id(folder_id)
    if not folder or folder.user_id != uuid.UUID(user_id):
        raise NotFoundException("文件夹")

    success = await folder_repo.delete(folder_id)
    await db.commit()

    return success_response(message="删除成功")
