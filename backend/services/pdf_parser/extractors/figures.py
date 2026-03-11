"""
PDF 图表提取器
提取PDF中的图片和表格
"""

import os
import re
import base64
from typing import List, Optional, Dict
from pathlib import Path
import fitz
from ..schemas import Figure
import logging

logger = logging.getLogger(__name__)


class FigureExtractor:
    """PDF图表提取器"""

    def __init__(self, output_dir: str = "./uploads/figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def extract(self, pdf_path: str, extract_images: bool = True) -> List[Figure]:
        """
        提取PDF中的图表

        Args:
            pdf_path: PDF文件路径
            extract_images: 是否提取图片文件

        Returns:
            List[Figure] 图表列表
        """
        figures = []

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"无法打开PDF: {e}")
            return figures

        for page_num, page in enumerate(doc, 1):
            # 提取图片
            if extract_images:
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list, 1):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # 保存图片
                        figure_id = f"page{page_num}_img{img_index}"
                        filename = f"{figure_id}.{image_ext}"
                        filepath = self.output_dir / filename

                        with open(filepath, "wb") as f:
                            f.write(image_bytes)

                        # 查找图片说明
                        caption = self._find_caption(page, img_index, "figure")

                        figures.append(Figure(
                            id=figure_id,
                            type="figure",
                            caption=caption,
                            page_number=page_num,
                        ))
                    except Exception as e:
                        logger.warning(f"提取图片失败 (page {page_num}): {e}")

            # 提取表格（通过检测表格区域）
            tables = self._detect_tables(page)
            for table_idx, table in enumerate(tables, 1):
                caption = self._find_caption(page, table_idx, "table")
                figures.append(Figure(
                    id=f"page{page_num}_table{table_idx}",
                    type="table",
                    caption=caption,
                    page_number=page_num,
                    bbox=table.get("bbox"),
                ))

        doc.close()
        return figures

    def _detect_tables(self, page: fitz.Page) -> List[Dict]:
        """检测页面中的表格"""
        tables = []

        # 获取页面上的所有文本块
        blocks = page.get_text("blocks")

        # 表格特征：多列对齐的文本块
        # 这是一个简化的检测，实际可能需要更复杂的算法
        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block

            # 检测可能的表格：包含多行且对齐的文本
            lines = text.strip().split('\n')
            if len(lines) >= 3:  # 至少3行
                # 检查是否有表格特征（如制表符、多个空格分隔）
                tab_count = sum(1 for line in lines if '\t' in line or '  ' in line)
                if tab_count >= 2:  # 至少2行有制表特征
                    tables.append({
                        "bbox": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
                        "text": text[:200],  # 保存部分文本用于识别
                    })

        return tables

    def _find_caption(self, page: fitz.Page, index: int, figure_type: str) -> Optional[str]:
        """
        查找图表的说明文字

        Args:
            page: PDF页面对象
            index: 图表序号
            figure_type: "figure" 或 "table"
        """
        text = page.get_text()

        # 根据类型构建匹配模式
        if figure_type == "figure":
            patterns = [
                rf'图\s*{index}[.\s]+([^\n]+)',  # 中文：图 1. 说明
                rf'Figure\s*{index}[.:]?\s*([^\n]+)',  # 英文：Figure 1. Caption
                rf'Fig\.?\s*{index}[.:]?\s*([^\n]+)',  # Fig. 1. Caption
            ]
        else:  # table
            patterns = [
                rf'表\s*{index}[.\s]+([^\n]+)',  # 中文：表 1. 说明
                rf'Table\s*{index}[.:]?\s*([^\n]+)',  # 英文：Table 1. Caption
            ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                caption = match.group(1).strip()
                # 限制长度
                if len(caption) > 200:
                    caption = caption[:200] + "..."
                return caption

        return None

    async def extract_with_ocr(self, pdf_path: str, figure: Figure) -> Optional[str]:
        """
        对图表进行OCR识别

        Note: 需要安装 paddleocr 或 pytesseract
        """
        try:
            # 尝试使用 PaddleOCR（中文支持更好）
            from paddleocr import PaddleOCR

            ocr = PaddleOCR(use_angle_cls=True, lang='ch')

            # 找到对应的图片文件
            figure_path = self.output_dir / f"{figure.id}.png"
            if not figure_path.exists():
                return None

            result = ocr.ocr(str(figure_path), cls=True)

            # 提取识别的文本
            texts = []
            for line in result:
                if line:
                    for word in line:
                        texts.append(word[1][0])  # 文本内容

            return ' '.join(texts)

        except ImportError:
            logger.warning("PaddleOCR 未安装，跳过OCR识别")
            return None
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return None
