"""
AI 服务 API 路由
FastAPI 路由定义
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from shared.responses import success_response
from shared.dependencies import get_current_user_id
from shared.config import settings

from .schemas import (
    WritingRequest,
    WritingResponse,
    WritingTaskType,
    ContinueWritingRequest,
    PolishRequest,
    TranslateRequest,
    TranslateResponse,
    QARequest,
    QAResponse,
    ChartGenerationRequest,
    ChartGenerationResponse,
)
from .llm_provider import LLMService
from .writing_assistant import WritingAssistant

router = APIRouter(prefix="/api/v1/ai", tags=["AI写作助手"])

# 初始化服务
llm_service = LLMService(
    openai_key=settings.openai_api_key,
    anthropic_key=settings.anthropic_api_key,
)
writing_assistant = WritingAssistant(llm_service)


# ============== 写作助手路由 ==============

@router.post("/writing", summary="统一写作接口")
async def writing_task(
    request: WritingRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    统一写作接口

    支持的任务类型：
    - continue: 续写
    - rewrite: 改写
    - polish: 润色
    - expand: 扩写
    - summarize: 总结
    - translate: 翻译
    """
    result = ""
    suggestions = []

    if request.task_type == WritingTaskType.CONTINUE:
        result = await writing_assistant.continue_writing(
            context=request.text or request.context or "",
            max_tokens=request.max_tokens,
        )

    elif request.task_type == WritingTaskType.POLISH:
        result = await writing_assistant.polish_text(
            text=request.text or "",
        )

    elif request.task_type == WritingTaskType.REWRITE:
        result = await writing_assistant.rewrite_text(
            text=request.text or "",
        )

    elif request.task_type == WritingTaskType.EXPAND:
        result = await writing_assistant.expand_text(
            text=request.text or "",
            target_length=request.max_tokens,
        )

    elif request.task_type == WritingTaskType.SUMMARIZE:
        result = await writing_assistant.summarize_text(
            text=request.text or "",
        )

    elif request.task_type == WritingTaskType.TRANSLATE:
        result = await writing_assistant.translate(
            text=request.text or "",
            source_language=request.source_language or "zh",
            target_language=request.target_language or "en",
        )

    return success_response(
        data=WritingResponse(
            generated_text=result,
            task_type=request.task_type,
            provider="openai",  # 实际应从调用结果获取
            tokens_used=len(result),  # 模拟
            suggestions=suggestions,
        ).model_dump()
    )


@router.post("/writing/continue", summary="智能续写")
async def continue_writing(
    request: ContinueWritingRequest,
    user_id: str = Depends(get_current_user_id),
):
    """根据前文内容智能续写"""
    result = await writing_assistant.continue_writing(
        context=request.context,
        style=request.style,
        max_tokens=request.max_tokens,
    )

    return success_response(
        data={
            "generated_text": result,
            "style": request.style,
        }
    )


@router.post("/writing/polish", summary="文本润色")
async def polish_text(
    request: PolishRequest,
    user_id: str = Depends(get_current_user_id),
):
    """对文本进行学术润色"""
    result = await writing_assistant.polish_text(
        text=request.text,
        style=request.style,
        language=request.language,
    )

    return success_response(
        data={
            "original_text": request.text,
            "polished_text": result,
        }
    )


@router.post("/writing/translate", summary="翻译")
async def translate_text(
    request: TranslateRequest,
    user_id: str = Depends(get_current_user_id),
):
    """学术文本翻译"""
    result = await writing_assistant.translate(
        text=request.text,
        source_language=request.source_language,
        target_language=request.target_language,
    )

    return success_response(
        data=TranslateResponse(
            translated_text=result,
            source_language=request.source_language,
            target_language=request.target_language,
        ).model_dump()
    )


@router.post("/writing/outline", summary="生成大纲")
async def generate_outline(
    topic: str,
    paper_type: str = "thesis",
    language: str = "zh",
    user_id: str = Depends(get_current_user_id),
):
    """根据主题生成论文大纲"""
    outline = await writing_assistant.generate_outline(
        topic=topic,
        paper_type=paper_type,
        language=language,
    )

    return success_response(
        data={
            "topic": topic,
            "outline": outline,
        }
    )


@router.post("/writing/check-logic", summary="逻辑检查")
async def check_logic(
    text: str,
    language: str = "zh",
    user_id: str = Depends(get_current_user_id),
):
    """检查文本的逻辑连贯性"""
    result = await writing_assistant.check_logic(
        text=text,
        language=language,
    )

    return success_response(data=result)


# ============== 智能问答路由 ==============

@router.post("/qa", summary="智能问答")
async def question_answer(
    request: QARequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    学术智能问答

    可以针对特定论文或一般学术问题进行提问
    """
    # 构建上下文
    context = request.context or ""
    if request.paper_id:
        context += f"\n[论文ID: {request.paper_id}]"

    prompt = f"""请回答以下学术问题：

问题：{request.question}

{f'相关上下文：{context}' if context else ''}

请提供专业、准确的回答："""

    result, provider = await llm_service.generate(
        prompt=prompt,
        max_tokens=1000,
        temperature=0.5,
        system_prompt=writing_assistant.SYSTEM_PROMPTS["academic_zh"],
    )

    return success_response(
        data=QAResponse(
            answer=result,
            confidence=0.85,
            sources=[],
        ).model_dump()
    )


# ============== 图表生成路由 ==============

@router.post("/chart/generate", summary="图表生成")
async def generate_chart(
    request: ChartGenerationRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    根据数据生成图表配置

    返回 ECharts 配置和可选的代码片段
    """
    # 这里简化处理，实际应该使用AI生成图表配置
    chart_config = {
        "title": {
            "text": request.title or "数据图表",
            "left": "center",
        },
        "tooltip": {
            "trigger": "axis" if request.chart_type in ["bar", "line"] else "item",
        },
        "legend": {
            "data": [],
            "top": "bottom",
        },
        "xAxis": {
            "type": "category",
            "data": [item.get(request.x_axis or "name", str(i)) for i, item in enumerate(request.data)],
        } if request.chart_type in ["bar", "line"] else None,
        "yAxis": {
            "type": "value",
        } if request.chart_type in ["bar", "line"] else None,
        "series": [{
            "name": request.y_axis or "value",
            "type": request.chart_type,
            "data": [item.get(request.y_axis or "value", 0) for item in request.data],
        }],
    }

    # 生成Python代码
    code_snippet = f'''import matplotlib.pyplot as plt
import pandas as pd

# 数据
data = {request.data}

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar([d.get("{request.x_axis or 'name'}", str(i)) for i, d in enumerate(data)],
       [d.get("{request.y_axis or 'value'}", 0) for d in data])
ax.set_title("{request.title or '数据图表'}")
ax.set_xlabel("{request.x_axis or 'Category'}")
ax.set_ylabel("{request.y_axis or 'Value'}")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("chart.png")
plt.show()
'''

    return success_response(
        data=ChartGenerationResponse(
            chart_config=chart_config,
            code_snippet=code_snippet,
            description=f"已生成{request.chart_type}类型图表配置",
        ).model_dump()
    )


# ============== 文献分析路由 ==============

@router.post("/analyze/article", summary="文献分析")
async def analyze_article(
    article_id: uuid.UUID,
    analysis_type: str = "full",
    user_id: str = Depends(get_current_user_id),
):
    """
    智能分析文献

    分析类型：
    - full: 完整分析
    - methodology: 方法论分析
    - findings: 发现分析
    - references: 参考文献分析
    """
    # 模拟分析结果
    # 实际应该从文献服务获取文章内容，然后使用AI分析

    result = {
        "article_id": str(article_id),
        "research_background": "本文研究了人工智能在项目管理中的应用...",
        "core_findings": [
            "发现1: AI技术显著提升项目效率",
            "发现2: 协同机制是关键因素",
            "发现3: 人机协作模式需要优化",
        ],
        "methodology": "采用混合研究方法，结合定量分析与案例研究...",
        "key_figures": [
            "图1: 研究框架",
            "图2: 数据分析结果",
        ],
        "writing_suggestions": [
            "可以借鉴其研究框架设计",
            "方法论部分值得参考",
            "数据分析方法可以借鉴",
        ],
    }

    return success_response(data=result)
