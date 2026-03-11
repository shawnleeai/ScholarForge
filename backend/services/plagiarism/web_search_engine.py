"""
网络搜索查重引擎
集成Google Scholar、Bing Academic等学术搜索引擎
"""

import re
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote_plus, urlencode
import json

from .simhash_engine import SimHashEngine


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    source: str  # google_scholar, bing_academic, etc.
    citation_count: Optional[int] = None
    publication_year: Optional[int] = None


@dataclass
class WebMatch:
    """网络匹配结果"""
    search_result: SearchResult
    similarity: float
    matched_text: str
    match_type: str  # title, snippet, content


class WebSearchPlagiarismEngine:
    """
    网络搜索查重引擎

    通过搜索学术数据库检测文本相似度
    """

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cx: Optional[str] = None,
        bing_api_key: Optional[str] = None,
        similarity_threshold: float = 0.7
    ):
        self.google_api_key = google_api_key
        self.google_cx = google_cx  # Custom Search Engine ID
        self.bing_api_key = bing_api_key
        self.similarity_threshold = similarity_threshold

        # SimHash引擎用于相似度计算
        self.simhash_engine = SimHashEngine()

        # 请求配置
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        }

    async def check(
        self,
        text: str,
        title: Optional[str] = None
    ) -> Tuple[float, List[WebMatch]]:
        """
        执行网络搜索查重

        Args:
            text: 待检测文本
            title: 论文标题（可选）

        Returns:
            (整体相似度, 匹配列表)
        """
        matches = []

        # 1. 提取关键句进行搜索
        key_sentences = self._extract_key_sentences(text)

        # 2. 并行搜索多个引擎
        search_tasks = []

        # Google Scholar搜索
        if self.google_api_key:
            for sentence in key_sentences[:3]:  # 限制查询次数
                search_tasks.append(
                    self._search_google_scholar(sentence)
                )

        # Bing Academic搜索
        if self.bing_api_key:
            for sentence in key_sentences[:3]:
                search_tasks.append(
                    self._search_bing_academic(sentence)
                )

        # 执行搜索
        if search_tasks:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # 合并结果
            all_results = []
            for result in search_results:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    print(f"Search error: {result}")

            # 去重
            seen_urls = set()
            unique_results = []
            for r in all_results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    unique_results.append(r)

            # 3. 计算相似度
            for result in unique_results:
                match = await self._calculate_match(text, result)
                if match and match.similarity >= self.similarity_threshold:
                    matches.append(match)

        # 计算整体相似度
        overall_similarity = max([m.similarity for m in matches], default=0.0)

        return overall_similarity, matches

    def _extract_key_sentences(self, text: str, max_sentences: int = 5) -> List[str]:
        """
        提取关键句用于搜索

        策略：
        1. 选择较长的句子（更有可能是原创内容）
        2. 排除常见学术短语
        3. 去除引用和参考文献部分
        """
        # 简单的句子分割
        sentences = re.split(r'[。！？.!?]\s*', text)

        # 过滤和评分
        scored_sentences = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20 or len(sent) > 200:
                continue

            # 排除引用
            if sent.startswith('[') or sent.startswith('('):
                continue

            # 排除常见短语
            common_phrases = [
                '本文研究', '本研究', '实验结果表明',
                '综上所述', '参考文献', '致谢',
                'this paper', 'this study', 'in conclusion',
                'acknowledgment', 'references'
            ]
            if any(p in sent.lower() for p in common_phrases):
                continue

            # 评分：基于独特词的比例
            words = set(re.findall(r'\w+', sent.lower()))
            score = len(words) / len(sent) if sent else 0

            scored_sentences.append((sent, score))

        # 按评分排序并返回前N个
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored_sentences[:max_sentences]]

    async def _search_google_scholar(self, query: str) -> List[SearchResult]:
        """
        搜索Google Scholar

        使用Google Custom Search API（需要配置）
        或模拟搜索结果
        """
        if not self.google_api_key or not self.google_cx:
            return []

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cx,
            'q': query,
            'num': 5,
            'sort': 'date',
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    results = []

                    for item in data.get('items', []):
                        results.append(SearchResult(
                            title=item.get('title', ''),
                            url=item.get('link', ''),
                            snippet=item.get('snippet', ''),
                            source='google_scholar'
                        ))

                    return results

        except Exception as e:
            print(f"Google Scholar search error: {e}")
            return []

    async def _search_bing_academic(self, query: str) -> List[SearchResult]:
        """
        搜索Bing Academic

        使用Bing Search API v7
        """
        if not self.bing_api_key:
            return []

        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            'Ocp-Apim-Subscription-Key': self.bing_api_key
        }
        params = {
            'q': f"{query} academic",
            'count': 5,
            'responseFilter': 'Webpages',
            'mkt': 'zh-CN'
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    results = []

                    for item in data.get('webPages', {}).get('value', []):
                        results.append(SearchResult(
                            title=item.get('name', ''),
                            url=item.get('url', ''),
                            snippet=item.get('snippet', ''),
                            source='bing_academic'
                        ))

                    return results

        except Exception as e:
            print(f"Bing search error: {e}")
            return []

    async def _search_crossref(self, query: str) -> List[SearchResult]:
        """
        搜索Crossref学术数据库

        Crossref API是免费的，适合学术论文搜索
        """
        url = "https://api.crossref.org/works"
        params = {
            'query': query,
            'rows': 5,
            'sort': 'relevance',
            'order': 'desc'
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    results = []

                    for item in data.get('message', {}).get('items', []):
                        title = item.get('title', [''])[0] if item.get('title') else ''
                        url = item.get('URL', '')

                        # 提取年份
                        year = None
                        if 'published-print' in item:
                            year = item['published-print'].get('date-parts', [[None]])[0][0]
                        elif 'published-online' in item:
                            year = item['published-online'].get('date-parts', [[None]])[0][0]

                        # 引用次数
                        citations = item.get('is-referenced-by-count', 0)

                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=title,  # Crossref不提供摘要
                            source='crossref',
                            citation_count=citations,
                            publication_year=year
                        ))

                    return results

        except Exception as e:
            print(f"Crossref search error: {e}")
            return []

    async def _search_semantic_scholar(self, query: str) -> List[SearchResult]:
        """
        搜索Semantic Scholar

        免费API，适合学术论文搜索
        """
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            'query': query,
            'limit': 5,
            'fields': 'title,url,abstract,year,citationCount'
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return []

                    data = await response.json()
                    results = []

                    for item in data.get('data', []):
                        results.append(SearchResult(
                            title=item.get('title', ''),
                            url=item.get('url', ''),
                            snippet=item.get('abstract', '')[:200],
                            source='semantic_scholar',
                            citation_count=item.get('citationCount', 0),
                            publication_year=item.get('year')
                        ))

                    return results

        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
            return []

    async def _calculate_match(
        self,
        original_text: str,
        search_result: SearchResult
    ) -> Optional[WebMatch]:
        """
        计算搜索结果与原文的相似度

        由于无法直接获取全文，我们比较标题和摘要
        """
        # 计算标题相似度
        title_sim = self._text_similarity(original_text, search_result.title)

        # 计算摘要相似度
        snippet_sim = self._text_similarity(original_text, search_result.snippet)

        # 取最大值
        max_sim = max(title_sim, snippet_sim)

        if max_sim < self.similarity_threshold:
            return None

        # 找出匹配的文本
        matched_text = search_result.title if title_sim > snippet_sim else search_result.snippet
        match_type = 'title' if title_sim > snippet_sim else 'snippet'

        return WebMatch(
            search_result=search_result,
            similarity=max_sim,
            matched_text=matched_text[:200],
            match_type=match_type
        )

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度

        使用SimHash + Jaccard混合算法
        """
        if not text1 or not text2:
            return 0.0

        # SimHash相似度
        simhash_sim = self.simhash_engine.similarity(
            self.simhash_engine.compute_fingerprint(text1),
            self.simhash_engine.compute_fingerprint(text2)
        )

        # Jaccard相似度
        words1 = set(self.simhash_engine.tokenize(text1))
        words2 = set(self.simhash_engine.tokenize(text2))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2
        jaccard_sim = len(intersection) / len(union) if union else 0

        # 加权平均
        return simhash_sim * 0.6 + jaccard_sim * 0.4


class HybridPlagiarismEngine:
    """
    混合查重引擎

    结合本地SimHash和网络搜索的查重方案
    """

    def __init__(
        self,
        local_config: Optional[Dict] = None,
        web_config: Optional[Dict] = None
    ):
        from .engines import LocalPlagiarismEngine

        self.local_engine = LocalPlagiarismEngine(local_config or {})
        self.web_engine = WebSearchPlagiarismEngine(**(web_config or {}))

    async def check(self, text: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        执行混合查重

        策略：
        1. 先用本地引擎快速检测
        2. 如果相似度较高，再用网络搜索验证
        3. 综合两种结果
        """
        # 本地检测
        local_result = await self.local_engine.check(text, title)

        # 如果本地相似度低于20%，直接返回本地结果
        if local_result.overall_similarity < 20:
            return {
                'success': True,
                'source': 'local',
                'overall_similarity': local_result.overall_similarity,
                'local_result': local_result,
                'web_matches': [],
                'recommendation': '相似度较低，通过检测'
            }

        # 网络搜索验证
        web_similarity, web_matches = await self.web_engine.check(text, title)

        # 综合评分（本地权重70%，网络权重30%）
        combined_similarity = (
            local_result.overall_similarity * 0.7 +
            web_similarity * 100 * 0.3
        )

        # 生成建议
        recommendation = self._generate_recommendation(
            combined_similarity,
            len(web_matches)
        )

        return {
            'success': True,
            'source': 'hybrid',
            'overall_similarity': combined_similarity,
            'local_result': local_result,
            'web_similarity': web_similarity,
            'web_matches': web_matches,
            'recommendation': recommendation
        }

    def _generate_recommendation(
        self,
        similarity: float,
        web_match_count: int
    ) -> str:
        """生成查重建议"""
        if similarity < 15:
            return "相似度很低，论文原创性良好"
        elif similarity < 30:
            return "相似度较低，基本符合要求，建议检查标红部分"
        elif similarity < 50:
            return "相似度中等，需要修改部分重复内容"
        elif similarity < 70:
            return "相似度较高，建议大幅修改重复段落"
        else:
            return "相似度过高，存在严重抄袭风险，必须全面修改"


# 便捷函数
async def quick_web_check(text: str) -> Tuple[float, List[WebMatch]]:
    """快速网络查重"""
    engine = WebSearchPlagiarismEngine()
    return await engine.check(text)


if __name__ == "__main__":
    # 测试
    async def test():
        engine = WebSearchPlagiarismEngine()

        test_text = """
        人工智能在医疗领域的应用越来越广泛。通过深度学习技术，
        可以辅助医生进行疾病诊断，提高诊断准确率。
        本文提出了一种新的医学图像分析方法。
        """

        # 测试关键句提取
        key_sentences = engine._extract_key_sentences(test_text)
        print("关键句:")
        for sent in key_sentences:
            print(f"  - {sent}")

    asyncio.run(test())
