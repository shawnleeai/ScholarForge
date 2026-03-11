"""
RAG (Retrieval-Augmented Generation) 引擎
实现基于向量检索的增强生成，为AI问答提供精准的文献引用
"""

import json
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from .conversation_models import Citation, ConversationContext, Message


@dataclass
class RetrievalResult:
    """检索结果"""
    article_id: str
    title: str
    content: str  # 检索到的文本片段
    authors: List[str]
    year: Optional[int]
    journal: Optional[str]
    doi: Optional[str]
    score: float  # 相似度分数
    metadata: Dict[str, Any]

    def to_citation(self) -> Citation:
        """转换为引用格式"""
        return Citation(
            id=f"cite_{self.article_id}",
            article_id=self.article_id,
            title=self.title,
            authors=self.authors,
            year=self.year,
            journal=self.journal,
            doi=self.doi,
            snippet=self.content[:200] + "..." if len(self.content) > 200 else self.content,
            relevance_score=self.score,
        )


@dataclass
class RAGContext:
    """RAG上下文"""
    query: str
    retrieved_documents: List[RetrievalResult]
    formatted_context: str
    total_tokens: int
    retrieval_time_ms: int


class VectorStore:
    """
    向量存储接口
    实际实现可以使用: Pinecone, Weaviate, Milvus, 或 PostgreSQL + pgvector
    """

    def __init__(self, embedding_dimension: int = 1536):
        self.embedding_dimension = embedding_dimension
        # 内存存储（实际应用使用外部向量数据库）
        self._vectors: Dict[str, np.ndarray] = {}
        self._documents: Dict[str, Dict[str, Any]] = {}

    async def add_document(
        self,
        doc_id: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加文档到向量存储"""
        self._vectors[doc_id] = np.array(embedding)
        self._documents[doc_id] = {
            "text": text,
            "metadata": metadata or {},
        }

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float]]:
        """
        向量相似度搜索

        Returns:
            List[Tuple[doc_id, score]]: 文档ID和相似度分数
        """
        if not self._vectors:
            return []

        query_vec = np.array(query_embedding)
        results = []

        for doc_id, vec in self._vectors.items():
            # 检查过滤器
            if filter_metadata:
                doc_meta = self._documents[doc_id].get("metadata", {})
                if not all(doc_meta.get(k) == v for k, v in filter_metadata.items()):
                    continue

            # 计算余弦相似度
            similarity = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec))
            results.append((doc_id, float(similarity)))

        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def delete_document(self, doc_id: str):
        """删除文档"""
        if doc_id in self._vectors:
            del self._vectors[doc_id]
        if doc_id in self._documents:
            del self._documents[doc_id]


class EmbeddingService:
    """
    文本嵌入服务
    使用OpenAI, Sentence-Transformers等模型生成向量
    """

    def __init__(self, provider: str = "openai", model: str = "text-embedding-3-small"):
        self.provider = provider
        self.model = model
        self._cache: Dict[str, List[float]] = {}
        self._client = None
        self._dimension = 1536  # OpenAI text-embedding-3-small 维度

        # 根据提供商设置维度
        if "large" in model:
            self._dimension = 3072
        elif "ada" in model:
            self._dimension = 1536

    def _get_client(self):
        """懒加载客户端"""
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            try:
                from openai import AsyncOpenAI
                import os
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self._client = AsyncOpenAI(api_key=api_key)
            except ImportError:
                pass

        return self._client

    async def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        获取文本的向量表示

        Args:
            text: 输入文本
            use_cache: 是否使用缓存

        Returns:
            List[float]: 向量表示
        """
        # 检查缓存
        cache_key = hash(text)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        embedding = None

        # 尝试使用真实API
        client = self._get_client()
        if client and self.provider == "openai":
            try:
                response = await client.embeddings.create(
                    model=self.model,
                    input=text
                )
                embedding = response.data[0].embedding
            except Exception as e:
                # API调用失败，使用模拟
                print(f"[Embedding] OpenAI API error: {e}, falling back to mock")

        # 回退到模拟嵌入
        if embedding is None:
            await asyncio.sleep(0.01)  # 模拟延迟
            embedding = self._mock_embedding(text)

        if use_cache:
            self._cache[cache_key] = embedding

        return embedding

    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """批量获取嵌入"""
        client = self._get_client()

        # 尝试批量API调用
        if client and self.provider == "openai":
            try:
                embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = await client.embeddings.create(
                        model=self.model,
                        input=batch
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    embeddings.extend(batch_embeddings)
                return embeddings
            except Exception as e:
                print(f"[Embedding] Batch API error: {e}, falling back to sequential")

        # 回退到逐个获取
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await asyncio.gather(*[
                self.get_embedding(text) for text in batch
            ])
            embeddings.extend(batch_embeddings)
        return embeddings

    def _mock_embedding(self, text: str, dimension: int = None) -> List[float]:
        """模拟嵌入（实际应用删除）"""
        if dimension is None:
            dimension = self._dimension
        np.random.seed(hash(text) % 2**32)
        vec = np.random.randn(dimension)
        vec = vec / np.linalg.norm(vec)  # 归一化
        return vec.tolist()


class RAGEngine:
    """
    RAG引擎
    协调检索和生成的完整流程
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        llm_service=None,  # LLMService from llm_provider_v2
    ):
        self.vector_store = vector_store or VectorStore()
        self.embedding_service = embedding_service or EmbeddingService()
        self.llm_service = llm_service

        # 检索配置
        self.default_top_k = 5
        self.max_context_length = 3000
        self.min_relevance_score = 0.7

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_criteria: Optional[Dict[str, Any]] = None,
        context: Optional[ConversationContext] = None
    ) -> List[RetrievalResult]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_criteria: 过滤条件
            context: 会话上下文（用于个性化检索）

        Returns:
            List[RetrievalResult]: 检索结果
        """
        top_k = top_k or self.default_top_k

        # 1. 生成查询向量
        query_embedding = await self.embedding_service.get_embedding(query)

        # 2. 构建过滤器
        filter_metadata = {}
        if context and context.article_ids:
            # 限制在指定的文献范围内检索
            filter_metadata["article_id"] = {"$in": context.article_ids}

        if filter_criteria:
            filter_metadata.update(filter_criteria)

        # 3. 执行向量搜索
        search_results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # 多检索一些用于重排序
            filter_metadata=filter_metadata if filter_metadata else None
        )

        # 4. 构建结果
        results = []
        for doc_id, score in search_results:
            if score < self.min_relevance_score:
                continue

            doc = self.vector_store._documents.get(doc_id, {})
            metadata = doc.get("metadata", {})

            results.append(RetrievalResult(
                article_id=metadata.get("article_id", doc_id),
                title=metadata.get("title", "Unknown"),
                content=doc.get("text", ""),
                authors=metadata.get("authors", []),
                year=metadata.get("year"),
                journal=metadata.get("journal"),
                doi=metadata.get("doi"),
                score=score,
                metadata=metadata,
            ))

        # 5. 重排序（可以使用Cross-Encoder等更精确的模型）
        results = await self._rerank_results(query, results)

        return results[:top_k]

    async def _rerank_results(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        重排序检索结果
        可以使用更精确的Cross-Encoder模型
        """
        # TODO: 实现Cross-Encoder重排序
        # 目前按原始分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    async def build_context(
        self,
        query: str,
        retrieved_documents: List[RetrievalResult],
        include_citations: bool = True
    ) -> RAGContext:
        """
        构建LLM上下文

        Args:
            query: 用户查询
            retrieved_documents: 检索到的文档
            include_citations: 是否包含引用信息

        Returns:
            RAGContext: 格式化后的上下文
        """
        start_time = datetime.now()

        # 构建上下文字符串
        context_parts = []
        total_tokens = 0

        # 系统提示
        system_prompt = """你是一个学术研究助手。请基于以下提供的文献资料回答用户的问题。
在回答时，请注意：
1. 优先使用提供的文献资料中的信息
2. 如果资料不足以回答问题，请明确说明
3. 在回答中引用相关文献，使用 [1], [2] 等格式标注
4. 保持学术严谨性，不编造信息

以下是相关文献资料：

"""
        context_parts.append(system_prompt)
        total_tokens += len(system_prompt) // 4  # 粗略估算

        # 添加检索到的文档
        for i, doc in enumerate(retrieved_documents, 1):
            doc_text = f"[{i}] {doc.title}"
            if doc.authors:
                doc_text += f"\n作者: {', '.join(doc.authors)}"
            if doc.year:
                doc_text += f" ({doc.year})"
            doc_text += f"\n内容: {doc.content}\n\n"

            # 检查token限制
            estimated_tokens = len(doc_text) // 4
            if total_tokens + estimated_tokens > self.max_context_length:
                break

            context_parts.append(doc_text)
            total_tokens += estimated_tokens

        # 用户问题
        context_parts.append(f"用户问题: {query}\n")
        context_parts.append("请基于以上资料回答，并在相关处标注引用编号。")

        formatted_context = "".join(context_parts)

        retrieval_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return RAGContext(
            query=query,
            retrieved_documents=retrieved_documents,
            formatted_context=formatted_context,
            total_tokens=total_tokens,
            retrieval_time_ms=retrieval_time,
        )

    async def generate_answer(
        self,
        query: str,
        context: Optional[ConversationContext] = None,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        生成带引用的回答

        Args:
            query: 用户查询
            context: 会话上下文
            conversation_history: 对话历史
            stream: 是否流式输出

        Returns:
            Dict: 包含回答和引用信息
        """
        start_time = datetime.now()

        # 1. 检索相关文档
        retrieved_docs = await self.retrieve(
            query=query,
            context=context
        )

        # 2. 构建上下文
        rag_context = await self.build_context(query, retrieved_docs)

        # 3. 准备消息
        messages = []

        # 添加系统消息
        messages.append({
            "role": "system",
            "content": rag_context.formatted_context,
        })

        # 添加对话历史（最近几条）
        if conversation_history:
            for msg in conversation_history[-3:]:  # 最近3条
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        # 添加当前查询
        messages.append({
            "role": "user",
            "content": query,
        })

        # 4. 调用LLM生成回答
        if not self.llm_service:
            # 模拟生成
            answer = self._mock_generate_answer(query, retrieved_docs)
            citations = [doc.to_citation() for doc in retrieved_docs[:3]]
        else:
            # 实际LLM调用
            if stream:
                # 流式生成
                return await self._stream_answer(messages, retrieved_docs)
            else:
                result = await self.llm_service.generate(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2000,
                )
                answer = result.content if hasattr(result, 'content') else str(result)
                citations = [doc.to_citation() for doc in retrieved_docs if doc.score > 0.8]

        generation_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "answer": answer,
            "citations": [c.to_dict() for c in citations],
            "retrieval_info": {
                "retrieved_count": len(retrieved_docs),
                "context_tokens": rag_context.total_tokens,
                "retrieval_time_ms": rag_context.retrieval_time_ms,
            },
            "generation_time_ms": generation_time,
        }

    async def _stream_answer(
        self,
        messages: List[Dict[str, str]],
        retrieved_docs: List[RetrievalResult]
    ):
        """流式生成回答"""
        citations = [doc.to_citation() for doc in retrieved_docs if doc.score > 0.8]

        async def generator():
            try:
                if self.llm_service and hasattr(self.llm_service, 'generate_stream'):
                    # 使用真实LLM流式生成
                    prompt = messages[-1]["content"] if messages else ""
                    system_prompt = None
                    for msg in messages:
                        if msg["role"] == "system":
                            system_prompt = msg["content"]
                            break

                    full_answer = ""
                    async for chunk in self.llm_service.generate_stream(
                        prompt=prompt,
                        max_tokens=2000,
                        temperature=0.3,
                        system_prompt=system_prompt,
                    ):
                        full_answer += chunk
                        yield {
                            "chunk": chunk,
                            "is_final": False,
                            "citations": None,
                        }

                    # 发送最终消息，包含引用
                    yield {
                        "chunk": "",
                        "is_final": True,
                        "citations": [c.to_dict() for c in citations],
                        "full_answer": full_answer,
                    }
                else:
                    # 回退到模拟流式输出
                    answer = self._mock_generate_answer(messages[-1]["content"] if messages else "", retrieved_docs)
                    words = answer.split()
                    for i, word in enumerate(words):
                        yield {
                            "chunk": word + " ",
                            "is_final": i == len(words) - 1,
                            "citations": [c.to_dict() for c in citations] if i == len(words) - 1 else None,
                        }
                        await asyncio.sleep(0.01)
            except Exception as e:
                yield {
                    "chunk": f"\n[错误: {str(e)}]",
                    "is_final": True,
                    "citations": [],
                    "error": str(e),
                }

        return generator()

    def _mock_generate_answer(
        self,
        query: str,
        retrieved_docs: List[RetrievalResult]
    ) -> str:
        """模拟生成回答（实际应用删除）"""
        if not retrieved_docs:
            return "根据提供的文献资料，我暂时没有找到足够的信息来回答这个问题。建议扩大检索范围或提供更多相关文献。"

        answer_parts = []
        answer_parts.append("基于检索到的文献资料，我为您总结如下：\n")

        for i, doc in enumerate(retrieved_docs[:3], 1):
            answer_parts.append(f"\n{i}. {doc.title}")
            answer_parts.append(f"   该研究指出：{doc.content[:100]}... [引用: {i}]")

        answer_parts.append("\n\n综合来看，这些研究表明该领域仍在快速发展中，建议您进一步阅读原始文献以获取更详细的信息。")

        return "\n".join(answer_parts)

    async def index_document(
        self,
        article_id: str,
        title: str,
        abstract: str,
        full_text: Optional[str] = None,
        authors: Optional[List[str]] = None,
        year: Optional[int] = None,
        journal: Optional[str] = None,
        doi: Optional[str] = None,
        chunks: Optional[List[str]] = None
    ):
        """
        将文档索引到向量存储

        Args:
            article_id: 文献ID
            title: 标题
            abstract: 摘要
            full_text: 全文（可选）
            authors: 作者列表
            year: 年份
            journal: 期刊
            doi: DOI
            chunks: 预分块的文本（可选）
        """
        # 准备元数据
        metadata = {
            "article_id": article_id,
            "title": title,
            "authors": authors or [],
            "year": year,
            "journal": journal,
            "doi": doi,
        }

        # 如果没有提供chunks，自动生成
        if not chunks:
            chunks = self._chunk_text(abstract + "\n" + (full_text or ""))

        # 对每个chunk生成嵌入并存储
        for i, chunk in enumerate(chunks):
            embedding = await self.embedding_service.get_embedding(chunk)
            doc_id = f"{article_id}_chunk_{i}"

            await self.vector_store.add_document(
                doc_id=doc_id,
                text=chunk,
                embedding=embedding,
                metadata={**metadata, "chunk_index": i},
            )

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        将长文本分块

        Args:
            text: 原始文本
            chunk_size: 每块大小（字符数）
            overlap: 块之间重叠大小

        Returns:
            List[str]: 文本块列表
        """
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap

        return chunks

    async def delete_document_index(self, article_id: str):
        """删除文档索引"""
        # 查找所有相关chunk
        doc_ids_to_delete = []
        for doc_id in list(self.vector_store._documents.keys()):
            if doc_id.startswith(f"{article_id}_chunk_"):
                doc_ids_to_delete.append(doc_id)

        # 删除
        for doc_id in doc_ids_to_delete:
            await self.vector_store.delete_document(doc_id)


# RAG服务实例
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine(
    vector_store: Optional[VectorStore] = None,
    embedding_service: Optional[EmbeddingService] = None,
    llm_service=None
) -> RAGEngine:
    """获取RAG引擎单例"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine(
            vector_store=vector_store,
            embedding_service=embedding_service,
            llm_service=llm_service,
        )
    return _rag_engine
