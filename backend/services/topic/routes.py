"""
选题助手 API 路由
FastAPI 路由定义
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import random
import json

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.responses import success_response, paginated_response
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams

from .schemas import (
    TopicSuggestionRequest,
    TopicSuggestionResponse,
    TopicIdea,
    FeasibilityAnalysis,
    FeasibilityLevel,
    ResourceRequirement,
    TimelineMilestone,
    ResearchGap,
    TrendAnalysisResponse,
    ResearchTrend,
    TrendData,
    ResearchPlan,
    ResearchTask,
    ProposalOutline,
    ResearchQuestion,
    ResearchMethod,
)
from .repository import TopicSuggestionRepository, ProposalOutlineRepository
from .ai_client import ai_client

router = APIRouter(prefix="/api/v1/topics", tags=["选题助手"])


# ============== 选题建议 ==============

@router.post("/suggest", summary="获取选题建议")
async def suggest_topics(
    request: TopicSuggestionRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    基于研究领域和关键词生成选题建议

    使用AI分析研究趋势，识别研究空白，提供可行性评估
    """
    # 调用AI服务生成选题建议
    ai_suggestions = await ai_client.generate_topic_suggestions(
        field=request.field,
        keywords=request.keywords,
        interests=request.interests or [],
        degree_level=request.degree_level,
        num_suggestions=5
    )

    suggestions = []
    repo = TopicSuggestionRepository(db)

    if ai_suggestions:
        # 使用AI生成的建议
        for suggestion_data in ai_suggestions:
            try:
                # 保存到数据库
                db_data = {
                    "user_id": user_id,
                    "title": suggestion_data.get("title", "未命名选题"),
                    "description": suggestion_data.get("description", ""),
                    "field": suggestion_data.get("field", request.field),
                    "keywords": suggestion_data.get("keywords", request.keywords),
                    "feasibility_score": suggestion_data.get("feasibility_score", 70),
                    "feasibility_level": suggestion_data.get("feasibility_level", "medium"),
                }
                saved = await repo.create(db_data)

                # 构建响应对象
                research_gaps = [
                    ResearchGap(
                        gap_type=g.get("type", "method"),
                        description=g.get("description", ""),
                        significance=g.get("significance", "中"),
                    )
                    for g in suggestion_data.get("research_gaps", [])
                ]

                topic = TopicIdea(
                    id=str(saved["id"]) if saved else str(uuid.uuid4()),
                    title=suggestion_data.get("title", "未命名选题"),
                    description=suggestion_data.get("description", ""),
                    keywords=suggestion_data.get("keywords", request.keywords),
                    field=suggestion_data.get("field", request.field),
                    feasibility_level=FeasibilityLevel(suggestion_data.get("feasibility_level", "medium")),
                    feasibility_score=float(suggestion_data.get("feasibility_score", 70)),
                    research_gaps=research_gaps if research_gaps else [
                        ResearchGap(
                            gap_type="method",
                            description="研究方法需要创新",
                            significance="高",
                        )
                    ],
                    required_methods=["文献研究法", "实证研究法"],
                    required_data=["行业数据", "调研数据"],
                    required_tools=["数据分析工具", "文献管理工具"],
                    estimated_duration_months=suggestion_data.get("estimated_duration_months", 6),
                    risks=suggestion_data.get("risks", ["数据获取困难", "技术实现复杂"]),
                    mitigation_strategies=suggestion_data.get("mitigation_strategies", ["多渠道数据收集", "简化技术方案"]),
                    related_papers=["相关论文1", "相关论文2"],
                    recent_trends=["AI应用增长", "跨学科融合"],
                )
                suggestions.append(topic)
            except Exception as e:
                print(f"处理选题建议失败: {e}")
                continue

    # 如果AI没有返回结果或失败，使用后备方案
    if not suggestions:
        suggestions = await _generate_fallback_suggestions(
            request.field, request.keywords, request.degree_level, user_id, db
        )

    return success_response(
        data=TopicSuggestionResponse(
            suggestions=suggestions,
            total_count=len(suggestions),
            generated_at=datetime.now(),
        ).model_dump(),
        message=f"成功生成 {len(suggestions)} 个选题建议",
    )


async def _generate_fallback_suggestions(
    field: str,
    keywords: List[str],
    degree_level: str,
    user_id: str,
    db: AsyncSession
) -> List[TopicIdea]:
    """生成后备选题建议（当AI服务不可用时）"""
    repo = TopicSuggestionRepository(db)
    suggestions = []

    base_keywords = keywords[:3] if keywords else ["智能技术", "数据分析"]

    templates = [
        {
            "title": f"{field}领域基于{base_keywords[0] if base_keywords else 'AI'}的创新应用研究",
            "description": f"探索{base_keywords[0] if base_keywords else '新技术'}在{field}中的应用模式与效果，为实践提供理论指导。",
            "keywords": [base_keywords[0] if base_keywords else "AI", field, "创新应用"],
            "score": 75,
            "level": FeasibilityLevel.HIGH,
        },
        {
            "title": f"{field}中{base_keywords[0] if base_keywords else '新方法'}的实证研究",
            "description": f"通过实证方法研究{base_keywords[0] if base_keywords else '新方法'}在{field}中的实际应用效果，验证其有效性。",
            "keywords": [base_keywords[0] if base_keywords else "新方法", field, "实证研究"],
            "score": 70,
            "level": FeasibilityLevel.MEDIUM,
        },
        {
            "title": f"{field}转型升级的路径与策略研究",
            "description": f"分析{field}面临的挑战与机遇，提出转型升级的路径选择与实施策略。",
            "keywords": [field, "转型升级", "策略研究"],
            "score": 72,
            "level": FeasibilityLevel.MEDIUM,
        },
    ]

    for template in templates:
        db_data = {
            "user_id": user_id,
            "title": template["title"],
            "description": template["description"],
            "field": field,
            "keywords": template["keywords"],
            "feasibility_score": template["score"],
            "feasibility_level": template["level"].value,
        }
        saved = await repo.create(db_data)

        topic = TopicIdea(
            id=str(saved["id"]) if saved else str(uuid.uuid4()),
            title=template["title"],
            description=template["description"],
            keywords=template["keywords"],
            field=field,
            feasibility_level=template["level"],
            feasibility_score=float(template["score"]),
            research_gaps=[
                ResearchGap(
                    gap_type="method",
                    description="现有研究方法存在局限性",
                    significance="高",
                ),
            ],
            required_methods=["文献研究法", "实证研究法"],
            required_data=["行业数据"],
            required_tools=["数据分析工具"],
            estimated_duration_months=6 if degree_level == "master" else 12,
            risks=["数据获取困难"],
            mitigation_strategies=["多渠道数据收集"],
            related_papers=[],
            recent_trends=[],
        )
        suggestions.append(topic)

    return suggestions


# ============== 可行性分析 ==============

@router.post("/analyze/{topic_id}", summary="深度可行性分析")
async def analyze_feasibility(
    topic_id: str,
    detailed: bool = Query(False, description="是否返回详细分析"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    对特定选题进行深度可行性分析

    包括资源需求、时间估算、风险评估
    """
    # 从数据库获取选题信息
    repo = TopicSuggestionRepository(db)
    topic = await repo.get_by_id(topic_id, user_id)

    if not topic:
        raise HTTPException(status_code=404, detail="选题不存在")

    # 调用AI进行可行性分析
    ai_analysis = await ai_client.analyze_feasibility(
        topic=topic["title"],
        description=topic.get("description", ""),
        field=topic.get("field", ""),
        degree_level="master",  # 可以从用户资料获取
    )

    if ai_analysis:
        # 解析AI返回的结果
        analysis = FeasibilityAnalysis(
            topic=topic["title"],
            overall_score=float(ai_analysis.get("overall_score", 70)),
            level=FeasibilityLevel(ai_analysis.get("level", "medium")),
            academic_value_score=float(ai_analysis.get("academic_value_score", 70)),
            innovation_score=float(ai_analysis.get("innovation_score", 70)),
            resource_availability_score=float(ai_analysis.get("resource_availability_score", 70)),
            time_feasibility_score=float(ai_analysis.get("time_feasibility_score", 70)),
            risk_score=float(ai_analysis.get("risk_score", 50)),
            strengths=ai_analysis.get("strengths", ["研究问题具有现实意义", "理论基础扎实"]),
            weaknesses=ai_analysis.get("weaknesses", ["技术实现存在挑战"]),
            opportunities=ai_analysis.get("opportunities", ["领域发展迅速", "政策支持"]),
            threats=ai_analysis.get("threats", ["竞争激烈", "数据获取困难"]),
            resource_requirements=[
                ResourceRequirement(
                    resource_type=r.get("resource_type", "other"),
                    description=r.get("description", ""),
                    availability=r.get("availability", "medium"),
                    estimated_cost=r.get("estimated_cost"),
                )
                for r in ai_analysis.get("resource_requirements", [])
            ],
            timeline=[
                TimelineMilestone(
                    phase=t.get("phase", "未命名阶段"),
                    tasks=t.get("tasks", []),
                    duration_weeks=t.get("duration_weeks", 4),
                    dependencies=t.get("dependencies", []),
                )
                for t in ai_analysis.get("timeline", [])
            ],
            recommendations=ai_analysis.get("recommendations", ["建议先进行小规模预研究"]),
            alternative_topics=ai_analysis.get("alternative_topics", []),
            research_gaps=[
                ResearchGap(
                    gap_type=g.get("gap_type", "method"),
                    description=g.get("description", ""),
                    significance=g.get("significance", "中"),
                )
                for g in ai_analysis.get("research_gaps", [])
            ],
        )
    else:
        # 使用后备方案
        analysis = await _generate_fallback_analysis(topic)

    return success_response(data=analysis.model_dump())


async def _generate_fallback_analysis(topic: dict) -> FeasibilityAnalysis:
    """生成后备可行性分析"""
    base_score = topic.get("feasibility_score", 70)

    return FeasibilityAnalysis(
        topic=topic["title"],
        overall_score=float(base_score),
        level=FeasibilityLevel(topic.get("feasibility_level", "medium")),
        academic_value_score=float(base_score) + random.randint(-10, 10),
        innovation_score=float(base_score) + random.randint(-10, 5),
        resource_availability_score=float(base_score) + random.randint(-5, 10),
        time_feasibility_score=float(base_score) + random.randint(-10, 10),
        risk_score=random.randint(30, 60),
        strengths=[
            "研究问题具有现实意义",
            "理论基础扎实",
            "数据来源明确",
        ],
        weaknesses=[
            "技术实现存在挑战",
            "需要跨领域知识",
        ],
        opportunities=[
            "领域发展迅速",
            "政策支持",
        ],
        threats=[
            "竞争激烈",
            "数据获取困难",
        ],
        resource_requirements=[
            ResourceRequirement(
                resource_type="数据",
                description="需要收集近3年的行业数据",
                availability="medium",
                estimated_cost="时间成本约2周",
            ),
            ResourceRequirement(
                resource_type="软件",
                description="数据分析软件（如SPSS、Python）",
                availability="easy",
                estimated_cost="免费/低成本",
            ),
        ],
        timeline=[
            TimelineMilestone(
                phase="文献综述",
                tasks=["收集文献", "阅读分析", "撰写综述"],
                duration_weeks=4,
            ),
            TimelineMilestone(
                phase="研究设计",
                tasks=["确定方法", "设计问卷/实验", "预测试"],
                duration_weeks=3,
                dependencies=["文献综述"],
            ),
            TimelineMilestone(
                phase="数据收集",
                tasks=["收集数据", "数据清洗", "数据整理"],
                duration_weeks=4,
                dependencies=["研究设计"],
            ),
            TimelineMilestone(
                phase="数据分析",
                tasks=["统计分析", "结果解释", "可视化"],
                duration_weeks=3,
                dependencies=["数据收集"],
            ),
            TimelineMilestone(
                phase="论文撰写",
                tasks=["撰写初稿", "修改完善", "格式调整"],
                duration_weeks=6,
                dependencies=["数据分析"],
            ),
        ],
        recommendations=[
            "建议先进行小规模预研究",
            "可以参考类似研究的成功经验",
            "定期与导师沟通进展",
        ],
        research_gaps=[
            ResearchGap(
                gap_type="method",
                description="现有研究方法存在局限性",
                significance="高",
            ),
        ],
    )


# ============== 开题报告生成 ==============

@router.post("/proposal/generate", summary="生成开题报告大纲")
async def generate_proposal(
    topic: str = Query(..., description="选题标题"),
    field: str = Query(..., description="研究领域"),
    keywords: Optional[str] = Query(None, description="关键词（逗号分隔）"),
    degree_level: str = Query("master", description="学位级别"),
    university: Optional[str] = Query(None, description="学校"),
    supervisor: Optional[str] = Query(None, description="导师姓名"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    根据选题生成开题报告大纲

    包括研究背景、目的、方法、预期成果等
    """
    # 调用AI生成开题报告
    ai_proposal = await ai_client.generate_proposal(
        topic=topic,
        field=field,
        degree_level=degree_level,
        university=university,
        supervisor=supervisor,
    )

    if ai_proposal:
        proposal = ProposalOutline(
            title=ai_proposal.get("title", topic),
            background=ai_proposal.get("background", _generate_default_background(topic, field)),
            objectives=ai_proposal.get("objectives", _generate_default_objectives(topic)),
            research_questions=[
                ResearchQuestion(
                    id=rq.get("id", f"rq{i}"),
                    question=rq.get("question", ""),
                    sub_questions=rq.get("sub_questions", []),
                )
                for i, rq in enumerate(ai_proposal.get("research_questions", []))
            ],
            research_methods=[
                ResearchMethod(
                    method_type=rm.get("method_type", ""),
                    description=rm.get("description", ""),
                    data_source=rm.get("data_source"),
                    analysis_approach=rm.get("analysis_approach"),
                )
                for rm in ai_proposal.get("research_methods", [])
            ],
            expected_outcomes=ai_proposal.get("expected_outcomes", [
                "完成一篇高质量的学位论文",
                "在相关领域期刊发表1-2篇论文",
                "形成可操作的建议方案",
            ]),
            innovation_points=ai_proposal.get("innovation_points", [
                "研究视角创新",
                "研究方法创新",
                "理论贡献",
            ]),
            timeline=ai_proposal.get("timeline", [
                {"phase": "第一阶段", "task": "文献综述", "duration": "第1-2月"},
                {"phase": "第二阶段", "task": "研究设计", "duration": "第3月"},
                {"phase": "第三阶段", "task": "数据收集", "duration": "第4-5月"},
                {"phase": "第四阶段", "task": "数据分析", "duration": "第6月"},
                {"phase": "第五阶段", "task": "论文撰写", "duration": "第7-8月"},
            ]),
            references=ai_proposal.get("references", [
                "[1] 张三. 相关研究综述[J]. 学术期刊, 2024.",
                "[2] Li, M. et al. Research on related topics[J]. Journal, 2023.",
            ]),
            generated_at=datetime.now(),
            total_words=ai_proposal.get("total_words", 2000),
        )
    else:
        # 使用后备方案
        proposal = _generate_fallback_proposal(topic, field)

    # 保存到数据库
    repo = ProposalOutlineRepository(db)
    db_data = {
        "user_id": user_id,
        "title": proposal.title,
        "background": proposal.background,
        "objectives": proposal.objectives,
        "methods": [rm.model_dump() for rm in proposal.research_methods],
        "timeline": proposal.timeline,
        "references": proposal.references,
        "total_words": proposal.total_words,
    }
    await repo.create(db_data)

    return success_response(
        data=proposal.model_dump(),
        message="开题报告大纲生成成功",
    )


def _generate_default_background(topic: str, field: str) -> str:
    """生成默认研究背景"""
    return f"""一、研究背景

1.1 研究缘起

随着{field}领域的快速发展，{topic}成为学术界和实践界关注的焦点。现有研究虽然取得了一定进展，但在某些关键问题上仍存在不足，需要进一步深入探讨。

1.2 研究意义

本研究具有重要的理论意义和实践价值。理论上，可以丰富{field}领域的知识体系，推动相关理论的发展；实践上，可为相关决策提供科学依据，指导实际工作。

1.3 国内外研究现状

国内外学者对相关问题进行了广泛研究，主要集中在以下几个方面：...
"""


def _generate_default_objectives(topic: str) -> str:
    """生成默认研究目标"""
    return f"""二、研究目标

2.1 总体目标

系统研究{topic}，揭示其内在规律，提出有效的解决方案。

2.2 具体目标

1. 梳理{topic}的理论基础和发展脉络
2. 分析当前存在的问题和挑战
3. 提出创新性的解决方案
4. 验证方案的有效性
"""


def _generate_fallback_proposal(topic: str, field: str) -> ProposalOutline:
    """生成后备开题报告"""
    return ProposalOutline(
        title=topic,
        background=_generate_default_background(topic, field),
        objectives=_generate_default_objectives(topic),
        research_questions=[
            ResearchQuestion(
                id="rq1",
                question=f"{topic}的核心影响因素有哪些？",
                sub_questions=["因素如何相互作用？", "各因素的影响程度如何？"],
            ),
            ResearchQuestion(
                id="rq2",
                question=f"如何优化{topic}的实施路径？",
                sub_questions=["关键步骤是什么？", "需要哪些资源支持？"],
            ),
        ],
        research_methods=[
            ResearchMethod(
                method_type="文献研究法",
                description="系统梳理国内外相关文献，构建理论框架",
                data_source="学术数据库（CNKI、Web of Science等）",
                analysis_approach="系统性文献综述",
            ),
            ResearchMethod(
                method_type="实证研究法",
                description="通过问卷调查或实验收集数据，验证研究假设",
                data_source="调研数据/实验数据",
                analysis_approach="统计分析（SPSS/Python）",
            ),
        ],
        expected_outcomes=[
            "完成一篇高质量的学位论文",
            "在相关领域期刊发表1-2篇论文",
            "形成可操作的建议方案",
        ],
        innovation_points=[
            "研究视角创新：从新角度审视问题",
            "研究方法创新：采用混合研究方法",
            "理论贡献：丰富相关理论体系",
        ],
        timeline=[
            {"phase": "第一阶段", "task": "文献综述", "duration": "第1-2月"},
            {"phase": "第二阶段", "task": "研究设计", "duration": "第3月"},
            {"phase": "第三阶段", "task": "数据收集", "duration": "第4-5月"},
            {"phase": "第四阶段", "task": "数据分析", "duration": "第6月"},
            {"phase": "第五阶段", "task": "论文撰写", "duration": "第7-8月"},
        ],
        references=[
            "[1] 张三. 相关研究综述[J]. 学术期刊, 2024.",
            "[2] Li, M. et al. Research on related topics[J]. Journal, 2023.",
        ],
        generated_at=datetime.now(),
        total_words=2000,
    )


# ============== 趋势分析 ==============

@router.get("/trends", summary="研究趋势分析")
async def analyze_trends(
    field: str = Query(..., description="研究领域"),
    keywords: Optional[str] = Query(None, description="关键词（逗号分隔）"),
    years: int = Query(5, description="分析年数"),
    user_id: str = Depends(get_current_user_id),
):
    """
    分析研究领域的热点趋势

    识别热门话题、新兴话题和衰退话题
    """
    keyword_list = [k.strip() for k in keywords.split(",")] if keywords else [field]

    # 调用AI分析趋势
    ai_trends = await ai_client.analyze_trends(
        field=field,
        keywords=keyword_list,
        years=years,
    )

    if ai_trends:
        trends = [
            ResearchTrend(
                keyword=t.get("keyword", kw),
                trend_data=[
                    TrendData(
                        year=td.get("year", datetime.now().year - years + i),
                        count=td.get("count", random.randint(50, 200)),
                        growth_rate=td.get("growth_rate"),
                    )
                    for i, td in enumerate(t.get("trend_data", []))
                ],
                current_hotness=t.get("current_hotness", 0.7),
                predicted_trend=t.get("predicted_trend", "stable"),
                related_keywords=t.get("related_keywords", []),
            )
            for t, kw in zip(ai_trends.get("trends", []), keyword_list)
        ]

        return success_response(
            data=TrendAnalysisResponse(
                field=field,
                trends=trends,
                hot_topics=ai_trends.get("hot_topics", ["AI应用", "数字化转型"]),
                emerging_topics=ai_trends.get("emerging_topics", ["大模型应用", "绿色技术"]),
                declining_topics=ai_trends.get("declining_topics", ["传统方法"]),
                analyzed_at=datetime.now(),
            ).model_dump()
        )

    # 使用后备方案
    trends = []
    current_year = datetime.now().year

    for kw in keyword_list[:5]:
        trend_data = []
        base_count = random.randint(100, 500)

        for i in range(years):
            year = current_year - years + i + 1
            growth = random.uniform(0.8, 1.3)
            count = int(base_count * (growth ** i))
            growth_rate = (growth - 1) * 100

            trend_data.append(TrendData(
                year=year,
                count=count,
                growth_rate=round(growth_rate, 1),
            ))

        current_hotness = random.uniform(0.5, 1.0)
        predicted_trend = random.choice(["rising", "stable", "rising"])

        trends.append(ResearchTrend(
            keyword=kw,
            trend_data=trend_data,
            current_hotness=round(current_hotness, 2),
            predicted_trend=predicted_trend,
            related_keywords=[f"{kw}应用", f"{kw}方法", f"{kw}优化"],
        ))

    return success_response(
        data=TrendAnalysisResponse(
            field=field,
            trends=trends,
            hot_topics=["AI应用", "数字化转型", "可持续发展"],
            emerging_topics=["大模型应用", "绿色技术", "元宇宙"],
            declining_topics=["传统方法", "过时技术"],
            analyzed_at=datetime.now(),
        ).model_dump()
    )


# ============== 研究计划 ==============

@router.post("/plan/generate", summary="生成研究计划")
async def generate_research_plan(
    topic: str = Query(..., description="选题"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    duration_months: int = Query(6, description="持续时间（月）"),
    user_id: str = Depends(get_current_user_id),
):
    """
    生成详细的研究计划

    包括甘特图数据、任务分解、里程碑
    """
    total_weeks = duration_months * 4
    start = datetime.now() if not start_date else datetime.fromisoformat(start_date)

    tasks = []
    phases = [
        {"name": "文献综述", "weeks": (1, 8), "tasks": ["文献检索", "文献阅读", "综述撰写"]},
        {"name": "研究设计", "weeks": (9, 12), "tasks": ["方法确定", "问卷设计", "预测试"]},
        {"name": "数据收集", "weeks": (13, 20), "tasks": ["数据采集", "数据清洗", "数据整理"]},
        {"name": "数据分析", "weeks": (21, 26), "tasks": ["统计分析", "结果解读", "图表制作"]},
        {"name": "论文撰写", "weeks": (27, 36), "tasks": ["初稿撰写", "修改完善", "格式调整"]},
        {"name": "答辩准备", "weeks": (37, 40), "tasks": ["PPT制作", "模拟答辩", "材料准备"]},
    ]

    task_id = 1
    for phase in phases:
        phase_start, phase_end = phase["weeks"]
        for i, task_name in enumerate(phase["tasks"]):
            tasks.append(ResearchTask(
                id=f"task_{task_id}",
                title=task_name,
                description=f"{phase['name']}阶段：{task_name}",
                phase=phase["name"],
                start_week=phase_start + i * 2,
                end_week=min(phase_start + (i + 1) * 2, phase_end),
                dependencies=[f"task_{task_id - 1}"] if task_id > 1 else [],
                status="pending",
                priority="high" if i == 0 else "medium",
            ))
            task_id += 1

    milestones = [
        {"week": 8, "name": "完成文献综述", "type": "review"},
        {"week": 20, "name": "完成数据收集", "type": "data"},
        {"week": 32, "name": "完成论文初稿", "type": "draft"},
        {"week": 40, "name": "答辩", "type": "defense"},
    ]

    # 甘特图数据
    gantt_data = {
        "tasks": [
            {
                "id": t.id,
                "name": t.title,
                "start": (start + timedelta(weeks=t.start_week)).isoformat(),
                "end": (start + timedelta(weeks=t.end_week)).isoformat(),
                "progress": 0,
                "dependencies": t.dependencies,
            }
            for t in tasks
        ],
        "milestones": [
            {
                "name": m["name"],
                "date": (start + timedelta(weeks=m["week"])).isoformat(),
            }
            for m in milestones
        ],
    }

    plan = ResearchPlan(
        topic=topic,
        total_weeks=total_weeks,
        phases=[{"name": p["name"], "start_week": p["weeks"][0], "end_week": p["weeks"][1]} for p in phases],
        tasks=tasks,
        milestones=milestones,
        gantt_chart=gantt_data,
    )

    return success_response(
        data=plan.model_dump(),
        message="研究计划生成成功",
    )


# ============== 选题收藏管理 ==============

@router.post("/favorites/{topic_id}", summary="收藏选题")
async def save_topic(
    topic_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """收藏感兴趣的选题"""
    repo = TopicSuggestionRepository(db)
    topic = await repo.get_by_id(topic_id, user_id)

    if not topic:
        raise HTTPException(status_code=404, detail="选题不存在")

    updated = await repo.update(topic_id, user_id, {"is_favorite": True})

    if updated:
        return success_response(message="选题已收藏")
    else:
        raise HTTPException(status_code=500, detail="收藏失败")


@router.delete("/favorites/{topic_id}", summary="取消收藏")
async def unsave_topic(
    topic_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """取消收藏选题"""
    repo = TopicSuggestionRepository(db)
    updated = await repo.update(topic_id, user_id, {"is_favorite": False})

    if updated:
        return success_response(message="已取消收藏")
    else:
        raise HTTPException(status_code=404, detail="选题不存在")


@router.get("/favorites", summary="获取收藏的选题")
async def get_saved_topics(
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户收藏的选题列表"""
    repo = TopicSuggestionRepository(db)

    items = await repo.get_favorites(
        user_id=user_id,
        limit=pagination.page_size,
        offset=(pagination.page - 1) * pagination.page_size
    )
    total = await repo.count_by_user(user_id)

    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/my", summary="获取我的选题")
async def get_my_topics(
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的所有选题建议"""
    repo = TopicSuggestionRepository(db)

    items = await repo.get_by_user(
        user_id=user_id,
        limit=pagination.page_size,
        offset=(pagination.page - 1) * pagination.page_size
    )
    total = await repo.count_by_user(user_id)

    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )
