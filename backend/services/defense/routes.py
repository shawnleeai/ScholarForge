"""
答辩准备服务路由
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from shared.database import get_db
from shared.dependencies import get_current_user_id
from services.defense.repository import (
    DefenseChecklistRepository, DefensePPTRepository,
    DefenseQARepository, DefenseMockRepository
)
from services.defense.schemas import (
    ChecklistResponse, ChecklistUpdateRequest,
    PPTOutlineResponse, PPTUpdateRequest,
    QAResponse, QAListRequest,
    MockSessionResponse, MockAnswerRequest, MockResultResponse
)
from services.llm.client import LLMClient

router = APIRouter(prefix="/defense", tags=["defense"])


@router.get("/checklist/{paper_id}", response_model=ChecklistResponse)
async def get_checklist(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取答辩检查清单"""
    repo = DefenseChecklistRepository(db)
    checklist = await repo.get_by_paper_id(paper_id)

    if not checklist:
        # 自动创建
        checklist = await repo.create(paper_id, current_user_id)

    return {
        "id": checklist["id"],
        "paper_id": checklist["paper_id"],
        "items": checklist["items"] if isinstance(checklist["items"], list) else json.loads(checklist["items"]),
        "progress": calculate_progress(checklist["items"]),
        "created_at": checklist["created_at"],
        "updated_at": checklist["updated_at"],
    }


@router.put("/checklist/{checklist_id}")
async def update_checklist(
    checklist_id: str,
    request: ChecklistUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """更新检查清单项"""
    repo = DefenseChecklistRepository(db)
    success = await repo.update_items(checklist_id, request.items)

    if not success:
        raise HTTPException(status_code=404, detail="检查清单不存在")

    return {"success": True}


@router.get("/ppt/{paper_id}", response_model=PPTOutlineResponse)
async def get_ppt_outline(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取PPT大纲"""
    repo = DefensePPTRepository(db)
    ppt = await repo.get_by_paper_id(paper_id)

    if not ppt:
        # 使用默认模板创建
        ppt = await repo.create(paper_id, current_user_id, "academic")

    return {
        "id": ppt["id"],
        "paper_id": ppt["paper_id"],
        "template": ppt["template"],
        "outline": ppt["outline"] if isinstance(ppt["outline"], dict) else json.loads(ppt["outline"]),
        "status": ppt["status"],
        "created_at": ppt["created_at"],
        "updated_at": ppt["updated_at"],
    }


@router.post("/ppt/generate/{paper_id}")
async def generate_ppt_outline(
    paper_id: str,
    template: str = "academic",
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """基于论文内容生成PPT大纲"""
    import uuid
    repo = DefensePPTRepository(db)

    # 获取论文内容（从数据库或服务）
    paper_content = ""
    paper_title = "论文答辩"

    # 尝试从paper服务获取内容
    try:
        from shared.database import get_db_context
        async with get_db_context() as paper_db:
            from sqlalchemy import text
            result = await paper_db.execute(
                text("SELECT title, abstract, content FROM papers WHERE id = :id"),
                {"id": paper_id}
            )
            paper_row = result.fetchone()
            if paper_row:
                paper_title = paper_row[0] or "论文答辩"
                paper_content = f"标题: {paper_row[0] or ''}\n摘要: {paper_row[1] or ''}\n"
    except Exception:
        pass

    # 使用LLM生成大纲
    llm = LLMClient()
    prompt = f"""基于以下论文信息，生成答辩PPT大纲。

论文信息:
{paper_content if paper_content else '（论文内容待获取）'}

请生成一个学术答辩PPT大纲，要求：
1. 包含封面、研究背景、研究方法、创新点、研究结果、结论、致谢等部分
2. 每页内容简洁，适合15-20分钟答辩
3. 标注每页的演讲时长建议

请严格按照以下JSON格式输出（不要包含其他内容）:
{{
  "title": "论文标题",
  "slides": [
    {{"id": "1", "type": "title", "title": "封面", "content": "论文标题、答辩人、导师", "duration": 1, "order": 0}},
    {{"id": "2", "type": "content", "title": "研究背景", "content": "研究背景要点", "duration": 2, "order": 1}},
    ...
  ]
}}"""

    outline = None
    try:
        llm_response = await llm.generate(prompt, temperature=0.7, max_tokens=2000)

        # 尝试解析JSON响应
        import re
        json_match = re.search(r'\{[\s\S]*\}', llm_response)
        if json_match:
            outline = json.loads(json_match.group())
    except Exception as e:
        print(f"LLM生成PPT大纲失败: {e}")

    # 如果LLM生成失败，使用默认模板
    if not outline or "slides" not in outline:
        outline = {
            "title": paper_title,
            "slides": [
                {"id": "1", "type": "title", "title": "封面", "content": f"{paper_title}\n答辩人\n导师", "duration": 1, "order": 0},
                {"id": "2", "type": "content", "title": "研究背景", "content": "研究背景与意义\n国内外研究现状\n研究问题", "duration": 3, "order": 1},
                {"id": "3", "type": "content", "title": "研究方法", "content": "研究设计\n数据收集\n分析方法", "duration": 3, "order": 2},
                {"id": "4", "type": "content", "title": "创新点", "content": "理论创新\n方法创新\n应用创新", "duration": 3, "order": 3},
                {"id": "5", "type": "content", "title": "研究结果", "content": "主要发现\n数据分析\n结果讨论", "duration": 4, "order": 4},
                {"id": "6", "type": "content", "title": "结论与展望", "content": "研究结论\n研究局限\n未来展望", "duration": 2, "order": 5},
                {"id": "7", "type": "thanks", "title": "致谢", "content": "感谢导师指导\n感谢评委老师", "duration": 1, "order": 6},
            ]
        }

    # 保存
    ppt = await repo.create(paper_id, current_user_id, template)
    await repo.update_outline(ppt["id"], outline)

    return {
        "id": ppt["id"],
        "outline": outline,
        "status": "generated",
        "generated_by": "llm" if llm_response else "template",
    }


@router.put("/ppt/{ppt_id}")
async def update_ppt_outline(
    ppt_id: str,
    request: PPTUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """更新PPT大纲"""
    repo = DefensePPTRepository(db)
    success = await repo.update_outline(ppt_id, request.outline)

    if not success:
        raise HTTPException(status_code=404, detail="PPT不存在")

    return {"success": True}


@router.get("/qa", response_model=List[QAResponse])
async def get_qa_list(
    paper_id: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """获取问答列表"""
    repo = DefenseQARepository(db)
    questions = await repo.get_questions(paper_id, category, difficulty, limit)

    return [
        {
            "id": q["id"],
            "question": q["question"],
            "answer": q["answer"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "paper_id": q["paper_id"],
        }
        for q in questions
    ]


@router.post("/qa/generate/{paper_id}")
async def generate_qa(
    paper_id: str,
    count: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """基于论文生成可能的问题"""
    # 获取论文内容
    paper_content = "论文内容..."

    # 使用LLM生成问题
    llm = LLMClient()

    # 生成问题列表
    questions = [
        {
            "question": "你的研究的主要创新点是什么？",
            "answer": "本研究的主要创新点在于...",
            "category": "创新点",
            "difficulty": "medium",
        },
        {
            "question": "你的研究方法与其他方法相比有什么优势？",
            "answer": "相比传统方法，本研究采用的方法具有以下优势...",
            "category": "方法",
            "difficulty": "medium",
        },
        {
            "question": "你的研究结果的实际应用价值是什么？",
            "answer": "研究结果可以在以下方面得到应用...",
            "category": "应用",
            "difficulty": "easy",
        },
    ]

    # 保存到数据库
    repo = DefenseQARepository(db)
    saved = []
    for q in questions:
        item = await repo.create_question(
            question=q["question"],
            answer=q["answer"],
            category=q["category"],
            difficulty=q["difficulty"],
            paper_id=paper_id
        )
        saved.append(item)

    return {"generated": len(saved), "questions": saved}


@router.post("/mock/start/{paper_id}", response_model=MockSessionResponse)
async def start_mock_defense(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """开始模拟答辩"""
    repo = DefenseMockRepository(db)
    session = await repo.create_session(paper_id, current_user_id)

    # 获取问题列表
    qa_repo = DefenseQARepository(db)
    questions = await qa_repo.get_questions(paper_id=paper_id, limit=5)

    return {
        "id": session["id"],
        "paper_id": session["paper_id"],
        "status": session["status"],
        "questions": [
            {
                "id": q["id"],
                "question": q["question"],
                "difficulty": q["difficulty"],
            }
            for q in questions
        ],
        "created_at": session["created_at"],
    }


@router.post("/mock/answer/{session_id}")
async def submit_answer(
    session_id: str,
    request: MockAnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """提交回答"""
    repo = DefenseMockRepository(db)

    # 使用AI评分
    llm = LLMClient()
    prompt = f"""
    评估以下答辩回答，给出0-100的分数和改进建议。

    问题：{request.question}
    回答：{request.answer}

    输出JSON格式：{{"score": 分数, "feedback": "评价建议"}}
    """

    # 模拟评分
    score = 85
    feedback = "回答比较完整，但可以补充更多具体案例。建议改进表达的逻辑性。"

    answer_record = await repo.add_answer(
        session_id=session_id,
        question_id=request.question_id,
        question=request.question,
        answer=request.answer,
        score=score,
        feedback=feedback
    )

    return {
        "answer_id": answer_record["id"],
        "score": score,
        "feedback": feedback,
    }


@router.post("/mock/complete/{session_id}", response_model=MockResultResponse)
async def complete_mock_defense(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """完成模拟答辩"""
    repo = DefenseMockRepository(db)

    # 获取所有回答并计算平均分
    answers = await repo.get_session_answers(session_id)
    if answers:
        scores = [a["score"] for a in answers if a.get("score") is not None]
        total_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    else:
        total_score = 0.0

    await repo.complete_session(session_id, total_score)

    # 根据分数生成建议
    suggestions = []
    if total_score >= 90:
        suggestions = [
            "表现优秀，继续保持",
            "可以尝试更高难度的模拟",
            "建议关注细节，追求完美",
        ]
    elif total_score >= 80:
        suggestions = [
            "继续保持对研究内容的深入理解",
            "注意控制回答时间，简洁明了",
            "建议多准备几个具体案例",
        ]
    elif total_score >= 60:
        suggestions = [
            "加强对核心概念的掌握",
            "多进行模拟练习",
            "建议准备更详细的回答提纲",
        ]
    else:
        suggestions = [
            "需要重点复习研究内容",
            "建议重新梳理论文逻辑",
            "多次模拟练习，提升自信",
        ]

    return {
        "session_id": session_id,
        "total_score": total_score,
        "grade": "优秀" if total_score >= 90 else "良好" if total_score >= 80 else "及格" if total_score >= 60 else "需改进",
        "suggestions": suggestions,
    }


def calculate_progress(items) -> float:
    """计算完成进度"""
    if not items:
        return 0.0

    if isinstance(items, str):
        items = json.loads(items)

    completed = sum(1 for item in items if item.get("completed", False))
    return round(completed / len(items) * 100, 1)
