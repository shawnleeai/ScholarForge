"""
文献格式解析器
支持多种文献管理软件的导入导出格式
"""

import re
import json
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime


def parse_bibtex(content: str) -> List[Dict[str, Any]]:
    """
    解析 BibTeX 格式

    示例格式：
    @article{key,
        title = {Title},
        author = {Author1 and Author2},
        year = {2023},
        journal = {Journal Name}
    }
    """
    references = []

    # 匹配每个条目
    entry_pattern = r'@(\w+)\s*\{\s*([^,]*)\s*,\s*([^@]*)\}'
    entries = re.findall(entry_pattern, content, re.DOTALL)

    for entry_type, cite_key, fields_text in entries:
        ref = {
            'publication_type': _map_bibtex_type(entry_type),
            'source_id': cite_key.strip()
        }

        # 解析字段
        field_pattern = r'(\w+)\s*=\s*\{([^}]*)\}'
        fields = re.findall(field_pattern, fields_text)

        for field_name, field_value in fields:
            field_name = field_name.lower().strip()
            field_value = field_value.strip()

            if field_name == 'title':
                ref['title'] = _clean_latex(field_value)
            elif field_name == 'author':
                ref['authors'] = _parse_authors(field_value)
            elif field_name == 'year':
                ref['publication_year'] = int(field_value) if field_value.isdigit() else None
            elif field_name == 'journal':
                ref['journal_name'] = _clean_latex(field_value)
            elif field_name == 'booktitle':
                ref['journal_name'] = _clean_latex(field_value)
                ref['publication_type'] = 'conference'
            elif field_name == 'volume':
                ref['volume'] = field_value
            elif field_name == 'number':
                ref['issue'] = field_value
            elif field_name == 'pages':
                ref['pages'] = field_value
            elif field_name == 'doi':
                ref['doi'] = field_value
            elif field_name == 'url':
                ref['url'] = field_value
            elif field_name == 'abstract':
                ref['abstract'] = _clean_latex(field_value)
            elif field_name == 'keywords':
                ref['keywords'] = [k.strip() for k in field_value.split(',')]
            elif field_name == 'publisher':
                ref['publisher'] = field_value

        if 'title' in ref:
            references.append(ref)

    return references


def parse_ris(content: str) -> List[Dict[str, Any]]:
    """
    解析 RIS 格式

    示例格式：
    TY  - JOUR
    TI  - Title
    AU  - Author1
    AU  - Author2
    PY  - 2023
    ER  -
    """
    references = []
    current_ref = {}

    lines = content.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # 匹配 RIS 标签
        match = re.match(r'^([A-Z][A-Z0-9])\s*-\s*(.*)$', line)
        if not match:
            continue

        tag, value = match.groups()
        value = value.strip()

        if tag == 'TY':  # Type
            if current_ref and 'title' in current_ref:
                references.append(current_ref)
            current_ref = {'publication_type': _map_ris_type(value)}
        elif tag == 'TI':  # Title
            current_ref['title'] = value
        elif tag == 'T1':  # Primary Title (alternative)
            if 'title' not in current_ref:
                current_ref['title'] = value
        elif tag == 'AU':  # Author
            if 'authors' not in current_ref:
                current_ref['authors'] = []
            current_ref['authors'].append(value)
        elif tag == 'A1':  # Author (alternative)
            if 'authors' not in current_ref:
                current_ref['authors'] = []
            if value not in current_ref['authors']:
                current_ref['authors'].append(value)
        elif tag == 'PY':  # Year
            year_match = re.search(r'(\d{4})', value)
            if year_match:
                current_ref['publication_year'] = int(year_match.group(1))
        elif tag == 'Y1':  # Year (alternative)
            if 'publication_year' not in current_ref:
                year_match = re.search(r'(\d{4})', value)
                if year_match:
                    current_ref['publication_year'] = int(year_match.group(1))
        elif tag == 'JO':  # Journal
            current_ref['journal_name'] = value
        elif tag == 'JA':  # Journal (abbreviated)
            if 'journal_name' not in current_ref:
                current_ref['journal_name'] = value
        elif tag == 'VL':  # Volume
            current_ref['volume'] = value
        elif tag == 'IS':  # Issue
            current_ref['issue'] = value
        elif tag == 'SP':  # Start Page
            current_ref['pages'] = value
        elif tag == 'EP':  # End Page
            if 'pages' in current_ref:
                current_ref['pages'] += f'-{value}'
            else:
                current_ref['pages'] = value
        elif tag == 'DO':  # DOI
            current_ref['doi'] = value
        elif tag == 'UR':  # URL
            current_ref['url'] = value
        elif tag == 'AB':  # Abstract
            current_ref['abstract'] = value
        elif tag == 'KW':  # Keywords
            if 'keywords' not in current_ref:
                current_ref['keywords'] = []
            current_ref['keywords'].append(value)
        elif tag == 'PB':  # Publisher
            current_ref['publisher'] = value
        elif tag == 'SN':  # ISBN/ISSN
            current_ref['isbn'] = value
        elif tag == 'ER':  # End of Reference
            if current_ref and 'title' in current_ref:
                references.append(current_ref)
            current_ref = {}

    # 添加最后一个参考文献
    if current_ref and 'title' in current_ref:
        references.append(current_ref)

    return references


def parse_endnote(content: str) -> List[Dict[str, Any]]:
    """
    解析 EndNote 导出的文本格式
    """
    references = []
    current_ref = {}
    current_field = None

    lines = content.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            if current_ref and 'title' in current_ref:
                references.append(current_ref)
                current_ref = {}
            continue

        # 检查是否是新字段
        field_match = re.match(r'^([A-Z][a-z]+):\s*(.*)$', line)
        if field_match:
            field_name, value = field_match.groups()
            current_field = field_name.lower()

            if current_field == 'title':
                current_ref['title'] = value
            elif current_field == 'author':
                current_ref['authors'] = _parse_authors(value)
            elif current_field == 'year':
                current_ref['publication_year'] = int(value) if value.isdigit() else None
            elif current_field == 'journal':
                current_ref['journal_name'] = value
            elif current_field == 'volume':
                current_ref['volume'] = value
            elif current_field == 'issue':
                current_ref['issue'] = value
            elif current_field == 'pages':
                current_ref['pages'] = value
            elif current_field == 'doi':
                current_ref['doi'] = value
            elif current_field == 'url':
                current_ref['url'] = value
            elif current_field == 'abstract':
                current_ref['abstract'] = value
            elif current_field == 'keywords':
                current_ref['keywords'] = [k.strip() for k in value.split(',')]
            elif current_field == 'publisher':
                current_ref['publisher'] = value
            elif current_field == 'reference type':
                current_ref['publication_type'] = _map_endnote_type(value)
        elif current_field and line:
            # 继续上一行
            if current_field == 'title':
                current_ref['title'] += ' ' + line
            elif current_field == 'abstract':
                current_ref['abstract'] += ' ' + line

    if current_ref and 'title' in current_ref:
        references.append(current_ref)

    return references


def parse_noteexpress(content: str) -> List[Dict[str, Any]]:
    """
    解析 NoteExpress 格式
    类似 RIS 格式但有不同标签
    """
    # NoteExpress 通常导出为 RIS 或自定义格式
    # 这里处理其特定格式
    if '{\n' in content and 'Title:' in content:
        return _parse_noteexpress_custom(content)
    else:
        # 尝试用 RIS 解析
        return parse_ris(content)


def _parse_noteexpress_custom(content: str) -> List[Dict[str, Any]]:
    """解析 NoteExpress 自定义格式"""
    references = []
    current_ref = {}

    # 按条目分割
    entries = re.split(r'\n\s*\n', content)

    for entry in entries:
        lines = entry.strip().split('\n')
        current_ref = {}

        for line in lines:
            line = line.strip()
            if not line or not line.startswith('{'):
                continue

            # 解析键值对
            match = re.match(r'\{(\w+):\s*(.*?)\}', line)
            if match:
                key, value = match.groups()

                if key == 'Title':
                    current_ref['title'] = value
                elif key == 'Author':
                    current_ref['authors'] = _parse_authors(value)
                elif key == 'Year':
                    current_ref['publication_year'] = int(value) if value.isdigit() else None
                elif key == 'Journal':
                    current_ref['journal_name'] = value
                elif key == 'Volume':
                    current_ref['volume'] = value
                elif key == 'Issue':
                    current_ref['issue'] = value
                elif key == 'Pages':
                    current_ref['pages'] = value
                elif key == 'DOI':
                    current_ref['doi'] = value
                elif key == 'Abstract':
                    current_ref['abstract'] = value
                elif key == 'Keywords':
                    current_ref['keywords'] = [k.strip() for k in value.split(';')]

        if 'title' in current_ref:
            references.append(current_ref)

    return references


# ============== 导出函数 ==============

def export_bibtex(references: List[Dict[str, Any]], options: Dict[str, Any] = None) -> str:
    """导出为 BibTeX 格式"""
    lines = []

    for i, ref in enumerate(references):
        # 生成引用键
        cite_key = _generate_cite_key(ref, i)
        entry_type = _reverse_map_bibtex_type(ref.get('publication_type', 'journal'))

        lines.append(f"@{entry_type}{{{cite_key},}")

        if ref.get('title'):
            lines.append(f"    title = {{{ref['title']}}},")
        if ref.get('authors'):
            authors = ' and '.join(ref['authors'])
            lines.append(f"    author = {{{authors}}},")
        if ref.get('publication_year'):
            lines.append(f"    year = {{{ref['publication_year']}}},")
        if ref.get('journal_name'):
            if ref.get('publication_type') == 'conference':
                lines.append(f"    booktitle = {{{ref['journal_name']}}},")
            else:
                lines.append(f"    journal = {{{ref['journal_name']}}},")
        if ref.get('volume'):
            lines.append(f"    volume = {{{ref['volume']}}},")
        if ref.get('issue'):
            lines.append(f"    number = {{{ref['issue']}}},")
        if ref.get('pages'):
            lines.append(f"    pages = {{{ref['pages']}}},")
        if ref.get('doi'):
            lines.append(f"    doi = {{{ref['doi']}}},")
        if ref.get('url'):
            lines.append(f"    url = {{{ref['url']}}},")
        if ref.get('abstract'):
            lines.append(f"    abstract = {{{ref['abstract']}}},")
        if ref.get('publisher'):
            lines.append(f"    publisher = {{{ref['publisher']}}},")
        if ref.get('keywords'):
            keywords = ', '.join(ref['keywords'])
            lines.append(f"    keywords = {{{keywords}}},")

        lines.append("}")
        lines.append("")

    return '\n'.join(lines)


def export_ris(references: List[Dict[str, Any]], options: Dict[str, Any] = None) -> str:
    """导出为 RIS 格式"""
    lines = []

    for ref in references:
        # 类型
        ris_type = _reverse_map_ris_type(ref.get('publication_type', 'journal'))
        lines.append(f"TY  - {ris_type}")

        if ref.get('title'):
            lines.append(f"TI  - {ref['title']}")
        if ref.get('authors'):
            for author in ref['authors']:
                lines.append(f"AU  - {author}")
        if ref.get('publication_year'):
            lines.append(f"PY  - {ref['publication_year']}//")
        if ref.get('journal_name'):
            lines.append(f"JO  - {ref['journal_name']}")
        if ref.get('volume'):
            lines.append(f"VL  - {ref['volume']}")
        if ref.get('issue'):
            lines.append(f"IS  - {ref['issue']}")
        if ref.get('pages'):
            pages = ref['pages'].split('-')
            lines.append(f"SP  - {pages[0]}")
            if len(pages) > 1:
                lines.append(f"EP  - {pages[1]}")
        if ref.get('doi'):
            lines.append(f"DO  - {ref['doi']}")
        if ref.get('url'):
            lines.append(f"UR  - {ref['url']}")
        if ref.get('abstract'):
            lines.append(f"AB  - {ref['abstract']}")
        if ref.get('publisher'):
            lines.append(f"PB  - {ref['publisher']}")
        if ref.get('keywords'):
            for keyword in ref['keywords']:
                lines.append(f"KW  - {keyword}")

        lines.append("ER  - ")
        lines.append("")

    return '\n'.join(lines)


def export_csv(references: List[Dict[str, Any]], options: Dict[str, Any] = None) -> str:
    """导出为 CSV 格式"""
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    headers = [
        'Title', 'Authors', 'Year', 'Journal', 'Volume', 'Issue',
        'Pages', 'DOI', 'URL', 'Abstract', 'Keywords', 'Publisher', 'Type'
    ]
    writer.writerow(headers)

    # 写入数据
    for ref in references:
        row = [
            ref.get('title', ''),
            '; '.join(ref.get('authors', [])),
            ref.get('publication_year', ''),
            ref.get('journal_name', ''),
            ref.get('volume', ''),
            ref.get('issue', ''),
            ref.get('pages', ''),
            ref.get('doi', ''),
            ref.get('url', ''),
            ref.get('abstract', ''),
            '; '.join(ref.get('keywords', [])),
            ref.get('publisher', ''),
            ref.get('publication_type', '')
        ]
        writer.writerow(row)

    return output.getvalue()


def export_json(references: List[Dict[str, Any]], options: Dict[str, Any] = None) -> str:
    """导出为 JSON 格式"""
    return json.dumps(references, ensure_ascii=False, indent=2, default=str)


# ============== 辅助函数 ==============

def _map_bibtex_type(bibtex_type: str) -> str:
    """映射 BibTeX 类型到内部类型"""
    type_map = {
        'article': 'journal',
        'inproceedings': 'conference',
        'conference': 'conference',
        'book': 'book',
        'incollection': 'book',
        'phdthesis': 'thesis',
        'mastersthesis': 'thesis',
        'techreport': 'report',
        'misc': 'online',
        'unpublished': 'other',
    }
    return type_map.get(bibtex_type.lower(), 'other')


def _reverse_map_bibtex_type(internal_type: str) -> str:
    """映射内部类型到 BibTeX 类型"""
    type_map = {
        'journal': 'article',
        'conference': 'inproceedings',
        'book': 'book',
        'thesis': 'phdthesis',
        'report': 'techreport',
        'online': 'misc',
        'other': 'misc',
    }
    return type_map.get(internal_type, 'article')


def _map_ris_type(ris_type: str) -> str:
    """映射 RIS 类型到内部类型"""
    type_map = {
        'JOUR': 'journal',
        'CONF': 'conference',
        'BOOK': 'book',
        'THES': 'thesis',
        'RPRT': 'report',
        'ELEC': 'online',
        'CHAP': 'book',
        'PAT': 'other',
        'STD': 'other',
    }
    return type_map.get(ris_type.upper(), 'other')


def _reverse_map_ris_type(internal_type: str) -> str:
    """映射内部类型到 RIS 类型"""
    type_map = {
        'journal': 'JOUR',
        'conference': 'CONF',
        'book': 'BOOK',
        'thesis': 'THES',
        'report': 'RPRT',
        'online': 'ELEC',
        'other': 'MISC',
    }
    return type_map.get(internal_type, 'JOUR')


def _map_endnote_type(endnote_type: str) -> str:
    """映射 EndNote 类型到内部类型"""
    type_map = {
        'journal article': 'journal',
        'conference paper': 'conference',
        'book': 'book',
        'thesis': 'thesis',
        'report': 'report',
        'web page': 'online',
        'electronic article': 'online',
    }
    return type_map.get(endnote_type.lower(), 'other')


def _parse_authors(author_str: str) -> List[str]:
    """解析作者字符串为列表"""
    # 支持的分隔符: and, &, comma
    authors = re.split(r'\s+and\s+|\s*&\s*|\s*;\s*', author_str)
    return [a.strip() for a in authors if a.strip()]


def _clean_latex(text: str) -> str:
    """清理 LaTeX 特殊字符"""
    # 替换常见的 LaTeX 命令
    replacements = [
        (r'\\&', '&'),
        (r'\\%', '%'),
        (r'\\$', '$'),
        (r'\\#', '#'),
        (r'\\_', '_'),
        (r'\\text', ''),
        (r'\{', ''),
        (r'\}', ''),
    ]

    result = text
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result)

    return result.strip()


def _generate_cite_key(ref: Dict[str, Any], index: int) -> str:
    """生成引用键"""
    # 尝试使用第一作者姓氏+年份
    authors = ref.get('authors', [])
    year = ref.get('publication_year', '')

    if authors:
        first_author = authors[0].split()[-1]  # 取姓氏
        cite_key = f"{first_author}{year}"
    else:
        cite_key = f"ref{index}"

    # 清理特殊字符
    cite_key = re.sub(r'[^a-zA-Z0-9]', '', cite_key)

    return cite_key.lower()
