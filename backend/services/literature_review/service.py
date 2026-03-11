"""
文献综述生成服务
基于AI自动生成学术综述
"""

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
import asyncio

from ..ai.llm_provider_v2 import LLMService, GenerationResult
from .schemas import (
    LiteratureReviewRequest,
    LiteratureReview,
    LiteratureReviewSection,
    ArticleSummary,
    ThemeAnalysis,
    ComparisonPoint,
    ReviewOutline,
    ReviewLength,
)


class LiteratureReviewService:
    """文献综述生成服务"""

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self._tasks: Dict[str, Dict] = {}

    async def generate_review(
        self,
        request: LiteratureReviewRequest,
        articles_data: List[Dict[str, Any]],
    ) -> LiteratureReview:
        """
        生成文献综述

        Args:
            request: 综述生成请求
            articles_data: 文献数据列表

        Returns:
            LiteratureReview: 生成的综述
        """
        review_id = str(uuid.uuid4())

        # 1. 分析文献并生成摘要
        article_summaries = await self._analyze_articles(articles_data)

        # 2. 识别主题
        themes = await self._identify_themes(article_summaries)

        # 3. 生成对比分析
        comparisons = await self._generate_comparisons(article_summaries)

        # 4. 生成综述大纲
        outline = await self._generate_outline(
            request, article_summaries, themes
        )

        # 5. 生成各章节内容
        sections = await self._generate_sections(
            request, outline, article_summaries, themes
        )

        # 6. 识别研究空白
        gaps = await self._identify_research_gaps(article_summaries, themes)

        # 7. 生成未来研究方向
        future_directions = await self._generate_future_directions(gaps, themes)

        # 8. 计算字数
        word_count = self._count_words(sections)

        return LiteratureReview(
            id=review_id,
            title=outline.title,
            abstract=await self._generate_abstract(sections),
            sections=sections,
            themes=themes,
            comparisons=comparisons,
            research_gaps=gaps,
            future_directions=future_directions,
            references=self._format_references(articles_data),
            generated_at=datetime.now(),
            word_count=word_count,
            metadata={
                "article_count": len(articles_data),
                "focus_area": request.focus_area.value,
                "output_length": request.output_length.value,
            }
        )

    async def _analyze_articles(
        self,
        articles: List[Dict[str, Any]]
    ) -> List[ArticleSummary]:
        """分析文献并生成摘要"""
        summaries = []

        for article in articles:
            # 使用AI提取关键信息
            prompt = f"""请分析以下论文，提取关键信息：

标题: {article.get('title', '')}
作者: {', '.join([a.get('name', '') for a in article.get('authors', [])])}
摘要: {article.get('abstract', '')[:1000]}

请用JSON格式返回：
{{
    "key_findings": ["发现1", "发现2", "发现3"],
    "methodology": "简要描述研究方法",
    "relevance_score": 0.85
}}"""

            try:
                result = await self.llm.generate(
                    prompt=prompt,
                    max_tokens=500,
                    temperature=0.3,
                )

                # 解析AI返回的结果
                import json
                analysis = json.loads(result.content if hasattr(result, 'content') else result)

                summary = ArticleSummary(
                    id=article.get('id', str(uuid.uuid4())),
                    title=article.get('title', ''),
                    authors=[a.get('name', '') for a in article.get('authors', [])],
                    year=article.get('publication_year'),
                    abstract=article.get('abstract', '')[:500],
                    key_findings=analysis.get('key_findings', []),
                    methodology=analysis.get('methodology', ''),
                    relevance_score=analysis.get('relevance_score', 0.5),
                )
                summaries.append(summary)

            except Exception as e:
                # 如果AI分析失败，使用基本信息
                summaries.append(ArticleSummary(
                    id=article.get('id', str(uuid.uuid4())),
                    title=article.get('title', ''),
                    authors=[a.get('name', '') for a in article.get('authors', [])],
                    year=article.get('publication_year'),
                    abstract=article.get('abstract', '')[:500],
                    key_findings=[],
                    methodology="",
                    relevance_score=0.5,
                ))

        return summaries

    async def _identify_themes(
        self,
        summaries: List[ArticleSummary]
    ) -> List[ThemeAnalysis]:
        """识别研究主题"""
        # 构建主题识别提示
        articles_text = "\n\n".join([
            f"文章{i+1}: {s.title}\n摘要: {s.abstract[:300]}\n关键发现: {', '.join(s.key_findings[:3])}"
            for i, s in enumerate(summaries[:10])  # 限制分析前10篇
        ])

        prompt = f"""请分析以下文献，识别3-5个主要研究主题：

{articles_text}

请用JSON格式返回主题列表：
[
    {{
        "theme": "主题名称",
        "description": "主题描述",
        "key_points": ["要点1", "要点2"]
    }}
]"""

        try:
            result = await self.llm.generate(
                prompt=prompt,
                max_tokens=800,
                temperature=0.4,
            )

            import json
            themes_data = json.loads(result.content if hasattr(result, 'content') else result)

            themes = []
            for t in themes_data:
                theme = ThemeAnalysis(
                    theme=t.get('theme', ''),
                    description=t.get('description', ''),
                    related_articles=[],  # 后续可以关联相关文章
                    key_points=t.get('key_points', []),
                )
                themes.append(theme)

            return themes

        except Exception as e:
            # 返回默认主题
            return [
                ThemeAnalysis(
                    theme="相关研究",
                    description="基于所选文献的综合研究",
                    related_articles=[s.id for s in summaries],
                    key_points=["文献分析", "研究综合"],
                )
            ]

    async def _generate_comparisons(
        self,
        summaries: List[ArticleSummary]
    ) -> List[ComparisonPoint]:
        """生成文献对比分析"""
        # 对比不同文献的方法论
        methodologies = [s.methodology for s in summaries if s.methodology]

        if len(methodologies) >= 2:
            prompt = f"""请对比以下研究方法：

{chr(10).join([f"文献{i+1}: {m}" for i, m in enumerate(methodologies[:5])])}

请描述它们的异同点和优缺点。"""

            try:
                result = await self.llm.generate(prompt=prompt, max_tokens=600)
                return [ComparisonPoint(
                    aspect="研究方法",
                    comparisons={s.id: s.methodology for s in summaries[:5]},
                    consensus=None,
                    differences=[result.content if hasattr(result, 'content') else str(result)],
                )]
            except:
                pass

        return []

    async def _generate_outline(
        self,
        request: LiteratureReviewRequest,
        summaries: List[ArticleSummary],
        themes: List[ThemeAnalysis],
    ) -> ReviewOutline:
        """生成综述大纲"""
        focus_map = {
            "general": "综合性文献综述",
            "methodology": "方法论综述",
            "findings": "研究发现综述",
            "trends": "研究趋势综述",
            "gaps": "研究空白综述",
        }

        length_map = {
            "short": "短篇(~1000字)",
            "medium": "中篇(~3000字)",
            "long": "长篇(~5000字)",
        }

        prompt = f"""请为以下文献综述生成大纲：

研究主题: {focus_map.get(request.focus_area.value, '文献综述')}
文献数量: {len(summaries)}篇
输出长度: {length_map.get(request.output_length.value, '中篇')}
主要主题: {', '.join([t.theme for t in themes])}

请用JSON格式返回：
{{
    "title": "综述标题",
    "sections": [
        {{"title": "1. 引言", "description": "..."}},
        {{"title": "2. 文献综述", "subsections": [...]}}
    ],
    "estimated_word_count": 3000,
    "key_themes": ["主题1", "主题2"]
}}"""

        try:
            result = await self.llm.generate(
                prompt=prompt,
                max_tokens=800,
                temperature=0.4,
            )

            import json
            outline_data = json.loads(result.content if hasattr(result, 'content') else result)

            return ReviewOutline(
                title=outline_data.get('title', '文献综述'),
                sections=outline_data.get('sections', []),
                estimated_word_count=outline_data.get('estimated_word_count', 3000),
                key_themes=outline_data.get('key_themes', []),
            )

        except Exception:
            # 返回默认大纲
            return ReviewOutline(
                title="文献综述：相关研究进展",
                sections=[
                    {"title": "1. 引言", "description": "研究背景和意义"},
                    {"title": "2. 文献综述", "description": "相关研究梳理"},
                    {"title": "3. 讨论", "description": "研究发现讨论"},
                    {"title": "4. 结论", "description": "总结与展望"},
                ],
                estimated_word_count=3000,
                key_themes=[t.theme for t in themes],
            )

    async def _generate_sections(
        self,
        request: LiteratureReviewRequest,
        outline: ReviewOutline,
        summaries: List[ArticleSummary],
        themes: List[ThemeAnalysis],
    ) -> List[LiteratureReviewSection]:
        """生成各章节内容"""
        sections = []

        # 生成引言
        intro_prompt = f"""请为文献综述撰写引言部分（约500字）：

主题: {outline.title}
文献数量: {len(summaries)}篇
时间范围: {min([s.year for s in summaries if s.year]) if any(s.year for s in summaries) else '未知'} - {max([s.year for s in summaries if s.year]) if any(s.year for s in summaries) else '未知'}

要求:
1. 介绍研究背景和意义
2. 说明文献筛选标准
3. 概述综述结构
"""
        intro_result = await self.llm.generate(prompt=intro_prompt, max_tokens=800)
        sections.append(LiteratureReviewSection(
            title="引言",
            content=intro_result.content if hasattr(intro_result, 'content') else str(intro_result),
            subsections=[],
            cited_articles=[s.id for s in summaries[:5]],
        ))

        # 为主题生成章节
        for theme in themes:
            theme_prompt = f"""请撰写关于"{theme.theme}"的文献综述部分：

主题描述: {theme.description}
相关文献: {len(theme.related_articles)}篇
关键要点: {', '.join(theme.key_points)}

要求:
1. 综合相关文献的观点
2. 指出共识和分歧
3. 约600-800字
"""
            theme_result = await self.llm.generate(prompt=theme_prompt, max_tokens=1200)
            sections.append(LiteratureReviewSection(
                title=theme.theme,
                content=theme_result.content if hasattr(theme_result, 'content') else str(theme_result),
                subsections=[],
                cited_articles=theme.related_articles,
            ))

        # 生成结论
        conclusion_prompt = f"""请撰写综述结论部分（约400字）：

主题: {outline.title}
主要发现: {len(summaries)}篇文献的综合分析

要求:
1. 总结主要发现
2. 指出研究局限
3. 展望未来方向
"""
        conclusion_result = await self.llm.generate(prompt=conclusion_prompt, max_tokens=600)
        sections.append(LiteratureReviewSection(
            title="结论与展望",
            content=conclusion_result.content if hasattr(conclusion_result, 'content') else str(conclusion_result),
            subsections=[],
            cited_articles=[s.id for s in summaries[:3]],
        ))

        return sections

    async def _identify_research_gaps(
        self,
        summaries: List[ArticleSummary],
        themes: List[ThemeAnalysis],
    ) -> List[str]:
        """识别研究空白"""
        findings_text = "\n".join([
            f"- {s.title}: {', '.join(s.key_findings[:2])}"
            for s in summaries[:10]
        ])

        prompt = f"""基于以下文献发现，识别3-5个研究空白：

文献发现:
{findings_text}

请列出研究空白:"""

        try:
            result = await self.llm.generate(prompt=prompt, max_tokens=500)
            content = result.content if hasattr(result, 'content') else str(result)
            return [line.strip("- ") for line in content.split("\n") if line.strip().startswith("-")][:5]
        except:
            return ["需要更多实证研究", "缺乏长期跟踪数据", "跨文化研究不足"]

    async def _generate_future_directions(
        self,
        gaps: List[str],
        themes: List[ThemeAnalysis],
    ) -> List[str]:
        """生成未来研究方向"""
        prompt = f"""基于以下研究空白，提出未来研究方向：

研究空白:
{chr(10).join([f'- {g}' for g in gaps])}

请提出3-5个未来研究方向:"""

        try:
            result = await self.llm.generate(prompt=prompt, max_tokens=500)
            content = result.content if hasattr(result, 'content') else str(result)
            return [line.strip("- ") for line in content.split("\n") if line.strip().startswith("-")][:5]
        except:
            return ["开展更多实证研究", "探索新的研究方法", "加强跨学科合作"]

    async def _generate_abstract(self, sections: List[LiteratureReviewSection]) -> str:
        """生成综述摘要"""
        sections_text = "\n\n".join([
            f"{s.title}:\n{s.content[:300]}..."
            for s in sections[:3]
        ])

        prompt = f"""请为以下综述生成摘要（200字以内）：

{sections_text}

摘要:"""

        try:
            result = await self.llm.generate(prompt=prompt, max_tokens=300)
            return result.content if hasattr(result, 'content') else str(result)
        except:
            return "本文对相关文献进行了系统综述，分析了研究现状、主要发现和未来方向。"

    def _format_references(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化参考文献"""
        return [
            {
                "id": a.get("id", ""),
                "title": a.get("title", ""),
                "authors": [author.get("name", "") for author in a.get("authors", [])],
                "year": a.get("publication_year"),
                "journal": a.get("source_name", ""),
                "doi": a.get("doi"),
                "url": a.get("source_url"),
            }
            for a in articles
        ]

    def _count_words(self, sections: List[LiteratureReviewSection]) -> int:
        """计算总字数"""
        total = 0
        for section in sections:
            total += len(section.content.replace(" ", ""))
            for sub in section.subsections:
                total += len(sub.content.replace(" ", ""))
        return total

    def export_to_markdown(self, review: LiteratureReview) -> str:
        """导出为Markdown格式"""
        lines = [
            f"# {review.title}",
            "",
            "## 摘要",
            review.abstract,
            "",
        ]

        for section in review.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

            for sub in section.subsections:
                lines.append(f"### {sub.title}")
                lines.append("")
                lines.append(sub.content)
                lines.append("")

        if review.research_gaps:
            lines.append("## 研究空白")
            lines.append("")
            for gap in review.research_gaps:
                lines.append(f"- {gap}")
            lines.append("")

        if review.future_directions:
            lines.append("## 未来研究方向")
            lines.append("")
            for direction in review.future_directions:
                lines.append(f"- {direction}")
            lines.append("")

        if review.references:
            lines.append("## 参考文献")
            lines.append("")
            for i, ref in enumerate(review.references, 1):
                authors = ", ".join(ref.get("authors", [])[:3])
                if len(ref.get("authors", [])) > 3:
                    authors += " et al."
                lines.append(
                    f"[{i}] {authors}. {ref.get('title', '')}. "
                    f"{ref.get('journal', '')} {ref.get('year', '')}."
                )

        return "\n".join(lines)
