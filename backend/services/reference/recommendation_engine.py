"""
智能引用推荐引擎
基于文本上下文和语义相似度推荐相关文献
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

from ..ai.rag_engine import RAGEngine, EmbeddingService, VectorStore
from ..article.repository import ArticleRepository


@dataclass
class CitationRecommendation:
    """引用推荐结果"""
    article_id: str
    title: str
    authors: List[str]
    year: Optional[int]
    journal: Optional[str]
    doi: Optional[str]
    abstract: str
    relevance_score: float  # 0-1 整体相关度
    context_match_score: float  # 上下文匹配度
    semantic_similarity: float  # 语义相似度
    citation_count: int  # 被引次数
    impact_score: float  # 影响力分数
    reason: str  # 推荐理由
    suggested_position: Optional[str] = None  # 建议插入位置

    def to_dict(self) -> Dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "abstract": self.abstract[:200] + "..." if len(self.abstract) > 200 else self.abstract,
            "relevance_score": round(self.relevance_score, 3),
            "context_match_score": round(self.context_match_score, 3),
            "semantic_similarity": round(self.semantic_similarity, 3),
            "citation_count": self.citation_count,
            "impact_score": round(self.impact_score, 2),
            "reason": self.reason,
            "suggested_position": self.suggested_position,
        }


class CitationRecommendationEngine:
    """
    智能引用推荐引擎
    基于多种策略推荐最合适的引用文献
    """

    def __init__(
        self,
        rag_engine: Optional[RAGEngine] = None,
        article_repository: Optional[ArticleRepository] = None,
    ):
        self.rag_engine = rag_engine
        self.article_repo = article_repository
        self.embedding_service = EmbeddingService()

    async def recommend(
        self,
        text: str,
        cursor_position: Optional[int] = None,
        user_id: Optional[str] = None,
        article_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.5,
    ) -> List[CitationRecommendation]:
        """
        基于文本上下文推荐引用

        Args:
            text: 当前文本内容
            cursor_position: 光标位置（用于获取上下文）
            user_id: 用户ID（用于获取用户的文献库）
            article_ids: 指定搜索的文献ID列表
            top_k: 返回推荐数量
            min_score: 最低相关度分数

        Returns:
            List[CitationRecommendation]: 推荐列表
        """
        # 1. 提取上下文
        context = self._extract_context(text, cursor_position)

        # 2. 提取关键词和主题
        keywords = self._extract_keywords(context)

        # 3. 多策略检索
        recommendations = []

        # 策略1: 语义相似度搜索
        semantic_results = await self._semantic_search(
            context, article_ids, top_k=top_k * 2
        )

        # 策略2: 关键词匹配
        keyword_results = await self._keyword_search(
            keywords, article_ids, top_k=top_k * 2
        )

        # 策略3: 协同过滤（如果知道用户ID）
        if user_id:
            collab_results = await self._collaborative_filtering(
                user_id, context, top_k=top_k
            )
        else:
            collab_results = []

        # 4. 合并和去重
        all_candidates = self._merge_candidates(
            semantic_results, keyword_results, collab_results
        )

        # 5. 排序和过滤
        for candidate in all_candidates:
            if candidate.relevance_score >= min_score:
                recommendations.append(candidate)

        # 按相关度排序
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)

        return recommendations[:top_k]

    async def recommend_for_paragraph(
        self,
        paragraph: str,
        existing_citations: Optional[List[str]] = None,
        top_k: int = 3,
    ) -> List[CitationRecommendation]:
        """
        为特定段落推荐引用

        Args:
            paragraph: 段落文本
            existing_citations: 已存在的引用ID（避免重复）
            top_k: 推荐数量

        Returns:
            List[CitationRecommendation]: 推荐列表
        """
        # 分析段落主题
        keywords = self._extract_keywords(paragraph)

        # 检查段落类型（方法、结果、讨论等）
        paragraph_type = self._detect_paragraph_type(paragraph)

        # 根据段落类型调整推荐策略
        if paragraph_type == "methodology":
            # 方法论段落：优先推荐方法论文献
            recommendations = await self._search_methodology_papers(
                paragraph, keywords, top_k=top_k * 2
            )
        elif paragraph_type == "results":
            # 结果段落：优先推荐实证研究
            recommendations = await self._search_empirical_studies(
                paragraph, keywords, top_k=top_k * 2
            )
        elif paragraph_type == "discussion":
            # 讨论段落：优先推荐综述和对比研究
            recommendations = await self._search_review_papers(
                paragraph, keywords, top_k=top_k * 2
            )
        else:
            recommendations = await self.recommend(
                text=paragraph,
                top_k=top_k * 2,
            )

        # 过滤已存在的引用
        if existing_citations:
            recommendations = [
                r for r in recommendations
                if r.article_id not in existing_citations
            ]

        return recommendations[:top_k]

    def _extract_context(
        self,
        text: str,
        cursor_position: Optional[int] = None,
        window_size: int = 200
    ) -> str:
        """
        提取光标周围的上下文

        Args:
            text: 完整文本
            cursor_position: 光标位置
            window_size: 上下文窗口大小（字符数）

        Returns:
            str: 上下文文本
        """
        if cursor_position is None:
            return text[-window_size:] if len(text) > window_size else text

        start = max(0, cursor_position - window_size // 2)
        end = min(len(text), cursor_position + window_size // 2)

        return text[start:end]

    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词

        简化实现：提取名词短语和术语
        实际应用可以使用NLP库（如jieba, spaCy）
        """
        # 移除停用词和标点
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     '的', '了', '在', '是', '和', '与', '或', '有', '被', '这个'}

        # 简单的词提取（实际应用使用NLP）
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        words = [w for w in words if w not in stop_words]

        # 统计词频
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # 返回高频词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:10]]

    def _detect_paragraph_type(self, paragraph: str) -> str:
        """
        检测段落类型

        Returns:
            str: 段落类型 (introduction/methodology/results/discussion/conclusion)
        """
        paragraph_lower = paragraph.lower()

        indicators = {
            "methodology": ['method', 'methodology', 'approach', 'procedure',
                           '步骤', '方法', '实验设计', '数据采集'],
            "results": ['result', 'finding', 'show', 'demonstrate', 'observed',
                       '结果', '发现', '表明', '显示'],
            "discussion": ['discuss', 'implication', 'compare', 'contrast',
                          '讨论', '分析', '对比', '影响'],
            "introduction": ['introduction', 'background', 'literature',
                            '引言', '背景', '文献'],
            "conclusion": ['conclusion', 'conclude', 'summary', 'future',
                          '结论', '总结', '展望'],
        }

        scores = {}
        for ptype, words in indicators.items():
            score = sum(1 for word in words if word in paragraph_lower)
            scores[ptype] = score

        return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"

    async def _semantic_search(
        self,
        context: str,
        article_ids: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[CitationRecommendation]:
        """
        基于语义相似度的搜索
        """
        if not self.rag_engine:
            return []

        # 使用RAG引擎检索
        retrieved = await self.rag_engine.retrieve(
            query=context,
            top_k=top_k,
        )

        recommendations = []
        for doc in retrieved:
            # 计算综合分数
            relevance = doc.score * 0.6  # 语义相似度权重60%
            context_match = self._calculate_context_match(context, doc.content) * 0.4

            recommendations.append(CitationRecommendation(
                article_id=doc.article_id,
                title=doc.title,
                authors=doc.authors,
                year=doc.year,
                journal=doc.journal,
                doi=doc.doi,
                abstract=doc.content,
                relevance_score=relevance + context_match,
                context_match_score=context_match,
                semantic_similarity=doc.score,
                citation_count=doc.metadata.get("citation_count", 0),
                impact_score=self._calculate_impact_score(doc.metadata),
                reason=f"与当前上下文语义相似度为 {doc.score:.2f}",
            ))

        return recommendations

    async def _keyword_search(
        self,
        keywords: List[str],
        article_ids: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[CitationRecommendation]:
        """
        基于关键词的搜索
        """
        if not self.article_repo or not keywords:
            return []

        # 构建查询
        query = " ".join(keywords[:5])

        # 从文章库搜索
        articles = await self.article_repo.search_articles(
            query=query,
            limit=top_k,
        )

        recommendations = []
        for article in articles:
            # 计算关键词匹配度
            keyword_match = self._calculate_keyword_match(
                keywords, article.get("keywords", [])
            )

            if keyword_match > 0.3:  # 最低匹配阈值
                recommendations.append(CitationRecommendation(
                    article_id=article["id"],
                    title=article["title"],
                    authors=article.get("authors", []),
                    year=article.get("publication_year"),
                    journal=article.get("journal"),
                    doi=article.get("doi"),
                    abstract=article.get("abstract", ""),
                    relevance_score=keyword_match * 0.7,  # 关键词匹配权重70%
                    context_match_score=keyword_match,
                    semantic_similarity=0.0,
                    citation_count=article.get("citation_count", 0),
                    impact_score=self._calculate_impact_score(article),
                    reason=f"关键词匹配度: {keyword_match:.2f}",
                ))

        return recommendations

    async def _collaborative_filtering(
        self,
        user_id: str,
        context: str,
        top_k: int = 5
    ) -> List[CitationRecommendation]:
        """
        基于协同过滤的推荐
        推荐相似用户使用的文献
        """
        # TODO: 实现协同过滤逻辑
        # 需要用户行为数据和相似度计算
        return []

    async def _search_methodology_papers(
        self,
        context: str,
        keywords: List[str],
        top_k: int = 10
    ) -> List[CitationRecommendation]:
        """
        搜索方法论相关论文
        """
        # 添加方法论文献筛选
        method_keywords = keywords + ['methodology', 'approach', 'framework', 'method']
        return await self._keyword_search(method_keywords, top_k=top_k)

    async def _search_empirical_studies(
        self,
        context: str,
        keywords: List[str],
        top_k: int = 10
    ) -> List[CitationRecommendation]:
        """
        搜索实证研究
        """
        empirical_keywords = keywords + ['empirical', 'study', 'experiment', 'data']
        return await self._keyword_search(empirical_keywords, top_k=top_k)

    async def _search_review_papers(
        self,
        context: str,
        keywords: List[str],
        top_k: int = 10
    ) -> List[CitationRecommendation]:
        """
        搜索综述论文
        """
        review_keywords = keywords + ['review', 'survey', 'meta-analysis', 'overview']
        return await self._keyword_search(review_keywords, top_k=top_k)

    def _calculate_context_match(
        self,
        context: str,
        article_text: str
    ) -> float:
        """
        计算上下文匹配度
        """
        context_words = set(context.lower().split())
        article_words = set(article_text.lower().split())

        if not context_words:
            return 0.0

        intersection = context_words & article_words
        return len(intersection) / len(context_words)

    def _calculate_keyword_match(
        self,
        query_keywords: List[str],
        article_keywords: List[str]
    ) -> float:
        """
        计算关键词匹配度
        """
        if not query_keywords or not article_keywords:
            return 0.0

        query_set = set(k.lower() for k in query_keywords)
        article_set = set(k.lower() for k in article_keywords)

        intersection = query_set & article_set
        return len(intersection) / len(query_set)

    def _calculate_impact_score(self, metadata: Dict[str, Any]) -> float:
        """
        计算文献影响力分数

        基于：引用次数、期刊影响因子、发表年份
        """
        score = 0.0

        # 引用次数（归一化到0-50）
        citation_count = metadata.get("citation_count", 0)
        score += min(citation_count / 10, 50)

        # 期刊影响因子（0-30）
        impact_factor = metadata.get("journal_impact_factor", 0)
        score += min(impact_factor * 3, 30)

        # 时效性（0-20）
        year = metadata.get("publication_year", datetime.now().year)
        years_ago = datetime.now().year - year
        if years_ago <= 2:
            score += 20
        elif years_ago <= 5:
            score += 15
        elif years_ago <= 10:
            score += 10
        else:
            score += 5

        return score

    def _merge_candidates(
        self,
        *candidate_lists: List[CitationRecommendation]
    ) -> List[CitationRecommendation]:
        """
        合并多个候选列表并去重
        """
        seen_ids = set()
        merged = []

        for candidates in candidate_lists:
            for candidate in candidates:
                if candidate.article_id not in seen_ids:
                    seen_ids.add(candidate.article_id)
                    merged.append(candidate)
                else:
                    # 合并分数
                    existing = next(
                        (c for c in merged if c.article_id == candidate.article_id),
                        None
                    )
                    if existing:
                        existing.relevance_score = max(
                            existing.relevance_score,
                            candidate.relevance_score
                        )

        return merged


# 服务实例
_recommendation_engine: Optional[CitationRecommendationEngine] = None


def get_recommendation_engine(
    rag_engine: Optional[RAGEngine] = None,
    article_repository: Optional[ArticleRepository] = None,
) -> CitationRecommendationEngine:
    """获取推荐引擎单例"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = CitationRecommendationEngine(
            rag_engine=rag_engine,
            article_repository=article_repository,
        )
    return _recommendation_engine
