"""
进度管理数据仓库
Progress Repository Layer
"""

from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc


class MilestoneRepository:
    """里程碑仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建里程碑"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO milestones (
                id, paper_id, title, description, planned_date, actual_date,
                status, completion_percentage, created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :paper_id, :title, :description, :planned_date, :actual_date,
                :status, :completion_percentage, NOW(), NOW()
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "paper_id": data["paper_id"],
            "title": data["title"],
            "description": data.get("description", ""),
            "planned_date": data.get("planned_date"),
            "actual_date": data.get("actual_date"),
            "status": data.get("status", "pending"),
            "completion_percentage": data.get("completion_percentage", 0),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_id(self, milestone_id: str) -> Optional[dict]:
        """根据ID获取里程碑"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM milestones WHERE id = :milestone_id
        """)

        result = await self.db.execute(query, {"milestone_id": milestone_id})
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_paper(self, paper_id: str, status: Optional[str] = None) -> List[dict]:
        """获取论文的所有里程碑"""
        from sqlalchemy import text

        if status:
            query = text("""
                SELECT * FROM milestones
                WHERE paper_id = :paper_id AND status = :status
                ORDER BY planned_date ASC
            """)
            result = await self.db.execute(query, {"paper_id": paper_id, "status": status})
        else:
            query = text("""
                SELECT * FROM milestones
                WHERE paper_id = :paper_id
                ORDER BY planned_date ASC
            """)
            result = await self.db.execute(query, {"paper_id": paper_id})

        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def update(self, milestone_id: str, data: dict) -> Optional[dict]:
        """更新里程碑"""
        from sqlalchemy import text

        fields = []
        params = {"milestone_id": milestone_id}

        if "title" in data:
            fields.append("title = :title")
            params["title"] = data["title"]
        if "description" in data:
            fields.append("description = :description")
            params["description"] = data["description"]
        if "planned_date" in data:
            fields.append("planned_date = :planned_date")
            params["planned_date"] = data["planned_date"]
        if "actual_date" in data:
            fields.append("actual_date = :actual_date")
            params["actual_date"] = data["actual_date"]
        if "status" in data:
            fields.append("status = :status")
            params["status"] = data["status"]
        if "completion_percentage" in data:
            fields.append("completion_percentage = :completion_percentage")
            params["completion_percentage"] = data["completion_percentage"]

        if not fields:
            return await self.get_by_id(milestone_id)

        fields.append("updated_at = NOW()")

        query = text(f"""
            UPDATE milestones
            SET {', '.join(fields)}
            WHERE id = :milestone_id
            RETURNING *
        """)

        result = await self.db.execute(query, params)
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def delete(self, milestone_id: str) -> bool:
        """删除里程碑"""
        from sqlalchemy import text

        query = text("""
            DELETE FROM milestones WHERE id = :milestone_id RETURNING id
        """)

        result = await self.db.execute(query, {"milestone_id": milestone_id})
        await self.db.commit()
        return result.fetchone() is not None

    async def count_by_paper(self, paper_id: str, status: Optional[str] = None) -> int:
        """统计里程碑数量"""
        from sqlalchemy import text

        if status:
            query = text("""
                SELECT COUNT(*) as count FROM milestones
                WHERE paper_id = :paper_id AND status = :status
            """)
            result = await self.db.execute(query, {"paper_id": paper_id, "status": status})
        else:
            query = text("""
                SELECT COUNT(*) as count FROM milestones WHERE paper_id = :paper_id
            """)
            result = await self.db.execute(query, {"paper_id": paper_id})

        row = result.fetchone()
        return row[0] if row else 0


class TaskRepository:
    """任务仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建任务"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO tasks (
                id, paper_id, milestone_id, title, description, status,
                priority, progress, planned_start, planned_end, actual_start, actual_end,
                assignee_id, created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :paper_id, :milestone_id, :title, :description, :status,
                :priority, :progress, :planned_start, :planned_end, :actual_start, :actual_end,
                :assignee_id, NOW(), NOW()
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "paper_id": data["paper_id"],
            "milestone_id": data.get("milestone_id"),
            "title": data["title"],
            "description": data.get("description", ""),
            "status": data.get("status", "pending"),
            "priority": data.get("priority", "medium"),
            "progress": data.get("progress", 0),
            "planned_start": data.get("planned_start"),
            "planned_end": data.get("planned_end"),
            "actual_start": data.get("actual_start"),
            "actual_end": data.get("actual_end"),
            "assignee_id": data.get("assignee_id"),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_id(self, task_id: str) -> Optional[dict]:
        """根据ID获取任务"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM tasks WHERE id = :task_id
        """)

        result = await self.db.execute(query, {"task_id": task_id})
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_paper(
        self,
        paper_id: str,
        milestone_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[dict]:
        """获取论文的所有任务"""
        from sqlalchemy import text

        conditions = ["paper_id = :paper_id"]
        params = {"paper_id": paper_id}

        if milestone_id:
            conditions.append("milestone_id = :milestone_id")
            params["milestone_id"] = milestone_id
        if status:
            conditions.append("status = :status")
            params["status"] = status

        query = text(f"""
            SELECT * FROM tasks
            WHERE {' AND '.join(conditions)}
            ORDER BY planned_start ASC, priority DESC
        """)

        result = await self.db.execute(query, params)
        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def update(self, task_id: str, data: dict) -> Optional[dict]:
        """更新任务"""
        from sqlalchemy import text

        fields = []
        params = {"task_id": task_id}

        if "title" in data:
            fields.append("title = :title")
            params["title"] = data["title"]
        if "description" in data:
            fields.append("description = :description")
            params["description"] = data["description"]
        if "status" in data:
            fields.append("status = :status")
            params["status"] = data["status"]
        if "priority" in data:
            fields.append("priority = :priority")
            params["priority"] = data["priority"]
        if "progress" in data:
            fields.append("progress = :progress")
            params["progress"] = data["progress"]
        if "planned_start" in data:
            fields.append("planned_start = :planned_start")
            params["planned_start"] = data["planned_start"]
        if "planned_end" in data:
            fields.append("planned_end = :planned_end")
            params["planned_end"] = data["planned_end"]
        if "actual_start" in data:
            fields.append("actual_start = :actual_start")
            params["actual_start"] = data["actual_start"]
        if "actual_end" in data:
            fields.append("actual_end = :actual_end")
            params["actual_end"] = data["actual_end"]
        if "milestone_id" in data:
            fields.append("milestone_id = :milestone_id")
            params["milestone_id"] = data["milestone_id"]

        if not fields:
            return await self.get_by_id(task_id)

        fields.append("updated_at = NOW()")

        query = text(f"""
            UPDATE tasks
            SET {', '.join(fields)}
            WHERE id = :task_id
            RETURNING *
        """)

        result = await self.db.execute(query, params)
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def delete(self, task_id: str) -> bool:
        """删除任务"""
        from sqlalchemy import text

        query = text("""
            DELETE FROM tasks WHERE id = :task_id RETURNING id
        """)

        result = await self.db.execute(query, {"task_id": task_id})
        await self.db.commit()
        return result.fetchone() is not None

    async def count_by_paper(self, paper_id: str, status: Optional[str] = None) -> int:
        """统计任务数量"""
        from sqlalchemy import text

        if status:
            query = text("""
                SELECT COUNT(*) as count FROM tasks
                WHERE paper_id = :paper_id AND status = :status
            """)
            result = await self.db.execute(query, {"paper_id": paper_id, "status": status})
        else:
            query = text("""
                SELECT COUNT(*) as count FROM tasks WHERE paper_id = :paper_id
            """)
            result = await self.db.execute(query, {"paper_id": paper_id})

        row = result.fetchone()
        return row[0] if row else 0


class ProgressAlertRepository:
    """进度预警仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建预警"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO progress_alerts (
                id, paper_id, alert_type, severity, title, description,
                affected_items, suggestions, is_read, is_resolved, created_at
            ) VALUES (
                gen_random_uuid(), :paper_id, :alert_type, :severity, :title, :description,
                :affected_items, :suggestions, FALSE, FALSE, NOW()
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "paper_id": data["paper_id"],
            "alert_type": data["alert_type"],
            "severity": data["severity"],
            "title": data["title"],
            "description": data["description"],
            "affected_items": data.get("affected_items", []),
            "suggestions": data.get("suggestions", []),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_paper(
        self,
        paper_id: str,
        severity: Optional[str] = None,
        unread_only: bool = False
    ) -> List[dict]:
        """获取论文的所有预警"""
        from sqlalchemy import text

        conditions = ["paper_id = :paper_id"]
        params = {"paper_id": paper_id}

        if severity:
            conditions.append("severity = :severity")
            params["severity"] = severity
        if unread_only:
            conditions.append("is_read = FALSE")

        query = text(f"""
            SELECT * FROM progress_alerts
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
        """)

        result = await self.db.execute(query, params)
        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def get_by_id(self, alert_id: str) -> Optional[dict]:
        """根据ID获取预警"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM progress_alerts WHERE id = :alert_id
        """)

        result = await self.db.execute(query, {"alert_id": alert_id})
        row = result.fetchone()
        return dict(row) if row else None

    async def mark_as_read(self, alert_id: str) -> bool:
        """标记预警为已读"""
        from sqlalchemy import text

        query = text("""
            UPDATE progress_alerts
            SET is_read = TRUE
            WHERE id = :alert_id
            RETURNING id
        """)

        result = await self.db.execute(query, {"alert_id": alert_id})
        await self.db.commit()
        return result.fetchone() is not None

    async def mark_as_resolved(self, alert_id: str, resolution_note: str = "") -> bool:
        """标记预警为已解决"""
        from sqlalchemy import text

        query = text("""
            UPDATE progress_alerts
            SET is_resolved = TRUE, resolution_note = :resolution_note
            WHERE id = :alert_id
            RETURNING id
        """)

        result = await self.db.execute(query, {
            "alert_id": alert_id,
            "resolution_note": resolution_note
        })
        await self.db.commit()
        return result.fetchone() is not None

    async def count_unread(self, paper_id: str) -> int:
        """统计未读预警数量"""
        from sqlalchemy import text

        query = text("""
            SELECT COUNT(*) as count FROM progress_alerts
            WHERE paper_id = :paper_id AND is_read = FALSE
        """)

        result = await self.db.execute(query, {"paper_id": paper_id})
        row = result.fetchone()
        return row[0] if row else 0

    async def delete(self, alert_id: str) -> bool:
        """删除预警"""
        from sqlalchemy import text

        query = text("""
            DELETE FROM progress_alerts WHERE id = :alert_id RETURNING id
        """)

        result = await self.db.execute(query, {"alert_id": alert_id})
        await self.db.commit()
        return result.fetchone() is not None
