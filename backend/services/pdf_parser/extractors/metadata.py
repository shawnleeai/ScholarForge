"""
PDF 元数据提取器
提取标题、作者、DOI、期刊等信息
"""

import re
import fitz
from typing import Optional, List, Dict
from ..schemas import PDFMetadata
import logging

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """PDF元数据提取器"""

    # DOI正则表达式
    DOI_PATTERN = re.compile(r'10\.\d{4,}/[^\s,;:<>"\']+')

    # 年份模式
    YEAR_PATTERN = re.compile(r'\b(19|20)\d{2}\b')

    def extract(self, pdf_path: str, text: str = None) -> PDFMetadata:
        """
        提取PDF元数据

        Args:
            pdf_path: PDF文件路径
            text: 已提取的文本（可选）

        Returns:
            PDFMetadata 元数据对象
        """
        metadata = PDFMetadata()

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"无法打开PDF: {e}")
            return metadata

        # 1. 提取PDF内置元数据
        self._extract_pdf_metadata(doc, metadata)

        # 2. 如果没有提供文本，提取第一页文本
        if text is None and len(doc) > 0:
            text = doc[0].get_text()
            # 也提取第二页（有时标题跨页）
            if len(doc) > 1:
                text += "\n" + doc[1].get_text()

        doc.close()

        # 3. 从文本中提取元数据
        if text:
            self._extract_from_text(text, metadata)

        return metadata

    def _extract_pdf_metadata(self, doc: fitz.Document, metadata: PDFMetadata):
        """提取PDF内置元数据"""
        pdf_meta = doc.metadata

        if pdf_meta.get('title'):
            metadata.title = pdf_meta['title']

        if pdf_meta.get('author'):
            metadata.authors = self._parse_authors(pdf_meta['author'])

    def _extract_from_text(self, text: str, metadata: PDFMetadata):
        """从文本中提取元数据"""
        lines = text.split('\n')

        # 提取标题（通常在开头几行）
        if not metadata.title:
            metadata.title = self._extract_title(text)

        # 提取作者（如果没有从PDF元数据获取）
        if not metadata.authors:
            metadata.authors = self._extract_authors_from_text(text)

        # 提取DOI
        if not metadata.doi:
            metadata.doi = self._extract_doi(text)

        # 提取年份
        if not metadata.publication_year:
            metadata.publication_year = self._extract_year(text)

        # 提取关键词
        if not metadata.keywords:
            metadata.keywords = self._extract_keywords(text)

        # 检测语言
        metadata.language = self._detect_language(text)

    def _extract_title(self, text: str) -> Optional[str]:
        """提取论文标题"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        # 跳过第一行（可能是页眉）
        start_idx = 1 if len(lines) > 1 else 0

        # 寻找可能的标题行（较长、居中的文本）
        candidates = []
        for i, line in enumerate(lines[start_idx:start_idx + 10], start_idx):
            # 标题特征：较长、没有标点（除了冒号）、可能全大写或首字母大写
            if 20 <= len(line) <= 200:
                if line.isupper() or line.istitle() or ':' in line:
                    candidates.append((i, line))

        if candidates:
            # 选择最长的一个作为标题
            return max(candidates, key=lambda x: len(x[1]))[1]

        # 如果没有找到，返回前几个非空行的组合
        if len(lines) > start_idx:
            return ' '.join(lines[start_idx:start_idx + 2])

        return None

    def _parse_authors(self, author_str: str) -> List[str]:
        """解析作者字符串"""
        # 分隔符可能是 , ; & 或 and
        authors = re.split(r'[,;]|\band\b', author_str)
        return [a.strip() for a in authors if a.strip() and len(a.strip()) > 2]

    def _extract_authors_from_text(self, text: str) -> List[str]:
        """从文本中提取作者"""
        lines = text.split('\n')
        authors = []

        # 通常在标题后的几行
        for i, line in enumerate(lines[:20]):
            line = line.strip()
            if not line:
                continue

            # 匹配作者行特征
            # 1. 包含逗号分隔的名字
            # 2. 可能包含上标数字（单位标记）
            # 3. 不包含常见的中文词汇（排除不是作者行）

            if ',' in line or '，' in line:
                # 排除包含这些词的行
                exclude_words = ['摘要', '关键词', 'Abstract', 'Keywords', '引言', 'Introduction']
                if not any(w in line for w in exclude_words):
                    # 移除上标数字
                    cleaned = re.sub(r'[\u00b0-\u00b9\u2070-\u2079†‡*]+', '', line)
                    # 分割作者
                    parts = re.split(r'[,，;；]', cleaned)
                    potential_authors = [p.strip() for p in parts if 2 < len(p.strip()) < 50]

                    if len(potential_authors) >= 1:
                        authors = potential_authors
                        break

        return authors[:10]  # 限制作者数量

    def _extract_doi(self, text: str) -> Optional[str]:
        """提取DOI"""
        match = self.DOI_PATTERN.search(text)
        if match:
            doi = match.group(0)
            # 清理可能的尾随字符
            doi = doi.rstrip('.,;:)')
            return doi
        return None

    def _extract_year(self, text: str) -> Optional[int]:
        """提取发表年份"""
        # 优先查找括号中的年份 (2024)
        match = re.search(r'\((\d{4})\)', text)
        if match:
            year = int(match.group(1))
            if 1900 < year < 2030:
                return year

        # 查找其他年份格式
        matches = self.YEAR_PATTERN.findall(text)
        for match in matches:
            year = int(match)
            if 1900 < year < 2030:
                return year

        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        patterns = [
            r'关键词[：:]\s*(.+?)(?=\n|摘要|Abstract)',
            r'Keywords[：:]\s*(.+?)(?=\n)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                keywords_str = match.group(1).strip()
                # 分割关键词
                keywords = re.split(r'[,，;；]', keywords_str)
                return [k.strip() for k in keywords if k.strip()]

        return []

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 简单检测：检查中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text)

        if total_chars > 0 and chinese_chars / total_chars > 0.1:
            return 'zh'
        return 'en'
