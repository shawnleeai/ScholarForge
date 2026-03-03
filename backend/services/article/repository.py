"""
文献数据访问层
数据库 CRUD 操作
"""

import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Article, UserLibrary, LibraryFolder


class ArticleRepository:
    """文献数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, article_data: Dict[str, Any]) -> Article:
        """创建文献记录"""
        article = Article(**article_data)
        self.db.add(article)
        await self.db.flush()
        await self.db.refresh(article)
        return article

    async def get_by_id(self, article_id: uuid.UUID) -> Optional[Article]:
        """通过ID获取文献"""
        result = await self.db.execute(
            select(Article).where(Article.id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_by_doi(self, doi: str) -> Optional[Article]:
        """通过DOI获取文献"""
        result = await self.db.execute(
            select(Article).where(Article.doi == doi)
        )
        return result.scalar_one_or_none()

    async def upsert(self, article_data: Dict[str, Any]) -> Article:
        """创建或更新文献（基于DOI）"""
        doi = article_data.get("doi")
        if doi:
            existing = await self.get_by_doi(doi)
            if existing:
                # 更新现有记录
                for key, value in article_data.items():
                    if value is not None:
                        setattr(existing, key, value)
                await self.db.flush()
                await self.db.refresh(existing)
                return existing

        return await self.create(article_data)

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[Article], int]:
        """搜索文献（本地数据库）"""
        filters = filters or {}

        # 构建搜索条件
        search_term = f"%{query}%"
        conditions = [
            or_(
                Article.title.ilike(search_term),
                Article.abstract.ilike(search_term),
            )
        ]

        if filters.get("year_from"):
            conditions.append(Article.publication_year >= filters["year_from"])
        if filters.get("year_to"):
            conditions.append(Article.publication_year <= filters["year_to"])
        if filters.get("source_db"):
            conditions.append(Article.source_db == filters["source_db"])

        # 构建查询
        base_query = select(Article).where(*conditions)

        # 计算总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query) or 0

        # 分页查询
        result = await self.db.execute(
            base_query
            .order_by(Article.citation_count.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        articles = list(result.scalars().all())

        return articles, total


class UserLibraryRepository:
    """用户文献库仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(
        self,
        user_id: uuid.UUID,
        article_id: uuid.UUID,
        folder_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> UserLibrary:
        """添加到文献库"""
        item = UserLibrary(
            user_id=user_id,
            article_id=article_id,
            folder_id=folder_id,
            tags=tags or [],
            notes=notes,
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def get_by_user_and_article(
        self, user_id: uuid.UUID, article_id: uuid.UUID
    ) -> Optional[UserLibrary]:
        """获取用户的文献库项"""
        result = await self.db.execute(
            select(UserLibrary)
            .options(selectinload(UserLibrary.article))
            .where(
                UserLibrary.user_id == user_id,
                UserLibrary.article_id == article_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_library(
        self,
        user_id: uuid.UUID,
        folder_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[UserLibrary], int]:
        """获取用户文献库"""
        conditions = [UserLibrary.user_id == user_id]

        if folder_id:
            conditions.append(UserLibrary.folder_id == folder_id)

        base_query = (
            select(UserLibrary)
            .options(selectinload(UserLibrary.article))
            .where(*conditions)
        )

        # 计算总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query) or 0

        # 分页查询
        result = await self.db.execute(
            base_query
            .order_by(UserLibrary.added_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(result.scalars().all())

        return items, total

    async def update(
        self,
        user_id: uuid.UUID,
        article_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[UserLibrary]:
        """更新文献库项"""
        item = await self.get_by_user_and_article(user_id, article_id)
        if not item:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(item, key, value)

        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def remove(self, user_id: uuid.UUID, article_id: uuid.UUID) -> bool:
        """从文献库移除"""
        item = await self.get_by_user_and_article(user_id, article_id)
        if not item:
            return False

        await self.db.delete(item)
        await self.db.flush()
        return True

    async def exists(self, user_id: uuid.UUID, article_id: uuid.UUID) -> bool:
        """检查是否已在文献库中"""
        result = await self.db.execute(
            select(func.count()).where(
                UserLibrary.user_id == user_id,
                UserLibrary.article_id == article_id,
            )
        )
        return (result.scalar() or 0) > 0


class FolderRepository:
    """文件夹仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[uuid.UUID] = None,
        color: Optional[str] = None,
    ) -> LibraryFolder:
        """创建文件夹"""
        folder = LibraryFolder(
            user_id=user_id,
            name=name,
            description=description,
            parent_id=parent_id,
            color=color,
        )
        self.db.add(folder)
        await self.db.flush()
        await self.db.refresh(folder)
        return folder

    async def get_by_id(self, folder_id: uuid.UUID) -> Optional[LibraryFolder]:
        """获取文件夹"""
        result = await self.db.execute(
            select(LibraryFolder).where(LibraryFolder.id == folder_id)
        )
        return result.scalar_one_or_none()

    async def get_user_folders(self, user_id: uuid.UUID) -> List[LibraryFolder]:
        """获取用户所有文件夹"""
        result = await self.db.execute(
            select(LibraryFolder)
            .where(LibraryFolder.user_id == user_id)
            .order_by(LibraryFolder.created_at)
        )
        return list(result.scalars().all())

    async def update(
        self, folder_id: uuid.UUID, update_data: Dict[str, Any]
    ) -> Optional[LibraryFolder]:
        """更新文件夹"""
        folder = await self.get_by_id(folder_id)
        if not folder:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(folder, key, value)

        await self.db.flush()
        await self.db.refresh(folder)
        return folder

    async def delete(self, folder_id: uuid.UUID) -> bool:
        """删除文件夹"""
        folder = await self.get_by_id(folder_id)
        if not folder:
            return False

        await self.db.delete(folder)
        await self.db.flush()
        return True
