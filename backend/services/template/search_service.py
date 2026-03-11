
模板搜索服务
提供高级模板搜索功能
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import re

from .models import PaperTemplate, TemplateType, TemplateStatus


@dataclass
class SearchFilter:
    """搜索过滤条件"""
    type: Optional[TemplateType] = None
    institution: Optional[str] = None
    discipline: Optional[str] = None
    language: Optional[str] = None
    difficulty: Optional[str] = None
    tags: List[str] = None
    min_rating: Optional[float] = None
    has_ai_support: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@dataclass
class SearchResult:
    """搜索结果"""
    template: PaperTemplate
    score: float
    matched_fields: List[str]


class TemplateSearchService:
    """
    模板搜索服务
    支持关键词搜索、筛选、排序
    """

    def __init__(self):
        # 模拟模板存储
        self._templates: Dict[str, PaperTemplate] = {}
        self._initialize_mock_data()

    def _initialize_mock_data(self):
        """初始化模拟数据"""
        from .models import TemplateSection, TemplateFormat, TemplateStats

        templates = [
            PaperTemplate(
                id="t1",
                name="浙江大学硕士学位论文模板",
                description="浙江大学硕士学位论文标准模板，符合学校格式要求，包含完整的章节结构和格式设置",
                type=TemplateType.THESIS,
                institution="浙江大学",
                author="ScholarForge",
                tags=["硕士", "浙大", "理工科", "中文"],
                discipline="engineering",
                language="zh",
                sections=[
                    TemplateSection(
                        id="s1", title="摘要", order_index=0, required=True,
                        description="简要概述研究背景、方法、结果和结论",
                        word_count_hint=800,
                        ai_guidance="撰写摘要时应包含：研究背景（100字）、研究目的（100字）、研究方法（200字）、主要结果（300字）、结论与意义（100字）",
                        example_content="本研究旨在探讨...",
                    ),
                    TemplateSection(
                        id="s2", title="Abstract", order_index=1, required=True,
                        description="英文摘要",
                        word_count_hint=500,
                        ai_guidance="Write the abstract following the same structure as the Chinese abstract",
                    ),
                    TemplateSection(
                        id="s3", title="目录", order_index=2, required=True,
                    ),
                    TemplateSection(
                        id="s4", title="第一章 绪论", order_index=3, required=True,
                        description="介绍研究背景、意义、国内外研究现状和论文结构",
                        word_count_hint=5000,
                        ai_guidance="绪论应包含：1.研究背景（1000字）2.研究意义（800字）3.国内外研究现状（2500字）4.研究内容与方法（500字）5.论文结构安排（200字）",
                        example_content="1.1 研究背景\n\n随着信息技术的快速发展...",
                    ),
                    TemplateSection(
                        id="s5", title="第二章 文献综述", order_index=4, required=True,
                        description="系统回顾相关领域的研究进展",
                        word_count_hint=8000,
                        ai_guidance="文献综述应系统梳理国内外相关研究，按照主题或时间线索组织，注意批判性分析",
                    ),
                    TemplateSection(
                        id="s6", title="第三章 研究方法", order_index=5, required=True,
                        description="详细描述研究设计、数据收集和分析方法",
                        word_count_hint=6000,
                        ai_guidance="研究方法部分应详细到可重复，包括：研究设计、样本选择、数据收集工具、分析方法",
                    ),
                    TemplateSection(
                        id="s7", title="第四章 研究结果", order_index=6, required=True,
                        description="客观呈现研究发现",
                        word_count_hint=6000,
                        ai_guidance="结果部分应客观陈述发现，使用图表辅助展示，注意与方法的对应关系",
                    ),
                    TemplateSection(
                        id="s8", title="第五章 讨论与结论", order_index=7, required=True,
                        description="解释结果意义，提出研究局限和未来方向",
                        word_count_hint=5000,
                        ai_guidance="讨论应解释结果的理论和实践意义，与文献对比，承认局限，展望未来研究",
                    ),
                    TemplateSection(
                        id="s9", title="参考文献", order_index=8, required=True,
                    ),
                    TemplateSection(
                        id="s10", title="附录", order_index=9, required=False,
                        description="补充材料",
                    ),
                    TemplateSection(
                        id="s11", title="致谢", order_index=10, required=False,
                        description="感谢对论文完成有贡献的人员",
                        word_count_hint=1000,
                    ),
                ],
                format=TemplateFormat(
                    font_family="SimSun",
                    font_size=12.0,
                    line_height=1.5,
                    margins={"top": 2.5, "bottom": 2.5, "left": 3.0, "right": 2.5},
                    heading_styles={
                        "h1": {"fontSize": 16, "bold": True},
                        "h2": {"fontSize": 14, "bold": True},
                        "h3": {"fontSize": 12, "bold": True},
                    },
                ),
                stats=TemplateStats(download_count=1250, rating=4.8, rating_count=156),
                keywords=["浙江大学", "硕士", "学位论文", "模板"],
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 2, 15),
            ),
            PaperTemplate(
                id="t2",
                name="GB/T 7714-2015 参考文献格式",
                description="国家标准 GB/T 7714-2015 参考文献著录规则模板，适用于中文学术论文",
                type=TemplateType.JOURNAL,
                author="ScholarForge",
                tags=["国标", "参考文献", "通用", "中文"],
                language="zh",
                format=TemplateFormat(
                    font_family="SimSun",
                    font_size=10.5,
                    line_height=1.25,
                    margins={"top": 2.5, "bottom": 2.5, "left": 2.5, "right": 2.5},
                ),
                stats=TemplateStats(download_count=3200, rating=4.9, rating_count=428),
                keywords=["国标", "GB/T 7714", "参考文献", "格式"],
                created_at=datetime(2026, 1, 1),
                updated_at=datetime(2026, 2, 1),
            ),
            PaperTemplate(
                id="t3",
                name="IEEE Conference Paper Template",
                description="IEEE conference paper standard format template, suitable for computer science and engineering fields",
                type=TemplateType.CONFERENCE,
                institution="IEEE",
                author="ScholarForge",
                tags=["IEEE", "conference", "English", "CS"],
                discipline="computer_science",
                language="en",
                difficulty="advanced",
                sections=[
                    TemplateSection(
                        id="s1", title="Abstract", order_index=0, required=True,
                        word_count_hint=200,
                        ai_guidance="Write a concise abstract summarizing: background, methods, key results, and significance",
                    ),
                    TemplateSection(
                        id="s2", title="Introduction", order_index=1, required=True,
                        word_count_hint=1000,
                        ai_guidance="Introduction should: 1. Present the problem 2. Review related work 3. State contributions",
                    ),
                    TemplateSection(
                        id="s3", title="Related Work", order_index=2, required=True,
                        word_count_hint=1000,
                        ai_guidance="Systematically review related approaches, highlighting differences from your work",
                    ),
                    TemplateSection(
                        id="s4", title="Methodology", order_index=3, required=True,
                        word_count_hint=2000,
                        ai_guidance="Describe your approach with sufficient detail for replication",
                    ),
                    TemplateSection(
                        id="s5", title="Experiments", order_index=4, required=True,
                        word_count_hint=2000,
                        ai_guidance="Present experimental setup, datasets, metrics, and results with statistical significance",
                    ),
                    TemplateSection(
                        id="s6", title="Conclusion", order_index=5, required=True,
                        word_count_hint=500,
                        ai_guidance="Summarize key findings, acknowledge limitations, and suggest future work",
                    ),
                    TemplateSection(
                        id="s7", title="References", order_index=6, required=True,
                    ),
                ],
                format=TemplateFormat(
                    font_family="Times New Roman",
                    font_size=10.0,
                    line_height=1.2,
                    margins={"top": 1.9, "bottom": 2.5, "left": 1.78, "right": 1.78},
                    heading_styles={
                        "h1": {"fontSize": 10, "bold": True},
                        "h2": {"fontSize": 10, "bold": True, "italic": True},
                    },
                    column_count=2,
                ),
                stats=TemplateStats(download_count=890, rating=4.7, rating_count=112),
                keywords=["IEEE", "conference", "computer science", "English"],
                created_at=datetime(2026, 1, 15),
                updated_at=datetime(2026, 2, 10),
            ),
            PaperTemplate(
                id="t4",
                name="ACM Journal Article Template",
                description="ACM journal article standard format template for computer science publications",
                type=TemplateType.JOURNAL,
                institution="ACM",
                author="ScholarForge",
                tags=["ACM", "journal", "English", "CS"],
                discipline="computer_science",
                language="en",
                difficulty="advanced",
                format=TemplateFormat(
                    font_family="Times New Roman",
                    font_size=9.0,
                    line_height=1.0,
                    margins={"top": 2.0, "bottom": 2.0, "left": 1.9, "right": 1.9},
                ),
                stats=TemplateStats(download_count=560, rating=4.6, rating_count=78),
                keywords=["ACM", "journal", "computer science", "English"],
                created_at=datetime(2026, 1, 20),
                updated_at=datetime(2026, 2, 5),
            ),
            PaperTemplate(
                id="t5",
                name="Nature Research Article Template",
                description="Nature research article template for high-impact scientific publications",
                type=TemplateType.JOURNAL,
                institution="Nature",
                author="ScholarForge",
                tags=["Nature", "journal", "English", "science", "high-impact"],
                discipline="science",
                language="en",
                difficulty="advanced",
                sections=[
                    TemplateSection(
                        id="s1", title="Abstract", order_index=0, required=True,
                        word_count_hint=150,
                        ai_guidance="Nature abstracts are concise: one sentence per section background, methods, key results, conclusion",
                    ),
                    TemplateSection(
                        id="s2", title="Introduction", order_index=1, required=True,
                        word_count_hint=800,
                    ),
                    TemplateSection(
                        id="s3", title="Results", order_index=2, required=True,
                        word_count_hint=3000,
                    ),
                    TemplateSection(
                        id="s4", title="Discussion", order_index=3, required=True,
                        word_count_hint=1500,
                    ),
                    TemplateSection(
                        id="s5", title="Methods", order_index=4, required=True,
                        word_count_hint=2000,
                    ),
                    TemplateSection(
                        id="s6", title="References", order_index=5, required=True,
                    ),
                ],
                format=TemplateFormat(
                    font_family="Arial",
                    font_size=11.0,
                    line_height=1.5,
                    margins={"top": 2.0, "bottom": 2.0, "left": 2.0, "right": 2.0},
                ),
                stats=TemplateStats(download_count=450, rating=4.8, rating_count=62),
                keywords=["Nature", "research", "high-impact", "English"],
                created_at=datetime(2026, 1, 25),
                updated_at=datetime(2026, 2, 8),
            ),
            PaperTemplate(
                id="t6",
                name="本科毕业论文模板（通用版）",
                description="适用于各类高校的本科毕业论文通用模板",
                type=TemplateType.THESIS,
                author="ScholarForge",
                tags=["本科", "毕业论文", "通用", "中文"],
                language="zh",
                difficulty="beginner",
                sections=[
                    TemplateSection(
                        id="s1", title="摘要", order_index=0, required=True,
                        word_count_hint=500,
                    ),
                    TemplateSection(
                        id="s2", title="Abstract", order_index=1, required=True,
                        word_count_hint=300,
                    ),
                    TemplateSection(
                        id="s3", title="第一章 绪论", order_index=2, required=True,
                        word_count_hint=3000,
                    ),
                    TemplateSection(
                        id="s4", title="第二章 相关理论与技术", order_index=3, required=True,
                        word_count_hint=4000,
                    ),
                    TemplateSection(
                        id="s5", title="第三章 系统设计与实现", order_index=4, required=True,
                        word_count_hint=5000,
                    ),
                    TemplateSection(
                        id="s6", title="第四章 测试与分析", order_index=5, required=True,
                        word_count_hint=3000,
                    ),
                    TemplateSection(
                        id="s7", title="第五章 总结与展望", order_index=6, required=True,
                        word_count_hint=2000,
                    ),
                    TemplateSection(
                        id="s8", title="参考文献", order_index=7, required=True,
                    ),
                    TemplateSection(
                        id="s9", title="致谢", order_index=8, required=False,
                        word_count_hint=800,
                    ),
                ],
                format=TemplateFormat(
                    font_family="SimSun",
                    font_size=12.0,
                    line_height=1.5,
                    margins={"top": 2.54, "bottom": 2.54, "left": 3.17, "right": 3.17},
                ),
                stats=TemplateStats(download_count=2100, rating=4.5, rating_count=289),
                keywords=["本科", "毕业论文", "通用", "中文"],
                created_at=datetime(2026, 1, 10),
                updated_at=datetime(2026, 2, 12),
            ),
        ]

        for template in templates:
            template.update_searchable_content()
            self._templates[template.id] = template

    async def search(
        self,
        query: str,
        filter: Optional[SearchFilter] = None,
        sort_by: str = "relevance",
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        搜索模板

        Args:
            query: 搜索关键词
            filter: 过滤条件
            sort_by: 排序方式 (relevance/rating/downloads/created)
            limit: 返回数量
            offset: 偏移量

        Returns:
            搜索结果和总数
        """
        results = []

        for template in self._templates.values():
            # 应用过滤
            if not self._matches_filter(template, filter):
                continue

            # 计算匹配分数
            score, matched_fields = self._calculate_score(template, query)

            if score > 0 or not query:
                results.append(SearchResult(
                    template=template,
                    score=score,
                    matched_fields=matched_fields,
                ))

        # 排序
        results = self._sort_results(results, sort_by)

        # 分页
        total = len(results)
        paginated = results[offset:offset + limit]

        return {
            "items": [r.template.to_dict() for r in paginated],
            "total": total,
            "page": offset // limit + 1,
            "page_size": limit,
            "query": query,
        }

    def _matches_filter(
        self,
        template: PaperTemplate,
        filter: Optional[SearchFilter],
    ) -> bool:
        """检查模板是否匹配过滤条件"""
        if not filter:
            return True

        if filter.type and template.type != filter.type:
            return False

        if filter.institution and filter.institution.lower() not in (
            template.institution or "").lower():
            return False

        if filter.discipline and template.discipline != filter.discipline:
            return False

        if filter.language and template.language != filter.language:
            return False

        if filter.difficulty and template.difficulty != filter.difficulty:
            return False

        if filter.tags:
            if not all(tag in template.tags for tag in filter.tags):
                return False

        if filter.min_rating and template.stats.rating < filter.min_rating:
            return False

        if filter.created_after and template.created_at < filter.created_after:
            return False

        if filter.created_before and template.created_at > filter.created_before:
            return False

        return True

    def _calculate_score(
        self,
        template: PaperTemplate,
        query: str,
    ) -> tuple[float, List[str]]:
        """计算匹配分数"""
        if not query:
            return 1.0, []

        query_lower = query.lower()
        query_terms = query_lower.split()
        score = 0.0
        matched_fields = []

        # 名称匹配 (最高权重)
        if query_lower in template.name.lower():
            score += 10.0
            matched_fields.append("name")
        elif any(term in template.name.lower() for term in query_terms):
            score += 5.0
            matched_fields.append("name")

        # 标签匹配
        for tag in template.tags:
            if query_lower in tag.lower():
                score += 8.0
                matched_fields.append("tags")
                break

        # 机构匹配
        if template.institution and query_lower in template.institution.lower():
            score += 7.0
            matched_fields.append("institution")

        # 描述匹配
        if query_lower in template.description.lower():
            score += 3.0
            matched_fields.append("description")

        # 关键词匹配
        for keyword in template.keywords:
            if query_lower in keyword.lower():
                score += 6.0
                matched_fields.append("keywords")
                break

        # 章节标题匹配
        for section in template.sections:
            if query_lower in section.title.lower():
                score += 2.0
                matched_fields.append("sections")
                break

        # 可搜索内容匹配
        if template.searchable_content and query_lower in template.searchable_content:
            score += 1.0

        return score, list(set(matched_fields))

    def _sort_results(
        self,
        results: List[SearchResult],
        sort_by: str,
    ) -> List[SearchResult]:
        """排序结果"""
        if sort_by == "relevance":
            return sorted(results, key=lambda r: (-r.score, -r.template.stats.rating))
        elif sort_by == "rating":
            return sorted(results, key=lambda r: (-r.template.stats.rating, -r.score))
        elif sort_by == "downloads":
            return sorted(results, key=lambda r: (-r.template.stats.download_count, -r.score))
        elif sort_by == "created":
            return sorted(results, key=lambda r: (r.template.created_at or datetime.min), reverse=True)
        elif sort_by == "updated":
            return sorted(results, key=lambda r: (r.template.updated_at or datetime.min), reverse=True)
        else:
            return results

    async def get_template(self, template_id: str) -> Optional[PaperTemplate]:
        """获取模板详情"""
        return self._templates.get(template_id)

    async def get_templates_by_ids(self, ids: List[str]) -> List[PaperTemplate]:
        """批量获取模板"""
        return [self._templates[id] for id in ids if id in self._templates]

    async def get_suggestions(
        self,
        query: str,
        limit: int = 5,
    ) -> List[str]:
        """获取搜索建议"""
        suggestions = set()
        query_lower = query.lower()

        for template in self._templates.values():
            # 名称建议
            if query_lower in template.name.lower():
                suggestions.add(template.name)

            # 标签建议
            for tag in template.tags:
                if query_lower in tag.lower():
                    suggestions.add(tag)

            # 机构建议
            if template.institution and query_lower in template.institution.lower():
                suggestions.add(template.institution)

        return list(suggestions)[:limit]

    async def get_filters(self) -> Dict[str, Any]:
        """获取可用的过滤选项"""
        institutions = set()
        disciplines = set()
        tags = set()

        for template in self._templates.values():
            if template.institution:
                institutions.add(template.institution)
            if template.discipline:
                disciplines.add(template.discipline)
            tags.update(template.tags)

        return {
            "types": [t.value for t in TemplateType],
            "institutions": sorted(institutions),
            "disciplines": sorted(disciplines),
            "languages": ["zh", "en"],
            "difficulties": ["beginner", "intermediate", "advanced"],
            "tags": sorted(tags),
        }
