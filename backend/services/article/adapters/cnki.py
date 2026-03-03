"""
CNKI (中国知网) 适配器
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx

from .base import BaseAdapter, SearchResult


class CNKIAdapter(BaseAdapter):
    """中国知网适配器"""

    BASE_URL = "http://gateway.cnki.net/openx"  # 实际URL需要根据API文档配置

    @property
    def source_name(self) -> str:
        return "cnki"

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResult:
        """
        搜索CNKI文献

        Args:
            query: 搜索关键词
            page: 页码
            page_size: 每页数量
            filters: 过滤条件（year_from, year_to, source_type等）
        """
        filters = filters or {}

        # 构建查询参数
        params = {
            "keyword": query,
            "page": page,
            "pageSize": page_size,
        }

        # 添加过滤条件
        if filters.get("year_from"):
            params["yearFrom"] = filters["year_from"]
        if filters.get("year_to"):
            params["yearTo"] = filters["year_to"]
        if filters.get("source_type"):
            params["sourceType"] = filters["source_type"]

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 注意：这里使用模拟数据，实际需要对接真实API
                # response = await client.get(f"{self.BASE_URL}/search", params=params, headers=headers)

                # 模拟返回数据（开发阶段）
                mock_articles = self._generate_mock_results(query, page_size)

                return SearchResult(
                    articles=mock_articles,
                    total=100,  # 模拟总数
                    source=self.source_name,
                    page=page,
                    page_size=page_size,
                    has_more=page * page_size < 100,
                )

        except Exception as e:
            # 返回空结果而不是抛出异常
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
        # CNKI可能不支持DOI查询，这里返回None
        return None

    async def get_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """通过CNKI ID获取文献详情"""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # response = await client.get(f"{self.BASE_URL}/article/{article_id}", headers=headers)
                # return self.normalize_article(response.json())

                # 模拟返回
                return self.normalize_article({
                    "id": article_id,
                    "doi": None,
                    "title": f"文献详情 - {article_id}",
                    "authors": [{"name": "张三"}, {"name": "李四"}],
                    "abstract": "这是文献摘要...",
                    "keywords": ["关键词1", "关键词2"],
                    "source_type": "journal",
                    "source_name": "管理科学学报",
                    "publication_year": 2024,
                    "citation_count": 10,
                })

        except Exception:
            return None

    async def get_hot_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门文献"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # response = await client.get(f"{self.BASE_URL}/sparkling/article/hots")
                # return [self.normalize_article(a) for a in response.json().get("data", [])]

                # 模拟返回
                return [
                    self.normalize_article({
                        "id": f"hot_{i}",
                        "title": f"热门文献 {i+1}",
                        "authors": [{"name": "作者"}],
                        "source_name": "核心期刊",
                        "publication_year": 2024,
                        "citation_count": 100 - i * 5,
                    })
                    for i in range(limit)
                ]

        except Exception:
            return []

    def _generate_mock_results(self, query: str, count: int) -> List[Dict[str, Any]]:
        """生成模拟搜索结果（开发测试用）"""
        results = []
        for i in range(count):
            results.append(self.normalize_article({
                "id": f"cnki_{query}_{i}",
                "doi": f"10.xxxx/cnki.{i}",
                "title": f"关于{query}的研究与应用 - 论文{i+1}",
                "authors": [
                    {"name": "张三", "affiliation": "浙江大学"},
                    {"name": "李四", "affiliation": "清华大学"},
                ],
                "abstract": f"本文研究了{query}的相关问题，提出了一种新的方法...",
                "keywords": [query, "研究方法", "应用"],
                "source_type": "journal",
                "source_name": "管理科学学报" if i % 2 == 0 else "系统工程理论与实践",
                "publication_year": 2024 - (i % 3),
                "volume": f"第{30 + i % 10}卷",
                "issue": f"第{i % 6 + 1}期",
                "citation_count": 50 - i * 2,
                "source_url": f"https://cnki.net/article/{i}",
            }))
        return results
