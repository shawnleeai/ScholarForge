"""
知识图谱API路由
提供RESTful API访问知识图谱功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from .neo4j_client import get_neo4j_client, init_neo4j
from .knowledge_builder import KnowledgeBuilder
from .query_engine import QueryEngine

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge_graph"])


# ========== 数据模型 ==========

class PaperInput(BaseModel):
    title: str
    abstract: Optional[str] = None
    authors: List[Dict[str, Any]] = []
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    keywords: List[str] = []
    citations: int = 0
    affiliations: List[str] = []
    references: List[Dict[str, Any]] = []


class EntityResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class SearchResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]] = []
    total: int = 0


class NetworkResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]


# ========== 依赖注入 ==========

def get_query_engine():
    """获取查询引擎"""
    client = get_neo4j_client()
    if not client.is_connected():
        if not init_neo4j():
            raise HTTPException(status_code=503, detail="Neo4j database not available")
    return QueryEngine(client)


def get_knowledge_builder():
    """获取知识构建器"""
    client = get_neo4j_client()
    if not client.is_connected():
        if not init_neo4j():
            raise HTTPException(status_code=503, detail="Neo4j database not available")
    return KnowledgeBuilder(client)


# ========== 健康检查 ==========

@router.get("/health")
async def health_check():
    """检查Neo4j连接状态"""
    client = get_neo4j_client()
    if client.is_connected():
        stats = client.get_statistics()
        return {
            "status": "healthy",
            "connected": True,
            "statistics": stats
        }
    else:
        # 尝试连接
        if init_neo4j():
            stats = client.get_statistics()
            return {
                "status": "healthy",
                "connected": True,
                "statistics": stats
            }
        return {
            "status": "unhealthy",
            "connected": False,
            "error": "Failed to connect to Neo4j"
        }


# ========== 实体查询 ==========

@router.get("/author/{author_id}", response_model=EntityResponse)
async def get_author(
    author_id: str,
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取作者详情"""
    author = engine.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return EntityResponse(success=True, data=author)


@router.get("/paper/{paper_id}", response_model=EntityResponse)
async def get_paper(
    paper_id: str,
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取论文详情"""
    paper = engine.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return EntityResponse(success=True, data=paper)


@router.get("/concept/{concept_name}", response_model=EntityResponse)
async def get_concept(
    concept_name: str,
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取概念详情"""
    concept = engine.get_concept_by_name(concept_name)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    return EntityResponse(success=True, data=concept)


# ========== 搜索 ==========

@router.get("/search/authors", response_model=SearchResponse)
async def search_authors(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    engine: QueryEngine = Depends(get_query_engine)
):
    """搜索作者"""
    results = engine.search_authors(q, limit)
    return SearchResponse(
        success=True,
        results=results,
        total=len(results)
    )


@router.get("/search/papers", response_model=SearchResponse)
async def search_papers(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    engine: QueryEngine = Depends(get_query_engine)
):
    """搜索论文"""
    results = engine.search_papers(q, limit)
    return SearchResponse(
        success=True,
        results=results,
        total=len(results)
    )


# ========== 关系网络 ==========

@router.get("/network/citation/{paper_id}", response_model=NetworkResponse)
async def get_citation_network(
    paper_id: str,
    depth: int = Query(2, ge=1, le=5),
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取引用网络"""
    network = engine.get_citation_network(paper_id, depth)
    return NetworkResponse(**network)


@router.get("/network/collaboration/{author_id}", response_model=NetworkResponse)
async def get_collaboration_network(
    author_id: str,
    depth: int = Query(2, ge=1, le=4),
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取合作网络"""
    network = engine.get_collaboration_network(author_id, depth)
    return NetworkResponse(**network)


@router.get("/author/{author_id}/coauthors")
async def get_coauthors(
    author_id: str,
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取合作者列表"""
    coauthors = engine.get_coauthors(author_id)
    return {
        "success": True,
        "coauthors": coauthors,
        "total": len(coauthors)
    }


# ========== 推荐 ==========

@router.get("/recommend/papers/{author_id}")
async def recommend_papers(
    author_id: str,
    limit: int = Query(10, ge=1, le=50),
    engine: QueryEngine = Depends(get_query_engine)
):
    """推荐论文"""
    papers = engine.recommend_papers(author_id, limit)
    return {
        "success": True,
        "papers": papers,
        "total": len(papers)
    }


@router.get("/recommend/collaborators/{author_id}")
async def recommend_collaborators(
    author_id: str,
    limit: int = Query(10, ge=1, le=50),
    engine: QueryEngine = Depends(get_query_engine)
):
    """推荐合作者"""
    collaborators = engine.recommend_collaborators(author_id, limit)
    return {
        "success": True,
        "collaborators": collaborators,
        "total": len(collaborators)
    }


# ========== 相似度 ==========

@router.get("/similar/papers/{paper_id}")
async def find_similar_papers(
    paper_id: str,
    limit: int = Query(10, ge=1, le=50),
    engine: QueryEngine = Depends(get_query_engine)
):
    """找到相似论文"""
    similar = engine.find_similar_papers(paper_id, limit)
    return {
        "success": True,
        "papers": [
            {
                "paper": s.entity,
                "similarity": s.similarity,
                "reason": s.reason
            }
            for s in similar
        ]
    }


@router.get("/similar/authors/{author_id}")
async def find_similar_authors(
    author_id: str,
    limit: int = Query(10, ge=1, le=50),
    engine: QueryEngine = Depends(get_query_engine)
):
    """找到相似作者"""
    similar = engine.find_similar_authors(author_id, limit)
    return {
        "success": True,
        "authors": [
            {
                "author": s.entity,
                "similarity": s.similarity,
                "reason": s.reason
            }
            for s in similar
        ]
    }


# ========== 统计分析 ==========

@router.get("/stats/trending")
async def get_trending_topics(
    year: int = Query(..., description="Year to analyze"),
    limit: int = Query(10, ge=1, le=100),
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取热门研究主题"""
    topics = engine.get_trending_topics(year, limit)
    return {
        "success": True,
        "year": year,
        "topics": topics
    }


@router.get("/stats/ranking/authors")
async def get_author_ranking(
    metric: str = Query("h_index", enum=["h_index", "citations", "papers"]),
    limit: int = Query(100, ge=1, le=500),
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取作者排名"""
    ranking = engine.get_author_ranking(metric, limit)
    return {
        "success": True,
        "metric": metric,
        "ranking": ranking
    }


@router.get("/stats/ranking/institutions")
async def get_institution_ranking(
    limit: int = Query(50, ge=1, le=200),
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取机构排名"""
    ranking = engine.get_institution_ranking(limit)
    return {
        "success": True,
        "ranking": ranking
    }


@router.get("/stats/concept/{concept_name}/evolution")
async def get_concept_evolution(
    concept_name: str,
    start_year: int = Query(..., description="Start year"),
    end_year: int = Query(..., description="End year"),
    engine: QueryEngine = Depends(get_query_engine)
):
    """获取概念演变"""
    evolution = engine.get_concept_evolution(concept_name, start_year, end_year)
    return {
        "success": True,
        "concept": concept_name,
        "evolution": evolution
    }


# ========== 知识图谱构建 ==========

@router.post("/build/paper")
async def build_from_paper(
    paper: PaperInput,
    builder: KnowledgeBuilder = Depends(get_knowledge_builder)
):
    """从单篇论文构建知识图谱"""
    paper_data = paper.dict()
    success = builder.build_from_paper(paper_data)

    if success:
        return {
            "success": True,
            "message": "Knowledge graph built successfully"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to build knowledge graph"
        )


@router.post("/build/papers")
async def build_from_papers(
    papers: List[PaperInput],
    builder: KnowledgeBuilder = Depends(get_knowledge_builder)
):
    """从多篇论文批量构建知识图谱"""
    papers_data = [p.dict() for p in papers]
    stats = builder.build_from_papers(papers_data)

    return {
        "success": True,
        "stats": stats
    }


@router.get("/path/{from_author_id}/{to_author_id}")
async def find_research_path(
    from_author_id: str,
    to_author_id: str,
    engine: QueryEngine = Depends(get_query_engine)
):
    """查找两个作者之间的最短路径（Erdős数）"""
    path = engine.find_research_path(from_author_id, to_author_id)

    if path:
        return {
            "success": True,
            "path_exists": True,
            "path_length": path.length,
            "nodes": path.nodes,
            "relationships": path.relationships
        }
    else:
        return {
            "success": True,
            "path_exists": False,
            "message": "No path found between authors"
        }
