/"""
答辩准备数据访问层
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession


class DefenseChecklistRepository:
    """答辩检查清单数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, paper_id: str, user_id: str) -> Dict[str, Any]:
        """创建答辩检查清单"""
        checklist_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # 默认检查项
        default_items = [
            {"id": str(uuid.uuid4()), "category": "文档", "content": "论文终稿定稿并导师签字", "order": 1},
            {"id": str(uuid.uuid4()), "category": "文档", "content": "查重报告（符合学校要求）", "order": 2},
            {"id": str(uuid.uuid4()), "category": "文档", "content": "答辩申请表填写完整", "order": 3},
            {"id": str(uuid.uuid4()), "category": "文档", "content": "答辩决议书准备", "order": 4},
            {"id": str(uuid.uuid4()), "category": "PPT", "content": "答辩PPT初稿完成", "order": 5},
            {"id": str(uuid.uuid4()), "category": "PPT", "content": "PPT时长控制在规定范围内", "order": 6},
            {"id": str(uuid.uuid4()), "category": "PPT", "content": "PPT视觉效果优化", "order": 7},
            {"id": str(uuid.uuid4()), "category": "演练", "content": "完成自我陈述演练", "order": 8},
            {"id": str(uuid.uuid4()), "category": "演练", "content": "模拟问答3次以上", "order": 9},
            {"id": str(uuid.uuid4()), "category": "准备", "content": "熟悉答辩委员会成员研究方向", "order": 10},
            {"id": str(uuid.uuid4()), "category": "准备", "content": "准备纸笔记录问题", "order": 11},
            {"id": str(uuid.uuid4()), "category": "准备", "content": "准备论文副本供评委翻阅", "order": 12},
        ]

        query = text("""
            INSERT INTO defense_checklists (id, paper_id, user_id, items, created_at, updated_at)
            VALUES (:id, :paper_id, :user_id, :items, :created_at, :updated_at)
            RETURNING *
        """)

        result = await self.db.execute(query, {
            "id": checklist_id,
            "paper_id": paper_id,
            "user_id": user_id,
            "items": json.dumps(default_items),
            "created_at": now,
            "updated_at": now,
        })
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_by_paper_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """获取论文的答辩检查清单"""
        query = text("""
            SELECT * FROM defense_checklists
            WHERE paper_id = :paper_id
        """)
        result = await self.db.execute(query, {"paper_id": paper_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def update_items(self, checklist_id: str, items: List[Dict]) -> bool:
        """更新检查项"""
        query = text("""
            UPDATE defense_checklists
            SET items = :items, updated_at = :updated_at
            WHERE id = :id
            RETURNING id
        """)
        result = await self.db.execute(query, {
            "id": checklist_id,
            "items": json.dumps(items),
            "updated_at": datetime.utcnow(),
        })
        row = result.fetchone()
        await self.db.flush()
        return row is not None


class DefensePPTRepository:
    """答辩PPT数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, paper_id: str, user_id: str, template: str) -> Dict[str, Any]:
        """创建PPT大纲"""
        ppt_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # 默认大纲结构
        default_outline = {
            "title": "",
            "slides": [
                {"id": str(uuid.uuid4()), "type": "title", "title": "封面", "content": "", "order": 0},
                {"id": str(uuid.uuid4()), "type": "content", "title": "研究背景与意义", "content": "", "order": 1},
                {"id": str(uuid.uuid4()), "type": "content", "title": "国内外研究现状", "content": "", "order": 2},
                {"id": str(uuid.uuid4()), "type": "content", "title": "研究内容与方法", "content": "", "order": 3},
                {"id": str(uuid.uuid4()), "type": "content", "title": "主要创新点", "content": "", "order": 4},
                {"id": str(uuid.uuid4()), "type": "content", "title": "实验结果与分析", "content": "", "order": 5},
                {"id": str(uuid.uuid4()), "type": "content", "title": "结论与展望", "content": "", "order": 6},
                {"id": str(uuid.uuid4()), "type": "thanks", "title": "致谢", "content": "", "order": 7},
            ]
        }

        query = text("""
            INSERT INTO defense_ppts (id, paper_id, user_id, template, outline, status, created_at, updated_at)
            VALUES (:id, :paper_id, :user_id, :template, :outline, 'draft', :created_at, :updated_at)
            RETURNING *
        """)

        result = await self.db.execute(query, {
            "id": ppt_id,
            "paper_id": paper_id,
            "user_id": user_id,
            "template": template,
            "outline": json.dumps(default_outline),
            "created_at": now,
            "updated_at": now,
        })
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_by_paper_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """获取论文的PPT"""
        query = text("""
            SELECT * FROM defense_ppts
            WHERE paper_id = :paper_id
            ORDER BY created_at DESC
            LIMIT 1
        """)
        result = await self.db.execute(query, {"paper_id": paper_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    async def update_outline(self, ppt_id: str, outline: Dict) -> bool:
        """更新PPT大纲"""
        query = text("""
            UPDATE defense_ppts
            SET outline = :outline, updated_at = :updated_at
            WHERE id = :id
            RETURNING id
        """)
        result = await self.db.execute(query, {
            "id": ppt_id,
            "outline": json.dumps(outline),
            "updated_at": datetime.utcnow(),
        })
        row = result.fetchone()
        await self.db.flush()
        return row is not None


class DefenseQARepository:
    """答辩问答数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_question(self, question: str, answer: str, category: str,
                              difficulty: str = "medium", paper_id: str = None) -> Dict[str, Any]:
        """创建问答条目"""
        qa_id = str(uuid.uuid4())

        query = text("""
            INSERT INTO defense_qa (id, paper_id, question, answer, category, difficulty, created_at)
            VALUES (:id, :paper_id, :question, :answer, :category, :difficulty, :created_at)
            RETURNING *
        """)

        result = await self.db.execute(query, {
            "id": qa_id,
            "paper_id": paper_id,
            "question": question,
            "answer": answer,
            "category": category,
            "difficulty": difficulty,
            "created_at": datetime.utcnow(),
        })
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def get_questions(self, paper_id: str = None, category: str = None,
                           difficulty: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """获取问答列表"""
        conditions = ["1=1"]
        params = {}

        if paper_id:
            conditions.append("(paper_id = :paper_id OR paper_id IS NULL)")
            params["paper_id"] = paper_id
        if category:
            conditions.append("category = :category")
            params["category"] = category
        if difficulty:
            conditions.append("difficulty = :difficulty")
            params["difficulty"] = difficulty

        where_clause = " AND ".join(conditions)

        query = text(f"""
            SELECT * FROM defense_qa
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        params["limit"] = limit
        result = await self.db.execute(query, params)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]


class DefenseMockRepository:
    """模拟答辩数据仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, paper_id: str, user_id: str) -> Dict[str, Any]:
        """创建模拟答辩会话"""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        query = text("""
            INSERT INTO defense_mock_sessions (id, paper_id, user_id, status, created_at)
            VALUES (:id, :paper_id, :user_id, 'ongoing', :created_at)
            RETURNING *
        """)

        result = await self.db.execute(query, {
            "id": session_id,
            "paper_id": paper_id,
            "user_id": user_id,
            "created_at": now,
        })
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def add_answer(self, session_id: str, question_id: str,
                        question: str, answer: str, score: int, feedback: str) -> Dict[str, Any]:
        """添加回答记录"""
        answer_id = str(uuid.uuid4())

        query = text("""
            INSERT INTO defense_mock_answers
            (id, session_id, question_id, question, answer, score, feedback, created_at)
            VALUES (:id, :session_id, :question_id, :question, :answer, :score, :feedback, :created_at)
            RETURNING *
        """)

        result = await self.db.execute(query, {
            "id": answer_id,
            "session_id": session_id,
            "question_id": question_id,
            "question": question,
            "answer": answer,
            "score": score,
            "feedback": feedback,
            "created_at": datetime.utcnow(),
        })
        row = result.fetchone()
        await self.db.flush()

        return dict(row._mapping) if row else None

    async def complete_session(self, session_id: str, total_score: float) -> bool:
        """完成模拟答辩"""
        query = text("""
            UPDATE defense_mock_sessions
            SET status = 'completed', total_score = :total_score, completed_at = :completed_at
            WHERE id = :id
            RETURNING id
        """)
        result = await self.db.execute(query, {
            "id": session_id,
            "total_score": total_score,
            "completed_at": datetime.utcnow(),
        })
        row = result.fetchone()
        await self.db.flush()
        return row is not None


import json
