"""
Knowledge Management API Routes
知识管理API路由 - 智能引用、文件夹、知识图谱
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from .service import get_knowledge_service, ReferenceType

router = APIRouter(prefix="/knowledge-mgmt", tags=["knowledge-management"])


# ==================== 请求/响应模型 ====================

class CreateReferenceRequest(BaseModel):
    """创建引用请求"""
    target_id: str = Field(..., description="被引用目标ID")
    target_type: str = Field(..., description="类型: paper/note/news/dataset/code/url")
    position_start: int = Field(0)
    position_end: int = Field(0)
    context_text: str = Field(default="")


class CreateFolderRequest(BaseModel):
    """创建文件夹请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    parent_id: Optional[str] = Field(None)
    color: Optional[str] = Field(None)
    is_public: bool = Field(False)


class AddToFolderRequest(BaseModel):
    """添加到文件夹请求"""
    item_id: str = Field(...)
    item_type: str = Field(...)
    notes: str = Field(default="")


class CreateTagRequest(BaseModel):
    """创建标签请求"""
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field("#1890ff")
    icon: Optional[str] = Field(None)


class CreateRelationRequest(BaseModel):
    """创建关联请求"""
    source_id: str = Field(...)
    source_type: str = Field(...)
    target_id: str = Field(...)
    target_type: str = Field(...)
    relation_type: str = Field(default="related")
    strength: float = Field(0.5, ge=0, le=1)
    reason: str = Field(default="")


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== 智能引用API ====================

@router.post("/references/parse")
async def parse_references(
    text: str,
    source_id: str,
    user_id: str = Depends(get_current_user)
):
    """从文本中解析@引用"""
    service = get_knowledge_service()
    references = service.parse_references_from_text(text, source_id, user_id)

    return {
        "parsed_count": len(references),
        "references": [
            {
                "id": r.id,
                "target_id": r.target_id,
                "target_type": r.target_type.value,
                "position": {"start": r.position_start, "end": r.position_end},
                "context": r.context_text[:100] + "..." if len(r.context_text) > 100 else r.context_text
            }
            for r in references
        ]
    }


@router.post("/references")
async def create_reference(
    request: CreateReferenceRequest,
    source_id: str,
    user_id: str = Depends(get_current_user)
):
    """手动创建引用"""
    service = get_knowledge_service()

    try:
        target_type = ReferenceType(request.target_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid reference type")

    reference = service.create_reference(
        source_id=source_id,
        target_id=request.target_id,
        target_type=target_type,
        position_start=request.position_start,
        position_end=request.position_end,
        context_text=request.context_text,
        created_by=user_id
    )

    return {
        "message": "Reference created successfully",
        "reference": {
            "id": reference.id,
            "target_id": reference.target_id,
            "target_type": reference.target_type.value
        }
    }


@router.get("/references/{reference_id}/preview")
async def get_reference_preview(
    reference_id: str,
    user_id: str = Depends(get_current_user)
):
    """获取引用预览（悬停卡片）"""
    service = get_knowledge_service()
    preview = service.get_reference_preview(reference_id, user_id)

    if not preview:
        raise HTTPException(status_code=404, detail="Reference not found")

    return {
        "reference_id": preview.reference_id,
        "target_type": preview.target_type.value,
        "target_id": preview.target_id,
        "title": preview.title,
        "summary": preview.summary,
        "thumbnail_url": preview.thumbnail_url,
        "metadata": preview.metadata
    }


@router.get("/documents/{document_id}/references")
async def get_document_references(
    document_id: str,
    direction: str = "outgoing"
):
    """获取文档的引用关系"""
    service = get_knowledge_service()
    references = service.get_document_references(document_id, direction)

    return {
        "document_id": document_id,
        "direction": direction,
        "count": len(references),
        "references": [
            {
                "id": r.id,
                "target_id": r.target_id,
                "target_type": r.target_type.value,
                "context": r.context_text[:100] if r.context_text else None,
                "created_at": r.created_at.isoformat()
            }
            for r in references
        ]
    }


@router.get("/references/suggestions")
async def get_reference_suggestions(
    text: str,
    limit: int = 10
):
    """获取引用自动补全建议"""
    service = get_knowledge_service()
    suggestions = service.get_reference_suggestions(text, limit)

    return {"suggestions": suggestions}


# ==================== 文件夹API ====================

@router.post("/folders")
async def create_folder(
    request: CreateFolderRequest,
    user_id: str = Depends(get_current_user)
):
    """创建文件夹"""
    service = get_knowledge_service()

    folder = service.create_folder(
        name=request.name,
        owner_id=user_id,
        description=request.description,
        parent_id=request.parent_id,
        color=request.color,
        is_public=request.is_public
    )

    return {
        "message": "Folder created successfully",
        "folder": {
            "id": folder.id,
            "name": folder.name,
            "path": folder.path
        }
    }


@router.get("/folders")
async def get_folders(
    parent_id: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """获取用户文件夹"""
    service = get_knowledge_service()
    folders = service.get_user_folders(user_id, parent_id)

    return {
        "folders": [
            {
                "id": f.id,
                "name": f.name,
                "description": f.description,
                "path": f.path,
                "color": f.color,
                "item_count": len(f.items),
                "is_public": f.is_public,
                "created_at": f.created_at.isoformat()
            }
            for f in folders
        ]
    }


@router.get("/folders/{folder_id}/contents")
async def get_folder_contents(
    folder_id: str,
    item_type: Optional[str] = None
):
    """获取文件夹内容"""
    service = get_knowledge_service()
    contents = service.get_folder_contents(folder_id, item_type)

    return {
        "folder_id": folder_id,
        "contents": contents
    }


@router.post("/folders/{folder_id}/items")
async def add_to_folder(
    folder_id: str,
    request: AddToFolderRequest,
    user_id: str = Depends(get_current_user)
):
    """添加项目到文件夹"""
    service = get_knowledge_service()

    item = service.add_to_folder(
        folder_id=folder_id,
        item_id=request.item_id,
        item_type=request.item_type,
        notes=request.notes
    )

    return {
        "message": "Item added to folder",
        "folder_item_id": item.id
    }


# ==================== 标签API ====================

@router.post("/tags")
async def create_tag(
    request: CreateTagRequest,
    user_id: str = Depends(get_current_user)
):
    """创建标签"""
    service = get_knowledge_service()

    tag = service.create_tag(
        name=request.name,
        owner_id=user_id,
        color=request.color,
        icon=request.icon
    )

    return {
        "message": "Tag created successfully",
        "tag": {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "icon": tag.icon
        }
    }


@router.get("/tags")
async def get_user_tags(user_id: str = Depends(get_current_user)):
    """获取用户标签"""
    service = get_knowledge_service()

    tags = [t for t in service._tags.values() if t.owner_id == user_id]

    return {
        "tags": [
            {
                "id": t.id,
                "name": t.name,
                "color": t.color,
                "icon": t.icon,
                "usage_count": t.usage_count,
                "created_at": t.created_at.isoformat()
            }
            for t in sorted(tags, key=lambda x: x.usage_count, reverse=True)
        ]
    }


@router.get("/items/{item_id}/tags")
async def get_item_tags(item_id: str, item_type: str):
    """获取项目的标签"""
    service = get_knowledge_service()
    tags = service.get_item_tags(item_id, item_type)

    return {
        "item_id": item_id,
        "item_type": item_type,
        "tags": [
            {"id": t.id, "name": t.name, "color": t.color}
            for t in tags
        ]
    }


# ==================== 知识关联API ====================

@router.post("/relations")
async def create_relation(
    request: CreateRelationRequest,
    user_id: str = Depends(get_current_user)
):
    """创建知识关联"""
    service = get_knowledge_service()

    relation = service.create_relation(
        source_id=request.source_id,
        source_type=request.source_type,
        target_id=request.target_id,
        target_type=request.target_type,
        relation_type=request.relation_type,
        strength=request.strength,
        reason=request.reason,
        is_auto=False
    )

    return {
        "message": "Relation created successfully",
        "relation_id": relation.id
    }


@router.get("/items/{item_id}/related")
async def get_related_items(
    item_id: str,
    item_type: str,
    limit: int = 10
):
    """获取相关知识"""
    service = get_knowledge_service()
    related = service.find_related_items(item_id, item_type, limit)

    return {
        "item_id": item_id,
        "item_type": item_type,
        "related_count": len(related),
        "related_items": related
    }


@router.post("/graph/generate")
async def generate_knowledge_graph(
    center_item_id: str,
    center_item_type: str,
    depth: int = 2,
    user_id: str = Depends(get_current_user)
):
    """生成知识图谱"""
    service = get_knowledge_service()

    graph = service.generate_knowledge_graph(
        center_item_id=center_item_id,
        center_item_type=center_item_type,
        depth=depth,
        user_id=user_id
    )

    return {
        "graph_id": graph.id,
        "name": graph.name,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "nodes": graph.nodes,
        "edges": graph.edges
    }


# ==================== 引用统计API ====================

@router.get("/items/{item_id}/citations")
async def get_citation_statistics(
    item_id: str,
    item_type: str
):
    """获取引用统计"""
    service = get_knowledge_service()
    report = service.get_citation_report(item_id, item_type)

    return report


# ==================== 全文搜索API ====================

@router.get("/search")
async def full_text_search(
    query: str,
    item_types: Optional[str] = None,
    folder_ids: Optional[str] = None,
    limit: int = 20,
    user_id: str = Depends(get_current_user)
):
    """全文搜索"""
    service = get_knowledge_service()

    item_type_list = item_types.split(",") if item_types else None
    folder_id_list = folder_ids.split(",") if folder_ids else None

    results = service.search(
        query=query,
        owner_id=user_id,
        item_types=item_type_list,
        folder_ids=folder_id_list,
        limit=limit
    )

    return {
        "query": query,
        "result_count": len(results),
        "results": results
    }
