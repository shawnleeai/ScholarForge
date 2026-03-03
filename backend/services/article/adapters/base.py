"""
文献数据源适配器基类
定义统一的数据源接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any


@dataclass
class ArticleData:
    """文献数据结构"""
    doi: Optional[str] = None
    title: str = ""
    authors: List[Dict[str, str]] = field(default_factory=list)
    abstract: Optional[str] = None
    source_type: Optional[str] = None  # journal, conference, book, thesis
    source_name: Optional[str] = None
    source_db: Optional[str] = None  # cnki, wos, ieee, arxiv
    publication_year: Optional[int] = None
    publication_date: Optional[date] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    citation_count: int = 0
    impact_factor: Optional[float] = None
    pdf_url: Optional[str] = None
    source_url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """搜索结果"""
    articles: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    source: str
    query: str
    filters: Dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    """数据源适配器基类"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称"""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResult:
        """
        搜索文献

        Args:
            query: 搜索关键词
            page: 页码
            page_size: 每页数量
            filters: 过滤条件
        """
        pass

    @abstractmethod
    async def get_by_doi(self, doi: str) -> Optional[ArticleData]:
        """通过DOI获取文献"""
        pass

    @abstractmethod
    async def get_by_id(self, article_id: str) -> Optional[ArticleData]:
        """通过ID获取文献"""
        pass

    def _article_to_dict(self, article: ArticleData) -> Dict[str, Any]:
        """将ArticleData转换为字典"""
        return {
            "doi": article.doi,
            "title": article.title,
            "authors": article.authors,
            "abstract": article.abstract,
            "source_type": article.source_type,
            "source_name": article.source_name,
            "source_db": article.source_db,
            "publication_year": article.publication_year,
            "publication_date": article.publication_date.isoformat() if article.publication_date else None,
            "volume": article.volume,
            "issue": article.issue,
            "pages": article.pages,
            "keywords": article.keywords,
            "citation_count": article.citation_count,
            "impact_factor": article.impact_factor,
            "pdf_url": article.pdf_url,
            "source_url": article.source_url,
        }
