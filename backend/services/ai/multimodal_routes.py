"""
Multimodal API Routes
多模态功能API路由 - 视频生成、虚拟导师、知识图谱
"""

from typing import Optional, Literal
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from .virtual_advisor_v2 import get_virtual_advisor_v2, AdvisorConfig, AdvisorPersonality, ReviewFocus
from .video_abstract_service import get_video_abstract_service
from ..knowledge_graph.multimodal_knowledge_graph import get_multimodal_kg

router = APIRouter(prefix="/multimodal", tags=["multimodal"])


# ==================== 虚拟导师V2 ====================

@router.post("/advisor/session")
async def create_advisor_session(
    user_id: str = Form(...),
    paper_id: Optional[str] = Form(None),
    personality: str = Form("balanced"),
    focus_areas: str = Form("comprehensive"),  # 逗号分隔
    voice_enabled: bool = Form(True),
    strictness_level: int = Form(5)
):
    """创建导师会话"""
    advisor = get_virtual_advisor_v2()

    # 解析关注点
    focus_list = [f.strip() for f in focus_areas.split(",")]
    focus_enums = [ReviewFocus(f) for f in focus_list if f in [e.value for e in ReviewFocus]]

    config = AdvisorConfig(
        personality=AdvisorPersonality(personality),
        focus_areas=focus_enums or [ReviewFocus.COMPREHENSIVE],
        voice_enabled=voice_enabled,
        strictness_level=strictness_level
    )

    session = advisor.create_session(user_id, paper_id, config)

    return {
        "session_id": session.id,
        "config": {
            "personality": config.personality.value,
            "focus_areas": [f.value for f in config.focus_areas],
            "voice_enabled": config.voice_enabled
        },
        "created_at": session.start_time.isoformat()
    }


@router.post("/advisor/{session_id}/review")
async def review_paper(
    session_id: str,
    paper_content: str = Form(...),
    review_type: Literal["quick", "detailed", "deep"] = Form("detailed")
):
    """审阅论文"""
    advisor = get_virtual_advisor_v2()

    try:
        result = await advisor.review_paper(session_id, paper_content, review_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/advisor/{session_id}/chat")
async def advisor_chat(
    session_id: str,
    message: str = Form(...),
    paper_context: str = Form("")
):
    """导师对话"""
    advisor = get_virtual_advisor_v2()

    try:
        response = await advisor.chat(session_id, message, paper_context)
        return {
            "session_id": session_id,
            "user_message": message,
            "advisor_response": response
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/advisor/{session_id}/voice-chat")
async def advisor_voice_chat(
    session_id: str,
    audio: UploadFile = File(...),
    paper_context: str = Form("")
):
    """语音对话"""
    advisor = get_virtual_advisor_v2()

    audio_data = await audio.read()

    try:
        result = await advisor.voice_chat(session_id, audio_data, paper_context)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {
            "user_text": result["user_text"],
            "advisor_response": result["advisor_response"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/advisor/{session_id}/mock-defense")
async def generate_mock_defense(
    session_id: str,
    paper_content: str = Form(...),
    num_questions: int = Form(10)
):
    """生成模拟答辩问题"""
    advisor = get_virtual_advisor_v2()

    try:
        questions = await advisor.generate_mock_defense_questions(
            paper_content, num_questions
        )
        return {
            "session_id": session_id,
            "num_questions": len(questions),
            "questions": questions
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/advisor/{session_id}")
async def close_advisor_session(session_id: str):
    """关闭会话"""
    advisor = get_virtual_advisor_v2()
    summary = advisor.close_session(session_id)

    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")

    return summary


# ==================== 视频摘要 ====================

@router.get("/video/templates")
async def get_video_templates():
    """获取视频模板"""
    service = get_video_abstract_service()
    return {"templates": service.get_available_templates()}


@router.post("/video/generate-script")
async def generate_video_script(
    title: str = Form(...),
    abstract: str = Form(...),
    authors: str = Form(...),
    keywords: str = Form(...),
    template_id: str = Form("academic"),
    target_audience: str = Form("experts")
):
    """生成视频脚本"""
    service = get_video_abstract_service()

    paper_data = {
        "title": title,
        "abstract": abstract,
        "authors": authors.split(","),
        "keywords": keywords.split(",")
    }

    script = await service.generate_script(
        paper_data=paper_data,
        template_id=template_id,
        target_audience=target_audience
    )

    return script


@router.post("/video/generate")
async def generate_video_abstract(
    title: str = Form(...),
    abstract: str = Form(...),
    authors: str = Form(...),
    keywords: str = Form(...),
    template_id: str = Form("academic"),
    generate_audio: bool = Form(True),
    generate_video: bool = Form(True)
):
    """生成视频摘要"""
    service = get_video_abstract_service()

    paper_data = {
        "id": f"paper_{hash(title) % 1000000}",
        "title": title,
        "abstract": abstract,
        "authors": authors.split(","),
        "keywords": keywords.split(",")
    }

    video_abstract = await service.generate_video_abstract(
        paper_data=paper_data,
        template_id=template_id,
        generate_audio=generate_audio,
        generate_video=generate_video
    )

    return {
        "paper_id": video_abstract.paper_id,
        "status": video_abstract.status,
        "script": video_abstract.script,
        "audio_url": video_abstract.audio_url,
        "video_url": video_abstract.video_url,
        "created_at": video_abstract.created_at.isoformat()
    }


@router.post("/video/slides")
async def generate_slide_deck(
    title: str = Form(...),
    abstract: str = Form(...),
    methodology: str = Form(""),
    results: str = Form(""),
    num_slides: int = Form(10)
):
    """生成演示幻灯片"""
    service = get_video_abstract_service()

    paper_data = {
        "title": title,
        "abstract": abstract,
        "methodology": methodology,
        "results": results
    }

    slides = await service.generate_slide_deck(paper_data, num_slides)
    return {"slides": slides}


# ==================== 多模态知识图谱 ====================

@router.post("/knowledge/extract-figure")
async def extract_figure_knowledge(
    figure: UploadFile = File(...),
    caption: str = Form(...),
    paper_context: str = Form("")
):
    """从图表抽取知识"""
    kg = get_multimodal_kg()

    figure_data = await figure.read()

    result = await kg.extract_from_figure(
        figure_image=figure_data,
        caption=caption,
        paper_context=paper_context
    )

    return result


@router.post("/knowledge/build")
async def build_multimodal_graph(
    paper_id: str = Form(...),
    title: str = Form(...),
    abstract: str = Form(...),
    content: str = Form(""),
    year: int = Form(...),
    venue: str = Form("")
):
    """构建多模态知识图谱"""
    kg = get_multimodal_kg()

    paper_data = {
        "id": paper_id,
        "title": title,
        "abstract": abstract,
        "content": content,
        "year": year,
        "venue": venue
    }

    result = await kg.build_multimodal_graph(paper_data)
    return result


@router.get("/knowledge/similar-methods/{method_name}")
async def find_similar_methods(method_name: str, limit: int = 10):
    """查找相似方法"""
    kg = get_multimodal_kg()
    methods = kg.find_similar_methods(method_name, limit)
    return {"methods": methods}


@router.get("/knowledge/method-evolution/{concept}")
async def get_method_evolution(concept: str):
    """获取方法演进"""
    kg = get_multimodal_kg()
    evolution = kg.get_method_evolution(concept)
    return {"evolution": evolution}
