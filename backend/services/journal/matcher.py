"""
期刊匹配算法
基于论文内容智能推荐投稿期刊
"""

import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import math


@dataclass
class PaperInfo:
    """论文信息"""
    title: str
    abstract: str
    keywords: List[str]
    field: str = ""
    word_count: int = 0


@dataclass
class JournalInfo:
    """期刊信息"""
    id: str
    name: str
    subject_areas: List[str]
    keywords: List[str]
    impact_factor: float
    acceptance_rate: float
    scope: str = ""


class JournalMatcher:
    """期刊匹配器"""

    # 学科领域关键词映射
    FIELD_KEYWORDS = {
        "计算机科学": ["计算机", "算法", "人工智能", "机器学习", "深度学习", "数据挖掘", "软件工程", "网络安全"],
        "工程管理": ["项目管理", "工程管理", "风险管理", "质量控制", "供应链", "建筑", "施工"],
        "经济学": ["经济", "金融", "投资", "市场", "贸易", "货币政策"],
        "管理学": ["管理", "组织", "战略", "领导力", "人力资源", "创新", "创业"],
        "教育学": ["教育", "教学", "课程", "学习", "培训", "高等教育"],
        "心理学": ["心理", "认知", "行为", "情绪", "发展", "社会心理"],
        "社会学": ["社会", "社区", "人口", "家庭", "文化", "性别"],
        "医学": ["医学", "临床", "疾病", "治疗", "药物", "健康"],
        "环境科学": ["环境", "生态", "气候", "污染", "可持续", "绿色"],
        "物理学": ["物理", "量子", "材料", "光学", "电子", "凝聚态"],
    }

    # 期刊数据库（示例数据）
    SAMPLE_JOURNALS = [
        {
            "id": "j1",
            "name": "管理世界",
            "subject_areas": ["管理学", "经济学"],
            "keywords": ["管理", "战略", "创新", "组织"],
            "impact_factor": 5.2,
            "acceptance_rate": 0.15,
            "scope": "管理学领域顶级期刊",
        },
        {
            "id": "j2",
            "name": "系统工程理论与实践",
            "subject_areas": ["系统工程", "管理科学"],
            "keywords": ["系统", "优化", "决策", "工程管理"],
            "impact_factor": 3.5,
            "acceptance_rate": 0.20,
            "scope": "系统工程领域核心期刊",
        },
        {
            "id": "j3",
            "name": "科研管理",
            "subject_areas": ["管理学", "科技管理"],
            "keywords": ["研发", "创新", "科技政策", "知识管理"],
            "impact_factor": 2.8,
            "acceptance_rate": 0.25,
            "scope": "科研管理领域专业期刊",
        },
        {
            "id": "j4",
            "name": "IEEE Transactions on Engineering Management",
            "subject_areas": ["工程管理", "项目管理"],
            "keywords": ["engineering", "management", "project", "technology"],
            "impact_factor": 8.5,
            "acceptance_rate": 0.10,
            "scope": "工程管理领域顶级国际期刊",
        },
        {
            "id": "j5",
            "name": "Journal of Management",
            "subject_areas": ["管理学"],
            "keywords": ["management", "organization", "strategy", "leadership"],
            "impact_factor": 13.0,
            "acceptance_rate": 0.05,
            "scope": "管理学顶级国际期刊",
        },
        {
            "id": "j6",
            "name": "项目管理技术",
            "subject_areas": ["项目管理"],
            "keywords": ["项目", "管理", "进度", "成本", "质量"],
            "impact_factor": 1.2,
            "acceptance_rate": 0.40,
            "scope": "项目管理专业期刊",
        },
        {
            "id": "j7",
            "name": "计算机学报",
            "subject_areas": ["计算机科学"],
            "keywords": ["计算机", "算法", "软件", "系统"],
            "impact_factor": 3.0,
            "acceptance_rate": 0.18,
            "scope": "计算机领域顶级中文期刊",
        },
        {
            "id": "j8",
            "name": "Journal of Construction Engineering and Management",
            "subject_areas": ["建筑工程", "工程管理"],
            "keywords": ["construction", "engineering", "project", "building"],
            "impact_factor": 4.5,
            "acceptance_rate": 0.20,
            "scope": "建筑工程管理领域国际期刊",
        },
    ]

    def __init__(self, journals: List[Dict] = None):
        """
        初始化匹配器

        Args:
            journals: 期刊数据库，为 None 时使用示例数据
        """
        self.journals = journals or self.SAMPLE_JOURNALS

    def match(
        self,
        paper: PaperInfo,
        top_n: int = 5,
        min_score: float = 30.0,
    ) -> List[Tuple[JournalInfo, float, List[str]]]:
        """
        匹配期刊

        Args:
            paper: 论文信息
            top_n: 返回前 N 个结果
            min_score: 最低匹配分数

        Returns:
            List of (journal, score, reasons)
        """
        results = []

        for journal_data in self.journals:
            journal = JournalInfo(
                id=journal_data["id"],
                name=journal_data["name"],
                subject_areas=journal_data.get("subject_areas", []),
                keywords=journal_data.get("keywords", []),
                impact_factor=journal_data.get("impact_factor", 0),
                acceptance_rate=journal_data.get("acceptance_rate", 0),
                scope=journal_data.get("scope", ""),
            )

            score, reasons = self._calculate_match_score(paper, journal)

            if score >= min_score:
                results.append((journal, score, reasons))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_n]

    def _calculate_match_score(
        self,
        paper: PaperInfo,
        journal: JournalInfo,
    ) -> Tuple[float, List[str]]:
        """
        计算匹配分数

        评分维度：
        1. 学科领域匹配 (30%)
        2. 关键词匹配 (25%)
        3. 标题/摘要语义匹配 (25%)
        4. 期刊影响力 (10%)
        5. 投稿难度匹配 (10%)
        """
        reasons = []
        total_score = 0.0

        # 1. 学科领域匹配 (30%)
        field_score = self._match_field(paper, journal)
        if field_score > 0:
            reasons.append(f"研究领域匹配: {', '.join(journal.subject_areas[:3])}")
        total_score += field_score * 0.30

        # 2. 关键词匹配 (25%)
        keyword_score = self._match_keywords(paper, journal)
        if keyword_score > 50:
            matched = self._get_matched_keywords(paper, journal)
            if matched:
                reasons.append(f"关键词匹配: {', '.join(matched[:5])}")
        total_score += keyword_score * 0.25

        # 3. 标题/摘要语义匹配 (25%)
        semantic_score = self._match_semantic(paper, journal)
        if semantic_score > 50:
            reasons.append("论文内容与期刊范围契合")
        total_score += semantic_score * 0.25

        # 4. 期刊影响力 (10%)
        impact_score = self._calculate_impact_score(journal)
        if impact_score > 80:
            reasons.append(f"高影响力期刊 (IF: {journal.impact_factor})")
        total_score += impact_score * 0.10

        # 5. 投稿难度匹配 (10%)
        difficulty_score = self._calculate_difficulty_score(journal, paper)
        total_score += difficulty_score * 0.10

        return total_score, reasons

    def _match_field(self, paper: PaperInfo, journal: JournalInfo) -> float:
        """学科领域匹配"""
        # 检查论文领域是否在期刊领域列表中
        paper_field = paper.field.lower() if paper.field else ""

        for area in journal.subject_areas:
            if paper_field and paper_field in area.lower():
                return 100.0

        # 从关键词推断领域
        paper_keywords_lower = [k.lower() for k in paper.keywords]
        for field_name, field_keywords in self.FIELD_KEYWORDS.items():
            field_match = any(
                any(fk in pk for pk in paper_keywords_lower)
                for fk in field_keywords
            )
            if field_match and field_name in journal.subject_areas:
                return 80.0

        return 20.0  # 基础分

    def _match_keywords(self, paper: PaperInfo, journal: JournalInfo) -> float:
        """关键词匹配"""
        if not paper.keywords or not journal.keywords:
            return 50.0

        paper_keywords_lower = set(k.lower() for k in paper.keywords)
        journal_keywords_lower = set(k.lower() for k in journal.keywords)

        # 计算交集比例
        common = paper_keywords_lower & journal_keywords_lower
        if not journal_keywords_lower:
            return 50.0

        match_ratio = len(common) / len(journal_keywords_lower)
        return min(100, match_ratio * 150)  # 放大匹配效果

    def _get_matched_keywords(self, paper: PaperInfo, journal: JournalInfo) -> List[str]:
        """获取匹配的关键词"""
        paper_keywords_lower = {k.lower(): k for k in paper.keywords}
        journal_keywords_lower = {k.lower(): k for k in journal.keywords}

        common = set(paper_keywords_lower.keys()) & set(journal_keywords_lower.keys())
        return [paper_keywords_lower[k] for k in common]

    def _match_semantic(self, paper: PaperInfo, journal: JournalInfo) -> float:
        """语义匹配（简化版）"""
        # 合并论文文本
        paper_text = f"{paper.title} {paper.abstract}".lower()

        # 检查期刊关键词在论文中的出现
        journal_keywords = [k.lower() for k in journal.keywords]
        scope_text = journal.scope.lower()

        # 检查关键词出现
        keyword_matches = sum(1 for k in journal_keywords if k in paper_text)
        keyword_score = min(100, keyword_matches * 20)

        # 检查 scope 词汇
        scope_words = re.findall(r'\w+', scope_text)
        scope_matches = sum(1 for w in scope_words if w in paper_text and len(w) > 3)
        scope_score = min(100, scope_matches * 10)

        return (keyword_score + scope_score) / 2

    def _calculate_impact_score(self, journal: JournalInfo) -> float:
        """计算影响力分数"""
        if not journal.impact_factor:
            return 50.0

        # IF 分数映射
        if journal.impact_factor >= 10:
            return 100.0
        elif journal.impact_factor >= 5:
            return 80.0
        elif journal.impact_factor >= 3:
            return 70.0
        elif journal.impact_factor >= 1:
            return 60.0
        else:
            return 50.0

    def _calculate_difficulty_score(self, journal: JournalInfo, paper: PaperInfo) -> float:
        """
        计算投稿难度分数

        根据论文质量估计合适的期刊难度
        """
        # 简化：根据论文字数和关键词数量估计
        if not journal.acceptance_rate:
            return 60.0

        # 接受率越高，分数越高（更容易投中）
        acceptance_score = journal.acceptance_rate * 100

        # 质量调整：关键词多、篇幅长的论文可以尝试更难的期刊
        quality_factor = min(1.5, 1 + len(paper.keywords) * 0.05 + paper.word_count / 20000)

        adjusted_score = acceptance_score * quality_factor
        return min(100, adjusted_score)

    def estimate_acceptance_probability(
        self,
        paper: PaperInfo,
        journal: JournalInfo,
        match_score: float,
    ) -> float:
        """
        估计录用概率

        Args:
            paper: 论文信息
            journal: 期刊信息
            match_score: 匹配分数

        Returns:
            估计录用概率 (0-1)
        """
        base_rate = journal.acceptance_rate or 0.2

        # 根据匹配分数调整
        if match_score >= 80:
            adjustment = 1.5
        elif match_score >= 60:
            adjustment = 1.2
        elif match_score >= 40:
            adjustment = 1.0
        else:
            adjustment = 0.8

        estimated = base_rate * adjustment
        return min(0.8, max(0.05, estimated))

    def get_comparison_matrix(
        self,
        journals: List[JournalInfo],
    ) -> Dict[str, Dict[str, Any]]:
        """
        生成期刊对比矩阵

        Args:
            journals: 要对比的期刊列表

        Returns:
            对比矩阵数据
        """
        matrix = {}

        for journal in journals:
            matrix[journal.id] = {
                "name": journal.name,
                "impact_factor": journal.impact_factor,
                "acceptance_rate": journal.acceptance_rate,
                "subject_areas": journal.subject_areas,
                "estimated_review_time": "2-4个月",  # 可从实际数据获取
                "publication_fee": "免费",  # 可从实际数据获取
                "open_access": False,  # 可从实际数据获取
            }

        return matrix
