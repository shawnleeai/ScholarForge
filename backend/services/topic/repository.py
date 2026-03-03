"""
选题助手数据仓库
Topic Repository Layer
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from shared.database import get_db


class TopicSuggestionRepository:
    """选题建议仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建选题建议"""
        # 使用raw query因为表可能还未创建
        from sqlalchemy import text

        query = text("""
            INSERT INTO topic_suggestions (
                id, user_id, title, description, field, keywords,
                feasibility_score, feasibility_level, is_favorite, created_at
            ) VALUES (
                gen_random_uuid(), :user_id, :title, :description, :field, :keywords,
                :feasibility_score, :feasibility_level, :is_favorite, NOW()
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "user_id": data["user_id"],
            "title": data["title"],
            "description": data.get("description", ""),
            "field": data.get("field", ""),
            "keywords": data.get("keywords", []),
            "feasibility_score": data.get("feasibility_score", 70),
            "feasibility_level": data.get("feasibility_level", "medium"),
            "is_favorite": data.get("is_favorite", False),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_id(self, topic_id: str, user_id: str) -> Optional[dict]:
        """根据ID获取选题建议"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM topic_suggestions
            WHERE id = :topic_id AND user_id = :user_id
        """)

        result = await self.db.execute(query, {
            "topic_id": topic_id,
            "user_id": user_id
        })
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[dict]:
        """获取用户的所有选题建议"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM topic_suggestions
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(query, {
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        })
        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def get_favorites(self, user_id: str, limit: int = 50, offset: int = 0) -> List[dict]:
        """获取用户收藏的选题"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM topic_suggestions
            WHERE user_id = :user_id AND is_favorite = TRUE
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(query, {
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        })
        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def update(self, topic_id: str, user_id: str, data: dict) -> Optional[dict]:
        """更新选题建议"""
        from sqlalchemy import text

        # 构建动态更新语句
        fields = []
        params = {"topic_id": topic_id, "user_id": user_id}

        if "title" in data:
            fields.append("title = :title")
            params["title"] = data["title"]
        if "description" in data:
            fields.append("description = :description")
            params["description"] = data["description"]
        if "is_favorite" in data:
            fields.append("is_favorite = :is_favorite")
            params["is_favorite"] = data["is_favorite"]
        if "feasibility_score" in data:
            fields.append("feasibility_score = :feasibility_score")
            params["feasibility_score"] = data["feasibility_score"]

        if not fields:
            return await self.get_by_id(topic_id, user_id)

        query = text(f"""
            UPDATE topic_suggestions
            SET {', '.join(fields)}
            WHERE id = :topic_id AND user_id = :user_id
            RETURNING *
        """)

        result = await self.db.execute(query, params)
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def delete(self, topic_id: str, user_id: str) -> bool:
        """删除选题建议"""
        from sqlalchemy import text

        query = text("""
            DELETE FROM topic_suggestions
            WHERE id = :topic_id AND user_id = :user_id
            RETURNING id
        """)

        result = await self.db.execute(query, {
            "topic_id": topic_id,
            "user_id": user_id
        })
        await self.db.commit()
        return result.fetchone() is not None

    async def count_by_user(self, user_id: str) -> int:
        """统计用户的选题数量"""
        from sqlalchemy import text

        query = text("""
            SELECT COUNT(*) as count FROM topic_suggestions
            WHERE user_id = :user_id
        """)

        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()
        return row[0] if row else 0


class ProposalOutlineRepository:
    """开题报告仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建开题报告"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO proposal_outlines (
                id, user_id, topic_id, title, background, objectives,
                methods, timeline, references, total_words, generated_at
            ) VALUES (
                gen_random_uuid(), :user_id, :topic_id, :title, :background,
                :objectives, :methods::jsonb, :timeline::jsonb, :references, :total_words, NOW()
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "user_id": data["user_id"],
            "topic_id": data.get("topic_id"),
            "title": data["title"],
            "background": data.get("background", ""),
            "objectives": data.get("objectives", ""),
            "methods": data.get("methods", []),
            "timeline": data.get("timeline", []),
            "references": data.get("references", []),
            "total_words": data.get("total_words", 0),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_id(self, proposal_id: str, user_id: str) -> Optional[dict]:
        """根据ID获取开题报告"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM proposal_outlines
            WHERE id = :proposal_id AND user_id = :user_id
        """)

        result = await self.db.execute(query, {
            "proposal_id": proposal_id,
            "user_id": user_id
        })
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_topic(self, topic_id: str, user_id: str) -> Optional[dict]:
        """根据选题ID获取开题报告"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM proposal_outlines
            WHERE topic_id = :topic_id AND user_id = :user_id
            ORDER BY generated_at DESC
            LIMIT 1
        """)

        result = await self.db.execute(query, {
            "topic_id": topic_id,
            "user_id": user_id
        })
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
        """获取用户的所有开题报告"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM proposal_outlines
            WHERE user_id = :user_id
            ORDER BY generated_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(query, {
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        })
        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def delete(self, proposal_id: str, user_id: str) -> bool:
        """删除开题报告"""
        from sqlalchemy import text

        query = text("""
            DELETE FROM proposal_outlines
            WHERE id = :proposal_id AND user_id = :user_id
            RETURNING id
        """)

        result = await self.db.execute(query, {
            "proposal_id": proposal_id,
            "user_id": user_id
        })
        await self.db.commit()
        return result.fetchone() is not None
