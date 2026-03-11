"""
AI 服务 API 路由
FastAPI 路由定义
"""

import json
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

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
    deepseek_key=settings.deepseek_api_key if hasattr(settings, 'deepseek_api_key') else None,
    moonshot_key=settings.moonshot_api_key if hasattr(settings, 'moonshot_api_key') else None,
    stepfun_key=settings.stepfun_api_key if hasattr(settings, 'stepfun_api_key') else None,
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


# ============== AI 服务管理路由 ==============

@router.get("/health", summary="AI 服务健康检查")
async def check_ai_health(
    user_id: str = Depends(get_current_user_id),
):
    """
    检查所有 AI 提供商的健康状态

    返回各提供商的状态、延迟和可用模型
    """
    health_results = await llm_service.check_all_health()

    return success_response(
        data={
            "providers": [
                {
                    "name": h.provider,
                    "status": h.status.value,
                    "latency_ms": h.latency_ms,
                    "error": h.error_message,
                    "supported_models": h.supported_models,
                    "checked_at": h.last_checked.isoformat(),
                }
                for h in health_results
            ],
            "available_providers": llm_service.get_available_providers(),
            "default_provider": llm_service.default_provider,
        }
    )


@router.get("/usage", summary="AI 使用统计")
async def get_usage_stats(
    user_id: str = Depends(get_current_user_id),
):
    """
    获取 AI 服务使用统计

    包括 Token 使用量和成本估算
    """
    report = llm_service.get_usage_report()

    return success_response(
        data={
            "total_tokens": report["total_tokens"],
            "total_cost_usd": round(report["total_cost_usd"], 6),
            "total_cost_cny": round(report["total_cost_usd"] * 7.2, 4),  # 估算人民币
            "providers": report["providers"],
        }
    )


@router.post("/stream", summary="流式生成文本")
async def stream_generate(
    prompt: str,
    max_tokens: int = 500,
    temperature: float = 0.7,
    provider: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    流式生成文本（SSE）

    用于实时显示 AI 生成进度
    """
    from fastapi.responses import StreamingResponse

    async def event_generator():
        async for chunk in llm_service.generate_stream(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            provider=provider,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.post("/batch", summary="批量生成")
async def batch_generate(
    prompts: List[str],
    max_tokens: int = 500,
    temperature: float = 0.7,
    provider: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    批量生成文本

    同时处理多个提示，提高效率
    """
    import asyncio

    tasks = [
        llm_service.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            provider=provider,
        )
        for prompt in prompts
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return success_response(
        data={
            "results": [
                {
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "content": r.content if isinstance(r, Exception) == False else str(r),
                    "provider": r.provider if isinstance(r, Exception) == False else "error",
                    "tokens": r.usage.total_tokens if isinstance(r, Exception) == False else 0,
                }
                for prompt, r in zip(prompts, results)
            ],
            "total_prompts": len(prompts),
            "successful": sum(1 for r in results if isinstance(r, Exception) == False and r.finish_reason != "error"),
        }
    )


# ============== AI 问答对话系统路由 ==============

from fastapi import Query, Path
from fastapi.responses import StreamingResponse
from .conversation_models import (
    Conversation,
    ConversationContext,
    Message,
    ConversationStatus,
    MessageRole,
    MessageType,
    Citation,
)
from .conversation_service import ConversationService, get_conversation_service
from .rag_engine import RAGEngine, get_rag_engine

# 初始化服务
conversation_service = get_conversation_service()
rag_engine = get_rag_engine(llm_service=llm_service)


class CreateConversationRequest(BaseModel):
    """创建会话请求"""
    title: Optional[str] = None
    context: Optional[dict] = None
    metadata: Optional[dict] = None


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str
    parent_id: Optional[str] = None
    use_rag: bool = True
    stream: bool = False


@router.post("/chat", summary="创建对话会话")
async def create_conversation(
    request: CreateConversationRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    创建新的AI问答对话会话

    - 可以指定初始标题
    - 可以设置关联的论文和文献
    - 可以设置研究领域和问题
    """
    # 构建上下文
    context = None
    if request.context:
        context = ConversationContext.from_dict(request.context)

    conversation = await conversation_service.create_conversation(
        user_id=user_id,
        title=request.title,
        context=context,
        metadata=request.metadata or {},
    )

    return success_response(
        data={
            "conversation": conversation.to_dict(include_messages=False),
            "message": "会话创建成功",
        }
    )


@router.get("/chat", summary="获取会话列表")
async def list_conversations(
    status: Optional[str] = Query(None, description="筛选状态: active, archived, deleted"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="搜索关键词"),
    user_id: str = Depends(get_current_user_id),
):
    """
    获取用户的对话会话列表

    - 支持分页
    - 支持状态筛选
    - 支持关键词搜索
    """
    status_enum = None
    if status:
        try:
            status_enum = ConversationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

    result = await conversation_service.list_conversations(
        user_id=user_id,
        status=status_enum,
        limit=limit,
        offset=offset,
        search_query=search,
    )

    return success_response(data=result)


@router.get("/chat/{conversation_id}", summary="获取对话详情")
async def get_conversation(
    conversation_id: str = Path(..., description="会话ID"),
    include_messages: bool = Query(True, description="是否包含消息列表"),
    user_id: str = Depends(get_current_user_id),
):
    """
    获取对话会话详情

    - 包含会话元数据
    - 可选包含完整消息历史
    - 包含关联的上下文信息
    """
    try:
        conversation = await conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            include_messages=include_messages,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except ConversationAccessError:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    return success_response(
        data={
            "conversation": conversation.to_dict(include_messages=include_messages),
        }
    )


@router.put("/chat/{conversation_id}", summary="更新对话")
async def update_conversation(
    conversation_id: str = Path(..., description="会话ID"),
    title: Optional[str] = None,
    context: Optional[dict] = None,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    更新对话会话

    - 修改标题
    - 更新上下文（关联的论文、文献等）
    - 更改状态（归档等）
    """
    status_enum = None
    if status:
        try:
            status_enum = ConversationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

    conv_context = None
    if context:
        conv_context = ConversationContext.from_dict(context)

    try:
        conversation = await conversation_service.update_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title,
            context=conv_context,
            status=status_enum,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except ConversationAccessError:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    return success_response(
        data={
            "conversation": conversation.to_dict(include_messages=False),
            "message": "会话更新成功",
        }
    )


@router.delete("/chat/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: str = Path(..., description="会话ID"),
    soft_delete: bool = Query(True, description="是否软删除"),
    user_id: str = Depends(get_current_user_id),
):
    """
    删除对话会话

    - 默认软删除（可恢复）
    - 可选硬删除
    """
    try:
        await conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            soft_delete=soft_delete,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except ConversationAccessError:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    return success_response(
        data={"message": "会话已删除", "soft_delete": soft_delete}
    )


@router.post("/chat/{conversation_id}/message", summary="发送消息")
async def send_message(
    conversation_id: str = Path(..., description="会话ID"),
    content: str = Query(..., description="消息内容"),
    use_rag: bool = Query(True, description="是否使用RAG检索"),
    stream: bool = Query(False, description="是否流式响应"),
    user_id: str = Depends(get_current_user_id),
):
    """
    向对话发送消息并获取AI回复

    - 支持普通响应和流式响应
    - 可选使用RAG检索增强
    - 自动保存消息历史
    """
    try:
        conversation = await conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except ConversationAccessError:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    # 创建用户消息
    user_message = Message.create_user_message(
        conversation_id=conversation_id,
        content=content,
    )
    await conversation_service.add_message(
        conversation_id=conversation_id,
        message=user_message,
        auto_update_title=True,
    )

    if stream:
        # 流式响应
        async def stream_generator():
            # 使用RAG生成带引用的回答
            if use_rag:
                result = await rag_engine.generate_answer(
                    query=content,
                    context=conversation.context,
                    conversation_history=conversation.get_last_n_messages(5),
                    stream=True,
                )
                async for chunk in result:
                    data = {
                        "chunk": chunk.get("chunk", ""),
                        "is_final": chunk.get("is_final", False),
                    }
                    if chunk.get("citations"):
                        data["citations"] = chunk.get("citations")
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            else:
                # 直接LLM生成
                prompt = f"请回答以下学术问题：\n\n{content}"
                async for chunk in llm_service.generate_stream(
                    prompt=prompt,
                    max_tokens=2000,
                    temperature=0.3,
                ):
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
        )
    else:
        # 非流式响应
        if use_rag:
            result = await rag_engine.generate_answer(
                query=content,
                context=conversation.context,
                conversation_history=conversation.get_last_n_messages(5),
            )
            answer_content = result["answer"]
            citations = [Citation(**c) for c in result.get("citations", [])]
            metadata = {
                "retrieval_info": result.get("retrieval_info"),
                "generation_time_ms": result.get("generation_time_ms"),
            }
        else:
            # 直接LLM生成
            prompt = f"请回答以下学术问题：\n\n{content}"
            answer, _ = await llm_service.generate(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3,
            )
            answer_content = answer.content if hasattr(answer, 'content') else str(answer)
            citations = []
            metadata = {}

        # 创建助手消息
        assistant_message = Message.create_assistant_message(
            conversation_id=conversation_id,
            content=answer_content,
            citations=citations,
            metadata=metadata,
        )
        await conversation_service.add_message(
            conversation_id=conversation_id,
            message=assistant_message,
        )

        return success_response(
            data={
                "message": assistant_message.to_dict(),
                "conversation_id": conversation_id,
            }
        )


@router.get("/chat/{conversation_id}/messages", summary="获取消息历史")
async def get_messages(
    conversation_id: str = Path(..., description="会话ID"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    role: Optional[str] = Query(None, description="按角色筛选: user, assistant, system"),
    user_id: str = Depends(get_current_user_id),
):
    """
    获取对话的消息历史

    - 支持分页
    - 支持按角色筛选
    - 按时间顺序排列
    """
    role_enum = None
    if role:
        try:
            role_enum = MessageRole(role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的角色: {role}")

    try:
        messages = await conversation_service.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
            role=role_enum,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except ConversationAccessError:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    return success_response(
        data={
            "messages": [m.to_dict() for m in messages],
            "total": len(messages),
            "limit": limit,
            "offset": offset,
        }
    )


@router.delete("/chat/{conversation_id}/messages/{message_id}", summary="删除消息")
async def delete_message(
    conversation_id: str = Path(..., description="会话ID"),
    message_id: str = Path(..., description="消息ID"),
    user_id: str = Depends(get_current_user_id),
):
    """
    删除单条消息
    """
    try:
        await conversation_service.delete_message(
            conversation_id=conversation_id,
            message_id=message_id,
            user_id=user_id,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except ConversationAccessError:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    return success_response(data={"message": "消息已删除"})


@router.put("/chat/{conversation_id}/context", summary="更新对话上下文")
async def update_context(
    conversation_id: str = Path(..., description="会话ID"),
    paper_ids: Optional[List[str]] = None,
    article_ids: Optional[List[str]] = None,
    research_field: Optional[str] = None,
    research_question: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    更新对话的上下文信息

    - 关联论文
    - 关联文献
    - 设置研究领域
    - 设置研究问题
    """
    try:
        context = await conversation_service.update_context(
            conversation_id=conversation_id,
            user_id=user_id,
            paper_ids=paper_ids,
            article_ids=article_ids,
            research_field=research_field,
            research_question=research_question,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except ConversationAccessError:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    return success_response(
        data={
            "context": context.to_dict(),
            "message": "上下文已更新",
        }
    )


# 导入异常类
from .conversation_service import ConversationNotFoundError, ConversationAccessError
