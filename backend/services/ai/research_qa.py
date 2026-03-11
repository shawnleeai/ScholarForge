"""
研究问题专门回答服务
针对不同类型的研究问题提供专门的回答逻辑
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .conversation_models import ResearchQuestion, ResearchQuestionType, Citation
from .rag_engine import RAGEngine, RetrievalResult


class AnswerConfidence(str, Enum):
    """答案置信度级别"""
    HIGH = "high"           # 高置信度（有明确证据支持）
    MEDIUM = "medium"       # 中等置信度（有部分证据）
    LOW = "low"             # 低置信度（证据不足或存在争议）
    INSUFFICIENT = "insufficient"  # 证据不足无法回答


class ConsensusLevel(str, Enum):
    """学术界共识度"""
    STRONG = "strong"       # 强共识（>80%研究一致）
    MODERATE = "moderate"   # 中等共识（60-80%一致）
    MIXED = "mixed"         # 混合（40-60%分歧）
    CONTROVERSIAL = "controversial"  # 争议（<40%一致）
    UNKNOWN = "unknown"     # 未知


@dataclass
class ResearchAnswer:
    """研究问题答案"""
    answer: str
    confidence: AnswerConfidence
    confidence_score: float  # 0-1
    consensus_level: ConsensusLevel
    supporting_evidence: List[Citation]
    counter_evidence: List[Citation]  # 反对证据
    reasoning: str  # 推理过程
    limitations: List[str]  # 答案局限性
    suggestions: List[str]  # 进一步研究建议
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "consensus_level": self.consensus_level.value,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "counter_evidence": [e.to_dict() for e in self.counter_evidence],
            "reasoning": self.reasoning,
            "limitations": self.limitations,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }


class ResearchQAService:
    """
    研究问题问答服务
    针对不同类型的研究问题提供专门的回答策略
    """

    def __init__(self, rag_engine: Optional[RAGEngine] = None):
        self.rag_engine = rag_engine

    async def answer(
        self,
        question: str,
        question_type: Optional[ResearchQuestionType] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ResearchAnswer:
        """
        回答研究问题

        Args:
            question: 研究问题
            question_type: 问题类型（自动检测如果未提供）
            context: 上下文信息

        Returns:
            ResearchAnswer: 结构化答案
        """
        # 1. 检测问题类型
        if question_type is None:
            question_type = self._detect_question_type(question)

        # 2. 检索相关文献
        retrieved_docs = []
        if self.rag_engine:
            retrieved_docs = await self.rag_engine.retrieve(
                query=question,
                top_k=10,
                context=context
            )

        # 3. 根据问题类型选择回答策略
        if question_type == ResearchQuestionType.YES_NO:
            return await self._answer_yes_no(question, retrieved_docs)
        elif question_type == ResearchQuestionType.HOW:
            return await self._answer_how(question, retrieved_docs)
        elif question_type == ResearchQuestionType.WHY:
            return await self._answer_why(question, retrieved_docs)
        elif question_type == ResearchQuestionType.WHAT:
            return await self._answer_what(question, retrieved_docs)
        elif question_type == ResearchQuestionType.COMPARE:
            return await self._answer_compare(question, retrieved_docs)
        else:
            return await self._answer_general(question, retrieved_docs)

    def _detect_question_type(self, question: str) -> ResearchQuestionType:
        """自动检测问题类型"""
        question_lower = question.lower()

        # 是/否问题模式
        yes_no_patterns = [
            r'^(是|是否|能否|可不可以|有没有|能否|会不会|是不是)',
            r'(吗\?|吗？|么\?|么？)$',
            r'^(does|is|are|can|could|would|will|has|have|should)\s',
            r'(true|false|yes|no)\?',
        ]
        for pattern in yes_no_patterns:
            if re.search(pattern, question_lower):
                return ResearchQuestionType.YES_NO

        # 如何/方法问题
        how_patterns = [
            r'(如何|怎样|怎么|什么样|什么方法|什么方式|怎么做|如何实现)',
            r'^(how|what\s+is\s+the\s+best\s+way|what\s+are\s+the\s+steps)',
        ]
        for pattern in how_patterns:
            if re.search(pattern, question_lower):
                return ResearchQuestionType.HOW

        # 为什么/因果问题
        why_patterns = [
            r'(为什么|为何|什么原因|什么因素|怎么解释)',
            r'^(why|what\s+causes|what\s+are\s+the\s+reasons)',
        ]
        for pattern in why_patterns:
            if re.search(pattern, question_lower):
                return ResearchQuestionType.WHY

        # 对比问题
        compare_patterns = [
            r'(对比|比较|区别|差异|优劣|vs|versus|区别在哪)',
            r'(difference\s+between|compare|versus|vs\.|compared\s+to)',
        ]
        for pattern in compare_patterns:
            if re.search(pattern, question_lower):
                return ResearchQuestionType.COMPARE

        # 是什么/定义问题
        what_patterns = [
            r'(是什么|什么是|定义|概念|含义|意思)',
            r'^(what\s+is|what\s+are|define|definition\s+of)',
        ]
        for pattern in what_patterns:
            if re.search(pattern, question_lower):
                return ResearchQuestionType.WHAT

        return ResearchQuestionType.GENERAL

    async def _answer_yes_no(
        self,
        question: str,
        docs: List[RetrievalResult]
    ) -> ResearchAnswer:
        """
        回答是/否问题

        分析支持/反对的文献，给出置信度和共识度
        """
        # 分析文献立场
        supporting = []
        opposing = []
        uncertain = []

        for doc in docs:
            # 这里应该使用更复杂的NLP分析
            # 简化版本：基于关键词判断
            content_lower = doc.content.lower()

            # 检查明确的肯定/否定表达
            positive_signals = ['yes', '是', '确实', '显著', 'effective', 'positive', 'beneficial']
            negative_signals = ['no', '否', '不是', '不显著', 'ineffective', 'negative', 'no effect']

            pos_count = sum(1 for s in positive_signals if s in content_lower)
            neg_count = sum(1 for s in negative_signals if s in content_lower)

            if pos_count > neg_count:
                supporting.append(doc)
            elif neg_count > pos_count:
                opposing.append(doc)
            else:
                uncertain.append(doc)

        # 计算共识度
        total = len(supporting) + len(opposing)
        if total == 0:
            consensus = ConsensusLevel.UNKNOWN
            confidence = AnswerConfidence.INSUFFICIENT
            answer = "根据现有文献，无法确定该问题的答案。"
        else:
            support_ratio = len(supporting) / total

            if support_ratio > 0.8:
                consensus = ConsensusLevel.STRONG
                answer = "是的，现有研究强烈支持这一观点。"
                confidence = AnswerConfidence.HIGH
            elif support_ratio > 0.6:
                consensus = ConsensusLevel.MODERATE
                answer = "是的，大多数研究支持这一观点，但仍有部分研究持不同意见。"
                confidence = AnswerConfidence.MEDIUM
            elif support_ratio > 0.4:
                consensus = ConsensusLevel.MIXED
                answer = "现有研究对此存在分歧，尚无明确结论。"
                confidence = AnswerConfidence.LOW
            elif support_ratio > 0.2:
                consensus = ConsensusLevel.MIXED
                answer = "现有研究对此存在分歧，部分研究不支持这一观点。"
                confidence = AnswerConfidence.LOW
            else:
                consensus = ConsensusLevel.CONTROVERSIAL
                answer = "不，大多数研究不支持这一观点。"
                confidence = AnswerConfidence.MEDIUM

        # 构建推理过程
        reasoning_parts = []
        reasoning_parts.append(f"分析了{len(docs)}篇相关文献。")
        if supporting:
            reasoning_parts.append(f"{len(supporting)}篇文献支持该观点。")
        if opposing:
            reasoning_parts.append(f"{len(opposing)}篇文献提出反对证据或不同观点。")

        return ResearchAnswer(
            answer=answer,
            confidence=confidence,
            confidence_score=support_ratio if total > 0 else 0.0,
            consensus_level=consensus,
            supporting_evidence=[doc.to_citation() for doc in supporting[:3]],
            counter_evidence=[doc.to_citation() for doc in opposing[:3]],
            reasoning=" ".join(reasoning_parts),
            limitations=[
                "基于有限文献的分析",
                "可能遗漏最新研究",
                "文献质量未做严格筛选"
            ],
            suggestions=[
                "阅读原始文献获取更详细信息",
                "关注该领域的最新研究进展",
                "考虑研究的上下文和边界条件"
            ],
            metadata={
                "total_docs": len(docs),
                "supporting_count": len(supporting),
                "opposing_count": len(opposing),
                "uncertain_count": len(uncertain),
            }
        )

    async def _answer_how(
        self,
        question: str,
        docs: List[RetrievalResult]
    ) -> ResearchAnswer:
        """
        回答"如何"问题（方法、步骤）

        综合多篇文献的方法论信息
        """
        # 提取方法论信息
        methods = []
        for doc in docs:
            # 简化处理：提取包含方法关键词的片段
            content = doc.content
            # 这里应该使用更复杂的提取逻辑
            if any(kw in content.lower() for kw in ['method', 'approach', 'framework', 'procedure', '步骤', '方法']):
                methods.append({
                    "source": doc,
                    "method_snippet": content[:200]
                })

        # 综合方法
        if methods:
            answer = f"基于{len(methods)}篇文献，该问题的主要解决方法包括：\n\n"
            for i, m in enumerate(methods[:5], 1):
                answer += f"{i}. {m['source'].title}\n   {m['method_snippet'][:100]}...\n\n"
            confidence = AnswerConfidence.MEDIUM if len(methods) >= 3 else AnswerConfidence.LOW
            confidence_score = min(0.7, 0.3 + len(methods) * 0.1)
        else:
            answer = "现有文献中未找到明确的方法论描述。"
            confidence = AnswerConfidence.INSUFFICIENT
            confidence_score = 0.0

        return ResearchAnswer(
            answer=answer,
            confidence=confidence,
            confidence_score=confidence_score,
            consensus_level=ConsensusLevel.MODERATE if len(methods) >= 3 else ConsensusLevel.UNKNOWN,
            supporting_evidence=[m["source"].to_citation() for m in methods[:3]],
            counter_evidence=[],
            reasoning=f"从{len(docs)}篇文献中提取方法论信息，找到{len(methods)}篇相关描述。",
            limitations=[
                "方法论描述可能不完整",
                "不同研究的具体实施细节可能不同"
            ],
            suggestions=[
                "查看原始文献的Methodology章节",
                "考虑方法的适用性和可重复性",
                "关注样本量和实验设计"
            ],
            metadata={"methods_found": len(methods)}
        )

    async def _answer_why(
        self,
        question: str,
        docs: List[RetrievalResult]
    ) -> ResearchAnswer:
        """
        回答"为什么"问题（因果、原因）

        分析文献中的因果解释和机制
        """
        # 提取因果解释
        explanations = []
        causal_keywords = ['because', 'due to', 'caused by', 'reason', 'factor', 'mechanism',
                          '因为', '由于', '导致', '原因', '因素', '机制']

        for doc in docs:
            content = doc.content
            if any(kw in content.lower() for kw in causal_keywords):
                explanations.append({
                    "source": doc,
                    "explanation": content[:250]
                })

        if explanations:
            answer = f"基于文献分析，该现象的主要原因包括：\n\n"
            for i, e in enumerate(explanations[:4], 1):
                answer += f"{i}. {e['explanation'][:120]}...\n   [来源: {e['source'].title}]\n\n"
            confidence = AnswerConfidence.MEDIUM
            confidence_score = min(0.75, 0.4 + len(explanations) * 0.08)
        else:
            answer = "现有文献中缺乏对该问题因果机制的明确解释。"
            confidence = AnswerConfidence.INSUFFICIENT
            confidence_score = 0.0

        return ResearchAnswer(
            answer=answer,
            confidence=confidence,
            confidence_score=confidence_score,
            consensus_level=ConsensusLevel.MODERATE if len(explanations) >= 3 else ConsensusLevel.UNKNOWN,
            supporting_evidence=[e["source"].to_citation() for e in explanations[:3]],
            counter_evidence=[],
            reasoning=f"分析了{len(docs)}篇文献，找到{len(explanations)}个因果解释。",
            limitations=[
                "因果关系可能是复杂的",
                "可能存在未考虑的混杂因素",
                "相关性不等于因果性"
            ],
            suggestions=[
                "查看原始文献的讨论部分",
                "关注研究的局限性说明",
                "考虑其他可能的解释机制"
            ],
            metadata={"explanations_found": len(explanations)}
        )

    async def _answer_what(
        self,
        question: str,
        docs: List[RetrievalResult]
    ) -> ResearchAnswer:
        """
        回答"是什么"问题（定义、概念）

        提供概念的定义和解释
        """
        # 提取定义
        definitions = []
        for doc in docs:
            content = doc.content
            # 查找定义性语句
            if any(kw in content.lower() for kw in ['is defined as', 'refers to', 'is a', '概念', '定义为']):
                definitions.append({
                    "source": doc,
                    "definition": content[:200]
                })

        if definitions:
            # 选择最详细的定义
            best_def = max(definitions, key=lambda x: len(x["definition"]))
            answer = f"根据文献定义：\n\n{best_def['definition'][:300]}...\n\n"
            answer += f"该定义来自：{best_def['source'].title}"
            confidence = AnswerConfidence.HIGH if len(definitions) >= 2 else AnswerConfidence.MEDIUM
            confidence_score = min(0.85, 0.5 + len(definitions) * 0.1)
        else:
            answer = "现有文献中未找到明确的定义。"
            confidence = AnswerConfidence.INSUFFICIENT
            confidence_score = 0.0

        return ResearchAnswer(
            answer=answer,
            confidence=confidence,
            confidence_score=confidence_score,
            consensus_level=ConsensusLevel.STRONG if len(definitions) >= 3 else ConsensusLevel.MODERATE,
            supporting_evidence=[d["source"].to_citation() for d in definitions[:3]],
            counter_evidence=[],
            reasoning=f"从{len(docs)}篇文献中提取定义信息。",
            limitations=[
                "不同文献可能有不同的定义角度",
                "概念可能随时间发展而演变"
            ],
            suggestions=[
                "查看该领域的经典文献",
                "关注概念的操作化定义",
                "考虑不同学派的观点"
            ],
            metadata={"definitions_found": len(definitions)}
        )

    async def _answer_compare(
        self,
        question: str,
        docs: List[RetrievalResult]
    ) -> ResearchAnswer:
        """
        回答对比问题

        比较不同方法、理论或结果的异同
        """
        # 提取对比信息
        comparisons = []
        compare_keywords = ['compared to', 'versus', 'difference', 'similar', 'better', 'worse',
                           '比较', '对比', '区别', '差异', '优于', '劣于']

        for doc in docs:
            content = doc.content
            if any(kw in content.lower() for kw in compare_keywords):
                comparisons.append({
                    "source": doc,
                    "comparison": content[:200]
                })

        if comparisons:
            answer = f"基于文献对比分析：\n\n"
            for i, c in enumerate(comparisons[:4], 1):
                answer += f"{i}. {c['comparison'][:120]}...\n"
            confidence = AnswerConfidence.MEDIUM
            confidence_score = min(0.7, 0.4 + len(comparisons) * 0.06)
        else:
            answer = "现有文献中缺乏直接的对比分析。"
            confidence = AnswerConfidence.INSUFFICIENT
            confidence_score = 0.0

        return ResearchAnswer(
            answer=answer,
            confidence=confidence,
            confidence_score=confidence_score,
            consensus_level=ConsensusLevel.MODERATE if len(comparisons) >= 3 else ConsensusLevel.UNKNOWN,
            supporting_evidence=[c["source"].to_citation() for c in comparisons[:3]],
            counter_evidence=[],
            reasoning=f"从{len(docs)}篇文献中提取对比信息。",
            limitations=[
                "对比可能基于不同的评估标准",
                "研究背景可能不同"
            ],
            suggestions=[
                "明确对比的维度",
                "考虑各自的适用场景",
                "查看最新比较研究"
            ],
            metadata={"comparisons_found": len(comparisons)}
        )

    async def _answer_general(
        self,
        question: str,
        docs: List[RetrievalResult]
    ) -> ResearchAnswer:
        """
        回答一般性问题

        综合文献信息给出全面回答
        """
        if not docs:
            return ResearchAnswer(
                answer="没有找到相关文献来回答这个问题。",
                confidence=AnswerConfidence.INSUFFICIENT,
                confidence_score=0.0,
                consensus_level=ConsensusLevel.UNKNOWN,
                supporting_evidence=[],
                counter_evidence=[],
                reasoning="检索未返回相关文献。",
                limitations=["缺乏相关文献"],
                suggestions=["尝试使用不同的关键词", "扩大检索范围"]
            )

        # 综合回答
        answer_parts = ["基于相关文献的分析：\n\n"]
        for i, doc in enumerate(docs[:5], 1):
            answer_parts.append(f"{i}. {doc.title}指出：{doc.content[:150]}...\n")

        answer = "\n".join(answer_parts)

        return ResearchAnswer(
            answer=answer,
            confidence=AnswerConfidence.MEDIUM if len(docs) >= 3 else AnswerConfidence.LOW,
            confidence_score=min(0.7, 0.3 + len(docs) * 0.05),
            consensus_level=ConsensusLevel.MODERATE,
            supporting_evidence=[doc.to_citation() for doc in docs[:5]],
            counter_evidence=[],
            reasoning=f"综合了{len(docs)}篇文献的信息。",
            limitations=[
                "回答基于有限的文献",
                "可能遗漏其他重要观点"
            ],
            suggestions=[
                "阅读原始文献获取完整信息",
                "查看引文网络发现更多相关研究"
            ],
            metadata={"docs_used": len(docs)}
        )


# 服务实例
_research_qa_service: Optional[ResearchQAService] = None


def get_research_qa_service(rag_engine: Optional[RAGEngine] = None) -> ResearchQAService:
    """获取研究问答服务单例"""
    global _research_qa_service
    if _research_qa_service is None:
        _research_qa_service = ResearchQAService(rag_engine=rag_engine)
    return _research_qa_service
