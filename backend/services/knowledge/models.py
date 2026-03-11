"""
Knowledge Management Models
知识管理模型 - 智能引用、文件夹、知识关联
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ReferenceType(str, Enum):
    """引用类型"""
    PAPER = "paper"           # 论文
    NOTE = "note"             # 笔记
    NEWS = "news"             # 新闻
    DATASET = "dataset"       # 数据集
    CODE = "code"             # 代码
    URL = "url"               # 网页链接


class ReferenceStatus(str, Enum):
    """引用状态"""
    ACTIVE = "active"
    BROKEN = "broken"         # 链接失效
    ARCHIVED = "archived"     # 已归档


@dataclass
class Reference:
    """引用实体"""
    id: str
    source_id: str            # 引用来源文档ID
    target_id: str            # 被引用目标ID
    target_type: ReferenceType

    # 引用位置
    position_start: int = 0   # 文档中起始位置
    position_end: int = 0     # 文档中结束位置
    context_text: str = ""    # 引用上下文

    # 元数据
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    status: ReferenceStatus = ReferenceStatus.ACTIVE

    # 统计
    click_count: int = 0      # 点击次数
    preview_count: int = 0    # 预览次数


@dataclass
class ReferencePreview:
    """引用预览内容"""
    reference_id: str
    target_type: ReferenceType
    target_id: str
    title: str
    summary: str
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Folder:
    """知识文件夹"""
    id: str
    name: str
    description: str
    owner_id: str

    # 层级结构
    parent_id: Optional[str] = None
    path: str = ""            # 完整路径 /folder1/folder2

    # 内容
    items: List[str] = field(default_factory=list)  # 包含的项目ID
    tags: List[str] = field(default_factory=list)
    color: Optional[str] = None  # 文件夹颜色标识

    # 设置
    is_public: bool = False
    is_system: bool = False   # 系统默认文件夹

    # 时间
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FolderItem:
    """文件夹中的项目"""
    id: str
    folder_id: str
    item_id: str              # 实际内容ID
    item_type: str            # paper/note/dataset等
    order_index: int = 0      # 排序索引
    added_at: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""           # 用户备注


@dataclass
class KnowledgeTag:
    """知识标签"""
    id: str
    name: str
    color: str = "#1890ff"    # 标签颜色
    icon: Optional[str] = None
    owner_id: str = ""
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TaggedItem:
    """标签关联"""
    tag_id: str
    item_id: str
    item_type: str
    tagged_at: datetime = field(default_factory=datetime.utcnow)
    tagged_by: str = ""


@dataclass
class KnowledgeRelation:
    """知识关联"""
    id: str
    source_id: str
    source_type: str
    target_id: str
    target_type: str
    relation_type: str        # similar/related/cited/referenced等
    strength: float = 0.5     # 关联强度 0-1
    reason: str = ""          # 关联原因
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_auto: bool = True      # 是否自动生成


@dataclass
class KnowledgeGraph:
    """知识图谱视图"""
    id: str
    name: str
    description: str
    owner_id: str

    # 图谱节点和边
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)

    # 设置
    layout: str = "force"     # 布局算法
    filters: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CitationStatistics:
    """引用统计"""
    item_id: str
    item_type: str

    # 引用统计
    total_citations: int = 0
    total_references: int = 0

    # 被引用
    cited_by_papers: List[str] = field(default_factory=list)
    cited_by_notes: List[str] = field(default_factory=list)

    # 引用来源
    reference_sources: Dict[str, int] = field(default_factory=dict)

    # 时间分布
    citation_timeline: List[Dict[str, Any]] = field(default_factory=list)

    # 影响力
    h_index: float = 0.0
    impact_factor: float = 0.0

    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SearchIndex:
    """全文搜索索引"""
    item_id: str
    item_type: str
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    folder_ids: List[str] = field(default_factory=list)
    owner_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
