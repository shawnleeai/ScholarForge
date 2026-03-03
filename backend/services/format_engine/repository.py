"""
格式引擎数据访问层
数据库 CRUD 操作
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession


class FormatTemplateRepository:
    """格式模板数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建格式模板"""
        if 'id' not in template_data:
            template_data['id'] = str(uuid.uuid4())

        columns = list(template_data.keys())
        placeholders = [f":{col}" for col in columns]

        query = text(f"""
            INSERT INTO format_templates ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """)

        result = await self.db.execute(query, template_data)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取模板详情"""
        query = text("""
            SELECT * FROM format_templates
            WHERE id = :template_id
        """)
        result = await self.db.execute(query, {"template_id": template_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def get_public_templates(
        self,
        template_type: Optional[str] = None,
        institution: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取公开模板列表"""
        conditions = ["is_public = TRUE"]
        params = {}

        if template_type:
            conditions.append("template_type = :template_type")
            params['template_type'] = template_type

        if institution:
            conditions.append("institution ILIKE :institution")
            params['institution'] = f"%{institution}%"

        where_clause = " AND ".join(conditions)

        # 计算总数
        count_query = text(f"""
            SELECT COUNT(*) FROM format_templates
            WHERE {where_clause}
        """)
        count_result = await self.db.execute(count_query, params)
        total = count_result.scalar() or 0

        # 分页查询
        query = text(f"""
            SELECT * FROM format_templates
            WHERE {where_clause}
            ORDER BY usage_count DESC, rating DESC
            LIMIT :limit OFFSET :offset
        """)

        params['limit'] = page_size
        params['offset'] = (page - 1) * page_size

        result = await self.db.execute(query, params)
        rows = result.fetchall()
        templates = [dict(row._mapping) for row in rows]

        return templates, total

    async def increment_usage(self, template_id: str) -> bool:
        """增加模板使用计数"""
        query = text("""
            UPDATE format_templates
            SET usage_count = usage_count + 1
            WHERE id = :template_id
            RETURNING id
        """)
        result = await self.db.execute(query, {"template_id": template_id})
        row = result.fetchone()
        await self.db.flush()
        return row is not None


class FormatTaskRepository:
    """格式任务数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建格式任务"""
        if 'id' not in task_data:
            task_data['id'] = str(uuid.uuid4())

        task_data['created_at'] = datetime.utcnow()

        columns = list(task_data.keys())
        placeholders = [f":{col}" for col in columns]

        query = text(f"""
            INSERT INTO format_tasks ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """)

        result = await self.db.execute(query, task_data)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        query = text("""
            SELECT * FROM format_tasks
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
            UPDATE format_tasks
            SET {set_clause}
            WHERE id = :task_id
            RETURNING id
        """)

        params = {**updates, "task_id": task_id}
        result = await self.db.execute(query, params)
        row = result.fetchone()
        await self.db.flush()
        return row is not None

    async def get_user_tasks(
        self,
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取用户的格式任务"""
        conditions = ["user_id = :user_id"]
        params = {"user_id": user_id}

        if status:
            conditions.append("status = :status")
            params['status'] = status

        where_clause = " AND ".join(conditions)

        # 计算总数
        count_query = text(f"""
            SELECT COUNT(*) FROM format_tasks
            WHERE {where_clause}
        """)
        count_result = await self.db.execute(count_query, params)
        total = count_result.scalar() or 0

        # 分页查询
        query = text(f"""
            SELECT t.*, ft.name as template_name
            FROM format_tasks t
            LEFT JOIN format_templates ft ON t.template_id = ft.id
            WHERE t.{where_clause.replace('user_id', 't.user_id').replace('status', 't.status')}
            ORDER BY t.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        params['limit'] = page_size
        params['offset'] = (page - 1) * page_size

        result = await self.db.execute(query, params)
        rows = result.fetchall()
        tasks = [dict(row._mapping) for row in rows]

        return tasks, total


class FormatSettingsRepository:
    """格式设置数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, user_id: str) -> Dict[str, Any]:
        """获取或创建设置"""
        query = text("""
            SELECT * FROM format_settings
            WHERE user_id = :user_id
        """)
        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        if row:
            return dict(row._mapping)

        # 创建默认设置
        query = text("""
            INSERT INTO format_settings (user_id)
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
            UPDATE format_settings
            SET {set_clause}
            WHERE user_id = :user_id
            RETURNING *
        """)

        params = {**updates, "user_id": user_id}
        result = await self.db.execute(query, params)
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None
