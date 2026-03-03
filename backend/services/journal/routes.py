"""
期刊匹配服务 API 路由
FastAPI 路由定义
"""

import uuid
from datetime import datetime
from typing import Optional, List
import time

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.responses import success_response, paginated_response
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams

from .schemas import (
    MatchRequest,
    MatchResult,
    MatchResponse,
    MatchStatus,
    JournalBase,
    JournalDetail,
    JournalFilter,
    JournalType,
    JournalRanking,
    SubmissionRecord,
    SubmissionRecordCreate,
    SubmissionRecordUpdate,
    SubmissionSuggestion,
    JournalStats,
)
from .matcher import JournalMatcher, PaperInfo
from .repository import JournalRepository, SubmissionRepository, JournalMatchRepository

router = APIRouter(prefix="/api/v1/journals", tags=["期刊匹配"])
submission_router = APIRouter(prefix="/api/v1/submissions", tags=["投稿记录"])


# ============== 期刊匹配 ==============

@router.post("/match", summary="匹配期刊")
async def match_journals(
    request: MatchRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    基于论文内容智能匹配期刊

    分析论文标题、摘要、关键词等，推荐最适合的投稿期刊
    """
    start_time = time.time()

    # 构建论文信息
    paper = PaperInfo(
        title=request.title or "",
        abstract=request.abstract or "",
        keywords=request.keywords or [],
        field=request.field or "",
    )

    # 从数据库获取期刊列表
    journal_repo = JournalRepository(db)
    journals_data = await journal_repo.get_all_journals()

    if not journals_data:
        # 如果数据库为空，初始化示例数据
        journals_data = await _init_sample_journals(db)

    # 执行匹配
    matcher = JournalMatcher(journals_data)
    results = matcher.match(paper, top_n=10, min_score=20.0)

    # 保存匹配历史
    match_repo = JournalMatchRepository(db)

    # 构建响应
    match_results = []
    for journal, score, reasons in results:
        # 查找期刊ID
        journal_id = None
        for jd in journals_data:
            if jd.get("name") == journal.name:
                journal_id = str(jd.get("id"))
                break

        # 保存匹配记录
        if journal_id:
            await match_repo.create({
                "user_id": user_id,
                "paper_id": str(request.paper_id),
                "journal_id": journal_id,
                "match_score": round(score, 1),
                "match_reasons": reasons,
                "estimated_acceptance_rate": matcher.estimate_acceptance_probability(paper, journal, score),
            })

        match_results.append(
            MatchResult(
                journal=JournalBase(
                    id=journal_id or journal.id,
                    name=journal.name,
                    subject_areas=journal.subject_areas,
                    impact_factor=journal.impact_factor,
                    acceptance_rate=journal.acceptance_rate,
                ),
                match_score=round(score, 1),
                match_reasons=reasons,
                recommendations=_generate_recommendations(journal, score),
                estimated_acceptance_rate=matcher.estimate_acceptance_probability(paper, journal, score),
                estimated_review_time=journal.review_cycle_days or 90,
            )
        )

    processing_time = (time.time() - start_time) * 1000

    return success_response(
        data=MatchResponse(
            match_id=str(uuid.uuid4()),
            status=MatchStatus.COMPLETED,
            results=match_results,
            total_journals_analyzed=len(journals_data),
            processing_time_ms=processing_time,
            created_at=datetime.now(),
        ).model_dump(),
        message="期刊匹配完成",
    )


def _generate_recommendations(journal, score: float) -> List[str]:
    """生成投稿建议"""
    recommendations = []

    if score >= 80:
        recommendations.append("强烈推荐投稿，匹配度很高")
    elif score >= 60:
        recommendations.append("推荐投稿，匹配度较好")
    else:
        recommendations.append("可以考虑投稿，但匹配度一般")

    if journal.impact_factor and journal.impact_factor >= 5:
        recommendations.append("高影响力期刊，建议确保论文质量")
    elif journal.impact_factor and journal.impact_factor < 2:
        recommendations.append("影响力较低，适合首次投稿或时间紧迫时选择")

    if journal.acceptance_rate and journal.acceptance_rate < 0.15:
        recommendations.append("录用率较低，竞争激烈，建议做好多手准备")
    elif journal.acceptance_rate and journal.acceptance_rate > 0.3:
        recommendations.append("录用率相对较高，适合稳妥选择")

    return recommendations


async def _init_sample_journals(db: AsyncSession) -> List[dict]:
    """初始化示例期刊数据"""
    from sqlalchemy import text

    sample_journals = [
        {
            "name": "管理世界",
            "subject_areas": ["管理学", "经济学"],
            "keywords": ["管理", "战略", "创新", "组织"],
            "impact_factor": 5.2,
            "acceptance_rate": 0.15,
            "scope": "管理学领域顶级期刊",
            "language": "zh",
            "review_cycle_days": 60,
        },
        {
            "name": "系统工程理论与实践",
            "subject_areas": ["系统工程", "管理科学"],
            "keywords": ["系统", "优化", "决策", "工程管理"],
            "impact_factor": 3.5,
            "acceptance_rate": 0.20,
            "scope": "系统工程领域核心期刊",
            "language": "zh",
            "review_cycle_days": 45,
        },
        {
            "name": "科研管理",
            "subject_areas": ["管理学", "科技管理"],
            "keywords": ["研发", "创新", "科技政策", "知识管理"],
            "impact_factor": 2.8,
            "acceptance_rate": 0.25,
            "scope": "科研管理领域专业期刊",
            "language": "zh",
            "review_cycle_days": 50,
        },
        {
            "name": "IEEE Transactions on Engineering Management",
            "subject_areas": ["工程管理", "项目管理"],
            "keywords": ["engineering", "management", "project", "technology"],
            "impact_factor": 8.5,
            "acceptance_rate": 0.10,
            "scope": "工程管理领域顶级国际期刊",
            "language": "en",
            "review_cycle_days": 90,
        },
        {
            "name": "Journal of Management",
            "subject_areas": ["管理学"],
            "keywords": ["management", "organization", "strategy", "leadership"],
            "impact_factor": 13.0,
            "acceptance_rate": 0.05,
            "scope": "管理学顶级国际期刊",
            "language": "en",
            "review_cycle_days": 120,
        },
        {
            "name": "项目管理技术",
            "subject_areas": ["项目管理"],
            "keywords": ["项目", "管理", "进度", "成本", "质量"],
            "impact_factor": 1.2,
            "acceptance_rate": 0.40,
            "scope": "项目管理专业期刊",
            "language": "zh",
            "review_cycle_days": 30,
        },
        {
            "name": "计算机学报",
            "subject_areas": ["计算机科学"],
            "keywords": ["计算机", "算法", "软件", "系统"],
            "impact_factor": 3.0,
            "acceptance_rate": 0.18,
            "scope": "计算机领域顶级中文期刊",
            "language": "zh",
            "review_cycle_days": 60,
        },
        {
            "name": "Journal of Construction Engineering and Management",
            "subject_areas": ["建筑工程", "工程管理"],
            "keywords": ["construction", "engineering", "project", "building"],
            "impact_factor": 4.5,
            "acceptance_rate": 0.20,
            "scope": "建筑工程管理领域国际期刊",
            "language": "en",
            "review_cycle_days": 75,
        },
        {
            "name": "管理科学学报",
            "subject_areas": ["管理科学", "运筹学"],
            "keywords": ["管理科学", "运筹学", "决策", "优化"],
            "impact_factor": 2.5,
            "acceptance_rate": 0.22,
            "scope": "管理科学领域核心期刊",
            "language": "zh",
            "review_cycle_days": 55,
        },
        {
            "name": "中国管理科学",
            "subject_areas": ["管理科学", "管理学"],
            "keywords": ["管理", "决策", "系统", "优化"],
            "impact_factor": 2.2,
            "acceptance_rate": 0.28,
            "scope": "中国管理科学领域重要期刊",
            "language": "zh",
            "review_cycle_days": 50,
        },
    ]

    journal_repo = JournalRepository(db)
    created_journals = []

    for journal_data in sample_journals:
        created = await journal_repo.create(journal_data)
        if created:
            created_journals.append(created)

    return created_journals


@router.post("/match/{paper_id}", summary="基于论文ID匹配期刊")
async def match_by_paper_id(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    根据论文ID自动获取论文信息并匹配期刊
    """
    # TODO: 从论文服务获取论文详情
    # 这里使用模拟数据
    paper = PaperInfo(
        title="AI协同项目管理在学术论文辅助工具开发中的应用研究",
        abstract="本研究探讨了人工智能技术如何提升学术论文写作效率...",
        keywords=["AI", "项目管理", "学术论文", "协同"],
        field="工程管理",
    )

    # 从数据库获取期刊列表
    journal_repo = JournalRepository(db)
    journals_data = await journal_repo.get_all_journals()

    if not journals_data:
        journals_data = await _init_sample_journals(db)

    matcher = JournalMatcher(journals_data)
    results = matcher.match(paper, top_n=5)

    match_results = [
        MatchResult(
            journal=JournalBase(
                id=journal.id,
                name=journal.name,
                subject_areas=journal.subject_areas,
                impact_factor=journal.impact_factor,
                acceptance_rate=journal.acceptance_rate,
            ),
            match_score=round(score, 1),
            match_reasons=reasons,
            recommendations=_generate_recommendations(journal, score),
        )
        for journal, score, reasons in results
    ]

    return success_response(
        data={
            "paper_id": paper_id,
            "results": [r.model_dump() for r in match_results],
        }
    )


# ============== 期刊查询 ==============

@router.get("", summary="获取期刊列表")
async def get_journals(
    subject_area: Optional[str] = Query(None, description="学科领域"),
    journal_type: Optional[JournalType] = Query(None, description="期刊类型"),
    ranking: Optional[JournalRanking] = Query(None, description="期刊等级"),
    min_impact_factor: Optional[float] = Query(None, description="最小影响因子"),
    max_impact_factor: Optional[float] = Query(None, description="最大影响因子"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取期刊列表，支持筛选和搜索"""
    journal_repo = JournalRepository(db)

    # 获取期刊列表
    journals = await journal_repo.list_journals(
        subject_area=subject_area,
        min_impact_factor=min_impact_factor,
        max_impact_factor=max_impact_factor,
        search=search,
        limit=pagination.page_size,
        offset=(pagination.page - 1) * pagination.page_size
    )

    # 获取总数
    total = await journal_repo.count_journals(
        subject_area=subject_area,
        min_impact_factor=min_impact_factor,
        max_impact_factor=max_impact_factor,
        search=search
    )

    return paginated_response(
        items=[_journal_to_dict(j) for j in journals],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


def _journal_to_dict(j: dict) -> dict:
    """将期刊数据转换为字典"""
    return {
        "id": str(j["id"]),
        "name": j["name"],
        "issn": j.get("issn"),
        "publisher": j.get("publisher"),
        "subject_areas": j.get("subject_areas", []),
        "impact_factor": float(j["impact_factor"]) if j.get("impact_factor") else None,
        "h_index": j.get("h_index"),
        "acceptance_rate": float(j["acceptance_rate"]) if j.get("acceptance_rate") else None,
        "review_cycle_days": j.get("review_cycle_days"),
        "is_open_access": j.get("is_open_access", False),
        "submission_url": j.get("submission_url"),
    }


@router.get("/{journal_id}", summary="获取期刊详情")
async def get_journal(
    journal_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取期刊详细信息"""
    journal_repo = JournalRepository(db)
    journal = await journal_repo.get_by_id(journal_id)

    if not journal:
        raise HTTPException(status_code=404, detail="期刊不存在")

    return success_response(
        data=JournalDetail(
            id=str(journal["id"]),
            name=journal["name"],
            issn=journal.get("issn"),
            publisher=journal.get("publisher"),
            subject_areas=journal.get("subject_areas", []),
            impact_factor=float(journal["impact_factor"]) if journal.get("impact_factor") else None,
            h_index=journal.get("h_index"),
            sjr=float(journal["sjr"]) if journal.get("sjr") else None,
            acceptance_rate=float(journal["acceptance_rate"]) if journal.get("acceptance_rate") else None,
            review_cycle_days=journal.get("review_cycle_days"),
            publication_fee=float(journal["publication_fee"]) if journal.get("publication_fee") else None,
            is_open_access=journal.get("is_open_access", False),
            apc=float(journal["apc"]) if journal.get("apc") else None,
            description=journal.get("description"),
            scope=journal.get("scope"),
            language=journal.get("language", "zh"),
            keywords=journal.get("keywords", []),
            submission_url=journal.get("submission_url"),
        ).model_dump()
    )


@router.post("/compare", summary="对比期刊")
async def compare_journals(
    journal_ids: List[str] = Query(..., description="期刊ID列表"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """对比多个期刊"""
    journal_repo = JournalRepository(db)

    selected_journals = []
    for journal_id in journal_ids:
        journal = await journal_repo.get_by_id(journal_id)
        if journal:
            selected_journals.append(journal)

    if not selected_journals:
        raise HTTPException(status_code=404, detail="未找到指定期刊")

    # 生成对比矩阵
    comparison = {}
    for journal in selected_journals:
        comparison[str(journal["id"])] = {
            "name": journal["name"],
            "impact_factor": float(journal["impact_factor"]) if journal.get("impact_factor") else 0,
            "acceptance_rate": float(journal["acceptance_rate"]) if journal.get("acceptance_rate") else 0,
            "subject_areas": journal.get("subject_areas", []),
            "review_cycle_days": journal.get("review_cycle_days", 90),
            "is_open_access": journal.get("is_open_access", False),
        }

    return success_response(
        data={
            "journals": [_journal_to_dict(j) for j in selected_journals],
            "comparison": comparison,
        }
    )


# ============== 投稿记录 ==============

@submission_router.get("", summary="获取我的投稿记录")
async def get_my_submissions(
    status: Optional[str] = Query(None, description="状态筛选"),
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的投稿记录"""
    submission_repo = SubmissionRepository(db)

    submissions = await submission_repo.get_by_user(
        user_id=user_id,
        status=status,
        limit=pagination.page_size,
        offset=(pagination.page - 1) * pagination.page_size
    )

    total = await submission_repo.count_by_user(user_id, status)

    return paginated_response(
        items=[_submission_to_dict(s) for s in submissions],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


def _submission_to_dict(s: dict) -> dict:
    """将投稿记录转换为字典"""
    return {
        "id": str(s["id"]),
        "paper_id": str(s["paper_id"]),
        "journal_id": str(s["journal_id"]),
        "journal_name": s.get("journal_name", ""),
        "status": s["status"],
        "manuscript_id": s.get("manuscript_id"),
        "submitted_at": s["submitted_at"].isoformat() if s.get("submitted_at") else None,
        "first_decision_at": s["first_decision_at"].isoformat() if s.get("first_decision_at") else None,
        "final_decision_at": s["final_decision_at"].isoformat() if s.get("final_decision_at") else None,
        "decision": s.get("decision"),
        "notes": s.get("notes"),
    }


@submission_router.post("", summary="创建投稿记录")
async def create_submission(
    data: SubmissionRecordCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新的投稿记录"""
    # 验证期刊存在
    journal_repo = JournalRepository(db)
    journal = await journal_repo.get_by_id(str(data.journal_id))

    if not journal:
        raise HTTPException(status_code=404, detail="期刊不存在")

    submission_repo = SubmissionRepository(db)

    record_data = {
        "paper_id": str(data.paper_id),
        "journal_id": str(data.journal_id),
        "manuscript_id": data.manuscript_id,
        "status": "submitted",
        "submitted_at": datetime.now(),
        "notes": data.notes,
    }

    created = await submission_repo.create(record_data)

    if not created:
        raise HTTPException(status_code=500, detail="创建投稿记录失败")

    return success_response(
        data=_submission_to_dict(created),
        message="投稿记录已创建",
        code=201,
    )


@submission_router.get("/{submission_id}", summary="获取投稿记录详情")
async def get_submission(
    submission_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取投稿记录详情"""
    submission_repo = SubmissionRepository(db)
    submission = await submission_repo.get_by_id(submission_id)

    if not submission:
        raise HTTPException(status_code=404, detail="投稿记录不存在")

    return success_response(data=_submission_to_dict(submission))


@submission_router.put("/{submission_id}", summary="更新投稿记录")
async def update_submission(
    submission_id: str,
    data: SubmissionRecordUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新投稿记录状态"""
    submission_repo = SubmissionRepository(db)

    update_data = {}
    if data.status:
        update_data["status"] = data.status
    if data.manuscript_id:
        update_data["manuscript_id"] = data.manuscript_id
    if data.first_decision_at:
        update_data["first_decision_at"] = data.first_decision_at
    if data.final_decision_at:
        update_data["final_decision_at"] = data.final_decision_at
    if data.decision:
        update_data["decision"] = data.decision
    if data.notes is not None:
        update_data["notes"] = data.notes

    updated = await submission_repo.update(submission_id, update_data)

    if not updated:
        raise HTTPException(status_code=404, detail="投稿记录不存在")

    return success_response(
        data=_submission_to_dict(updated),
        message="投稿记录已更新"
    )


@submission_router.delete("/{submission_id}", summary="删除投稿记录")
async def delete_submission(
    submission_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除投稿记录"""
    submission_repo = SubmissionRepository(db)
    deleted = await submission_repo.delete(submission_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="投稿记录不存在")

    return success_response(message="投稿记录已删除")


# ============== 匹配历史 ==============

@router.get("/matches/history", summary="获取匹配历史")
async def get_match_history(
    paper_id: Optional[str] = Query(None, description="论文ID筛选"),
    limit: int = Query(20, description="返回数量"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的期刊匹配历史"""
    match_repo = JournalMatchRepository(db)
    history = await match_repo.get_by_user(
        user_id=user_id,
        paper_id=paper_id,
        limit=limit
    )

    return success_response(data=[
        {
            "id": str(h["id"]),
            "paper_id": str(h["paper_id"]),
            "journal_id": str(h["journal_id"]),
            "journal_name": h.get("journal_name", ""),
            "match_score": float(h["match_score"]) if h.get("match_score") else 0,
            "match_reasons": h.get("match_reasons", []),
            "estimated_acceptance_rate": float(h["estimated_acceptance_rate"]) if h.get("estimated_acceptance_rate") else None,
            "created_at": h["created_at"].isoformat() if h.get("created_at") else None,
        }
        for h in history
    ])


# ============== 统计 ==============

@router.get("/stats/overview", summary="获取期刊统计")
async def get_journal_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取期刊数据库统计信息"""
    journal_repo = JournalRepository(db)

    # 获取所有期刊用于统计
    all_journals = await journal_repo.get_all_journals()

    if not all_journals:
        # 初始化示例数据
        all_journals = await _init_sample_journals(db)

    total = len(all_journals)

    by_type = {}
    by_ranking = {}
    by_subject = {}
    total_impact = 0
    impact_count = 0
    total_acceptance = 0
    acceptance_count = 0

    for journal in all_journals:
        # 统计学科分布
        for area in journal.get("subject_areas", []):
            by_subject[area] = by_subject.get(area, 0) + 1

        # 统计影响因子
        if journal.get("impact_factor"):
            total_impact += float(journal["impact_factor"])
            impact_count += 1

        # 统计接受率
        if journal.get("acceptance_rate"):
            total_acceptance += float(journal["acceptance_rate"])
            acceptance_count += 1

    return success_response(
        data=JournalStats(
            total_journals=total,
            by_type=by_type,
            by_ranking=by_ranking,
            by_subject=by_subject,
            average_impact_factor=total_impact / impact_count if impact_count > 0 else 0,
            average_acceptance_rate=total_acceptance / acceptance_count if acceptance_count > 0 else 0,
        ).model_dump()
    )
