"""
事实检查器
验证生成内容的准确性和一致性
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FactStatus(str, Enum):
    """事实状态"""
    SUPPORTED = "supported"  # 有证据支持
    CONTRADICTED = "contradicted"  # 与证据矛盾
    UNSURE = "unsure"  # 无法验证


@dataclass
class FactCheck:
    """事实检查结果"""
    claim: str  # 声称的内容
    status: FactStatus
    evidence: List[str]  # 支持/反驳的证据
    confidence: float
    explanation: str


class FactChecker:
    """事实检查器"""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def check(
        self,
        claim: str,
        evidence: List[Dict],
        context: Optional[str] = None
    ) -> FactCheck:
        """
        检查单个事实

        Args:
            claim: 待检查的事实陈述
            evidence: 证据列表
            context: 可选上下文

        Returns:
            检查结果
        """
        if not self.llm:
            # 简单检查：看证据中是否包含关键词
            return self._simple_check(claim, evidence)

        # 构建证据文本
        evidence_text = "\n\n".join([
            f"证据{i+1}: {e.get('content', '')}"
            for i, e in enumerate(evidence[:5])
        ])

        prompt = f"""验证以下事实是否被证据支持。

事实: {claim}
{f"上下文: {context}" if context else ""}

证据:
{evidence_text}

请判断:
1. 该事实是否被证据支持？
2. 还是被证据反驳？
3. 还是无法从证据中确认？

请按以下格式输出:
判断: [支持/反驳/无法确认]
置信度: [0-1之间的数字]
解释: [简要解释原因]
相关证据: [列出支持判断的证据编号]"""

        try:
            response = await self.llm.generate(prompt)
            return self._parse_check_result(claim, response, evidence)
        except Exception as e:
            logger.error(f"Fact check failed: {e}")
            return FactCheck(
                claim=claim,
                status=FactStatus.UNSURE,
                evidence=[],
                confidence=0.0,
                explanation="检查失败"
            )

    def _simple_check(self, claim: str, evidence: List[Dict]) -> FactCheck:
        """简单的事实检查（无需LLM）"""
        claim_words = set(claim.lower().split())

        best_match = None
        best_score = 0

        for e in evidence:
            content = e.get('content', '').lower()
            content_words = set(content.split())

            # 计算重叠词数
            overlap = len(claim_words & content_words)
            score = overlap / len(claim_words) if claim_words else 0

            if score > best_score:
                best_score = score
                best_match = content

        if best_score > 0.5:
            return FactCheck(
                claim=claim,
                status=FactStatus.SUPPORTED,
                evidence=[best_match[:200]] if best_match else [],
                confidence=best_score,
                explanation=f"找到相关证据，匹配度{best_score:.2f}"
            )
        elif best_score > 0.2:
            return FactCheck(
                claim=claim,
                status=FactStatus.UNSURE,
                evidence=[best_match[:200]] if best_match else [],
                confidence=best_score,
                explanation="证据不充分"
            )
        else:
            return FactCheck(
                claim=claim,
                status=FactStatus.UNSURE,
                evidence=[],
                confidence=0,
                explanation="未找到相关证据"
            )

    def _parse_check_result(
        self,
        claim: str,
        response: str,
        evidence: List[Dict]
    ) -> FactCheck:
        """解析检查结果"""
        status = FactStatus.UNSURE
        confidence = 0.5
        explanation = ""
        relevant_evidence = []

        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('判断:'):
                judgment = line.replace('判断:', '').strip()
                if '支持' in judgment:
                    status = FactStatus.SUPPORTED
                elif '反驳' in judgment or '矛盾' in judgment:
                    status = FactStatus.CONTRADICTED
            elif line.startswith('置信度:'):
                try:
                    confidence = float(line.replace('置信度:', '').strip())
                except:
                    pass
            elif line.startswith('解释:'):
                explanation = line.replace('解释:', '').strip()
            elif line.startswith('相关证据:'):
                evidence_str = line.replace('相关证据:', '').strip()
                # 提取证据编号
                import re
                nums = re.findall(r'\d+', evidence_str)
                for num in nums:
                    idx = int(num) - 1
                    if 0 <= idx < len(evidence):
                        relevant_evidence.append(
                            evidence[idx].get('content', '')[:200]
                        )

        return FactCheck(
            claim=claim,
            status=status,
            evidence=relevant_evidence,
            confidence=confidence,
            explanation=explanation
        )

    async def check_consistency(
        self,
        statements: List[str]
    ) -> List[Tuple[str, str, float]]:
        """
        检查多个陈述之间的一致性

        Returns:
            不一致的陈述对 [(stmt1, stmt2, conflict_score), ...]
        """
        if len(statements) < 2 or not self.llm:
            return []

        inconsistencies = []

        # 两两比较
        for i in range(len(statements)):
            for j in range(i + 1, len(statements)):
                prompt = f"""判断以下两个陈述是否一致。

陈述1: {statements[i]}
陈述2: {statements[j]}

这两个陈述:
- 一致（compatible）
- 矛盾（contradictory）
- 无关（unrelated）

如果矛盾，请给出矛盾程度（0-1）。

格式输出:
关系: [一致/矛盾/无关]
矛盾程度: [0-1]"""

                try:
                    response = await self.llm.generate(prompt)
                    if '矛盾' in response:
                        # 提取矛盾程度
                        import re
                        nums = re.findall(r'0\.\d+|1\.0|1', response)
                        if nums:
                            conflict_score = float(nums[-1])
                            inconsistencies.append(
                                (statements[i], statements[j], conflict_score)
                            )
                except Exception as e:
                    logger.error(f"Consistency check failed: {e}")

        return inconsistencies

    async def verify_answer(
        self,
        answer: str,
        sources: List[Dict]
    ) -> Dict:
        """
        验证答案的准确性

        Returns:
            验证报告
        """
        # 提取答案中的事实陈述
        claims = self._extract_claims(answer)

        # 检查每个事实
        fact_checks = []
        for claim in claims:
            check = await self.check(claim, sources)
            fact_checks.append(check)

        # 生成报告
        supported = sum(1 for c in fact_checks if c.status == FactStatus.SUPPORTED)
        contradicted = sum(1 for c in fact_checks if c.status == FactStatus.CONTRADICTED)
        unsure = sum(1 for c in fact_checks if c.status == FactStatus.UNSURE)

        avg_confidence = sum(c.confidence for c in fact_checks) / len(fact_checks) if fact_checks else 0

        return {
            "total_claims": len(claims),
            "supported": supported,
            "contradicted": contradicted,
            "unsure": unsure,
            "average_confidence": avg_confidence,
            "verdict": "verified" if contradicted == 0 and supported > unsure else "needs_review",
            "fact_checks": fact_checks
        }

    def _extract_claims(self, answer: str) -> List[str]:
        """从答案中提取事实陈述"""
        # 简单实现：按句子分割
        import re
        sentences = re.split(r'[.!?。！？]', answer)
        claims = []

        for sent in sentences:
            sent = sent.strip()
            # 过滤短句和疑问句
            if len(sent) > 10 and not sent.endswith('?'):
                claims.append(sent)

        return claims[:10]  # 限制数量
