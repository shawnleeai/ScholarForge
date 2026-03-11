"""
多跳问答系统
处理需要多步推理的复杂问题
"""

import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

from .retrieval import HybridSearcher, QueryRewriter
from .reasoning import ChainBuilder, FactChecker, ReasoningChain

logger = logging.getLogger(__name__)


@dataclass
class MultiHopAnswer:
    """多跳问答结果"""
    question: str
    answer: str
    reasoning_chain: ReasoningChain
    sources: List[Dict]
    confidence: float
    explanation: str


class MultiHopQA:
    """多跳问答系统"""

    def __init__(
        self,
        llm_client,
        searcher: HybridSearcher,
        max_hops: int = 3
    ):
        """
        Args:
            llm_client: LLM客户端
            searcher: 混合检索器
            max_hops: 最大跳数
        """
        self.llm = llm_client
        self.searcher = searcher
        self.max_hops = max_hops

        self.query_rewriter = QueryRewriter(llm_client)
        self.chain_builder = ChainBuilder(llm_client)
        self.fact_checker = FactChecker(llm_client)

    async def answer(
        self,
        question: str,
        context: Optional[str] = None
    ) -> MultiHopAnswer:
        """
        回答多跳问题

        Args:
            question: 问题
            context: 可选上下文

        Returns:
            答案和推理过程
        """
        logger.info(f"Processing multi-hop question: {question}")

        # 步骤1: 重写查询
        rewritten = await self.query_rewriter.rewrite(
            question, context, strategy="decompose"
        )

        # 步骤2: 构建推理链
        async def retrieval_fn(query: str) -> List[Dict]:
            """检索函数"""
            results = self.searcher.search(query, top_k=5)
            return [
                {
                    "id": r.doc_id,
                    "content": r.content,
                    "metadata": r.metadata,
                    "score": r.hybrid_score
                }
                for r in results
            ]

        chain = await self.chain_builder.build_chain(
            question, retrieval_fn, max_steps=self.max_hops
        )

        # 步骤3: 验证答案
        all_sources = []
        for step in chain.steps:
            all_sources.extend(step.evidence)

        verification = await self.fact_checker.verify_answer(
            chain.final_answer or "", all_sources
        )

        # 步骤4: 生成解释
        explanation = self._generate_explanation(chain, verification)

        return MultiHopAnswer(
            question=question,
            answer=chain.final_answer or "未能生成答案",
            reasoning_chain=chain,
            sources=all_sources[:10],
            confidence=chain.overall_confidence * verification.get("average_confidence", 0.5),
            explanation=explanation
        )

    async def answer_with_follow_up(
        self,
        question: str,
        previous_qa: List[Dict],
        context: Optional[str] = None
    ) -> MultiHopAnswer:
        """
        回答追问（基于之前的问答历史）

        Args:
            question: 当前问题
            previous_qa: 之前的问答历史 [{"question": ..., "answer": ...}]
            context: 可选上下文
        """
        # 构建上下文
        qa_context = ""
        for qa in previous_qa[-3:]:  # 最近3轮
            qa_context += f"Q: {qa['question']}\nA: {qa['answer']}\n\n"

        full_context = f"{qa_context}\n{context or ''}"

        # 重写问题以消解指代
        rewritten_question = await self._resolve_coreference(
            question, qa_context
        )

        return await self.answer(rewritten_question, full_context)

    async def _resolve_coreference(
        self,
        question: str,
        context: str
    ) -> str:
        """消解指代词"""
        if not self.llm:
            return question

        prompt = f"""将问题中的指代词（如"它"、"这个"、"那个"）替换为具体实体。

上下文:
{context}

当前问题: {question}

重写后的问题:"""

        try:
            rewritten = await self.llm.generate(prompt)
            return rewritten.strip() or question
        except:
            return question

    def _generate_explanation(
        self,
        chain: ReasoningChain,
        verification: Dict
    ) -> str:
        """生成答案解释"""
        lines = ["## 推理过程", ""]

        for step in chain.steps:
            lines.append(f"**步骤 {step.step_number}**: {step.description}")
            lines.append(f"- 检索到 {len(step.evidence)} 条相关证据")
            lines.append(f"- 中间结论: {step.intermediate_answer[:100]}...")
            lines.append(f"- 置信度: {step.confidence:.2%}")
            lines.append("")

        lines.append("## 答案验证")
        lines.append(f"- 事实陈述数: {verification['total_claims']}")
        lines.append(f"- 有证据支持: {verification['supported']}")
        lines.append(f"- 无法确认: {verification['unsure']}")
        lines.append(f"- 整体可信度: {verification['average_confidence']:.2%}")

        if verification.get('verdict') == 'needs_review':
            lines.append("")
            lines.append("⚠️ 部分信息需要进一步验证")

        return "\n".join(lines)

    async def stream_answer(
        self,
        question: str,
        context: Optional[str] = None
    ):
        """
        流式返回答案（用于实时展示推理过程）
        """
        # 步骤1: 分解问题
        yield {"type": "status", "content": "正在分析问题..."}

        sub_questions = await self.chain_builder.decompose_question(question)
        yield {
            "type": "decomposition",
            "content": f"将问题分解为 {len(sub_questions)} 个子问题",
            "sub_questions": sub_questions
        }

        # 步骤2: 逐跳推理
        current_context = ""
        all_sources = []

        for i, sub_q in enumerate(sub_questions, 1):
            yield {"type": "status", "content": f"正在检索相关信息 (步骤 {i}/{len(sub_questions)})..."}

            # 检索
            results = self.searcher.search(sub_q, top_k=5)
            evidence = [
                {"id": r.doc_id, "content": r.content, "score": r.hybrid_score}
                for r in results
            ]
            all_sources.extend(evidence)

            yield {
                "type": "retrieval",
                "step": i,
                "evidence_count": len(evidence)
            }

            # 生成中间答案
            yield {"type": "status", "content": f"正在分析 (步骤 {i}/{len(sub_questions)})..."}

            intermediate = await self.chain_builder._generate_intermediate_answer(
                sub_q, evidence, current_context
            )
            current_context += f"\n{sub_q}: {intermediate}"

            yield {
                "type": "intermediate_answer",
                "step": i,
                "question": sub_q,
                "answer": intermediate
            }

        # 步骤3: 生成最终答案
        yield {"type": "status", "content": "正在生成最终答案..."}

        final_answer = await self.chain_builder._synthesize_answer(
            question,
            []  # 实际应该传入steps
        )

        # 验证
        verification = await self.fact_checker.verify_answer(final_answer, all_sources)

        yield {
            "type": "final_answer",
            "content": final_answer,
            "confidence": verification.get("average_confidence", 0.5),
            "sources": list(set(s["id"] for s in all_sources))[:5]
        }

    def get_similar_questions(
        self,
        question: str,
        top_k: int = 3
    ) -> List[str]:
        """
        生成类似的问题（用于扩展检索）
        """
        # 基于关键词的变体生成
        variants = [question]

        # 句式转换
        if "什么是" in question:
            variants.append(question.replace("什么是", "请解释"))
        if "如何" in question:
            variants.append(question.replace("如何", "怎样"))

        # 添加限定词
        variants.append(f"详细说明: {question}")
        variants.append(f"学术角度分析: {question}")

        return variants[:top_k]
