"""
推理链构建器
实现多跳推理中的推理链构建
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class StepType(str, Enum):
    """推理步骤类型"""
    RETRIEVAL = "retrieval"  # 检索步骤
    REASONING = "reasoning"  # 推理步骤
    SYNTHESIS = "synthesis"  # 综合步骤
    VERIFICATION = "verification"  # 验证步骤


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_number: int
    step_type: StepType
    description: str  # 步骤描述
    query: str  # 当前查询
    evidence: List[Dict] = field(default_factory=list)  # 证据
    intermediate_answer: Optional[str] = None  # 中间答案
    confidence: float = 0.0  # 置信度
    metadata: Dict = field(default_factory=dict)


@dataclass
class ReasoningChain:
    """推理链"""
    original_question: str
    steps: List[ReasoningStep]
    final_answer: Optional[str] = None
    overall_confidence: float = 0.0
    reasoning_path: List[str] = field(default_factory=list)


class ChainBuilder:
    """推理链构建器"""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def decompose_question(
        self,
        question: str,
        context: Optional[str] = None
    ) -> List[str]:
        """
        将复杂问题分解为子问题

        Args:
            question: 原始问题
            context: 可选上下文

        Returns:
            子问题列表
        """
        if not self.llm:
            # 简单分解：按问号分割
            return [q.strip() for q in question.split('?') if q.strip()]

        prompt = f"""将以下复杂问题分解为多个简单的子问题。

原始问题: {question}
{f"上下文: {context}" if context else ""}

分解要求:
1. 每个子问题应该可以独立回答
2. 子问题之间可以有依赖关系
3. 回答所有子问题应该能完整回答原始问题
4. 分解为2-4个子问题

请按以下格式输出:
子问题1: [第一个子问题]
子问题2: [第二个子问题]
..."""

        try:
            response = await self.llm.generate(prompt)
            return self._parse_sub_questions(response)
        except Exception as e:
            logger.error(f"Question decomposition failed: {e}")
            return [question]

    def _parse_sub_questions(self, response: str) -> List[str]:
        """解析子问题"""
        sub_questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('子问题') or line.startswith('Q'):
                # 提取冒号后的内容
                if ':' in line:
                    q = line.split(':', 1)[1].strip()
                    if q:
                        sub_questions.append(q)
                elif '.' in line:
                    q = line.split('.', 1)[1].strip()
                    if q:
                        sub_questions.append(q)

        return sub_questions if sub_questions else [response.strip()]

    async def build_chain(
        self,
        question: str,
        retrieval_fn: callable,
        max_steps: int = 5
    ) -> ReasoningChain:
        """
        构建推理链

        Args:
            question: 问题
            retrieval_fn: 检索函数 (query) -> List[Dict]
            max_steps: 最大步骤数

        Returns:
            推理链
        """
        chain = ReasoningChain(
            original_question=question,
            steps=[]
        )

        # 步骤1: 问题分解
        sub_questions = await self.decompose_question(question)

        # 为每个子问题构建推理步骤
        current_context = ""

        for i, sub_q in enumerate(sub_questions[:max_steps], 1):
            # 检索证据
            evidence = await retrieval_fn(sub_q)

            # 生成中间答案
            intermediate_answer = await self._generate_intermediate_answer(
                sub_q, evidence, current_context
            )

            step = ReasoningStep(
                step_number=i,
                step_type=StepType.REASONING,
                description=f"回答: {sub_q}",
                query=sub_q,
                evidence=evidence,
                intermediate_answer=intermediate_answer,
                confidence=self._calculate_confidence(evidence)
            )

            chain.steps.append(step)
            current_context += f"\n{sub_q}: {intermediate_answer}"

        # 生成最终答案
        chain.final_answer = await self._synthesize_answer(
            question, chain.steps
        )
        chain.overall_confidence = sum(
            s.confidence for s in chain.steps
        ) / len(chain.steps) if chain.steps else 0

        return chain

    async def _generate_intermediate_answer(
        self,
        question: str,
        evidence: List[Dict],
        context: str
    ) -> str:
        """生成中间答案"""
        if not self.llm:
            # 简单拼接证据
            return " ".join([e.get('content', '')[:200] for e in evidence[:2]])

        # 构建证据文本
        evidence_text = "\n\n".join([
            f"证据{i+1}: {e.get('content', '')}"
            for i, e in enumerate(evidence[:3])
        ])

        prompt = f"""基于以下证据回答问题。

{f"上下文: {context}" if context else ""}

{evidence_text}

问题: {question}

请给出简洁准确的答案:"""

        try:
            return await self.llm.generate(prompt)
        except Exception as e:
            logger.error(f"Intermediate answer generation failed: {e}")
            return "未能生成答案"

    def _calculate_confidence(self, evidence: List[Dict]) -> float:
        """计算置信度"""
        if not evidence:
            return 0.0

        # 基于证据分数和数量计算
        avg_score = sum(e.get('score', 0) for e in evidence) / len(evidence)
        coverage = min(len(evidence) / 3, 1.0)  # 假设3个证据是理想的

        return avg_score * coverage

    async def _synthesize_answer(
        self,
        original_question: str,
        steps: List[ReasoningStep]
    ) -> str:
        """综合所有中间答案生成最终答案"""
        if not self.llm:
            # 简单拼接
            return " ".join([
                s.intermediate_answer for s in steps if s.intermediate_answer
            ])

        # 构建中间答案文本
        steps_text = "\n\n".join([
            f"步骤{s.step_number}: {s.description}\n答案: {s.intermediate_answer}"
            for s in steps
        ])

        prompt = f"""综合以下推理步骤的答案，回答原始问题。

原始问题: {original_question}

推理过程:
{steps_text}

请给出一个完整、连贯的最终答案。确保答案直接回应原始问题:"""

        try:
            return await self.llm.generate(prompt)
        except Exception as e:
            logger.error(f"Answer synthesis failed: {e}")
            return "未能综合答案"

    def get_chain_explanation(self, chain: ReasoningChain) -> str:
        """获取推理链的可解释文本"""
        lines = [f"问题: {chain.original_question}\n"]
        lines.append("推理过程:\n")

        for step in chain.steps:
            lines.append(f"步骤 {step.step_number}: {step.description}")
            lines.append(f"  检索到 {len(step.evidence)} 条证据")
            lines.append(f"  中间答案: {step.intermediate_answer[:100]}...")
            lines.append(f"  置信度: {step.confidence:.2f}\n")

        lines.append(f"\n最终答案: {chain.final_answer}")
        lines.append(f"整体置信度: {chain.overall_confidence:.2f}")

        return "\n".join(lines)
