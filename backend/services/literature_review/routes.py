"""
文献综述生成服务 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime

from shared.dependencies import get_current_user_id
from shared.responses import success_response
from shared.config import settings

from ..ai.llm_provider_v2 import LLMService
from .schemas import (
    LiteratureReviewRequest,
    LiteratureReview,
    QuickReviewRequest,
    ReviewGenerationTask,
)
from .service import LiteratureReviewService

router = APIRouter(prefix="/api/v1/literature-review", tags=["文献综述"])

# 初始化服务
llm_service = LLMService(
    openai_key=settings.openai_api_key,
    anthropic_key=settings.anthropic_api_key,
)
review_service = LiteratureReviewService(llm_service)

# 任务存储（实际应用应使用Redis或数据库）
tasks: dict[str, ReviewGenerationTask] = {}


@router.post("/generate", summary="生成文献综述")
async def generate_review(
    request: LiteratureReviewRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    基于选定的文献生成综述

    - **article_ids**: 文献ID列表（2-50篇）
    - **focus_area**: 综述聚焦领域
    - **output_length**: 输出长度
    - **language**: 输出语言
    """
    task_id = str(uuid.uuid4())

    # 创建任务
    task = ReviewGenerationTask(
        task_id=task_id,
        status="pending",
        request=request,
    )
    tasks[task_id] = task

    # TODO: 实际应该从数据库获取文献数据
    # 这里使用模拟数据演示
    mock_articles = [
        {
            "id": f"article_{i}",
            "title": f"Sample Research Paper {i+1}",
            "authors": [{"name": f"Author {i+1}"}],
            "abstract": f"This is a sample abstract for research paper {i+1}.",
            "publication_year": 2023,
            "source_name": "Journal of Example",
        }
        for i in range(min(len(request.article_ids), 10))
    ]

    try:
        task.status = "processing"
        task.current_step = "正在分析文献..."

        # 生成综述
        review = await review_service.generate_review(request, mock_articles)

        task.status = "completed"
        task.result = review
        task.completed_at = datetime.now()

        return success_response(
            data={
                "task_id": task_id,
                "status": "completed",
                "review": review.dict(),
            },
            message="综述生成成功",
        )

    except Exception as e:
        task.status = "failed"
        task.error_message = str(e)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/quick-generate", summary="快速生成综述")
async def quick_generate(
    request: QuickReviewRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    基于主题快速生成综述（自动检索文献）

    - **topic**: 研究主题
    - **keywords**: 关键词
    - **max_articles**: 最大文献数量
    """
    # 这里应该调用文献检索服务自动获取文献
    # 简化版本：返回任务ID，异步处理

    task_id = str(uuid.uuid4())

    return success_response(
        data={
            "task_id": task_id,
            "status": "processing",
            "message": f"正在为主题 '{request.topic}' 生成综述...",
        },
        code=202,
    )


@router.get("/tasks/{task_id}", summary="查询综述生成任务")
async def get_task_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """查询综述生成任务状态"""
    task = tasks.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return success_response(
        data={
            "task_id": task.task_id,
            "status": task.status,
            "progress": task.progress,
            "current_step": task.current_step,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result.dict() if task.result else None,
        }
    )


@router.get("/tasks/{task_id}/export", summary="导出综述")
async def export_review(
    task_id: str,
    format: str = "markdown",  # markdown | docx | pdf
    user_id: str = Depends(get_current_user_id),
):
    """导出文献综述为指定格式"""
    task = tasks.get(task_id)

    if not task or task.status != "completed":
        raise HTTPException(status_code=404, detail="综述不存在或未生成完成")

    review = task.result

    if format == "markdown":
        content = review_service.export_to_markdown(review)
        return success_response(
            data={
                "format": "markdown",
                "content": content,
                "filename": f"literature_review_{task_id[:8]}.md",
            }
        )

    # TODO: 支持 docx 和 pdf 导出
    raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")


@router.delete("/tasks/{task_id}", summary="删除综述任务")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """删除综述生成任务"""
    if task_id in tasks:
        del tasks[task_id]
        return success_response(message="任务已删除")

    raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/analyze-themes", summary="分析研究主题")
async def analyze_themes(
    article_ids: List[str],
    user_id: str = Depends(get_current_user_id),
):
    """分析选定文献的研究主题"""
    # TODO: 实现主题分析
    return success_response(
        data={
            "themes": [
                {"name": "主题1", "description": "描述1", "article_count": 5},
                {"name": "主题2", "description": "描述2", "article_count": 3},
            ]
        }
    )


@router.post("/compare", summary="文献对比分析")
async def compare_articles(
    article_ids: List[str],
    comparison_aspects: Optional[List[str]] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    对比分析多篇文献

    - **article_ids**: 要对比的文献ID
    - **comparison_aspects**: 对比维度（方法论、发现等）
    """
    # TODO: 实现文献对比
    return success_response(
        data={
            "comparison": {
                "methodology": "方法论对比...",
                "findings": "研究发现对比...",
            }
        }
    )


# ============== 证据矩阵 API ==============

from .evidence_extractor import get_evidence_extractor, Evidence
from .evidence_matrix import get_matrix_generator, EvidenceMatrix
from .consensus_analyzer import get_consensus_analyzer, ConsensusAnalysis


@router.post("/evidence-matrix", summary="生成证据矩阵")
async def generate_evidence_matrix(
    article_ids: List[str],
    title: Optional[str] = "文献证据矩阵",
    description: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    基于选定的文献生成证据矩阵

    - 提取各文献的关键证据
    - 按标准维度整理对比
    - 支持自定义对比维度
    """
    extractor = get_evidence_extractor()
    matrix_generator = get_matrix_generator()

    # TODO: 从数据库获取文献数据
    # 这里使用模拟数据
    mock_articles = [
        {
            "article_id": f"article_{i}",
            "title": f"Research Paper {i+1}",
            "abstract": f"Abstract for paper {i+1}.",
            "authors": [f"Author {i+1}"],
            "year": 2023,
            "journal": "Journal of Example",
        }
        for i in range(min(len(article_ids), 5))
    ]

    # 提取证据
    evidences = await extractor.extract_from_articles_batch(mock_articles)

    # 生成矩阵
    matrix = matrix_generator.generate_matrix(
        evidences=evidences,
        title=title,
        description=description,
    )

    # 生成总结
    summary = matrix_generator.generate_comparison_summary(matrix)

    return success_response(
        data={
            "matrix": matrix.to_dict(),
            "summary": summary,
        }
    )


@router.post("/evidence-extract", summary="提取文献证据")
async def extract_evidence(
    article_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    从单篇文献中提取结构化证据

    - 提取研究设计、样本、主要发现
    - 评估证据质量和强度
    - 识别研究局限性
    """
    extractor = get_evidence_extractor()

    # TODO: 从数据库获取文献详情
    # 模拟数据
    mock_article = {
        "article_id": article_id,
        "title": "Sample Research Paper",
        "abstract": "This is a sample abstract with findings.",
        "authors": ["Author 1", "Author 2"],
        "year": 2023,
        "journal": "Journal of Example",
    }

    evidences = await extractor.extract_from_article(**mock_article)

    return success_response(
        data={
            "article_id": article_id,
            "evidences": [e.to_dict() for e in evidences],
            "extraction_count": len(evidences),
        }
    )


@router.post("/consensus", summary="分析共识度")
async def analyze_consensus(
    question: str,
    article_ids: List[str],
    user_id: str = Depends(get_current_user_id),
):
    """
    分析学术界对特定问题的共识度

    - 识别各研究的立场（支持/反对/中立）
    - 计算共识分数和级别
    - 提取支持和反对的主要证据
    - 识别分歧点和可能来源
    """
    analyzer = get_consensus_analyzer()
    extractor = get_evidence_extractor()

    # TODO: 从数据库获取文献数据
    # 模拟数据
    mock_articles = [
        {
            "article_id": f"article_{i}",
            "title": f"Research Paper {i+1}",
            "abstract": f"Findings about {question}.",
            "authors": [f"Author {i+1}"],
            "year": 2023,
        }
        for i in range(min(len(article_ids), 5))
    ]

    # 提取证据
    evidences = await extractor.extract_from_articles_batch(mock_articles)

    # 分析共识度
    analysis = await analyzer.analyze_consensus(question, evidences)

    return success_response(
        data=analysis.to_dict()
    )


@router.get("/consensus-levels", summary="获取共识度等级说明")
async def get_consensus_levels(
    user_id: str = Depends(get_current_user_id),
):
    """
    获取共识度等级及其说明
    """
    levels = [
        {
            "level": "unanimous",
            "name": "完全一致",
            "description": "超过95%的研究得出相同结论",
            "score_range": "0.95 - 1.0",
        },
        {
            "level": "strong",
            "name": "强共识",
            "description": "80-95%的研究达成一致",
            "score_range": "0.80 - 0.95",
        },
        {
            "level": "moderate",
            "name": "中等共识",
            "description": "60-80%的研究达成一致",
            "score_range": "0.60 - 0.80",
        },
        {
            "level": "mixed",
            "name": "混合",
            "description": "40-60%存在分歧",
            "score_range": "0.40 - 0.60",
        },
        {
            "level": "controversial",
            "name": "争议",
            "description": "20-40%存在严重分歧",
            "score_range": "0.20 - 0.40",
        },
        {
            "level": "fragmented",
            "name": "高度分歧",
            "description": "少于20%达成一致",
            "score_range": "0.00 - 0.20",
        },
    ]

    return success_response(data={"levels": levels})
