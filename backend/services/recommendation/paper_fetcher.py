"""
论文采集服务
集成多个学术数据源：arXiv、Semantic Scholar、PubMed
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any, AsyncGenerator
from dataclasses import dataclass

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from .paper_feed_models import (
    PaperCreate, PaperSource, Paper, FetchResult
)

logger = logging.getLogger(__name__)


@dataclass
class FetchConfig:
    """采集配置"""
    source: PaperSource
    categories: List[str]
    keywords: List[str]
    max_results: int = 100
    days_back: int = 7


class ArXivFetcher:
    """arXiv论文采集器"""

    BASE_URL = "http://export.arxiv.org/api/query"
    RATE_LIMIT_DELAY = 3  # 秒，arXiv限制3秒/请求

    # 类别映射
    CATEGORY_MAP = {
        "cs.AI": "Artificial Intelligence",
        "cs.CL": "Computation and Language (NLP)",
        "cs.CV": "Computer Vision",
        "cs.LG": "Machine Learning",
        "cs.IR": "Information Retrieval",
        "cs.DB": "Databases",
        "cs.SE": "Software Engineering",
        "stat.ML": "Statistics - Machine Learning",
        "physics.data-an": "Data Analysis",
        "q-bio": "Quantitative Biology",
    }

    def __init__(self, rate_limit: int = 3):
        self.rate_limit_delay = rate_limit
        self.last_request_time: Optional[datetime] = None

    async def _rate_limit(self):
        """请求频率限制"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = datetime.now()

    async def fetch(
        self,
        categories: List[str],
        keywords: List[str],
        max_results: int = 100,
        days_back: int = 7
    ) -> List[PaperCreate]:
        """获取arXiv论文"""
        await self._rate_limit()

        # 构建查询
        cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
        keyword_query = " OR ".join([f"all:{kw}" for kw in keywords]) if keywords else ""

        if cat_query and keyword_query:
            query = f"({cat_query}) AND ({keyword_query})"
        else:
            query = cat_query or keyword_query

        # 计算日期范围
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")
        date_range = f"submittedDate:[{start_date}0000 TO {end_date}2359]"

        if query:
            query = f"({query}) AND {date_range}"
        else:
            query = date_range

        params = {
            "search_query": query,
            "start": 0,
            "max_results": min(max_results, 2000),  # arXiv最大2000
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        logger.error(f"arXiv API error: {resp.status}")
                        return []

                    content = await resp.text()
                    return self._parse_feed(content)

        except Exception as e:
            logger.error(f"Error fetching from arXiv: {e}")
            return []

    def _parse_feed(self, content: str) -> List[PaperCreate]:
        """解析arXiv RSS feed"""
        feed = feedparser.parse(content)
        papers = []

        for entry in feed.entries:
            try:
                # 解析作者
                authors = []
                for author in entry.get("authors", []):
                    authors.append({
                        "name": author.get("name", ""),
                        "affiliation": ""
                    })

                # 解析类别
                categories = [tag.get("term", "") for tag in entry.get("tags", [])]
                primary_category = categories[0] if categories else ""

                # 解析日期
                published = entry.get("published", "")
                published_date = None
                if published:
                    try:
                        published_date = datetime.fromisoformat(
                            published.replace("Z", "+00:00")
                        ).date()
                    except:
                        pass

                # 获取PDF链接
                pdf_url = ""
                for link in entry.get("links", []):
                    if link.get("type") == "application/pdf":
                        pdf_url = link.get("href", "")
                        break
                    if "arxiv.org/abs/" in link.get("href", ""):
                        arxiv_id = link.get("href", "").split("/abs/")[-1]
                        pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"

                paper = PaperCreate(
                    title=entry.get("title", "").replace("\n", " ").strip(),
                    abstract=entry.get("summary", "").replace("\n", " ").strip(),
                    authors=authors,
                    url=entry.get("link", ""),
                    pdf_url=pdf_url,
                    arxiv_id=entry.get("id", "").split("/abs/")[-1],
                    source=PaperSource.ARXIV,
                    source_id=entry.get("id", ""),
                    published_at=published_date,
                    categories=categories,
                    primary_category=primary_category,
                    keywords=categories,
                    raw_data=dict(entry)
                )
                papers.append(paper)

            except Exception as e:
                logger.warning(f"Error parsing arXiv entry: {e}")
                continue

        return papers


class SemanticScholarFetcher:
    """Semantic Scholar论文采集器"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    DEFAULT_FIELDS = "title,abstract,authors,year,citationCount,referenceCount,fieldsOfStudy,publicationDate,openAccessPdf"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["x-api-key"] = api_key

    async def fetch(
        self,
        fields: List[str],
        keywords: List[str],
        max_results: int = 100,
        days_back: int = 7
    ) -> List[PaperCreate]:
        """获取Semantic Scholar论文"""
        papers = []

        # 按关键词搜索
        for keyword in keywords[:3]:  # 限制关键词数量避免过多请求
            try:
                keyword_papers = await self._search_papers(
                    keyword, max_results // len(keywords)
                )
                papers.extend(keyword_papers)
                await asyncio.sleep(1)  # 限速
            except Exception as e:
                logger.error(f"Error searching Semantic Scholar for '{keyword}': {e}")

        # 去重
        seen_ids = set()
        unique_papers = []
        for paper in papers:
            if paper.source_id not in seen_ids:
                seen_ids.add(paper.source_id)
                unique_papers.append(paper)

        return unique_papers[:max_results]

    async def _search_papers(self, query: str, limit: int) -> List[PaperCreate]:
        """搜索论文"""
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "fields": self.DEFAULT_FIELDS,
            "limit": limit,
            "offset": 0,
        }

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params, timeout=30) as resp:
                if resp.status != 200:
                    logger.error(f"Semantic Scholar API error: {resp.status}")
                    return []

                data = await resp.json()
                return self._parse_papers(data.get("data", []))

    def _parse_papers(self, papers_data: List[Dict]) -> List[PaperCreate]:
        """解析论文数据"""
        papers = []

        for paper_data in papers_data:
            try:
                authors = []
                for author in paper_data.get("authors", [])[:20]:  # 限制作者数量
                    authors.append({
                        "name": author.get("name", ""),
                        "affiliation": ""
                    })

                # 解析日期
                pub_date = paper_data.get("publicationDate")
                published_at = None
                if pub_date:
                    try:
                        published_at = datetime.strptime(pub_date, "%Y-%m-%d").date()
                    except:
                        pass

                # 获取PDF链接
                open_access = paper_data.get("openAccessPdf", {}) or {}
                pdf_url = open_access.get("url", "")

                paper = PaperCreate(
                    title=paper_data.get("title", ""),
                    abstract=paper_data.get("abstract", "") or "",
                    authors=authors,
                    url=f"https://www.semanticscholar.org/paper/{paper_data.get('paperId', '')}",
                    pdf_url=pdf_url,
                    doi=paper_data.get("externalIds", {}).get("DOI"),
                    source=PaperSource.SEMANTIC_SCHOLAR,
                    source_id=paper_data.get("paperId", ""),
                    published_at=published_at,
                    year=paper_data.get("year"),
                    categories=paper_data.get("fieldsOfStudy", []) or [],
                    citation_count=paper_data.get("citationCount", 0) or 0,
                    raw_data=paper_data
                )
                papers.append(paper)

            except Exception as e:
                logger.warning(f"Error parsing Semantic Scholar paper: {e}")
                continue

        return papers

    async def fetch_by_ids(self, paper_ids: List[str]) -> List[PaperCreate]:
        """通过ID批量获取论文详情"""
        if not paper_ids:
            return []

        papers = []
        # 批量请求，每批100个
        for i in range(0, len(paper_ids), 100):
            batch = paper_ids[i:i+100]
            try:
                batch_papers = await self._fetch_batch(batch)
                papers.extend(batch_papers)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error fetching batch from Semantic Scholar: {e}")

        return papers

    async def _fetch_batch(self, paper_ids: List[str]) -> List[PaperCreate]:
        """批量获取论文"""
        url = f"{self.BASE_URL}/paper/batch"
        params = {"fields": self.DEFAULT_FIELDS}
        payload = {"ids": paper_ids}

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(url, params=params, json=payload, timeout=30) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return self._parse_papers(data)


class PubMedFetcher:
    """PubMed论文采集器"""

    EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.rate_limit = 0.34 if api_key else 1.0  # 有API key: 3/秒，无: 1/秒

    async def fetch(
        self,
        categories: List[str],
        keywords: List[str],
        max_results: int = 100,
        days_back: int = 7
    ) -> List[PaperCreate]:
        """获取PubMed论文"""
        # 构建查询
        query_parts = []
        if keywords:
            query_parts.extend(keywords)
        if categories:
            # 将类别映射到MeSH terms
            query_parts.extend(categories)

        if not query_parts:
            return []

        query = " OR ".join([f"({q})" for q in query_parts])

        # 添加日期限制
        date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
        date_to = datetime.now().strftime("%Y/%m/%d")
        query = f"({query}) AND ({date_from}:{date_to}[Date - Publication])"

        try:
            # 搜索PMID
            pmids = await self._search(query, max_results)
            if not pmids:
                return []

            await asyncio.sleep(self.rate_limit)

            # 获取详情
            papers = await self._fetch_details(pmids)
            return papers

        except Exception as e:
            logger.error(f"Error fetching from PubMed: {e}")
            return []

    async def _search(self, query: str, max_results: int) -> List[str]:
        """搜索PMID"""
        url = f"{self.EUTILS_BASE}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "date",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as resp:
                data = await resp.json()
                return data.get("esearchresult", {}).get("idlist", [])

    async def _fetch_details(self, pmids: List[str]) -> List[PaperCreate]:
        """获取论文详情"""
        url = f"{self.EUTILS_BASE}/esummary.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=30) as resp:
                data = await resp.json()
                return self._parse_summaries(data)

    def _parse_summaries(self, data: Dict) -> List[PaperCreate]:
        """解析摘要数据"""
        papers = []
        result = data.get("result", {})

        for pmid in result.get("uids", []):
            try:
                paper_data = result.get(pmid, {})

                authors = []
                for author in paper_data.get("authors", []):
                    authors.append({
                        "name": author.get("name", ""),
                        "affiliation": ""
                    })

                # 解析日期
                pub_date = paper_data.get("pubdate", "")
                published_at = None
                if pub_date:
                    try:
                        year = pub_date.split()[0]
                        published_at = date(int(year), 1, 1)
                    except:
                        pass

                paper = PaperCreate(
                    title=paper_data.get("title", ""),
                    abstract=paper_data.get("abstract", ""),
                    authors=authors,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    pmid=pmid,
                    source=PaperSource.PUBMED,
                    source_id=pmid,
                    published_at=published_at,
                    year=published_at.year if published_at else None,
                    journal=paper_data.get("fulljournalname", ""),
                    raw_data=paper_data
                )
                papers.append(paper)

            except Exception as e:
                logger.warning(f"Error parsing PubMed paper {pmid}: {e}")
                continue

        return papers


class PaperFetcher:
    """论文采集主控制器"""

    def __init__(
        self,
        semantic_scholar_key: Optional[str] = None,
        pubmed_key: Optional[str] = None
    ):
        self.arxiv = ArXivFetcher()
        self.semantic_scholar = SemanticScholarFetcher(semantic_scholar_key)
        self.pubmed = PubMedFetcher(pubmed_key)

    async def fetch_all(
        self,
        config: FetchConfig
    ) -> FetchResult:
        """从所有源采集论文"""
        start_time = datetime.now()

        sources = []
        if config.source == PaperSource.ARXIV or not config.source:
            sources.append(("arXiv", self.arxiv))
        if config.source == PaperSource.SEMANTIC_SCHOLAR or not config.source:
            sources.append(("Semantic Scholar", self.semantic_scholar))
        if config.source == PaperSource.PUBMED or not config.source:
            sources.append(("PubMed", self.pubmed))

        all_papers = []
        for name, fetcher in sources:
            try:
                logger.info(f"Fetching from {name}...")
                papers = await fetcher.fetch(
                    config.categories,
                    config.keywords,
                    config.max_results,
                    config.days_back
                )
                logger.info(f"Fetched {len(papers)} papers from {name}")
                all_papers.extend(papers)
                await asyncio.sleep(1)  # 源间延迟
            except Exception as e:
                logger.error(f"Error fetching from {name}: {e}")

        # 去重
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            key = f"{paper.source}:{paper.source_id}"
            if key not in seen_ids:
                seen_ids.add(key)
                unique_papers.append(paper)

        duration = (datetime.now() - start_time).total_seconds()

        return FetchResult(
            source=config.source or PaperSource.ARXIV,
            fetched_count=len(all_papers),
            new_count=len(unique_papers),
            updated_count=0,
            failed_count=len(all_papers) - len(unique_papers),
            duration_seconds=duration,
            timestamp=datetime.now()
        ), unique_papers

    async def fetch_by_source(
        self,
        source: PaperSource,
        categories: List[str],
        keywords: List[str],
        max_results: int = 100,
        days_back: int = 7
    ) -> List[PaperCreate]:
        """从特定源采集"""
        config = FetchConfig(
            source=source,
            categories=categories,
            keywords=keywords,
            max_results=max_results,
            days_back=days_back
        )
        _, papers = await self.fetch_all(config)
        return papers
