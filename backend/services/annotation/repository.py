"""
批注数据访问层
数据库 CRUD 操作
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .schemas import AnnotationType, AnnotationStatus, AnnotationPriority


class AnnotationRepository:
    """批注数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        paper_id: uuid.UUID,
        author_id: uuid.UUID,
        annotation_type: str,
        content: str,
        section_id: Optional[uuid.UUID] = None,
        position: Optional[Dict] = None,
        priority: str = "medium",
        parent_id: Optional[uuid.UUID] = None,
    ) -> Any:
        """创建批注"""
        # 动态导入模型避免循环依赖
        from sqlalchemy import text

        annotation_id = uuid.uuid4()
        now = datetime.now()

        query = text("""
            INSERT INTO annotations
            (id, paper_id, section_id, author_id, annotation_type, content, position, status, parent_id, created_at, updated_at)
            VALUES (:id, :paper_id, :section_id, :author_id, :annotation_type, :content, :position::jsonb, 'pending', :parent_id, :now, :now)
            RETURNING *
        """)

        result = await self.db.execute(query, {
            "id": annotation_id,
            "paper_id": paper_id,
            "section_id": section_id,
            "author_id": author_id,
            "annotation_type": annotation_type,
            "content": content,
            "position": position or {},
            "parent_id": parent_id,
            "now": now,
        })

        await self.db.flush()
        return result.fetchone()

    async def get_by_id(self, annotation_id: uuid.UUID) -> Optional[Any]:
        """获取单条批注"""
        from sqlalchemy import text

        query = text("""
            SELECT a.*, u.username, u.full_name, u.avatar_url
            FROM annotations a
            LEFT JOIN users u ON a.author_id = u.id
            WHERE a.id = :id
        """)

        result = await self.db.execute(query, {"id": annotation_id})
        return result.fetchone()

    async def get_paper_annotations(
        self,
        paper_id: uuid.UUID,
        section_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        annotation_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Any], int]:
        """获取论文的批注列表"""
        from sqlalchemy import text

        conditions = ["a.paper_id = :paper_id"]
        params = {"paper_id": paper_id}

        if section_id:
            conditions.append("a.section_id = :section_id")
            params["section_id"] = section_id
        if status:
            conditions.append("a.status = :status")
            params["status"] = status
        if annotation_type:
            conditions.append("a.annotation_type = :annotation_type")
            params["annotation_type"] = annotation_type

        where_clause = " AND ".join(conditions)

        # 统计总数
        count_query = text(f"""
            SELECT COUNT(*) as total
            FROM annotations a
            WHERE {where_clause}
        """)
        count_result = await self.db.execute(count_query, params)
        total = count_result.scalar() or 0

        # 分页查询
        params["offset"] = (page - 1) * page_size
        params["limit"] = page_size

        list_query = text(f"""
            SELECT a.*, u.username, u.full_name, u.avatar_url,
                   (SELECT COUNT(*) FROM annotations r WHERE r.parent_id = a.id) as reply_count
            FROM annotations a
            LEFT JOIN users u ON a.author_id = u.id
            WHERE {where_clause}
            ORDER BY a.created_at DESC
            OFFSET :offset LIMIT :limit
        """)

        result = await self.db.execute(list_query, params)
        return list(result.fetchall()), total

    async def get_annotation_thread(self, annotation_id: uuid.UUID) -> Tuple[Any, List[Any]]:
        """获取批注线程（包含所有回复）"""
        from sqlalchemy import text

        # 获取主批注
        main_query = text("""
            SELECT a.*, u.username, u.full_name, u.avatar_url
            FROM annotations a
            LEFT JOIN users u ON a.author_id = u.id
            WHERE a.id = :id
        """)
        main_result = await self.db.execute(main_query, {"id": annotation_id})
        main_annotation = main_result.fetchone()

        if not main_annotation:
            return None, []

        # 获取所有回复
        replies_query = text("""
            SELECT a.*, u.username, u.full_name, u.avatar_url
            FROM annotations a
            LEFT JOIN users u ON a.author_id = u.id
            WHERE a.parent_id = :id
            ORDER BY a.created_at ASC
        """)
        replies_result = await self.db.execute(replies_query, {"id": annotation_id})
        replies = list(replies_result.fetchall())

        return main_annotation, replies

    async def update(
        self,
        annotation_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[Any]:
        """更新批注"""
        from sqlalchemy import text

        set_clauses = []
        params = {"id": annotation_id}

        if "content" in update_data:
            set_clauses.append("content = :content")
            params["content"] = update_data["content"]
        if "status" in update_data:
            set_clauses.append("status = :status")
            params["status"] = update_data["status"]
        if "priority" in update_data:
            set_clauses.append("priority = :priority")
            params["priority"] = update_data["priority"]

        if not set_clauses:
            return await self.get_by_id(annotation_id)

        set_clauses.append("updated_at = :now")
        params["now"] = datetime.now()

        query = text(f"""
            UPDATE annotations
            SET {', '.join(set_clauses)}
            WHERE id = :id
            RETURNING *
        """)

        result = await self.db.execute(query, params)
        await self.db.flush()
        return result.fetchone()

    async def resolve(
        self,
        annotation_id: uuid.UUID,
        resolved_by: uuid.UUID,
        resolution_note: Optional[str] = None,
    ) -> Optional[Any]:
        """解决批注"""
        from sqlalchemy import text

        now = datetime.now()
        query = text("""
            UPDATE annotations
            SET status = 'resolved',
                resolved_by = :resolved_by,
                resolved_at = :now,
                updated_at = :now
            WHERE id = :id
            RETURNING *
        """)

        result = await self.db.execute(query, {
            "id": annotation_id,
            "resolved_by": resolved_by,
            "now": now,
        })
        await self.db.flush()
        return result.fetchone()

    async def delete(self, annotation_id: uuid.UUID) -> bool:
        """删除批注"""
        from sqlalchemy import text

        query = text("DELETE FROM annotations WHERE id = :id")
        result = await self.db.execute(query, {"id": annotation_id})
        await self.db.flush()
        return result.rowcount > 0

    async def get_stats(self, paper_id: uuid.UUID) -> Dict[str, Any]:
        """获取批注统计"""
        from sqlalchemy import text

        # 基础统计
        stats_query = text("""
            SELECT
                COUNT(*) as total_count,
                COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
                COUNT(*) FILTER (WHERE status = 'accepted') as accepted_count,
                COUNT(*) FILTER (WHERE status = 'rejected') as rejected_count,
                COUNT(*) FILTER (WHERE status = 'resolved') as resolved_count,
                COUNT(*) FILTER (WHERE created_at > :week_ago) as recent_count
            FROM annotations
            WHERE paper_id = :paper_id AND parent_id IS NULL
        """)

        week_ago = datetime.now() - timedelta(days=7)
        result = await self.db.execute(stats_query, {
            "paper_id": paper_id,
            "week_ago": week_ago,
        })
        stats = result.fetchone()

        # 按类型统计
        type_query = text("""
            SELECT annotation_type, COUNT(*) as count
            FROM annotations
            WHERE paper_id = :paper_id
            GROUP BY annotation_type
        """)
        type_result = await self.db.execute(type_query, {"paper_id": paper_id})
        by_type = {row.annotation_type: row.count for row in type_result.fetchall()}

        # 按优先级统计
        priority_query = text("""
            SELECT priority, COUNT(*) as count
            FROM annotations
            WHERE paper_id = :paper_id
            GROUP BY priority
        """)
        priority_result = await self.db.execute(priority_query, {"paper_id": paper_id})
        by_priority = {row.priority: row.count for row in priority_result.fetchall()}

        return {
            "total_count": stats.total_count or 0,
            "pending_count": stats.pending_count or 0,
            "accepted_count": stats.accepted_count or 0,
            "rejected_count": stats.rejected_count or 0,
            "resolved_count": stats.resolved_count or 0,
            "recent_count": stats.recent_count or 0,
            "by_type": by_type,
            "by_priority": by_priority,
        }

    async def get_user_annotations(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Any], int]:
        """获取用户的批注列表"""
        from sqlalchemy import text

        # 统计总数
        count_query = text("""
            SELECT COUNT(*) FROM annotations WHERE author_id = :user_id
        """)
        total = await self.db.scalar(count_query, {"user_id": user_id}) or 0

        # 分页查询
        list_query = text("""
            SELECT a.*, p.title as paper_title, u.username, u.full_name
            FROM annotations a
            LEFT JOIN papers p ON a.paper_id = p.id
            LEFT JOIN users u ON a.author_id = u.id
            WHERE a.author_id = :user_id
            ORDER BY a.created_at DESC
            OFFSET :offset LIMIT :limit
        """)

        result = await self.db.execute(list_query, {
            "user_id": user_id,
            "offset": (page - 1) * page_size,
            "limit": page_size,
        })

        return list(result.fetchall()), total
