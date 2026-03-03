"""
推荐算法模块
多维度评分体系
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import Counter
import math


class RecommendationAlgorithm:
    """推荐算法"""

    # 权重配置
    WEIGHTS = {
        'relevance': 0.35,      # 相关度
        'timeliness': 0.25,     # 时效性
        'authority': 0.20,      # 权威性
        'practice': 0.10,       # 实践价值
        'school_match': 0.05,   # 学校关联
        'readability': 0.05,    # 可读性
    }

    def __init__(self):
        pass

    def calculate_relevance_score(
        self,
        user_interests: Dict[str, float],
        article_keywords: List[str],
        abstract_similarity: float = 0.5,
    ) -> float:
        """
        计算相关度分数

        Args:
            user_interests: 用户兴趣关键词及其权重
            article_keywords: 文章关键词
            abstract_similarity: 摘要相似度
        """
        if not user_interests or not article_keywords:
            return 0.0

        # 关键词匹配分数
        keyword_score = 0.0
        for kw in article_keywords:
            if kw in user_interests:
                keyword_score += user_interests[kw]

        # 归一化
        max_possible = sum(user_interests.values())
        if max_possible > 0:
            keyword_score = min(keyword_score / max_possible, 1.0)

        # 综合关键词匹配和摘要相似度
        relevance = 0.6 * keyword_score + 0.4 * abstract_similarity

        return min(relevance, 1.0)

    def calculate_timeliness_score(
        self,
        publication_date: Optional[datetime],
        current_date: Optional[datetime] = None,
    ) -> float:
        """
        计算时效性分数

        越新的文献分数越高，指数衰减
        """
        if not publication_date:
            return 0.5

        if not current_date:
            current_date = datetime.now()

        # 计算月份差
        months_diff = (current_date.year - publication_date.year) * 12 + \
                      (current_date.month - publication_date.month)

        # 指数衰减，半衰期为12个月
        score = math.exp(-months_diff / 12.0)

        return max(score, 0.1)  # 最低0.1分

    def calculate_authority_score(
        self,
        citation_count: int,
        impact_factor: Optional[float] = None,
        h_index: Optional[int] = None,
    ) -> float:
        """
        计算权威性分数
        """
        # 引用数分数（对数缩放）
        citation_score = min(math.log10(max(citation_count, 1)) / 3.0, 1.0)

        # 影响因子分数
        if_score = 0.5
        if impact_factor:
            if_score = min(impact_factor / 10.0, 1.0)

        # H指数分数
        h_score = 0.5
        if h_index:
            h_score = min(h_index / 50.0, 1.0)

        # 加权综合
        authority = 0.5 * citation_score + 0.3 * if_score + 0.2 * h_score

        return authority

    def calculate_practice_score(
        self,
        has_case_study: bool = False,
        has_data: bool = False,
        has_methodology: bool = False,
    ) -> float:
        """
        计算实践价值分数
        """
        score = 0.0
        if has_case_study:
            score += 0.4
        if has_data:
            score += 0.3
        if has_methodology:
            score += 0.3
        return score

    def calculate_school_match_score(
        self,
        user_school: Optional[str],
        author_affiliations: List[str],
    ) -> float:
        """
        计算学校关联分数
        """
        if not user_school or not author_affiliations:
            return 0.5

        for aff in author_affiliations:
            if user_school.lower() in aff.lower():
                return 1.0

        return 0.3

    def calculate_readability_score(
        self,
        abstract_length: int,
        has_clear_structure: bool = True,
    ) -> float:
        """
        计算可读性分数
        """
        # 摘要长度适中
        length_score = 1.0 - abs(abstract_length - 300) / 500.0
        length_score = max(min(length_score, 1.0), 0.0)

        structure_score = 0.8 if has_clear_structure else 0.4

        return 0.6 * length_score + 0.4 * structure_score

    def calculate_total_score(
        self,
        relevance: float,
        timeliness: float,
        authority: float,
        practice: float = 0.5,
        school_match: float = 0.5,
        readability: float = 0.7,
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算总分

        Returns:
            Tuple[float, Dict]: (总分, 各维度分数)
        """
        scores = {
            'relevance': relevance,
            'timeliness': timeliness,
            'authority': authority,
            'practice': practice,
            'school_match': school_match,
            'readability': readability,
        }

        total = sum(
            scores[key] * self.WEIGHTS[key]
            for key in self.WEIGHTS
        )

        return total, scores

    def generate_explanation(
        self,
        scores: Dict[str, float],
        article_title: str,
    ) -> str:
        """
        生成推荐解释
        """
        reasons = []

        if scores['relevance'] > 0.7:
            reasons.append("与您的研究方向高度相关")
        elif scores['relevance'] > 0.5:
            reasons.append("与您的研究领域相关")

        if scores['timeliness'] > 0.8:
            reasons.append("近期发表的新研究")
        elif scores['timeliness'] > 0.6:
            reasons.append("时效性较好")

        if scores['authority'] > 0.7:
            reasons.append("高引用权威文献")
        elif scores['authority'] > 0.5:
            reasons.append("具有一定学术影响力")

        if scores['practice'] > 0.7:
            reasons.append("包含实践案例")

        if not reasons:
            reasons.append("基于您的阅读偏好推荐")

        return f"推荐理由：{'；'.join(reasons[:3])}"


class CollaborativeFiltering:
    """协同过滤"""

    def __init__(self):
        self.user_item_matrix = {}
        self.item_similarity = {}

    def fit(self, user_behaviors: Dict[str, List[str]]):
        """
        训练协同过滤模型

        Args:
            user_behaviors: {user_id: [article_id1, article_id2, ...]}
        """
        self.user_item_matrix = user_behaviors

        # 计算物品相似度
        self.item_similarity = self._calculate_item_similarity()

    def _calculate_item_similarity(self) -> Dict[str, Dict[str, float]]:
        """计算物品相似度矩阵"""
        # 统计共现次数
        co_occurrence = Counter()
        item_count = Counter()

        for items in self.user_item_matrix.values():
            for i in items:
                item_count[i] += 1
                for j in items:
                    if i != j:
                        co_occurrence[(i, j)] += 1

        # 计算余弦相似度
        similarity = {}
        for (i, j), count in co_occurrence.items():
            if i not in similarity:
                similarity[i] = {}
            denom = math.sqrt(item_count[i] * item_count[j])
            if denom > 0:
                similarity[i][j] = count / denom

        return similarity

    def recommend(
        self,
        user_id: str,
        n: int = 10,
        exclude: Optional[List[str]] = None,
    ) -> List[Tuple[str, float]]:
        """
        为用户推荐文章

        Returns:
            List[Tuple[str, float]]: [(article_id, score), ...]
        """
        exclude = exclude or []
        user_items = set(self.user_item_matrix.get(user_id, []))

        scores = Counter()
        for item in user_items:
            if item in self.item_similarity:
                for similar_item, sim in self.item_similarity[item].items():
                    if similar_item not in user_items and similar_item not in exclude:
                        scores[similar_item] += sim

        return scores.most_common(n)


class ContentBasedFiltering:
    """基于内容的过滤"""

    def __init__(self):
        self.item_features = {}
        self.user_profiles = {}

    def set_item_features(self, features: Dict[str, Dict]):
        """设置物品特征"""
        self.item_features = features

    def update_user_profile(
        self,
        user_id: str,
        liked_items: List[str],
    ):
        """更新用户画像"""
        if not liked_items:
            return

        # 聚合用户喜欢的物品特征
        profile = Counter()
        for item_id in liked_items:
            if item_id in self.item_features:
                for kw, weight in self.item_features[item_id].get('keywords', {}).items():
                    profile[kw] += weight

        # 归一化
        if profile:
            max_weight = max(profile.values())
            self.user_profiles[user_id] = {
                k: v / max_weight for k, v in profile.items()
            }

    def recommend(
        self,
        user_id: str,
        n: int = 10,
        exclude: Optional[List[str]] = None,
    ) -> List[Tuple[str, float]]:
        """基于内容推荐"""
        exclude = exclude or []
        profile = self.user_profiles.get(user_id, {})

        if not profile:
            return []

        scores = []
        for item_id, features in self.item_features.items():
            if item_id in exclude:
                continue

            score = 0.0
            for kw, weight in features.get('keywords', {}).items():
                if kw in profile:
                    score += weight * profile[kw]

            if score > 0:
                scores.append((item_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]


class HybridRecommender:
    """混合推荐器"""

    def __init__(self):
        self.cf = CollaborativeFiltering()
        self.cbf = ContentBasedFiltering()
        self.algorithm = RecommendationAlgorithm()

        # 混合权重
        self.cf_weight = 0.4
        self.cbf_weight = 0.6

    def recommend(
        self,
        user_id: str,
        n: int = 10,
        exclude: Optional[List[str]] = None,
    ) -> List[Tuple[str, float]]:
        """混合推荐"""
        exclude = exclude or []

        # 协同过滤推荐
        cf_recs = dict(self.cf.recommend(user_id, n * 2, exclude))

        # 基于内容推荐
        cbf_recs = dict(self.cbf.recommend(user_id, n * 2, exclude))

        # 混合分数
        all_items = set(cf_recs.keys()) | set(cbf_recs.keys())

        hybrid_scores = []
        for item in all_items:
            cf_score = cf_recs.get(item, 0)
            cbf_score = cbf_recs.get(item, 0)
            hybrid_score = self.cf_weight * cf_score + self.cbf_weight * cbf_score
            hybrid_scores.append((item, hybrid_score))

        hybrid_scores.sort(key=lambda x: x[1], reverse=True)
        return hybrid_scores[:n]
