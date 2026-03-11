"""
证据提取服务
从文献中提取关键证据信息
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EvidenceType(str, Enum):
    """证据类型"""
    EMPIRICAL = "empirical"  # 实证证据
    THEORETICAL = "theoretical"  # 理论证据
    METHODOLOGICAL = "methodological"  # 方法论证据
    STATISTICAL = "statistical"  # 统计证据
    CASE_STUDY = "case_study"  # 案例研究
    META_ANALYSIS = "meta_analysis"  # 元分析


class EvidenceStrength(str, Enum):
    """证据强度"""
    STRONG = "strong"  # 强证据
    MODERATE = "moderate"  # 中等证据
    WEAK = "weak"  # 弱证据
    INCONCLUSIVE = "inconclusive"  # 不确定


@dataclass
class StudyDesign:
    """研究设计信息"""
    design_type: str  # 实验/观察性/回顾性等
    sample_size: Optional[int] = None
    duration: Optional[str] = None  # 研究持续时间
    control_group: bool = False
    randomization: bool = False
    blinding: Optional[str] = None  # 单盲/双盲
    setting: Optional[str] = None  # 实验室/现场/在线等


@dataclass
class Evidence:
    """证据条目"""
    id: str
    article_id: str
    article_title: str
    authors: List[str]
    year: Optional[int]
    journal: Optional[str]

    # 证据内容
    claim: str  # 主张/结论
    evidence_type: EvidenceType
    evidence_strength: EvidenceStrength

    # 研究细节
    study_design: Optional[StudyDesign] = None
    sample_description: Optional[str] = None  # 样本描述
    key_findings: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)  # 统计数据

    # 方法论
    methodology: Optional[str] = None
    measures: List[str] = field(default_factory=list)  # 测量指标
    interventions: List[str] = field(default_factory=list)  # 干预措施

    # 质量评估
    limitations: List[str] = field(default_factory=list)
    quality_score: Optional[float] = None  # 0-1

    # 元数据
    extracted_at: datetime = field(default_factory=datetime.now)
    extraction_confidence: float = 0.0  # AI提取置信度

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "article_id": self.article_id,
            "article_title": self.article_title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "claim": self.claim,
            "evidence_type": self.evidence_type.value,
            "evidence_strength": self.evidence_strength.value,
            "study_design": {
                "design_type": self.study_design.design_type,
                "sample_size": self.study_design.sample_size,
                "duration": self.study_design.duration,
                "control_group": self.study_design.control_group,
                "randomization": self.study_design.randomization,
            } if self.study_design else None,
            "sample_description": self.sample_description,
            "key_findings": self.key_findings,
            "statistics": self.statistics,
            "methodology": self.methodology,
            "measures": self.measures,
            "limitations": self.limitations,
            "quality_score": self.quality_score,
            "extraction_confidence": self.extraction_confidence,
        }


class EvidenceExtractor:
    """
    证据提取器
    使用AI从文献中提取结构化证据
    """

    def __init__(self, llm_service=None):
        self.llm = llm_service

    async def extract_from_article(
        self,
        article_id: str,
        title: str,
        abstract: str,
        full_text: Optional[str] = None,
        authors: Optional[List[str]] = None,
        year: Optional[int] = None,
        journal: Optional[str] = None,
    ) -> List[Evidence]:
        """
        从单篇文献中提取证据

        Args:
            article_id: 文献ID
            title: 标题
            abstract: 摘要
            full_text: 全文（可选）
            authors: 作者列表
            year: 年份
            journal: 期刊

        Returns:
            List[Evidence]: 提取的证据列表
        """
        # 构建提取提示
        content = full_text if full_text else abstract

        prompt = f"""请从以下学术论文中提取关键证据信息。

论文标题: {title}
作者: {', '.join(authors) if authors else 'Unknown'}
年份: {year or 'Unknown'}
期刊: {journal or 'Unknown'}

内容:
{content[:3000]}

请提取以下信息并以JSON格式返回:
{{
    "main_claim": "论文的主要主张/结论",
    "evidence_type": "证据类型 (empirical/theoretical/methodological/statistical/case_study/meta_analysis)",
    "evidence_strength": "证据强度 (strong/moderate/weak/inconclusive)",
    "study_design": {{
        "type": "研究设计类型",
        "sample_size": 样本数量（数字）,
        "duration": "研究持续时间",
        "control_group": true/false,
        "randomization": true/false
    }},
    "key_findings": ["发现1", "发现2"],
    "statistics": {{
        "effect_size": "效应量",
        "p_value": "p值",
        "confidence_interval": "置信区间"
    }},
    "methodology": "研究方法简述",
    "measures": ["测量指标1", "测量指标2"],
    "limitations": ["局限性1", "局限性2"],
    "quality_score": 0.8  // 0-1之间的质量评分
}}"""

        try:
            # 调用LLM提取
            if self.llm:
                result = await self.llm.generate(
                    prompt=prompt,
                    max_tokens=1500,
                    temperature=0.2,
                )
                # 解析结果
                import json
                data = json.loads(result.content if hasattr(result, 'content') else result)

                # 创建Evidence对象
                evidence = self._create_evidence_from_data(
                    data, article_id, title, authors, year, journal
                )
                return [evidence]
            else:
                # 模拟提取
                return [self._mock_evidence(
                    article_id, title, authors, year, journal
                )]

        except Exception as e:
            print(f"提取证据失败: {e}")
            return []

    async def extract_from_articles_batch(
        self,
        articles: List[Dict[str, Any]]
    ) -> List[Evidence]:
        """
        批量从多篇文献中提取证据

        Args:
            articles: 文献数据列表

        Returns:
            List[Evidence]: 所有提取的证据
        """
        import asyncio

        tasks = [
            self.extract_from_article(**article)
            for article in articles
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_evidence = []
        for result in results:
            if isinstance(result, list):
                all_evidence.extend(result)
            elif isinstance(result, Exception):
                print(f"提取证据时出错: {result}")

        return all_evidence

    def _create_evidence_from_data(
        self,
        data: Dict[str, Any],
        article_id: str,
        title: str,
        authors: Optional[List[str]],
        year: Optional[int],
        journal: Optional[str],
    ) -> Evidence:
        """从解析的数据创建Evidence对象"""
        import uuid

        # 解析研究设计
        study_design = None
        if data.get("study_design"):
            sd = data["study_design"]
            study_design = StudyDesign(
                design_type=sd.get("type", "unknown"),
                sample_size=sd.get("sample_size"),
                duration=sd.get("duration"),
                control_group=sd.get("control_group", False),
                randomization=sd.get("randomization", False),
            )

        return Evidence(
            id=str(uuid.uuid4()),
            article_id=article_id,
            article_title=title,
            authors=authors or [],
            year=year,
            journal=journal,
            claim=data.get("main_claim", ""),
            evidence_type=EvidenceType(data.get("evidence_type", "empirical")),
            evidence_strength=EvidenceStrength(data.get("evidence_strength", "moderate")),
            study_design=study_design,
            key_findings=data.get("key_findings", []),
            statistics=data.get("statistics", {}),
            methodology=data.get("methodology"),
            measures=data.get("measures", []),
            limitations=data.get("limitations", []),
            quality_score=data.get("quality_score"),
            extraction_confidence=0.85,
        )

    def _mock_evidence(
        self,
        article_id: str,
        title: str,
        authors: Optional[List[str]],
        year: Optional[int],
        journal: Optional[str],
    ) -> Evidence:
        """创建模拟证据（用于测试）"""
        import uuid

        return Evidence(
            id=str(uuid.uuid4()),
            article_id=article_id,
            article_title=title,
            authors=authors or ["Unknown"],
            year=year or 2023,
            journal=journal or "Unknown Journal",
            claim="该研究发现了显著的正面效果",
            evidence_type=EvidenceType.EMPIRICAL,
            evidence_strength=EvidenceStrength.MODERATE,
            study_design=StudyDesign(
                design_type="experimental",
                sample_size=120,
                control_group=True,
                randomization=True,
            ),
            key_findings=["效果显著", "具有统计意义"],
            statistics={"p_value": "<0.05", "effect_size": "medium"},
            quality_score=0.75,
            extraction_confidence=0.8,
        )


# 服务实例
_extractor: Optional[EvidenceExtractor] = None


def get_evidence_extractor(llm_service=None) -> EvidenceExtractor:
    """获取证据提取器单例"""
    global _extractor
    if _extractor is None:
        _extractor = EvidenceExtractor(llm_service)
    return _extractor
