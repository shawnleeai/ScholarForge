"""
AI模板填充服务
使用AI智能填充模板内容
"""

from typing import List, Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import json

from .models import PaperTemplate, TemplateSection, TemplateField, FieldType


@dataclass
class FillRequest:
    """填充请求"""
    template_id: str
    paper_title: str
    paper_abstract: Optional[str] = None
    paper_keywords: List[str] = None
    research_area: Optional[str] = None
    target_audience: Optional[str] = None
    tone: str = "academic"  # academic/formal/casual
    language: str = "zh"
    additional_context: Optional[str] = None


@dataclass
class SectionFillResult:
    """章节填充结果"""
    section_id: str
    section_title: str
    content: str
    word_count: int
    confidence: float
    suggestions: List[str]
    references: List[str]


@dataclass
class FillResult:
    """填充结果"""
    template_id: str
    filled_sections: List[SectionFillResult]
    total_word_count: int
    estimated_quality: float
    suggestions: List[str]
    generated_at: datetime


class TemplateAIFiller:
    """
    AI模板填充服务
    根据论文信息智能生成各章节内容
    """

    def __init__(self, llm_service=None):
        self.llm = llm_service
        self._prompts = self._initialize_prompts()

    def _initialize_prompts(self) -> Dict[str, str]:
        """初始化提示词模板"""
        return {
            "abstract_zh": """请根据以下论文信息撰写中文摘要（约800字）：

论文标题：{title}
关键词：{keywords}
研究背景：{research_area}
附加信息：{context}

摘要应包含以下结构：
1. 研究背景与意义（100-150字）
2. 研究目的（100字左右）
3. 研究方法（200-250字）
4. 主要研究结果（300-350字）
5. 结论与意义（100-150字）

要求：
- 使用学术中文撰写
- 逻辑清晰，层次分明
- 突出研究创新点
- 不要包含具体数据但要有概括性描述""",

            "abstract_en": """Please write an abstract (about 250 words) based on the following information:

Title: {title}
Keywords: {keywords}
Research Area: {research_area}
Context: {context}

The abstract should include:
1. Background and motivation
2. Research objectives
3. Methodology
4. Key findings
5. Conclusions and implications

Requirements:
- Use formal academic English
- Be concise and informative
- Highlight the contribution
- No citations needed""",

            "introduction_zh": """请为论文"{title}"撰写绪论部分（约5000字）。

研究背景：{research_area}
关键词：{keywords}
摘要：{abstract}
附加信息：{context}

绪论应包含以下小节：
1.1 研究背景（约1000字）
   - 介绍研究领域的发展历程
   - 阐述研究问题的现实需求
   - 说明研究的理论价值

1.2 研究意义（约800字）
   - 理论意义
   - 实践意义

1.3 国内外研究现状（约2500字）
   - 国外研究进展
   - 国内研究进展
   - 现有研究的不足

1.4 研究内容与方法（约500字）
   - 主要研究内容
   - 采用的研究方法

1.5 论文结构安排（约200字）
   - 各章节内容简介

写作要求：
- 学术语言，逻辑严谨
- 引用相关重要文献（用[作者, 年份]格式标注）
- 突出研究创新点
- 与后续章节呼应""",

            "literature_review_zh": """请为论文"{title}"撰写文献综述部分（约8000字）。

研究主题：{research_area}
关键词：{keywords}
研究摘要：{abstract}

文献综述应：
1. 系统梳理相关领域的研究脉络
2. 按照主题或时间线索组织
3. 对重要研究进行批判性分析
4. 指出现有研究的空白和不足
5. 引证至少15-20篇重要文献

结构建议：
- 按研究主题分类综述
- 或按时间发展脉络综述
- 或按研究方法分类综述

写作风格：
- 客观评述，避免简单罗列
- 指出研究间的联系和差异
- 为本研究定位提供依据""",

            "methodology_zh": """请为论文"{title}"撰写研究方法部分（约6000字）。

研究摘要：{abstract}
研究关键词：{keywords}

方法部分应包含：
1. 研究设计
   - 研究类型（实验/调查/案例等）
   - 研究框架

2. 数据收集
   - 数据来源
   - 样本选择标准
   - 收集工具和程序

3. 数据分析方法
   - 定量分析方法
   - 定性分析方法
   - 使用的软件工具

4. 信度和效度保障
   - 可靠性措施
   - 有效性验证

5. 研究伦理
   - 伦理考量
   - 隐私保护

要求：
- 详细到可重复研究
- 说明方法选择的理由
- 承认方法的局限性""",

            "results_zh": """请为论文"{title}"撰写研究结果部分（约6000字）。

研究方法：{methodology_summary}
预期发现：{expected_findings}

结果部分应：
1. 客观呈现研究发现
2. 使用图表辅助说明（用文字描述图表内容）
3. 按逻辑顺序组织结果
4. 突出重要发现
5. 注意与方法部分的对应关系

结构：
- 主要发现（核心结果）
- 次要发现（支持性结果）
- 意外发现（如有）

注意：
- 不要解释结果（留给讨论部分）
- 使用准确的学术语言
- 包含统计显著性信息""",

            "discussion_zh": """请为论文"{title}"撰写讨论与结论部分（约5000字）。

研究结果摘要：{results_summary}
研究意义：{significance}

讨论部分应包含：
1. 主要发现的解释
   - 结果的理论意义
   - 与已有研究的对比

2. 实践意义
   - 对实践的指导价值
   - 应用前景

3. 研究创新点
   - 理论创新
   - 方法创新

4. 研究局限性
   - 承认不足
   - 对结果的影响

5. 未来研究方向
   - 可进一步探索的问题
   - 改进建议

结论部分应：
- 总结核心发现
- 重申研究贡献
- 结束语有力""",

            "conclusion_en": """Please write the conclusion section for the paper "{title}" (about 1000 words).

Key findings: {findings}
Research contribution: {contribution}

The conclusion should:
1. Summarize the main findings
2. Highlight the theoretical contribution
3. Discuss practical implications
4. Acknowledge limitations
5. Suggest future research directions

Requirements:
- Do not introduce new information
- Be concise and impactful
- End with a strong closing statement""",
        }

    async def fill_template(
        self,
        template: PaperTemplate,
        request: FillRequest,
        stream: bool = False,
    ) -> FillResult:
        """
        填充整个模板

        Args:
            template: 模板对象
            request: 填充请求
            stream: 是否流式返回

        Returns:
            填充结果
        """
        filled_sections = []
        total_words = 0
        all_suggestions = []

        # 为每个必需章节生成内容
        for section in template.get_required_sections():
            # 跳过非内容章节（如目录、参考文献）
            if section.title in ["目录", "参考文献", "References"]:
                continue

            result = await self._fill_section(
                section=section,
                request=request,
                template=template,
            )

            if result:
                filled_sections.append(result)
                total_words += result.word_count
                all_suggestions.extend(result.suggestions)

        # 去重建议
        unique_suggestions = list(set(all_suggestions))

        # 估算质量
        quality = self._estimate_quality(filled_sections, request)

        return FillResult(
            template_id=template.id,
            filled_sections=filled_sections,
            total_word_count=total_words,
            estimated_quality=quality,
            suggestions=unique_suggestions[:10],
            generated_at=datetime.now(),
        )

    async def _fill_section(
        self,
        section: TemplateSection,
        request: FillRequest,
        template: PaperTemplate,
    ) -> Optional[SectionFillResult]:
        """填充单个章节"""

        # 获取对应的提示词
        prompt = self._get_section_prompt(
            section=section,
            request=request,
            template=template,
        )

        if not prompt:
            return None

        # 如果有LLM服务，使用它生成内容
        if self.llm:
            try:
                content = await self._generate_with_llm(prompt)
            except Exception as e:
                # 如果LLM失败，使用模拟内容
                content = self._generate_mock_content(section, request)
        else:
            # 使用模拟内容
            content = self._generate_mock_content(section, request)

        word_count = len(content.replace(" ", "").replace("\n", ""))

        # 分析内容质量
        confidence = self._analyze_confidence(content, section)

        # 生成建议
        suggestions = self._generate_suggestions(content, section, request)

        # 提取引用
        references = self._extract_references(content)

        return SectionFillResult(
            section_id=section.id,
            section_title=section.title,
            content=content,
            word_count=word_count,
            confidence=confidence,
            suggestions=suggestions,
            references=references,
        )

    def _get_section_prompt(
        self,
        section: TemplateSection,
        request: FillRequest,
        template: PaperTemplate,
    ) -> Optional[str]:
        """获取章节的提示词"""

        section_title_lower = section.title.lower()

        # 根据章节标题匹配提示词
        if "abstract" in section_title_lower or "摘要" in section_title_lower:
            if request.language == "zh":
                return self._prompts["abstract_zh"].format(
                    title=request.paper_title,
                    keywords=", ".join(request.paper_keywords or []),
                    research_area=request.research_area or "",
                    context=request.additional_context or "",
                )
            else:
                return self._prompts["abstract_en"].format(
                    title=request.paper_title,
                    keywords=", ".join(request.paper_keywords or []),
                    research_area=request.research_area or "",
                    context=request.additional_context or "",
                )

        elif "introduction" in section_title_lower or "绪论" in section_title_lower:
            return self._prompts["introduction_zh"].format(
                title=request.paper_title,
                research_area=request.research_area or "",
                keywords=", ".join(request.paper_keywords or []),
                abstract=request.paper_abstract or "",
                context=request.additional_context or "",
            )

        elif "literature" in section_title_lower or "文献综述" in section_title_lower:
            return self._prompts["literature_review_zh"].format(
                title=request.paper_title,
                research_area=request.research_area or "",
                keywords=", ".join(request.paper_keywords or []),
                abstract=request.paper_abstract or "",
            )

        elif "method" in section_title_lower or "方法" in section_title_lower:
            return self._prompts["methodology_zh"].format(
                title=request.paper_title,
                abstract=request.paper_abstract or "",
                keywords=", ".join(request.paper_keywords or []),
            )

        elif "result" in section_title_lower or "结果" in section_title_lower:
            return self._prompts["results_zh"].format(
                title=request.paper_title,
                methodology_summary="待补充",
                expected_findings="待补充",
            )

        elif "discussion" in section_title_lower or "conclusion" in section_title_lower or \
             "讨论" in section_title_lower or "结论" in section_title_lower:
            return self._prompts["discussion_zh"].format(
                title=request.paper_title,
                results_summary="待补充",
                significance="待补充",
            )

        # 使用通用AI指导
        if section.ai_guidance:
            return f"""请为论文"{request.paper_title}"撰写"{section.title}"部分。

研究背景：{request.research_area}
关键词：{', '.join(request.paper_keywords or [])}

写作指导：
{section.ai_guidance}

示例内容参考：
{section.example_content or '无'}

要求：
- 字数约{section.word_count_hint or '适当'}字
- 使用学术语言
- 与前文保持逻辑连贯"""

        return None

    async def _generate_with_llm(self, prompt: str) -> str:
        """使用LLM生成内容"""
        # 这里应该调用实际的LLM服务
        # 简化版本返回提示词的一部分
        if self.llm:
            return await self.llm.generate(prompt)
        raise NotImplementedError("LLM service not available")

    def _generate_mock_content(self, section: TemplateSection, request: FillRequest) -> str:
        """生成模拟内容"""
        # 这是演示用的模拟内容
        content_parts = [
            f"# {section.title}",
            "",
            f"【这是{section.title}的AI生成内容示例】",
            "",
            f"论文标题：{request.paper_title}",
            "",
        ]

        if section.description:
            content_parts.extend([
                f"本章主要内容：{section.description}",
                "",
            ])

        if section.word_count_hint:
            content_parts.extend([
                f"【建议字数：{section.word_count_hint}字】",
                "",
            ])

        content_parts.extend([
            "【AI写作指导】",
            section.ai_guidance or "无特定指导",
            "",
            "【示例内容参考】",
            section.example_content or "无示例内容",
            "",
            "---",
            "注意：以上为AI生成的示例内容。在实际部署时，这里将包含由大语言模型生成的完整学术内容。",
        ])

        return "\n".join(content_parts)

    def _analyze_confidence(self, content: str, section: TemplateSection) -> float:
        """分析内容置信度"""
        confidence = 0.5

        # 检查字数是否接近建议
        if section.word_count_hint:
            word_count = len(content)
            ratio = min(word_count / section.word_count_hint, 1.5)
            if 0.8 <= ratio <= 1.2:
                confidence += 0.2
            elif 0.5 <= ratio <= 1.5:
                confidence += 0.1

        # 检查是否有实质内容
        if len(content) > 200:
            confidence += 0.1

        # 检查是否有结构化标记
        if "#" in content or "1." in content or "一、" in content:
            confidence += 0.1

        # 检查AI指导是否被应用
        if section.ai_guidance and len(section.ai_guidance) > 50:
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_suggestions(
        self,
        content: str,
        section: TemplateSection,
        request: FillRequest,
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 字数建议
        if section.word_count_hint:
            actual_words = len(content)
            if actual_words < section.word_count_hint * 0.5:
                suggestions.append(f"{section.title}内容可能偏短，建议扩充至{section.word_count_hint}字左右")

        # 引用建议
        if "[" not in content and section.title not in ["摘要", "Abstract"]:
            suggestions.append(f"建议在{section.title}中增加文献引用以支撑论述")

        # 结构建议
        if section.title in ["文献综述", "Literature Review"]:
            if content.count("\n") < 10:
                suggestions.append("文献综述建议采用更清晰的段落结构，按主题或时间组织")

        # 关键词建议
        if request.paper_keywords:
            content_lower = content.lower()
            missing_keywords = [
                kw for kw in request.paper_keywords[:3]
                if kw.lower() not in content_lower
            ]
            if missing_keywords:
                suggestions.append(f"建议在内容中提及关键词：{', '.join(missing_keywords)}")

        return suggestions

    def _extract_references(self, content: str) -> List[str]:
        """从内容中提取引用"""
        import re

        # 匹配常见的引用格式
        patterns = [
            r'\[([^\]]+?, \d{4})\]',  # [Author, 2020]
            r'\(([^\)]+? et al\.,? \d{4})\)',  # (Author et al., 2020)
            r'【([^】]+?)】',  # 【中文引用】
        ]

        references = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            references.extend(matches)

        return list(set(references))[:10]

    def _estimate_quality(self, sections: List[SectionFillResult], request: FillRequest) -> float:
        """估算整体质量"""
        if not sections:
            return 0.0

        # 基于各章节的置信度
        avg_confidence = sum(s.confidence for s in sections) / len(sections)

        # 章节完整性
        completeness = min(len(sections) / 5, 1.0)  # 假设至少5个主要章节

        # 信息充分性
        info_score = 0.3
        if request.paper_abstract:
            info_score += 0.2
        if request.paper_keywords:
            info_score += 0.2
        if request.research_area:
            info_score += 0.2
        if request.additional_context:
            info_score += 0.1

        return round((avg_confidence * 0.4 + completeness * 0.3 + info_score * 0.3), 2)

    async def fill_section_stream(
        self,
        section: TemplateSection,
        request: FillRequest,
        template: PaperTemplate,
    ) -> AsyncGenerator[str, None]:
        """
        流式填充单个章节

        Args:
            section: 章节对象
            request: 填充请求
            template: 模板对象

        Yields:
            生成的内容片段
        """
        prompt = self._get_section_prompt(section, request, template)

        if not prompt:
            yield f"【{section.title}暂不支持AI填充】"
            return

        # 模拟流式生成
        # 实际实现应该调用LLM的流式接口
        mock_content = self._generate_mock_content(section, request)

        # 模拟逐段输出
        paragraphs = mock_content.split("\n\n")
        for para in paragraphs:
            yield para + "\n\n"

    async def improve_section(
        self,
        section_content: str,
        improvement_type: str,  # expand/condense/clarify/formalize
        target_word_count: Optional[int] = None,
    ) -> str:
        """
        改进章节内容

        Args:
            section_content: 原始内容
            improvement_type: 改进类型
            target_word_count: 目标字数

        Returns:
            改进后的内容
        """
        prompts = {
            "expand": f"请扩充以下内容，增加更多细节和论证。目标字数：{target_word_count or '适当增加'}。\n\n{section_content}",
            "condense": f"请精简以下内容，保留核心观点。目标字数：{target_word_count or '适当精简'}。\n\n{section_content}",
            "clarify": f"请改写以下内容，使其更清晰易懂，逻辑更连贯。\n\n{section_content}",
            "formalize": f"请改写以下内容，使用更正式的学术语言。\n\n{section_content}",
        }

        prompt = prompts.get(improvement_type)
        if not prompt:
            return section_content

        if self.llm:
            try:
                return await self._generate_with_llm(prompt)
            except:
                pass

        # 返回原始内容加注释
        return f"【{improvement_type}改进后的内容】\n\n{section_content}\n\n【改进说明】\n这是模拟的改进结果。实际部署时将使用LLM生成改进后的内容。"

    def get_fill_guidance(self, template: PaperTemplate) -> Dict[str, Any]:
        """获取填充指导"""
        guidance = {
            "template_info": {
                "name": template.name,
                "type": template.type.value,
                "estimated_total_words": template.get_total_word_hint(),
            },
            "sections": [],
            "general_tips": [
                "提供详细的论文信息可以获得更好的生成效果",
                "AI生成的内容需要人工审核和修改",
                "建议逐章生成，而不是一次性生成全部内容",
                "使用专业术语和关键词有助于提高内容质量",
            ],
        }

        for section in template.sections:
            section_guidance = {
                "id": section.id,
                "title": section.title,
                "required": section.required,
                "word_count_hint": section.word_count_hint,
                "has_ai_support": bool(section.ai_guidance),
                "tips": [],
            }

            if section.ai_guidance:
                section_guidance["tips"].append(f"AI指导：{section.ai_guidance[:100]}...")

            if section.example_content:
                section_guidance["tips"].append("有示例内容可供参考")

            if section.required:
                section_guidance["tips"].append("必填章节")
            else:
                section_guidance["tips"].append("可选章节")

            guidance["sections"].append(section_guidance)

        return guidance
