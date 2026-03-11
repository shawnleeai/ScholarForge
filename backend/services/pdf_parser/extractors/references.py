"""
PDF 参考文献提取器
支持 GB/T 7714、APA、IEEE 等常见引用格式
"""

import re
from typing import List, Optional, Dict
from ..schemas import Reference
import logging

logger = logging.getLogger(__name__)


class ReferenceExtractor:
    """参考文献提取器"""

    # 不同格式的参考文献特征
    FORMAT_PATTERNS = {
        'gb_t_7714': [
            r'^\[\d+\]\s*.+',  # [1] 作者. 标题[J]. ...
            r'^\d+[.\s]+.+',   # 1. 作者. 标题...
        ],
        'apa': [
            r'^[A-Z][a-z]+,\s*[A-Z]\.\s*\(\d{4}\)',  # Author, A. (2024)
        ],
        'ieee': [
            r'^\[\d+\]\s*[A-Z]',  # [1] A. Author
        ],
        'numeric': [
            r'^\[\d+\]\s*.+',
            r'^\(\d+\)\s*.+',
        ],
    }

    # DOI模式
    DOI_PATTERN = re.compile(r'10\.\d{4,}/[^\s,]+')

    # URL模式
    URL_PATTERN = re.compile(r'https?://[^\s,]+')

    # 年份模式
    YEAR_PATTERN = re.compile(r'\((\d{4})\)|(\d{4})')

    def extract(self, text: str) -> List[Reference]:
        """
        从文本中提取参考文献

        Args:
            text: 完整文本或参考文献章节文本

        Returns:
            List[Reference] 参考文献列表
        """
        # 找到参考文献章节
        ref_section = self._find_reference_section(text)
        if not ref_section:
            logger.info("未找到参考文献章节")
            return []

        # 确定引用格式类型
        ref_format = self._detect_format(ref_section)
        logger.info(f"检测到引用格式: {ref_format}")

        # 解析参考文献
        raw_refs = self._split_references(ref_section, ref_format)
        references = []

        for i, raw_ref in enumerate(raw_refs, 1):
            if len(raw_ref.strip()) < 10:  # 太短的跳过
                continue
            try:
                ref = self._parse_single_reference(raw_ref, i)
                if ref:
                    references.append(ref)
            except Exception as e:
                logger.warning(f"解析参考文献 #{i} 失败: {e}")
                # 仍然添加原始文本
                references.append(Reference(
                    id=f"ref_{i}",
                    raw_text=raw_ref.strip(),
                    authors=[],
                    title="",
                ))

        return references

    def _find_reference_section(self, text: str) -> str:
        """找到参考文献章节"""
        # 匹配参考文献标题后的内容
        patterns = [
            r'(?:参考文献|References?|Bibliography)[\s:：]*\n+(.+?)(?=\n\s*(?:附录|Appendix|致谢|Acknowledgment)|$)',
            r'(?:参考文献|References?|Bibliography)[\s:：]*\n+(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _detect_format(self, text: str) -> str:
        """检测引用格式类型"""
        lines = text.split('\n')[:20]  # 检查前20行

        for format_name, patterns in self.FORMAT_PATTERNS.items():
            match_count = 0
            for line in lines:
                for pattern in patterns:
                    if re.match(pattern, line.strip()):
                        match_count += 1
                        break
            if match_count >= 3:  # 至少有3个匹配
                return format_name

        return 'unknown'

    def _split_references(self, text: str, ref_format: str) -> List[str]:
        """将参考文献章节分割成单独条目"""
        refs = []

        if ref_format in ['gb_t_7714', 'ieee', 'numeric']:
            # 数字编号格式
            # 匹配 [数字] 或 数字. 开头的行
            pattern = r'(?:^|\n)\s*(?:\[(\d+)\]|(\d+)[.\s])\s*'
            parts = re.split(pattern, text)

            current_ref = ""
            for i, part in enumerate(parts):
                if part and part.strip().isdigit():
                    # 这是一个编号
                    if current_ref:
                        refs.append(current_ref.strip())
                    current_ref = ""
                elif part:
                    current_ref += part

            if current_ref:
                refs.append(current_ref.strip())

        else:
            # 作者-年份格式（APA等）
            # 匹配 作者姓氏, 名字首字母 开头的行
            lines = text.split('\n')
            current_ref = ""

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 检查是否是新条目的开始
                if re.match(r'^[A-Z][a-z]+,\s*[A-Z]', line) or \
                   re.match(r'^[A-Z][a-z]+\s+[A-Z]\.\s*,', line):
                    if current_ref:
                        refs.append(current_ref.strip())
                    current_ref = line
                else:
                    current_ref += " " + line

            if current_ref:
                refs.append(current_ref.strip())

        return refs

    def _parse_single_reference(self, raw_text: str, index: int) -> Optional[Reference]:
        """解析单个参考文献"""
        # 移除编号
        clean_text = re.sub(r'^\[?\d+\]?[.\s]*', '', raw_text.strip())

        # 提取作者
        authors = self._extract_authors(clean_text)

        # 提取年份
        year_match = self.YEAR_PATTERN.search(clean_text)
        year = int(year_match.group(1) or year_match.group(2)) if year_match else None

        # 提取标题（通常在引号或期刊名之前）
        title = self._extract_title(clean_text)

        # 提取期刊
        journal = self._extract_journal(clean_text)

        # 提取DOI
        doi_match = self.DOI_PATTERN.search(clean_text)
        doi = doi_match.group(0) if doi_match else None

        # 提取URL
        url_match = self.URL_PATTERN.search(clean_text)
        url = url_match.group(0) if url_match else None

        return Reference(
            id=f"ref_{index}",
            raw_text=raw_text.strip(),
            authors=authors,
            title=title or "Unknown",
            journal=journal or "Unknown",
            year=year,
            doi=doi,
            url=url,
        )

    def _extract_authors(self, text: str) -> List[str]:
        """提取作者列表"""
        authors = []

        # GB/T 7714 格式: 作者1, 作者2, 等. 或 作者1, 作者2, 作者3.
        gb_match = re.match(r'^([^[（(]+?)[.,][\s\u3000]*', text)
        if gb_match:
            author_part = gb_match.group(1)
            # 分割多个作者
            for author in re.split(r'[,，;；]', author_part):
                author = author.strip()
                if author and len(author) > 1 and not author.startswith('et'):
                    authors.append(author)

        # 如果没有提取到作者，尝试其他模式
        if not authors:
            # 匹配 "作者 et al." 或 "作者等"
            et_al_match = re.search(r'^([^.]+?)\s+(?:et\s+al|等)[.,]', text)
            if et_al_match:
                authors = [a.strip() for a in et_al_match.group(1).split(',') if a.strip()]

        return authors[:10]  # 最多返回10个作者

    def _extract_title(self, text: str) -> Optional[str]:
        """提取论文标题"""
        # 尝试匹配引号中的标题
        patterns = [
            r'[""]([^""]+)[""]',
            r'[《〈]([^》〉]+)[》〉]',
            r'\[J\][.,\s]*([^[.,]+)',
            r'\)\.[\s]*(.+?)(?:\[|\.\s*\d)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                if len(title) > 5:  # 标题应该有一定长度
                    return title

        return None

    def _extract_journal(self, text: str) -> Optional[str]:
        """提取期刊名称"""
        # 匹配 [J] 后的期刊名
        journal_match = re.search(r'\[J\][.,\s]*([^.,\d\[]+)', text)
        if journal_match:
            return journal_match.group(1).strip()

        # 匹配年份前的期刊名
        journal_match = re.search(r'\.\s*([^.,\d]+?),?\s*\d{4}', text)
        if journal_match:
            return journal_match.group(1).strip()

        return None

    def normalize_reference(self, ref: Reference) -> Reference:
        """规范化参考文献格式"""
        # 清理作者名
        ref.authors = [a.strip() for a in ref.authors if a.strip()]

        # 清理标题
        if ref.title:
            ref.title = ref.title.strip().rstrip('.')

        # 清理期刊名
        if ref.journal:
            ref.journal = ref.journal.strip().rstrip(',.')

        return ref
