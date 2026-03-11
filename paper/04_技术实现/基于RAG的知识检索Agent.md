# 4.2 基于RAG的知识检索Agent

知识检索Agent是ScholarForge系统的另一核心组件，负责为用户提供精准的学术知识检索服务。本节详细介绍基于检索增强生成（Retrieval-Augmented Generation, RAG）的知识检索Agent的实现。

## 4.2.1 知识库构建

### （1）文档处理流程

**文档采集**：
系统支持多种来源的文档采集：

| 来源类型 | 采集方式 | 处理特点 |
|----------|----------|----------|
| PDF文献 | 文件上传 | 解析文本、提取元数据 |
| 网页文章 | URL抓取 | 清洗HTML、提取正文 |
| 数据库文献 | API对接 | 格式化转换、去重 |
| 用户笔记 | 直接录入 | 实时索引、即时可用 |

**文档解析**：

PDF解析是文献处理的关键环节：

```python
class PDFParser:
    def parse(self, pdf_path: str) -> ParsedDocument:
        # 1. 提取文本
        text = self._extract_text(pdf_path)

        # 2. 提取元数据
        metadata = self._extract_metadata(pdf_path)

        # 3. 识别章节结构
        sections = self._identify_sections(text)

        # 4. 提取引用
        references = self._extract_references(text)

        return ParsedDocument(
            text=text,
            metadata=metadata,
            sections=sections,
            references=references
        )
```

**文档切分策略**：

将长文档切分为适合检索的片段：

```python
class DocumentChunker:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 128
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        document: str,
        strategy: str = "sliding_window"
    ) -> List[DocumentChunk]:
        """
        文档切分策略：
        1. sliding_window: 滑动窗口，保证上下文连续性
        2. paragraph: 按段落切分，保持语义完整性
        3. section: 按章节切分，适合结构化文档
        """
        if strategy == "sliding_window":
            return self._sliding_window_chunk(document)
        elif strategy == "paragraph":
            return self._paragraph_chunk(document)
        elif strategy == "section":
            return self._section_chunk(document)
```

切分策略对比：

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 滑动窗口 | 上下文连续 | 可能切断语义 | 通用场景 |
| 段落切分 | 语义完整 | 长度不均 | 结构化文本 |
| 章节切分 | 结构清晰 | 粒度过大 | 目录检索 |

### （2）向量化方法

**嵌入模型选择**：

| 模型 | 维度 | 特点 | 适用场景 |
|------|------|------|----------|
| text-embedding-ada-002 | 1536 | 通用性强 | 多领域文献 |
| text-embedding-3-large | 3072 | 精度高 | 高质量检索 |
| BGE-large-zh | 1024 | 中文优化 | 中文文献 |
| GTE-large | 1024 | 开源高效 | 成本控制 |

**向量化实现**：

```python
class EmbeddingService:
    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
        self.client = OpenAI()

    async def embed_text(self, text: str) -> List[float]:
        """将文本转换为向量"""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """批量向量化"""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            embeddings.extend([d.embedding for d in response.data])
        return embeddings
```

**混合表示策略**：

结合稀疏向量（关键词）和稠密向量（语义）：

```python
class HybridEmbedding:
    def __init__(self):
        self.dense_embedder = DenseEmbedding()
        self.sparse_embedder = SparseEmbedding()

    async def embed(self, text: str) -> HybridVector:
        # 稠密向量（语义）
        dense_vector = await self.dense_embedder.embed(text)

        # 稀疏向量（关键词）
        sparse_vector = self.sparse_embedder.embed(text)

        return HybridVector(
            dense=dense_vector,
            sparse=sparse_vector
        )
```

### （3）向量存储方案

**存储架构选择**：

系统采用分层存储架构：

```
热数据（Redis）
    ↓
温数据（PostgreSQL + pgvector）
    ↓
冷数据（对象存储）
```

**内存缓存（热数据）**：

```python
class VectorCache:
    """Redis缓存热点向量"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1小时过期

    async def get(self, doc_id: str) -> Optional[List[float]]:
        key = f"vec:{doc_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, doc_id: str, vector: List[float]):
        key = f"vec:{doc_id}"
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(vector)
        )
```

**数据库存储（温数据）**：

```sql
-- PostgreSQL + pgvector 表结构
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),  -- pgvector类型
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建向量索引
CREATE INDEX ON document_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**对象存储（冷数据）**：

原始文档存储在MinIO对象存储：

```python
class DocumentStorage:
    def __init__(self):
        self.client = Minio(
            "minio:9000",
            access_key="access_key",
            secret_key="secret_key"
        )
        self.bucket = "documents"

    async def store_document(
        self,
        doc_id: str,
        file_path: str
    ) -> str:
        """存储原始文档"""
        object_name = f"{doc_id}.pdf"
        await self.client.fput_object(
            self.bucket,
            object_name,
            file_path
        )
        return f"s3://{self.bucket}/{object_name}"
```

## 4.2.2 检索算法

### （1）向量相似度计算

**余弦相似度**：

```python
def cosine_similarity(
    vec1: np.ndarray,
    vec2: np.ndarray
) -> float:
    """计算两个向量的余弦相似度"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)
```

**近似最近邻搜索**：

使用HNSW算法实现高效检索：

```python
class HNSWIndex:
    """HNSW近似最近邻索引"""

    def __init__(
        self,
        dim: int = 1536,
        M: int = 16,  # 每个节点的邻居数
        ef_construction: int = 200
    ):
        self.index = hnswlib.Index(
            space='cosine',
            dim=dim
        )
        self.index.init_index(
            max_elements=1000000,
            ef_construction=ef_construction,
            M=M
        )

    def add_items(
        self,
        vectors: np.ndarray,
        ids: List[str]
    ):
        """添加向量到索引"""
        self.index.add_items(vectors, ids)

    def search(
        self,
        query_vector: np.ndarray,
        k: int = 10
    ) -> Tuple[List[str], List[float]]:
        """搜索最近邻"""
        labels, distances = self.index.knn_query(
            query_vector,
            k=k
        )
        return labels[0], distances[0]
```

### （2）混合检索

结合向量检索和关键词检索：

```python
class HybridRetriever:
    def __init__(self):
        self.vector_retriever = VectorRetriever()
        self.keyword_retriever = KeywordRetriever()
        self.reranker = Reranker()

    async def retrieve(
        self,
        query: str,
        top_k: int = 10
    ) -> List[RetrievalResult]:
        # 1. 向量检索
        vector_results = await self.vector_retriever.search(
            query, top_k=top_k * 2
        )

        # 2. 关键词检索
        keyword_results = await self.keyword_retriever.search(
            query, top_k=top_k * 2
        )

        # 3. 结果融合
        merged = self._merge_results(
            vector_results,
            keyword_results
        )

        # 4. 重排序
        reranked = await self.reranker.rerank(
            query, merged, top_k=top_k
        )

        return reranked
```

**结果融合策略**：

```python
def _merge_results(
    self,
    vector_results: List[RetrievalResult],
    keyword_results: List[RetrievalResult],
    alpha: float = 0.5
) -> List[RetrievalResult]:
    """
    融合向量检索和关键词检索结果
    alpha: 向量检索权重
    """
    # 归一化分数
    vector_scores = {r.id: r.score for r in vector_results}
    keyword_scores = {r.id: r.score for r in keyword_results}

    # 合并所有文档ID
    all_ids = set(vector_scores.keys()) | set(keyword_scores.keys())

    merged = []
    for doc_id in all_ids:
        v_score = vector_scores.get(doc_id, 0)
        k_score = keyword_scores.get(doc_id, 0)

        # 加权融合
        final_score = alpha * v_score + (1 - alpha) * k_score

        merged.append(RetrievalResult(
            id=doc_id,
            score=final_score
        ))

    return sorted(merged, key=lambda x: x.score, reverse=True)
```

### （3）重排序优化

**交叉编码器重排序**：

使用更精确的模型进行重排序：

```python
class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 10
    ) -> List[Document]:
        """使用交叉编码器重排序"""
        # 构建查询-文档对
        pairs = [[query, doc.content] for doc in documents]

        # 计算相关性分数
        scores = self.model.predict(pairs)

        # 按分数排序
        for doc, score in zip(documents, scores):
            doc.rerank_score = score

        return sorted(
            documents,
            key=lambda x: x.rerank_score,
            reverse=True
        )[:top_k]
```

### （4）多跳检索

对于复杂问题，进行多步检索：

```python
class MultiHopRetriever:
    async def retrieve(
        self,
        query: str,
        max_hops: int = 3
    ) -> List[Document]:
        """多跳检索：迭代扩展检索范围"""
        all_documents = []
        current_query = query

        for hop in range(max_hops):
            # 检索当前查询
            docs = await self.retriever.retrieve(current_query)

            # 检查是否找到答案
            if self._is_sufficient(docs, query):
                break

            # 生成子查询
            sub_query = await self._generate_sub_query(
                query, docs
            )
            current_query = sub_query
            all_documents.extend(docs)

        return self._deduplicate(all_documents)
```

## 4.2.3 答案生成

### （1）上下文组装

将检索结果组装为LLM可用的上下文：

```python
class ContextAssembler:
    def assemble(
        self,
        query: str,
        retrieved_docs: List[Document],
        max_tokens: int = 3000
    ) -> str:
        """组装检索结果为上下文"""
        context_parts = []
        total_tokens = 0

        for i, doc in enumerate(retrieved_docs, 1):
            # 格式化文档
            doc_text = f"[文档{i}]\n标题：{doc.title}\n内容：{doc.content}\n\n"
            doc_tokens = self._estimate_tokens(doc_text)

            # 检查是否超出限制
            if total_tokens + doc_tokens > max_tokens:
                break

            context_parts.append(doc_text)
            total_tokens += doc_tokens

        return "\n".join(context_parts)
```

### （2）提示构建

构建RAG专用提示：

```python
class RAGPromptBuilder:
    def build(
        self,
        query: str,
        context: str
    ) -> str:
        prompt = f"""基于以下参考资料回答问题。

【参考资料】
{context}

【问题】
{query}

【回答要求】
1. 基于参考资料回答，不要编造信息
2. 如果参考资料不足以回答问题，请明确说明
3. 引用相关文档时标注来源，如[文档1]
4. 保持回答简洁准确

请回答："""
        return prompt
```

### （3）引用追踪

确保生成内容的可溯源性：

```python
class CitationTracker:
    def track_citations(
        self,
        answer: str,
        source_docs: List[Document]
    ) -> Tuple[str, List[Citation]]:
        """追踪回答中的引用"""
        citations = []

        # 识别引用标记
        import re
        citation_pattern = r'\[文档(\d+)\]'
        matches = re.findall(citation_pattern, answer)

        for match in set(matches):
            doc_index = int(match) - 1
            if 0 <= doc_index < len(source_docs):
                doc = source_docs[doc_index]
                citations.append(Citation(
                    doc_id=doc.id,
                    title=doc.title,
                    authors=doc.authors,
                    year=doc.year,
                    snippet=doc.content[:200]
                ))

        return answer, citations
```

### （4）幻觉抑制

防止生成虚假内容：

```python
class HallucinationDetector:
    def detect(
        self,
        answer: str,
        source_docs: List[Document]
    ) -> float:
        """
        检测回答中的幻觉内容
        返回置信度分数（0-1）
        """
        # 1. 提取回答中的事实陈述
        facts = self._extract_facts(answer)

        # 2. 验证每个事实
        verified_count = 0
        for fact in facts:
            if self._verify_fact(fact, source_docs):
                verified_count += 1

        # 3. 计算验证率
        if not facts:
            return 1.0

        return verified_count / len(facts)

    def _verify_fact(
        self,
        fact: str,
        source_docs: List[Document]
    ) -> bool:
        """验证单个事实是否在源文档中"""
        fact_embedding = self.embedder.embed(fact)

        for doc in source_docs:
            # 计算与文档各片段的相似度
            for chunk in doc.chunks:
                similarity = cosine_similarity(
                    fact_embedding,
                    chunk.embedding
                )
                if similarity > 0.85:  # 阈值
                    return True

        return False
```

---

**本节小结**：

本节详细介绍了基于RAG的知识检索Agent的实现。首先，在知识库构建方面，设计了完整的文档处理流程，包括多源文档采集、PDF解析、文档切分等；采用多种嵌入模型进行向量化，并设计了分层存储架构（内存缓存+数据库存储+对象存储）。其次，在检索算法方面，实现了基于HNSW的近似最近邻搜索、向量与关键词的混合检索、交叉编码器重排序以及多跳检索等高级功能。最后，在答案生成方面，设计了上下文组装、提示构建、引用追踪和幻觉抑制等机制，确保生成内容的准确性、可追溯性和可靠性。这些技术共同构成了知识检索Agent的核心能力，为系统提供了强大的知识支撑。
