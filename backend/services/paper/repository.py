"""
论文数据访问层
数据库 CRUD 操作
"""

import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Paper,
    PaperSection,
    PaperCollaborator,
    PaperVersion,
    PaperTemplate,
)


class PaperRepository:
    """论文数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        owner_id: uuid.UUID,
        paper_data: Dict[str, Any],
    ) -> Paper:
        """创建论文"""
        paper = Paper(
            owner_id=owner_id,
            **paper_data,
        )
        self.db.add(paper)
        await self.db.flush()
        await self.db.refresh(paper)

        # 创建默认章节结构
        default_sections = [
            {"title": "摘要", "section_type": "abstract", "order_index": 0},
            {"title": "第一章 绪论", "section_type": "chapter", "order_index": 1},
            {"title": "第二章 文献综述", "section_type": "chapter", "order_index": 2},
            {"title": "第三章 研究方法", "section_type": "chapter", "order_index": 3},
            {"title": "第四章 研究结果", "section_type": "chapter", "order_index": 4},
            {"title": "第五章 结论与展望", "section_type": "chapter", "order_index": 5},
            {"title": "参考文献", "section_type": "references", "order_index": 6},
            {"title": "致谢", "section_type": "acknowledgment", "order_index": 7},
        ]

        for section_data in default_sections:
            section = PaperSection(
                paper_id=paper.id,
                **section_data,
            )
            self.db.add(section)

        await self.db.flush()
        await self.db.refresh(paper)
        return paper

    async def get_by_id(
        self,
        paper_id: uuid.UUID,
        with_sections: bool = False,
    ) -> Optional[Paper]:
        """通过ID获取论文"""
        query = select(Paper).where(Paper.id == paper_id)

        if with_sections:
            query = query.options(
                selectinload(Paper.sections)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_papers(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Paper], int]:
        """获取用户论文列表"""
        conditions = [Paper.owner_id == user_id]

        if status:
            conditions.append(Paper.status == status)

        base_query = select(Paper).where(*conditions)

        # 计算总数
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query) or 0

        # 分页查询
        result = await self.db.execute(
            base_query
            .order_by(Paper.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        papers = list(result.scalars().all())

        return papers, total

    async def update(
        self,
        paper_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[Paper]:
        """更新论文"""
        paper = await self.get_by_id(paper_id)
        if not paper:
            return None

        for field, value in update_data.items():
            if value is not None:
                setattr(paper, field, value)

        await self.db.flush()
        await self.db.refresh(paper)
        return paper

    async def delete(self, paper_id: uuid.UUID) -> bool:
        """删除论文"""
        paper = await self.get_by_id(paper_id)
        if not paper:
            return False

        await self.db.delete(paper)
        await self.db.flush()
        return True

    async def get_collaborator_papers(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Paper], int]:
        """获取用户协作的论文"""
        base_query = (
            select(Paper)
            .join(PaperCollaborator)
            .where(PaperCollaborator.user_id == user_id)
        )

        count_query = select(func.count()).select_from(base_query.subquery())
        total = await self.db.scalar(count_query) or 0

        result = await self.db.execute(
            base_query
            .order_by(Paper.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        papers = list(result.scalars().all())

        return papers, total


class SectionRepository:
    """章节数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        paper_id: uuid.UUID,
        section_data: Dict[str, Any],
    ) -> PaperSection:
        """创建章节"""
        section = PaperSection(paper_id=paper_id, **section_data)
        self.db.add(section)
        await self.db.flush()
        await self.db.refresh(section)
        return section

    async def get_by_id(self, section_id: uuid.UUID) -> Optional[PaperSection]:
        """获取章节"""
        result = await self.db.execute(
            select(PaperSection).where(PaperSection.id == section_id)
        )
        return result.scalar_one_or_none()

    async def get_paper_sections(
        self,
        paper_id: uuid.UUID,
    ) -> List[PaperSection]:
        """获取论文所有章节"""
        result = await self.db.execute(
            select(PaperSection)
            .where(PaperSection.paper_id == paper_id)
            .order_by(PaperSection.order_index)
        )
        return list(result.scalars().all())

    async def update(
        self,
        section_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[PaperSection]:
        """更新章节"""
        section = await self.get_by_id(section_id)
        if not section:
            return None

        for field, value in update_data.items():
            if value is not None:
                setattr(section, field, value)

        # 计算字数
        if section.content:
            section.word_count = len(section.content)

        await self.db.flush()
        await self.db.refresh(section)
        return section

    async def delete(self, section_id: uuid.UUID) -> bool:
        """删除章节"""
        section = await self.get_by_id(section_id)
        if not section:
            return False

        await self.db.delete(section)
        await self.db.flush()
        return True


class CollaboratorRepository:
    """协作者数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(
        self,
        paper_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str = "viewer",
        permissions: Optional[Dict[str, bool]] = None,
        invited_by: Optional[uuid.UUID] = None,
    ) -> PaperCollaborator:
        """添加协作者"""
        permissions = permissions or {}
        collaborator = PaperCollaborator(
            paper_id=paper_id,
            user_id=user_id,
            role=role,
            can_edit=permissions.get("can_edit", False),
            can_comment=permissions.get("can_comment", True),
            can_share=permissions.get("can_share", False),
            invited_by=invited_by,
        )
        self.db.add(collaborator)
        await self.db.flush()
        await self.db.refresh(collaborator)
        return collaborator

    async def get_paper_collaborators(
        self,
        paper_id: uuid.UUID,
    ) -> List[PaperCollaborator]:
        """获取论文协作者列表"""
        result = await self.db.execute(
            select(PaperCollaborator)
            .where(PaperCollaborator.paper_id == paper_id)
        )
        return list(result.scalars().all())

    async def update(
        self,
        paper_id: uuid.UUID,
        user_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[PaperCollaborator]:
        """更新协作者权限"""
        result = await self.db.execute(
            select(PaperCollaborator).where(
                PaperCollaborator.paper_id == paper_id,
                PaperCollaborator.user_id == user_id,
            )
        )
        collaborator = result.scalar_one_or_none()
        if not collaborator:
            return None

        for field, value in update_data.items():
            if value is not None:
                setattr(collaborator, field, value)

        await self.db.flush()
        await self.db.refresh(collaborator)
        return collaborator

    async def remove(
        self,
        paper_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """移除协作者"""
        result = await self.db.execute(
            select(PaperCollaborator).where(
                PaperCollaborator.paper_id == paper_id,
                PaperCollaborator.user_id == user_id,
            )
        )
        collaborator = result.scalar_one_or_none()
        if not collaborator:
            return False

        await self.db.delete(collaborator)
        await self.db.flush()
        return True

    async def is_collaborator(
        self,
        paper_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """检查是否为协作者"""
        result = await self.db.execute(
            select(func.count()).where(
                PaperCollaborator.paper_id == paper_id,
                PaperCollaborator.user_id == user_id,
            )
        )
        return (result.scalar() or 0) > 0


class VersionRepository:
    """版本数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        paper_id: uuid.UUID,
        version_number: int,
        content_snapshot: Optional[dict] = None,
        change_summary: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> PaperVersion:
        """创建版本"""
        version = PaperVersion(
            paper_id=paper_id,
            version_number=version_number,
            content_snapshot=content_snapshot,
            change_summary=change_summary,
            created_by=created_by,
        )
        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def get_paper_versions(
        self,
        paper_id: uuid.UUID,
        limit: int = 20,
    ) -> List[PaperVersion]:
        """获取论文版本历史"""
        result = await self.db.execute(
            select(PaperVersion)
            .where(PaperVersion.paper_id == paper_id)
            .order_by(PaperVersion.version_number.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_version_number(
        self,
        paper_id: uuid.UUID,
    ) -> int:
        """获取最新版本号"""
        result = await self.db.execute(
            select(func.max(PaperVersion.version_number)).where(
                PaperVersion.paper_id == paper_id
            )
        )
        return result.scalar() or 0


class TemplateRepository:
    """模板数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_public_templates(self) -> List[PaperTemplate]:
        """获取公开模板"""
        result = await self.db.execute(
            select(PaperTemplate)
            .where(PaperTemplate.is_public == True)
            .order_by(PaperTemplate.created_at)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        template_id: uuid.UUID,
    ) -> Optional[PaperTemplate]:
        """获取模板"""
        result = await self.db.execute(
            select(PaperTemplate).where(PaperTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
