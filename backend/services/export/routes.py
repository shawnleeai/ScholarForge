"""
文档导出路由
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from shared.dependencies import get_current_user_id
from shared.responses import success_response

from .service import export_service

router = APIRouter(prefix="/api/v1/export", tags=["文档导出"])


@router.post("/literature-review/{task_id}", summary="导出文献综述")
async def export_literature_review(
    task_id: str,
    format: str = "markdown",  # markdown, docx, pdf
    user_id: str = Depends(get_current_user_id),
):
    """
    导出文献综述为指定格式

    - **task_id**: 综述生成任务ID
    - **format**: 导出格式 (markdown, docx, pdf)
    """
    # TODO: 从数据库获取综述数据
    # 这里使用模拟数据
    review_data = {
        "title": "人工智能在医疗领域的应用研究综述",
        "abstract": "本文综述了人工智能技术在医疗诊断、药物研发、健康管理等领域的应用...",
        "word_count": 3500,
        "sections": [
            {
                "title": "1. 引言",
                "content": "随着人工智能技术的快速发展，其在医疗健康领域的应用日益广泛...",
                "subsections": []
            },
            {
                "title": "2. 医疗诊断应用",
                "content": "AI在影像诊断、病理分析等方面展现出优异性能...",
                "subsections": [
                    {"title": "2.1 影像诊断", "content": "深度学习在CT、MRI影像分析中的应用..."},
                    {"title": "2.2 病理分析", "content": "计算机辅助病理诊断系统..."}
                ]
            }
        ],
        "research_gaps": ["缺乏大规模临床试验验证", "数据隐私保护机制不完善"],
        "future_directions": ["多模态数据融合", "联邦学习应用"],
        "references": [
            {"authors": ["张三", "李四"], "title": "AI医疗应用综述", "journal": "医学信息学杂志", "year": 2024},
            {"authors": ["Wang, J.", "Smith, A."], "title": "Deep Learning in Healthcare", "journal": "Nature Medicine", "year": 2023}
        ]
    }

    try:
        content = await export_service.export_literature_review(review_data, format)

        # 根据格式设置MIME类型和文件名
        mime_types = {
            "markdown": ("text/markdown", f"literature_review_{task_id[:8]}.md"),
            "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", f"literature_review_{task_id[:8]}.docx"),
            "pdf": ("application/pdf", f"literature_review_{task_id[:8]}.pdf"),
        }

        mime_type, filename = mime_types.get(format, ("text/plain", "export.txt"))

        return StreamingResponse(
            io.BytesIO(content),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/paper/{paper_id}", summary="导出论文")
async def export_paper(
    paper_id: str,
    format: str = "docx",
    user_id: str = Depends(get_current_user_id),
):
    """导出论文"""
    try:
        content = await export_service.export_paper({}, format)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=paper_{paper_id[:8]}.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
