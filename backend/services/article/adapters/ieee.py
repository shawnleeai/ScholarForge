"""
IEEE Xplore 适配器
"""

import asyncio
from typing import Any, Dict, List, Optional

import httpx

from .base import BaseAdapter, SearchResult


class IEEEAdapter(BaseAdapter):
    """IEEE Xplore 适配器"""

    BASE_URL = "https://ieeexploreapi.ieee.org/api/v1"

    @property
    def source_name(self) -> str:
        return "ieee"

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResult:
        """
        搜索IEEE Xplore文献
        """
        filters = filters or {}

        params = {
            "querytext": query,
            "start": (page - 1) * page_size,
            "max_records": page_size,
        }

        if filters.get("year_from"):
            params["publication_year"] = f"{filters['year_from']}-"

        if self.api_key:
            params["apikey"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # response = await client.get(f"{self.BASE_URL}/search", params=params)

                # 模拟返回数据
                mock_articles = self._generate_mock_results(query, page_size)

                return SearchResult(
                    articles=mock_articles,
                    total=60,
                    source=self.source_name,
                    page=page,
                    page_size=page_size,
                    has_more=page * page_size < 60,
                )

        except Exception:
            return SearchResult(
                articles=[],
                total=0,
                source=self.source_name,
                page=page,
                page_size=page_size,
                has_more=False,
            )

    async def get_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """通过DOI获取文献"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # response = await client.get(
                #     f"{self.BASE_URL}/document/{doi}",
                #     params={"apikey": self.api_key} if self.api_key else {}
                # )

                return self.normalize_article({
                    "doi": doi,
                    "title": f"IEEE Article: {doi}",
                    "authors": [{"name": "IEEE Author"}],
                    "source_name": "IEEE Transactions on Engineering Management",
                    "publication_year": 2024,
                })

        except Exception:
            return None

    async def get_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """通过IEEE文章ID获取"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                return self.normalize_article({
                    "id": article_id,
                    "doi": f"10.1109/ieee.{article_id}",
                    "title": f"IEEE Article {article_id}",
                    "authors": [{"name": "Author"}],
                    "source_name": "IEEE Access",
                    "publication_year": 2024,
                })

        except Exception:
            return None

    def _generate_mock_results(self, query: str, count: int) -> List[Dict[str, Any]]:
        """生成模拟搜索结果"""
        results = []
        publications = [
            "IEEE Transactions on Engineering Management",
            "IEEE Access",
            "Proceedings of the IEEE",
            "IEEE Software",
        ]

        for i in range(count):
            results.append(self.normalize_article({
                "id": f"ieee_{i}",
                "doi": f"10.1109/ieee.{i}",
                "title": f"Engineering Applications of {query} - Study {i+1}",
                "authors": [
                    {"name": "Chen Wei", "affiliation": "Tsinghua University"},
                    {"name": "Wang Ming", "affiliation": "Zhejiang University"},
                ],
                "abstract": f"This IEEE paper presents research on {query}...",
                "keywords": [query, "engineering", "technology"],
                "source_type": "journal" if i % 3 != 2 else "conference",
                "source_name": publications[i % len(publications)],
                "publication_year": 2024 - (i % 3),
                "citation_count": 30 + i,
                "source_url": f"https://ieeexplore.ieee.org/document/{i}",
            }))
        return results
