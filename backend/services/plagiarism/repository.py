"""
查重检测数据访问层
数据库 CRUD 操作
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession


class PlagiarismCheckRepository:
    """查重检测任务数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, check_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建查重任务"""
        if 'id' not in check_data:
            check_data['id'] = str(uuid.uuid4())

        check_data['submitted_at'] = datetime.utcnow()

        columns = list(check_data.keys())
        placeholders = [f":{col}" for col in columns]

        query = text(f"""
            INSERT INTO plagiarism_checks ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """)

        result = await self.db.execute(query, check_data)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_by_id(self, check_id: str) -> Optional[Dict[str, Any]]:
        """获取查重任务"""
        query = text("""
            SELECT * FROM plagiarism_checks
            WHERE id = :check_id
        """)
        result = await self.db.execute(query, {"check_id": check_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def update_status(
        self,
        check_id: str,
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
            UPDATE plagiarism_checks
            SET {set_clause}
            WHERE id = :check_id
            RETURNING id
        """)

        params = {**updates, "check_id": check_id}
        result = await self.db.execute(query, params)
        row = result.fetchone()
        await self.db.flush()
        return row is not None

    async def get_user_checks(
        self,
        user_id: str,
        paper_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取用户的查重任务"""
        conditions = ["user_id = :user_id"]
        params = {"user_id": user_id}

        if paper_id:
            conditions.append("paper_id = :paper_id")
            params['paper_id'] = paper_id

        if status:
            conditions.append("status = :status")
            params['status'] = status

        where_clause = " AND ".join(conditions)

        # 计算总数
        count_query = text(f"""
            SELECT COUNT(*) FROM plagiarism_checks
            WHERE {where_clause}
        """)
        count_result = await self.db.execute(count_query, params)
        total = count_result.scalar() or 0

        # 分页查询
        query = text(f"""
            SELECT * FROM plagiarism_checks
            WHERE {where_clause}
            ORDER BY submitted_at DESC
            LIMIT :limit OFFSET :offset
        """)

        params['limit'] = page_size
        params['offset'] = (page - 1) * page_size

        result = await self.db.execute(query, params)
        rows = result.fetchall()
        checks = [dict(row._mapping) for row in rows]

        return checks, total

    async def get_paper_checks(self, paper_id: str) -> List[Dict[str, Any]]:
        """获取论文的所有查重任务"""
        query = text("""
            SELECT * FROM plagiarism_checks
            WHERE paper_id = :paper_id
            ORDER BY submitted_at DESC
        """)
        result = await self.db.execute(query, {"paper_id": paper_id})
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def get_by_file_hash(self, file_hash: str, user_id: str) -> Optional[Dict[str, Any]]:
        """通过文件哈希获取最近的查重任务"""
        query = text("""
            SELECT * FROM plagiarism_checks
            WHERE file_hash = :file_hash AND user_id = :user_id
            ORDER BY submitted_at DESC
            LIMIT 1
        """)
        result = await self.db.execute(query, {
            "file_hash": file_hash,
            "user_id": user_id
        })
        row = result.fetchone()
        return dict(row._mapping) if row else None


class PlagiarismHistoryRepository:
    """查重历史记录数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建查重历史记录"""
        if 'id' not in history_data:
            history_data['id'] = str(uuid.uuid4())

        columns = list(history_data.keys())
        placeholders = [f":{col}" for col in columns]

        query = text(f"""
            INSERT INTO plagiarism_history ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """)

        result = await self.db.execute(query, history_data)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_paper_history(self, paper_id: str) -> List[Dict[str, Any]]:
        """获取论文的查重历史"""
        query = text("""
            SELECT h.*, c.task_name, c.engine
            FROM plagiarism_history h
            JOIN plagiarism_checks c ON h.check_id = c.id
            WHERE h.paper_id = :paper_id
            ORDER BY h.created_at DESC
        """)
        result = await self.db.execute(query, {"paper_id": paper_id})
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def get_next_version(self, paper_id: str) -> int:
        """获取下一个版本号"""
        query = text("""
            SELECT COALESCE(MAX(version), 0) + 1
            FROM plagiarism_history
            WHERE paper_id = :paper_id
        """)
        result = await self.db.execute(query, {"paper_id": paper_id})
        return result.scalar() or 1


class PlagiarismWhitelistRepository:
    """查重白名单数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, whitelist_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加白名单条目"""
        if 'id' not in whitelist_data:
            whitelist_data['id'] = str(uuid.uuid4())

        # 计算内容哈希
        if 'content' in whitelist_data and not whitelist_data.get('content_hash'):
            import hashlib
            content = whitelist_data['content'].encode('utf-8')
            whitelist_data['content_hash'] = hashlib.sha256(content).hexdigest()[:64]

        columns = list(whitelist_data.keys())
        placeholders = [f":{col}" for col in columns]

        query = text(f"""
            INSERT INTO plagiarism_whitelist ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """)

        result = await self.db.execute(query, whitelist_data)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_paper_whitelist(self, paper_id: str) -> List[Dict[str, Any]]:
        """获取论文的白名单"""
        query = text("""
            SELECT * FROM plagiarism_whitelist
            WHERE paper_id = :paper_id
            ORDER BY created_at DESC
        """)
        result = await self.db.execute(query, {"paper_id": paper_id})
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def exists(self, content_hash: str, paper_id: str) -> bool:
        """检查内容是否已在白名单中"""
        query = text("""
            SELECT EXISTS(
                SELECT 1 FROM plagiarism_whitelist
                WHERE content_hash = :content_hash AND paper_id = :paper_id
            )
        """)
        result = await self.db.execute(query, {
            "content_hash": content_hash,
            "paper_id": paper_id
        })
        return result.scalar()

    async def delete(self, whitelist_id: str, user_id: str) -> bool:
        """删除白名单条目"""
        query = text("""
            DELETE FROM plagiarism_whitelist
            WHERE id = :id AND user_id = :user_id
            RETURNING id
        """)
        result = await self.db.execute(query, {
            "id": whitelist_id,
            "user_id": user_id
        })
        row = result.fetchone()
        await self.db.flush()
        return row is not None


class PlagiarismSettingsRepository:
    """查重设置数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, user_id: str) -> Dict[str, Any]:
        """获取或创建设置"""
        query = text("""
            SELECT * FROM plagiarism_settings
            WHERE user_id = :user_id
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        if row:
            return dict(row._mapping)

        # 创建默认设置
        query = text("""
            INSERT INTO plagiarism_settings (user_id)
            VALUES (:user_id)
            RETURNING *
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def update(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新设置"""
        updates['updated_at'] = datetime.utcnow()

        set_clause = ', '.join([f"{k} = :{k}" for k in updates.keys()])

        query = text(f"""
            UPDATE plagiarism_settings
            SET {set_clause}
            WHERE user_id = :user_id
            RETURNING *
        """)

        params = {**updates, "user_id": user_id}
        result = await self.db.execute(query, params)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None
