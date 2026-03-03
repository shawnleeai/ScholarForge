"""
知识图谱数据模型
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """节点类型"""
    CONCEPT = "concept"       # 概念
    METHOD = "method"         # 方法
    THEORY = "theory"         # 理论
    PERSON = "person"         # 人物
    PAPER = "paper"           # 论文
    INSTITUTION = "institution"  # 机构
    KEYWORD = "keyword"       # 关键词
    DOMAIN = "domain"         # 领域


class RelationType(str, Enum):
    """关系类型"""
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    DERIVED_FROM = "derived_from"
    APPLIES = "applies"
    CITES = "cites"
    AUTHORED_BY = "authored_by"
    BELONGS_TO = "belongs_to"
    USES = "uses"


# ============== 图谱节点 ==============

class GraphNode(BaseModel):
    """图谱节点"""
    id: str
    label: str
    type: NodeType
    properties: Dict[str, Any] = {}
    importance: float = 1.0
    x: Optional[float] = None
    y: Optional[float] = None


class GraphEdge(BaseModel):
    """图谱边"""
    id: str
    source: str
    target: str
    type: RelationType
    weight: float = 1.0
    properties: Dict[str, Any] = {}


class KnowledgeGraph(BaseModel):
    """知识图谱"""
    id: str
    name: str
    description: Optional[str] = None
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, int] = {}
    created_at: datetime


# ============== 构建请求 ==============

class GraphBuildRequest(BaseModel):
    """图谱构建请求"""
    paper_id: Optional[str] = None
    text: Optional[str] = None
    keywords: List[str] = []
    depth: int = Field(2, ge=1, le=4, description="构建深度")
    max_nodes: int = Field(100, ge=10, le=500, description="最大节点数")


class GraphBuildResponse(BaseModel):
    """图谱构建响应"""
    graph_id: str
    status: str
    node_count: int
    edge_count: int
    created_at: datetime


# ============== 概念抽取 ==============

class ConceptExtraction(BaseModel):
    """概念抽取结果"""
    concept: str
    type: NodeType
    confidence: float
    context: str
    position: Dict[str, int]


class ExtractionResponse(BaseModel):
    """抽取响应"""
    text: str
    concepts: List[ConceptExtraction]
    relations: List[Dict[str, Any]]
    processed_at: datetime


# ============== 路径查询 ==============

class PathNode(BaseModel):
    """路径节点"""
    id: str
    label: str
    type: NodeType


class PathEdge(BaseModel):
    """路径边"""
    type: RelationType
    properties: Dict[str, Any] = {}


class GraphPath(BaseModel):
    """图谱路径"""
    nodes: List[PathNode]
    edges: List[PathEdge]
    length: int
    weight: float


class PathQueryRequest(BaseModel):
    """路径查询请求"""
    start_node: str
    end_node: str
    max_depth: int = Field(4, ge=1, le=6)
    relation_types: Optional[List[RelationType]] = None


# ============== 邻域查询 ==============

class NeighborhoodResponse(BaseModel):
    """邻域响应"""
    center_node: GraphNode
    neighbors: List[Dict[str, Any]]
    depth: int
    total_nodes: int


# ============== 统计分析 ==============

class GraphStatistics(BaseModel):
    """图谱统计"""
    total_nodes: int
    total_edges: int
    node_types: Dict[str, int]
    relation_types: Dict[str, int]
    avg_degree: float
    density: float
    hub_nodes: List[Dict[str, Any]]
    clusters: List[Dict[str, Any]]


# ============== 研究脉络 ==============

class ResearchLineage(BaseModel):
    """研究脉络"""
    topic: str
    timeline: List[Dict[str, Any]]
    key_papers: List[Dict[str, Any]]
    evolution: List[Dict[str, Any]]
    future_directions: List[str]
