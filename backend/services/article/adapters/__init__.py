"""
文献数据源适配器
多源统一接口
"""

from .base import BaseAdapter, SearchResult
from .cnki import CNKIAdapter
from .wos import WoSAdapter
from .ieee import IEEEAdapter
from .arxiv import ArxivAdapter
from .semantic_scholar import SemanticScholarAdapter

__all__ = [
    "BaseAdapter",
    "SearchResult",
    "CNKIAdapter",
    "WoSAdapter",
    "IEEEAdapter",
    "ArxivAdapter",
    "SemanticScholarAdapter",
]
