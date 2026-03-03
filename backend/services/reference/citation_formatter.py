"""
引用格式生成器
支持多种学术引用格式：APA、MLA、Chicago、GB/T 7714、IEEE、Harvard 等
"""

from typing import Dict, Any, Optional, List
import re


class CitationFormatter:
    """引用格式生成器"""

    def format(self, reference: Dict[str, Any], style: str = "gb7714") -> str:
        """
        格式化完整引用

        Args:
            reference: 参考文献数据
            style: 引用格式风格

        Returns:
            格式化后的引用字符串
        """
        formatters = {
            'apa': self._format_apa,
            'mla': self._format_mla,
            'chicago': self._format_chicago,
            'gb7714': self._format_gb7714,
            'ieee': self._format_ieee,
            'harvard': self._format_harvard,
            'vancouver': self._format_vancouver,
        }

        formatter = formatters.get(style.lower(), self._format_gb7714)
        return formatter(reference)

    def format_in_text(self, reference: Dict[str, Any], style: str = "gb7714") -> str:
        """
        格式化文中引用

        Args:
            reference: 参考文献数据
            style: 引用格式风格

        Returns:
            文中引用格式
        """
        in_text_formatters = {
            'apa': self._in_text_apa,
            'mla': self._in_text_mla,
            'chicago': self._in_text_chicago,
            'gb7714': self._in_text_gb7714,
            'ieee': self._in_text_ieee,
            'harvard': self._in_text_harvard,
            'vancouver': self._in_text_vancouver,
        }

        formatter = in_text_formatters.get(style.lower(), self._in_text_gb7714)
        return formatter(reference)

    def format_bibliography(
        self,
        references: List[Dict[str, Any]],
        style: str = "gb7714"
    ) -> str:
        """
        格式化参考文献列表

        Args:
            references: 参考文献列表
            style: 引用格式风格

        Returns:
            格式化后的参考文献列表
        """
        formatted_refs = []
        for i, ref in enumerate(references, 1):
            if style == 'ieee' or style == 'vancouver':
                # 编号制格式
                formatted = f"[{i}] {self.format(ref, style)}"
            else:
                formatted = self.format(ref, style)
            formatted_refs.append(formatted)

        return '\n'.join(formatted_refs)

    # ============== APA 格式 ==============

    def _format_apa(self, ref: Dict[str, Any]) -> str:
        """APA 第7版格式"""
        parts = []

        # 作者
        authors = ref.get('authors', [])
        if authors:
            if len(authors) == 1:
                author_str = self._format_author_apa(authors[0])
            elif len(authors) == 2:
                author_str = f"{self._format_author_apa(authors[0])} & {self._format_author_apa(authors[1])}"
            elif len(authors) <= 20:
                author_str = ', '.join([self._format_author_apa(a) for a in authors[:-1]])
                author_str += f", & {self._format_author_apa(authors[-1])}"
            else:
                author_str = ', '.join([self._format_author_apa(a) for a in authors[:19]])
                author_str += ', ... '
                author_str += self._format_author_apa(authors[-1])
            parts.append(author_str)

        # 年份
        year = ref.get('publication_year')
        if year:
            parts.append(f"({year})")

        # 标题
        title = ref.get('title', '')
        if title:
            if ref.get('publication_type') == 'journal':
                parts.append(title)
            else:
                parts.append(f"{title}")

        # 期刊/来源
        if ref.get('publication_type') == 'journal':
            journal = ref.get('journal_name', '')
            if journal:
                italic_journal = self._italicize(journal)
                volume = ref.get('volume', '')
                issue = ref.get('issue', '')
                pages = ref.get('pages', '')

                if volume:
                    italic_journal += f", {volume}"
                if issue:
                    italic_journal += f"({issue})"
                if pages:
                    italic_journal += f", {pages}"
                parts.append(italic_journal)
        else:
            source = ref.get('journal_name') or ref.get('publisher', '')
            if source:
                parts.append(f"{source}")

        # DOI
        doi = ref.get('doi', '')
        if doi:
            parts.append(f"https://doi.org/{doi}")

        return '. '.join(parts) + '.'

    def _in_text_apa(self, ref: Dict[str, Any]) -> str:
        """APA 文中引用"""
        authors = ref.get('authors', [])
        year = ref.get('publication_year', '')

        if not authors:
            return f"({year})"

        if len(authors) == 1:
            author = authors[0].split()[-1]
            return f"({author}, {year})"
        elif len(authors) == 2:
            author1 = authors[0].split()[-1]
            author2 = authors[1].split()[-1]
            return f"({author1} & {author2}, {year})"
        else:
            author = authors[0].split()[-1]
            return f"({author} et al., {year})"

    def _format_author_apa(self, author: str) -> str:
        """格式化 APA 作者名"""
        parts = author.split()
        if len(parts) >= 2:
            last_name = parts[-1]
            initials = ''.join([p[0] + '.' for p in parts[:-1]])
            return f"{last_name}, {initials}"
        return author

    # ============== MLA 格式 ==============

    def _format_mla(self, ref: Dict[str, Any]) -> str:
        """MLA 第9版格式"""
        parts = []

        # 作者
        authors = ref.get('authors', [])
        if authors:
            author_str = self._format_author_mla(authors[0])
            if len(authors) > 1:
                author_str += f", et al"
            parts.append(author_str)

        # 标题
        title = ref.get('title', '')
        if title:
            if ref.get('publication_type') == 'journal':
                parts.append(f'"{title}."')
            else:
                parts.append(f"{title}")

        # 容器（期刊/来源）
        if ref.get('publication_type') == 'journal':
            journal = ref.get('journal_name', '')
            if journal:
                container = self._italicize(journal)
                volume = ref.get('volume', '')
                issue = ref.get('issue', '')
                year = ref.get('publication_year', '')
                pages = ref.get('pages', '')

                if volume:
                    container += f", vol. {volume}"
                if issue:
                    container += f", no. {issue}"
                if year:
                    container += f", {year}"
                if pages:
                    container += f", pp. {pages}"
                parts.append(container)

        # DOI/URL
        doi = ref.get('doi', '')
        url = ref.get('url', '')
        if doi:
            parts.append(f"doi:{doi}")
        elif url:
            parts.append(url)

        return '. '.join(parts) + '.'

    def _in_text_mla(self, ref: Dict[str, Any]) -> str:
        """MLA 文中引用"""
        authors = ref.get('authors', [])
        page = ref.get('pages', '').split('-')[0]  # 使用起始页

        if not authors:
            return ""

        author = authors[0].split()[-1]
        if page:
            return f"({author} {page})"
        return f"({author})"

    def _format_author_mla(self, author: str) -> str:
        """格式化 MLA 作者名"""
        parts = author.split()
        if len(parts) >= 2:
            last_name = parts[-1]
            first_names = ' '.join(parts[:-1])
            return f"{last_name}, {first_names}"
        return author

    # ============== Chicago 格式 ==============

    def _format_chicago(self, ref: Dict[str, Any]) -> str:
        """Chicago 第17版（作者-日期）格式"""
        parts = []

        # 作者
        authors = ref.get('authors', [])
        if authors:
            author_str = self._format_author_chicago(authors[0])
            if len(authors) > 3:
                author_str += " et al."
            elif len(authors) > 1:
                author_str += f", {self._format_author_chicago(authors[1])}"
            parts.append(author_str)

        # 年份
        year = ref.get('publication_year')
        if year:
            parts.append(str(year))

        # 标题
        title = ref.get('title', '')
        if title:
            parts.append(f'"{title}."')

        # 期刊/来源
        if ref.get('publication_type') == 'journal':
            journal = ref.get('journal_name', '')
            if journal:
                container = self._italicize(journal)
                volume = ref.get('volume', '')
                issue = ref.get('issue', '')
                pages = ref.get('pages', '')

                if volume:
                    container += f" {volume}"
                if issue:
                    container += f", no. {issue}"
                if pages:
                    container += f" ({pages})"
                parts.append(container)

        # DOI/URL
        doi = ref.get('doi', '')
        if doi:
            parts.append(f"https://doi.org/{doi}")

        return '. '.join(parts) + '.'

    def _in_text_chicago(self, ref: Dict[str, Any]) -> str:
        """Chicago 文中引用"""
        authors = ref.get('authors', [])
        year = ref.get('publication_year', '')

        if not authors:
            return f"({year})"

        author = authors[0].split()[-1]
        return f"({author} {year})"

    def _format_author_chicago(self, author: str) -> str:
        """格式化 Chicago 作者名"""
        parts = author.split()
        if len(parts) >= 2:
            last_name = parts[-1]
            first_names = ' '.join(parts[:-1])
            return f"{last_name}, {first_names}"
        return author

    # ============== GB/T 7714 格式（中国国家标准） ==============

    def _format_gb7714(self, ref: Dict[str, Any]) -> str:
        """GB/T 7714-2015 格式"""
        parts = []

        # 作者
        authors = ref.get('authors', [])
        if authors:
            author_str = self._format_authors_gb7714(authors)
            parts.append(author_str)

        # 标题
        title = ref.get('title', '')
        if title:
            parts.append(title)

        # 根据类型格式化
        pub_type = ref.get('publication_type', 'journal')

        if pub_type == 'journal':
            # 期刊论文: 作者. 题名[J]. 刊名, 年, 卷(期): 页码.
            journal = ref.get('journal_name', '')
            if journal:
                journal_part = f"{journal}[J]"
                year = ref.get('publication_year', '')
                volume = ref.get('volume', '')
                issue = ref.get('issue', '')
                pages = ref.get('pages', '')

                if year:
                    journal_part += f", {year}"
                if volume:
                    journal_part += f", {volume}"
                if issue:
                    journal_part += f"({issue})"
                if pages:
                    journal_part += f": {pages}"
                parts.append(journal_part)

        elif pub_type == 'conference':
            # 会议论文: 作者. 题名[C]//会议名称. 出版地: 出版者, 年: 页码.
            conf_name = ref.get('journal_name', '')
            if conf_name:
                parts.append(f"{conf_name}[C]")
            year = ref.get('publication_year', '')
            pages = ref.get('pages', '')
            if year:
                parts.append(f"{year}")
            if pages:
                parts.append(f": {pages}")

        elif pub_type == 'book':
            # 专著: 作者. 书名[M]. 出版地: 出版者, 年.
            publisher = ref.get('publisher', '')
            if publisher:
                parts.append(f"{publisher}[M]")
            year = ref.get('publication_year', '')
            if year:
                parts.append(f"{year}")

        elif pub_type == 'thesis':
            # 学位论文: 作者. 题名[D]. 保存地: 保存单位, 年.
            parts.append("[D]")
            year = ref.get('publication_year', '')
            if year:
                parts.append(f"{year}")

        # DOI
        doi = ref.get('doi', '')
        if doi:
            parts.append(f"DOI: {doi}")

        return '. '.join(parts) + '.'

    def _in_text_gb7714(self, ref: Dict[str, Any]) -> str:
        """GB/T 7714 文中引用（顺序编码制）"""
        # 在顺序编码制中，文中使用 [1], [2] 等上标
        # 这里返回作者-年份格式作为备选
        authors = ref.get('authors', [])
        year = ref.get('publication_year', '')

        if not authors:
            return f"({year})"

        if len(authors) <= 3:
            author_names = ''.join([a.split()[-1] for a in authors])
            return f"({author_names}等, {year})"
        else:
            author = authors[0].split()[-1]
            return f"({author}等, {year})"

    def _format_authors_gb7714(self, authors: List[str]) -> str:
        """格式化 GB/T 7714 作者名"""
        if len(authors) <= 3:
            formatted = []
            for author in authors:
                formatted.append(self._format_author_gb7714(author))
            return ', '.join(formatted)
        else:
            # 超过3个作者只列前3个
            formatted = [self._format_author_gb7714(a) for a in authors[:3]]
            return ', '.join(formatted) + ', 等'

    def _format_author_gb7714(self, author: str) -> str:
        """格式化单个作者名为 GB/T 7714 格式"""
        parts = author.split()
        if len(parts) >= 2:
            # 姓在前，名缩写在后
            last_name = parts[-1]
            first_initials = ''.join([p[0] for p in parts[:-1]])
            return f"{last_name} {first_initials}"
        return author

    # ============== IEEE 格式 ==============

    def _format_ieee(self, ref: Dict[str, Any]) -> str:
        """IEEE 格式"""
        parts = []

        # 作者
        authors = ref.get('authors', [])
        if authors:
            if len(authors) <= 6:
                author_strs = [self._format_author_ieee(a) for a in authors]
                parts.append(', '.join(author_strs))
            else:
                author_strs = [self._format_author_ieee(a) for a in authors[:6]]
                parts.append(', '.join(author_strs) + ', et al.')

        # 标题
        title = ref.get('title', '')
        if title:
            parts.append(f'"{title},"')

        # 期刊/来源
        if ref.get('publication_type') == 'journal':
            journal = ref.get('journal_name', '')
            if journal:
                container = self._italicize(journal)
                volume = ref.get('volume', '')
                issue = ref.get('issue', '')
                pages = ref.get('pages', '')
                year = ref.get('publication_year', '')

                if volume:
                    container += f", vol. {volume}"
                if issue:
                    container += f", no. {issue}"
                if pages:
                    container += f", pp. {pages}"
                if year:
                    container += f", {year}"
                parts.append(container)

        # DOI
        doi = ref.get('doi', '')
        if doi:
            parts.append(f"doi: {doi}")

        return ', '.join(parts) + '.'

    def _in_text_ieee(self, ref: Dict[str, Any]) -> str:
        """IEEE 文中引用（使用编号）"""
        # IEEE 使用 [1], [2], [3] 等编号
        # 这里返回占位符
        return "[X]"

    def _format_author_ieee(self, author: str) -> str:
        """格式化 IEEE 作者名"""
        parts = author.split()
        if len(parts) >= 2:
            last_name = parts[-1]
            initials = ''.join([p[0] + '.' for p in parts[:-1]])
            return f"{initials} {last_name}"
        return author

    # ============== Harvard 格式 ==============

    def _format_harvard(self, ref: Dict[str, Any]) -> str:
        """Harvard 格式"""
        parts = []

        # 作者
        authors = ref.get('authors', [])
        if authors:
            if len(authors) == 1:
                parts.append(self._format_author_harvard(authors[0]))
            elif len(authors) <= 3:
                author_strs = [self._format_author_harvard(a) for a in authors[:-1]]
                parts.append(', '.join(author_strs) + f' and {self._format_author_harvard(authors[-1])}')
            else:
                parts.append(self._format_author_harvard(authors[0]) + ' et al.')

        # 年份
        year = ref.get('publication_year')
        if year:
            parts.append(f"({year})")

        # 标题
        title = ref.get('title', '')
        if title:
            if ref.get('publication_type') == 'journal':
                parts.append(f"'{title}'")
            else:
                parts.append(f"{title}")

        # 期刊
        if ref.get('publication_type') == 'journal':
            journal = ref.get('journal_name', '')
            if journal:
                container = self._italicize(journal)
                volume = ref.get('volume', '')
                issue = ref.get('issue', '')
                pages = ref.get('pages', '')

                if volume:
                    container += f", {volume}"
                if issue:
                    container += f"({issue})"
                if pages:
                    container += f", pp. {pages}"
                parts.append(container)

        # DOI/URL
        doi = ref.get('doi', '')
        url = ref.get('url', '')
        if doi:
            parts.append(f"doi: {doi}")
        elif url:
            parts.append(f"Available at: {url}")

        return '. '.join(parts)

    def _in_text_harvard(self, ref: Dict[str, Any]) -> str:
        """Harvard 文中引用"""
        authors = ref.get('authors', [])
        year = ref.get('publication_year', '')

        if not authors:
            return f"({year})"

        if len(authors) <= 2:
            author_names = ' and '.join([a.split()[-1] for a in authors])
        else:
            author_names = authors[0].split()[-1] + ' et al.'

        return f"({author_names}, {year})"

    def _format_author_harvard(self, author: str) -> str:
        """格式化 Harvard 作者名"""
        parts = author.split()
        if len(parts) >= 2:
            last_name = parts[-1]
            initials = ''.join([p[0] + '.' for p in parts[:-1]])
            return f"{last_name}, {initials}"
        return author

    # ============== Vancouver 格式 ==============

    def _format_vancouver(self, ref: Dict[str, Any]) -> str:
        """Vancouver 格式"""
        parts = []

        # 作者（最多6个）
        authors = ref.get('authors', [])
        if authors:
            if len(authors) <= 6:
                author_strs = [self._format_author_vancouver(a) for a in authors]
                parts.append(', '.join(author_strs))
            else:
                author_strs = [self._format_author_vancouver(a) for a in authors[:6]]
                parts.append(', '.join(author_strs) + ', et al.')

        # 标题
        title = ref.get('title', '')
        if title:
            parts.append(title)

        # 期刊
        if ref.get('publication_type') == 'journal':
            journal = ref.get('journal_name', '')
            if journal:
                container = self._italicize(journal)
                year = ref.get('publication_year', '')
                volume = ref.get('volume', '')
                issue = ref.get('issue', '')
                pages = ref.get('pages', '')

                if year:
                    container += f". {year}"
                if volume:
                    container += f";{volume}"
                if issue:
                    container += f"({issue})"
                if pages:
                    container += f":{pages}"
                parts.append(container)

        return '. '.join(parts) + '.'

    def _in_text_vancouver(self, ref: Dict[str, Any]) -> str:
        """Vancouver 文中引用（使用编号）"""
        return "[X]"

    def _format_author_vancouver(self, author: str) -> str:
        """格式化 Vancouver 作者名"""
        parts = author.split()
        if len(parts) >= 2:
            last_name = parts[-1]
            initials = ''.join([p[0] for p in parts[:-1]])
            return f"{last_name} {initials}"
        return author

    # ============== 辅助方法 ==============

    def _italicize(self, text: str) -> str:
        """
        将文本标记为斜体
        在实际输出中可以使用 Markdown 或 HTML 格式
        """
        # 这里使用简单的标记，前端可以解析为斜体
        return f"*{text}*"
