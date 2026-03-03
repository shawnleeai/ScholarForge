"""
arXiv 适配器
"""

import asyncio
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from .base import BaseAdapter, SearchResult


class ArxivAdapter(BaseAdapter):
    """arXiv 预印本适配器"""

    BASE_URL = "http://export.arxiv.org/api/query"

    @property
    def source_name(self) -> str:
        return "arxiv"

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResult:
        """
        搜索arXiv预印本

        arXiv API是免费的，不需要API密钥
        """
        filters = filters or {}

        # 构建查询
        search_query = f"all:{query}"
        start = (page - 1) * page_size

        params = {
            "search_query": search_query,
            "start": start,
            "max_results": page_size,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # response = await client.get(self.BASE_URL, params=params)
                # articles, total = self._parse_arxiv_response(response.text)

                # 模拟返回数据
                mock_articles = self._generate_mock_results(query, page_size)

                return SearchResult(
                    articles=mock_articles,
                    total=50,
                    source=self.source_name,
                    page=page,
                    page_size=page_size,
                    has_more=page * page_size < 50,
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
        """arXiv通常没有DOI，返回None"""
        return None

    async def get_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """通过arXiv ID获取文献"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # params = {"id_list": article_id}
                # response = await client.get(self.BASE_URL, params=params)

                return self.normalize_article({
                    "id": article_id,
                    "doi": None,
                    "title": f"arXiv:{article_id}",
                    "authors": [{"name": "arXiv Author"}],
                    "source_type": "preprint",
                    "source_name": "arXiv",
                    "publication_year": 2024,
                    "pdf_url": f"https://arxiv.org/pdf/{article_id}",
                    "source_url": f"https://arxiv.org/abs/{article_id}",
                })

        except Exception:
            return None

    def _parse_arxiv_response(self, xml_text: str) -> tuple[List[Dict], int]:
        """解析arXiv API返回的XML"""
        articles = []
        root = ET.fromstring(xml_text)

        # 获取总数
        total = int(root.find(".//{http://a9.com/-/spec/opensearch/1.1/}totalResults").text or 0)

        # 解析条目
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            article = {
                "id": entry.find("atom:id", ns).text.split("/")[-1],
                "title": entry.find("atom:title", ns).text.strip(),
                "abstract": entry.find("atom:summary", ns).text.strip(),
                "authors": [
                    {"name": a.find("atom:name", ns).text}
                    for a in entry.findall("atom:author", ns)
                ],
                "source_type": "preprint",
                "source_name": "arXiv",
                "publication_year": entry.find("atom:published", ns).text[:4],
            }

            # 获取PDF链接
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    article["pdf_url"] = link.get("href")

            articles.append(self.normalize_article(article))

        return articles, total

    def _generate_mock_results(self, query: str, count: int) -> List[Dict[str, Any]]:
        """生成模拟搜索结果"""
        results = []
        categories = ["cs.AI", "cs.LG", "stat.ML", "physics.data-an"]

        for i in range(count):
            arxiv_id = f"2403.{10000 + i}"
            results.append(self.normalize_article({
                "id": arxiv_id,
                "doi": None,
                "title": f"[{categories[i % len(categories)]}] Advances in {query} - Preprint {i+1}",
                "authors": [
                    {"name": "Alice Johnson"},
                    {"name": "Bob Chen"},
                ],
                "abstract": f"This preprint discusses recent advances in {query}...",
                "keywords": [query, "machine learning", "preprint"],
                "source_type": "preprint",
                "source_name": "arXiv",
                "publication_year": 2024,
                "source_url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
            }))
        return results
