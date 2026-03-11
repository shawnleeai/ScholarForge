"""
SimHash 查重引擎实现
基于局部敏感哈希(LSH)的文本相似度检测算法

核心特性：
- 64位指纹生成
- 海明距离计算
- 大规模文档快速去重
- 支持中文和英文
"""

import re
import hashlib
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import jieba
import mmh3  # MurmurHash3


@dataclass
class SimHashResult:
    """SimHash匹配结果"""
    fingerprint: int
    text: str
    similarity: float
    hamming_distance: int
    source_id: str
    source_title: Optional[str] = None


@dataclass
class TextChunk:
    """文本分块"""
    content: str
    start_pos: int
    end_pos: int
    weight: float = 1.0


class SimHashEngine:
    """
    SimHash查重引擎

    算法步骤：
    1. 文本分词
    2. 计算词权重（TF-IDF）
    3. 对每个词计算hash并加权
    4. 合并所有词的特征向量
    5. 降维得到64位指纹
    """

    def __init__(
        self,
        hash_bits: int = 64,
        hamming_threshold: int = 3,
        chunk_size: int = 50,
        use_jieba: bool = True
    ):
        """
        初始化SimHash引擎

        Args:
            hash_bits: 指纹位数（默认64位）
            hamming_threshold: 海明距离阈值，小于此值认为是相似
            chunk_size: 文本分块大小
            use_jieba: 是否使用jieba分词（中文）
        """
        self.hash_bits = hash_bits
        self.hamming_threshold = hamming_threshold
        self.chunk_size = chunk_size
        self.use_jieba = use_jieba

        # 指纹数据库
        self.fingerprints: Dict[str, int] = {}

        # IDF词典（用于计算权重）
        self.idf_dict: Dict[str, float] = defaultdict(lambda: 1.0)

        # 停用词
        self.stopwords = self._load_stopwords()

    def _load_stopwords(self) -> Set[str]:
        """加载停用词"""
        return {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can',
            'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for',
            'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'between',
            'and', 'but', 'or', 'yet', 'so', 'if', 'because', 'although',
            'though', 'while', 'where', 'when', 'that', 'which', 'who',
            'whom', 'whose', 'what', 'this', 'these', 'those', 'i', 'me',
            'my', 'mine', 'myself', 'we', 'us', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
            'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
            'itself', 'they', 'them', 'their', 'theirs', 'themselves',
        }

    def tokenize(self, text: str) -> List[str]:
        """
        分词

        支持中英文混合分词
        """
        if not text:
            return []

        tokens = []

        # 中文分词
        if self.use_jieba and self._contains_chinese(text):
            words = jieba.lcut(text)
            tokens.extend([w.strip() for w in words if len(w.strip()) > 1])

        # 英文单词提取
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        tokens.extend(english_words)

        # 数字提取
        numbers = re.findall(r'\d+', text)
        tokens.extend(numbers)

        # 过滤停用词
        tokens = [t for t in tokens if t not in self.stopwords]

        return tokens

    def _contains_chinese(self, text: str) -> bool:
        """检查文本是否包含中文"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    def calculate_weights(self, tokens: List[str]) -> Dict[str, float]:
        """
        计算词权重（使用TF-IDF）

        Args:
            tokens: 分词结果

        Returns:
            词权重字典
        """
        if not tokens:
            return {}

        # 词频统计
        tf = defaultdict(int)
        for token in tokens:
            tf[token] += 1

        # 计算TF-IDF权重
        total_tokens = len(tokens)
        weights = {}
        for token, count in tf.items():
            tf_score = count / total_tokens
            idf_score = self.idf_dict.get(token, 1.0)
            weights[token] = tf_score * idf_score

        return weights

    def compute_fingerprint(self, text: str) -> int:
        """
        计算文本的SimHash指纹

        Args:
            text: 输入文本

        Returns:
            64位整数指纹
        """
        # 分词
        tokens = self.tokenize(text)
        if not tokens:
            return 0

        # 计算权重
        weights = self.calculate_weights(tokens)

        # 初始化特征向量
        vector = np.zeros(self.hash_bits)

        # 对每个词计算hash并加权
        for token, weight in weights.items():
            # 使用MurmurHash3生成hash
            hash_value = mmh3.hash64(token, seed=0)[0]

            # 处理每一位
            for i in range(self.hash_bits):
                bit = (hash_value >> i) & 1
                if bit == 1:
                    vector[i] += weight
                else:
                    vector[i] -= weight

        # 生成指纹
        fingerprint = 0
        for i in range(self.hash_bits):
            if vector[i] > 0:
                fingerprint |= (1 << i)

        return fingerprint & ((1 << self.hash_bits) - 1)

    def hamming_distance(self, fp1: int, fp2: int) -> int:
        """
        计算两个指纹的海明距离

        Args:
            fp1: 指纹1
            fp2: 指纹2

        Returns:
            海明距离（不同位的数量）
        """
        xor = fp1 ^ fp2
        distance = 0
        while xor:
            distance += 1
            xor &= xor - 1  # 清除最低位的1
        return distance

    def similarity(self, fp1: int, fp2: int) -> float:
        """
        计算两个指纹的相似度

        Args:
            fp1: 指纹1
            fp2: 指纹2

        Returns:
            相似度（0-1）
        """
        distance = self.hamming_distance(fp1, fp2)
        # 海明距离越小，相似度越高
        return max(0, 1 - distance / self.hash_bits)

    def find_similar(
        self,
        text: str,
        candidates: Optional[Dict[str, int]] = None
    ) -> List[SimHashResult]:
        """
        查找相似文本

        Args:
            text: 查询文本
            candidates: 候选指纹字典 {id: fingerprint}

        Returns:
            相似结果列表
        """
        query_fp = self.compute_fingerprint(text)
        results = []

        candidates = candidates or self.fingerprints

        for source_id, fingerprint in candidates.items():
            distance = self.hamming_distance(query_fp, fingerprint)

            if distance <= self.hamming_threshold:
                sim = self.similarity(query_fp, fingerprint)
                results.append(SimHashResult(
                    fingerprint=fingerprint,
                    text=text[:200],
                    similarity=sim,
                    hamming_distance=distance,
                    source_id=source_id
                ))

        # 按相似度排序
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results

    def add_document(self, doc_id: str, text: str) -> int:
        """
        添加文档到指纹库

        Args:
            doc_id: 文档ID
            text: 文档文本

        Returns:
            文档指纹
        """
        fingerprint = self.compute_fingerprint(text)
        self.fingerprints[doc_id] = fingerprint

        # 更新IDF
        tokens = self.tokenize(text)
        for token in set(tokens):
            self.idf_dict[token] += 1

        return fingerprint

    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        将文本分块

        使用滑动窗口分块，支持重叠
        """
        chunks = []
        text_len = len(text)

        # 按句子分割
        sentences = re.split(r'([。！？.!?]\s*)', text)
        current_text = ""
        start_pos = 0

        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""
            current_text += sentence + punct

            if len(current_text) >= self.chunk_size:
                chunks.append(TextChunk(
                    content=current_text,
                    start_pos=start_pos,
                    end_pos=start_pos + len(current_text)
                ))
                # 保留部分重叠
                overlap = len(current_text) // 4
                start_pos += len(current_text) - overlap
                current_text = current_text[-overlap:] if overlap > 0 else ""

        # 处理剩余内容
        if len(current_text) >= self.chunk_size // 2:
            chunks.append(TextChunk(
                content=current_text,
                start_pos=start_pos,
                end_pos=start_pos + len(current_text)
            ))

        return chunks

    def detailed_check(
        self,
        text: str,
        reference_texts: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        详细查重检测

        Args:
            text: 待检测文本
            reference_texts: 参考文本字典 {id: text}

        Returns:
            详细查重结果
        """
        # 分块检测
        chunks = self.chunk_text(text)

        chunk_results = []
        total_similarity = 0.0
        matched_chunks = 0

        for chunk in chunks:
            chunk_fp = self.compute_fingerprint(chunk.content)

            # 与参考文本比较
            max_similarity = 0.0
            best_match = None

            if reference_texts:
                for ref_id, ref_text in reference_texts.items():
                    ref_fp = self.compute_fingerprint(ref_text)
                    sim = self.similarity(chunk_fp, ref_fp)

                    if sim > max_similarity:
                        max_similarity = sim
                        best_match = ref_id

            chunk_results.append({
                'chunk': chunk,
                'fingerprint': chunk_fp,
                'similarity': max_similarity,
                'best_match': best_match
            })

            total_similarity += max_similarity
            if max_similarity > 0.5:
                matched_chunks += 1

        avg_similarity = total_similarity / len(chunks) if chunks else 0
        match_rate = matched_chunks / len(chunks) if chunks else 0

        return {
            'overall_similarity': avg_similarity,
            'match_rate': match_rate,
            'total_chunks': len(chunks),
            'matched_chunks': matched_chunks,
            'chunk_results': chunk_results,
            'full_fingerprint': self.compute_fingerprint(text)
        }

    def batch_add_documents(self, documents: Dict[str, str]) -> Dict[str, int]:
        """
        批量添加文档

        Args:
            documents: 文档字典 {id: text}

        Returns:
            指纹字典 {id: fingerprint}
        """
        fingerprints = {}
        for doc_id, text in documents.items():
            fingerprints[doc_id] = self.add_document(doc_id, text)
        return fingerprints

    def find_near_duplicates(self, threshold: Optional[int] = None) -> List[Tuple[str, str, int]]:
        """
        查找近似重复文档

        Args:
            threshold: 海明距离阈值

        Returns:
            相似文档对列表 [(id1, id2, distance)]
        """
        threshold = threshold or self.hamming_threshold
        duplicates = []

        doc_ids = list(self.fingerprints.keys())

        for i in range(len(doc_ids)):
            for j in range(i + 1, len(doc_ids)):
                id1, id2 = doc_ids[i], doc_ids[j]
                fp1 = self.fingerprints[id1]
                fp2 = self.fingerprints[id2]

                distance = self.hamming_distance(fp1, fp2)
                if distance <= threshold:
                    duplicates.append((id1, id2, distance))

        # 按距离排序
        duplicates.sort(key=lambda x: x[2])
        return duplicates


class SimHashIndexer:
    """
    SimHash索引器
    使用分桶策略加速大规模查询
    """

    def __init__(self, hash_bits: int = 64, band_size: int = 8):
        """
        初始化索引器

        Args:
            hash_bits: 总哈希位数
            band_size: 每个band的位数
        """
        self.hash_bits = hash_bits
        self.band_size = band_size
        self.num_bands = hash_bits // band_size

        # 分桶索引
        self.buckets: List[Dict[int, List[str]]] = [
            defaultdict(list) for _ in range(self.num_bands)
        ]

        # 指纹存储
        self.fingerprints: Dict[str, int] = {}

    def _get_band_hash(self, fingerprint: int, band_idx: int) -> int:
        """获取指定band的hash值"""
        start = band_idx * self.band_size
        mask = (1 << self.band_size) - 1
        return (fingerprint >> start) & mask

    def add(self, doc_id: str, fingerprint: int):
        """添加文档到索引"""
        self.fingerprints[doc_id] = fingerprint

        for band_idx in range(self.num_bands):
            band_hash = self._get_band_hash(fingerprint, band_idx)
            self.buckets[band_idx][band_hash].append(doc_id)

    def query(self, fingerprint: int) -> Set[str]:
        """
        查询候选相似文档

        使用LSH策略：只要有一个band相同，就可能是相似文档
        """
        candidates = set()

        for band_idx in range(self.num_bands):
            band_hash = self._get_band_hash(fingerprint, band_idx)
            candidates.update(self.buckets[band_idx].get(band_hash, []))

        return candidates


# 便捷函数
def compute_simhash(text: str) -> int:
    """计算文本的SimHash指纹"""
    engine = SimHashEngine()
    return engine.compute_fingerprint(text)


def calculate_similarity(text1: str, text2: str) -> float:
    """计算两段文本的相似度"""
    engine = SimHashEngine()
    fp1 = engine.compute_fingerprint(text1)
    fp2 = engine.compute_fingerprint(text2)
    return engine.similarity(fp1, fp2)


if __name__ == "__main__":
    # 测试
    engine = SimHashEngine()

    # 测试文本
    text1 = "人工智能在医疗领域的应用越来越广泛，可以帮助医生进行疾病诊断。"
    text2 = "人工智能在医疗领域的应用日益广泛，能够辅助医生进行疾病诊断。"
    text3 = "区块链技术在金融行业的应用前景非常广阔。"

    fp1 = engine.compute_fingerprint(text1)
    fp2 = engine.compute_fingerprint(text2)
    fp3 = engine.compute_fingerprint(text3)

    print(f"Text 1 FP: {fp1:016x}")
    print(f"Text 2 FP: {fp2:016x}")
    print(f"Text 3 FP: {fp3:016x}")

    sim12 = engine.similarity(fp1, fp2)
    sim13 = engine.similarity(fp1, fp3)

    print(f"\n相似度(1 vs 2): {sim12:.4f}")
    print(f"相似度(1 vs 3): {sim13:.4f}")

    dist12 = engine.hamming_distance(fp1, fp2)
    dist13 = engine.hamming_distance(fp1, fp3)

    print(f"\n海明距离(1 vs 2): {dist12}")
    print(f"海明距离(1 vs 3): {dist13}")
