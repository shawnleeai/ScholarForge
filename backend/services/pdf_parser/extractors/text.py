"""
PDF 文本提取器
使用 PyMuPDF (fitz) 进行高效的PDF文本提取
"""

import re
import fitz  # PyMuPDF
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TextExtractor:
    """PDF文本提取器"""

    # 学术论文章节标题模式（中英文）
    SECTION_PATTERNS = [
        # 中文模式
        (r'^\s*摘\s*要', 'abstract', 1),
        (r'^\s*Abstract', 'abstract', 1),
        (r'^\s*1[.\s]+引言|Introduction', 'introduction', 1),
        (r'^\s*2[.\s]+相关工作|Related\s+Work|Literature\s+Review', 'related_work', 1),
        (r'^\s*3[.\s]+研究方法?|Methodology|Methods', 'methodology', 1),
        (r'^\s*4[.\s]+实验|Experiments?', 'experiments', 1),
        (r'^\s*5[.\s]+结果|Results?', 'results', 1),
        (r'^\s*6[.\s]+讨论|Discussion', 'discussion', 1),
        (r'^\s*7[.\s]+结论|Conclusion', 'conclusion', 1),
        (r'^\s*致谢?|Acknowledgments?', 'acknowledgments', 1),
        (r'^\s*参考|References?|Bibliography', 'references', 1),
        # 英文模式
        (r'^\s*I\.\s+', 'section', 1),
        (r'^\s*II\.\s+', 'section', 1),
        (r'^\s*III\.\s+', 'section', 1),
        (r'^\s*IV\.\s+', 'section', 1),
        (r'^\s*V\.\s+', 'section', 1),
    ]

    def __init__(self):
        self.section_patterns = [
            (re.compile(pattern, re.IGNORECASE), section_type, level)
            for pattern, section_type, level in self.SECTION_PATTERNS
        ]

    async def extract(self, pdf_path: str) -> Dict:
        """
        提取PDF文本内容

        Args:
            pdf_path: PDF文件路径

        Returns:
            Dict 包含完整文本、章节结构和页数
        """
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"无法打开PDF文件: {e}")
            raise ValueError(f"无法打开PDF文件: {e}")

        full_text_parts = []
        sections = []
        current_section = {"title": "开头", "content": [], "level": 1, "page_start": 1}

        for page_num, page in enumerate(doc, 1):
            # 提取页面文本
            text = page.get_text("text")
            if not text.strip():
                continue

            full_text_parts.append(f"\n--- Page {page_num} ---\n{text}")

            # 按行处理，识别章节
            lines = text.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue

                # 检测章节标题
                section_info = self._detect_section(line_stripped)
                if section_info:
                    # 保存当前章节
                    if current_section["content"]:
                        current_section["content"] = '\n'.join(current_section["content"])
                        current_section["page_end"] = page_num - 1
                        sections.append(current_section)

                    # 开始新章节
                    current_section = {
                        "title": line_stripped,
                        "content": [line_stripped],
                        "level": section_info["level"],
                        "page_start": page_num,
                        "section_type": section_info["type"]
                    }
                else:
                    current_section["content"].append(line)

        # 保存最后一个章节
        if current_section["content"]:
            current_section["content"] = '\n'.join(current_section["content"])
            current_section["page_end"] = len(doc)
            sections.append(current_section)

        page_count = len(doc)
        doc.close()

        return {
            "full_text": '\n'.join(full_text_parts),
            "sections": sections,
            "page_count": page_count,
        }

    def _detect_section(self, line: str) -> Optional[Dict]:
        """
        检测章节标题

        Returns:
            Dict with 'type' and 'level' or None
        """
        for pattern, section_type, level in self.section_patterns:
            if pattern.match(line):
                return {"type": section_type, "level": level}
        return None

    def extract_abstract(self, text: str) -> Optional[str]:
        """提取摘要部分"""
        patterns = [
            r'摘\s*要[：:]\s*(.+?)(?=\n\s*\n|关键词|1\.|引言)',
            r'Abstract[：:]?\s*(.+?)(?=\n\s*\n|Keywords|1\.|Introduction)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                # 清理多余的空白
                abstract = re.sub(r'\s+', ' ', abstract)
                return abstract
        return None

    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        patterns = [
            r'关键词[：:]\s*(.+?)(?=\n|$)',
            r'Keywords[：:]\s*(.+?)(?=\n|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                keywords_str = match.group(1)
                # 支持中英文分隔符
                keywords = re.split(r'[,;，；]', keywords_str)
                return [k.strip() for k in keywords if k.strip()]
        return []

    def clean_text(self, text: str) -> str:
        """清理文本中的噪声"""
        # 移除页眉页脚常见的页码
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        # 合并多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 移除孤立的单字符行（可能是页码或装饰）
        text = re.sub(r'\n\s*[^\w\s]{1,2}\s*\n', '\n', text)
        return text.strip()
