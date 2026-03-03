"""
文献导入适配器
支持多种外部文献管理系统的数据导入
"""

import io
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import aiohttp


@dataclass
class ImportResult:
    """导入结果"""
    success: bool
    references: List[Dict[str, Any]]
    errors: List[Dict[str, str]]
    total_count: int
    success_count: int
    failed_count: int
    duplicates: List[Dict[str, Any]]  # 重复项


class BaseImportAdapter:
    """导入适配器基类"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.errors: List[Dict[str, str]] = []
        self.duplicates: List[Dict[str, Any]] = []

    async def import_from_file(self, file_content: bytes) -> ImportResult:
        """从文件导入"""
        raise NotImplementedError

    async def import_from_api(self, credentials: Dict[str, str]) -> ImportResult:
        """从 API 导入"""
        raise NotImplementedError

    def _normalize_reference(self, ref: Dict[str, Any]) -> Dict[str, Any]:
        """规范化参考文献数据"""
        normalized = {
            'user_id': self.user_id,
            'title': ref.get('title', '').strip(),
            'authors': self._normalize_authors(ref.get('authors', [])),
            'publication_year': self._normalize_year(ref.get('publication_year')),
            'journal_name': ref.get('journal_name', '').strip() or None,
            'volume': str(ref.get('volume', '')) or None,
            'issue': str(ref.get('issue', '')) or None,
            'pages': ref.get('pages', '').strip() or None,
            'doi': ref.get('doi', '').strip() or None,
            'pmid': ref.get('pmid', '').strip() or None,
            'url': ref.get('url', '').strip() or None,
            'abstract': ref.get('abstract', '').strip() or None,
            'keywords': ref.get('keywords', []),
            'publisher': ref.get('publisher', '').strip() or None,
            'publication_type': self._normalize_publication_type(ref.get('publication_type')),
            'language': ref.get('language', 'en'),
            'notes': ref.get('notes', '').strip() or None,
            'tags': ref.get('tags', []),
            'is_important': ref.get('is_important', False),
            'source_db': ref.get('source_db'),
            'source_id': ref.get('source_id'),
            'added_at': datetime.utcnow(),
            'status': 'active'
        }

        # 清理空值
        return {k: v for k, v in normalized.items() if v is not None and v != []}

    def _normalize_authors(self, authors: Any) -> List[str]:
        """规范化作者列表"""
        if isinstance(authors, str):
            # 分割作者字符串
            separators = [';', ' and ', '，', '&']
            for sep in separators:
                if sep in authors:
                    return [a.strip() for a in authors.split(sep) if a.strip()]
            return [authors.strip()]
        elif isinstance(authors, list):
            return [str(a).strip() for a in authors if str(a).strip()]
        return []

    def _normalize_year(self, year: Any) -> Optional[int]:
        """规范化年份"""
        if year is None:
            return None
        if isinstance(year, int):
            return year if 1000 < year < 2100 else None
        if isinstance(year, str):
            # 提取年份数字
            match = re.search(r'(\d{4})', year)
            if match:
                y = int(match.group(1))
                return y if 1000 < y < 2100 else None
        return None

    def _normalize_publication_type(self, pub_type: Optional[str]) -> str:
        """规范化文献类型"""
        if not pub_type:
            return 'journal'

        pub_type = pub_type.lower().strip()

        type_mapping = {
            'journal article': 'journal',
            'article': 'journal',
            'journal': 'journal',
            'conference paper': 'conference',
            'conference': 'conference',
            'proceedings': 'conference',
            'book': 'book',
            'monograph': 'book',
            'thesis': 'thesis',
            'dissertation': 'thesis',
            'master thesis': 'thesis',
            'phd thesis': 'thesis',
            'report': 'report',
            'technical report': 'report',
            'web page': 'online',
            'website': 'online',
            'electronic': 'online',
            'online': 'online',
            'preprint': 'journal',
            'working paper': 'other',
        }

        return type_mapping.get(pub_type, 'other')

    def _detect_duplicates(self, references: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """检测重复项"""
        seen = {}
        unique = []
        duplicates = []

        for ref in references:
            # 使用 DOI 或标题+作者+年份作为唯一标识
            key = None
            if ref.get('doi'):
                key = ref['doi'].lower()
            elif ref.get('title') and ref.get('publication_year'):
                title_key = re.sub(r'[^\w]', '', ref['title'].lower())
                key = f"{title_key}_{ref.get('publication_year')}"

            if key and key in seen:
                duplicates.append({
                    'reference': ref,
                    'duplicate_of': seen[key],
                    'reason': 'DOI或标题重复'
                })
            else:
                if key:
                    seen[key] = ref
                unique.append(ref)

        return unique, duplicates


class ZoteroAdapter(BaseImportAdapter):
    """Zotero 导入适配器"""

    ZOTERO_API_BASE = 'https://api.zotero.org'

    async def import_from_api(
        self,
        credentials: Dict[str, str],
        collection_key: Optional[str] = None
    ) -> ImportResult:
        """
        从 Zotero API 导入

        Args:
            credentials: { 'user_id': 'xxx', 'api_key': 'xxx' }
            collection_key: 特定收藏夹的 key
        """
        user_id = credentials.get('user_id')
        api_key = credentials.get('api_key')

        if not user_id or not api_key:
            return ImportResult(
                success=False,
                references=[],
                errors=[{'error': '缺少 Zotero 用户ID 或 API Key'}],
                total_count=0,
                success_count=0,
                failed_count=0,
                duplicates=[]
            )

        headers = {
            'Zotero-API-Key': api_key,
            'Zotero-API-Version': '3'
        }

        references = []
        errors = []
        start = 0
        limit = 100

        async with aiohttp.ClientSession(headers=headers) as session:
            # 构建 URL
            if collection_key:
                url = f"{self.ZOTERO_API_BASE}/users/{user_id}/collections/{collection_key}/items"
            else:
                url = f"{self.ZOTERO_API_BASE}/users/{user_id}/items"

            # 分页获取所有条目
            while True:
                params = {
                    'start': start,
                    'limit': limit,
                    'format': 'json',
                    'include': 'data'
                }

                try:
                    async with session.get(url, params=params) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            return ImportResult(
                                success=False,
                                references=[],
                                errors=[{'error': f'Zotero API 错误: {response.status} - {error_text}'}],
                                total_count=0,
                                success_count=0,
                                failed_count=0,
                                duplicates=[]
                            )

                        items = await response.json()

                        if not items:
                            break

                        for item in items:
                            try:
                                ref = self._parse_zotero_item(item)
                                if ref:
                                    references.append(ref)
                            except Exception as e:
                                errors.append({
                                    'item_key': item.get('key', 'unknown'),
                                    'error': str(e)
                                })

                        if len(items) < limit:
                            break

                        start += limit

                except aiohttp.ClientError as e:
                    return ImportResult(
                        success=False,
                        references=[],
                        errors=[{'error': f'网络请求失败: {str(e)}'}],
                        total_count=0,
                        success_count=0,
                        failed_count=0,
                        duplicates=[]
                    )

        # 规范化并去重
        normalized = [self._normalize_reference(ref) for ref in references]
        unique_refs, duplicates = self._detect_duplicates(normalized)

        return ImportResult(
            success=True,
            references=unique_refs,
            errors=errors,
            total_count=len(references),
            success_count=len(unique_refs),
            failed_count=len(errors),
            duplicates=duplicates
        )

    async def import_from_file(self, file_content: bytes) -> ImportResult:
        """从 Zotero 导出的 RDF/BibTeX/JSON 导入"""
        # 检测文件类型
        content_str = file_content.decode('utf-8', errors='ignore')

        if content_str.startswith('{'):
            # JSON 格式
            return await self._import_from_json(file_content)
        elif '<rdf:RDF' in content_str or '<bib:Article' in content_str:
            # RDF 格式
            return await self._import_from_rdf(file_content)
        elif '@' in content_str and '{' in content_str:
            # BibTeX 格式
            from .parsers import parse_bibtex
            refs = parse_bibtex(content_str)
            normalized = [self._normalize_reference({**ref, 'source_db': 'zotero'}) for ref in refs]
            unique_refs, duplicates = self._detect_duplicates(normalized)

            return ImportResult(
                success=True,
                references=unique_refs,
                errors=[],
                total_count=len(refs),
                success_count=len(unique_refs),
                failed_count=0,
                duplicates=duplicates
            )
        else:
            return ImportResult(
                success=False,
                references=[],
                errors=[{'error': '不支持的 Zotero 导出格式'}],
                total_count=0,
                success_count=0,
                failed_count=0,
                duplicates=[]
            )

    def _parse_zotero_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析 Zotero API 返回的条目"""
        data = item.get('data', {})

        if not data.get('title'):
            return None

        # 解析作者
        creators = data.get('creators', [])
        authors = []
        for creator in creators:
            if creator.get('creatorType') in ['author', 'editor', 'director']:
                first_name = creator.get('firstName', '')
                last_name = creator.get('lastName', '')
                if first_name and last_name:
                    authors.append(f"{first_name} {last_name}")
                elif last_name:
                    authors.append(last_name)

        return {
            'title': data.get('title', ''),
            'authors': authors,
            'publication_year': data.get('date'),
            'journal_name': data.get('publicationTitle') or data.get('proceedingsTitle'),
            'volume': data.get('volume'),
            'issue': data.get('issue'),
            'pages': data.get('pages'),
            'doi': data.get('DOI'),
            'url': data.get('url'),
            'abstract': data.get('abstractNote'),
            'keywords': data.get('tags', []),
            'publisher': data.get('publisher'),
            'publication_type': data.get('itemType', 'journal'),
            'language': data.get('language', 'en'),
            'notes': data.get('notes', [{}])[0].get('note', '') if data.get('notes') else None,
            'source_db': 'zotero',
            'source_id': item.get('key')
        }

    async def _import_from_json(self, file_content: bytes) -> ImportResult:
        """从 Zotero JSON 导入"""
        import json
        try:
            data = json.loads(file_content.decode('utf-8'))

            # 可能是数组或对象
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and 'items' in data:
                items = data['items']
            else:
                items = [data]

            references = []
            errors = []

            for item in items:
                try:
                    ref = self._parse_zotero_item({'data': item})
                    if ref:
                        references.append(ref)
                except Exception as e:
                    errors.append({'error': str(e)})

            normalized = [self._normalize_reference(ref) for ref in references]
            unique_refs, duplicates = self._detect_duplicates(normalized)

            return ImportResult(
                success=True,
                references=unique_refs,
                errors=errors,
                total_count=len(references),
                success_count=len(unique_refs),
                failed_count=len(errors),
                duplicates=duplicates
            )

        except json.JSONDecodeError as e:
            return ImportResult(
                success=False,
                references=[],
                errors=[{'error': f'JSON 解析失败: {str(e)}'}],
                total_count=0,
                success_count=0,
                failed_count=0,
                duplicates=[]
            )

    async def _import_from_rdf(self, file_content: bytes) -> ImportResult:
        """从 Zotero RDF 导入"""
        try:
            root = ET.fromstring(file_content.decode('utf-8'))

            # RDF 命名空间
            ns = {
                'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'bib': 'http://purl.org/net/biblio#',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'dcterms': 'http://purl.org/dc/terms/',
                'foaf': 'http://xmlns.com/foaf/0.1/',
                'z': 'http://www.zotero.org/namespaces/export#'
            }

            references = []

            # 查找所有文献条目
            for article in root.findall('.//bib:Article', ns):
                try:
                    ref = {}

                    # 标题
                    title = article.find('dc:title', ns)
                    if title is not None:
                        ref['title'] = title.text

                    # 作者
                    authors = []
                    for creator in article.findall('.//foaf:Person', ns):
                        firstname = creator.find('foaf:firstName', ns)
                        lastname = creator.find('foaf:surname', ns)
                        if firstname is not None and lastname is not None:
                            authors.append(f"{firstname.text} {lastname.text}")
                        elif lastname is not None:
                            authors.append(lastname.text)
                    if authors:
                        ref['authors'] = authors

                    # 期刊
                    journal = article.find('dcterms:isPartOf/bib:Journal/dc:title', ns)
                    if journal is not None:
                        ref['journal_name'] = journal.text

                    # 日期
                    date = article.find('dc:date', ns)
                    if date is not None:
                        ref['publication_year'] = date.text

                    # DOI
                    doi = article.find('bib:doi', ns)
                    if doi is not None:
                        ref['doi'] = doi.text

                    # URL
                    url = article.find('dc:identifier', ns)
                    if url is not None and url.text.startswith('http'):
                        ref['url'] = url.text

                    # 摘要
                    abstract = article.find('dcterms:abstract', ns)
                    if abstract is not None:
                        ref['abstract'] = abstract.text

                    ref['source_db'] = 'zotero'

                    if ref.get('title'):
                        references.append(ref)

                except Exception:
                    continue

            normalized = [self._normalize_reference(ref) for ref in references]
            unique_refs, duplicates = self._detect_duplicates(normalized)

            return ImportResult(
                success=True,
                references=unique_refs,
                errors=[],
                total_count=len(references),
                success_count=len(unique_refs),
                failed_count=0,
                duplicates=duplicates
            )

        except ET.ParseError as e:
            return ImportResult(
                success=False,
                references=[],
                errors=[{'error': f'RDF 解析失败: {str(e)}'}],
                total_count=0,
                success_count=0,
                failed_count=0,
                duplicates=[]
            )


class EndNoteAdapter(BaseImportAdapter):
    """EndNote 导入适配器"""

    async def import_from_file(self, file_content: bytes) -> ImportResult:
        """从 EndNote 导出的 XML 导入"""
        try:
            root = ET.fromstring(file_content.decode('utf-8'))

            references = []
            errors = []

            # EndNote XML 命名空间
            ns = {'': 'http://www.endnote.com/exportformat/4/0/'}

            # 查找所有记录
            for record in root.findall('.//record'):
                try:
                    ref = self._parse_endnote_record(record)
                    if ref and ref.get('title'):
                        ref['source_db'] = 'endnote'
                        references.append(ref)
                except Exception as e:
                    errors.append({'error': str(e)})

            normalized = [self._normalize_reference(ref) for ref in references]
            unique_refs, duplicates = self._detect_duplicates(normalized)

            return ImportResult(
                success=True,
                references=unique_refs,
                errors=errors,
                total_count=len(references),
                success_count=len(unique_refs),
                failed_count=len(errors),
                duplicates=duplicates
            )

        except ET.ParseError as e:
            return ImportResult(
                success=False,
                references=[],
                errors=[{'error': f'XML 解析失败: {str(e)}'}],
                total_count=0,
                success_count=0,
                failed_count=0,
                duplicates=[]
            )

    def _parse_endnote_record(self, record: ET.Element) -> Dict[str, Any]:
        """解析 EndNote XML 记录"""
        ref = {}

        # 获取文献类型
        ref_type = record.find('.//ref-type')
        if ref_type is not None:
            type_id = ref_type.get('name', 'Journal Article')
            ref['publication_type'] = self._map_endnote_type(type_id)

        # 作者
        contributors = record.find('.//contributors')
        if contributors is not None:
            authors = []
            for author in contributors.findall('.//author'):
                first = author.find('first-name')
                last = author.find('last-name')
                if first is not None and last is not None:
                    authors.append(f"{first.text} {last.text}")
                elif last is not None:
                    authors.append(last.text)
            if authors:
                ref['authors'] = authors

        # 标题
        titles = record.find('.//titles')
        if titles is not None:
            title = titles.find('title')
            if title is not None:
                ref['title'] = title.text

        # 期刊
        periodical = record.find('.//periodical')
        if periodical is not None:
            full_title = periodical.find('full-title')
            if full_title is not None:
                ref['journal_name'] = full_title.text

        # 年份
        dates = record.find('.//dates')
        if dates is not None:
            year = dates.find('year')
            if year is not None:
                ref['publication_year'] = year.text

        # 卷期页
        volume = record.find('.//volume')
        if volume is not None:
            ref['volume'] = volume.text

        issue = record.find('.//issue')
        if issue is not None:
            ref['issue'] = issue.text

        pages = record.find('.//pages')
        if pages is not None:
            ref['pages'] = pages.text

        # DOI
        doi = record.find('.//electronic-resource-num')
        if doi is not None:
            ref['doi'] = doi.text

        # URL
        urls = record.find('.//urls')
        if urls is not None:
            web_urls = urls.find('web-urls')
            if web_urls is not None:
                url = web_urls.find('url')
                if url is not None:
                    ref['url'] = url.text

        # 摘要
        abstract = record.find('.//abstract')
        if abstract is not None:
            ref['abstract'] = abstract.text

        # 关键词
        keywords = record.findall('.//keyword')
        if keywords:
            ref['keywords'] = [k.text for k in keywords if k.text]

        # 出版商
        publisher = record.find('.//publisher')
        if publisher is not None:
            ref['publisher'] = publisher.text

        return ref

    def _map_endnote_type(self, type_name: str) -> str:
        """映射 EndNote 类型"""
        type_mapping = {
            'Journal Article': 'journal',
            'Book': 'book',
            'Conference Proceedings': 'conference',
            'Conference Paper': 'conference',
            'Thesis': 'thesis',
            'Report': 'report',
            'Web Page': 'online',
            'Electronic Article': 'online',
        }
        return type_mapping.get(type_name, 'other')


class MendeleyAdapter(BaseImportAdapter):
    """Mendeley 导入适配器"""

    async def import_from_file(self, file_content: bytes) -> ImportResult:
        """从 Mendeley 导出的 JSON/BibTeX/RIS 导入"""
        content_str = file_content.decode('utf-8', errors='ignore')

        if content_str.startswith('{'):
            # JSON 格式
            return await self._import_from_json(file_content)
        elif '@' in content_str and '{' in content_str:
            # BibTeX 格式
            from .parsers import parse_bibtex
            refs = parse_bibtex(content_str)
            normalized = [self._normalize_reference({**ref, 'source_db': 'mendeley'}) for ref in refs]
            unique_refs, duplicates = self._detect_duplicates(normalized)

            return ImportResult(
                success=True,
                references=unique_refs,
                errors=[],
                total_count=len(refs),
                success_count=len(unique_refs),
                failed_count=0,
                duplicates=duplicates
            )
        else:
            return ImportResult(
                success=False,
                references=[],
                errors=[{'error': '不支持的 Mendeley 导出格式'}],
                total_count=0,
                success_count=0,
                failed_count=0,
                duplicates=[]
            )

    async def _import_from_json(self, file_content: bytes) -> ImportResult:
        """从 Mendeley JSON 导入"""
        import json
        try:
            data = json.loads(file_content.decode('utf-8'))

            # Mendeley 导出的 JSON 可能是一个数组
            if isinstance(data, list):
                documents = data
            elif isinstance(data, dict):
                documents = data.get('documents', [])
            else:
                documents = []

            references = []
            errors = []

            for doc in documents:
                try:
                    ref = self._parse_mendeley_document(doc)
                    if ref and ref.get('title'):
                        ref['source_db'] = 'mendeley'
                        references.append(ref)
                except Exception as e:
                    errors.append({'error': str(e)})

            normalized = [self._normalize_reference(ref) for ref in references]
            unique_refs, duplicates = self._detect_duplicates(normalized)

            return ImportResult(
                success=True,
                references=unique_refs,
                errors=errors,
                total_count=len(references),
                success_count=len(unique_refs),
                failed_count=len(errors),
                duplicates=duplicates
            )

        except json.JSONDecodeError as e:
            return ImportResult(
                success=False,
                references=[],
                errors=[{'error': f'JSON 解析失败: {str(e)}'}],
                total_count=0,
                success_count=0,
                failed_count=0,
                duplicates=[]
            )

    def _parse_mendeley_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """解析 Mendeley 文档"""
        ref = {
            'title': doc.get('title', ''),
            'authors': [f"{a.get('first_name', '')} {a.get('last_name', '')}".strip()
                       for a in doc.get('authors', [])],
            'publication_year': doc.get('year'),
            'journal_name': doc.get('source') or doc.get('publication'),
            'volume': doc.get('volume'),
            'issue': doc.get('issue'),
            'pages': doc.get('pages'),
            'doi': doc.get('doi'),
            'url': doc.get('websites', [None])[0] if doc.get('websites') else None,
            'abstract': doc.get('abstract'),
            'keywords': doc.get('keywords', []),
            'publisher': doc.get('publisher'),
            'publication_type': doc.get('type', 'journal'),
            'source_id': doc.get('id')
        }

        return ref


class CNKIAdapter(BaseImportAdapter):
    """知网导入适配器"""

    async def import_from_file(self, file_content: bytes) -> ImportResult:
        """从知网导出的 Refworks/EndNote/NoteExpress 格式导入"""
        content_str = file_content.decode('utf-8', errors='ignore')

        # 检测格式
        if 'RT ' in content_str or 'TY  - ' in content_str:
            # RIS 格式
            from .parsers import parse_ris
            refs = parse_ris(content_str)
        elif '%0' in content_str or '%A' in content_str:
            # 自定义格式
            refs = self._parse_cnki_custom(content_str)
        else:
            # 尝试文本解析
            refs = self._parse_cnki_text(content_str)

        # 添加来源标记
        for ref in refs:
            ref['source_db'] = 'cnki'

        normalized = [self._normalize_reference(ref) for ref in refs]
        unique_refs, duplicates = self._detect_duplicates(normalized)

        return ImportResult(
            success=True,
            references=unique_refs,
            errors=[],
            total_count=len(refs),
            success_count=len(unique_refs),
            failed_count=0,
            duplicates=duplicates
        )

    def _parse_cnki_custom(self, content: str) -> List[Dict[str, Any]]:
        """解析知网自定义格式"""
        references = []
        current_ref = {}

        lines = content.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                if current_ref and current_ref.get('title'):
                    references.append(current_ref)
                current_ref = {}
                continue

            # 匹配知网字段格式 %X 内容
            match = re.match(r'^%([A-Z])\s*(.*)$', line)
            if match:
                field_code, value = match.groups()

                if field_code == '0':  # 文献类型
                    current_ref['publication_type'] = self._map_cnki_type(value)
                elif field_code == 'A':  # 作者
                    if 'authors' not in current_ref:
                        current_ref['authors'] = []
                    current_ref['authors'].append(value)
                elif field_code == 'T':  # 标题
                    current_ref['title'] = value
                elif field_code == 'J':  # 期刊
                    current_ref['journal_name'] = value
                elif field_code == 'D':  # 日期/年份
                    match = re.search(r'(\d{4})', value)
                    if match:
                        current_ref['publication_year'] = int(match.group(1))
                elif field_code == 'V':  # 卷
                    current_ref['volume'] = value
                elif field_code == 'N':  # 期
                    current_ref['issue'] = value
                elif field_code == 'P':  # 页码
                    current_ref['pages'] = value
                elif field_code == 'K':  # 关键词
                    current_ref['keywords'] = [k.strip() for k in value.split(';')]
                elif field_code == 'X':  # 摘要
                    current_ref['abstract'] = value
                elif field_code == 'U':  # URL
                    current_ref['url'] = value

        if current_ref and current_ref.get('title'):
            references.append(current_ref)

        return references

    def _parse_cnki_text(self, content: str) -> List[Dict[str, Any]]:
        """解析知网纯文本格式"""
        references = []

        # 知网文本通常每行一个引用
        lines = content.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试匹配知网引用格式
            # 作者. 标题[J]. 期刊, 年, 卷(期): 页码.
            pattern = r'^([^\.]+)\.\s*([^\[]+)\[([^\]]+)\]\.\s*([^,]+),\s*(\d{4})(?:,\s*([^:]+))?'
            match = re.match(pattern, line)

            if match:
                ref = {
                    'authors': [a.strip() for a in match.group(1).split(',')],
                    'title': match.group(2).strip(),
                    'publication_type': self._map_cnki_type_code(match.group(3)),
                    'journal_name': match.group(4).strip(),
                    'publication_year': int(match.group(5)),
                }

                # 解析卷期页
                vol_issue = match.group(6)
                if vol_issue:
                    vol_match = re.match(r'(\d+)\((\d+)\):\s*(.+)', vol_issue)
                    if vol_match:
                        ref['volume'] = vol_match.group(1)
                        ref['issue'] = vol_match.group(2)
                        ref['pages'] = vol_match.group(3)

                references.append(ref)

        return references

    def _map_cnki_type(self, type_str: str) -> str:
        """映射知网类型"""
        type_mapping = {
            'Journal Article': 'journal',
            '会议论文': 'conference',
            '学位论文': 'thesis',
            '图书': 'book',
            '专利': 'other',
            '标准': 'other',
        }
        return type_mapping.get(type_str, 'journal')

    def _map_cnki_type_code(self, code: str) -> str:
        """映射知网类型代码"""
        type_mapping = {
            'J': 'journal',
            'C': 'conference',
            'D': 'thesis',
            'M': 'book',
            'P': 'patent',
            'S': 'standard',
        }
        return type_mapping.get(code.upper(), 'journal')


class ImportAdapterFactory:
    """导入适配器工厂"""

    _adapters = {
        'zotero': ZoteroAdapter,
        'endnote': EndNoteAdapter,
        'mendeley': MendeleyAdapter,
        'cnki': CNKIAdapter,
    }

    @classmethod
    def get_adapter(cls, source_type: str, user_id: str) -> BaseImportAdapter:
        """
        获取导入适配器

        Args:
            source_type: 数据源类型 (zotero/endnote/mendeley/cnki/...)
            user_id: 用户ID

        Returns:
            对应的导入适配器实例
        """
        adapter_class = cls._adapters.get(source_type.lower())
        if not adapter_class:
            raise ValueError(f"不支持的导入类型: {source_type}")

        return adapter_class(user_id)

    @classmethod
    def register_adapter(cls, source_type: str, adapter_class: type):
        """注册新的适配器"""
        cls._adapters[source_type.lower()] = adapter_class

    @classmethod
    def supported_types(cls) -> List[str]:
        """获取支持的导入类型"""
        return list(cls._adapters.keys())
