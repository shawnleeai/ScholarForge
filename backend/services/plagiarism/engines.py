"""
查重引擎实现
支持多种查重方式：本地、Turnitin、PaperPass 等
"""

import abc
import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import asyncio

from .simhash_engine import SimHashEngine, SimHashResult


@dataclass
class SimilarityMatch:
    """相似片段"""
    text: str
    start_index: int
    end_index: int
    similarity: float
    source_id: str
    source_title: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class SimilaritySource:
    """相似来源"""
    id: str
    title: str
    type: str  # internet/publication/student_paper
    url: Optional[str] = None
    similarity: float = 0.0
    match_count: int = 0


@dataclass
class PlagiarismResult:
    """查重结果"""
    success: bool
    overall_similarity: float
    internet_similarity: float
    publications_similarity: float
    student_papers_similarity: float
    matches: List[SimilarityMatch]
    sources: List[SimilaritySource]
    report_url: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0


class BasePlagiarismEngine(abc.ABC):
    """查重引擎基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abc.abstractmethod
    async def check(self, text: str, title: Optional[str] = None) -> PlagiarismResult:
        """执行查重检查"""
        pass

    @abc.abstractmethod
    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        pass

    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 去除页眉页脚标记
        text = re.sub(r'第\s*\d+\s*页', '', text)
        # 去除参考文献标记（如果配置）
        if self.config.get('exclude_bibliography', True):
            text = self._remove_bibliography(text)
        return text.strip()

    def _remove_bibliography(self, text: str) -> str:
        """移除参考文献部分"""
        # 常见的参考文献标题
        bib_patterns = [
            r'参考\s*文献[：:]',
            r'References[：:]',
            r'Bibliography[：:]',
        ]
        for pattern in bib_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return text[:match.start()]
        return text

    def _calculate_hash(self, text: str) -> str:
        """计算文本哈希"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()


class LocalPlagiarismEngine(BasePlagiarismEngine):
    """
    本地查重引擎
    基于SimHash算法进行文本相似度检测
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.similarity_threshold = config.get('similarity_threshold', 0.6)
        self.min_match_length = config.get('min_match_length', 50)
        self.hamming_threshold = config.get('hamming_threshold', 3)

        # 初始化SimHash引擎
        self.simhash_engine = SimHashEngine(
            hash_bits=64,
            hamming_threshold=self.hamming_threshold,
            chunk_size=self.min_match_length
        )

        # 本地文档库
        self._local_db: Dict[str, str] = {}

    async def check(self, text: str, title: Optional[str] = None) -> PlagiarismResult:
        """
        本地查重实现
        使用SimHash算法检测相似度
        """
        import time
        start_time = time.time()

        try:
            # 预处理文本
            processed_text = self._preprocess_text(text)

            # 使用SimHash进行详细检测
            check_result = self.simhash_engine.detailed_check(
                processed_text,
                self._local_db
            )

            # 查找相似文档
            similar_docs = self.simhash_engine.find_similar(processed_text, self._local_db)

            # 构建匹配结果
            matches = []
            sources = []

            # 处理分块检测结果
            for chunk_result in check_result['chunk_results']:
                if chunk_result['similarity'] >= self.similarity_threshold:
                    chunk = chunk_result['chunk']
                    matches.append(SimilarityMatch(
                        text=chunk.content[:200],
                        start_index=chunk.start_pos,
                        end_index=chunk.end_pos,
                        similarity=chunk_result['similarity'],
                        source_id=chunk_result['best_match'] or 'unknown',
                        source_title='本地数据库匹配'
                    ))

            # 处理相似文档
            for sim_result in similar_docs:
                sources.append(SimilaritySource(
                    id=sim_result.source_id,
                    title=f"相似文档 {sim_result.source_id}",
                    type='local',
                    similarity=sim_result.similarity,
                    match_count=1
                ))

            # 计算整体相似度
            overall_similarity = check_result['overall_similarity'] * 100

            processing_time = time.time() - start_time

            return PlagiarismResult(
                success=True,
                overall_similarity=overall_similarity,
                internet_similarity=overall_similarity * 0.2,
                publications_similarity=overall_similarity * 0.5,
                student_papers_similarity=overall_similarity * 0.3,
                matches=matches,
                sources=sources,
                processing_time=processing_time
            )

        except Exception as e:
            return PlagiarismResult(
                success=False,
                overall_similarity=0.0,
                internet_similarity=0.0,
                publications_similarity=0.0,
                student_papers_similarity=0.0,
                matches=[],
                sources=[],
                error_message=str(e)
            )

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """本地查重是同步的，直接返回完成"""
        return {
            'status': 'completed',
            'progress': 100
        }

    def add_to_database(self, doc_id: str, text: str):
        """添加文档到本地查重库"""
        self._local_db[doc_id] = text
        self.simhash_engine.add_document(doc_id, text)

    def batch_add_to_database(self, documents: Dict[str, str]):
        """批量添加文档到本地查重库"""
        for doc_id, text in documents.items():
            self.add_to_database(doc_id, text)


class TurnitinEngine(BasePlagiarismEngine):
    """
    Turnitin 查重引擎
    通过 Turnitin API 进行查重
    """

    TURNITIN_API_BASE = 'https://api.turnitin.com/api/v1'

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.institution_id = config.get('institution_id')

    async def check(self, text: str, title: Optional[str] = None) -> PlagiarismResult:
        """使用 Turnitin API 查重"""
        if not self.api_key:
            return PlagiarismResult(
                success=False,
                overall_similarity=0.0,
                internet_similarity=0.0,
                publications_similarity=0.0,
                student_papers_similarity=0.0,
                matches=[],
                sources=[],
                error_message='Turnitin API 密钥未配置'
            )

        # 注意：这是模拟实现，实际需要根据 Turnitin API 文档实现
        # Turnitin API 通常是异步的，需要先提交任务，再轮询结果

        try:
            async with aiohttp.ClientSession() as session:
                # 1. 提交文件
                submit_url = f"{self.TURNITIN_API_BASE}/submissions"

                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }

                payload = {
                    'title': title or 'Untitled',
                    'content': text,
                    'author': {'name': 'API User'},
                    'metadata': {
                        'exclude_bibliography': self.config.get('exclude_bibliography', True),
                        'exclude_quotes': self.config.get('exclude_quotes', False),
                    }
                }

                async with session.post(submit_url, json=payload, headers=headers) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        return PlagiarismResult(
                            success=False,
                            overall_similarity=0.0,
                            internet_similarity=0.0,
                            publications_similarity=0.0,
                            student_papers_similarity=0.0,
                            matches=[],
                            sources=[],
                            error_message=f'Turnitin API 错误: {error_text}'
                        )

                    result = await response.json()
                    submission_id = result.get('id')

                    # 2. 轮询结果
                    return await self._poll_result(session, headers, submission_id)

        except aiohttp.ClientError as e:
            return PlagiarismResult(
                success=False,
                overall_similarity=0.0,
                internet_similarity=0.0,
                publications_similarity=0.0,
                student_papers_similarity=0.0,
                matches=[],
                sources=[],
                error_message=f'网络错误: {str(e)}'
            )
        except Exception as e:
            return PlagiarismResult(
                success=False,
                overall_similarity=0.0,
                internet_similarity=0.0,
                publications_similarity=0.0,
                student_papers_similarity=0.0,
                matches=[],
                sources=[],
                error_message=str(e)
            )

    async def _poll_result(
        self,
        session: aiohttp.ClientSession,
        headers: Dict[str, str],
        submission_id: str,
        max_attempts: int = 30
    ) -> PlagiarismResult:
        """轮询查重结果"""
        for _ in range(max_attempts):
            status_url = f"{self.TURNITIN_API_BASE}/submissions/{submission_id}"

            async with session.get(status_url, headers=headers) as response:
                if response.status != 200:
                    await asyncio.sleep(2)
                    continue

                result = await response.json()
                status = result.get('status')

                if status == 'completed':
                    # 解析结果
                    similarity = result.get('similarity', {})
                    return PlagiarismResult(
                        success=True,
                        overall_similarity=similarity.get('overall', 0.0) * 100,
                        internet_similarity=similarity.get('internet', 0.0) * 100,
                        publications_similarity=similarity.get('publications', 0.0) * 100,
                        student_papers_similarity=similarity.get('student_papers', 0.0) * 100,
                        matches=self._parse_matches(result.get('matches', [])),
                        sources=self._parse_sources(result.get('sources', [])),
                        report_url=result.get('report_url')
                    )
                elif status == 'failed':
                    return PlagiarismResult(
                        success=False,
                        overall_similarity=0.0,
                        internet_similarity=0.0,
                        publications_similarity=0.0,
                        student_papers_similarity=0.0,
                        matches=[],
                        sources=[],
                        error_message=result.get('error_message', '查重失败')
                    )

            await asyncio.sleep(2)

        return PlagiarismResult(
            success=False,
            overall_similarity=0.0,
            internet_similarity=0.0,
            publications_similarity=0.0,
            student_papers_similarity=0.0,
            matches=[],
            sources=[],
            error_message='查询超时'
        )

    def _parse_matches(self, matches_data: List[Dict]) -> List[SimilarityMatch]:
        """解析相似片段"""
        matches = []
        for m in matches_data:
            matches.append(SimilarityMatch(
                text=m.get('text', ''),
                start_index=m.get('start_index', 0),
                end_index=m.get('end_index', 0),
                similarity=m.get('similarity', 0.0),
                source_id=m.get('source_id', ''),
                source_title=m.get('source_title'),
                source_url=m.get('source_url')
            ))
        return matches

    def _parse_sources(self, sources_data: List[Dict]) -> List[SimilaritySource]:
        """解析来源"""
        sources = []
        for s in sources_data:
            sources.append(SimilaritySource(
                id=s.get('id', ''),
                title=s.get('title', ''),
                type=s.get('type', 'unknown'),
                url=s.get('url'),
                similarity=s.get('similarity', 0.0),
                match_count=s.get('match_count', 0)
            ))
        return sources

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """获取 Turnitin 任务状态"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.api_key}'}
                status_url = f"{self.TURNITIN_API_BASE}/submissions/{task_id}"

                async with session.get(status_url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'status': result.get('status'),
                            'progress': result.get('progress', 0)
                        }
                    return {'status': 'unknown', 'progress': 0}
        except Exception:
            return {'status': 'error', 'progress': 0}


class MockPlagiarismEngine(BasePlagiarismEngine):
    """
    模拟查重引擎
    用于开发和测试
    """

    async def check(self, text: str, title: Optional[str] = None) -> PlagiarismResult:
        """生成模拟查重结果"""
        import random
        import time

        start_time = time.time()

        # 生成随机相似度
        overall = random.uniform(5, 35)

        # 生成模拟匹配
        matches = []
        text_length = len(text)
        match_count = random.randint(0, 8)

        for i in range(match_count):
            start = random.randint(0, max(0, text_length - 200))
            end = min(start + random.randint(50, 200), text_length)
            matches.append(SimilarityMatch(
                text=text[start:end][:100],
                start_index=start,
                end_index=end,
                similarity=random.uniform(0.7, 1.0),
                source_id=f'source_{i}',
                source_title=f'Sample Source {i+1}',
                source_url='https://example.com'
            ))

        # 生成模拟来源
        sources = []
        for i in range(min(match_count, 5)):
            sources.append(SimilaritySource(
                id=f'source_{i}',
                title=f'Sample Academic Paper {i+1}',
                type=random.choice(['internet', 'publication', 'student_paper']),
                url='https://example.com',
                similarity=random.uniform(1, overall),
                match_count=random.randint(1, 5)
            ))

        processing_time = time.time() - start_time

        # 模拟处理延迟
        await asyncio.sleep(1)

        return PlagiarismResult(
            success=True,
            overall_similarity=overall,
            internet_similarity=overall * 0.4,
            publications_similarity=overall * 0.35,
            student_papers_similarity=overall * 0.25,
            matches=matches,
            sources=sources,
            report_url='https://example.com/report'
        )

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        return {'status': 'completed', 'progress': 100}


class PlagiarismEngineFactory:
    """查重引擎工厂"""

    _engines = {
        'local': LocalPlagiarismEngine,
        'turnitin': TurnitinEngine,
        'mock': MockPlagiarismEngine,
    }

    @classmethod
    def get_engine(cls, engine_type: str, config: Dict[str, Any]) -> BasePlagiarismEngine:
        """获取查重引擎"""
        engine_class = cls._engines.get(engine_type.lower())
        if not engine_class:
            raise ValueError(f"不支持的查重引擎: {engine_type}")
        return engine_class(config)

    @classmethod
    def register_engine(cls, engine_type: str, engine_class: type):
        """注册新引擎"""
        cls._engines[engine_type.lower()] = engine_class

    @classmethod
    def available_engines(cls) -> List[str]:
        """获取可用引擎列表"""
        return list(cls._engines.keys())
