"""
Smart Literature Reading Service
智能文献阅读服务 - AI驱动的文献深度理解与对话
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from .stepfun_client import get_stepfun_client, StepFunModel


class LiteratureReadingService:
    """智能文献阅读服务"""

    def __init__(self):
        self.stepfun = get_stepfun_client()

    # ==================== PDF多模态解析 ====================

    async def analyze_pdf_page(
        self,
        page_image: bytes,
        page_number: int,
        extract_mode: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        使用多模态模型分析PDF页面

        Args:
            page_image: 页面图片数据
            page_number: 页码
            extract_mode: 提取模式 (comprehensive/detailed/figures_only)
        """
        prompts = {
            "comprehensive": """请详细分析这页学术论文，提取以下信息并以JSON格式返回：
{
    "page_type": "页面类型(title/abstract/introduction/method/results/discussion/references)",
    "main_content": "主要内容摘要(200字以内)",
    "key_findings": ["关键发现1", "关键发现2"],
    "methodology": "研究方法描述",
    "figures_tables": [{"type": "图/表", "description": "描述", "key_data": "关键数据"}],
    "citations": ["引用1", "引用2"],
    "technical_terms": [{"term": "术语", "context": "上下文"}],
    "research_questions": ["研究问题"],
    "limitations_mentioned": ["局限性"],
    "future_work": ["未来工作建议"]
}""",
            "detailed": "请详细描述这页论文的所有内容，包括文字、图表、公式等。",
            "figures_only": "请识别并描述这页中的所有图表，提取关键数据。"
        }

        response = await self.stepfun.vision_analysis(
            image_data=page_image,
            prompt=prompts.get(extract_mode, prompts["comprehensive"]),
            model="step-1o",
            detail="high"
        )

        content = response['choices'][0]['message']['content']

        # 尝试解析JSON
        try:
            # 提取JSON部分
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            analysis = json.loads(json_str.strip())
        except:
            # 如果解析失败，返回原始内容
            analysis = {"raw_content": content}

        return {
            "page_number": page_number,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def batch_analyze_pdf(
        self,
        pages: List[Dict[str, Any]],  # [{"image": bytes, "page_number": int}]
        paper_id: str
    ) -> Dict[str, Any]:
        """
        批量分析PDF所有页面
        """
        results = []

        for page in pages:
            try:
                result = await self.analyze_pdf_page(
                    page_image=page["image"],
                    page_number=page["page_number"]
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "page_number": page["page_number"],
                    "error": str(e)
                })

        # 生成整体摘要
        summary = await self._generate_paper_summary(results)

        return {
            "paper_id": paper_id,
            "total_pages": len(pages),
            "analyzed_pages": len([r for r in results if "error" not in r]),
            "page_analyses": results,
            "summary": summary
        }

    async def _generate_paper_summary(
        self,
        page_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """基于页面分析生成论文整体摘要"""

        # 提取所有关键信息
        all_findings = []
        all_methods = []
        all_citations = []

        for page in page_analyses:
            if "analysis" in page:
                analysis = page["analysis"]
                if isinstance(analysis, dict):
                    all_findings.extend(analysis.get("key_findings", []))
                    if "methodology" in analysis:
                        all_methods.append(analysis["methodology"])
                    all_citations.extend(analysis.get("citations", []))

        prompt = f"""基于以下论文页面分析结果，生成一个结构化的论文摘要：

关键发现:
{json.dumps(all_findings, ensure_ascii=False)}

研究方法:
{json.dumps(all_methods, ensure_ascii=False)}

引用文献:
{json.dumps(all_citations[:20], ensure_ascii=False)}

请输出JSON格式:
{{
    "title": "论文标题(推断或提取)",
    "core_contribution": "核心贡献(100字以内)",
    "research_question": "研究问题",
    "methodology_summary": "方法论总结",
    "key_results": ["主要结果1", "主要结果2"],
    "significance": "研究意义",
    "novelty_score": 0-10,  // 创新性评分
    "relevance_score": 0-10  // 相关性评分
}}"""

        response = await self.stepfun.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="step-1-128k"
        )

        try:
            content = response['choices'][0]['message']['content']
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str.strip())
        except:
            return {"summary": content}

    # ==================== 对话式文献问答 ====================

    async def chat_about_paper(
        self,
        question: str,
        paper_context: str,
        chat_history: List[Dict[str, str]] = None,
        stream: bool = False
    ) -> str:
        """
        与AI对话讨论论文

        Args:
            question: 用户问题
            paper_context: 论文内容上下文
            chat_history: 历史对话
            stream: 是否流式输出
        """
        system_prompt = """你是一位专业的学术文献助手，擅长深度理解论文并回答研究相关问题。

你的能力:
1. 解释复杂的学术概念和方法
2. 分析论文的创新点和局限性
3. 对比不同研究的异同
4. 帮助发现研究机会
5. 用通俗易懂的语言解释专业内容

回答原则:
- 基于论文内容回答，不臆测
- 如果信息不足，明确说明
- 适当引用论文中的具体部分
- 保持客观和学术性"""

        messages = [{"role": "system", "content": system_prompt}]

        # 添加上下文
        messages.append({
            "role": "system",
            "content": f"论文内容:\n{paper_context[:30000]}"  # 限制上下文长度
        })

        # 添加历史对话
        if chat_history:
            for msg in chat_history[-5:]:  # 只保留最近5轮
                messages.append(msg)

        # 添加当前问题
        messages.append({"role": "user", "content": question})

        if stream:
            result = ""
            async for chunk in self.stepfun.chat_completion_stream(
                messages=messages,
                model="step-1-128k"
            ):
                result += chunk
            return result
        else:
            response = await self.stepfun.chat_completion(
                messages=messages,
                model="step-1-128k"
            )
            return response['choices'][0]['message']['content']

    # ==================== 关键信息提取 ====================

    async def extract_key_information(
        self,
        paper_text: str,
        extraction_type: str = "all"
    ) -> Dict[str, Any]:
        """
        提取论文关键信息

        extraction_type:
        - all: 提取所有类型信息
        - contributions: 主要贡献
        - methods: 研究方法
        - results: 实验结果
        - limitations: 研究局限
        - future_work: 未来工作
        """
        extraction_prompts = {
            "all": """请从这篇论文中提取所有关键信息，包括：
1. 研究背景和动机
2. 核心贡献（3-5条）
3. 研究方法详细描述
4. 实验设计和数据集
5. 主要结果和指标
6. 研究局限性和不足
7. 未来研究方向
8. 关键术语和定义

输出为结构化JSON格式。""",
            "contributions": "提取论文的核心贡献，按重要性排序。",
            "methods": "详细描述论文使用的方法、模型、算法。",
            "results": "提取所有实验结果、性能指标、对比数据。",
            "limitations": "识别论文中明确提到或隐含的研究局限。",
            "future_work": "提取作者建议的未来研究方向。"
        }

        prompt = f"""{extraction_prompts.get(extraction_type, extraction_prompts['all'])}

论文内容:
{paper_text[:20000]}

请输出JSON格式。"""

        response = await self.stepfun.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="step-1-128k"
        )

        content = response['choices'][0]['message']['content']

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str.strip())
        except:
            return {"extraction": content}

    # ==================== 对比分析 ====================

    async def compare_papers(
        self,
        paper1_text: str,
        paper2_text: str,
        comparison_focus: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        对比两篇论文

        comparison_focus:
        - comprehensive: 全面对比
        - methodology: 方法对比
        - results: 结果对比
        - contributions: 贡献对比
        """
        focus_prompts = {
            "comprehensive": "从研究问题、方法、结果、贡献等方面全面对比这两篇论文。",
            "methodology": "重点对比两篇论文的研究方法，分析各自的优缺点。",
            "results": "对比两篇论文的实验结果和性能指标。",
            "contributions": "对比两篇论文的核心贡献和创新点。"
        }

        prompt = f"""{focus_prompts.get(comparison_focus, focus_prompts['comprehensive'])}

论文1:
{paper1_text[:15000]}

论文2:
{paper2_text[:15000]}

请输出JSON格式，包含:
{{
    "similarities": ["相似点1", "相似点2"],
    "differences": ["差异点1", "差异点2"],
    "strengths_comparison": "优势对比分析",
    "limitations_comparison": "局限对比分析",
    "recommendation": "推荐阅读哪篇及原因"
}}"""

        response = await self.stepfun.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="step-1-256k"  # 使用长上下文模型
        )

        content = response['choices'][0]['message']['content']

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str.strip())
        except:
            return {"comparison": content}

    # ==================== 研究机会识别 ====================

    async def identify_research_gaps(
        self,
        paper_text: str,
        related_papers: List[str] = None
    ) -> Dict[str, Any]:
        """
        基于论文识别研究空白和机会
        """
        related_context = ""
        if related_papers:
            related_context = "相关研究:\n" + "\n\n".join(related_papers[:5])

        prompt = f"""基于以下论文内容，识别潜在的研究空白和未来机会：

{paper_text[:20000]}

{related_context}

请分析并输出JSON格式:
{{
    "identified_gaps": [
        {{
            "gap_description": "研究空白描述",
            "significance": "重要性(高/中/低)",
            "feasibility": "可行性评估",
            "suggested_approach": "建议的研究方法"
        }}
    ],
    "extension_opportunities": ["扩展机会1", "扩展机会2"],
    "method_improvements": ["方法改进建议"],
    "application_areas": ["潜在应用领域"],
    "interdisciplinary_connections": ["跨学科联系"]
}}"""

        response = await self.stepfun.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="step-1-128k"
        )

        content = response['choices'][0]['message']['content']

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str.strip())
        except:
            return {"gaps": content}


# 单例
_literature_reading_service: Optional[LiteratureReadingService] = None


def get_literature_reading_service() -> LiteratureReadingService:
    """获取文献阅读服务单例"""
    global _literature_reading_service
    if _literature_reading_service is None:
        _literature_reading_service = LiteratureReadingService()
    return _literature_reading_service
