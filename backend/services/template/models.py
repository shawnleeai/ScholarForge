"""
模板数据模型
定义论文模板的完整数据结构
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TemplateType(str, Enum):
    """模板类型"""
    THESIS = "thesis"           # 学位论文
    JOURNAL = "journal"         # 期刊论文
    CONFERENCE = "conference"   # 会议论文
    REPORT = "report"           # 研究报告
    PROPOSAL = "proposal"       # 开题报告
    REVIEW = "review"           # 综述文章
    BOOK = "book"               # 书籍章节


class TemplateStatus(str, Enum):
    """模板状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    PRIVATE = "private"


class FieldType(str, Enum):
    """字段类型"""
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    BOOLEAN = "boolean"
    RICH_TEXT = "rich_text"


@dataclass
class TemplateField:
    """模板字段定义"""
    id: str
    name: str
    label: str
    type: FieldType
    required: bool = True
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None
    options: List[str] = field(default_factory=list)
    validation: Dict[str, Any] = field(default_factory=dict)
    ai_prompt: Optional[str] = None  # AI填充时的提示词


@dataclass
class TemplateSection:
    """模板章节"""
    id: str
    title: str
    order_index: int
    required: bool = True
    placeholder: Optional[str] = None
    description: Optional[str] = None
    word_count_hint: Optional[int] = None
    fields: List[TemplateField] = field(default_factory=list)
    ai_guidance: Optional[str] = None  # AI写作指导
    example_content: Optional[str] = None  # 示例内容


@dataclass
class TemplateFormat:
    """模板格式设置"""
    font_family: str = "Times New Roman"
    font_size: float = 12.0
    line_height: float = 1.5
    margins: Dict[str, float] = field(default_factory=lambda: {
        "top": 2.5,
        "bottom": 2.5,
        "left": 2.5,
        "right": 2.5
    })
    heading_styles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    page_size: str = "A4"
    column_count: int = 1


@dataclass
class TemplateTag:
    """模板标签"""
    id: str
    name: str
    category: str  # institution/field/language/etc
    count: int = 0


@dataclass
class TemplateStats:
    """模板统计"""
    download_count: int = 0
    usage_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    view_count: int = 0
    favorite_count: int = 0


@dataclass
class PaperTemplate:
    """论文模板"""
    id: str
    name: str
    description: str
    type: TemplateType
    status: TemplateStatus = TemplateStatus.PUBLISHED

    # 来源信息
    institution: Optional[str] = None
    author: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None

    # 内容
    thumbnail: Optional[str] = None
    preview_images: List[str] = field(default_factory=list)
    sections: List[TemplateSection] = field(default_factory=list)
    format: TemplateFormat = field(default_factory=TemplateFormat)
    tags: List[str] = field(default_factory=list)

    # 分类
    language: str = "zh"  # zh/en/etc
    discipline: Optional[str] = None  # 学科分类
    difficulty: str = "intermediate"  # beginner/intermediate/advanced

    # 统计
    stats: TemplateStats = field(default_factory=TemplateStats)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    version: str = "1.0.0"

    # 搜索优化
    keywords: List[str] = field(default_factory=list)
    searchable_content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "status": self.status.value,
            "institution": self.institution,
            "author": self.author,
            "source_url": self.source_url,
            "license": self.license,
            "thumbnail": self.thumbnail,
            "preview_images": self.preview_images,
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "order_index": s.order_index,
                    "required": s.required,
                    "placeholder": s.placeholder,
                    "description": s.description,
                    "word_count_hint": s.word_count_hint,
                    "fields": [
                        {
                            "id": f.id,
                            "name": f.name,
                            "label": f.label,
                            "type": f.type.value,
                            "required": f.required,
                            "placeholder": f.placeholder,
                            "default_value": f.default_value,
                            "options": f.options,
                            "ai_prompt": f.ai_prompt,
                        }
                        for f in s.fields
                    ],
                    "ai_guidance": s.ai_guidance,
                    "example_content": s.example_content,
                }
                for s in self.sections
            ],
            "format": {
                "font_family": self.format.font_family,
                "font_size": self.format.font_size,
                "line_height": self.format.line_height,
                "margins": self.format.margins,
                "heading_styles": self.format.heading_styles,
                "page_size": self.format.page_size,
                "column_count": self.format.column_count,
            },
            "tags": self.tags,
            "language": self.language,
            "discipline": self.discipline,
            "difficulty": self.difficulty,
            "stats": {
                "download_count": self.stats.download_count,
                "usage_count": self.stats.usage_count,
                "rating": self.stats.rating,
                "rating_count": self.stats.rating_count,
                "view_count": self.stats.view_count,
                "favorite_count": self.stats.favorite_count,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "version": self.version,
            "keywords": self.keywords,
        }

    def get_required_sections(self) -> List[TemplateSection]:
        """获取必需章节"""
        return [s for s in self.sections if s.required]

    def get_optional_sections(self) -> List[TemplateSection]:
        """获取可选章节"""
        return [s for s in self.sections if not s.required]

    def get_total_word_hint(self) -> int:
        """获取总字数建议"""
        return sum(
            s.word_count_hint or 0
            for s in self.sections
            if s.word_count_hint
        )

    def update_searchable_content(self):
        """更新可搜索内容"""
        parts = [
            self.name,
            self.description,
            self.institution or "",
            self.author or "",
            " ".join(self.tags),
            " ".join(self.keywords),
            " ".join(s.title for s in self.sections),
        ]
        self.searchable_content = " ".join(p for p in parts if p).lower()


@dataclass
class TemplateUsage:
    """模板使用记录"""
    id: str
    template_id: str
    user_id: str
    paper_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    filled_sections: Dict[str, str] = field(default_factory=dict)
    ai_assisted: bool = False


@dataclass
class TemplateRating:
    """模板评分"""
    id: str
    template_id: str
    user_id: str
    rating: int  # 1-5
    comment: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
