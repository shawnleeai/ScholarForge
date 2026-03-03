"""
格式引擎核心实现
自动排版和格式转换
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FormatConfig:
    """格式配置"""
    # 页面设置
    page_width: float = 210  # mm (A4)
    page_height: float = 297  # mm (A4)
    margin_top: float = 25.4  # mm
    margin_bottom: float = 25.4  # mm
    margin_left: float = 31.7  # mm
    margin_right: float = 31.7  # mm

    # 字体设置
    font_family: str = "SimSun"  # 宋体
    font_size: float = 12  # 小四
    line_spacing: float = 1.5  # 1.5倍行距

    # 标题格式
    heading1_font: str = "SimHei"
    heading1_size: float = 16  # 三号
    heading2_font: str = "SimHei"
    heading2_size: float = 14  # 四号
    heading3_font: str = "SimHei"
    heading3_size: float = 12  # 小四

    # 段落设置
    paragraph_indent: float = 24  # 首行缩进2字符 (pt)
    paragraph_spacing: float = 6  # 段后间距 (pt)


class FormatEngine:
    """格式引擎"""

    def __init__(self, config: FormatConfig):
        self.config = config

    def format_paper(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化整篇论文

        Args:
            content: 论文内容字典，包含各章节

        Returns:
            格式化后的内容
        """
        formatted = {
            "title": self._format_title(content.get("title", "")),
            "abstract": self._format_abstract(content.get("abstract", "")),
            "keywords": self._format_keywords(content.get("keywords", [])),
            "sections": [],
            "references": self._format_references(content.get("references", [])),
        }

        # 格式化各章节
        for section in content.get("sections", []):
            formatted_section = self._format_section(section)
            formatted["sections"].append(formatted_section)

        return formatted

    def _format_title(self, title: str) -> str:
        """格式化标题"""
        # 清理多余空格
        title = re.sub(r'\s+', ' ', title.strip())
        return title

    def _format_abstract(self, abstract: str) -> str:
        """格式化摘要"""
        if not abstract:
            return ""

        # 清理空格
        abstract = re.sub(r'\s+', ' ', abstract.strip())

        # 确保首行缩进
        return abstract

    def _format_keywords(self, keywords: List[str]) -> List[str]:
        """格式化关键词"""
        formatted = []
        for kw in keywords:
            kw = kw.strip()
            if kw:
                formatted.append(kw)
        return formatted

    def _format_section(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """格式化章节"""
        formatted = {
            "title": section.get("title", ""),
            "level": section.get("level", 1),
            "content": self._format_content(section.get("content", "")),
        }

        # 递归处理子章节
        if "subsections" in section:
            formatted["subsections"] = [
                self._format_section(sub) for sub in section["subsections"]
            ]

        return formatted

    def _format_content(self, content: str) -> str:
        """格式化正文内容"""
        if not content:
            return ""

        # 清理多余空白
        content = re.sub(r'[ \t]+', ' ', content)
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

        # 确保段落首行缩进
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if para:
                # 检查是否已经是标题
                if not para.startswith('#') and not para.startswith('第'):
                    formatted_paragraphs.append(para)
                else:
                    formatted_paragraphs.append(para)

        return '\n\n'.join(formatted_paragraphs)

    def _format_references(self, references: List[Dict]) -> List[Dict]:
        """格式化参考文献"""
        formatted = []
        for ref in references:
            formatted_ref = {
                "id": ref.get("id", ""),
                "content": self._format_reference_item(ref),
            }
            formatted.append(formatted_ref)
        return formatted

    def _format_reference_item(self, ref: Dict) -> str:
        """格式化单条参考文献（GB/T 7714格式）"""
        ref_type = ref.get("type", "journal")

        if ref_type == "journal":
            # 期刊论文: 作者. 题名[J]. 刊名, 年, 卷(期): 页码.
            authors = ref.get("authors", [])
            author_str = ", ".join(authors) if authors else "佚名"

            return f"{author_str}. {ref.get('title', '')}[J]. {ref.get('journal', '')}, {ref.get('year', '')}, {ref.get('volume', '')}({ref.get('issue', '')}): {ref.get('pages', '')}."

        elif ref_type == "book":
            # 图书: 作者. 书名[M]. 出版地: 出版社, 年.
            authors = ref.get("authors", [])
            author_str = ", ".join(authors) if authors else "佚名"

            return f"{author_str}. {ref.get('title', '')}[M]. {ref.get('publisher', '')}, {ref.get('year', '')}."

        else:
            return ref.get("content", "")

    def check_format(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查格式问题

        Returns:
            格式问题列表
        """
        issues = []

        # 检查标题
        title = content.get("title", "")
        if len(title) > 50:
            issues.append({
                "type": "title_length",
                "severity": "warning",
                "message": "标题过长，建议控制在50字以内",
                "position": "title"
            })

        # 检查摘要
        abstract = content.get("abstract", "")
        word_count = len(abstract)
        if word_count < 200:
            issues.append({
                "type": "abstract_length",
                "severity": "error",
                "message": f"摘要字数不足（当前{word_count}字），建议200-500字",
                "position": "abstract"
            })
        elif word_count > 800:
            issues.append({
                "type": "abstract_length",
                "severity": "warning",
                "message": f"摘要字数过多（当前{word_count}字），建议精简",
                "position": "abstract"
            })

        # 检查关键词
        keywords = content.get("keywords", [])
        if len(keywords) < 3:
            issues.append({
                "type": "keywords_count",
                "severity": "error",
                "message": "关键词数量不足，建议3-8个",
                "position": "keywords"
            })
        elif len(keywords) > 8:
            issues.append({
                "type": "keywords_count",
                "severity": "warning",
                "message": "关键词数量过多",
                "position": "keywords"
            })

        # 检查章节
        sections = content.get("sections", [])
        if not sections:
            issues.append({
                "type": "no_sections",
                "severity": "error",
                "message": "论文章节结构不完整",
                "position": "content"
            })

        # 检查参考文献
        references = content.get("references", [])
        if len(references) < 10:
            issues.append({
                "type": "references_count",
                "severity": "warning",
                "message": f"参考文献数量较少（当前{len(references)}篇），建议至少15篇",
                "position": "references"
            })

        return issues


class TemplateManager:
    """模板管理器"""

    # 预设模板
    TEMPLATES = {
        "cn_thesis": {
            "name": "中文论文标准格式",
            "description": "符合大多数国内高校要求的学位论文格式",
            "config": FormatConfig(
                font_family="SimSun",
                font_size=12,
                line_spacing=1.5,
                margin_top=25.4,
                margin_bottom=25.4,
                margin_left=31.7,
                margin_right=31.7,
            )
        },
        "cn_journal": {
            "name": "中文期刊论文格式",
            "description": "常见中文学术期刊格式",
            "config": FormatConfig(
                font_family="SimSun",
                font_size=10.5,
                line_spacing=1.0,
                margin_top=25.4,
                margin_bottom=25.4,
                margin_left=25.4,
                margin_right=25.4,
            )
        },
        "ieee": {
            "name": "IEEE 会议/期刊格式",
            "description": "IEEE 标准论文格式",
            "config": FormatConfig(
                font_family="Times New Roman",
                font_size=10,
                line_spacing=1.0,
                margin_top=19.0,
                margin_bottom=19.0,
                margin_left=19.0,
                margin_right=19.0,
            )
        },
    }

    @classmethod
    def get_template(cls, template_id: str) -> Optional[Dict]:
        """获取模板"""
        return cls.TEMPLATES.get(template_id)

    @classmethod
    def get_all_templates(cls) -> List[Dict]:
        """获取所有预设模板"""
        return [
            {"id": k, "name": v["name"], "description": v["description"]}
            for k, v in cls.TEMPLATES.items()
        ]

    @classmethod
    def get_format_config(cls, template_id: str) -> FormatConfig:
        """获取格式配置"""
        template = cls.TEMPLATES.get(template_id)
        if template:
            return template["config"]
        return FormatConfig()  # 返回默认配置
