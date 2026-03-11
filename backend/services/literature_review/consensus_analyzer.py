"""
共识度分析服务
分析学术界对某一观点的共识程度
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .evidence_extractor import Evidence, EvidenceStrength


class ConsensusLevel(str, Enum):
    """共识级别"""
    UNANIMOUS = "unanimous"  # 完全一致 (>95%)
    STRONG = "strong"  # 强共识 (80-95%)
    MODERATE = "moderate"  # 中等共识 (60-80%)
    MIXED = "mixed"  # 混合 (40-60%)
    CONTROVERSIAL = "controversial"  # 争议 (20-40%)
    FRAGMENTED = "fragmented"  # 高度分歧 (<20%)


class Stance(str, Enum):
    """立场"""
    SUPPORT = "support"  # 支持
    OPPOSE = "oppose"  # 反对
    NEUTRAL = "neutral"  # 中立
    UNCERTAIN = "uncertain"  # 不确定


@dataclass
class StudyStance:
    """研究立场"""
    article_id: str
    article_title: str
    stance: Stance
    confidence: float  # 立场置信度 0-1
    evidence_quality: EvidenceStrength
    key_arguments: List[str]  # 关键论据


@dataclass
class ConsensusAnalysis:
    """共识度分析结果"""
    id: str
    question: str  # 研究问题
    consensus_level: ConsensusLevel
    consensus_score: float  # 0-1 共识分数

    # 统计
    total_studies: int
    supporting_count: int
    opposing_count: int
    neutral_count: int
    uncertain_count: int

    # 详细立场
    stances: List[StudyStance]

    # 分析
    supporting_evidence: List[str]  # 支持方主要证据
    opposing_evidence: List[str]  # 反对方主要证据
    key_disagreements: List[str]  # 主要分歧点
    potential_sources: List[str]  # 分歧可能来源

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "consensus_level": self.consensus_level.value,
            "consensus_score": round(self.consensus_score, 3),
            "statistics": {
                "total_studies": self.total_studies,
                "supporting": self.supporting_count,
                "opposing": self.opposing_count,
                "neutral": self.neutral_count,
                "uncertain": self.uncertain_count,
            },
            "stances": [
                {
                    "article_id": s.article_id,
                    "article_title": s.article_title,
                    "stance": s.stance.value,
                    "confidence": s.confidence,
                    "evidence_quality": s.evidence_quality.value,
                    "key_arguments": s.key_arguments,
                }
                for s in self.stances
            ],
            "supporting_evidence": self.supporting_evidence,
            "opposing_evidence": self.opposing_evidence,
            "key_disagreements": self.key_disagreements,
            "potential_sources": self.potential_sources,
            "created_at": self.created_at.isoformat(),
        }


class ConsensusAnalyzer:
    """
    共识度分析器
    分析学术界对特定观点的共识程度
    """

    def __init__(self, llm_service=None):
        self.llm = llm_service

    async def analyze_consensus(
        self,
        question: str,
        evidences: List[Evidence],
    ) -> ConsensusAnalysis:
        """
        分析共识度

        Args:
            question: 研究问题
            evidences: 证据列表

        Returns:
            ConsensusAnalysis: 共识度分析结果
        """
        import uuid

        if not evidences:
            return ConsensusAnalysis(
                id=str(uuid.uuid4()),
                question=question,
                consensus_level=ConsensusLevel.FRAGMENTED,
                consensus_score=0.0,
                total_studies=0,
                supporting_count=0,
                opposing_count=0,
                neutral_count=0,
                uncertain_count=0,
                stances=[],
                supporting_evidence=[],
                opposing_evidence=[],
                key_disagreements=["没有相关研究"],
                potential_sources=[],
            )

        # 分析每个研究的立场
        stances = await self._analyze_stances(question, evidences)

        # 统计立场分布
        stance_counts = self._count_stances(stances)

        # 计算共识度
        consensus_level, consensus_score = self._calculate_consensus(
            stance_counts, len(stances)
        )

        # 提取支持和反对的主要证据
        supporting_evidence = self._extract_supporting_evidence(stances)
        opposing_evidence = self._extract_opposing_evidence(stances)

        # 识别主要分歧点
        key_disagreements = self._identify_disagreements(stances)

        # 分析分歧来源
        potential_sources = self._analyze_disagreement_sources(stances)

        return ConsensusAnalysis(
            id=str(uuid.uuid4()),
            question=question,
            consensus_level=consensus_level,
            consensus_score=consensus_score,
            total_studies=len(stances),
            supporting_count=stance_counts[Stance.SUPPORT],
            opposing_count=stance_counts[Stance.OPPOSE],
            neutral_count=stance_counts[Stance.NEUTRAL],
            uncertain_count=stance_counts[Stance.UNCERTAIN],
            stances=stances,
            supporting_evidence=supporting_evidence,
            opposing_evidence=opposing_evidence,
            key_disagreements=key_disagreements,
            potential_sources=potential_sources,
        )

    async def _analyze_stances(
        self,
        question: str,
        evidences: List[Evidence],
    ) -> List[StudyStance]:
        """分析每个研究的立场"""
        stances = []

        for evidence in evidences:
            # 使用AI或规则判断立场
            stance = self._determine_stance(evidence)

            study_stance = StudyStance(
                article_id=evidence.article_id,
                article_title=evidence.article_title,
                stance=stance,
                confidence=self._calculate_stance_confidence(evidence),
                evidence_quality=evidence.evidence_strength,
                key_arguments=evidence.key_findings[:3],
            )
            stances.append(study_stance)

        return stances

    def _determine_stance(self, evidence: Evidence) -> Stance:
        """确定单个研究的立场"""
        # 基于证据强度和主张判断
        claim_lower = evidence.claim.lower()

        # 检查否定词
        negative_indicators = [
            "no effect", "no significant", "not effective", "negative",
            "无效", "不显著", "没有影响", "负面"
        ]

        positive_indicators = [
            "significant", "effective", "positive", "improve",
            "显著", "有效", "正面", "提高"
        ]

        neg_count = sum(1 for ind in negative_indicators if ind in claim_lower)
        pos_count = sum(1 for ind in positive_indicators if ind in claim_lower)

        if evidence.evidence_strength == EvidenceStrength.INCONCLUSIVE:
            return Stance.UNCERTAIN

        if neg_count > pos_count:
            return Stance.OPPOSE
        elif pos_count > neg_count:
            return Stance.SUPPORT
        else:
            return Stance.NEUTRAL

    def _calculate_stance_confidence(self, evidence: Evidence) -> float:
        """计算立场置信度"""
        base_confidence = {
            EvidenceStrength.STRONG: 0.9,
            EvidenceStrength.MODERATE: 0.7,
            EvidenceStrength.WEAK: 0.5,
            EvidenceStrength.INCONCLUSIVE: 0.3,
        }.get(evidence.evidence_strength, 0.5)

        # 根据证据质量调整
        if evidence.quality_score:
            base_confidence = (base_confidence + evidence.quality_score) / 2

        return round(base_confidence, 2)

    def _count_stances(self, stances: List[StudyStance]) -> Dict[Stance, int]:
        """统计立场分布"""
        counts = {
            Stance.SUPPORT: 0,
            Stance.OPPOSE: 0,
            Stance.NEUTRAL: 0,
            Stance.UNCERTAIN: 0,
        }

        for stance in stances:
            counts[stance.stance] += 1

        return counts

    def _calculate_consensus(
        self,
        stance_counts: Dict[Stance, int],
        total: int,
    ) -> Tuple[ConsensusLevel, float]:
        """计算共识度和级别"""
        if total == 0:
            return ConsensusLevel.FRAGMENTED, 0.0

        # 计算支持率（不包括中立和不确定）
        decisive = stance_counts[Stance.SUPPORT] + stance_counts[Stance.OPPOSE]

        if decisive == 0:
            return ConsensusLevel.MIXED, 0.5

        support_ratio = stance_counts[Stance.SUPPORT] / decisive

        # 共识分数（距离0.5的远近）
        consensus_score = abs(support_ratio - 0.5) * 2

        # 确定共识级别
        if consensus_score > 0.95:
            level = ConsensusLevel.UNANIMOUS
        elif consensus_score > 0.8:
            level = ConsensusLevel.STRONG
        elif consensus_score > 0.6:
            level = ConsensusLevel.MODERATE
        elif consensus_score > 0.4:
            level = ConsensusLevel.MIXED
        elif consensus_score > 0.2:
            level = ConsensusLevel.CONTROVERSIAL
        else:
            level = ConsensusLevel.FRAGMENTED

        return level, round(consensus_score, 3)

    def _extract_supporting_evidence(self, stances: List[StudyStance]) -> List[str]:
        """提取支持方的主要证据"""
        supporting = [
            s for s in stances
            if s.stance == Stance.SUPPORT and s.evidence_quality in [
                EvidenceStrength.STRONG, EvidenceStrength.MODERATE
            ]
        ]

        # 按置信度排序
        supporting.sort(key=lambda x: x.confidence, reverse=True)

        evidence_list = []
        for s in supporting[:3]:  # 取前3个
            evidence_list.extend(s.key_arguments)

        return evidence_list[:5]  # 最多返回5条

    def _extract_opposing_evidence(self, stances: List[StudyStance]) -> List[str]:
        """提取反对方的主要证据"""
        opposing = [
            s for s in stances
            if s.stance == Stance.OPPOSE and s.evidence_quality in [
                EvidenceStrength.STRONG, EvidenceStrength.MODERATE
            ]
        ]

        opposing.sort(key=lambda x: x.confidence, reverse=True)

        evidence_list = []
        for s in opposing[:3]:
            evidence_list.extend(s.key_arguments)

        return evidence_list[:5]

    def _identify_disagreements(self, stances: List[StudyStance]) -> List[str]:
        """识别主要分歧点"""
        disagreements = []

        # 检查是否有明确的分歧
        has_support = any(s.stance == Stance.SUPPORT for s in stances)
        has_oppose = any(s.stance == Stance.OPPOSE for s in stances)

        if has_support and has_oppose:
            disagreements.append("对该问题的效果方向存在分歧")

        # 检查证据质量差异
        high_quality_support = any(
            s.stance == Stance.SUPPORT and s.evidence_quality == EvidenceStrength.STRONG
            for s in stances
        )
        high_quality_oppose = any(
            s.stance == Stance.OPPOSE and s.evidence_quality == EvidenceStrength.STRONG
            for s in stances
        )

        if high_quality_support and high_quality_oppose:
            disagreements.append("高质量研究也得出了相反的结论")

        return disagreements if disagreements else ["主要分歧点不明显"]

    def _analyze_disagreement_sources(self, stances: List[StudyStance]) -> List[str]:
        """分析分歧的可能来源"""
        sources = []

        # 检查样本差异
        # 检查方法差异
        # 检查测量差异

        # 默认来源
        if len(stances) > 2:
            sources.extend([
                "研究设计的差异",
                "样本特征的不同",
                "测量工具的差异",
                "文化或环境背景的差异",
            ])
        else:
            sources.append("研究数量不足，难以分析分歧来源")

        return sources[:4]


# 服务实例
_analyzer: Optional[ConsensusAnalyzer] = None


def get_consensus_analyzer(llm_service=None) -> ConsensusAnalyzer:
    """获取共识度分析器单例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = ConsensusAnalyzer(llm_service)
    return _analyzer
