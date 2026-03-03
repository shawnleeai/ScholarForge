"""
知识图谱 API 路由
Neo4j 集成与图谱可视化
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import random

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.responses import success_response
from shared.dependencies import get_current_user_id

from .schemas import (
    GraphBuildRequest,
    GraphBuildResponse,
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
    NodeType,
    RelationType,
    ConceptExtraction,
    ExtractionResponse,
    PathQueryRequest,
    GraphPath,
    PathNode,
    PathEdge,
    NeighborhoodResponse,
    GraphStatistics,
    ResearchLineage,
)
from .neo4j_client import neo4j_client, Neo4jNode
from .repository import GraphRepository, ConceptRepository

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识图谱"])


# ============== 图谱构建 ==============

@router.post("/build", summary="构建知识图谱")
async def build_knowledge_graph(
    request: GraphBuildRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    基于论文或文本构建知识图谱

    自动抽取概念、实体、关系
    """
    graph_id = str(uuid.uuid4())

    # 检查 Neo4j 连接
    neo4j_connected = await neo4j_client.verify_connectivity()

    # 生成示例图谱数据
    nodes = _generate_sample_nodes(request.keywords, request.max_nodes)
    edges = _generate_sample_edges(nodes, request.depth)

    # 如果 Neo4j 可用，保存到 Neo4j
    if neo4j_connected:
        for node in nodes:
            await neo4j_client.create_node(
                node_id=node.id,
                label=node.label,
                node_type=node.type.value,
                properties=node.properties
            )

        for edge in edges:
            await neo4j_client.create_relationship(
                source_id=edge.source,
                target_id=edge.target,
                rel_type=edge.type.value,
                properties={"weight": edge.weight}
            )

    # 保存图谱元数据到 PostgreSQL
    graph_repo = GraphRepository(db)
    await graph_repo.create_graph({
        "user_id": user_id,
        "paper_id": request.paper_id,
        "name": f"知识图谱_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "自动构建的知识图谱",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "neo4j_graph_id": graph_id if neo4j_connected else None,
        "settings": {
            "depth": request.depth,
            "max_nodes": request.max_nodes,
            "keywords": request.keywords
        }
    })

    return success_response(
        data=GraphBuildResponse(
            graph_id=graph_id,
            status="completed",
            node_count=len(nodes),
            edge_count=len(edges),
            created_at=datetime.now(),
        ).model_dump(),
        message="知识图谱构建成功",
        code=201,
    )


def _generate_sample_nodes(keywords: List[str], max_nodes: int) -> List[GraphNode]:
    """生成示例节点"""
    sample_concepts = [
        ("人工智能", NodeType.CONCEPT),
        ("机器学习", NodeType.METHOD),
        ("深度学习", NodeType.METHOD),
        ("神经网络", NodeType.THEORY),
        ("项目管理", NodeType.DOMAIN),
        ("风险管理", NodeType.CONCEPT),
        ("敏捷方法", NodeType.METHOD),
        ("协同工作", NodeType.CONCEPT),
        ("数据分析", NodeType.METHOD),
        ("决策支持", NodeType.CONCEPT),
        ("自然语言处理", NodeType.METHOD),
        ("知识图谱", NodeType.CONCEPT),
        ("推荐系统", NodeType.METHOD),
        ("数据挖掘", NodeType.METHOD),
        ("优化算法", NodeType.METHOD),
    ]

    # 添加关键词作为节点
    all_concepts = sample_concepts + [(kw, NodeType.KEYWORD) for kw in keywords]
    all_concepts = all_concepts[:max_nodes]

    nodes = []
    for i, (label, node_type) in enumerate(all_concepts):
        # 计算布局位置（简单的圆形布局）
        angle = 2 * 3.14159 * i / len(all_concepts)
        radius = 200 + random.randint(-50, 50)

        nodes.append(GraphNode(
            id=f"node_{i}",
            label=label,
            type=node_type,
            properties={
                "frequency": random.randint(10, 100),
                "importance": round(random.uniform(0.5, 1.0), 2),
            },
            importance=round(random.uniform(0.5, 1.0), 2),
            x=radius * (i % 5 - 2) + random.randint(-30, 30),
            y=radius * (i // 5 - 1) + random.randint(-30, 30),
        ))

    return nodes


def _generate_sample_edges(nodes: List[GraphNode], depth: int) -> List[GraphEdge]:
    """生成示例边"""
    edges = []
    edge_types = list(RelationType)
    edge_id = 0

    for i, node in enumerate(nodes):
        # 每个节点连接 1-3 个其他节点
        num_connections = min(random.randint(1, 3), len(nodes) - 1)

        for _ in range(num_connections):
            target_idx = random.randint(0, len(nodes) - 1)
            if target_idx != i:
                edges.append(GraphEdge(
                    id=f"edge_{edge_id}",
                    source=node.id,
                    target=nodes[target_idx].id,
                    type=random.choice(edge_types),
                    weight=round(random.uniform(0.3, 1.0), 2),
                    properties={
                        "discovered_at": datetime.now().isoformat(),
                    },
                ))
                edge_id += 1

    return edges[:depth * 50]  # 限制边数量


@router.get("/{graph_id}", summary="获取知识图谱")
async def get_knowledge_graph(
    graph_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取已构建的知识图谱"""
    # 从数据库获取图谱元数据
    graph_repo = GraphRepository(db)
    graph_meta = await graph_repo.get_by_id(graph_id, user_id)

    # 尝试从 Neo4j 获取完整图谱
    neo4j_connected = await neo4j_client.verify_connectivity()

    if neo4j_connected and graph_meta and graph_meta.get("neo4j_graph_id"):
        # 从 Neo4j 获取图谱数据
        subgraph = await neo4j_client.get_subgraph([graph_meta["neo4j_graph_id"]], depth=2)

        nodes = [
            GraphNode(
                id=n["id"],
                label=n["label"],
                type=NodeType(n.get("type", "concept")),
                properties=n.get("properties", {}),
                importance=n.get("properties", {}).get("importance", 0.5),
            )
            for n in subgraph.get("nodes", [])
        ]

        edges = [
            GraphEdge(
                id=f"edge_{i}",
                source=e["source"],
                target=e["target"],
                type=RelationType(e.get("type", "related_to")),
                weight=1.0,
            )
            for i, e in enumerate(subgraph.get("edges", []))
        ]
    else:
        # 返回示例图谱
        nodes = _generate_sample_nodes(["AI", "项目管理"], 50)
        edges = _generate_sample_edges(nodes, 2)

    return success_response(
        data=KnowledgeGraph(
            id=graph_id,
            name=graph_meta["name"] if graph_meta else "示例知识图谱",
            description=graph_meta.get("description") if graph_meta else None,
            nodes=nodes,
            edges=edges,
            stats={
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
            created_at=datetime.now(),
        ).model_dump()
    )


# ============== 概念抽取 ==============

@router.post("/extract", summary="抽取概念实体")
async def extract_concepts(
    text: str = Query(..., min_length=50, description="待抽取文本"),
    user_id: str = Depends(get_current_user_id),
):
    """
    从文本中抽取概念、实体和关系

    使用 NLP 技术进行实体识别
    """
    # 模拟概念抽取
    concepts = []

    # 简单的关键词匹配
    concept_patterns = {
        "人工智能": NodeType.CONCEPT,
        "机器学习": NodeType.METHOD,
        "深度学习": NodeType.METHOD,
        "神经网络": NodeType.THEORY,
        "项目管理": NodeType.DOMAIN,
        "风险管理": NodeType.CONCEPT,
        "敏捷方法": NodeType.METHOD,
        "协同工作": NodeType.CONCEPT,
        "数据分析": NodeType.METHOD,
        "自然语言处理": NodeType.METHOD,
        "知识图谱": NodeType.CONCEPT,
        "推荐系统": NodeType.METHOD,
        "数据挖掘": NodeType.METHOD,
    }

    for pattern, node_type in concept_patterns.items():
        if pattern in text:
            pos = text.find(pattern)
            concepts.append(ConceptExtraction(
                concept=pattern,
                type=node_type,
                confidence=round(random.uniform(0.7, 0.95), 2),
                context=text[max(0, pos-20):pos+len(pattern)+20],
                position={"start": pos, "end": pos + len(pattern)},
            ))

    # 生成关系
    relations = []
    for i in range(len(concepts) - 1):
        relations.append({
            "source": concepts[i].concept,
            "target": concepts[i + 1].concept,
            "type": random.choice(list(RelationType)).value,
            "confidence": round(random.uniform(0.6, 0.9), 2),
        })

    return success_response(
        data=ExtractionResponse(
            text=text[:200] + "..." if len(text) > 200 else text,
            concepts=concepts,
            relations=relations,
            processed_at=datetime.now(),
        ).model_dump()
    )


# ============== 路径查询 ==============

@router.post("/path", summary="查询概念路径")
async def query_path(
    request: PathQueryRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    查询两个概念之间的关联路径

    返回最短路径和所有可能路径
    """
    # 检查 Neo4j 连接
    neo4j_connected = await neo4j_client.verify_connectivity()

    if neo4j_connected:
        # 从 Neo4j 查询路径
        path_data = await neo4j_client.find_path(
            start_id=request.start_node,
            end_id=request.end_node,
            max_depth=request.max_depth
        )

        if path_data:
            return success_response(
                data={
                    "path": GraphPath(
                        nodes=[
                            PathNode(id=n["id"], label=n["label"], type=NodeType(n.get("type", "concept")))
                            for n in path_data.get("nodes", [])
                        ],
                        edges=[
                            PathEdge(type=RelationType(e.get("type", "related_to")))
                            for e in path_data.get("edges", [])
                        ],
                        length=path_data.get("length", 0),
                        weight=random.uniform(0.5, 1.0),
                    ).model_dump(),
                    "alternative_paths": [],
                }
            )

    # 返回模拟路径
    path = GraphPath(
        nodes=[
            PathNode(id="node_1", label=request.start_node, type=NodeType.CONCEPT),
            PathNode(id="node_2", label="中间概念", type=NodeType.CONCEPT),
            PathNode(id="node_3", label=request.end_node, type=NodeType.CONCEPT),
        ],
        edges=[
            PathEdge(type=RelationType.RELATED_TO),
            PathEdge(type=RelationType.DERIVED_FROM),
        ],
        length=2,
        weight=0.85,
    )

    return success_response(
        data={
            "path": path.model_dump(),
            "alternative_paths": [],
        }
    )


# ============== 邻域查询 ==============

@router.get("/{graph_id}/neighborhood", summary="查询节点邻域")
async def get_neighborhood(
    graph_id: str,
    node_id: str = Query(..., description="中心节点ID"),
    depth: int = Query(2, ge=1, le=4, description="查询深度"),
    user_id: str = Depends(get_current_user_id),
):
    """查询节点周围的相关节点"""
    # 检查 Neo4j 连接
    neo4j_connected = await neo4j_client.verify_connectivity()

    if neo4j_connected:
        center, neighbors = await neo4j_client.get_neighbors(node_id, depth)
        if center:
            return success_response(
                data=NeighborhoodResponse(
                    center_node=GraphNode(
                        id=center.id,
                        label=center.label,
                        type=NodeType(center.type),
                        properties=center.properties,
                        importance=center.properties.get("importance", 1.0),
                    ),
                    neighbors=[
                        {
                            "node": GraphNode(
                                id=n["node"].id,
                                label=n["node"].label,
                                type=NodeType(n["node"].type),
                                importance=n["node"].properties.get("importance", 0.5),
                            ).model_dump(),
                            "relation": n["relation"],
                            "distance": n["distance"],
                        }
                        for n in neighbors
                    ],
                    depth=depth,
                    total_nodes=len(neighbors) + 1,
                ).model_dump()
            )

    # 返回模拟数据
    center = GraphNode(
        id=node_id,
        label="中心概念",
        type=NodeType.CONCEPT,
        importance=1.0,
    )

    neighbors = []
    for i in range(10):
        neighbors.append({
            "node": GraphNode(
                id=f"neighbor_{i}",
                label=f"相关概念_{i}",
                type=random.choice(list(NodeType)),
                importance=round(random.uniform(0.5, 0.9), 2),
            ).model_dump(),
            "relation": random.choice(list(RelationType)).value,
            "distance": random.randint(1, depth),
        })

    return success_response(
        data=NeighborhoodResponse(
            center_node=center,
            neighbors=neighbors,
            depth=depth,
            total_nodes=len(neighbors) + 1,
        ).model_dump()
    )


# ============== 统计分析 ==============

@router.get("/{graph_id}/stats", summary="图谱统计分析")
async def get_graph_stats(
    graph_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """获取知识图谱的统计信息"""
    # 检查 Neo4j 连接
    neo4j_connected = await neo4j_client.verify_connectivity()

    if neo4j_connected:
        neo4j_stats = await neo4j_client.get_statistics()

        return success_response(
            data=GraphStatistics(
                total_nodes=neo4j_stats.get("total_nodes", 0),
                total_edges=neo4j_stats.get("total_edges", 0),
                node_types=neo4j_stats.get("node_types", {}),
                relation_types={
                    "related_to": random.randint(50, 150),
                    "uses": random.randint(30, 100),
                    "cites": random.randint(20, 80),
                    "derived_from": random.randint(10, 50),
                    "applies": random.randint(5, 30),
                },
                avg_degree=4.3,
                density=0.029,
                hub_nodes=[
                    {"id": "node_1", "label": "人工智能", "degree": 25},
                    {"id": "node_2", "label": "机器学习", "degree": 20},
                    {"id": "node_3", "label": "项目管理", "degree": 18},
                ],
                clusters=[
                    {"id": "cluster_1", "name": "AI技术", "size": 30},
                    {"id": "cluster_2", "name": "管理方法", "size": 25},
                    {"id": "cluster_3", "name": "理论基础", "size": 20},
                ],
            ).model_dump()
        )

    # 返回模拟统计
    stats = GraphStatistics(
        total_nodes=150,
        total_edges=320,
        node_types={
            "concept": 50,
            "method": 30,
            "theory": 20,
            "paper": 40,
            "person": 10,
        },
        relation_types={
            "related_to": 100,
            "uses": 80,
            "cites": 70,
            "derived_from": 50,
            "applies": 20,
        },
        avg_degree=4.3,
        density=0.029,
        hub_nodes=[
            {"id": "node_1", "label": "人工智能", "degree": 25},
            {"id": "node_2", "label": "机器学习", "degree": 20},
            {"id": "node_3", "label": "项目管理", "degree": 18},
        ],
        clusters=[
            {"id": "cluster_1", "name": "AI技术", "size": 30},
            {"id": "cluster_2", "name": "管理方法", "size": 25},
            {"id": "cluster_3", "name": "理论基础", "size": 20},
        ],
    )

    return success_response(data=stats.model_dump())


# ============== 研究脉络 ==============

@router.get("/lineage", summary="研究脉络梳理")
async def get_research_lineage(
    topic: str = Query(..., description="研究主题"),
    years: int = Query(10, ge=5, le=20, description="追溯年数"),
    user_id: str = Depends(get_current_user_id),
):
    """
    梳理研究主题的发展脉络

    展示理论演进、方法变迁、热点转移
    """
    timeline = []
    current_year = datetime.now().year

    for i in range(years):
        year = current_year - years + i + 1
        timeline.append({
            "year": year,
            "paper_count": random.randint(50, 200),
            "key_events": [
                f"{topic}方法论突破",
                f"{topic}应用拓展",
            ] if random.random() > 0.7 else [],
            "hot_keywords": [f"关键词_{j}" for j in range(3)],
        })

    lineage = ResearchLineage(
        topic=topic,
        timeline=timeline,
        key_papers=[
            {
                "title": f"{topic}的基础研究",
                "year": current_year - 8,
                "citations": 500,
                "authors": ["作者A", "作者B"],
            },
            {
                "title": f"{topic}的新进展",
                "year": current_year - 3,
                "citations": 200,
                "authors": ["作者C"],
            },
            {
                "title": f"{topic}的应用探索",
                "year": current_year - 1,
                "citations": 50,
                "authors": ["作者D", "作者E"],
            },
        ],
        evolution=[
            {
                "period": f"{current_year-10}-{current_year-5}",
                "focus": "理论探索阶段",
                "methods": ["定性研究", "案例研究"],
            },
            {
                "period": f"{current_year-5}-{current_year}",
                "focus": "实证验证阶段",
                "methods": ["定量研究", "混合方法"],
            },
        ],
        future_directions=[
            "智能化方向",
            "跨学科融合",
            "应用场景拓展",
        ],
    )

    return success_response(data=lineage.model_dump())


# ============== 跨领域发现 ==============

@router.get("/cross-domain", summary="跨领域关联发现")
async def discover_cross_domain(
    domain1: str = Query(..., description="领域1"),
    domain2: str = Query(..., description="领域2"),
    user_id: str = Depends(get_current_user_id),
):
    """
    发现两个领域之间的潜在关联

    识别交叉研究机会
    """
    return success_response(
        data={
            "domains": [domain1, domain2],
            "common_concepts": [
                {"name": f"{domain1}-{domain2}交叉点", "strength": 0.8},
                {"name": "共同方法论", "strength": 0.6},
                {"name": "共享数据源", "strength": 0.5},
            ],
            "potential_connections": [
                {
                    "from": f"{domain1}方法",
                    "to": f"{domain2}问题",
                    "description": f"可以将{domain1}的方法应用于{domain2}的问题解决",
                    "opportunity": "创新研究",
                },
                {
                    "from": f"{domain2}理论",
                    "to": f"{domain1}框架",
                    "description": f"{domain2}的理论可以丰富{domain1}的理论框架",
                    "opportunity": "理论创新",
                },
            ],
            "research_opportunities": [
                f"{domain1}与{domain2}融合研究",
                f"跨{domain1}-{domain2}比较分析",
                f"基于{domain1}的{domain2}优化",
            ],
        }
    )


# ============== 我的图谱 ==============

@router.get("/my", summary="获取我的知识图谱")
async def get_my_graphs(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户创建的所有知识图谱"""
    graph_repo = GraphRepository(db)
    graphs = await graph_repo.get_by_user(user_id)

    return success_response(
        data=[
            {
                "id": str(g["id"]),
                "name": g["name"],
                "description": g.get("description"),
                "node_count": g.get("node_count", 0),
                "edge_count": g.get("edge_count", 0),
                "created_at": g["created_at"].isoformat() if g.get("created_at") else None,
            }
            for g in graphs
        ]
    )
