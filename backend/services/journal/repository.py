"""
期刊匹配服务数据仓库
Journal Repository Layer
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc


class JournalRepository:
    """期刊仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建期刊"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO journals (
                id, name, issn, eissn, publisher, subject_areas, language,
                impact_factor, h_index, sjr, review_cycle_days, acceptance_rate,
                publication_fee, is_open_access, apc, description, scope,
                submission_url, keywords, created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :name, :issn, :eissn, :publisher, :subject_areas, :language,
                :impact_factor, :h_index, :sjr, :review_cycle_days, :acceptance_rate,
                :publication_fee, :is_open_access, :apc, :description, :scope,
                :submission_url, :keywords, NOW(), NOW()
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "name": data["name"],
            "issn": data.get("issn"),
            "eissn": data.get("eissn"),
            "publisher": data.get("publisher"),
            "subject_areas": data.get("subject_areas", []),
            "language": data.get("language", "zh"),
            "impact_factor": data.get("impact_factor"),
            "h_index": data.get("h_index"),
            "sjr": data.get("sjr"),
            "review_cycle_days": data.get("review_cycle_days"),
            "acceptance_rate": data.get("acceptance_rate"),
            "publication_fee": data.get("publication_fee"),
            "is_open_access": data.get("is_open_access", False),
            "apc": data.get("apc"),
            "description": data.get("description"),
            "scope": data.get("scope"),
            "submission_url": data.get("submission_url"),
            "keywords": data.get("keywords", []),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_id(self, journal_id: str) -> Optional[dict]:
        """根据ID获取期刊"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM journals WHERE id = :journal_id
        """)

        result = await self.db.execute(query, {"journal_id": journal_id})
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_issn(self, issn: str) -> Optional[dict]:
        """根据ISSN获取期刊"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM journals WHERE issn = :issn OR eissn = :issn
        """)

        result = await self.db.execute(query, {"issn": issn})
        row = result.fetchone()
        return dict(row) if row else None

    async def list_journals(
        self,
        subject_area: Optional[str] = None,
        min_impact_factor: Optional[float] = None,
        max_impact_factor: Optional[float] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[dict]:
        """获取期刊列表"""
        from sqlalchemy import text

        conditions = []
        params = {"limit": limit, "offset": offset}

        if subject_area:
            conditions.append(":subject_area = ANY(subject_areas)")
            params["subject_area"] = subject_area

        if min_impact_factor is not None:
            conditions.append("impact_factor >= :min_impact_factor")
            params["min_impact_factor"] = min_impact_factor

        if max_impact_factor is not None:
            conditions.append("impact_factor <= :max_impact_factor")
            params["max_impact_factor"] = max_impact_factor

        if search:
            conditions.append("(name ILIKE :search OR :search = ANY(keywords))")
            params["search"] = f"%{search}%"

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = text(f"""
            SELECT * FROM journals
            {where_clause}
            ORDER BY impact_factor DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(query, params)
        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def count_journals(
        self,
        subject_area: Optional[str] = None,
        min_impact_factor: Optional[float] = None,
        max_impact_factor: Optional[float] = None,
        search: Optional[str] = None
    ) -> int:
        """统计期刊数量"""
        from sqlalchemy import text

        conditions = []
        params = {}

        if subject_area:
            conditions.append(":subject_area = ANY(subject_areas)")
            params["subject_area"] = subject_area

        if min_impact_factor is not None:
            conditions.append("impact_factor >= :min_impact_factor")
            params["min_impact_factor"] = min_impact_factor

        if max_impact_factor is not None:
            conditions.append("impact_factor <= :max_impact_factor")
            params["max_impact_factor"] = max_impact_factor

        if search:
            conditions.append("(name ILIKE :search OR :search = ANY(keywords))")
            params["search"] = f"%{search}%"

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = text(f"""
            SELECT COUNT(*) as count FROM journals
            {where_clause}
        """)

        result = await self.db.execute(query, params)
        row = result.fetchone()
        return row[0] if row else 0

    async def update(self, journal_id: str, data: dict) -> Optional[dict]:
        """更新期刊信息"""
        from sqlalchemy import text

        fields = []
        params = {"journal_id": journal_id}

        updatable_fields = [
            "name", "issn", "eissn", "publisher", "subject_areas", "language",
            "impact_factor", "h_index", "sjr", "review_cycle_days", "acceptance_rate",
            "publication_fee", "is_open_access", "apc", "description", "scope",
            "submission_url", "keywords"
        ]

        for field in updatable_fields:
            if field in data:
                fields.append(f"{field} = :{field}")
                params[field] = data[field]

        if not fields:
            return await self.get_by_id(journal_id)

        fields.append("updated_at = NOW()")

        query = text(f"""
            UPDATE journals
            SET {', '.join(fields)}
            WHERE id = :journal_id
            RETURNING *
        """)

        result = await self.db.execute(query, params)
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def delete(self, journal_id: str) -> bool:
        """删除期刊"""
        from sqlalchemy import text

        query = text("""
            DELETE FROM journals WHERE id = :journal_id RETURNING id
        """)

        result = await self.db.execute(query, {"journal_id": journal_id})
        await self.db.commit()
        return result.fetchone() is not None

    async def get_all_journals(self) -> List[dict]:
        """获取所有期刊（用于匹配算法）"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM journals ORDER BY impact_factor DESC NULLS LAST
        """)

        result = await self.db.execute(query)
        rows = result.fetchall()
        return [dict(row) for row in rows]


class SubmissionRepository:
    """投稿记录仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建投稿记录"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO submissions (
                id, paper_id, journal_id, manuscript_id, status,
                submitted_at, first_decision_at, revision_submitted_at,
                final_decision_at, decision, decision_letter, reviewers, notes
            ) VALUES (
                gen_random_uuid(), :paper_id, :journal_id, :manuscript_id, :status,
                :submitted_at, :first_decision_at, :revision_submitted_at,
                :final_decision_at, :decision, :decision_letter, :reviewers, :notes
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "paper_id": data["paper_id"],
            "journal_id": data["journal_id"],
            "manuscript_id": data.get("manuscript_id"),
            "status": data.get("status", "draft"),
            "submitted_at": data.get("submitted_at"),
            "first_decision_at": data.get("first_decision_at"),
            "revision_submitted_at": data.get("revision_submitted_at"),
            "final_decision_at": data.get("final_decision_at"),
            "decision": data.get("decision"),
            "decision_letter": data.get("decision_letter"),
            "reviewers": data.get("reviewers", []),
            "notes": data.get("notes"),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_id(self, submission_id: str) -> Optional[dict]:
        """根据ID获取投稿记录"""
        from sqlalchemy import text

        query = text("""
            SELECT s.*, j.name as journal_name
            FROM submissions s
            JOIN journals j ON s.journal_id = j.id
            WHERE s.id = :submission_id
        """)

        result = await self.db.execute(query, {"submission_id": submission_id})
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_paper(self, paper_id: str, status: Optional[str] = None) -> List[dict]:
        """获取论文的所有投稿记录"""
        from sqlalchemy import text

        if status:
            query = text("""
                SELECT s.*, j.name as journal_name
                FROM submissions s
                JOIN journals j ON s.journal_id = j.id
                WHERE s.paper_id = :paper_id AND s.status = :status
                ORDER BY s.submitted_at DESC
            """)
            result = await self.db.execute(query, {"paper_id": paper_id, "status": status})
        else:
            query = text("""
                SELECT s.*, j.name as journal_name
                FROM submissions s
                JOIN journals j ON s.journal_id = j.id
                WHERE s.paper_id = :paper_id
                ORDER BY s.submitted_at DESC
            """)
            result = await self.db.execute(query, {"paper_id": paper_id})

        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def get_by_user(self, user_id: str, status: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[dict]:
        """获取用户的所有投稿记录"""
        from sqlalchemy import text

        # 需要通过papers表关联获取用户ID
        if status:
            query = text("""
                SELECT s.*, j.name as journal_name, p.title as paper_title
                FROM submissions s
                JOIN journals j ON s.journal_id = j.id
                JOIN papers p ON s.paper_id = p.id
                WHERE p.owner_id = :user_id AND s.status = :status
                ORDER BY s.submitted_at DESC
                LIMIT :limit OFFSET :offset
            """)
            result = await self.db.execute(query, {
                "user_id": user_id,
                "status": status,
                "limit": limit,
                "offset": offset
            })
        else:
            query = text("""
                SELECT s.*, j.name as journal_name, p.title as paper_title
                FROM submissions s
                JOIN journals j ON s.journal_id = j.id
                JOIN papers p ON s.paper_id = p.id
                WHERE p.owner_id = :user_id
                ORDER BY s.submitted_at DESC
                LIMIT :limit OFFSET :offset
            """)
            result = await self.db.execute(query, {
                "user_id": user_id,
                "limit": limit,
                "offset": offset
            })

        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def update(self, submission_id: str, data: dict) -> Optional[dict]:
        """更新投稿记录"""
        from sqlalchemy import text

        fields = []
        params = {"submission_id": submission_id}

        updatable_fields = [
            "status", "manuscript_id", "submitted_at", "first_decision_at",
            "revision_submitted_at", "final_decision_at", "decision",
            "decision_letter", "reviewers", "notes"
        ]

        for field in updatable_fields:
            if field in data:
                fields.append(f"{field} = :{field}")
                params[field] = data[field]

        if not fields:
            return await self.get_by_id(submission_id)

        query = text(f"""
            UPDATE submissions
            SET {', '.join(fields)}
            WHERE id = :submission_id
            RETURNING *
        """)

        result = await self.db.execute(query, params)
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def delete(self, submission_id: str) -> bool:
        """删除投稿记录"""
        from sqlalchemy import text

        query = text("""
            DELETE FROM submissions WHERE id = :submission_id RETURNING id
        """)

        result = await self.db.execute(query, {"submission_id": submission_id})
        await self.db.commit()
        return result.fetchone() is not None

    async def count_by_user(self, user_id: str, status: Optional[str] = None) -> int:
        """统计用户的投稿记录数量"""
        from sqlalchemy import text

        if status:
            query = text("""
                SELECT COUNT(*) as count
                FROM submissions s
                JOIN papers p ON s.paper_id = p.id
                WHERE p.owner_id = :user_id AND s.status = :status
            """)
            result = await self.db.execute(query, {"user_id": user_id, "status": status})
        else:
            query = text("""
                SELECT COUNT(*) as count
                FROM submissions s
                JOIN papers p ON s.paper_id = p.id
                WHERE p.owner_id = :user_id
            """)
            result = await self.db.execute(query, {"user_id": user_id})

        row = result.fetchone()
        return row[0] if row else 0


class JournalMatchRepository:
    """期刊匹配历史仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建匹配记录"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO journal_matches (
                id, user_id, paper_id, journal_id, match_score,
                match_reasons, estimated_acceptance_rate, created_at
            ) VALUES (
                gen_random_uuid(), :user_id, :paper_id, :journal_id, :match_score,
                :match_reasons, :estimated_acceptance_rate, NOW()
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "user_id": data["user_id"],
            "paper_id": data["paper_id"],
            "journal_id": data["journal_id"],
            "match_score": data["match_score"],
            "match_reasons": data.get("match_reasons", []),
            "estimated_acceptance_rate": data.get("estimated_acceptance_rate"),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_user(self, user_id: str, paper_id: Optional[str] = None, limit: int = 20) -> List[dict]:
        """获取用户的匹配历史"""
        from sqlalchemy import text

        if paper_id:
            query = text("""
                SELECT m.*, j.name as journal_name
                FROM journal_matches m
                JOIN journals j ON m.journal_id = j.id
                WHERE m.user_id = :user_id AND m.paper_id = :paper_id
                ORDER BY m.created_at DESC
                LIMIT :limit
            """)
            result = await self.db.execute(query, {
                "user_id": user_id,
                "paper_id": paper_id,
                "limit": limit
            })
        else:
            query = text("""
                SELECT m.*, j.name as journal_name
                FROM journal_matches m
                JOIN journals j ON m.journal_id = j.id
                WHERE m.user_id = :user_id
                ORDER BY m.created_at DESC
                LIMIT :limit
            """)
            result = await self.db.execute(query, {"user_id": user_id, "limit": limit})

        rows = result.fetchall()
        return [dict(row) for row in rows]
