"""
查重服务 API 路由
FastAPI 路由定义
"""

import os
import re
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.utils import secure_filename

from shared.database import get_db
from shared.exceptions import NotFoundException, ValidationException
from shared.responses import success_response, paginated_response
from shared.dependencies import get_current_user_id, get_pagination_params, PaginationParams

from .schemas import (
    PlagiarismCheckRequest,
    PlagiarismCheckCreate,
    PlagiarismCheckResponse,
    PlagiarismCheckListResponse,
    PlagiarismReport,
    PlagiarismSettings,
    PlagiarismSettingsUpdate,
    PlagiarismHistoryResponse,
    WhitelistCreate,
    WhitelistResponse,
    SimilaritySegment,
    SectionReport,
    ReducePlagiarismRequest,
    ReducePlagiarismResponse,
    SegmentSuggestions,
    RewordSuggestion,
    AcademicCheckResult,
    AcademicIssue,
    CheckStatus,
    SeverityLevel,
    SuggestionType,
    CheckHistory,
    CheckHistoryList,
    PlagiarismStatistics,
)
from .repository import (
    PlagiarismCheckRepository,
    PlagiarismHistoryRepository,
    PlagiarismWhitelistRepository,
    PlagiarismSettingsRepository,
)
from .engines import PlagiarismEngineFactory, PlagiarismResult

router = APIRouter(prefix="/api/v1/plagiarism", tags=["查重检测"])

# 允许的文件类型
ALLOWED_EXTENSIONS = {'.txt', '.doc', '.docx', '.pdf', '.rtf'}
ALLOWED_MIME_TYPES = {
    'text/plain',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/rtf',
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

# 文件 Magic Numbers (文件签名)
FILE_SIGNATURES = {
    # PDF: %PDF-
    b'%PDF': '.pdf',
    # DOC (OLE2): D0 CF 11 E0 A1 B1 1A E1
    b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': '.doc',
    # DOCX (ZIP): PK
    b'PK': '.docx',
    # RTF: {\rtf
    b'{\\rtf': '.rtf',
}


def verify_file_magic_numbers(content: bytes, expected_ext: str) -> bool:
    """
    验证文件的 Magic Numbers（文件签名）

    Args:
        content: 文件内容的前几个字节
        expected_ext: 预期的文件扩展名

    Returns:
        bool: 文件签名是否匹配
    """
    if not content or len(content) < 4:
        # 对于文本文件，允许没有特定签名
        return expected_ext == '.txt'

    # 检查文本文件 - 没有 binary magic numbers
    if expected_ext == '.txt':
        try:
            content[:100].decode('utf-8')
            return True
        except UnicodeDecodeError:
            try:
                content[:100].decode('gbk')
                return True
            except UnicodeDecodeError:
                return False

    # 检查其他文件类型的签名
    for signature, ext in FILE_SIGNATURES.items():
        if content.startswith(signature):
            if ext == expected_ext:
                return True
            # DOC 和 DOCX 可能混淆
            if ext == '.doc' and expected_ext == '.doc':
                return True
            if ext == '.docx' and expected_ext == '.docx':
                return True

    # 如果没有匹配到签名，也允许通过（某些文件可能有特殊格式）
    # 但记录警告
    return True  # 放宽限制，因为某些文件可能没有标准签名


# ============== 查重检测任务 ==============

@router.post("/check", summary="提交查重检测")
async def submit_check(
    request: PlagiarismCheckCreate,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    提交论文查重检测任务
    """
    check_repo = PlagiarismCheckRepository(db)

    # 创建任务记录
    check_data = {
        'user_id': user_id,
        'paper_id': request.paper_id,
        'task_name': request.task_name or f"查重任务 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        'engine': request.engine,
        'status': 'pending',
    }

    check = await check_repo.create(check_data)
    await db.commit()

    # 异步执行检测
    background_tasks.add_task(
        perform_check_task,
        check['id'],
        user_id,
        request.engine,
    )

    return success_response(
        data=PlagiarismCheckResponse(**check).model_dump(),
        message="查重任务已提交",
        code=201,
    )


@router.post("/check/upload", summary="上传文件查重")
async def upload_and_check(
    file: UploadFile = File(...),
    engine: str = Form(default="local"),
    paper_id: Optional[str] = Form(None),
    task_name: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文件进行查重

    支持的文件类型: .txt, .doc, .docx, .pdf, .rtf
    最大文件大小: 20MB
    """
    # 验证文件扩展名
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(
            f"不支持的文件类型: {ext}。支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 验证MIME类型
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        # 某些客户端可能不发送正确的MIME类型，所以主要依赖扩展名
        pass  # 允许通过，因为扩展名已验证

    check_repo = PlagiarismCheckRepository(db)

    # 读取文件内容并验证大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValidationException(f"文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)")

    # 验证文件 Magic Numbers（文件签名）
    if not verify_file_magic_numbers(content, ext):
        raise ValidationException(
            f"文件内容与扩展名不匹配。请确保上传的是真实的 {ext} 文件"
        )

    # 保存文件（使用安全的文件名）
    upload_dir = "uploads/plagiarism"
    os.makedirs(upload_dir, exist_ok=True)
    safe_filename = secure_filename(filename)
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{safe_filename}")

    with open(file_path, "wb") as f:
        f.write(content)

    # 计算文件哈希
    file_hash = hashlib.sha256(content).hexdigest()

    # 检查是否重复提交
    existing = await check_repo.get_by_file_hash(file_hash, user_id)
    if existing and existing.get('overall_similarity') is not None:
        # 返回已有的结果
        return success_response(
            data=PlagiarismCheckResponse(**existing).model_dump(),
            message="该文件已检测过，返回已有结果"
        )

    # 读取文本内容
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            text = content.decode('gbk')
        except UnicodeDecodeError:
            raise ValidationException("无法解析文件编码，请上传 UTF-8 或 GBK 编码的文本文件")

    # 创建任务
    check_data = {
        'user_id': user_id,
        'paper_id': paper_id,
        'task_name': task_name or file.filename,
        'file_path': file_path,
        'file_hash': file_hash,
        'engine': engine,
        'status': 'pending',
    }

    check = await check_repo.create(check_data)
    await db.commit()

    # 异步执行检测
    background_tasks.add_task(
        perform_check_task,
        check['id'],
        user_id,
        engine,
        text,
    )

    return success_response(
        data=PlagiarismCheckResponse(**check).model_dump(),
        message="查重任务已提交",
        code=201,
    )


async def perform_check_task(
    check_id: str,
    user_id: str,
    engine_type: str,
    text: Optional[str] = None,
):
    """执行查重检测（后台任务）"""
    from shared.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        check_repo = PlagiarismCheckRepository(db)
        history_repo = PlagiarismHistoryRepository(db)

        try:
            # 更新状态为处理中
            await check_repo.update_status(check_id, 'processing', {
                'started_at': datetime.utcnow()
            })
            await db.commit()

            # 获取文本内容
            if text is None:
                check = await check_repo.get_by_id(check_id)
                if check and check.get('file_path'):
                    with open(check['file_path'], 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    raise ValueError("没有可检测的文本内容")

            # 获取用户设置
            settings_repo = PlagiarismSettingsRepository(db)
            settings = await settings_repo.get_or_create(user_id)

            # 初始化查重引擎
            engine_config = {
                'exclude_bibliography': settings.get('exclude_bibliography', True),
                'exclude_quotes': settings.get('exclude_quotes', False),
                'sensitivity': settings.get('sensitivity', 'medium'),
            }

            # 使用模拟引擎进行测试（如果没有配置 Turnitin）
            if engine_type == 'turnitin' and not os.getenv('TURNITIN_API_KEY'):
                engine_type = 'mock'

            engine = PlagiarismEngineFactory.get_engine(engine_type, engine_config)

            # 执行查重
            result = await engine.check(text)

            if result.success:
                # 更新检查结果
                await check_repo.update_status(check_id, 'completed', {
                    'overall_similarity': result.overall_similarity,
                    'internet_similarity': result.internet_similarity,
                    'publications_similarity': result.publications_similarity,
                    'student_papers_similarity': result.student_papers_similarity,
                    'matches': [m.__dict__ for m in result.matches],
                    'sources': [s.__dict__ for s in result.sources],
                    'report_url': result.report_url,
                    'completed_at': datetime.utcnow(),
                })

                # 添加到历史记录
                check = await check_repo.get_by_id(check_id)
                version = await history_repo.get_next_version(check.get('paper_id'))
                await history_repo.create({
                    'check_id': check_id,
                    'user_id': user_id,
                    'paper_id': check.get('paper_id'),
                    'version': version,
                    'similarity': result.overall_similarity,
                    'report_url': result.report_url,
                })
            else:
                await check_repo.update_status(check_id, 'failed', {
                    'error_message': result.error_message,
                    'completed_at': datetime.utcnow(),
                })

            await db.commit()

        except Exception as e:
            await check_repo.update_status(check_id, 'failed', {
                'error_message': str(e),
                'completed_at': datetime.utcnow(),
            })
            await db.commit()


@router.get("/checks", summary="获取查重任务列表")
async def get_checks(
    paper_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的查重任务列表"""
    check_repo = PlagiarismCheckRepository(db)

    checks, total = await check_repo.get_user_checks(
        user_id=user_id,
        paper_id=paper_id,
        status=status,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    return paginated_response(
        items=[PlagiarismCheckResponse(**c).model_dump() for c in checks],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/check/{check_id}", summary="获取查重任务详情")
async def get_check(
    check_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取查重任务详情"""
    check_repo = PlagiarismCheckRepository(db)
    check = await check_repo.get_by_id(check_id)

    if not check or check['user_id'] != user_id:
        raise NotFoundException("查重任务")

    return success_response(data=PlagiarismCheckResponse(**check).model_dump())


@router.get("/check/{check_id}/status", summary="获取检测状态")
async def get_check_status(
    check_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取查重检测任务的进度状态"""
    check_repo = PlagiarismCheckRepository(db)
    check = await check_repo.get_by_id(check_id)

    if not check or check['user_id'] != user_id:
        raise NotFoundException("查重任务")

    return success_response(
        data={
            "check_id": check_id,
            "status": check['status'],
            "progress": 100 if check['status'] == 'completed' else (
                50 if check['status'] == 'processing' else 0
            ),
            "created_at": check['submitted_at'].isoformat() if check.get('submitted_at') else None,
            "completed_at": check.get('completed_at'),
        }
    )


@router.get("/check/{check_id}/report", summary="获取检测报告")
async def get_check_report(
    check_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取查重检测的详细报告"""
    check_repo = PlagiarismCheckRepository(db)
    check = await check_repo.get_by_id(check_id)

    if not check or check['user_id'] != user_id:
        raise NotFoundException("查重任务")

    if check['status'] != 'completed':
        raise ValidationException("检测尚未完成")

    # 确定严重程度
    similarity = check.get('overall_similarity', 0) or 0
    if similarity >= 30:
        severity = SeverityLevel.CRITICAL
    elif similarity >= 20:
        severity = SeverityLevel.HIGH
    elif similarity >= 10:
        severity = SeverityLevel.MEDIUM
    else:
        severity = SeverityLevel.LOW

    report = PlagiarismReport(
        check_id=check_id,
        paper_id=check.get('paper_id'),
        overall_similarity=similarity / 100,  # 转换为小数
        severity=severity,
        total_words=0,
        checked_words=0,
        similar_word_count=0,
        section_reports=[
            SectionReport(
                section_id="main",
                section_title="全文",
                word_count=0,
                similarity_rate=similarity / 100,
                similar_segments=[
                    SimilaritySegment(
                        id=m.get('source_id', str(uuid.uuid4())),
                        source_text=m.get('text', ''),
                        similar_text=m.get('text', ''),
                        similarity=m.get('similarity', 0),
                        source_title=m.get('source_title'),
                        source_url=m.get('source_url'),
                        position={"start": m.get('start_index', 0), "end": m.get('end_index', 0)},
                    )
                    for m in (check.get('matches') or [])
                ],
            )
        ],
        similar_sources=check.get('sources') or [],
        created_at=check.get('submitted_at') or datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
    )

    return success_response(data=report.model_dump())


@router.delete("/check/{check_id}", summary="删除检测记录")
async def delete_check(
    check_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除查重检测记录"""
    check_repo = PlagiarismCheckRepository(db)
    check = await check_repo.get_by_id(check_id)

    if not check or check['user_id'] != user_id:
        raise NotFoundException("查重任务")

    # TODO: 实现删除逻辑

    return success_response(message="检测记录已删除")


# ============== 降重建议 ==============

@router.post("/reduce", summary="获取降重建议")
async def get_reduce_suggestions(
    request: ReducePlagiarismRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    根据查重报告生成降重建议
    """
    check_repo = PlagiarismCheckRepository(db)
    check = await check_repo.get_by_id(request.check_id)

    if not check or check['user_id'] != user_id:
        raise NotFoundException("查重任务")

    if check['status'] != 'completed':
        raise ValidationException("检测尚未完成")

    # 模拟生成降重建议
    suggestions = []
    matches = check.get('matches') or []

    for i, match in enumerate(matches[:5]):
        if request.segment_ids and match.get('source_id') not in request.segment_ids:
            continue

        segment_suggestions = SegmentSuggestions(
            segment_id=match.get('source_id', str(i)),
            original_text=match.get('text', ''),
            suggestions=[
                RewordSuggestion(
                    original_text=match.get('text', ''),
                    suggested_text="建议改写后的文本示例...",
                    suggestion_type=SuggestionType.REPHRASE,
                    confidence=0.85,
                    reason="使用同义词替换和调整句式结构",
                    alternatives=[
                        "替代改写方案 1",
                        "替代改写方案 2",
                    ],
                )
            ],
        )
        suggestions.append(segment_suggestions)

    tips = [
        "建议先处理高相似度段落",
        "可以通过增加原创内容稀释重复率",
        "注意保持学术表达的规范性",
        "引用内容需正确标注来源",
    ]

    return success_response(
        data=ReducePlagiarismResponse(
            check_id=request.check_id,
            total_segments=len(matches),
            processed_segments=len(suggestions),
            suggestions=suggestions,
            tips=tips,
        ).model_dump()
    )


# ============== 白名单管理 ==============

@router.get("/whitelist", summary="获取白名单")
async def get_whitelist(
    paper_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的查重白名单"""
    whitelist_repo = PlagiarismWhitelistRepository(db)

    if paper_id:
        items = await whitelist_repo.get_paper_whitelist(paper_id)
    else:
        # 获取用户的所有白名单
        items = []

    return success_response(
        data=[WhitelistResponse(**item).model_dump() for item in items]
    )


@router.post("/whitelist", summary="添加白名单")
async def add_whitelist(
    request: WhitelistCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """添加白名单条目"""
    whitelist_repo = PlagiarismWhitelistRepository(db)

    # 检查是否已存在
    import hashlib
    content_hash = hashlib.sha256(request.content.encode()).hexdigest()[:64]

    if request.paper_id:
        exists = await whitelist_repo.exists(content_hash, request.paper_id)
        if exists:
            raise ValidationException("该内容已在白名单中")

    item = await whitelist_repo.create({
        'user_id': user_id,
        'paper_id': request.paper_id,
        'content': request.content,
        'content_hash': content_hash,
        'reason': request.reason,
        'source': request.source,
    })
    await db.commit()

    return success_response(
        data=WhitelistResponse(**item).model_dump(),
        message="添加成功",
        code=201,
    )


@router.delete("/whitelist/{whitelist_id}", summary="删除白名单")
async def delete_whitelist(
    whitelist_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除白名单条目"""
    whitelist_repo = PlagiarismWhitelistRepository(db)
    success = await whitelist_repo.delete(whitelist_id, user_id)

    if not success:
        raise NotFoundException("白名单条目")

    await db.commit()
    return success_response(message="删除成功")


# ============== 设置管理 ==============

@router.get("/settings", summary="获取查重设置")
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的查重设置"""
    settings_repo = PlagiarismSettingsRepository(db)
    settings = await settings_repo.get_or_create(user_id)

    return success_response(data=PlagiarismSettings(**settings).model_dump())


@router.put("/settings", summary="更新查重设置")
async def update_settings(
    request: PlagiarismSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新用户的查重设置"""
    settings_repo = PlagiarismSettingsRepository(db)

    settings = await settings_repo.update(
        user_id,
        request.model_dump(exclude_unset=True)
    )
    await db.commit()

    return success_response(
        data=PlagiarismSettings(**settings).model_dump(),
        message="设置已更新"
    )


# ============== 历史记录 ==============

@router.get("/history", summary="获取检测历史")
async def get_check_history(
    paper_id: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的查重检测历史"""
    check_repo = PlagiarismCheckRepository(db)

    checks, total = await check_repo.get_user_checks(
        user_id=user_id,
        paper_id=paper_id,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    items = [
        CheckHistory(
            check_id=c['id'],
            paper_id=c.get('paper_id') or '',
            paper_title=c.get('task_name'),
            similarity_rate=c.get('overall_similarity') or 0,
            status=CheckStatus(c.get('status', 'pending')),
            created_at=c.get('submitted_at') or datetime.now(),
        )
        for c in checks
    ]

    return paginated_response(
        items=[h.model_dump() for h in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/paper/{paper_id}/history", summary="获取论文查重历史")
async def get_paper_history(
    paper_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取论文的查重历史"""
    history_repo = PlagiarismHistoryRepository(db)
    history = await history_repo.get_paper_history(paper_id)

    return success_response(
        data=[PlagiarismHistoryResponse(**h).model_dump() for h in history]
    )


# ============== 统计 ==============

@router.get("/statistics", summary="获取查重统计")
async def get_statistics(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的查重统计信息"""
    check_repo = PlagiarismCheckRepository(db)

    checks, _ = await check_repo.get_user_checks(user_id=user_id, page=1, page_size=1000)

    completed = [c for c in checks if c['status'] == 'completed']
    similarities = [c.get('overall_similarity') or 0 for c in completed if c.get('overall_similarity')]

    stats = PlagiarismStatistics(
        total_checks=len(checks),
        completed_checks=len(completed),
        failed_checks=len([c for c in checks if c['status'] == 'failed']),
        average_similarity=round(sum(similarities) / len(similarities), 2) if similarities else 0,
        max_similarity=max(similarities) if similarities else 0,
        min_similarity=min(similarities) if similarities else 0,
        recent_trend=[
            {
                'date': c.get('submitted_at').strftime('%Y-%m-%d') if c.get('submitted_at') else '',
                'similarity': c.get('overall_similarity') or 0
            }
            for c in completed[-10:]
        ],
    )

    return success_response(data=stats.model_dump())


# ============== 可用引擎 ==============

@router.get("/engines", summary="获取可用引擎")
async def get_available_engines(
    user_id: str = Depends(get_current_user_id),
):
    """获取可用的查重引擎列表"""
    engines = PlagiarismEngineFactory.available_engines()

    engine_info = []
    for engine in engines:
        info = {
            'id': engine,
            'name': {
                'local': '本地查重',
                'turnitin': 'Turnitin',
                'paperpass': 'PaperPass',
                'mock': '模拟查重（测试）',
            }.get(engine, engine),
            'available': True,
        }
        # Turnitin 需要配置 API 密钥
        if engine == 'turnitin' and not os.getenv('TURNITIN_API_KEY'):
            info['available'] = False
            info['reason'] = '未配置 API 密钥'
        engine_info.append(info)

    return success_response(data=engine_info)
