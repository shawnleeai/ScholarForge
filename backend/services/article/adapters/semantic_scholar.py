"""
Semantic Scholar 适配器
免费学术API，提供论文搜索、引用图谱等功能
文档: https://api.semanticscholar.org/api-docs/
"""

from typing import Any, Dict, List, Optional
from urllib.parse import quote
import time

import httpx

from .base import BaseAdapter, SearchResult


class SemanticScholarAdapter(BaseAdapter):
    """Semantic Scholar 适配器"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    # 默认查询字段
    DEFAULT_FIELDS = [
        "paperId",
        "title",
        "abstract",
        "authors",
        "year",
        "citationCount",
        "referenceCount",
        "influentialCitationCount",
        "fieldsOfStudy",
        "publicationTypes",
        "publicationDate",
        "journal",
        "venue",
        "externalIds",
        "url",
        "openAccessPdf",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.last_request_time = 0
        self.min_interval = 1.0  # 1秒间隔（免费版限制）

    @property
    def source_name(self) -> str:
        return "semantic_scholar"

    async def _rate_limit(self):
        """速率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> SearchResult:
        """
        搜索论文

        Semantic Scholar API 是免费的，不需要API Key
        """
        filters = filters or {}

        # 构建查询参数
        offset = (page - 1) * page_size
        fields = ",".join(self.DEFAULT_FIELDS)

        params = {
            "query": query,
            "fields": fields,
            "offset": offset,
            "limit": min(page_size, 100),  # 最大100
        }

        # 添加过滤器
        if filters.get("year_start"):
            params["publicationDateOrYear"] = f"{filters['year_start']}-"
        if filters.get("year_end"):
            current = params.get("publicationDateOrYear", "")
            params["publicationDateOrYear"] = f"{current}{filters['year_end']}"
        if filters.get("fields_of_study"):
            params["fieldsOfStudy"] = filters["fields_of_study"]

        try:
            await self._rate_limit()

            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/paper/search",
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                articles = [
                    self._parse_paper(paper) for paper in data.get("data", [])
                ]
                total = data.get("total", 0)

                return SearchResult(
                    articles=articles,
                    total=total,
                    source=self.source_name,
                    page=page,
                    page_size=page_size,
                    has_more=offset + len(articles) < total,
                )

        except Exception as e:
            print(f"Semantic Scholar搜索失败: {e}")
            return SearchResult(
                articles=[],
                total=0,
                source=self.source_name,
                page=page,
                page_size=page_size,
                has_more=False,
                error=str(e),
            )

    async def get_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """通过ID获取论文详情"""
        fields = ",".join(self.DEFAULT_FIELDS + ["references", "citations"])

        try:
            await self._rate_limit()

            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/paper/{paper_id}",
                    params={"fields": fields},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                return self._parse_paper(data, include_refs=True)

        except Exception as e:
            print(f"获取论文详情失败: {e}")
            return None

    async def get_citations(self, paper_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取引用该论文的文献"""
        try:
            await self._rate_limit()

            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/paper/{paper_id}/citations",
                    params={
                        "fields": ",".join(self.DEFAULT_FIELDS),
                        "limit": limit,
                    },
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                return [
                    self._parse_citation(citing)
                    for citing in data.get("data", [])
                ]

        except Exception as e:
            print(f"获取引用失败: {e}")
            return []

    async def get_references(self, paper_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取该论文的参考文献"""
        try:
            await self._rate_limit()

            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/paper/{paper_id}/references",
                    params={
                        "fields": ",".join(self.DEFAULT_FIELDS),
                        "limit": limit,
                    },
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                return [
                    self._parse_citation(cited)
                    for cited in data.get("data", [])
                ]

        except Exception as e:
            print(f"获取参考文献失败: {e}")
            return []

    async def get_author_papers(self, author_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取作者的所有论文"""
        try:
            await self._rate_limit()

            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/author/{author_id}/papers",
                    params={
                        "fields": ",".join(self.DEFAULT_FIELDS),
                        "limit": limit,
                    },
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                return [
                    self._parse_paper(paper)
                    for paper in data.get("data", [])
                ]

        except Exception as e:
            print(f"获取作者论文失败: {e}")
            return []

    async def batch_get_papers(self, paper_ids: List[str]) -> List[Dict[str, Any]]:
        """批量获取论文（更高效的API）"""
        if not paper_ids:
            return []

        fields = ",".join(self.DEFAULT_FIELDS)

        try:
            await self._rate_limit()

            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/paper/batch",
                    headers=headers,
                    json={
                        "ids": paper_ids,
                        "fields": fields,
                    },
                )
                response.raise_for_status()
                data = response.json()

                return [
                    self._parse_paper(paper)
                    for paper in data if paper
                ]

        except Exception as e:
            print(f"批量获取论文失败: {e}")
            return []

    def _parse_paper(self, paper: Dict[str, Any], include_refs: bool = False) -> Dict[str, Any]:
        """解析论文数据"""
        # 处理作者
        authors = []
        for author in paper.get("authors", []):
            if isinstance(author, dict):
                authors.append({
                    "name": author.get("name", ""),
                    "author_id": author.get("authorId"),
                })

        # 处理外部ID
        external_ids = paper.get("externalIds", {})
        doi = external_ids.get("DOI")
        arxiv_id = external_ids.get("ArXiv")

        # 构建URL
        source_url = paper.get("url", f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}")
        pdf_url = None
        if paper.get("openAccessPdf"):
            pdf_url = paper["openAccessPdf"].get("url")

        result = {
            "id": paper.get("paperId", ""),
            "title": paper.get("title", ""),
            "abstract": paper.get("abstract", ""),
            "authors": authors,
            "publication_year": paper.get("year"),
            "publication_date": paper.get("publicationDate"),
            "journal": paper.get("journal", {}).get("name") if paper.get("journal") else paper.get("venue"),
            "source_type": "journal" if paper.get("publicationTypes") and "JournalArticle" in paper.get("publicationTypes", []) else "conference",
            "source_name": "Semantic Scholar",
            "doi": doi,
            "arxiv_id": arxiv_id,
            "citation_count": paper.get("citationCount", 0),
            "reference_count": paper.get("referenceCount", 0),
            "influential_citation_count": paper.get("influentialCitationCount", 0),
            "fields_of_study": paper.get("fieldsOfStudy", []),
            "source_url": source_url,
            "pdf_url": pdf_url,
        }

        # 如果包含引用信息
        if include_refs:
            result["references"] = [
                self._parse_citation(ref)
                for ref in paper.get("references", [])
            ]
            result["citations"] = [
                self._parse_citation(cit)
                for cit in paper.get("citations", [])
            ]

        return self.normalize_article(result)

    def _parse_citation(self, citation_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析引用数据"""
        paper = citation_data.get("citedPaper") or citation_data.get("citingPaper")
        if not paper:
            return {}

        return self._parse_paper(paper)

    async def get_recommended_papers(self, paper_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取推荐的相关论文"""
        try:
            await self._rate_limit()

            headers = {}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/paper/{paper_id}/related-papers",
                    params={
                        "fields": ",".join(self.DEFAULT_FIELDS),
                        "limit": limit,
                    },
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                return [
                    self._parse_paper(paper)
                    for paper in data.get("data", [])
                ]

        except Exception as e:
            print(f"获取推荐论文失败: {e}")
            return []


import asyncio
