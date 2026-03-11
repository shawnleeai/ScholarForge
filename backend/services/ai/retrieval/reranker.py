"""
重排序模块
使用Cross-Encoder等模型对初筛结果进行精细排序
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
import asyncio

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RankedDocument:
    """重排序后的文档"""
    doc_id: str
    content: str
    metadata: dict
    initial_score: float
    rerank_score: float
    final_score: float
    rank_before: int
    rank_after: int


class CrossEncoderReranker:
    """
    基于Cross-Encoder的重排序器

    Cross-Encoder将查询和文档一起编码，可以更准确地判断相关性
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        batch_size: int = 8
    ):
        """
        Args:
            model_name: Cross-Encoder模型名称
            batch_size: 批处理大小
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = None
        self._load_model()

    def _load_model(self):
        """加载模型"""
        try:
            # 尝试加载sentence-transformers的CrossEncoder
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
            logger.info(f"Loaded CrossEncoder: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder: {e}")
            self.model = None

    async def rerank(
        self,
        query: str,
        documents: List[Tuple[str, str, dict, float]],  # (id, content, metadata, initial_score)
        top_k: int = 10,
        alpha: float = 0.7  # rerank分数权重
    ) -> List[RankedDocument]:
        """
        重排序文档

        Args:
            query: 查询
            documents: [(doc_id, content, metadata, initial_score), ...]
            top_k: 返回数量
            alpha: 最终分数中rerank的权重

        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []

        if self.model is None:
            # 如果没有模型，按初始分数返回
            return [
                RankedDocument(
                    doc_id=doc[0],
                    content=doc[1],
                    metadata=doc[2],
                    initial_score=doc[3],
                    rerank_score=doc[3],
                    final_score=doc[3],
                    rank_before=i+1,
                    rank_after=i+1
                )
                for i, doc in enumerate(documents[:top_k])
            ]

        # 构建pairs
        pairs = [(query, doc[1][:512]) for doc in documents]  # 截断避免过长

        # 批量预测
        try:
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                lambda: self.model.predict(pairs, batch_size=self.batch_size)
            )
        except Exception as e:
            logger.error(f"CrossEncoder prediction failed: {e}")
            scores = [0.5] * len(documents)

        # 组合分数
        results = []
        for i, (doc, rerank_score) in enumerate(zip(documents, scores)):
            doc_id, content, metadata, initial_score = doc

            # 归一化rerank分数
            rerank_norm = float(rerank_score)

            # 最终分数
            final_score = alpha * rerank_norm + (1 - alpha) * initial_score

            results.append(RankedDocument(
                doc_id=doc_id,
                content=content,
                metadata=metadata,
                initial_score=initial_score,
                rerank_score=rerank_norm,
                final_score=final_score,
                rank_before=i+1,
                rank_after=0  # 稍后设置
            ))

        # 按最终分数排序
        results.sort(key=lambda x: -x.final_score)

        # 设置新排名
        for i, result in enumerate(results[:top_k], 1):
            result.rank_after = i

        return results[:top_k]


class LLMReranker:
    """
    基于LLM的重排序器

    使用大语言模型判断文档与查询的相关性
    更准确但成本更高
    """

    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLM客户端
        """
        self.llm = llm_client

    async def rerank(
        self,
        query: str,
        documents: List[Tuple[str, str, dict, float]],
        top_k: int = 5
    ) -> List[RankedDocument]:
        """
        使用LLM重排序

        由于LLM调用成本高，建议只对少量文档（如top-10）使用
        """
        results = []

        # 只处理前10个文档
        docs_to_rerank = documents[:10]

        for i, (doc_id, content, metadata, initial_score) in enumerate(docs_to_rerank):
            try:
                # 截断内容避免过长
                truncated_content = content[:500]

                # 构建提示
                prompt = f"""评估以下文档与用户查询的相关性。

用户查询: {query}

文档内容: {truncated_content}

请评分:
- 5分: 文档直接回答查询
- 4分: 文档高度相关，包含大部分答案
- 3分: 文档部分相关
- 2分: 文档略微相关
- 1分: 文档不相关

只输出1-5的数字评分:"""

                response = await self.llm.generate(prompt)

                # 解析分数
                try:
                    score = float(response.strip()[0])
                    score = max(1, min(5, score)) / 5.0  # 归一化到0-1
                except:
                    score = 0.5

                results.append(RankedDocument(
                    doc_id=doc_id,
                    content=content,
                    metadata=metadata,
                    initial_score=initial_score,
                    rerank_score=score,
                    final_score=score * 0.8 + initial_score * 0.2,
                    rank_before=i+1,
                    rank_after=0
                ))

            except Exception as e:
                logger.error(f"LLM rerank failed for doc {doc_id}: {e}")
                results.append(RankedDocument(
                    doc_id=doc_id,
                    content=content,
                    metadata=metadata,
                    initial_score=initial_score,
                    rerank_score=initial_score,
                    final_score=initial_score,
                    rank_before=i+1,
                    rank_after=0
                ))

        # 排序
        results.sort(key=lambda x: -x.final_score)

        for i, result in enumerate(results[:top_k], 1):
            result.rank_after = i

        return results[:top_k]


class DiversityReranker:
    """
    多样性重排序器

    基于MMR (Maximal Marginal Relevance)算法
    在相关性和多样性之间做权衡
    """

    def __init__(self, lambda_param: float = 0.5):
        """
        Args:
            lambda_param: 相关性权重 (0-1)，越大越注重相关性
        """
        self.lambda_param = lambda_param

    def rerank(
        self,
        query: str,
        documents: List[Tuple[str, str, dict, float]],
        embeddings: Optional[dict] = None,
        top_k: int = 10
    ) -> List[RankedDocument]:
        """
        MMR重排序

        MMR = λ * Relevance - (1-λ) * max(Similarity(selected_docs))
        """
        if not documents:
            return []

        # 如果没有提供embeddings，使用简单实现
        selected = []
        remaining = list(range(len(documents)))

        # 先选相关性最高的
        first_idx = max(remaining, key=lambda i: documents[i][3])
        selected.append(first_idx)
        remaining.remove(first_idx)

        # 迭代选择
        while len(selected) < top_k and remaining:
            max_mmr_score = -float('inf')
            max_mmr_idx = -1

            for idx in remaining:
                doc = documents[idx]
                relevance = doc[3]  # 初始分数作为相关性

                # 计算与已选文档的最大相似度
                max_sim = 0
                for sel_idx in selected:
                    sim = self._similarity(documents[idx], documents[sel_idx])
                    max_sim = max(max_sim, sim)

                # MMR分数
                mmr_score = (
                    self.lambda_param * relevance -
                    (1 - self.lambda_param) * max_sim
                )

                if mmr_score > max_mmr_score:
                    max_mmr_score = mmr_score
                    max_mmr_idx = idx

            if max_mmr_idx >= 0:
                selected.append(max_mmr_idx)
                remaining.remove(max_mmr_idx)

        # 构建结果
        results = []
        for rank, idx in enumerate(selected, 1):
            doc_id, content, metadata, initial_score = documents[idx]
            results.append(RankedDocument(
                doc_id=doc_id,
                content=content,
                metadata=metadata,
                initial_score=initial_score,
                rerank_score=initial_score,  # MMR不重新打分
                final_score=initial_score,
                rank_before=idx+1,
                rank_after=rank
            ))

        return results

    def _similarity(
        self,
        doc1: Tuple[str, str, dict, float],
        doc2: Tuple[str, str, dict, float]
    ) -> float:
        """计算两篇文档的相似度（简单实现）"""
        # 基于类别的Jaccard相似度
        cats1 = set(doc1[2].get('categories', []))
        cats2 = set(doc2[2].get('categories', []))

        if not cats1 or not cats2:
            return 0

        intersection = len(cats1 & cats2)
        union = len(cats1 | cats2)

        return intersection / union if union > 0 else 0


class Reranker:
    """
    统一的重排序接口
    """

    def __init__(
        self,
        cross_encoder_model: Optional[str] = None,
        llm_client=None,
        use_diversity: bool = True
    ):
        """
        Args:
            cross_encoder_model: CrossEncoder模型名
            llm_client: LLM客户端
            use_diversity: 是否使用多样性重排序
        """
        self.cross_encoder = None
        self.llm_reranker = None
        self.diversity_reranker = None

        if cross_encoder_model:
            self.cross_encoder = CrossEncoderReranker(cross_encoder_model)

        if llm_client:
            self.llm_reranker = LLMReranker(llm_client)

        if use_diversity:
            self.diversity_reranker = DiversityReranker()

    async def rerank(
        self,
        query: str,
        documents: List[Tuple[str, str, dict, float]],
        top_k: int = 10,
        use_llm: bool = False
    ) -> List[RankedDocument]:
        """
        多阶段重排序

        1. Cross-Encoder重排序（如果有）
        2. LLM重排序（如果use_llm=True）
        3. 多样性重排序（如果有）
        """
        current_docs = documents

        # 阶段1: Cross-Encoder
        if self.cross_encoder:
            results = await self.cross_encoder.rerank(
                query, current_docs, top_k=len(current_docs)
            )
            current_docs = [
                (r.doc_id, r.content, r.metadata, r.final_score)
                for r in results
            ]

        # 阶段2: LLM (可选，成本高)
        if use_llm and self.llm_reranker:
            results = await self.llm_reranker.rerank(
                query, current_docs, top_k=min(10, len(current_docs))
            )
            current_docs = [
                (r.doc_id, r.content, r.metadata, r.final_score)
                for r in results
            ]

        # 阶段3: 多样性
        if self.diversity_reranker:
            return self.diversity_reranker.rerank(
                query, current_docs, top_k=top_k
            )

        # 如果没有配置任何重排序器，返回原始顺序
        return [
            RankedDocument(
                doc_id=doc[0],
                content=doc[1],
                metadata=doc[2],
                initial_score=doc[3],
                rerank_score=doc[3],
                final_score=doc[3],
                rank_before=i+1,
                rank_after=i+1
            )
            for i, doc in enumerate(current_docs[:top_k])
        ]
