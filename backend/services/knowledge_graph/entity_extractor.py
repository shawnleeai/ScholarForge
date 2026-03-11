"""
实体抽取模块
从学术文本中抽取实体（作者、论文、概念、机构）
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Author:
    """作者实体"""
    id: str
    name: str
    email: Optional[str] = None
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    h_index: Optional[int] = None


@dataclass
class Paper:
    """论文实体"""
    id: str
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    citations: int = 0
    keywords: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class Concept:
    """概念/关键词实体"""
    name: str
    category: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Institution:
    """机构实体"""
    id: str
    name: str
    location: Optional[str] = None
    type: Optional[str] = None  # university, research_institute, company


@dataclass
class ExtractedEntities:
    """抽取结果"""
    authors: List[Author]
    papers: List[Paper]
    concepts: List[Concept]
    institutions: List[Institution]


class EntityExtractor:
    """
    实体抽取器
    从论文文本、引用数据中抽取实体
    """

    def __init__(self):
        self.academic_keywords = {
            'machine learning', 'deep learning', 'neural networks',
            'natural language processing', 'computer vision',
            'artificial intelligence', 'data mining',
            'big data', 'cloud computing', 'internet of things',
            'blockchain', 'cybersecurity', 'quantum computing',
            # 中文关键词
            '机器学习', '深度学习', '神经网络', '自然语言处理',
            '计算机视觉', '人工智能', '数据挖掘', '大数据',
            '云计算', '物联网', '区块链', '网络安全', '量子计算',
        }

    def extract_from_paper(
        self,
        paper_data: Dict[str, Any]
    ) -> ExtractedEntities:
        """
        从论文数据中提取实体

        Args:
            paper_data: 论文数据字典
                {
                    'title': str,
                    'abstract': str,
                    'authors': List[Dict],
                    'year': int,
                    'venue': str,
                    'doi': str,
                    'keywords': List[str],
                    'citations': int
                }

        Returns:
            抽取的实体集合
        """
        # 抽取论文
        paper = self._extract_paper(paper_data)

        # 抽取作者
        authors = self._extract_authors(
            paper_data.get('authors', []),
            paper_data.get('affiliations', [])
        )

        # 抽取概念/关键词
        concepts = self._extract_concepts(
            paper_data.get('keywords', []),
            paper_data.get('abstract', '')
        )

        # 抽取机构
        institutions = self._extract_institutions(
            paper_data.get('affiliations', [])
        )

        return ExtractedEntities(
            authors=authors,
            papers=[paper],
            concepts=concepts,
            institutions=institutions
        )

    def extract_from_text(self, text: str) -> ExtractedEntities:
        """
        从纯文本中抽取实体（简化版）

        Args:
            text: 论文文本内容

        Returns:
            抽取的实体集合
        """
        authors = self._extract_authors_from_text(text)
        concepts = self._extract_concepts_from_text(text)
        institutions = self._extract_institutions_from_text(text)

        return ExtractedEntities(
            authors=authors,
            papers=[],  # 需要更多上下文
            concepts=concepts,
            institutions=institutions
        )

    def _extract_paper(self, data: Dict[str, Any]) -> Paper:
        """抽取论文实体"""
        return Paper(
            id=data.get('doi') or data.get('id') or self._generate_id(),
            title=data.get('title', ''),
            abstract=data.get('abstract'),
            year=data.get('year'),
            venue=data.get('venue'),
            doi=data.get('doi'),
            citations=data.get('citations', 0),
            keywords=data.get('keywords', [])
        )

    def _extract_authors(
        self,
        authors_data: List[Dict],
        affiliations: List[str]
    ) -> List[Author]:
        """抽取作者实体"""
        authors = []
        for i, author_data in enumerate(authors_data):
            if isinstance(author_data, str):
                # 简单字符串格式
                author = Author(
                    id=self._generate_id(),
                    name=author_data,
                    affiliation=affiliations[i] if i < len(affiliations) else None
                )
            else:
                # 字典格式
                author = Author(
                    id=author_data.get('id') or self._generate_id(),
                    name=author_data.get('name', ''),
                    email=author_data.get('email'),
                    affiliation=author_data.get('affiliation') or (
                        affiliations[i] if i < len(affiliations) else None
                    ),
                    orcid=author_data.get('orcid')
                )
            authors.append(author)
        return authors

    def _extract_concepts(
        self,
        keywords: List[str],
        abstract: str
    ) -> List[Concept]:
        """抽取概念/关键词"""
        concepts = []

        # 从关键词列表提取
        for keyword in keywords:
            concepts.append(Concept(name=keyword.strip()))

        # 从摘要中提取额外概念
        abstract_concepts = self._extract_keywords_from_text(abstract)
        for concept_name in abstract_concepts:
            if not any(c.name == concept_name for c in concepts):
                concepts.append(Concept(name=concept_name))

        return concepts

    def _extract_institutions(self, affiliations: List[str]) -> List[Institution]:
        """抽取机构实体"""
        institutions = []
        for aff in affiliations:
            if not aff:
                continue

            # 清理机构名称
            name = self._clean_institution_name(aff)

            institution = Institution(
                id=self._generate_id(),
                name=name,
                location=self._extract_location(aff),
                type=self._classify_institution(name)
            )
            institutions.append(institution)

        return institutions

    def _extract_authors_from_text(self, text: str) -> List[Author]:
        """从文本中识别作者（简化版）"""
        # 匹配常见的作者格式
        patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # 英文姓名
            r'([\u4e00-\u9fa5]{2,4})',  # 中文姓名
        ]

        authors = []
        for pattern in patterns:
            matches = re.findall(pattern, text[:1000])  # 只在开头查找
            for name in matches[:10]:  # 限制数量
                authors.append(Author(
                    id=self._generate_id(),
                    name=name
                ))

        return authors

    def _extract_concepts_from_text(self, text: str) -> List[Concept]:
        """从文本中识别概念"""
        concepts = []
        text_lower = text.lower()

        for keyword in self.academic_keywords:
            if keyword in text_lower:
                concepts.append(Concept(name=keyword))

        return concepts

    def _extract_institutions_from_text(self, text: str) -> List[Institution]:
        """从文本中识别机构"""
        # 匹配常见的大学和研究机构的模式
        patterns = [
            r'([\u4e00-\u9fa5]+(?:大学|学院|研究所|研究院))',
            r'((?:University|College|Institute|Laboratory)\s+of\s+[\w\s]+)',
        ]

        institutions = []
        for pattern in patterns:
            matches = re.findall(pattern, text[:2000])
            for name in matches:
                institutions.append(Institution(
                    id=self._generate_id(),
                    name=name.strip(),
                    type='university' if 'University' in name or '大学' in name else 'research_institute'
                ))

        return institutions

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        keywords = []
        text_lower = text.lower()

        for keyword in self.academic_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        return keywords[:10]  # 限制数量

    def _clean_institution_name(self, name: str) -> str:
        """清理机构名称"""
        # 移除常见的无关文本
        name = re.sub(r'\d+', '', name)  # 移除数字
        name = re.sub(r',\s*$', '', name)  # 移除末尾逗号
        return name.strip()

    def _extract_location(self, affiliation: str) -> Optional[str]:
        """从机构信息中提取位置"""
        # 匹配城市/国家
        location_patterns = [
            r'([\u4e00-\u9fa5]+(?:市|省|国))',
            r',\s*([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)?)\s*$',
        ]

        for pattern in location_patterns:
            match = re.search(pattern, affiliation)
            if match:
                return match.group(1).strip()

        return None

    def _classify_institution(self, name: str) -> Optional[str]:
        """分类机构类型"""
        name_lower = name.lower()

        if any(word in name_lower for word in ['university', 'college', '大学', '学院']):
            return 'university'
        elif any(word in name_lower for word in ['institute', 'research', '研究所', '研究院']):
            return 'research_institute'
        elif any(word in name_lower for word in ['company', 'corp', '公司']):
            return 'company'
        elif any(word in name_lower for word in ['hospital', 'medical', '医院']):
            return 'hospital'

        return 'other'

    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())[:8]


# 便捷函数
def extract_entities_from_paper(paper_data: Dict[str, Any]) -> ExtractedEntities:
    """从论文数据中提取实体"""
    extractor = EntityExtractor()
    return extractor.extract_from_paper(paper_data)


def extract_entities_from_text(text: str) -> ExtractedEntities:
    """从文本中提取实体"""
    extractor = EntityExtractor()
    return extractor.extract_from_text(text)


if __name__ == "__main__":
    # 测试
    test_paper = {
        'title': 'Deep Learning for Natural Language Processing',
        'abstract': 'This paper explores deep learning techniques for NLP tasks including machine learning and neural networks.',
        'authors': [
            {'name': 'John Smith', 'email': 'john@example.com'},
            {'name': '张三', 'affiliation': '清华大学计算机系'}
        ],
        'year': 2024,
        'venue': 'ACL',
        'doi': '10.1234/example',
        'keywords': ['deep learning', 'NLP', 'neural networks'],
        'citations': 100,
        'affiliations': [
            'Stanford University, CA, USA',
            '清华大学, 北京, 中国'
        ]
    }

    extractor = EntityExtractor()
    entities = extractor.extract_from_paper(test_paper)

    print("Extracted Entities:")
    print(f"  Authors: {[a.name for a in entities.authors]}")
    print(f"  Papers: {[p.title for p in entities.papers]}")
    print(f"  Concepts: {[c.name for c in entities.concepts]}")
    print(f"  Institutions: {[i.name for i in entities.institutions]}")
