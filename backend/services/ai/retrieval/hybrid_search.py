"""
混合检索实现
结合BM25和向量相似度，获得更好的检索效果
"""

import math
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """文档结构"""
    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """搜索结果"""
    doc_id: str
    content: str
    metadata: Dict
    bm25_score: float
    vector_score: float
    hybrid_score: float
    rank: int


class BM25:
    """BM25实现"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: 控制词频饱和度 (1.2-2.0)
            b: 控制文档长度归一化 (0-1)
        """
        self.k1 = k1
        self.b = b
        self.documents: List[str] = []
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_len: List[int] = []
        self.avg_doc_len = 0
        self.N = 0

    def fit(self, documents: List[str]):
        """构建索引"""
        self.documents = documents
        self.N = len(documents)

        # 计算文档频率
        for doc in documents:
            words = set(self._tokenize(doc))
            for word in words:
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1

        # 计算IDF
        for word, freq in self.doc_freqs.items():
            self.idf[word] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1)

        # 计算文档长度
        self.doc_len = [len(self._tokenize(doc)) for doc in documents]
        self.avg_doc_len = sum(self.doc_len) / self.N if self.N > 0 else 0

        return self

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """搜索"""
        scores = []
        query_terms = self._tokenize(query)

        for idx, doc in enumerate(self.documents):
            score = self._score(doc, query_terms, idx)
            scores.append((idx, score))

        # 排序并返回top_k
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]

    def _score(self, doc: str, query_terms: List[str], doc_idx: int) -> float:
        """计算文档得分"""
        doc_terms = self._tokenize(doc)
        doc_len = self.doc_len[doc_idx]

        score = 0
        for term in query_terms:
            if term not in self.idf:
                continue

            # 词频
            tf = doc_terms.count(term)
            if tf == 0:
                continue

            # BM25公式
            idf = self.idf[term]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)

            score += idf * numerator / denominator

        return score

    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        # 简单的空格分词 + 小写化
        # 实际项目中可以使用更复杂的分词器
        return text.lower().split()


class HybridSearcher:
    """混合检索器"""

    def __init__(
        self,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        use_rrf: bool = False
    ):
        """
        Args:
            bm25_weight: BM25分数权重
            vector_weight: 向量分数权重
            use_rrf: 是否使用Reciprocal Rank Fusion
        """
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.use_rrf = use_rrf

        self.bm25 = BM25()
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2)
        )

        self.documents: List[Document] = []
        self.doc_embeddings: Optional[np.ndarray] = None
        self.doc_id_to_idx: Dict[str, int] = {}

    def index(self, documents: List[Document]):
        """
        构建索引

        Args:
            documents: 文档列表
        """
        self.documents = documents

        # 构建BM25索引
        texts = [doc.content for doc in documents]
        self.bm25.fit(texts)

        # 构建向量索引
        if documents and documents[0].embedding:
            # 使用预计算的embedding
            self.doc_embeddings = np.array([doc.embedding for doc in documents])
        else:
            # 使用TF-IDF计算向量
            self.doc_embeddings = self.vectorizer.fit_transform(texts).toarray()

        # 构建ID映射
        for idx, doc in enumerate(documents):
            self.doc_id_to_idx[doc.id] = idx

        logger.info(f"Indexed {len(documents)} documents")

    def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 10,
        filter_fn: Optional[callable] = None
    ) -> List[SearchResult]:
        """
        混合检索

        Args:
            query: 查询文本
            query_embedding: 查询向量（可选）
            top_k: 返回结果数量
            filter_fn: 过滤函数

        Returns:
            搜索结果列表
        """
        # BM25检索
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        bm25_scores = {idx: score for idx, score in bm25_results}

        # 向量检索
        if query_embedding is not None:
            query_vec = np.array(query_embedding).reshape(1, -1)
        else:
            query_vec = self.vectorizer.transform([query]).toarray()

        similarities = cosine_similarity(query_vec, self.doc_embeddings)[0]
        vector_scores = {idx: float(sim) for idx, sim in enumerate(similarities)}

        # 合并结果
        candidate_ids = set(bm25_scores.keys()) | set(
            np.argsort(similarities)[-top_k * 2:]
        )

        # 计算混合分数
        results = []
        for doc_idx in candidate_ids:
            doc = self.documents[doc_idx]

            # 应用过滤
            if filter_fn and not filter_fn(doc):
                continue

            bm25_score = bm25_scores.get(doc_idx, 0)
            vector_score = vector_scores.get(doc_idx, 0)

            # 归一化
            max_bm25 = max(bm25_scores.values()) if bm25_scores else 1
            max_vector = 1.0

            norm_bm25 = bm25_score / max_bm25 if max_bm25 > 0 else 0
            norm_vector = vector_score / max_vector if max_vector > 0 else 0

            # 加权融合
            hybrid_score = (
                self.bm25_weight * norm_bm25 +
                self.vector_weight * norm_vector
            )

            results.append(SearchResult(
                doc_id=doc.id,
                content=doc.content,
                metadata=doc.metadata,
                bm25_score=norm_bm25,
                vector_score=norm_vector,
                hybrid_score=hybrid_score,
                rank=0  # 稍后设置
            ))

        # 排序
        results.sort(key=lambda x: -x.hybrid_score)

        # 设置排名
        for i, result in enumerate(results[:top_k], 1):
            result.rank = i

        return results[:top_k]

    def search_with_rrf(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 10,
        k: int = 60  # RRF常数
    ) -> List[SearchResult]:
        """
        使用Reciprocal Rank Fusion的混合检索

        RRF公式: score = Σ(1 / (k + rank))
        """
        # BM25检索（获取更多用于融合）
        bm25_results = self.bm25.search(query, top_k=top_k * 3)
        bm25_ranks = {idx: rank for rank, (idx, _) in enumerate(bm25_results, 1)}

        # 向量检索
        if query_embedding is not None:
            query_vec = np.array(query_embedding).reshape(1, -1)
        else:
            query_vec = self.vectorizer.transform([query]).toarray()

        similarities = cosine_similarity(query_vec, self.doc_embeddings)[0]
        vector_top_k = np.argsort(similarities)[-top_k * 3:][::-1]
        vector_ranks = {idx: rank for rank, idx in enumerate(vector_top_k, 1)}

        # 计算RRF分数
        all_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())

        rrf_scores = {}
        for doc_idx in all_ids:
            score = 0
            if doc_idx in bm25_ranks:
                score += 1.0 / (k + bm25_ranks[doc_idx])
            if doc_idx in vector_ranks:
                score += 1.0 / (k + vector_ranks[doc_idx])
            rrf_scores[doc_idx] = score

        # 排序并构建结果
        sorted_results = sorted(rrf_scores.items(), key=lambda x: -x[1])

        results = []
        for rank, (doc_idx, score) in enumerate(sorted_results[:top_k], 1):
            doc = self.documents[doc_idx]
            results.append(SearchResult(
                doc_id=doc.id,
                content=doc.content,
                metadata=doc.metadata,
                bm25_score=1.0 / (k + bm25_ranks.get(doc_idx, 999)),
                vector_score=1.0 / (k + vector_ranks.get(doc_idx, 999)),
                hybrid_score=score,
                rank=rank
            ))

        return results


class QueryExpander:
    """查询扩展器"""

    def __init__(self):
        # 简单的同义词词典
        self.synonyms = {
            'llm': ['large language model', 'language model', 'gpt'],
            'nlp': ['natural language processing', 'text processing'],
            'ai': ['artificial intelligence', 'machine intelligence'],
            'ml': ['machine learning', 'deep learning'],
            'cv': ['computer vision', 'image recognition'],
        }

    def expand(self, query: str) -> List[str]:
        """
        扩展查询

        Returns:
            扩展后的查询列表（包含原始查询）
        """
        expanded = [query]
        query_lower = query.lower()

        # 同义词替换
        for term, synonyms in self.synonyms.items():
            if term in query_lower:
                for syn in synonyms:
                    new_query = query_lower.replace(term, syn)
                    if new_query not in expanded:
                        expanded.append(new_query)

        return expanded

    def expand_with_embeddings(
        self,
        query: str,
        embedding_fn: callable,
        top_k: int = 3
    ) -> List[str]:
        """
        使用向量相似度扩展查询
        """
        # 这个方法需要预先定义的嵌入函数
        # 实际实现中可以使用词向量找到相似词
        return self.expand(query)
