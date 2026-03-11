"""
知识图谱构建器
将抽取的实体构建为知识图谱，存储到Neo4j
"""

from typing import List, Dict, Any, Optional
from dataclasses import asdict

from .neo4j_client import Neo4jClient, get_neo4j_client
from .entity_extractor import (
    EntityExtractor,
    ExtractedEntities,
    Author,
    Paper,
    Concept,
    Institution
)


class KnowledgeBuilder:
    """
    知识图谱构建器
    负责将实体和关系导入Neo4j
    """

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        self.client = neo4j_client or get_neo4j_client()
        self.extractor = EntityExtractor()

    def build_from_paper(self, paper_data: Dict[str, Any]) -> bool:
        """
        从单篇论文构建知识图谱

        Args:
            paper_data: 论文数据

        Returns:
            是否成功
        """
        try:
            entities = self.extractor.extract_from_paper(paper_data)
            self._insert_entities(entities)
            self._build_relationships(entities, paper_data)
            return True
        except Exception as e:
            print(f"Error building knowledge graph: {e}")
            return False

    def build_from_papers(self, papers_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        从多篇论文批量构建知识图谱

        Args:
            papers_data: 论文数据列表

        Returns:
            统计信息
        """
        stats = {'success': 0, 'failed': 0}

        for paper_data in papers_data:
            if self.build_from_paper(paper_data):
                stats['success'] += 1
            else:
                stats['failed'] += 1

        return stats

    def _insert_entities(self, entities: ExtractedEntities):
        """插入实体到数据库"""
        # 插入作者
        for author in entities.authors:
            self._create_author(author)

        # 插入论文
        for paper in entities.papers:
            self._create_paper(paper)

        # 插入概念
        for concept in entities.concepts:
            self._create_concept(concept)

        # 插入机构
        for institution in entities.institutions:
            self._create_institution(institution)

    def _create_author(self, author: Author):
        """创建作者节点"""
        query = """
        MERGE (a:Author {id: $id})
        ON CREATE SET
            a.name = $name,
            a.email = $email,
            a.orcid = $orcid,
            a.h_index = $h_index,
            a.created_at = datetime()
        ON MATCH SET
            a.name = $name,
            a.email = $email,
            a.orcid = $orcid,
            a.h_index = $h_index,
            a.updated_at = datetime()
        """
        self.client.execute_write(query, {
            'id': author.id,
            'name': author.name,
            'email': author.email,
            'orcid': author.orcid,
            'h_index': author.h_index
        })

    def _create_paper(self, paper: Paper):
        """创建论文节点"""
        query = """
        MERGE (p:Paper {id: $id})
        ON CREATE SET
            p.title = $title,
            p.abstract = $abstract,
            p.year = $year,
            p.venue = $venue,
            p.doi = $doi,
            p.citations = $citations,
            p.keywords = $keywords,
            p.created_at = datetime()
        ON MATCH SET
            p.title = $title,
            p.abstract = $abstract,
            p.year = $year,
            p.venue = $venue,
            p.doi = $doi,
            p.citations = $citations,
            p.keywords = $keywords,
            p.updated_at = datetime()
        """
        self.client.execute_write(query, {
            'id': paper.id,
            'title': paper.title,
            'abstract': paper.abstract,
            'year': paper.year,
            'venue': paper.venue,
            'doi': paper.doi,
            'citations': paper.citations,
            'keywords': paper.keywords
        })

    def _create_concept(self, concept: Concept):
        """创建概念节点"""
        query = """
        MERGE (c:Concept {name: $name})
        ON CREATE SET
            c.category = $category,
            c.description = $description,
            c.created_at = datetime()
        ON MATCH SET
            c.category = $category,
            c.description = $description,
            c.updated_at = datetime()
        """
        self.client.execute_write(query, {
            'name': concept.name,
            'category': concept.category,
            'description': concept.description
        })

    def _create_institution(self, institution: Institution):
        """创建机构节点"""
        query = """
        MERGE (i:Institution {id: $id})
        ON CREATE SET
            i.name = $name,
            i.location = $location,
            i.type = $type,
            i.created_at = datetime()
        ON MATCH SET
            i.name = $name,
            i.location = $location,
            i.type = $type,
            i.updated_at = datetime()
        """
        self.client.execute_write(query, {
            'id': institution.id,
            'name': institution.name,
            'location': institution.location,
            'type': institution.type
        })

    def _build_relationships(self, entities: ExtractedEntities, paper_data: Dict[str, Any]):
        """构建实体之间的关系"""
        paper_id = entities.papers[0].id if entities.papers else None
        if not paper_id:
            return

        # 1. 作者-论文关系 (AUTHORED)
        for i, author in enumerate(entities.authors):
            self._create_authored_rel(author.id, paper_id, i + 1)

        # 2. 论文-概念关系 (BELONGS_TO)
        for concept in entities.concepts:
            self._create_belongs_to_rel(paper_id, concept.name)

        # 3. 作者-机构关系 (AFFILIATED_WITH)
        for author in entities.authors:
            if author.affiliation:
                inst_id = self._find_institution_by_name(author.affiliation)
                if inst_id:
                    self._create_affiliated_rel(author.id, inst_id)

        # 4. 引用关系 (CITES)
        references = paper_data.get('references', [])
        for ref in references:
            ref_id = ref.get('doi') or ref.get('id')
            if ref_id:
                self._create_citation_rel(paper_id, ref_id)

        # 5. 合作者关系 (CO_AUTHOR)
        author_ids = [a.id for a in entities.authors]
        for i in range(len(author_ids)):
            for j in range(i + 1, len(author_ids)):
                self._create_coauthor_rel(author_ids[i], author_ids[j], paper_id)

    def _create_authored_rel(self, author_id: str, paper_id: str, order: int):
        """创建作者-论文关系"""
        query = """
        MATCH (a:Author {id: $author_id})
        MATCH (p:Paper {id: $paper_id})
        MERGE (a)-[r:AUTHORED]->(p)
        ON CREATE SET
            r.order = $order,
            r.created_at = datetime()
        """
        self.client.execute_write(query, {
            'author_id': author_id,
            'paper_id': paper_id,
            'order': order
        })

    def _create_belongs_to_rel(self, paper_id: str, concept_name: str):
        """创建论文-概念关系"""
        query = """
        MATCH (p:Paper {id: $paper_id})
        MATCH (c:Concept {name: $concept_name})
        MERGE (p)-[r:BELONGS_TO]->(c)
        ON CREATE SET r.created_at = datetime()
        """
        self.client.execute_write(query, {
            'paper_id': paper_id,
            'concept_name': concept_name
        })

    def _create_affiliated_rel(self, author_id: str, institution_id: str):
        """创建作者-机构关系"""
        query = """
        MATCH (a:Author {id: $author_id})
        MATCH (i:Institution {id: $institution_id})
        MERGE (a)-[r:AFFILIATED_WITH]->(i)
        ON CREATE SET r.created_at = datetime()
        """
        self.client.execute_write(query, {
            'author_id': author_id,
            'institution_id': institution_id
        })

    def _create_citation_rel(self, from_paper_id: str, to_paper_id: str):
        """创建引用关系"""
        query = """
        MATCH (p1:Paper {id: $from_id})
        MATCH (p2:Paper {id: $to_id})
        MERGE (p1)-[r:CITES]->(p2)
        ON CREATE SET r.created_at = datetime()
        """
        self.client.execute_write(query, {
            'from_id': from_paper_id,
            'to_id': to_paper_id
        })

    def _create_coauthor_rel(self, author1_id: str, author2_id: str, paper_id: str):
        """创建合作关系"""
        query = """
        MATCH (a1:Author {id: $author1_id})
        MATCH (a2:Author {id: $author2_id})
        MATCH (p:Paper {id: $paper_id})
        MERGE (a1)-[r:CO_AUTHOR]->(a2)
        ON CREATE SET
            r.paper_id = $paper_id,
            r.created_at = datetime()
        ON MATCH SET
            r.paper_id = $paper_id,
            r.updated_at = datetime()
        """
        self.client.execute_write(query, {
            'author1_id': author1_id,
            'author2_id': author2_id,
            'paper_id': paper_id
        })

    def _find_institution_by_name(self, name: str) -> Optional[str]:
        """根据名称查找机构ID"""
        query = """
        MATCH (i:Institution)
        WHERE i.name CONTAINS $name OR $name CONTAINS i.name
        RETURN i.id as id
        LIMIT 1
        """
        result = self.client.run_query(query, {'name': name})
        return result[0]['id'] if result else None

    def update_citation_count(self, paper_id: str, citations: int):
        """更新论文引用数"""
        query = """
        MATCH (p:Paper {id: $paper_id})
        SET p.citations = $citations,
            p.updated_at = datetime()
        """
        self.client.execute_write(query, {
            'paper_id': paper_id,
            'citations': citations
        })

    def update_author_metrics(self, author_id: str, h_index: int):
        """更新作者指标"""
        query = """
        MATCH (a:Author {id: $author_id})
        SET a.h_index = $h_index,
            a.updated_at = datetime()
        """
        self.client.execute_write(query, {
            'author_id': author_id,
            'h_index': h_index
        })


if __name__ == "__main__":
    # 测试
    from neo4j_client import init_neo4j

    if init_neo4j():
        print("✅ Neo4j initialized")

        builder = KnowledgeBuilder()

        test_paper = {
            'title': 'Deep Learning for Natural Language Processing: A Survey',
            'abstract': 'This paper surveys deep learning techniques for NLP.',
            'authors': [
                {'name': 'Yoshua Bengio', 'email': 'yoshua@example.com'},
                {'name': 'Geoffrey Hinton', 'email': 'geoffrey@example.com'}
            ],
            'year': 2023,
            'venue': 'Nature Machine Intelligence',
            'doi': '10.1038/s42256-023-00611-3',
            'keywords': ['deep learning', 'NLP', 'transformer', 'BERT'],
            'citations': 1500,
            'affiliations': [
                'University of Montreal',
                'University of Toronto'
            ],
            'references': [
                {'doi': '10.5555/1953048.2078195', 'title': 'Original Transformer Paper'},
                {'doi': '10.18653/v1/N19-1423', 'title': 'BERT Paper'}
            ]
        }

        if builder.build_from_paper(test_paper):
            print("✅ Knowledge graph built successfully")
        else:
            print("❌ Failed to build knowledge graph")

        # 获取统计
        stats = builder.client.get_statistics()
        print(f"📊 Current statistics: {stats}")
    else:
        print("❌ Failed to initialize Neo4j")
