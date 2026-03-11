"""
Knowledge Management Service
知识管理服务 - 智能引用、知识管理、引用统计
"""

import uuid
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from .models import (
    Reference, ReferenceType, ReferenceStatus, ReferencePreview,
    Folder, FolderItem, KnowledgeTag, TaggedItem, KnowledgeRelation,
    KnowledgeGraph, CitationStatistics, SearchIndex
)


class KnowledgeService:
    """知识管理服务"""

    def __init__(self):
        # 内存存储
        self._references: Dict[str, Reference] = {}
        self._folders: Dict[str, Folder] = {}
        self._folder_items: Dict[str, FolderItem] = {}
        self._tags: Dict[str, KnowledgeTag] = {}
        self._tagged_items: List[TaggedItem] = []
        self._relations: List[KnowledgeRelation] = []
        self._graphs: Dict[str, KnowledgeGraph] = {}
        self._citation_stats: Dict[str, CitationStatistics] = {}
        self._search_index: Dict[str, SearchIndex] = {}

    # ==================== 智能引用 ====================

    def create_reference(
        self,
        source_id: str,
        target_id: str,
        target_type: ReferenceType,
        position_start: int = 0,
        position_end: int = 0,
        context_text: str = "",
        created_by: str = ""
    ) -> Reference:
        """创建引用"""
        reference = Reference(
            id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            target_type=target_type,
            position_start=position_start,
            position_end=position_end,
            context_text=context_text[:200],  # 限制长度
            created_by=created_by
        )

        self._references[reference.id] = reference

        # 更新引用统计
        self._update_citation_stats(target_id, target_type.value, source_id)

        return reference

    def parse_references_from_text(
        self,
        text: str,
        source_id: str,
        created_by: str
    ) -> List[Reference]:
        """从文本中解析@引用

        支持格式:
        - @paper:12345
        - @note:abc123
        - @news:xyz789
        - @dataset:data001
        """
        references = []

        # 匹配 @type:id 格式
        pattern = r'@(\w+):([\w-]+)'
        matches = re.finditer(pattern, text)

        for match in matches:
            type_str = match.group(1)
            target_id = match.group(2)

            try:
                ref_type = ReferenceType(type_str)
            except ValueError:
                continue

            # 获取上下文
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            reference = self.create_reference(
                source_id=source_id,
                target_id=target_id,
                target_type=ref_type,
                position_start=match.start(),
                position_end=match.end(),
                context_text=context,
                created_by=created_by
            )
            references.append(reference)

        return references

    def get_reference_preview(
        self,
        reference_id: str,
        user_id: str
    ) -> Optional[ReferencePreview]:
        """获取引用预览"""
        reference = self._references.get(reference_id)
        if not reference:
            return None

        # 更新预览次数
        reference.preview_count += 1

        # 根据类型获取预览内容
        preview_data = self._fetch_target_preview(
            reference.target_id,
            reference.target_type
        )

        return ReferencePreview(
            reference_id=reference_id,
            target_type=reference.target_type,
            target_id=reference.target_id,
            title=preview_data.get("title", "Unknown"),
            summary=preview_data.get("summary", "")[:300],
            thumbnail_url=preview_data.get("thumbnail_url"),
            metadata=preview_data.get("metadata", {})
        )

    def _fetch_target_preview(
        self,
        target_id: str,
        target_type: ReferenceType
    ) -> Dict[str, Any]:
        """获取目标预览数据（模拟实现）"""
        # 实际应从对应服务获取
        preview_templates = {
            ReferenceType.PAPER: {
                "title": f"Paper: {target_id}",
                "summary": "This is a research paper about...",
                "metadata": {"authors": ["Author A"], "year": 2024}
            },
            ReferenceType.NOTE: {
                "title": f"Note: {target_id}",
                "summary": "Research notes and findings...",
                "metadata": {"created": "2024-01-01"}
            },
            ReferenceType.NEWS: {
                "title": f"News: {target_id}",
                "summary": "Latest research news...",
                "metadata": {"source": "Nature", "date": "2024-01-01"}
            }
        }

        return preview_templates.get(target_type, {
            "title": f"Item: {target_id}",
            "summary": "No preview available"
        })

    def get_document_references(
        self,
        document_id: str,
        direction: str = "outgoing"  # outgoing/incoming/both
    ) -> List[Reference]:
        """获取文档的引用关系"""
        references = []

        if direction in ["outgoing", "both"]:
            # 文档引用了哪些内容
            refs = [
                r for r in self._references.values()
                if r.source_id == document_id
            ]
            references.extend(refs)

        if direction in ["incoming", "both"]:
            # 哪些内容引用了文档
            refs = [
                r for r in self._references.values()
                if r.target_id == document_id
            ]
            references.extend(refs)

        return references

    def get_reference_suggestions(
        self,
        text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取引用自动补全建议"""
        # 简单实现：基于文本关键词匹配
        suggestions = []

        # 模拟建议数据
        for ref_type in ReferenceType:
            for i in range(3):
                suggestions.append({
                    "id": f"{ref_type.value}_suggestion_{i}",
                    "type": ref_type.value,
                    "title": f"Suggested {ref_type.value} {i}",
                    "match_score": 0.9 - (i * 0.1)
                })

        return suggestions[:limit]

    # ==================== 文件夹管理 ====================

    def create_folder(
        self,
        name: str,
        owner_id: str,
        description: str = "",
        parent_id: Optional[str] = None,
        color: Optional[str] = None,
        is_public: bool = False
    ) -> Folder:
        """创建文件夹"""
        folder = Folder(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            owner_id=owner_id,
            parent_id=parent_id,
            color=color,
            is_public=is_public
        )

        # 计算完整路径
        if parent_id and parent_id in self._folders:
            parent = self._folders[parent_id]
            folder.path = f"{parent.path}/{name}"
        else:
            folder.path = f"/{name}"

        self._folders[folder.id] = folder
        return folder

    def get_folder(self, folder_id: str) -> Optional[Folder]:
        """获取文件夹"""
        return self._folders.get(folder_id)

    def get_user_folders(
        self,
        user_id: str,
        parent_id: Optional[str] = None
    ) -> List[Folder]:
        """获取用户的文件夹"""
        folders = [
            f for f in self._folders.values()
            if f.owner_id == user_id and f.parent_id == parent_id
        ]
        return sorted(folders, key=lambda x: x.created_at, reverse=True)

    def add_to_folder(
        self,
        folder_id: str,
        item_id: str,
        item_type: str,
        notes: str = "",
        order_index: int = 0
    ) -> FolderItem:
        """添加项目到文件夹"""
        item = FolderItem(
            id=str(uuid.uuid4()),
            folder_id=folder_id,
            item_id=item_id,
            item_type=item_type,
            order_index=order_index,
            notes=notes
        )

        self._folder_items[item.id] = item

        # 更新文件夹
        folder = self._folders.get(folder_id)
        if folder and item_id not in folder.items:
            folder.items.append(item_id)
            folder.updated_at = datetime.utcnow()

        return item

    def get_folder_contents(
        self,
        folder_id: str,
        item_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取文件夹内容"""
        items = [
            item for item in self._folder_items.values()
            if item.folder_id == folder_id
        ]

        if item_type:
            items = [i for i in items if i.item_type == item_type]

        # 按排序索引排序
        items.sort(key=lambda x: x.order_index)

        result = []
        for item in items:
            # 获取实际内容
            content = self._fetch_item_content(item.item_id, item.item_type)
            result.append({
                "folder_item_id": item.id,
                "item_id": item.item_id,
                "item_type": item.item_type,
                "notes": item.notes,
                "added_at": item.added_at.isoformat(),
                "content": content
            })

        return result

    def _fetch_item_content(
        self,
        item_id: str,
        item_type: str
    ) -> Dict[str, Any]:
        """获取项目内容（模拟）"""
        return {
            "id": item_id,
            "type": item_type,
            "title": f"{item_type.title()}: {item_id}",
            "preview": "Content preview..."
        }

    # ==================== 标签系统 ====================

    def create_tag(
        self,
        name: str,
        owner_id: str,
        color: str = "#1890ff",
        icon: Optional[str] = None
    ) -> KnowledgeTag:
        """创建标签"""
        tag = KnowledgeTag(
            id=str(uuid.uuid4()),
            name=name,
            color=color,
            icon=icon,
            owner_id=owner_id
        )

        self._tags[tag.id] = tag
        return tag

    def tag_item(
        self,
        tag_id: str,
        item_id: str,
        item_type: str,
        tagged_by: str
    ) -> TaggedItem:
        """为项目打标签"""
        tagged = TaggedItem(
            tag_id=tag_id,
            item_id=item_id,
            item_type=item_type,
            tagged_by=tagged_by
        )

        self._tagged_items.append(tagged)

        # 更新标签使用次数
        tag = self._tags.get(tag_id)
        if tag:
            tag.usage_count += 1

        return tagged

    def get_item_tags(
        self,
        item_id: str,
        item_type: str
    ) -> List[KnowledgeTag]:
        """获取项目的标签"""
        tag_ids = [
            t.tag_id for t in self._tagged_items
            if t.item_id == item_id and t.item_type == item_type
        ]

        return [self._tags[tid] for tid in tag_ids if tid in self._tags]

    def search_by_tags(
        self,
        tag_ids: List[str],
        item_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """按标签搜索"""
        # 找到所有匹配的项目
        item_matches = defaultdict(int)

        for tagged in self._tagged_items:
            if tagged.tag_id in tag_ids:
                if item_type and tagged.item_type != item_type:
                    continue
                key = (tagged.item_id, tagged.item_type)
                item_matches[key] += 1

        # 按匹配度排序
        results = []
        for (item_id, item_type), match_count in sorted(
            item_matches.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            results.append({
                "item_id": item_id,
                "item_type": item_type,
                "match_count": match_count,
                "content": self._fetch_item_content(item_id, item_type)
            })

        return results

    # ==================== 知识关联 ====================

    def create_relation(
        self,
        source_id: str,
        source_type: str,
        target_id: str,
        target_type: str,
        relation_type: str,
        strength: float = 0.5,
        reason: str = "",
        is_auto: bool = True
    ) -> KnowledgeRelation:
        """创建知识关联"""
        relation = KnowledgeRelation(
            id=str(uuid.uuid4()),
            source_id=source_id,
            source_type=source_type,
            target_id=target_id,
            target_type=target_type,
            relation_type=relation_type,
            strength=strength,
            reason=reason,
            is_auto=is_auto
        )

        self._relations.append(relation)
        return relation

    def find_related_items(
        self,
        item_id: str,
        item_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """查找相关知识"""
        # 找到所有关联
        relations = [
            r for r in self._relations
            if (r.source_id == item_id and r.source_type == item_type) or
               (r.target_id == item_id and r.target_type == item_type)
        ]

        # 按强度排序
        relations.sort(key=lambda x: x.strength, reverse=True)

        results = []
        for r in relations[:limit]:
            # 确定关联方向
            if r.source_id == item_id:
                target_id = r.target_id
                target_type = r.target_type
            else:
                target_id = r.source_id
                target_type = r.source_type

            results.append({
                "relation_id": r.id,
                "item_id": target_id,
                "item_type": target_type,
                "relation_type": r.relation_type,
                "strength": r.strength,
                "reason": r.reason,
                "is_auto": r.is_auto,
                "content": self._fetch_item_content(target_id, target_type)
            })

        return results

    def generate_knowledge_graph(
        self,
        center_item_id: str,
        center_item_type: str,
        depth: int = 2,
        user_id: str = ""
    ) -> KnowledgeGraph:
        """生成知识图谱"""
        graph = KnowledgeGraph(
            id=str(uuid.uuid4()),
            name=f"Graph for {center_item_id}",
            description="Auto-generated knowledge graph",
            owner_id=user_id
        )

        nodes = {}
        edges = []
        visited = set()

        def add_node(item_id: str, item_type: str, depth_level: int):
            node_id = f"{item_type}:{item_id}"
            if node_id in visited:
                return node_id
            visited.add(node_id)

            content = self._fetch_item_content(item_id, item_type)
            nodes[node_id] = {
                "id": node_id,
                "item_id": item_id,
                "item_type": item_type,
                "label": content.get("title", item_id),
                "depth": depth_level
            }
            return node_id

        def traverse(current_id: str, current_type: str, current_depth: int):
            if current_depth > depth:
                return

            current_node_id = add_node(current_id, current_type, current_depth)

            # 找到关联
            relations = [
                r for r in self._relations
                if (r.source_id == current_id and r.source_type == current_type) or
                   (r.target_id == current_id and r.target_type == current_type)
            ]

            for r in relations:
                if r.source_id == current_id:
                    next_id, next_type = r.target_id, r.target_type
                else:
                    next_id, next_type = r.source_id, r.source_type

                next_node_id = add_node(next_id, next_type, current_depth + 1)

                edges.append({
                    "source": current_node_id,
                    "target": next_node_id,
                    "type": r.relation_type,
                    "strength": r.strength
                })

                if current_depth < depth:
                    traverse(next_id, next_type, current_depth + 1)

        # 从中心节点开始遍历
        traverse(center_item_id, center_item_type, 0)

        graph.nodes = list(nodes.values())
        graph.edges = edges

        return graph

    # ==================== 引用统计 ====================

    def _update_citation_stats(
        self,
        item_id: str,
        item_type: str,
        source_id: str
    ):
        """更新引用统计"""
        key = f"{item_type}:{item_id}"

        if key not in self._citation_stats:
            self._citation_stats[key] = CitationStatistics(
                item_id=item_id,
                item_type=item_type
            )

        stats = self._citation_stats[key]
        stats.total_citations += 1

        # 分类统计
        if "paper" in source_id:
            stats.cited_by_papers.append(source_id)
        else:
            stats.cited_by_notes.append(source_id)

        stats.last_updated = datetime.utcnow()

    def get_citation_statistics(
        self,
        item_id: str,
        item_type: str
    ) -> Optional[CitationStatistics]:
        """获取引用统计"""
        key = f"{item_type}:{item_id}"
        return self._citation_stats.get(key)

    def get_citation_report(
        self,
        item_id: str,
        item_type: str
    ) -> Dict[str, Any]:
        """获取引用报告"""
        stats = self.get_citation_statistics(item_id, item_type)

        if not stats:
            return {
                "item_id": item_id,
                "item_type": item_type,
                "total_citations": 0,
                "message": "No citation data available"
            }

        return {
            "item_id": item_id,
            "item_type": item_type,
            "total_citations": stats.total_citations,
            "cited_by": {
                "papers": len(stats.cited_by_papers),
                "notes": len(stats.cited_by_notes)
            },
            "unique_sources": len(set(stats.cited_by_papers + stats.cited_by_notes)),
            "h_index": stats.h_index,
            "impact_factor": stats.impact_factor,
            "last_updated": stats.last_updated.isoformat()
        }

    # ==================== 全文搜索 ====================

    def index_item(
        self,
        item_id: str,
        item_type: str,
        title: str,
        content: str,
        tags: List[str],
        folder_ids: List[str],
        owner_id: str
    ):
        """索引项目用于搜索"""
        index = SearchIndex(
            item_id=item_id,
            item_type=item_type,
            title=title,
            content=content,
            tags=tags,
            folder_ids=folder_ids,
            owner_id=owner_id
        )

        self._search_index[f"{item_type}:{item_id}"] = index

    def search(
        self,
        query: str,
        owner_id: str,
        item_types: Optional[List[str]] = None,
        folder_ids: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """全文搜索"""
        query_lower = query.lower()
        results = []

        for key, index in self._search_index.items():
            # 权限检查
            if index.owner_id != owner_id:
                continue

            # 类型过滤
            if item_types and index.item_type not in item_types:
                continue

            # 文件夹过滤
            if folder_ids:
                if not any(fid in index.folder_ids for fid in folder_ids):
                    continue

            # 计算匹配分数
            score = 0.0

            # 标题匹配权重最高
            if query_lower in index.title.lower():
                score += 10.0

            # 内容匹配
            if query_lower in index.content.lower():
                score += 5.0

            # 标签匹配
            for tag in index.tags:
                if query_lower in tag.lower():
                    score += 3.0

            if score > 0:
                results.append({
                    "item_id": index.item_id,
                    "item_type": index.item_type,
                    "title": index.title,
                    "excerpt": self._generate_excerpt(index.content, query),
                    "score": score,
                    "tags": index.tags
                })

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _generate_excerpt(
        self,
        content: str,
        query: str,
        excerpt_length: int = 150
    ) -> str:
        """生成搜索摘要"""
        query_lower = query.lower()
        content_lower = content.lower()

        pos = content_lower.find(query_lower)
        if pos == -1:
            return content[:excerpt_length] + "..."

        start = max(0, pos - excerpt_length // 2)
        end = min(len(content), pos + len(query) + excerpt_length // 2)

        excerpt = content[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        return excerpt


# 单例
_knowledge_service = None


def get_knowledge_service() -> KnowledgeService:
    """获取知识服务单例"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service
