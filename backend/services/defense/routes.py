"""
答辩准备服务路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database import get_db
from core.auth import get_current_user
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
    current_user = Depends(get_current_user)
):
    """获取答辩检查清单"""
    repo = DefenseChecklistRepository(db)
    checklist = await repo.get_by_paper_id(paper_id)

    if not checklist:
        # 自动创建
        checklist = await repo.create(paper_id, current_user["id"])

    return {
        "id": checklist["id"],
        "paper_id": checklist["paper_id"],
        "items": checklist["items"] if isinstance(checklist["items"], list) else eval(checklist["items"]),
        "progress": calculate_progress(checklist["items"]),
        "created_at": checklist["created_at"],
        "updated_at": checklist["updated_at"],
    }


@router.put("/checklist/{checklist_id}")
async def update_checklist(
    checklist_id: str,
    request: ChecklistUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
):
    """获取PPT大纲"""
    repo = DefensePPTRepository(db)
    ppt = await repo.get_by_paper_id(paper_id)

    if not ppt:
        # 使用默认模板创建
        ppt = await repo.create(paper_id, current_user["id"], "academic")

    return {
        "id": ppt["id"],
        "paper_id": ppt["paper_id"],
        "template": ppt["template"],
        "outline": ppt["outline"] if isinstance(ppt["outline"], dict) else eval(ppt["outline"]),
        "status": ppt["status"],
        "created_at": ppt["created_at"],
        "updated_at": ppt["updated_at"],
    }


@router.post("/ppt/generate/{paper_id}")
async def generate_ppt_outline(
    paper_id: str,
    template: str = "academic",
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """基于论文内容生成PPT大纲"""
    repo = DefensePPTRepository(db)

    # 获取论文内容
    # TODO: 从论文服务获取内容
    paper_content = "论文内容..."

    # 使用LLM生成大纲
    llm = LLMClient()
    prompt = f"""
    基于以下论文内容，生成答辩PPT大纲：

    {paper_content}

    要求：
    1. 包含研究背景、方法、创新点、结果、结论
    2. 每页内容简洁，适合演讲
    3. 建议每页演讲时长

    输出JSON格式，包含slides数组。
    """

    # 生成大纲
    outline = {
        "title": "论文答辩",
        "slides": [
            {"id": "1", "type": "title", "title": "封面", "content": "", "order": 0},
            {"id": "2", "type": "content", "title": "研究背景", "content": "", "order": 1},
            {"id": "3", "type": "content", "title": "研究方法", "content": "", "order": 2},
            {"id": "4", "type": "content", "title": "创新点", "content": "", "order": 3},
            {"id": "5", "type": "content", "title": "研究结果", "content": "", "order": 4},
            {"id": "6", "type": "content", "title": "结论", "content": "", "order": 5},
            {"id": "7", "type": "thanks", "title": "致谢", "content": "", "order": 6},
        ]
    }

    # 保存
    ppt = await repo.create(paper_id, current_user["id"], template)
    await repo.update_outline(ppt["id"], outline)

    return {
        "id": ppt["id"],
        "outline": outline,
        "status": "generated",
    }


@router.put("/ppt/{ppt_id}")
async def update_ppt_outline(
    ppt_id: str,
    request: PPTUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
):
    """开始模拟答辩"""
    repo = DefenseMockRepository(db)
    session = await repo.create_session(paper_id, current_user["id"])

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
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
):
    """完成模拟答辩"""
    # TODO: 计算平均分
    total_score = 85.0

    repo = DefenseMockRepository(db)
    await repo.complete_session(session_id, total_score)

    return {
        "session_id": session_id,
        "total_score": total_score,
        "grade": "良好" if total_score >= 80 else "及格" if total_score >= 60 else "需改进",
        "suggestions": [
            "继续保持对研究内容的深入理解",
            "注意控制回答时间，简洁明了",
            "建议多准备几个具体案例",
        ],
    }


def calculate_progress(items) -> float:
    """计算完成进度"""
    if not items:
        return 0.0

    if isinstance(items, str):
        items = eval(items)

    completed = sum(1 for item in items if item.get("completed", False))
    return round(completed / len(items) * 100, 1)
