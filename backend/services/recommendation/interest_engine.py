"""
用户兴趣建模与推荐引擎
实现协同过滤 + 内容过滤 + 混合推荐
"""

import json
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
import math

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .paper_feed_models import (
    Paper, PaperCreate, UserInterest, DailyRecommendationCreate,
    RecommendationReason, RecommendationFeedback
)

logger = logging.getLogger(__name__)


class InterestProfiler:
    """用户兴趣画像生成器"""

    def __init__(self):
        self.tfidf = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )

    async def build_profile(
        self,
        user_id: str,
        reading_history: List[Dict],
        saved_papers: List[Paper],
        search_queries: List[str],
        explicit_preferences: Optional[Dict] = None
    ) -> UserInterest:
        """
        构建用户兴趣画像

        Args:
            user_id: 用户ID
            reading_history: 阅读历史 [{"paper_id": "", "paper_title": "", "time_spent": 0, "scroll_depth": 0}]
            saved_papers: 收藏的论文
            search_queries: 搜索查询历史
            explicit_preferences: 显式偏好设置
        """
        interest = UserInterest(user_id=user_id)

        # 1. 从阅读历史提取关键词
        reading_keywords = self._extract_from_reading(reading_history)
        for kw, weight in reading_keywords.items():
            interest.keywords.append({
                "word": kw,
                "weight": weight,
                "source": "reading"
            })

        # 2. 从收藏论文提取类别和作者
        if saved_papers:
            category_weights = defaultdict(float)
            author_weights = defaultdict(float)
            journal_weights = defaultdict(float)

            for paper in saved_papers:
                # 类别权重
                for cat in paper.categories:
                    category_weights[cat] += 1.0

                # 作者权重
                for author in paper.authors[:3]:  # 前3作者
                    author_weights[author.get("name", "")] += 1.0

                # 期刊权重
                if paper.journal:
                    journal_weights[paper.journal] += 1.0

            # 归一化
            max_cat = max(category_weights.values()) if category_weights else 1
            max_auth = max(author_weights.values()) if author_weights else 1
            max_jour = max(journal_weights.values()) if journal_weights else 1

            interest.categories = [
                {"category": k, "weight": v / max_cat}
                for k, v in sorted(category_weights.items(), key=lambda x: -x[1])[:20]
            ]
            interest.authors = [
                {"author": k, "weight": v / max_auth}
                for k, v in sorted(author_weights.items(), key=lambda x: -x[1])[:20]
            ]
            interest.journals = [
                {"journal": k, "weight": v / max_jour}
                for k, v in sorted(journal_weights.items(), key=lambda x: -x[1])[:10]
            ]

        # 3. 从搜索查询提取关键词
        if search_queries:
            search_keywords = self._extract_from_queries(search_queries)
            for kw, weight in search_keywords.items():
                existing = next((k for k in interest.keywords if k["word"] == kw), None)
                if existing:
                    existing["weight"] = max(existing["weight"], weight)
                else:
                    interest.keywords.append({
                        "word": kw,
                        "weight": weight,
                        "source": "search"
                    })

        # 4. 合并显式偏好
        if explicit_preferences:
            for kw in explicit_preferences.get("keywords", []):
                existing = next((k for k in interest.keywords if k["word"] == kw), None)
                if existing:
                    existing["weight"] = max(existing["weight"], 1.0)
                    existing["source"] = "explicit"
                else:
                    interest.keywords.append({
                        "word": kw,
                        "weight": 1.0,
                        "source": "explicit"
                    })

        # 5. 分析阅读模式
        interest.reading_patterns = self._analyze_patterns(reading_history)

        # 关键词排序并截断
        interest.keywords.sort(key=lambda x: -x["weight"])
        interest.keywords = interest.keywords[:50]

        return interest

    def _extract_from_reading(self, reading_history: List[Dict]) -> Dict[str, float]:
        """从阅读历史提取关键词"""
        if not reading_history:
            return {}

        # 构建加权文本
        texts = []
        for item in reading_history:
            title = item.get("paper_title", "")
            # 根据阅读时间加权
            time_weight = min(item.get("time_spent", 60) / 300, 3.0)  # 最大3倍权重
            texts.extend([title] * int(time_weight))

        if not texts:
            return {}

        try:
            # TF-IDF提取关键词
            tfidf_matrix = self.tfidf.fit_transform(texts)
            feature_names = self.tfidf.get_feature_names_out()

            # 计算平均TF-IDF分数
            scores = np.mean(tfidf_matrix.toarray(), axis=0)
            top_indices = np.argsort(scores)[-50:]

            return {
                feature_names[i]: float(scores[i])
                for i in top_indices if scores[i] > 0
            }
        except Exception as e:
            logger.warning(f"Error extracting keywords from reading: {e}")
            return {}

    def _extract_from_queries(self, queries: List[str]) -> Dict[str, float]:
        """从搜索查询提取关键词"""
        if not queries:
            return {}

        # 统计词频
        word_freq = defaultdict(int)
        for query in queries:
            words = query.lower().split()
            for word in words:
                word = word.strip(".,!?;:")
                if len(word) > 2:
                    word_freq[word] += 1

        # 归一化
        max_freq = max(word_freq.values()) if word_freq else 1
        return {
            word: freq / max_freq * 0.8  # 搜索词权重略低于显式偏好
            for word, freq in sorted(word_freq.items(), key=lambda x: -x[1])[:30]
        }

    def _analyze_patterns(self, reading_history: List[Dict]) -> Dict:
        """分析阅读模式"""
        if not reading_history:
            return {}

        # 按时间分组统计
        hourly_dist = defaultdict(int)
        weekday_dist = defaultdict(int)

        for item in reading_history:
            read_time = item.get("read_at")
            if read_time:
                try:
                    dt = datetime.fromisoformat(read_time)
                    hourly_dist[dt.hour] += 1
                    weekday_dist[dt.weekday()] += 1
                except:
                    pass

        # 找出高峰阅读时段
        peak_hours = sorted(hourly_dist.items(), key=lambda x: -x[1])[:3]
        preferred_weekdays = sorted(weekday_dist.items(), key=lambda x: -x[1])[:3]

        return {
            "peak_hours": [h[0] for h in peak_hours],
            "preferred_weekdays": [d[0] for d in preferred_weekdays],
            "avg_time_per_paper": sum(
                item.get("time_spent", 0) for item in reading_history
            ) / len(reading_history),
            "total_papers_read": len(reading_history)
        }


class ContentBasedRecommender:
    """基于内容的推荐器"""

    def __init__(self):
        self.tfidf = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2)
        )

    def recommend(
        self,
        user_interest: UserInterest,
        candidate_papers: List[Paper],
        top_k: int = 10
    ) -> List[Tuple[Paper, float, RecommendationReason, str]]:
        """
        基于内容推荐

        Returns:
            [(paper, score, reason, reason_detail), ...]
        """
        if not candidate_papers:
            return []

        # 构建用户画像向量
        user_text = self._build_user_text(user_interest)

        # 构建论文文本向量
        paper_texts = [self._build_paper_text(p) for p in candidate_papers]

        # 计算相似度
        try:
            all_texts = [user_text] + paper_texts
            tfidf_matrix = self.tfidf.fit_transform(all_texts)
            user_vector = tfidf_matrix[0]
            paper_vectors = tfidf_matrix[1:]

            similarities = cosine_similarity(user_vector, paper_vectors)[0]
        except Exception as e:
            logger.error(f"Error computing content similarity: {e}")
            return []

        # 结合其他特征
        scored_papers = []
        for paper, sim_score in zip(candidate_papers, similarities):
            # 基础内容相似度
            score = sim_score * 0.6

            # 类别匹配加分
            cat_score = self._category_match_score(user_interest, paper)
            score += cat_score * 0.2

            # 作者匹配加分
            author_score = self._author_match_score(user_interest, paper)
            score += author_score * 0.15

            # 期刊匹配加分
            journal_score = self._journal_match_score(user_interest, paper)
            score += journal_score * 0.05

            # 确定推荐理由
            reason, detail = self._determine_reason(
                sim_score, cat_score, author_score, user_interest, paper
            )

            scored_papers.append((paper, score, reason, detail))

        # 排序并返回top_k
        scored_papers.sort(key=lambda x: -x[1])
        return scored_papers[:top_k]

    def _build_user_text(self, interest: UserInterest) -> str:
        """构建用户画像文本"""
        parts = []

        # 关键词
        for kw in interest.keywords[:30]:
            weight = int(kw.get("weight", 1) * 5)
            parts.extend([kw["word"]] * weight)

        # 类别
        for cat in interest.categories[:10]:
            weight = int(cat.get("weight", 1) * 3)
            parts.extend([cat["category"]] * weight)

        return " ".join(parts)

    def _build_paper_text(self, paper: Paper) -> str:
        """构建论文文本"""
        parts = [paper.title]
        if paper.abstract:
            parts.append(paper.abstract)
        parts.extend(paper.categories)
        return " ".join(parts)

    def _category_match_score(self, interest: UserInterest, paper: Paper) -> float:
        """计算类别匹配分数"""
        if not interest.categories or not paper.categories:
            return 0.0

        interest_cats = {c["category"]: c["weight"] for c in interest.categories}
        score = 0.0

        for cat in paper.categories:
            if cat in interest_cats:
                score += interest_cats[cat]

        return min(score, 1.0)

    def _author_match_score(self, interest: UserInterest, paper: Paper) -> float:
        """计算作者匹配分数"""
        if not interest.authors or not paper.authors:
            return 0.0

        interest_authors = {a["author"]: a["weight"] for a in interest.authors}
        score = 0.0

        for author in paper.authors:
            name = author.get("name", "")
            if name in interest_authors:
                score += interest_authors[name]

        return min(score, 1.0)

    def _journal_match_score(self, interest: UserInterest, paper: Paper) -> float:
        """计算期刊匹配分数"""
        if not interest.journals or not paper.journal:
            return 0.0

        interest_journals = {j["journal"]: j["weight"] for j in interest.journals}

        if paper.journal in interest_journals:
            return interest_journals[paper.journal]

        return 0.0

    def _determine_reason(
        self,
        sim_score: float,
        cat_score: float,
        author_score: float,
        interest: UserInterest,
        paper: Paper
    ) -> Tuple[RecommendationReason, str]:
        """确定推荐理由"""
        if author_score > 0.5:
            matched_authors = [
                a["name"] for a in paper.authors
                if any(ia["author"] == a.get("name", "") for ia in interest.authors)
            ]
            return (
                RecommendationReason.FOLLOW_AUTHOR,
                f"包含您关注的作者: {', '.join(matched_authors[:2])}"
            )

        if cat_score > 0.5:
            matched_cats = [
                c for c in paper.categories
                if any(ic["category"] == c for ic in interest.categories)
            ]
            return (
                RecommendationReason.BASED_ON_INTEREST,
                f"匹配您的研究兴趣: {', '.join(matched_cats[:2])}"
            )

        if sim_score > 0.3:
            top_keywords = [k["word"] for k in interest.keywords[:5]]
            return (
                RecommendationReason.KEYWORD_MATCH,
                f"与您关注的关键词相关: {', '.join(top_keywords[:3])}"
            )

        return (
            RecommendationReason.BASED_ON_READING,
            "基于您的阅读历史推荐"
        )


class CollaborativeFilteringRecommender:
    """协同过滤推荐器"""

    def __init__(self):
        pass

    async def recommend(
        self,
        user_id: str,
        user_item_matrix: Dict[str, Dict[str, float]],
        candidate_papers: List[Paper],
        top_k: int = 10
    ) -> List[Tuple[Paper, float, RecommendationReason, str]]:
        """
        基于用户的协同过滤

        Args:
            user_id: 目标用户ID
            user_item_matrix: {user_id: {paper_id: rating}}
            candidate_papers: 候选论文
            top_k: 推荐数量
        """
        if user_id not in user_item_matrix:
            return []

        user_ratings = user_item_matrix[user_id]

        # 计算与其他用户的相似度
        similarities = {}
        for other_id, other_ratings in user_item_matrix.items():
            if other_id == user_id:
                continue
            sim = self._cosine_similarity(user_ratings, other_ratings)
            if sim > 0:
                similarities[other_id] = sim

        # 获取最相似的K个用户
        top_users = sorted(similarities.items(), key=lambda x: -x[1])[:20]

        # 预测评分
        predictions = {}
        for paper in candidate_papers:
            score = 0.0
            sim_sum = 0.0

            for other_id, sim in top_users:
                if paper.id in user_item_matrix.get(other_id, {}):
                    score += sim * user_item_matrix[other_id][paper.id]
                    sim_sum += sim

            if sim_sum > 0:
                predictions[paper.id] = score / sim_sum

        # 排序
        sorted_papers = sorted(
            [(p, predictions.get(p.id, 0)) for p in candidate_papers],
            key=lambda x: -x[1]
        )

        return [
            (paper, score, RecommendationReason.SIMILAR_TO_SAVED,
             "与您兴趣相似的用户也关注了这篇论文")
            for paper, score in sorted_papers[:top_k]
            if score > 0
        ]

    def _cosine_similarity(
        self,
        ratings1: Dict[str, float],
        ratings2: Dict[str, float]
    ) -> float:
        """计算余弦相似度"""
        common_items = set(ratings1.keys()) & set(ratings2.keys())

        if not common_items:
            return 0.0

        dot_product = sum(ratings1[item] * ratings2[item] for item in common_items)
        norm1 = math.sqrt(sum(r ** 2 for r in ratings1.values()))
        norm2 = math.sqrt(sum(r ** 2 for r in ratings2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class HybridRecommender:
    """混合推荐引擎"""

    def __init__(self):
        self.content_recommender = ContentBasedRecommender()
        self.cf_recommender = CollaborativeFilteringRecommender()
        self.interest_profiler = InterestProfiler()

    async def recommend(
        self,
        user_id: str,
        user_interest: UserInterest,
        candidate_papers: List[Paper],
        user_item_matrix: Optional[Dict] = None,
        top_k: int = 10,
        diversity_factor: float = 0.3
    ) -> List[DailyRecommendationCreate]:
        """
        混合推荐

        Args:
            user_id: 用户ID
            user_interest: 用户兴趣画像
            candidate_papers: 候选论文
            user_item_matrix: 用户-物品评分矩阵 (用于协同过滤)
            top_k: 推荐数量
            diversity_factor: 多样性因子 (0-1)
        """
        recommendations = []

        # 1. 内容推荐 (权重 0.7)
        content_results = self.content_recommender.recommend(
            user_interest, candidate_papers, top_k * 2
        )

        for paper, score, reason, detail in content_results:
            recommendations.append((
                paper, score * 0.7, reason, detail, "content"
            ))

        # 2. 协同过滤推荐 (权重 0.3, 如果有数据)
        if user_item_matrix and len(user_item_matrix) > 5:
            cf_results = await self.cf_recommender.recommend(
                user_id, user_item_matrix, candidate_papers, top_k
            )

            for paper, score, reason, detail in cf_results:
                recommendations.append((
                    paper, score * 0.3, reason, detail, "collaborative"
                ))

        # 3. 合并并去重
        seen_papers = set()
        unique_recommendations = []

        # 按分数排序
        recommendations.sort(key=lambda x: -x[1])

        for paper, score, reason, detail, algo in recommendations:
            if paper.id not in seen_papers:
                seen_papers.add(paper.id)
                unique_recommendations.append((
                    paper, score, reason, detail, algo
                ))

        # 4. 多样性重排序 (MMR算法)
        if diversity_factor > 0:
            final_recommendations = self._diverse_ranking(
                unique_recommendations, top_k, diversity_factor
            )
        else:
            final_recommendations = unique_recommendations[:top_k]

        # 5. 构建输出
        today = date.today()
        result = []
        for rank, (paper, score, reason, detail, algo) in enumerate(final_recommendations, 1):
            rec = DailyRecommendationCreate(
                user_id=user_id,
                paper_id=paper.id,
                score=round(score, 4),
                reason=reason,
                reason_detail=detail,
                rank=rank,
                recommend_date=today
            )
            result.append(rec)

        return result

    def _diverse_ranking(
        self,
        recommendations: List[Tuple],
        top_k: int,
        lambda_param: float
    ) -> List[Tuple]:
        """
        MMR (Maximal Marginal Relevance) 多样性重排序
        """
        if len(recommendations) <= top_k:
            return recommendations

        selected = []
        remaining = list(recommendations)

        # 首先选择分数最高的
        selected.append(remaining.pop(0))

        while len(selected) < top_k and remaining:
            max_mmr_score = -float('inf')
            max_mmr_idx = 0

            for i, (paper, score, reason, detail, algo) in enumerate(remaining):
                # 计算与已选项目的最大相似度
                max_sim = 0
                for sel_paper, _, _, _, _ in selected:
                    sim = self._paper_similarity(paper, sel_paper)
                    max_sim = max(max_sim, sim)

                # MMR分数
                mmr_score = lambda_param * score - (1 - lambda_param) * max_sim

                if mmr_score > max_mmr_score:
                    max_mmr_score = mmr_score
                    max_mmr_idx = i

            selected.append(remaining.pop(max_mmr_idx))

        return selected

    def _paper_similarity(self, p1: Paper, p2: Paper) -> float:
        """计算两篇论文的相似度"""
        # 类别重叠
        cat_sim = len(set(p1.categories) & set(p2.categories)) / max(
            len(set(p1.categories) | set(p2.categories)), 1
        )

        # 作者重叠
        authors1 = {a.get("name", "") for a in p1.authors}
        authors2 = {a.get("name", "") for a in p2.authors}
        author_sim = len(authors1 & authors2) / max(len(authors1 | authors2), 1)

        return 0.7 * cat_sim + 0.3 * author_sim

    async def explain_recommendation(
        self,
        recommendation: DailyRecommendationCreate,
        user_interest: UserInterest
    ) -> str:
        """生成推荐解释"""
        explanations = {
            RecommendationReason.BASED_ON_INTEREST: f"这篇论文涉及您感兴趣的研究领域",
            RecommendationReason.BASED_ON_READING: f"基于您最近阅读的 {user_interest.reading_patterns.get('total_papers_read', 0)} 篇论文",
            RecommendationReason.FOLLOW_AUTHOR: f"作者匹配",
            RecommendationReason.SIMILAR_TO_SAVED: f"与您收藏的论文相似",
            RecommendationReason.KEYWORD_MATCH: f"匹配您的关注关键词",
            RecommendationReason.TRENDING: f"近期热门论文",
        }

        return explanations.get(recommendation.reason, recommendation.reason_detail)
