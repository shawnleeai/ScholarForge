"""
写作助手服务
学术写作智能辅助功能
"""

from typing import Optional, List, Dict, Any

from .llm_provider import LLMService
from .schemas import WritingTaskType


class WritingAssistant:
    """学术写作助手"""

    # 学术写作系统提示词
    SYSTEM_PROMPTS = {
        "academic_zh": """你是一位专业的学术写作助手，专门帮助研究生和科研人员撰写高质量的学术论文。
你的回答应该：
1. 使用规范的学术语言
2. 保持逻辑清晰、论证严密
3. 遵循学术写作规范
4. 注重原创性和创新性表达
请用中文回答。""",

        "academic_en": """You are a professional academic writing assistant specializing in helping researchers write high-quality academic papers.
Your responses should:
1. Use formal academic language
2. Be logically clear and well-argued
3. Follow academic writing conventions
4. Focus on originality and innovative expression
Please respond in English.""",

        "polish_zh": """你是一位中文学术论文润色专家。你的任务是改进文本的学术表达，使其更加：
1. 规范、专业的学术用语
2. 流畅、准确的语句结构
3. 清晰、简洁的表达方式
4. 符合学术写作规范
保持原文的核心意思，只改进表达方式。""",

        "translate": """You are a professional academic translator. Translate the given text accurately while:
1. Maintaining academic tone and terminology
2. Preserving the original meaning precisely
3. Using appropriate academic expressions in the target language
4. Ensuring natural and fluent translation""",
    }

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def continue_writing(
        self,
        context: str,
        style: str = "academic",
        max_tokens: int = 500,
        language: str = "zh",
    ) -> str:
        """
        智能续写

        Args:
            context: 前文内容
            style: 写作风格
            max_tokens: 最大生成token数
            language: 语言
        """
        system_prompt = self.SYSTEM_PROMPTS.get(
            f"academic_{language}",
            self.SYSTEM_PROMPTS["academic_zh"]
        )

        prompt = f"""请根据以下内容继续写作，保持相同的风格和语气：

{context}

请继续写作："""

        result, _ = await self.llm.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            system_prompt=system_prompt,
        )
        return result

    async def polish_text(
        self,
        text: str,
        style: str = "academic",
        language: str = "zh",
    ) -> str:
        """
        文本润色

        Args:
            text: 待润色文本
            style: 润色风格
            language: 语言
        """
        system_prompt = self.SYSTEM_PROMPTS.get(
            "polish_zh" if language == "zh" else "academic_en"
        )

        prompt = f"""请对以下学术文本进行润色，改进语言表达：

原文：
{text}

润色后的文本："""

        result, _ = await self.llm.generate(
            prompt=prompt,
            max_tokens=len(text) * 2,  # 给足够的空间
            temperature=0.3,  # 低温度保持一致性
            system_prompt=system_prompt,
        )
        return result

    async def rewrite_text(
        self,
        text: str,
        style: str = "academic",
        language: str = "zh",
    ) -> str:
        """
        改写文本（降低重复率）
        """
        system_prompt = self.SYSTEM_PROMPTS.get(
            f"academic_{language}",
            self.SYSTEM_PROMPTS["academic_zh"]
        )

        prompt = f"""请用不同的表达方式改写以下文本，保持原意但使用不同的词汇和句式：

原文：
{text}

改写后的文本："""

        result, _ = await self.llm.generate(
            prompt=prompt,
            max_tokens=len(text) * 2,
            temperature=0.8,  # 较高温度增加多样性
            system_prompt=system_prompt,
        )
        return result

    async def expand_text(
        self,
        text: str,
        target_length: int = 200,
        language: str = "zh",
    ) -> str:
        """
        扩写文本
        """
        system_prompt = self.SYSTEM_PROMPTS.get(
            f"academic_{language}",
            self.SYSTEM_PROMPTS["academic_zh"]
        )

        prompt = f"""请将以下文本扩写至约{target_length}字，增加更多细节和论述：

原文：
{text}

扩写后的文本："""

        result, _ = await self.llm.generate(
            prompt=prompt,
            max_tokens=target_length * 2,
            temperature=0.7,
            system_prompt=system_prompt,
        )
        return result

    async def summarize_text(
        self,
        text: str,
        max_length: int = 200,
        language: str = "zh",
    ) -> str:
        """
        总结文本
        """
        system_prompt = self.SYSTEM_PROMPTS.get(
            f"academic_{language}",
            self.SYSTEM_PROMPTS["academic_zh"]
        )

        prompt = f"""请将以下文本总结为不超过{max_length}字的摘要：

原文：
{text}

摘要："""

        result, _ = await self.llm.generate(
            prompt=prompt,
            max_tokens=max_length * 2,
            temperature=0.3,
            system_prompt=system_prompt,
        )
        return result

    async def translate(
        self,
        text: str,
        source_language: str = "zh",
        target_language: str = "en",
    ) -> str:
        """
        翻译文本
        """
        system_prompt = self.SYSTEM_PROMPTS["translate"]

        prompt = f"""Please translate the following text from {source_language} to {target_language}.
Maintain the academic tone and use appropriate terminology.

Text to translate:
{text}

Translation:"""

        result, _ = await self.llm.generate(
            prompt=prompt,
            max_tokens=len(text) * 3,
            temperature=0.3,
            system_prompt=system_prompt,
        )
        return result

    async def generate_outline(
        self,
        topic: str,
        paper_type: str = "thesis",
        language: str = "zh",
    ) -> List[str]:
        """
        生成论文大纲
        """
        system_prompt = self.SYSTEM_PROMPTS.get(
            f"academic_{language}",
            self.SYSTEM_PROMPTS["academic_zh"]
        )

        if language == "zh":
            prompt = f"""请为以下论文主题生成一个详细的章节大纲：

主题：{topic}
论文类型：{"学位论文" if paper_type == "thesis" else "期刊论文"}

请按章节结构列出大纲，每章包含主要小节："""
        else:
            prompt = f"""Please generate a detailed chapter outline for the following research topic:

Topic: {topic}
Paper Type: {"Thesis" if paper_type == "thesis" else "Journal Paper"}

Please list the outline with main sections and subsections:"""

        result, _ = await self.llm.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
            system_prompt=system_prompt,
        )

        # 解析大纲
        outline = [
            line.strip()
            for line in result.split("\n")
            if line.strip() and (line.strip().startswith(("第", "Chapter", "1.", "2.", "3.", "4.", "5.", "6."))
)]
        return outline

    async def suggest_references(
        self,
        topic: str,
        keywords: List[str],
        language: str = "zh",
    ) -> List[Dict[str, str]]:
        """
        建议参考文献方向（不提供具体文献，而是研究方向）
        """
        system_prompt = self.SYSTEM_PROMPTS.get(
            f"academic_{language}",
            self.SYSTEM_PROMPTS["academic_zh"]
        )

        prompt = f"""基于以下研究主题和关键词，建议可以参考的文献研究方向：

主题：{topic}
关键词：{', '.join(keywords)}

请列出3-5个可以参考的研究方向或理论框架："""

        result, _ = await self.llm.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
            system_prompt=system_prompt,
        )

        # 简单解析
        suggestions = [
            {"direction": line.strip()}
            for line in result.split("\n")
            if line.strip() and len(line.strip()) > 10
        ]
        return suggestions[:5]

    async def check_logic(
        self,
        text: str,
        language: str = "zh",
    ) -> Dict[str, Any]:
        """
        检查逻辑连贯性
        """
        system_prompt = self.SYSTEM_PROMPTS.get(
            f"academic_{language}",
            self.SYSTEM_PROMPTS["academic_zh"]
        )

        if language == "zh":
            prompt = f"""请分析以下学术文本的逻辑连贯性，指出可能的问题并给出改进建议：

文本：
{text}

请从以下方面分析：
1. 论点是否清晰
2. 论证是否充分
3. 逻辑是否连贯
4. 结构是否合理

分析结果："""
        else:
            prompt = f"""Please analyze the logical coherence of the following academic text and provide suggestions for improvement:

Text:
{text}

Please analyze from the following aspects:
1. Clarity of arguments
2. Sufficiency of evidence
3. Logical coherence
4. Structural organization

Analysis:"""

        result, _ = await self.llm.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3,
            system_prompt=system_prompt,
        )

        return {
            "analysis": result,
            "score": 0.8,  # 模拟评分
            "suggestions": ["建议1", "建议2"],  # 从结果中提取
        }
