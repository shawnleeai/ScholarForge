"""
学术分析 API 路由
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from shared.dependencies import get_current_user_id
from shared.responses import success_response

logger = logging.getLogger(__name__)

from .service import AnalyticsService
from .schemas import (
    AcademicImpactAnalysis,
    ResearcherProfile,
    TrendAnalysisResult,
    TrendAnalysisRequest,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["学术分析"])

# 初始化服务
analytics_service = AnalyticsService()


@router.post("/author/impact", summary="分析作者影响力")
async def analyze_author_impact(
    author_id: str,
    author_name: str,
    papers: List[dict],
    user_id: str = Depends(get_current_user_id),
):
    """
    分析研究者的学术影响力

    - **author_id**: 作者ID
    - **author_name**: 作者名称
    - **papers**: 论文列表
    """
    try:
        analysis = await analytics_service.analyze_author_impact(
            author_id=author_id,
            author_name=author_name,
            papers=papers,
        )
        return success_response(data=analysis.dict())
    except Exception as e:
        logger.error(f"Author impact analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")


@router.post("/trends", summary="研究趋势分析")
async def analyze_trends(
    request: TrendAnalysisRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    分析研究趋势

    - **keywords**: 研究关键词
    - **start_year**: 开始年份
    - **end_year**: 结束年份
    """
    try:
        result = await analytics_service.analyze_research_trends(
            keywords=request.keywords,
            start_year=request.start_year,
            end_year=request.end_year,
        )
        return success_response(data=result.dict())
    except Exception as e:
        logger.error(f"Trend analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="分析失败，请稍后重试")


@router.get("/paper/{paper_id}", summary="论文分析")
async def get_paper_analytics(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """获取单篇论文的详细分析"""
    analytics = await analytics_service.get_paper_analytics(paper_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="论文不存在")
    return success_response(data=analytics.dict())


@router.post("/compare", summary="对比分析")
async def compare_researchers(
    base_author: str,
    comparison_authors: List[str],
    papers_map: dict,  # {author_id: [papers]}
    user_id: str = Depends(get_current_user_id),
):
    """对比多个研究者的学术产出"""
    # 计算每个作者的指标
    metrics = {}

    all_authors = [base_author] + comparison_authors
    for author_id in all_authors:
        papers = papers_map.get(author_id, [])
        if not papers:
            metrics[author_id] = {
                "paper_count": 0,
                "total_citations": 0,
                "avg_citations": 0,
                "h_index": 0,
            }
            continue

        # 计算各项指标
        paper_count = len(papers)
        citation_counts = [p.get("citation_count", 0) for p in papers]
        total_citations = sum(citation_counts)
        avg_citations = round(total_citations / paper_count, 1) if paper_count > 0 else 0

        # 计算 h-index
        sorted_citations = sorted(citation_counts, reverse=True)
        h_index = 0
        for i, count in enumerate(sorted_citations, 1):
            if count >= i:
                h_index = i
            else:
                break

        metrics[author_id] = {
            "paper_count": paper_count,
            "total_citations": total_citations,
            "avg_citations": avg_citations,
            "h_index": h_index,
        }

    # 生成对比摘要
    base_metrics = metrics.get(base_author, {})
    comparison_summary = []
    for author_id in comparison_authors:
        author_metrics = metrics.get(author_id, {})
        diff_h_index = base_metrics.get("h_index", 0) - author_metrics.get("h_index", 0)
        diff_citations = base_metrics.get("total_citations", 0) - author_metrics.get("total_citations", 0)
        comparison_summary.append({
            "author_id": author_id,
            "h_index_diff": diff_h_index,
            "citations_diff": diff_citations,
            "comparison": "higher" if diff_h_index > 0 else "lower" if diff_h_index < 0 else "equal",
        })

    return success_response(
        data={
            "base_author": base_author,
            "comparison": comparison_authors,
            "metrics": metrics,
            "comparison_summary": comparison_summary,
        }
    )


@router.get("/h-index/calculate", summary="计算h-index")
async def calculate_h_index(
    citation_counts: List[int],
    user_id: str = Depends(get_current_user_id),
):
    """根据引用次数计算h-index"""
    citation_counts = sorted(citation_counts, reverse=True)
    h_index = 0
    for i, count in enumerate(citation_counts, 1):
        if count >= i:
            h_index = i
        else:
            break

    return success_response(
        data={
            "h_index": h_index,
            "citation_counts": citation_counts[:10],  # 只返回前10
        }
    )
