"""
参考文献数据访问层
数据库 CRUD 操作
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ReferenceRepository:
    """参考文献数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, reference_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建参考文献"""
        from backend.shared.database import references_table

        # 确保ID存在
        if 'id' not in reference_data:
            reference_data['id'] = str(uuid.uuid4())

        # 设置时间戳
        now = datetime.utcnow()
        reference_data['added_at'] = now
        reference_data['updated_at'] = now

        # 构建插入语句
        columns = list(reference_data.keys())
        values = [reference_data[col] for col in columns]
        placeholders = [f":{col}" for col in columns]

        query = text(f"""
            INSERT INTO references_table ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """)

        result = await self.db.execute(query, reference_data)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_by_id(self, reference_id: str) -> Optional[Dict[str, Any]]:
        """通过ID获取参考文献"""
        query = text("""
            SELECT * FROM references_table
            WHERE id = :reference_id AND status = 'active'
        """)
        result = await self.db.execute(query, {"reference_id": reference_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def get_by_doi(self, user_id: str, doi: str) -> Optional[Dict[str, Any]]:
        """通过DOI获取用户的参考文献"""
        query = text("""
            SELECT * FROM references_table
            WHERE user_id = :user_id AND doi = :doi AND status = 'active'
        """)
        result = await self.db.execute(query, {"user_id": user_id, "doi": doi})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def update(
        self,
        reference_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新参考文献"""
        # 移除不可更新的字段
        update_data.pop('id', None)
        update_data.pop('user_id', None)
        update_data.pop('added_at', None)

        update_data['updated_at'] = datetime.utcnow()

        # 构建SET语句
        set_clause = ', '.join([f"{k} = :{k}" for k in update_data.keys()])

        query = text(f"""
            UPDATE references_table
            SET {set_clause}
            WHERE id = :reference_id AND user_id = :user_id
            RETURNING *
        """)

        params = {**update_data, "reference_id": reference_id, "user_id": user_id}
        result = await self.db.execute(query, params)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def delete(self, reference_id: str, user_id: str) -> bool:
        """软删除参考文献"""
        query = text("""
            UPDATE references_table
            SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
            WHERE id = :reference_id AND user_id = :user_id
            RETURNING id
        """)
        result = await self.db.execute(query, {
            "reference_id": reference_id,
            "user_id": user_id
        })
        row = result.fetchone()
        await self.db.flush()
        return row is not None

    async def get_user_references(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取用户的参考文献列表"""
        filters = filters or {}

        # 构建WHERE条件
        conditions = ["user_id = :user_id", "status = 'active'"]
        params = {"user_id": user_id}

        if filters.get('paper_id'):
            conditions.append("paper_id = :paper_id")
            params['paper_id'] = filters['paper_id']

        if filters.get('folder_id'):
            conditions.append("folder_id = :folder_id")
            params['folder_id'] = filters['folder_id']

        if filters.get('publication_type'):
            conditions.append("publication_type = :publication_type")
            params['publication_type'] = filters['publication_type']

        if filters.get('is_important') is not None:
            conditions.append("is_important = :is_important")
            params['is_important'] = filters['is_important']

        if filters.get('is_read') is not None:
            conditions.append("is_read = :is_read")
            params['is_read'] = filters['is_read']

        if filters.get('year_from'):
            conditions.append("publication_year >= :year_from")
            params['year_from'] = filters['year_from']

        if filters.get('year_to'):
            conditions.append("publication_year <= :year_to")
            params['year_to'] = filters['year_to']

        if filters.get('tags'):
            tag_conditions = []
            for i, tag in enumerate(filters['tags']):
                key = f"tag_{i}"
                tag_conditions.append(f":{key} = ANY(tags)")
                params[key] = tag
            conditions.append(f"({' OR '.join(tag_conditions)})")

        if filters.get('search'):
            conditions.append("""
                (title ILIKE :search
                OR :search = ANY(authors)
                OR abstract ILIKE :search
                OR doi ILIKE :search)
            """)
            params['search'] = f"%{filters['search']}%"

        where_clause = " AND ".join(conditions)

        # 计算总数
        count_query = text(f"""
            SELECT COUNT(*) FROM references_table
            WHERE {where_clause}
        """)
        count_result = await self.db.execute(count_query, params)
        total = count_result.scalar() or 0

        # 分页查询
        order_by = filters.get('order_by', 'added_at DESC')
        allowed_orders = {
            'added_at DESC': 'added_at DESC',
            'added_at ASC': 'added_at ASC',
            'publication_year DESC': 'publication_year DESC NULLS LAST',
            'publication_year ASC': 'publication_year ASC NULLS LAST',
            'title ASC': 'title ASC',
            'citation_count DESC': 'citation_count DESC NULLS LAST',
        }
        order_clause = allowed_orders.get(order_by, 'added_at DESC')

        query = text(f"""
            SELECT * FROM references_table
            WHERE {where_clause}
            ORDER BY {order_clause}
            LIMIT :limit OFFSET :offset
        """)

        params['limit'] = page_size
        params['offset'] = (page - 1) * page_size

        result = await self.db.execute(query, params)
        rows = result.fetchall()
        references = [dict(row._mapping) for row in rows]

        return references, total

    async def add_tags(self, reference_id: str, user_id: str, tags: List[str]) -> bool:
        """添加标签到参考文献"""
        query = text("""
            UPDATE references_table
            SET tags = array_distinct(array_cat(tags, :tags)),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :reference_id AND user_id = :user_id
            RETURNING id
        """)
        result = await self.db.execute(query, {
            "reference_id": reference_id,
            "user_id": user_id,
            "tags": tags
        })
        row = result.fetchone()
        await self.db.flush()
        return row is not None

    async def remove_tags(self, reference_id: str, user_id: str, tags: List[str]) -> bool:
        """从参考文献移除标签"""
        query = text("""
            UPDATE references_table
            SET tags = array_remove_array(tags, :tags),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :reference_id AND user_id = :user_id
            RETURNING id
        """)
        result = await self.db.execute(query, {
            "reference_id": reference_id,
            "user_id": user_id,
            "tags": tags
        })
        row = result.fetchone()
        await self.db.flush()
        return row is not None

    async def get_user_tags(self, user_id: str) -> List[str]:
        """获取用户的所有标签"""
        query = text("""
            SELECT DISTINCT unnest(tags) as tag
            FROM references_table
            WHERE user_id = :user_id AND status = 'active'
            ORDER BY tag
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        return [row.tag for row in rows if row.tag]

    async def update_read_status(
        self,
        reference_id: str,
        user_id: str,
        is_read: bool
    ) -> bool:
        """更新阅读状态"""
        query = text("""
            UPDATE references_table
            SET is_read = :is_read,
                last_accessed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :reference_id AND user_id = :user_id
            RETURNING id
        """)
        result = await self.db.execute(query, {
            "reference_id": reference_id,
            "user_id": user_id,
            "is_read": is_read
        })
        row = result.fetchone()
        await self.db.flush()
        return row is not None

    async def batch_create(self, references: List[Dict[str, Any]]) -> int:
        """批量创建参考文献"""
        if not references:
            return 0

        created_count = 0
        for ref_data in references:
            try:
                await self.create(ref_data)
                created_count += 1
            except Exception:
                continue

        return created_count

    async def get_statistics(self, user_id: str, paper_id: Optional[str] = None) -> Dict[str, Any]:
        """获取参考文献统计"""
        conditions = ["user_id = :user_id", "status = 'active'"]
        params = {"user_id": user_id}

        if paper_id:
            conditions.append("paper_id = :paper_id")
            params['paper_id'] = paper_id

        where_clause = " AND ".join(conditions)

        # 总体统计
        query = text(f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_read) as read_count,
                COUNT(*) FILTER (WHERE is_important) as important_count,
                COUNT(*) FILTER (WHERE publication_type = 'journal') as journal_count,
                COUNT(*) FILTER (WHERE publication_type = 'conference') as conference_count,
                COUNT(*) FILTER (WHERE publication_type = 'book') as book_count,
                COUNT(*) FILTER (WHERE publication_year IS NOT NULL) as with_year_count,
                AVG(rating) FILTER (WHERE rating IS NOT NULL) as avg_rating
            FROM references_table
            WHERE {where_clause}
        """)
        result = await self.db.execute(query, params)
        stats_row = result.fetchone()

        # 年份分布
        year_query = text(f"""
            SELECT publication_year as year, COUNT(*) as count
            FROM references_table
            WHERE {where_clause} AND publication_year IS NOT NULL
            GROUP BY publication_year
            ORDER BY publication_year DESC
            LIMIT 10
        """)
        year_result = await self.db.execute(year_query, params)
        year_distribution = [dict(row._mapping) for row in year_result.fetchall()]

        # 高频作者
        author_query = text(f"""
            SELECT author, COUNT(*) as count
            FROM references_table, unnest(authors) as author
            WHERE {where_clause}
            GROUP BY author
            ORDER BY count DESC
            LIMIT 10
        """)
        author_result = await self.db.execute(author_query, params)
        top_authors = [dict(row._mapping) for row in author_result.fetchall()]

        # 高频期刊
        journal_query = text(f"""
            SELECT journal_name, COUNT(*) as count
            FROM references_table
            WHERE {where_clause} AND journal_name IS NOT NULL
            GROUP BY journal_name
            ORDER BY count DESC
            LIMIT 10
        """)
        journal_result = await self.db.execute(journal_query, params)
        top_journals = [dict(row._mapping) for row in journal_result.fetchall()]

        return {
            "total": stats_row.total,
            "read_count": stats_row.read_count,
            "unread_count": stats_row.total - stats_row.read_count,
            "important_count": stats_row.important_count,
            "by_type": {
                "journal": stats_row.journal_count,
                "conference": stats_row.conference_count,
                "book": stats_row.book_count,
                "others": stats_row.total - stats_row.journal_count - stats_row.conference_count - stats_row.book_count
            },
            "with_year_count": stats_row.with_year_count,
            "avg_rating": round(stats_row.avg_rating, 2) if stats_row.avg_rating else None,
            "year_distribution": year_distribution,
            "top_authors": top_authors,
            "top_journals": top_journals
        }


class CitationRepository:
    """引用关系数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, citation_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建引用关系"""
        if 'id' not in citation_data:
            citation_data['id'] = str(uuid.uuid4())

        columns = list(citation_data.keys())
        placeholders = [f":{col}" for col in columns]

        query = text(f"""
            INSERT INTO reference_citations ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """)

        result = await self.db.execute(query, citation_data)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_paper_citations(self, paper_id: str) -> List[Dict[str, Any]]:
        """获取论文的所有引用"""
        query = text("""
            SELECT c.*, r.title, r.authors, r.publication_year
            FROM reference_citations c
            LEFT JOIN references_table r ON c.citing_ref_id = r.id
            WHERE c.paper_id = :paper_id
            ORDER BY c.citation_number ASC
        """)
        result = await self.db.execute(query, {"paper_id": paper_id})
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def get_next_citation_number(self, paper_id: str) -> int:
        """获取下一个引用序号"""
        query = text("""
            SELECT COALESCE(MAX(citation_number), 0) + 1
            FROM reference_citations
            WHERE paper_id = :paper_id
        """)
        result = await self.db.execute(query, {"paper_id": paper_id})
        return result.scalar() or 1

    async def delete(self, citation_id: str) -> bool:
        """删除引用关系"""
        query = text("""
            DELETE FROM reference_citations
            WHERE id = :citation_id
            RETURNING id
        """)
        result = await self.db.execute(query, {"citation_id": citation_id})
        row = result.fetchone()
        await self.db.flush()
        return row is not None


class ReferenceFolderRepository:
    """文献文件夹数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, folder_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建文件夹"""
        if 'id' not in folder_data:
            folder_data['id'] = str(uuid.uuid4())

        folder_data['created_at'] = datetime.utcnow()
        folder_data['updated_at'] = datetime.utcnow()

        columns = list(folder_data.keys())
        placeholders = [f":{col}" for col in columns]

        query = text(f"""
            INSERT INTO reference_folders ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """)

        result = await self.db.execute(query, folder_data)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_by_id(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """获取文件夹"""
        query = text("""
            SELECT * FROM reference_folders
            WHERE id = :folder_id
        """)
        result = await self.db.execute(query, {"folder_id": folder_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def get_user_folders(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有文件夹"""
        query = text("""
            SELECT f.*,
                   (SELECT COUNT(*) FROM references_table
                    WHERE folder_id = f.id AND status = 'active') as item_count
            FROM reference_folders f
            WHERE f.user_id = :user_id
            ORDER BY f.sort_order ASC, f.created_at ASC
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def update(
        self,
        folder_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """更新文件夹"""
        update_data.pop('id', None)
        update_data.pop('user_id', None)
        update_data.pop('created_at', None)
        update_data['updated_at'] = datetime.utcnow()

        set_clause = ', '.join([f"{k} = :{k}" for k in update_data.keys()])

        query = text(f"""
            UPDATE reference_folders
            SET {set_clause}
            WHERE id = :folder_id AND user_id = :user_id
            RETURNING *
        """)

        params = {**update_data, "folder_id": folder_id, "user_id": user_id}
        result = await self.db.execute(query, params)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def delete(self, folder_id: str, user_id: str) -> bool:
        """删除文件夹"""
        query = text("""
            DELETE FROM reference_folders
            WHERE id = :folder_id AND user_id = :user_id
            RETURNING id
        """)
        result = await self.db.execute(query, {
            "folder_id": folder_id,
            "user_id": user_id
        })
        row = result.fetchone()
        await self.db.flush()
        return row is not None


class ImportTaskRepository:
    """导入任务数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建导入任务"""
        if 'id' not in task_data:
            task_data['id'] = str(uuid.uuid4())

        task_data['created_at'] = datetime.utcnow()

        columns = list(task_data.keys())
        placeholders = [f":{col}" for col in columns]

        query = text(f"""
            INSERT INTO reference_import_tasks ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """)

        result = await self.db.execute(query, task_data)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取导入任务"""
        query = text("""
            SELECT * FROM reference_import_tasks
            WHERE id = :task_id
        """)
        result = await self.db.execute(query, {"task_id": task_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def update_status(
        self,
        task_id: str,
        status: str,
        updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新任务状态"""
        updates = updates or {}
        updates['status'] = status

        if status in ['completed', 'failed']:
            updates['completed_at'] = datetime.utcnow()

        set_clause = ', '.join([f"{k} = :{k}" for k in updates.keys()])

        query = text(f"""
            UPDATE reference_import_tasks
            SET {set_clause}
            WHERE id = :task_id
            RETURNING id
        """)

        params = {**updates, "task_id": task_id}
        result = await self.db.execute(query, params)
        row = result.fetchone()
        await self.db.flush()
        return row is not None

    async def get_user_tasks(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的导入任务"""
        query = text("""
            SELECT * FROM reference_import_tasks
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        result = await self.db.execute(query, {"user_id": user_id, "limit": limit})
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
