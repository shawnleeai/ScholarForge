"""
文献元数据提取器
支持从 DOI、PMID、URL 或文本自动提取文献元数据
"""

import re
import aiohttp
from typing import Dict, Any, Optional, List
from .schemas import MetadataExtractResponse, ReferenceCreate


class MetadataExtractor:
    """文献元数据提取器"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'ScholarForge/1.0 (Academic Research Tool)'
                }
            )
        return self.session

    async def close(self):
        """关闭 HTTP 会话"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def extract_from_doi(self, doi: str) -> MetadataExtractResponse:
        """
        通过 DOI 提取元数据

        使用 CrossRef API 获取文献信息
        """
        # 清理 DOI
        doi = self._clean_doi(doi)

        if not self._validate_doi(doi):
            return MetadataExtractResponse(
                success=False,
                confidence=0,
                message="无效的 DOI 格式"
            )

        try:
            session = await self._get_session()
            url = f"https://api.crossref.org/works/{doi}"

            async with session.get(url) as response:
                if response.status != 200:
                    return MetadataExtractResponse(
                        success=False,
                        confidence=0,
                        message=f"无法获取 DOI 信息 (状态码: {response.status})"
                    )

                data = await response.json()
                work = data.get('message', {})

                reference = self._parse_crossref_work(work)
                return MetadataExtractResponse(
                    success=True,
                    confidence=0.95,
                    reference=reference
                )

        except aiohttp.ClientError as e:
            return MetadataExtractResponse(
                success=False,
                confidence=0,
                message=f"网络请求失败: {str(e)}"
            )
        except Exception as e:
            return MetadataExtractResponse(
                success=False,
                confidence=0,
                message=f"解析失败: {str(e)}"
            )

    async def extract_from_pmid(self, pmid: str) -> MetadataExtractResponse:
        """
        通过 PMID 提取元数据

        使用 PubMed E-utilities API 获取文献信息
        """
        # 清理 PMID
        pmid = pmid.strip()

        if not pmid.isdigit():
            return MetadataExtractResponse(
                success=False,
                confidence=0,
                message="无效的 PMID 格式 (应为数字)"
            )

        try:
            session = await self._get_session()

            # 第一步：获取摘要和详细信息
            summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'json'
            }

            async with session.get(summary_url, params=params) as response:
                if response.status != 200:
                    return MetadataExtractResponse(
                        success=False,
                        confidence=0,
                        message=f"无法获取 PMID 信息 (状态码: {response.status})"
                    )

                data = await response.json()
                result = data.get('result', {}).get(pmid, {})

                if not result:
                    return MetadataExtractResponse(
                        success=False,
                        confidence=0,
                        message="未找到该 PMID 的文献"
                    )

                reference = self._parse_pubmed_result(result, pmid)
                return MetadataExtractResponse(
                    success=True,
                    confidence=0.9,
                    reference=reference
                )

        except aiohttp.ClientError as e:
            return MetadataExtractResponse(
                success=False,
                confidence=0,
                message=f"网络请求失败: {str(e)}"
            )
        except Exception as e:
            return MetadataExtractResponse(
                success=False,
                confidence=0,
                message=f"解析失败: {str(e)}"
            )

    async def extract_from_text(self, text: str) -> MetadataExtractResponse:
        """
        从文本中提取文献元数据

        支持格式：
        - 引文文本（如 APA、MLA 等格式的引用）
        - 标题和作者信息
        - 混合文本
        """
        text = text.strip()

        # 尝试提取 DOI
        doi_match = self._extract_doi_from_text(text)
        if doi_match:
            return await self.extract_from_doi(doi_match)

        # 尝试提取 PMID
        pmid_match = self._extract_pmid_from_text(text)
        if pmid_match:
            return await self.extract_from_pmid(pmid_match)

        # 尝试提取 arXiv ID
        arxiv_match = self._extract_arxiv_from_text(text)
        if arxiv_match:
            return await self._extract_from_arxiv(arxiv_match)

        # 尝试解析引文格式
        parsed = self._parse_citation_text(text)
        if parsed and parsed.get('title'):
            return MetadataExtractResponse(
                success=True,
                confidence=0.7,
                reference=ReferenceCreate(**parsed)
            )

        # 如果只有标题，尝试搜索
        title = self._extract_title_from_text(text)
        if title:
            # 返回标题信息，提示用户可能需要手动补充
            return MetadataExtractResponse(
                success=True,
                confidence=0.5,
                reference=ReferenceCreate(title=title),
                message="仅从文本中提取到标题，建议提供 DOI 或 PMID 获取完整信息"
            )

        return MetadataExtractResponse(
            success=False,
            confidence=0,
            message="无法从文本中提取有效的文献信息"
        )

    async def _extract_from_arxiv(self, arxiv_id: str) -> MetadataExtractResponse:
        """从 arXiv 提取元数据"""
        try:
            session = await self._get_session()
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

            async with session.get(url) as response:
                if response.status != 200:
                    return MetadataExtractResponse(
                        success=False,
                        confidence=0,
                        message="无法获取 arXiv 信息"
                    )

                content = await response.text()
                reference = self._parse_arxiv_xml(content)

                if reference:
                    return MetadataExtractResponse(
                        success=True,
                        confidence=0.9,
                        reference=reference
                    )
                else:
                    return MetadataExtractResponse(
                        success=False,
                        confidence=0,
                        message="解析 arXiv 数据失败"
                    )

        except Exception as e:
            return MetadataExtractResponse(
                success=False,
                confidence=0,
                message=f"arXiv 解析失败: {str(e)}"
            )

    # ============== 解析方法 ==============

    def _parse_crossref_work(self, work: Dict[str, Any]) -> ReferenceCreate:
        """解析 CrossRef 返回的数据"""
        # 作者
        authors = []
        for author in work.get('author', []):
            given = author.get('given', '')
            family = author.get('family', '')
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)

        # 日期
        published = work.get('published-print') or work.get('published-online') or {}
        date_parts = published.get('date-parts', [[]])[0]
        year = date_parts[0] if date_parts else None

        # 页面
        page = work.get('page', '')

        # 构建参考文献
        return ReferenceCreate(
            title=work.get('title', [''])[0] if work.get('title') else '',
            authors=authors,
            publication_year=year,
            journal_name=work.get('container-title', [''])[0] if work.get('container-title') else '',
            volume=work.get('volume', ''),
            issue=work.get('issue', ''),
            pages=page,
            doi=work.get('DOI', ''),
            url=work.get('URL', ''),
            abstract=work.get('abstract', ''),
            publisher=work.get('publisher', ''),
            publication_type='journal',
            keywords=[k.strip() for k in work.get('subject', [])],
            language='en' if work.get('language') == 'en' else 'other'
        )

    def _parse_pubmed_result(self, result: Dict[str, Any], pmid: str) -> ReferenceCreate:
        """解析 PubMed 返回的数据"""
        # 作者
        authors = []
        for author in result.get('authors', []):
            name = author.get('name', '')
            if name:
                authors.append(name)

        # 获取文章类型
        pub_types = result.get('pubtype', [])
        pub_type = 'journal'
        if 'Review' in pub_types:
            pub_type = 'journal'  # 综述也是期刊文章
        elif 'Book' in pub_types:
            pub_type = 'book'

        # 构建 PMID URL
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        return ReferenceCreate(
            title=result.get('title', ''),
            authors=authors,
            publication_year=result.get('pubdate', '')[:4] if result.get('pubdate') else None,
            journal_name=result.get('fulljournalname', result.get('source', '')),
            volume=result.get('volume', ''),
            issue=result.get('issue', ''),
            pages=result.get('pages', ''),
            pmid=pmid,
            url=url,
            publication_type=pub_type,
            language='en'
        )

    def _parse_arxiv_xml(self, xml_content: str) -> Optional[ReferenceCreate]:
        """解析 arXiv XML"""
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(xml_content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            entry = root.find('.//atom:entry', ns)
            if entry is None:
                return None

            title = entry.find('atom:title', ns)
            title_text = title.text.strip() if title is not None else ''

            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns)
                if name is not None:
                    authors.append(name.text)

            published = entry.find('atom:published', ns)
            year = None
            if published is not None:
                year_match = re.search(r'(\d{4})', published.text)
                if year_match:
                    year = int(year_match.group(1))

            summary = entry.find('atom:summary', ns)
            abstract = summary.text if summary is not None else ''

            id_elem = entry.find('atom:id', ns)
            arxiv_url = id_elem.text if id_elem is not None else ''

            # 提取 arXiv ID
            arxiv_id = ''
            match = re.search(r'arXiv:(\d+\.\d+)', arxiv_url)
            if match:
                arxiv_id = match.group(1)

            return ReferenceCreate(
                title=title_text,
                authors=authors,
                publication_year=year,
                abstract=abstract,
                url=arxiv_url,
                publication_type='journal',  # arXiv 通常视为预印本/期刊
                keywords=[],
                language='en'
            )

        except ET.ParseError:
            return None

    def _parse_citation_text(self, text: str) -> Optional[Dict[str, Any]]:
        """解析引文文本提取元数据"""
        result = {}

        # 尝试匹配 APA 格式: Author, A. A. (Year). Title. Journal, Volume(Issue), Pages.
        apa_pattern = r'^([\w\s,\.\-]+)\s*\((\d{4})\)\.\s*([^\.]+)\.\s*([^,]+),\s*(\d+)\s*\((\d+)\),?\s*(.*?)\.$'
        match = re.match(apa_pattern, text)
        if match:
            result['authors'] = [a.strip() for a in match.group(1).split(',')]
            result['publication_year'] = int(match.group(2))
            result['title'] = match.group(3).strip()
            result['journal_name'] = match.group(4).strip()
            result['volume'] = match.group(5)
            result['issue'] = match.group(6)
            result['pages'] = match.group(7).strip()
            result['publication_type'] = 'journal'
            return result

        # 尝试匹配 GB/T 7714 格式
        gb_pattern = r'^([^\.]+)\.\s*([^\[]+)\[J\]\.\s*([^,]+),\s*(\d{4})[^:]*:\s*(\d+[-–]\d+)\.'
        match = re.match(gb_pattern, text)
        if match:
            result['authors'] = [a.strip() for a in match.group(1).split(',')]
            result['title'] = match.group(2).strip()
            result['journal_name'] = match.group(3).strip()
            result['publication_year'] = int(match.group(4))
            result['pages'] = match.group(5)
            result['publication_type'] = 'journal'
            return result

        # 尝试匹配简单的 "Author. Title. Journal Year" 格式
        simple_pattern = r'^([^\.]+)\.\s*([^\.]+)\.\s*([^\.]+)\.?\s*(\d{4})'
        match = re.match(simple_pattern, text)
        if match:
            result['authors'] = [match.group(1).strip()]
            result['title'] = match.group(2).strip()
            result['journal_name'] = match.group(3).strip()
            result['publication_year'] = int(match.group(4))
            result['publication_type'] = 'journal'
            return result

        return None

    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """从文本中提取可能的标题"""
        # 标题通常是最长的句子或引号内的内容
        text = text.strip()

        # 尝试匹配引号内的内容
        quote_match = re.search(r'"([^"]{10,200})"', text)
        if quote_match:
            return quote_match.group(1)

        # 尝试匹配书名号内的内容
        book_match = re.search(r'《([^》]{5,100})》', text)
        if book_match:
            return book_match.group(1)

        # 如果文本较短，可能是标题
        if 10 < len(text) < 300 and '\n' not in text:
            # 移除可能的作者前缀
            no_author = re.sub(r'^[^\d]{1,50},\s*', '', text)
            if len(no_author) > 10:
                return no_author

        return None

    # ============== 辅助方法 ==============

    def _clean_doi(self, doi: str) -> str:
        """清理 DOI"""
        doi = doi.strip()
        # 移除可能的 URL 前缀
        doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi)
        doi = re.sub(r'^doi:\s*', '', doi, flags=re.IGNORECASE)
        return doi

    def _validate_doi(self, doi: str) -> bool:
        """验证 DOI 格式"""
        # DOI 格式: 10.{registrant}/{suffix}
        pattern = r'^10\.\d{4,}\/.+$'
        return bool(re.match(pattern, doi))

    def _extract_doi_from_text(self, text: str) -> Optional[str]:
        """从文本中提取 DOI"""
        # 匹配 DOI 模式
        patterns = [
            r'doi[\s:]*([\d\.\/]+)',
            r'DOI[\s:]*([\d\.\/]+)',
            r'10\.\d{4,}\/[\w\-\.\/]+',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                doi = match.group(1) if 'doi' in pattern.lower() else match.group(0)
                return self._clean_doi(doi)
        return None

    def _extract_pmid_from_text(self, text: str) -> Optional[str]:
        """从文本中提取 PMID"""
        patterns = [
            r'pmid[\s:]*(\d+)',
            r'PMID[\s:]*(\d+)',
            r'PubMed[\s:]*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def _extract_arxiv_from_text(self, text: str) -> Optional[str]:
        """从文本中提取 arXiv ID"""
        patterns = [
            r'arXiv[\s:]*(\d+\.\d+)',
            r'arXiv[\s:]*(\d+)',
            r'arxiv[\s:]*(\d+\.\d+)',
            r'arxiv[\s/]*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
