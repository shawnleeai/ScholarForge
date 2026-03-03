"""
Web of Science 适配器
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx

from .base import BaseAdapter, SearchResult


class WoSAdapter(BaseAdapter):
    """Web of Science 适配器"""

    BASE_URL = "https://api.clarivate.com/apis/wos-starter/v1"

    @property
    def source_name(self) -> str:
        return "wos"

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResult:
        """
        搜索Web of Science文献

        Args:
            query: 搜索关键词（支持WoS查询语法）
            page: 页码
            page_size: 每页数量
            filters: 过滤条件
        """
        filters = filters or {}

        # 构建WoS查询字符串
        wos_query = self._build_wos_query(query, filters)

        params = {
            "q": wos_query,
            "count": page_size,
            "first": (page - 1) * page_size + 1,
        }

        headers = {}
        if self.api_key:
            headers["X-ApiKey"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # response = await client.get(f"{self.BASE_URL}/documents", params=params, headers=headers)
                # data = response.json()

                # 模拟返回数据（开发阶段）
                mock_articles = self._generate_mock_results(query, page_size)

                return SearchResult(
                    articles=mock_articles,
                    total=80,
                    source=self.source_name,
                    page=page,
                    page_size=page_size,
                    has_more=page * page_size < 80,
                )

        except Exception as e:
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
        headers = {}
        if self.api_key:
            headers["X-ApiKey"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # response = await client.get(
                #     f"{self.BASE_URL}/documents",
                #     params={"q": f"DO={doi}"},
                #     headers=headers
                # )

                # 模拟返回
                return self.normalize_article({
                    "doi": doi,
                    "title": f"Article with DOI: {doi}",
                    "authors": [{"name": "John Doe"}, {"name": "Jane Smith"}],
                    "abstract": "Abstract content...",
                    "source_name": "Nature",
                    "publication_year": 2024,
                    "citation_count": 50,
                })

        except Exception:
            return None

    async def get_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """通过UT（WoS唯一标识符）获取文献"""
        headers = {}
        if self.api_key:
            headers["X-ApiKey"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # response = await client.get(f"{self.BASE_URL}/documents/{article_id}", headers=headers)

                return self.normalize_article({
                    "id": article_id,
                    "doi": f"10.xxxx/wos.{article_id}",
                    "title": f"Article {article_id}",
                    "authors": [{"name": "Author Name"}],
                    "source_name": "Science",
                    "publication_year": 2024,
                })

        except Exception:
            return None

    def _build_wos_query(self, query: str, filters: Dict[str, Any]) -> str:
        """构建WoS查询字符串"""
        parts = [f"TS=({query})"]  # 主题搜索

        if filters.get("year_from") or filters.get("year_to"):
            year_from = filters.get("year_from", 1900)
            year_to = filters.get("year_to", datetime.now().year)
            parts.append(f"PY={year_from}-{year_to}")

        if filters.get("source_type"):
            # WoS文档类型映射
            type_map = {
                "journal": "J",
                "conference": "S",
                "book": "B",
            }
            if filters["source_type"] in type_map:
                parts.append(f"DT={type_map[filters['source_type']]}")

        return " AND ".join(parts)

    def _generate_mock_results(self, query: str, count: int) -> List[Dict[str, Any]]:
        """生成模拟搜索结果"""
        results = []
        journals = ["Nature", "Science", "Management Science", "IEEE Transactions"]

        for i in range(count):
            results.append(self.normalize_article({
                "id": f"wos_{i}",
                "doi": f"10.xxxx/wos.{i}",
                "title": f"Research on {query} - Paper {i+1}",
                "authors": [
                    {"name": "John Smith", "affiliation": "MIT"},
                    {"name": "Jane Doe", "affiliation": "Stanford University"},
                ],
                "abstract": f"This paper investigates {query} and proposes a novel approach...",
                "keywords": [query, "research", "methodology"],
                "source_type": "journal",
                "source_name": journals[i % len(journals)],
                "publication_year": 2024 - (i % 3),
                "volume": f"Vol.{50 + i % 10}",
                "issue": f"No.{i % 4 + 1}",
                "citation_count": 100 - i * 3,
                "impact_factor": 5.0 + (i % 5),
                "source_url": f"https://webofscience.com/article/{i}",
            }))
        return results
