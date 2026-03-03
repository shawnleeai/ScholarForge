"""
查重检测引擎
本地文本相似度检测 + 降重建议生成
"""

import re
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import random


@dataclass
class TextSegment:
    """文本片段"""
    id: str
    content: str
    start_pos: int
    end_pos: int
    section_id: Optional[str] = None


@dataclass
class SimilarityResult:
    """相似度检测结果"""
    segment: TextSegment
    similar_texts: List[Dict[str, Any]]
    max_similarity: float


class PlagiarismChecker:
    """查重检测器"""

    # 常见学术短语（这些不应计入重复）
    ACADEMIC_PHRASES = {
        "研究表明", "实验结果", "数据分析", "综上所述",
        "本文研究", "本文提出", "研究发现", "结果表明",
        "根据调查", "通过分析", "可以看出", "可以得出",
        "需要注意的是", "值得注意的是", "从表可以看出",
        "从图可以看出", "由上可知", "由此可知", "总而言之",
        "firstly", "secondly", "thirdly", "in conclusion",
        "as shown in", "as can be seen", "it is worth noting",
        "the results show", "the analysis indicates",
    }

    # 模拟的参考数据库
    REFERENCE_DB = [
        {
            "title": "人工智能在项目管理中的应用研究",
            "author": "张三",
            "text": "人工智能技术在项目管理中的应用日益广泛，通过机器学习算法可以实现对项目进度和成本的精准预测。",
        },
        {
            "title": "基于深度学习的工程管理决策系统",
            "author": "李四",
            "text": "本研究构建了基于深度学习的工程管理决策支持系统，实验结果表明该方法能够显著提升决策效率。",
        },
        {
            "title": "协同办公系统的设计与实现",
            "author": "王五",
            "text": "协同办公系统是现代企业管理的重要工具，本文设计并实现了一套完整的协同办公解决方案。",
        },
    ]

    def __init__(self):
        self.min_segment_length = 50  # 最小检测片段长度
        self.segment_overlap = 20     # 片段重叠字符数

    def check(
        self,
        text: str,
        section_id: Optional[str] = None,
        exclude_academic_phrases: bool = True,
    ) -> Tuple[float, List[SimilarityResult]]:
        """
        执行查重检测

        Args:
            text: 待检测文本
            section_id: 章节ID
            exclude_academic_phrases: 是否排除学术短语

        Returns:
            (总体相似度, 相似片段列表)
        """
        # 分段处理
        segments = self._split_text(text, section_id)

        if not segments:
            return 0.0, []

        # 检测每个片段
        results = []
        total_similar_chars = 0
        total_chars = 0

        for segment in segments:
            result = self._check_segment(segment, exclude_academic_phrases)
            if result.max_similarity > 0.1:  # 只记录相似度 > 10% 的
                results.append(result)

            total_similar_chars += len(segment.content) * result.max_similarity
            total_chars += len(segment.content)

        overall_similarity = total_similar_chars / total_chars if total_chars > 0 else 0

        return overall_similarity, results

    def _split_text(
        self,
        text: str,
        section_id: Optional[str] = None,
    ) -> List[TextSegment]:
        """
        将文本分割成片段

        按段落和句子分割，确保片段有重叠
        """
        segments = []
        paragraphs = text.split('\n\n')

        segment_id = 0
        for para in paragraphs:
            if len(para.strip()) < self.min_segment_length:
                continue

            # 按句子进一步分割长段落
            sentences = re.split(r'[。！？.!?]', para)

            current_text = ""
            start_pos = 0

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                current_text += sentence + "。"

                if len(current_text) >= self.min_segment_length:
                    segments.append(TextSegment(
                        id=f"seg_{segment_id}",
                        content=current_text,
                        start_pos=start_pos,
                        end_pos=start_pos + len(current_text),
                        section_id=section_id,
                    ))
                    segment_id += 1
                    start_pos += len(current_text) - self.segment_overlap
                    current_text = current_text[-self.segment_overlap:] if len(current_text) > self.segment_overlap else ""

            # 处理剩余内容
            if len(current_text) >= self.min_segment_length:
                segments.append(TextSegment(
                    id=f"seg_{segment_id}",
                    content=current_text,
                    start_pos=start_pos,
                    end_pos=start_pos + len(current_text),
                    section_id=section_id,
                ))
                segment_id += 1

        return segments

    def _check_segment(
        self,
        segment: TextSegment,
        exclude_academic_phrases: bool,
    ) -> SimilarityResult:
        """检测单个片段的相似度"""
        content = segment.content

        # 排除学术短语
        if exclude_academic_phrases:
            for phrase in self.ACADEMIC_PHRASES:
                content = content.replace(phrase, "")

        similar_texts = []
        max_similarity = 0.0

        # 与参考数据库比较
        for ref in self.REFERENCE_DB:
            similarity = self._calculate_similarity(content, ref["text"])
            if similarity > 0.3:  # 相似度阈值
                similar_texts.append({
                    "text": ref["text"][:200],
                    "similarity": similarity,
                    "source_title": ref["title"],
                    "source_author": ref["author"],
                })
                max_similarity = max(max_similarity, similarity)

        return SimilarityResult(
            segment=segment,
            similar_texts=similar_texts,
            max_similarity=max_similarity,
        )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度

        使用简单的词汇重叠率 + N-gram 匹配
        """
        # 分词（简化处理，按字符/单词）
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))

        if not words1 or not words2:
            return 0.0

        # Jaccard 相似度
        intersection = words1 & words2
        union = words1 | words2
        jaccard = len(intersection) / len(union) if union else 0

        # N-gram 匹配
        ngram_sim = self._ngram_similarity(text1, text2, n=3)

        # 综合相似度
        similarity = jaccard * 0.5 + ngram_sim * 0.5

        # 添加随机波动（模拟真实检测）
        similarity += random.uniform(-0.05, 0.05)

        return max(0, min(1, similarity))

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 中文字符
        chinese = re.findall(r'[\u4e00-\u9fff]+', text)
        # 英文单词
        english = re.findall(r'[a-zA-Z]+', text)
        # 数字
        numbers = re.findall(r'\d+', text)

        tokens = []
        for chars in chinese:
            tokens.extend(list(chars))  # 中文按字符
        tokens.extend(english)
        tokens.extend(numbers)

        return [t.lower() for t in tokens if len(t) > 1]

    def _ngram_similarity(self, text1: str, text2: str, n: int = 3) -> float:
        """N-gram 相似度"""
        def get_ngrams(text, n):
            text = text.replace(" ", "").replace("\n", "")
            return set(text[i:i+n] for i in range(len(text) - n + 1))

        ngrams1 = get_ngrams(text1, n)
        ngrams2 = get_ngrams(text2, n)

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = ngrams1 & ngrams2
        union = ngrams1 | ngrams2

        return len(intersection) / len(union) if union else 0


class RewordSuggester:
    """降重建议生成器"""

    # 同义词词典（简化版）
    SYNONYMS = {
        "研究": ["探讨", "分析", "考察", "探究", "调查"],
        "提出": ["建议", "倡议", "推荐", "主张", "提议"],
        "重要": ["关键", "核心", "主要", "首要", "至关重要"],
        "提高": ["提升", "增强", "改进", "优化", "加强"],
        "影响": ["作用", "效应", "冲击", "改变", "效果"],
        "分析": ["研究", "剖析", "考察", "评估", "解析"],
        "结果": ["结论", "成果", "产出", "发现", "成效"],
        "问题": ["难题", "困境", "挑战", "障碍", "疑问"],
        "方法": ["方式", "途径", "手段", "策略", "措施"],
        "实现": ["达成", "完成", "执行", "实施", "落实"],
    }

    # 学术表达替换
    FORMAL_EXPRESSIONS = {
        "很好": "较为理想",
        "很多": "大量",
        "我觉得": "本文认为",
        "大家都知道": "众所周知",
        "这个东西": "该对象",
        "想办法": "采取措施",
        "搞清楚": "明确",
        "看看": "考察",
        "说说": "阐述",
        "弄明白": "理解",
    }

    def suggest(
        self,
        original_text: str,
        max_suggestions: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        生成降重建议

        Args:
            original_text: 原始文本
            max_suggestions: 最大建议数

        Returns:
            建议列表
        """
        suggestions = []

        # 1. 同义词替换
        synonym_suggestion = self._suggest_synonyms(original_text)
        if synonym_suggestion:
            suggestions.append(synonym_suggestion)

        # 2. 句式调整
        structure_suggestion = self._suggest_structure_change(original_text)
        if structure_suggestion:
            suggestions.append(structure_suggestion)

        # 3. 学术表达优化
        formal_suggestion = self._suggest_formal_expression(original_text)
        if formal_suggestion:
            suggestions.append(formal_suggestion)

        return suggestions[:max_suggestions]

    def _suggest_synonyms(self, text: str) -> Optional[Dict[str, Any]]:
        """同义词替换建议"""
        modified_text = text
        replacements = []

        for word, synonyms in self.SYNONYMS.items():
            if word in text:
                import random
                new_word = random.choice(synonyms)
                modified_text = modified_text.replace(word, new_word, 1)
                replacements.append(f"{word} → {new_word}")

        if modified_text == text:
            return None

        return {
            "type": "rephrase",
            "original_text": text,
            "suggested_text": modified_text,
            "confidence": 0.8,
            "reason": "使用同义词替换降低相似度",
            "changes": replacements,
        }

    def _suggest_structure_change(self, text: str) -> Optional[Dict[str, Any]]:
        """句式调整建议"""
        # 简单的句式调整：主动变被动
        if "研究" in text and "了" in text:
            # 主动 -> 被动
            parts = text.split("研究")
            if len(parts) >= 2:
                modified = f"在{parts[0]}方面，相关研究{parts[1]}"
                return {
                    "type": "structure",
                    "original_text": text,
                    "suggested_text": modified,
                    "confidence": 0.7,
                    "reason": "调整句式结构，由主动句改为被动句",
                }

        # 添加过渡词
        if text.startswith("本文") or text.startswith("本研究"):
            modified = f"具体而言，{text}"
            return {
                "type": "expand",
                "original_text": text,
                "suggested_text": modified,
                "confidence": 0.6,
                "reason": "添加过渡性表达，增强学术性",
            }

        return None

    def _suggest_formal_expression(self, text: str) -> Optional[Dict[str, Any]]:
        """学术表达优化建议"""
        modified_text = text
        changes = []

        for informal, formal in self.FORMAL_EXPRESSIONS.items():
            if informal in modified_text:
                modified_text = modified_text.replace(informal, formal)
                changes.append(f"{informal} → {formal}")

        if modified_text == text:
            return None

        return {
            "type": "replace",
            "original_text": text,
            "suggested_text": modified_text,
            "confidence": 0.9,
            "reason": "使用更规范的学术表达",
            "changes": changes,
        }

    def check_academic_norms(self, text: str) -> List[Dict[str, Any]]:
        """检查学术规范问题"""
        issues = []

        # 检查口语化表达
        for informal, formal in self.FORMAL_EXPRESSIONS.items():
            if informal in text:
                issues.append({
                    "type": "colloquial",
                    "text": informal,
                    "suggestion": formal,
                    "severity": "medium",
                })

        # 检查常见问题
        patterns = [
            (r'我(们)?觉得', "应使用客观表达", "本文认为"),
            (r'非常(好|多|重要)', "避免程度副词堆砌", "较为理想/大量/关键"),
            (r'大概|可能|也许', "表述应更加确定", "推测/预计/较为"),
            (r'等等', "学术写作应避免使用", "等/以及其他相关内容"),
        ]

        for pattern, reason, suggestion in patterns:
            if re.search(pattern, text):
                issues.append({
                    "type": "informal",
                    "pattern": pattern,
                    "reason": reason,
                    "suggestion": suggestion,
                    "severity": "low",
                })

        return issues
