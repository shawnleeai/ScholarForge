
AI服务客户端
用于调用AI服务生成选题建议和开题报告
"""

import os
import json
import aiohttp
from typing import List, Dict, Any, Optional


class AIClient:
    """AI服务客户端"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("AI_SERVICE_URL", "http://localhost:8004")
        self.api_key = os.getenv("AI_SERVICE_API_KEY", "")

    async def _call_ai(self, endpoint: str, payload: dict) -> dict:
        """调用AI服务"""
        url = f"{self.base_url}/api/v1/ai/{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    # 如果AI服务不可用，返回None
                    return None

    async def generate_topic_suggestions(
        self,
        field: str,
        keywords: List[str],
        interests: List[str],
        degree_level: str,
        num_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        使用AI生成选题建议

        Args:
            field: 研究领域
            keywords: 关键词列表
            interests: 研究兴趣
            degree_level: 学位级别
            num_suggestions: 建议数量

        Returns:
            选题建议列表
        """
        # 构建提示词
        keywords_str = ", ".join(keywords) if keywords else "相关领域"
        interests_str = ", ".join(interests) if interests else ""

        prompt = f"""你是一个学术研究选题助手。请基于以下信息生成{num_suggestions}个高质量的学术研究选题建议：

研究领域：{field}
关键词：{keywords_str}
研究兴趣：{interests_str}
学位级别：{degree_level}

对于每个选题建议，请提供以下信息（JSON格式）：
- title: 选题标题（简洁明确，不超过30字）
- description: 选题描述（详细说明研究内容和意义，100-150字）
- keywords: 关键词列表（3-5个）
- field: 所属领域
- feasibility_score: 可行性评分（0-100）
- feasibility_level: 可行性等级（high/medium/low/risky）
- research_gaps: 研究空白点列表
- estimated_duration_months: 预计完成时间（月）
- risks: 潜在风险列表
- mitigation_strategies: 风险应对策略

请确保选题：
1. 具有学术价值和创新性
2. 符合{degree_level}学位要求
3. 研究范围适中，可在一段时间内完成
4. 有明确的研究空白和创新点

请以JSON数组格式返回结果。"""

        result = await self._call_ai("complete", {
            "prompt": prompt,
            "max_tokens": 2000,
            "temperature": 0.7,
        })

        if result and result.get("data"):
            try:
                # 尝试解析AI返回的内容
                content = result["data"].get("content", "")
                # 提取JSON部分
                start_idx = content.find("[")
                end_idx = content.rfind("]")
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx + 1]
                    suggestions = json.loads(json_str)
                    return suggestions if isinstance(suggestions, list) else []
            except (json.JSONDecodeError, Exception) as e:
                print(f"解析AI返回结果失败: {e}")
                return []

        return []

    async def analyze_feasibility(
        self,
        topic: str,
        description: str,
        field: str,
        degree_level: str
    ) -> Optional[Dict[str, Any]]:
        """
        使用AI进行可行性分析

        Args:
            topic: 选题标题
            description: 选题描述
            field: 研究领域
            degree_level: 学位级别

        Returns:
            可行性分析结果
        """
        prompt = f"""你是一个学术研究可行性分析专家。请对以下选题进行深度可行性分析：

选题标题：{topic}
选题描述：{description}
研究领域：{field}
学位级别：{degree_level}

请提供以下分析（JSON格式）：
{{
    "overall_score": 综合可行性评分（0-100）,
    "level": 可行性等级（high/medium/low/risky）,
    "academic_value_score": 学术价值评分（0-100）,
    "innovation_score": 创新性评分（0-100）,
    "resource_availability_score": 资源可获取性评分（0-100）,
    "time_feasibility_score": 时间可行性评分（0-100）,
    "risk_score": 风险评估分数（0-100，分数越高风险越大）,
    "strengths": ["优势1", "优势2", ...],
    "weaknesses": ["劣势1", "劣势2", ...],
    "opportunities": ["机会1", "机会2", ...],
    "threats": ["威胁1", "威胁2", ...],
    "resource_requirements": [
        {"resource_type": "数据", "description": "...", "availability": "easy/medium/hard"},
        {"resource_type": "工具", "description": "...", "availability": "easy/medium/hard"},
        {"resource_type": "专业知识", "description": "...", "availability": "easy/medium/hard"}
    ],
    "timeline": [
        {"phase": "阶段名称", "tasks": ["任务1", "任务2"], "duration_weeks": 4, "dependencies": []}
    ],
    "recommendations": ["建议1", "建议2", ...],
    "research_gaps": [
        {"gap_type": "method/theory/application", "description": "...", "significance": "高/中/低"}
    ]
}}"""

        result = await self._call_ai("complete", {
            "prompt": prompt,
            "max_tokens": 2500,
            "temperature": 0.5,
        })

        if result and result.get("data"):
            try:
                content = result["data"].get("content", "")
                # 提取JSON部分
                start_idx = content.find("{")
                end_idx = content.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx + 1]
                    analysis = json.loads(json_str)
                    return analysis
            except (json.JSONDecodeError, Exception) as e:
                print(f"解析AI返回结果失败: {e}")
                return None

        return None

    async def generate_proposal(
        self,
        topic: str,
        field: str,
        degree_level: str,
        university: Optional[str] = None,
        supervisor: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用AI生成开题报告

        Args:
            topic: 选题
            field: 研究领域
            degree_level: 学位级别
            university: 学校（可选）
            supervisor: 导师（可选）

        Returns:
            开题报告内容
        """
        university_info = f"\n学校：{university}" if university else ""
        supervisor_info = f"\n导师：{supervisor}" if supervisor else ""

        prompt = f"""你是一个专业的学术研究开题报告撰写专家。请为以下选题生成一份详细的开题报告大纲：

选题：{topic}
研究领域：{field}
学位级别：{degree_level}{university_info}{supervisor_info}

请生成以下章节（JSON格式）：
{{
    "title": "选题标题",
    "background": "研究背景（800-1000字，包括研究缘起、研究意义、国内外研究现状）",
    "objectives": "研究目标（包括总体目标和具体目标）",
    "research_questions": [
        {"id": "rq1", "question": "研究问题1", "sub_questions": ["子问题1", "子问题2"]},
        {"id": "rq2", "question": "研究问题2", "sub_questions": []}
    ],
    "research_methods": [
        {"method_type": "文献研究法", "description": "...", "data_source": "...", "analysis_approach": "..."},
        {"method_type": "实证研究法", "description": "...", "data_source": "...", "analysis_approach": "..."}
    ],
    "expected_outcomes": ["预期成果1", "预期成果2", "预期成果3"],
    "innovation_points": ["创新点1", "创新点2", "创新点3"],
    "timeline": [
        {"phase": "第一阶段", "task": "文献综述", "duration": "第1-2月"},
        {"phase": "第二阶段", "task": "研究设计", "duration": "第3月"},
        {"phase": "第三阶段", "task": "数据收集", "duration": "第4-5月"},
        {"phase": "第四阶段", "task": "数据分析", "duration": "第6月"},
        {"phase": "第五阶段", "task": "论文撰写", "duration": "第7-8月"}
    ],
    "references": ["参考文献1", "参考文献2", "参考文献3"],
    "total_words": 预估总字数
}}"""

        result = await self._call_ai("complete", {
            "prompt": prompt,
            "max_tokens": 3000,
            "temperature": 0.6,
        })

        if result and result.get("data"):
            try:
                content = result["data"].get("content", "")
                # 提取JSON部分
                start_idx = content.find("{")
                end_idx = content.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx + 1]
                    proposal = json.loads(json_str)
                    return proposal
            except (json.JSONDecodeError, Exception) as e:
                print(f"解析AI返回结果失败: {e}")
                return None

        return None

    async def analyze_trends(
        self,
        field: str,
        keywords: List[str],
        years: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        使用AI分析研究趋势

        Args:
            field: 研究领域
            keywords: 关键词
            years: 分析年数

        Returns:
            趋势分析结果
        """
        keywords_str = ", ".join(keywords) if keywords else field

        prompt = f"""你是一个学术研究趋势分析专家。请分析以下研究领域的发展趋势：

研究领域：{field}
关键词：{keywords_str}
分析年限：近{years}年

请提供以下分析（JSON格式）：
{{
    "trends": [
        {
            "keyword": "关键词1",
            "trend_data": [
                {"year": 2020, "count": 100, "growth_rate": 10.5},
                {"year": 2021, "count": 120, "growth_rate": 20.0},
                ...
            ],
            "current_hotness": 0.85,
            "predicted_trend": "rising/stable/declining",
            "related_keywords": ["相关词1", "相关词2", "相关词3"]
        }
    ],
    "hot_topics": ["热门话题1", "热门话题2", "热门话题3"],
    "emerging_topics": ["新兴话题1", "新兴话题2"],
    "declining_topics": ["衰退话题1", "衰退话题2"]
}}"""

        result = await self._call_ai("complete", {
            "prompt": prompt,
            "max_tokens": 2000,
            "temperature": 0.5,
        })

        if result and result.get("data"):
            try:
                content = result["data"].get("content", "")
                start_idx = content.find("{")
                end_idx = content.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx + 1]
                    trends = json.loads(json_str)
                    return trends
            except (json.JSONDecodeError, Exception) as e:
                print(f"解析AI返回结果失败: {e}")
                return None

        return None


# 全局AI客户端实例
ai_client = AIClient()
