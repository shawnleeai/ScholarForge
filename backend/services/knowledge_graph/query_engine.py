"""
知识图谱查询引擎
提供知识图谱的查询和分析功能
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .neo4j_client import Neo4jClient, get_neo4j_client


@dataclass
class PathResult:
    """路径查询结果"""
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    length: int


@dataclass
class SimilarityResult:
    """相似度查询结果"""
    entity: Dict[str, Any]
    similarity: float
    reason: str


class QueryEngine:
    """
    知识图谱查询引擎
    封装常用的图查询操作
    """

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        self.client = neo4j_client or get_neo4j_client()

    # ========== 基础查询 ==========

    def get_author_by_id(self, author_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取作者信息"""
        query = """
        MATCH (a:Author {id: $author_id})
        RETURN a {
            .*,
            papers: [(a)-[:AUTHORED]->(p:Paper) | p {.*}],
            coauthors: [(a)-[:CO_AUTHOR]-(c:Author) | c {.*}],
            institutions: [(a)-[:AFFILIATED_WITH]->(i:Institution) | i {.*}]
        } as author
        """
        result = self.client.run_query(query, {'author_id': author_id})
        return result[0]['author'] if result else None

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取论文信息"""
        query = """
        MATCH (p:Paper {id: $paper_id})
        RETURN p {
            .*,
            authors: [(a:Author)-[:AUTHORED]->(p) | a {.*}],
            concepts: [(p)-[:BELONGS_TO]->(c:Concept) | c.name],
            citations_out: [(p)-[:CITES]->(cited:Paper) | cited {.*}],
            citations_in: [(citing:Paper)-[:CITES]->(p) | citing {.*}]
        } as paper
        """
        result = self.client.run_query(query, {'paper_id': paper_id})
        return result[0]['paper'] if result else None

    def search_authors(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索作者"""
        query = """
        MATCH (a:Author)
        WHERE a.name CONTAINS $name
        RETURN a {
            .*,
            paper_count: count {(a)-[:AUTHORED]->(:Paper)}
        } as author
        ORDER BY a.h_index DESC
        LIMIT $limit
        """
        result = self.client.run_query(query, {'name': name, 'limit': limit})
        return [r['author'] for r in result]

    def search_papers(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索论文"""
        query = """
        MATCH (p:Paper)
        WHERE p.title CONTAINS $keyword OR p.abstract CONTAINS $keyword
        RETURN p {
            .*,
            authors: [(a:Author)-[:AUTHORED]->(p) | a.name]
        } as paper
        ORDER BY p.citations DESC
        LIMIT $limit
        """
        result = self.client.run_query(query, {'keyword': keyword, 'limit': limit})
        return [r['paper'] for r in result]

    def get_concept_by_name(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """获取概念信息"""
        query = """
        MATCH (c:Concept {name: $concept_name})
        RETURN c {
            .*,
            papers: [(p:Paper)-[:BELONGS_TO]->(c) | p {.*}],
            paper_count: count {(p:Paper)-[:BELONGS_TO]->(c)}
        } as concept
        """
        result = self.client.run_query(query, {'concept_name': concept_name})
        return result[0]['concept'] if result else None

    # ========== 关系查询 ==========

    def get_coauthors(self, author_id: str) -> List[Dict[str, Any]]:
        """获取合作者"""
        query = """
        MATCH (a:Author {id: $author_id})-[:CO_AUTHOR]-(coauthor:Author)
        RETURN coauthor {
            .*,
            collaboration_count: count {(a)-[:CO_AUTHOR]-(coauthor)},
            shared_papers: [(a)-[:CO_AUTHOR]-(coauthor)-[:AUTHORED]->(p:Paper) | p.title]
        } as coauthor
        ORDER BY collaboration_count DESC
        """
        result = self.client.run_query(query, {'author_id': author_id})
        return [r['coauthor'] for r in result]

    def get_citation_network(
        self,
        paper_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        获取引用网络

        Args:
            paper_id: 论文ID
            depth: 搜索深度（引用关系层级）
        """
        query = """
        MATCH path = (p:Paper {id: $paper_id})-[:CITES*1..$depth]-(related:Paper)
        RETURN {
            nodes: [n in nodes(path) | n {.*}],
            relationships: [r in relationships(path) | {type: type(r), start: startNode(r).id, end: endNode(r).id}],
            paper: p {.*}
        } as network
        LIMIT 100
        """
        result = self.client.run_query(query, {'paper_id': paper_id, 'depth': depth})

        if not result:
            return {'nodes': [], 'links': []}

        # 处理结果，去重
        nodes = {}
        links = []

        for record in result:
            network = record['network']
            for node in network['nodes']:
                if 'id' in node:
                    nodes[node['id']] = node
            for rel in network['relationships']:
                links.append(rel)

        return {
            'nodes': list(nodes.values()),
            'links': links
        }

    def get_collaboration_network(
        self,
        author_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """获取作者合作网络"""
        query = """
        MATCH path = (a:Author {id: $author_id})-[:CO_AUTHOR*1..$depth]-(related:Author)
        RETURN {
            nodes: [n in nodes(path) | n {.*}],
            relationships: [r in relationships(path) | {type: type(r), source: startNode(r).id, target: endNode(r).id, paper_id: r.paper_id}],
            author: a {.*}
        } as network
        LIMIT 100
        """
        result = self.client.run_query(query, {'author_id': author_id, 'depth': depth})

        if not result:
            return {'nodes': [], 'links': []}

        nodes = {}
        links = []

        for record in result:
            network = record['network']
            for node in network['nodes']:
                if 'id' in node:
                    nodes[node['id']] = node
            for rel in network['relationships']:
                links.append(rel)

        return {
            'nodes': list(nodes.values()),
            'links': links
        }

    # ========== 推荐查询 ==========

    def recommend_papers(
        self,
        author_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        基于作者兴趣推荐论文
        基于：作者的研究概念、合作者发表的论文
        """
        query = """
        MATCH (a:Author {id: $author_id})
        // 获取作者的概念兴趣
        MATCH (a)-[:AUTHORED]->(:Paper)-[:BELONGS_TO]->(concept:Concept)
        WITH a, concept, count(*) as concept_freq
        ORDER BY concept_freq DESC
        LIMIT 5
        // 找到相似概念的论文
        MATCH (concept)<-[:BELONGS_TO]-(rec:Paper)
        WHERE NOT (a)-[:AUTHORED]->(rec)
        RETURN rec {
            .*,
            match_concepts: collect(concept.name),
            relevance_score: sum(concept_freq)
        } as paper
        ORDER BY relevance_score DESC, rec.citations DESC
        LIMIT $limit
        """
        result = self.client.run_query(query, {'author_id': author_id, 'limit': limit})
        return [r['paper'] for r in result]

    def recommend_collaborators(
        self,
        author_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        推荐潜在合作者
        基于：共同概念、间接合作关系
        """
        query = """
        MATCH (a:Author {id: $author_id})
        // 找到研究相似概念的作者
        MATCH (a)-[:AUTHORED]->(:Paper)-[:BELONGS_TO]->(concept:Concept)
        MATCH (concept)<-[:BELONGS_TO]-(:Paper)<-[:AUTHORED]-(potential:Author)
        WHERE a <> potential
        AND NOT (a)-[:CO_AUTHOR]-(potential)
        // 计算相似度分数
        WITH potential, count(DISTINCT concept) as common_concepts,
             collect(DISTINCT concept.name) as shared_topics
        RETURN potential {
            .*,
            common_concepts: common_concepts,
            shared_topics: shared_topics,
            recommendation_reason: 'Research similar topics'
        } as author
        ORDER BY common_concepts DESC
        LIMIT $limit
        """
        result = self.client.run_query(query, {'author_id': author_id, 'limit': limit})
        return [r['author'] for r in result]

    def find_research_path(
        self,
        from_author_id: str,
        to_author_id: str
    ) -> Optional[PathResult]:
        """
        找到两个作者之间的最短路径（ Erdős数概念）
        """
        query = """
        MATCH path = shortestPath(
            (a1:Author {id: $from_id})-[:CO_AUTHOR*]-(a2:Author {id: $to_id})
        )
        RETURN {
            nodes: [n in nodes(path) | n {.*}],
            relationships: [r in relationships(path) | {type: type(r), source: startNode(r).id, target: endNode(r).id}],
            length: length(path)
        } as result
        """
        result = self.client.run_query(query, {
            'from_id': from_author_id,
            'to_id': to_author_id
        })

        if not result:
            return None

        data = result[0]['result']
        return PathResult(
            nodes=data['nodes'],
            relationships=data['relationships'],
            length=data['length']
        )

    # ========== 统计分析 ==========

    def get_trending_topics(self, year: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门研究主题"""
        query = """
        MATCH (p:Paper)-[:BELONGS_TO]->(c:Concept)
        WHERE p.year = $year
        RETURN c.name as concept,
               count(p) as paper_count,
               avg(p.citations) as avg_citations
        ORDER BY paper_count DESC, avg_citations DESC
        LIMIT $limit
        """
        result = self.client.run_query(query, {'year': year, 'limit': limit})
        return result

    def get_author_ranking(
        self,
        metric: str = 'h_index',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取作者排名

        Args:
            metric: 排序指标 ('h_index', 'citations', 'papers')
            limit: 返回数量
        """
        if metric == 'h_index':
            order_by = 'a.h_index'
        elif metric == 'citations':
            order_by = 'total_citations'
        elif metric == 'papers':
            order_by = 'paper_count'
        else:
            order_by = 'a.h_index'

        query = f"""
        MATCH (a:Author)-[:AUTHORED]->(p:Paper)
        WITH a, count(p) as paper_count, sum(p.citations) as total_citations
        RETURN a {{
            .*,
            paper_count: paper_count,
            total_citations: total_citations
        }} as author
        ORDER BY {order_by} DESC
        LIMIT $limit
        """
        result = self.client.run_query(query, {'limit': limit})
        return [r['author'] for r in result]

    def get_institution_ranking(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取机构排名"""
        query = """
        MATCH (i:Institution)<-[:AFFILIATED_WITH]-(a:Author)-[:AUTHORED]->(p:Paper)
        RETURN i {.*,
            author_count: count(DISTINCT a),
            paper_count: count(DISTINCT p),
            total_citations: sum(p.citations)
        } as institution
        ORDER BY total_citations DESC
        LIMIT $limit
        """
        result = self.client.run_query(query, {'limit': limit})
        return [r['institution'] for r in result]

    def get_concept_evolution(
        self,
        concept_name: str,
        start_year: int,
        end_year: int
    ) -> List[Dict[str, Any]]:
        """获取概念随时间的演变"""
        query = """
        MATCH (c:Concept {name: $concept})<-[:BELONGS_TO]-(p:Paper)
        WHERE p.year >= $start_year AND p.year <= $end_year
        RETURN p.year as year,
               count(p) as paper_count,
               avg(p.citations) as avg_citations
        ORDER BY year
        """
        result = self.client.run_query(query, {
            'concept': concept_name,
            'start_year': start_year,
            'end_year': end_year
        })
        return result

    # ========== 相似度查询 ==========

    def find_similar_papers(
        self,
        paper_id: str,
        limit: int = 10
    ) -> List[SimilarityResult]:
        """
        找到相似论文
        基于：共享概念、引用关系
        """
        query = """
        MATCH (p:Paper {id: $paper_id})-[:BELONGS_TO]->(concept:Concept)
        WITH p, collect(concept) as concepts
        MATCH (similar:Paper)-[:BELONGS_TO]->(shared_concept:Concept)
        WHERE similar <> p AND shared_concept IN concepts
        WITH similar,
             count(DISTINCT shared_concept) as common_concepts,
             collect(DISTINCT shared_concept.name) as shared_concept_names
        RETURN similar {.*,
            common_concepts: common_concepts,
            shared_concepts: shared_concept_names
        } as paper,
        common_concepts as similarity_score
        ORDER BY similarity_score DESC, similar.citations DESC
        LIMIT $limit
        """
        result = self.client.run_query(query, {'paper_id': paper_id, 'limit': limit})

        return [
            SimilarityResult(
                entity=r['paper'],
                similarity=r['similarity_score'] / 10.0,  # 归一化
                reason=f"Share {r['similarity_score']} concepts"
            )
            for r in result
        ]

    def find_similar_authors(
        self,
        author_id: str,
        limit: int = 10
    ) -> List[SimilarityResult]:
        """找到相似作者"""
        query = """
        MATCH (a:Author {id: $author_id})-[:AUTHORED]->(:Paper)-[:BELONGS_TO]->(concept:Concept)
        WITH a, collect(concept) as concepts
        MATCH (similar:Author)-[:AUTHORED]->(:Paper)-[:BELONGS_TO]->(shared_concept:Concept)
        WHERE similar <> a AND shared_concept IN concepts
        WITH similar, count(DISTINCT shared_concept) as common_concepts
        RETURN similar {.*, common_concepts: common_concepts} as author,
               common_concepts as similarity_score
        ORDER BY similarity_score DESC
        LIMIT $limit
        """
        result = self.client.run_query(query, {'author_id': author_id, 'limit': limit})

        return [
            SimilarityResult(
                entity=r['author'],
                similarity=r['similarity_score'] / 10.0,
                reason=f"Research {r['similarity_score']} common topics"
            )
            for r in result
        ]


if __name__ == "__main__":
    from neo4j_client import init_neo4j

    if init_neo4j():
        print("✅ Neo4j connected")

        engine = QueryEngine()

        # 测试查询
        print("\n📊 Database statistics:")
        stats = engine.client.get_statistics()
        print(stats)

        # 搜索作者
        print("\n🔍 Searching authors with 'Yoshua':")
        authors = engine.search_authors("Yoshua")
        for a in authors:
            print(f"  - {a['name']}")

        # 热门主题
        print("\n🔥 Trending topics in 2023:")
        trends = engine.get_trending_topics(2023, 5)
        for t in trends:
            print(f"  - {t['concept']}: {t['paper_count']} papers")

    else:
        print("❌ Failed to connect to Neo4j")
