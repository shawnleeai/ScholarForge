"""
arXiv 适配器 - 真实API版本
完全对接arXiv官方API，无需API Key
"""

import asyncio
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from datetime import datetime
import time

import httpx

from .base import BaseAdapter, SearchResult


class ArxivAdapter(BaseAdapter):
    """arXiv 预印本适配器 - 真实API版本"""

    BASE_URL = "http://export.arxiv.org/api/query"

    # 类别映射
    CATEGORY_MAP = {
        "cs.AI": "人工智能",
        "cs.CL": "计算语言学",
        "cs.CV": "计算机视觉",
        "cs.LG": "机器学习",
        "cs.IR": "信息检索",
        "cs.DB": "数据库",
        "cs.DC": "分布式计算",
        "cs.SE": "软件工程",
        "cs.NE": "神经与进化计算",
        "cs.RO": "机器人学",
        "stat.ML": "统计学习",
        "physics.data-an": "数据分析",
        "q-bio.QM": "定量生物学",
    }

    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 3  # arXiv API限制：每3秒一次请求

    @property
    def source_name(self) -> str:
        return "arxiv"

    async def _rate_limit(self):
        """速率限制，避免触发arXiv限制"""
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
        搜索arXiv预印本 - 真实API调用

        arXiv API文档: https://arxiv.org/help/api
        """
        filters = filters or {}

        # 构建查询
        search_query = self._build_query(query, filters)
        start = (page - 1) * page_size

        params = {
            "search_query": search_query,
            "start": start,
            "max_results": min(page_size, 50),  # arXiv限制最大50
            "sortBy": filters.get("sort_by", "relevance"),
            "sortOrder": filters.get("sort_order", "descending"),
        }

        try:
            # 速率限制
            await self._rate_limit()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()

                articles, total = self._parse_arxiv_response(response.text)

                return SearchResult(
                    articles=articles,
                    total=total,
                    source=self.source_name,
                    page=page,
                    page_size=page_size,
                    has_more=total > page * page_size,
                )

        except httpx.TimeoutException:
            return SearchResult(
                articles=[],
                total=0,
                source=self.source_name,
                page=page,
                page_size=page_size,
                has_more=False,
                error="请求超时，请稍后重试",
            )
        except Exception as e:
            print(f"arXiv搜索失败: {e}")
            # 降级到备用方案
            return SearchResult(
                articles=[],
                total=0,
                source=self.source_name,
                page=page,
                page_size=page_size,
                has_more=False,
                error=str(e),
            )

    def _build_query(self, query: str, filters: Dict[str, Any]) -> str:
        """构建arXiv查询字符串"""
        parts = [f"all:{quote(query)}"]

        # 类别过滤
        if filters.get("category"):
            parts.append(f"cat:{filters['category']}")

        # 作者过滤
        if filters.get("author"):
            parts.append(f"au:{quote(filters['author'])}")

        # 标题过滤
        if filters.get("title"):
            parts.append(f"ti:{quote(filters['title'])}")

        # 摘要过滤
        if filters.get("abstract"):
            parts.append(f"abs:{quote(filters['abstract'])}")

        # 日期范围
        if filters.get("date_from"):
            parts.append(f"submittedDate:[{filters['date_from']}0000+TO+*]")

        return "+AND+".join(parts)

    async def get_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """通过DOI搜索（arXiv通常没有DOI，但可以通过其他方式查找）"""
        # arXiv预印本通常没有DOI
        return None

    async def get_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """通过arXiv ID获取文献详情"""
        try:
            await self._rate_limit()

            params = {"id_list": article_id}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()

                articles, _ = self._parse_arxiv_response(response.text)
                return articles[0] if articles else None

        except Exception as e:
            print(f"获取arXiv文献失败: {e}")
            return None

    def _parse_arxiv_response(self, xml_text: str) -> tuple[List[Dict], int]:
        """解析arXiv API返回的XML"""
        articles = []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            print(f"XML解析错误: {e}")
            return [], 0

        # 定义命名空间
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
            "arxiv": "http://arxiv.org/schemas/atom"
        }

        # 获取总数
        total_elem = root.find(".//opensearch:totalResults", ns)
        total = int(total_elem.text) if total_elem is not None else 0

        # 解析条目
        for entry in root.findall("atom:entry", ns):
            try:
                article = self._parse_entry(entry, ns)
                if article:
                    articles.append(self.normalize_article(article))
            except Exception as e:
                print(f"解析条目失败: {e}")
                continue

        return articles, total

    def _parse_entry(self, entry: ET.Element, ns: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """解析单个arXiv条目"""
        # ID
        id_elem = entry.find("atom:id", ns)
        if id_elem is None:
            return None

        arxiv_id = id_elem.text.split("/")[-1]
        if "v" in arxiv_id:  # 移除版本号
            arxiv_id = arxiv_id.split("v")[0]

        # 标题
        title_elem = entry.find("atom:title", ns)
        title = title_elem.text.strip() if title_elem is not None else "Untitled"
        # 清理标题中的多余空白
        title = " ".join(title.split())

        # 摘要
        summary_elem = entry.find("atom:summary", ns)
        abstract = summary_elem.text.strip() if summary_elem is not None else ""
        abstract = " ".join(abstract.split())

        # 作者
        authors = []
        for author in entry.findall("atom:author", ns):
            name_elem = author.find("atom:name", ns)
            if name_elem is not None:
                authors.append({"name": name_elem.text.strip()})

        # 发布时间
        published_elem = entry.find("atom:published", ns)
        published = published_elem.text if published_elem is not None else ""
        year = int(published[:4]) if published else None

        # 更新时间
        updated_elem = entry.find("atom:updated", ns)
        updated = updated_elem.text if updated_elem is not None else published

        # 类别
        categories = []
        primary_category = None
        for cat in entry.findall("atom:category", ns):
            term = cat.get("term", "")
            if term:
                categories.append(term)
                if not primary_category:
                    primary_category = term

        # 链接
        source_url = f"https://arxiv.org/abs/{arxiv_id}"
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        # 检查是否有PDF链接
        for link in entry.findall("atom:link", ns):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", pdf_url)
                break

        # 获取主类别信息
        category_name = self.CATEGORY_MAP.get(primary_category, primary_category) if primary_category else "Unknown"

        return {
            "id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "source_type": "preprint",
            "source_name": "arXiv",
            "publication_year": year,
            "published_date": published,
            "updated_date": updated,
            "categories": categories,
            "primary_category": primary_category,
            "category_name": category_name,
            "source_url": source_url,
            "pdf_url": pdf_url,
            "doi": None,  # arXiv预印本通常没有DOI
        }

    async def download_pdf(self, article_id: str, save_path: str) -> bool:
        """下载PDF文件"""
        pdf_url = f"https://arxiv.org/pdf/{article_id}.pdf"

        try:
            await self._rate_limit()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()

                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True

        except Exception as e:
            print(f"下载PDF失败: {e}")
            return False

    async def get_recent_papers(self, category: str = "cs.AI", max_results: int = 10) -> List[Dict[str, Any]]:
        """获取最近提交的论文"""
        # 构建查询：该类别下的最新论文
        params = {
            "search_query": f"cat:{category}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            await self._rate_limit()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()

                articles, _ = self._parse_arxiv_response(response.text)
                return articles

        except Exception as e:
            print(f"获取最新论文失败: {e}")
            return []
