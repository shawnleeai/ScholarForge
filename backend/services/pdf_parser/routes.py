"""
PDF 解析服务 API 路由
"""

import os
import re
import time
import shutil
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from shared.dependencies import get_current_user_id
from shared.responses import success_response

from .parser import PDFParser, PDFParseManager
from .schemas import PDFParseRequest, PDFParseResponse

router = APIRouter(prefix="/api/v1/pdf", tags=["PDF解析"])

# 全局解析管理器
parse_manager = PDFParseManager()

# 上传目录
UPLOAD_DIR = Path("./uploads/pdf")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的MIME类型
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/acrobat",
    "applications/vnd.pdf",
    "text/pdf",
    "text/x-pdf",
}


def secure_filename(filename: str) -> str:
    """
    清理文件名，防止路径遍历攻击
    """
    # 移除路径分隔符
    filename = os.path.basename(filename)
    # 只保留字母、数字、下划线、连字符和点
    filename = re.sub(r'[^\w\-.]', '_', filename)
    # 限制长度
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200 - len(ext)] + ext
    return filename


def initialize_parser(ai_service):
    """初始化PDF解析器"""
    parse_manager.initialize(ai_service=ai_service)


@router.post("/upload", summary="上传并解析PDF")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enable_ai: bool = Form(True),
    extract_references: bool = Form(True),
    extract_figures: bool = Form(False),
    user_id: str = Depends(get_current_user_id),
):
    """
    上传PDF文件并进行解析

    - **file**: PDF文件
    - **enable_ai**: 是否启用AI分析
    - **extract_references**: 是否提取参考文献
    - **extract_figures**: 是否提取图表
    """
    # 验证文件扩展名
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")

    # 验证MIME类型
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        # 某些浏览器可能不发送正确的MIME类型，所以也检查扩展名
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {content_type}。只支持PDF文件"
            )

    # 验证文件大小 (最大50MB)
    max_size = 50 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > max_size:
        raise HTTPException(status_code=400, detail="文件大小超过50MB限制")

    # 清理文件名并生成安全的存储路径
    safe_filename = secure_filename(file.filename)
    file_id = f"{uuid.uuid4().hex}_{int(time.time())}_{safe_filename}"
    file_path = UPLOAD_DIR / file_id

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    finally:
        file.file.close()

    # 提交解析任务
    try:
        task_id = await parse_manager.submit_task(
            str(file_path),
            enable_ai=enable_ai,
            extract_references=extract_references,
            extract_figures=extract_figures,
        )

        return success_response(
            data={
                "task_id": task_id,
                "file_name": file.filename,
                "file_size": file_size,
                "status": "processing",
                "message": "PDF解析任务已提交",
            },
            code=202,
        )
    except Exception as e:
        # 清理文件
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"解析任务提交失败: {str(e)}")


@router.get("/status/{task_id}", summary="查询解析状态")
async def get_parse_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """查询PDF解析任务状态"""
    task = parse_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return success_response(
        data={
            "task_id": task.task_id,
            "status": task.status,
            "file_name": task.file_name,
            "file_size": task.file_size,
            "processing_time_ms": task.processing_time_ms,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
    )


@router.get("/result/{task_id}", summary="获取解析结果")
async def get_parse_result(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """获取PDF解析完整结果"""
    task = parse_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "failed":
        return success_response(
            data={"error": task.error_message},
            message="解析失败",
            code=500,
        )

    if task.status != "completed":
        return success_response(
            data={"status": task.status},
            message="解析进行中",
            code=202,
        )

    # 返回解析结果
    content = task.content

    return success_response(
        data={
            "task_id": task.task_id,
            "status": task.status,
            "file_name": task.file_name,
            "metadata": content.metadata.dict() if content.metadata else None,
            "page_count": len(content.sections) if content.sections else 0,
            "reference_count": len(content.references) if content.references else 0,
            "figure_count": len(content.figures) if content.figures else 0,
            "ai_summary": task.ai_analysis.summary if task.ai_analysis else None,
            "ai_key_points": task.ai_analysis.key_points if task.ai_analysis else None,
            "ai_methodology": task.ai_analysis.methodology if task.ai_analysis else None,
            "sections": [{"title": s.title, "page_start": s.page_start} for s in content.sections[:10]],
            "references": [r.dict() for r in content.references[:20]],
        }
    )


@router.get("/result/{task_id}/text", summary="获取全文")
async def get_full_text(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """获取PDF完整文本"""
    task = parse_manager.get_task(task_id)

    if not task or task.status != "completed":
        raise HTTPException(status_code=404, detail="结果不存在或解析未完成")

    return success_response(
        data={
            "full_text": task.content.full_text if task.content else "",
            "sections": [
                {"title": s.title, "content": s.content}
                for s in (task.content.sections if task.content else [])
            ],
        }
    )


@router.get("/result/{task_id}/references", summary="获取参考文献")
async def get_references(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """获取提取的参考文献列表"""
    task = parse_manager.get_task(task_id)

    if not task or task.status != "completed":
        raise HTTPException(status_code=404, detail="结果不存在或解析未完成")

    return success_response(
        data={
            "total": len(task.content.references) if task.content else 0,
            "references": [r.dict() for r in (task.content.references if task.content else [])],
        }
    )


@router.delete("/tasks/{task_id}", summary="删除解析任务")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """删除解析任务和相关文件"""
    task = parse_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 删除文件
    if task.file_path and Path(task.file_path).exists():
        Path(task.file_path).unlink()

    # 从管理器中移除
    if task_id in parse_manager._tasks:
        del parse_manager._tasks[task_id]

    return success_response(message="任务已删除")


import time
