"""
模板服务 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from shared.dependencies import get_current_user_id
from shared.responses import success_response

from .models import TemplateType, TemplateStatus
from .search_service import TemplateSearchService, SearchFilter
from .recommendation import TemplateRecommendation, RecommendationContext
from .ai_filler import TemplateAIFiller, FillRequest

router = APIRouter(prefix="/api/v1/templates", tags=["写作模板"])

# 初始化服务
search_service = TemplateSearchService()
recommendation_service = TemplateRecommendation()


@router.get("", summary="搜索模板")
async def search_templates(
    q: str = Query("", description="搜索关键词"),
    type: Optional[str] = Query(None, description="模板类型"),
    institution: Optional[str] = Query(None, description="机构"),
    discipline: Optional[str] = Query(None, description="学科"),
    language: Optional[str] = Query(None, description="语言"),
    difficulty: Optional[str] = Query(None, description="难度"),
    tags: Optional[str] = Query(None, description="标签（逗号分隔）"),
    min_rating: Optional[float] = Query(None, description="最低评分"),
    sort_by: str = Query("relevance", description="排序方式"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    搜索论文模板

    - 支持关键词搜索
    - 支持多维度筛选
    - 支持多种排序方式
    """
    # 构建过滤条件
    filter = SearchFilter()
    if type:
        try:
            filter.type = TemplateType(type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的模板类型: {type}")
    filter.institution = institution
    filter.discipline = discipline
    filter.language = language
    filter.difficulty = difficulty
    if tags:
        filter.tags = tags.split(",")
    filter.min_rating = min_rating

    offset = (page - 1) * page_size

    result = await search_service.search(
        query=q,
        filter=filter,
        sort_by=sort_by,
        limit=page_size,
        offset=offset,
    )

    return success_response(data=result)


@router.get("/filters", summary="获取筛选选项")
async def get_filter_options():
    """获取可用的筛选选项列表"""
    filters = await search_service.get_filters()
    return success_response(data=filters)


@router.get("/suggestions", summary="搜索建议")
async def get_search_suggestions(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(5, ge=1, le=10),
):
    """获取搜索建议"""
    suggestions = await search_service.get_suggestions(q, limit)
    return success_response(data={"suggestions": suggestions})


@router.get("/{template_id}", summary="获取模板详情")
async def get_template(template_id: str):
    """获取模板详细信息"""
    template = await search_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return success_response(data=template.to_dict())


@router.get("/{template_id}/similar", summary="获取相似模板")
async def get_similar_templates(
    template_id: str,
    limit: int = Query(5, ge=1, le=10),
):
    """获取与指定模板相似的其他模板"""
    template = await search_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    recommendations = await recommendation_service.get_similar_templates(
        template_id=template_id,
        limit=limit,
    )

    return success_response(data={
        "items": [
            {
                "template": r.template.to_dict(),
                "score": r.score,
                "reason": r.reason,
                "confidence": r.confidence,
            }
            for r in recommendations
        ]
    })


@router.post("/recommend", summary="获取推荐模板")
async def get_recommended_templates(
    paper_title: Optional[str] = None,
    paper_abstract: Optional[str] = None,
    paper_keywords: Optional[List[str]] = None,
    target_journal: Optional[str] = None,
    discipline: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = Query(5, ge=1, le=10),
    user_id: str = Depends(get_current_user_id),
):
    """
    根据论文信息获取推荐模板

    - 基于论文标题、摘要、关键词匹配
    - 考虑目标期刊/会议要求
    - 结合用户历史偏好
    """
    context = RecommendationContext(
        user_id=user_id,
        paper_title=paper_title,
        paper_abstract=paper_abstract,
        paper_keywords=paper_keywords or [],
        target_journal=target_journal,
        discipline=discipline,
        language=language,
    )

    recommendations = await recommendation_service.recommend(
        context=context,
        limit=limit,
    )

    return success_response(data={
        "items": [
            {
                "template": r.template.to_dict(),
                "score": r.score,
                "reason": r.reason,
                "confidence": r.confidence,
            }
            for r in recommendations
        ],
        "total": len(recommendations),
    })


@router.get("/trending/list", summary="获取热门模板")
async def get_trending_templates(
    days: int = Query(7, description="统计天数"),
    limit: int = Query(10, ge=1, le=20),
):
    """获取近期热门模板趋势"""
    trending = await recommendation_service.get_trending_templates(
        days=days,
        limit=limit,
    )
    return success_response(data={"items": trending})


@router.post("/{template_id}/fill", summary="AI填充模板")
async def fill_template_with_ai(
    template_id: str,
    request: FillRequest,
    stream: bool = Query(False, description="是否流式返回"),
    user_id: str = Depends(get_current_user_id),
):
    """
    使用AI智能填充模板内容

    - 根据论文信息生成各章节内容
    - 支持流式返回
    - 提供改进建议
    """
    template = await search_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 初始化AI填充服务
    ai_filler = TemplateAIFiller()  # TODO: 注入LLM服务

    try:
        result = await ai_filler.fill_template(
            template=template,
            request=request,
            stream=stream,
        )

        # 记录使用
        await recommendation_service.record_usage(
            user_id=user_id,
            template_id=template_id,
        )

        return success_response(data={
            "template_id": result.template_id,
            "filled_sections": [
                {
                    "section_id": s.section_id,
                    "section_title": s.section_title,
                    "content": s.content,
                    "word_count": s.word_count,
                    "confidence": s.confidence,
                    "suggestions": s.suggestions,
                    "references": s.references,
                }
                for s in result.filled_sections
            ],
            "total_word_count": result.total_word_count,
            "estimated_quality": result.estimated_quality,
            "suggestions": result.suggestions,
            "generated_at": result.generated_at.isoformat(),
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI填充失败: {str(e)}")


@router.post("/{template_id}/fill-stream", summary="AI填充模板（流式）")
async def fill_template_stream(
    template_id: str,
    section_id: str,
    request: FillRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    流式AI填充单个章节

    - 实时返回生成的内容
    - 适用于长章节生成
    """
    from fastapi.responses import StreamingResponse

    template = await search_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 查找指定章节
    section = None
    for s in template.sections:
        if s.id == section_id:
            section = s
            break

    if not section:
        raise HTTPException(status_code=404, detail="章节不存在")

    ai_filler = TemplateAIFiller()

    async def generate():
        async for chunk in ai_filler.fill_section_stream(section, request, template):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "X-Template-Id": template_id,
            "X-Section-Id": section_id,
        }
    )


@router.post("/{template_id}/improve", summary="改进章节内容")
async def improve_section(
    template_id: str,
    section_content: str,
    improvement_type: str = Query(..., description="改进类型: expand/condense/clarify/formalize"),
    target_word_count: Optional[int] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    改进已有章节内容

    - expand: 扩充内容
    - condense: 精简内容
    - clarify: 澄清表达
    - formalize: 正式化语言
    """
    ai_filler = TemplateAIFiller()

    try:
        improved = await ai_filler.improve_section(
            section_content=section_content,
            improvement_type=improvement_type,
            target_word_count=target_word_count,
        )

        return success_response(data={
            "original": section_content,
            "improved": improved,
            "improvement_type": improvement_type,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"改进失败: {str(e)}")


@router.get("/{template_id}/guidance", summary="获取填充指导")
async def get_fill_guidance(template_id: str):
    """获取模板的AI填充指导信息"""
    template = await search_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    ai_filler = TemplateAIFiller()
    guidance = ai_filler.get_fill_guidance(template)

    return success_response(data=guidance)


@router.post("/{template_id}/favorite", summary="收藏模板")
async def add_favorite(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """收藏模板到个人列表"""
    template = await search_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    await recommendation_service.add_favorite(user_id, template_id)

    return success_response(message="已添加到收藏")


@router.delete("/{template_id}/favorite", summary="取消收藏")
async def remove_favorite(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """取消收藏模板"""
    await recommendation_service.remove_favorite(user_id, template_id)

    return success_response(message="已取消收藏")


@router.get("/favorites/my", summary="获取我的收藏")
async def get_my_favorites(
    user_id: str = Depends(get_current_user_id),
):
    """获取用户收藏的模板列表"""
    favorite_ids = await recommendation_service.get_favorites(user_id)

    templates = await search_service.get_templates_by_ids(favorite_ids)

    return success_response(data={
        "items": [t.to_dict() for t in templates],
        "total": len(templates),
    })


@router.post("/{template_id}/use", summary="使用模板")
async def use_template(
    template_id: str,
    paper_title: str,
    paper_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    记录使用模板创建论文

    - 增加模板使用计数
    - 添加到用户历史
    """
    template = await search_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    await recommendation_service.record_usage(
        user_id=user_id,
        template_id=template_id,
        paper_id=paper_id,
    )

    # 更新使用计数
    template.stats.usage_count += 1

    return success_response(data={
        "template_id": template_id,
        "paper_title": paper_title,
        "used_at": datetime.now().isoformat(),
    })


@router.get("/types/list", summary="获取模板类型列表")
async def get_template_types():
    """获取所有可用的模板类型"""
    types = [
        {
            "value": t.value,
            "label": {
                "thesis": "学位论文",
                "journal": "期刊论文",
                "conference": "会议论文",
                "report": "研究报告",
                "proposal": "开题报告",
                "review": "综述文章",
                "book": "书籍章节",
            }.get(t.value, t.value),
        }
        for t in TemplateType
    ]

    return success_response(data={"types": types})
