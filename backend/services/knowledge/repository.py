"""
知识图谱数据仓库
Knowledge Graph Repository Layer
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class GraphRepository:
    """知识图谱仓库（PostgreSQL 存储图谱元数据）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_graph(self, data: dict) -> dict:
        """创建图谱记录"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO knowledge_graphs (
                id, user_id, paper_id, name, description,
                node_count, edge_count, neo4j_graph_id, settings, created_at
            ) VALUES (
                gen_random_uuid(), :user_id, :paper_id, :name, :description,
                :node_count, :edge_count, :neo4j_graph_id, :settings, NOW()
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "user_id": data["user_id"],
            "paper_id": data.get("paper_id"),
            "name": data["name"],
            "description": data.get("description", ""),
            "node_count": data.get("node_count", 0),
            "edge_count": data.get("edge_count", 0),
            "neo4j_graph_id": data.get("neo4j_graph_id"),
            "settings": data.get("settings", {}),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_id(self, graph_id: str, user_id: str) -> Optional[dict]:
        """根据ID获取图谱"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM knowledge_graphs
            WHERE id = :graph_id AND user_id = :user_id
        """)

        result = await self.db.execute(query, {
            "graph_id": graph_id,
            "user_id": user_id
        })
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> List[dict]:
        """获取用户的所有图谱"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM knowledge_graphs
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

    async def delete(self, graph_id: str, user_id: str) -> bool:
        """删除图谱"""
        from sqlalchemy import text

        query = text("""
            DELETE FROM knowledge_graphs
            WHERE id = :graph_id AND user_id = :user_id
            RETURNING id
        """)

        result = await self.db.execute(query, {
            "graph_id": graph_id,
            "user_id": user_id
        })
        await self.db.commit()
        return result.fetchone() is not None


class ConceptRepository:
    """概念实体仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建概念实体"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO concepts (
                id, name, concept_type, description,
                keywords, frequency, importance, properties
            ) VALUES (
                gen_random_uuid(), :name, :concept_type, :description,
                :keywords, :frequency, :importance, :properties
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "name": data["name"],
            "concept_type": data.get("concept_type", "concept"),
            "description": data.get("description", ""),
            "keywords": data.get("keywords", []),
            "frequency": data.get("frequency", 1),
            "importance": data.get("importance", 0.5),
            "properties": data.get("properties", {}),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_name(self, name: str) -> Optional[dict]:
        """根据名称获取概念"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM concepts WHERE name = :name
        """)

        result = await self.db.execute(query, {"name": name})
        row = result.fetchone()
        return dict(row) if row else None

    async def search(self, query_str: str, limit: int = 10) -> List[dict]:
        """搜索概念"""
        from sqlalchemy import text

        query = text("""
            SELECT * FROM concepts
            WHERE name ILIKE :query OR :query = ANY(keywords)
            ORDER BY importance DESC, frequency DESC
            LIMIT :limit
        """)

        result = await self.db.execute(query, {
            "query": f"%{query_str}%",
            "limit": limit
        })
        rows = result.fetchall()
        return [dict(row) for row in rows]


class ConceptRelationRepository:
    """概念关系仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """创建概念关系"""
        from sqlalchemy import text

        query = text("""
            INSERT INTO concept_relations (
                id, source_concept_id, target_concept_id,
                relation_type, weight, evidence
            ) VALUES (
                gen_random_uuid(), :source_concept_id, :target_concept_id,
                :relation_type, :weight, :evidence
            ) RETURNING *
        """)

        result = await self.db.execute(query, {
            "source_concept_id": data["source_concept_id"],
            "target_concept_id": data["target_concept_id"],
            "relation_type": data["relation_type"],
            "weight": data.get("weight", 1.0),
            "evidence": data.get("evidence", []),
        })
        await self.db.commit()
        row = result.fetchone()
        return dict(row) if row else None

    async def get_by_concept(self, concept_id: str) -> List[dict]:
        """获取概念的所有关系"""
        from sqlalchemy import text

        query = text("""
            SELECT r.*, sc.name as source_name, tc.name as target_name
            FROM concept_relations r
            JOIN concepts sc ON r.source_concept_id = sc.id
            JOIN concepts tc ON r.target_concept_id = tc.id
            WHERE r.source_concept_id = :concept_id OR r.target_concept_id = :concept_id
        """)

        result = await self.db.execute(query, {"concept_id": concept_id})
        rows = result.fetchall()
        return [dict(row) for row in rows]
