"""
PDF 解析器主类
整合所有提取器，提供统一的PDF解析接口
"""

import uuid
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .schemas import (
    PDFParseTask,
    PDFContent,
    PDFMetadata,
    AIAnalysisResult,
    Section,
)
from .extractors import (
    TextExtractor,
    ReferenceExtractor,
    MetadataExtractor,
    FigureExtractor,
)


class PDFParser:
    """PDF解析器"""

    def __init__(
        self,
        ai_service=None,
        enable_ocr: bool = False,
        figure_output_dir: str = "./uploads/figures",
    ):
        self.text_extractor = TextExtractor()
        self.reference_extractor = ReferenceExtractor()
        self.metadata_extractor = MetadataExtractor()
        self.figure_extractor = FigureExtractor(output_dir=figure_output_dir)
        self.ai_service = ai_service
        self.enable_ocr = enable_ocr

    async def parse(
        self,
        file_path: str,
        enable_ai: bool = True,
        extract_references: bool = True,
        extract_figures: bool = False,
    ) -> PDFParseTask:
        """
        解析PDF文件

        Args:
            file_path: PDF文件路径
            enable_ai: 是否启用AI分析
            extract_references: 是否提取参考文献
            extract_figures: 是否提取图表

        Returns:
            PDFParseTask 解析任务结果
        """
        task_id = str(uuid.uuid4())
        start_time = time.time()

        task = PDFParseTask(
            task_id=task_id,
            status="processing",
            file_name=Path(file_path).name,
            file_size=Path(file_path).stat().st_size,
            file_path=file_path,
        )

        try:
            # 1. 提取文本和章节结构
            text_result = await self.text_extractor.extract(file_path)

            # 2. 提取元数据
            metadata = self.metadata_extractor.extract(
                file_path, text_result["full_text"]
            )

            # 3. 提取参考文献
            references = []
            if extract_references:
                references = self.reference_extractor.extract(
                    text_result["full_text"]
                )

            # 4. 提取图表
            figures = []
            if extract_figures:
                figures = await self.figure_extractor.extract(
                    file_path, extract_images=True
                )

            # 构建Section对象
            sections = [
                Section(
                    title=s["title"],
                    content=s["content"],
                    level=s.get("level", 1),
                    page_start=s.get("page_start"),
                    page_end=s.get("page_end"),
                )
                for s in text_result["sections"]
            ]

            # 构建内容对象
            content = PDFContent(
                full_text=text_result["full_text"],
                sections=sections,
                references=references,
                figures=figures,
                metadata=metadata,
            )

            task.content = content

            # 5. AI分析
            if enable_ai and self.ai_service:
                ai_result = await self._analyze_with_ai(content)
                task.ai_analysis = ai_result

            # 计算处理时间
            processing_time = int((time.time() - start_time) * 1000)

            task.status = "completed"
            task.completed_at = datetime.now()
            task.processing_time_ms = processing_time

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now()

        return task

    async def _analyze_with_ai(self, content: PDFContent) -> AIAnalysisResult:
        """使用AI分析文献内容"""
        if not self.ai_service:
            return AIAnalysisResult(summary="AI服务未配置")

        # 截断文本以避免超出token限制
        text_for_analysis = content.full_text[:15000]

        # 并行执行多个AI分析任务
        import asyncio

        summary_task = self._generate_summary(text_for_analysis)
        key_points_task = self._extract_key_points(text_for_analysis)
        methodology_task = self._analyze_methodology(text_for_analysis)

        summary, key_points, methodology = await asyncio.gather(
            summary_task, key_points_task, methodology_task
        )

        return AIAnalysisResult(
            summary=summary,
            key_points=key_points,
            methodology=methodology,
        )

    async def _generate_summary(self, text: str) -> str:
        """生成AI摘要"""
        prompt = f"""请为以下学术论文生成一段简洁的摘要（300字以内）：

论文内容：
{text[:8000]}

要求：
1. 概括研究背景和目的
2. 说明研究方法
3. 总结主要发现
4. 指出研究意义

摘要："""

        try:
            result = await self.ai_service.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3,
                system_prompt="你是一位专业的学术文献分析专家，擅长提炼论文核心内容。",
            )
            return result.content if hasattr(result, "content") else str(result)
        except Exception as e:
            return f"摘要生成失败: {str(e)}"

    async def _extract_key_points(self, text: str) -> list:
        """提取核心观点"""
        prompt = f"""请从以下论文中提取5-8个核心观点或关键发现：

论文内容：
{text[:8000]}

请以列表形式返回，每行一个观点：
- 观点1
- 观点2
..."""

        try:
            result = await self.ai_service.generate(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3,
            )
            content = result.content if hasattr(result, "content") else str(result)

            # 解析列表
            points = [line.strip("- ").strip() for line in content.split("\n") if line.strip().startswith("-")]
            return points[:8]
        except Exception as e:
            return [f"关键观点提取失败: {str(e)}"]

    async def _analyze_methodology(self, text: str) -> dict:
        """分析研究方法"""
        prompt = f"""请分析以下论文的研究方法：

论文内容：
{text[:6000]}

请用简洁的语言说明：
1. 研究类型（定性/定量/混合）
2. 数据收集方法
3. 分析方法

格式：研究类型 | 数据收集 | 分析方法"""

        try:
            result = await self.ai_service.generate(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3,
            )
            content = result.content if hasattr(result, "content") else str(result)

            # 解析结果
            parts = content.split("|")
            if len(parts) >= 3:
                return {
                    "research_type": parts[0].strip(),
                    "data_collection": parts[1].strip(),
                    "analysis_method": parts[2].strip(),
                }
            return {"raw_analysis": content}
        except Exception as e:
            return {"error": str(e)}


class PDFParseManager:
    """PDF解析任务管理器"""

    def __init__(self):
        self._tasks: Dict[str, PDFParseTask] = {}
        self._parser: Optional[PDFParser] = None

    def initialize(self, ai_service=None, **kwargs):
        """初始化解析器"""
        self._parser = PDFParser(ai_service=ai_service, **kwargs)

    async def submit_task(
        self,
        file_path: str,
        **options,
    ) -> str:
        """提交解析任务"""
        if not self._parser:
            raise RuntimeError("PDFParser未初始化")

        task = await self._parser.parse(file_path, **options)
        self._tasks[task.task_id] = task
        return task.task_id

    def get_task(self, task_id: str) -> Optional[PDFParseTask]:
        """获取任务状态"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list:
        """获取所有任务"""
        return list(self._tasks.values())
