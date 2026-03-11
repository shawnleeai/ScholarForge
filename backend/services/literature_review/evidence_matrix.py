"""
证据矩阵生成服务
生成多文献对比矩阵
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from .evidence_extractor import Evidence, EvidenceType, EvidenceStrength


@dataclass
class MatrixCell:
    """矩阵单元格"""
    row_id: str  # 文献ID
    col_id: str  # 维度ID
    value: Any
    display_value: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatrixRow:
    """矩阵行（文献）"""
    article_id: str
    article_title: str
    authors: List[str]
    year: Optional[int]
    journal: Optional[str]
    cells: Dict[str, MatrixCell] = field(default_factory=dict)


@dataclass
class MatrixColumn:
    """矩阵列（维度）"""
    id: str
    name: str
    description: str
    type: str  # text/number/boolean/select
    options: Optional[List[str]] = None  # 用于select类型


@dataclass
class EvidenceMatrix:
    """证据矩阵"""
    id: str
    title: str
    description: Optional[str]
    columns: List[MatrixColumn]
    rows: List[MatrixRow]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "columns": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "type": c.type,
                    "options": c.options,
                }
                for c in self.columns
            ],
            "rows": [
                {
                    "article_id": r.article_id,
                    "article_title": r.article_title,
                    "authors": r.authors,
                    "year": r.year,
                    "journal": r.journal,
                    "cells": {
                        k: {
                            "value": v.value,
                            "display_value": v.display_value,
                            "metadata": v.metadata,
                        }
                        for k, v in r.cells.items()
                    },
                }
                for r in self.rows
            ],
            "created_at": self.created_at.isoformat(),
        }


class EvidenceMatrixGenerator:
    """
    证据矩阵生成器
    生成多文献对比矩阵
    """

    # 标准对比维度
    STANDARD_DIMENSIONS = [
        {
            "id": "study_design",
            "name": "研究设计",
            "description": "研究采用的设计类型",
            "type": "select",
            "options": ["实验研究", "准实验", "观察性研究", "案例研究", "元分析", "理论研究"],
        },
        {
            "id": "sample_size",
            "name": "样本量",
            "description": "研究样本大小",
            "type": "number",
        },
        {
            "id": "population",
            "name": "研究对象",
            "description": "研究针对的人群/样本",
            "type": "text",
        },
        {
            "id": "main_finding",
            "name": "主要发现",
            "description": "研究的主要结论",
            "type": "text",
        },
        {
            "id": "effect_direction",
            "name": "效应方向",
            "description": "效果的正负方向",
            "type": "select",
            "options": ["正面", "负面", "无效果", "混合", "不确定"],
        },
        {
            "id": "effect_size",
            "name": "效应量",
            "description": "效应量大小",
            "type": "select",
            "options": ["大", "中", "小", "可忽略", "未报告"],
        },
        {
            "id": "evidence_quality",
            "name": "证据质量",
            "description": "证据的整体质量",
            "type": "select",
            "options": ["高", "中", "低", "很低"],
        },
        {
            "id": "limitations",
            "name": "主要局限",
            "description": "研究的主要局限性",
            "type": "text",
        },
    ]

    def __init__(self):
        pass

    def generate_matrix(
        self,
        evidences: List[Evidence],
        title: str = "文献证据矩阵",
        description: Optional[str] = None,
        custom_dimensions: Optional[List[Dict]] = None,
    ) -> EvidenceMatrix:
        """
        生成证据矩阵

        Args:
            evidences: 证据列表
            title: 矩阵标题
            description: 矩阵描述
            custom_dimensions: 自定义维度

        Returns:
            EvidenceMatrix: 证据矩阵
        """
        import uuid

        # 使用标准维度或自定义维度
        dimensions = custom_dimensions or self.STANDARD_DIMENSIONS

        # 创建列定义
        columns = [
            MatrixColumn(
                id=d["id"],
                name=d["name"],
                description=d.get("description", ""),
                type=d.get("type", "text"),
                options=d.get("options"),
            )
            for d in dimensions
        ]

        # 创建行数据
        rows = []
        for evidence in evidences:
            row = self._create_matrix_row(evidence, columns)
            rows.append(row)

        return EvidenceMatrix(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            columns=columns,
            rows=rows,
        )

    def _create_matrix_row(
        self,
        evidence: Evidence,
        columns: List[MatrixColumn]
    ) -> MatrixRow:
        """创建矩阵行"""
        row = MatrixRow(
            article_id=evidence.article_id,
            article_title=evidence.article_title,
            authors=evidence.authors,
            year=evidence.year,
            journal=evidence.journal,
        )

        # 填充每个单元格
        for col in columns:
            cell = self._create_cell(evidence, col)
            row.cells[col.id] = cell

        return row

    def _create_cell(self, evidence: Evidence, column: MatrixColumn) -> MatrixCell:
        """创建单元格数据"""
        value = None
        display_value = "-"

        if column.id == "study_design":
            if evidence.study_design:
                value = evidence.study_design.design_type
                display_value = value

        elif column.id == "sample_size":
            if evidence.study_design:
                value = evidence.study_design.sample_size
                display_value = str(value) if value else "未报告"

        elif column.id == "population":
            value = evidence.sample_description
            display_value = value[:50] + "..." if value and len(value) > 50 else (value or "-")

        elif column.id == "main_finding":
            value = evidence.claim
            display_value = evidence.claim[:60] + "..." if len(evidence.claim) > 60 else evidence.claim

        elif column.id == "effect_direction":
            # 从发现中推断方向
            value = self._infer_effect_direction(evidence)
            display_value = value

        elif column.id == "effect_size":
            stats = evidence.statistics or {}
            value = stats.get("effect_size", "未报告")
            display_value = value

        elif column.id == "evidence_quality":
            quality_map = {
                EvidenceStrength.STRONG: "高",
                EvidenceStrength.MODERATE: "中",
                EvidenceStrength.WEAK: "低",
                EvidenceStrength.INCONCLUSIVE: "很低",
            }
            value = evidence.evidence_strength.value
            display_value = quality_map.get(evidence.evidence_strength, "未知")

        elif column.id == "limitations":
            value = evidence.limitations
            display_value = "; ".join(evidence.limitations[:2]) if evidence.limitations else "未报告"

        return MatrixCell(
            row_id=evidence.article_id,
            col_id=column.id,
            value=value,
            display_value=display_value,
            metadata={"evidence_type": evidence.evidence_type.value},
        )

    def _infer_effect_direction(self, evidence: Evidence) -> str:
        """推断效应方向"""
        findings = " ".join(evidence.key_findings).lower()

        positive_keywords = ["positive", "significant", "effective", "improve", "increase", "benefit"]
        negative_keywords = ["negative", "decrease", "reduce", "worse", "harm"]

        pos_count = sum(1 for kw in positive_keywords if kw in findings)
        neg_count = sum(1 for kw in negative_keywords if kw in findings)

        if pos_count > neg_count:
            return "正面"
        elif neg_count > pos_count:
            return "负面"
        elif pos_count == 0 and neg_count == 0:
            return "无效果"
        else:
            return "混合"

    def generate_comparison_summary(self, matrix: EvidenceMatrix) -> Dict[str, Any]:
        """
        生成矩阵的对比总结

        Args:
            matrix: 证据矩阵

        Returns:
            Dict: 总结信息
        """
        total_studies = len(matrix.rows)

        # 统计效应方向
        directions = {"正面": 0, "负面": 0, "无效果": 0, "混合": 0, "不确定": 0}
        for row in matrix.rows:
            if "effect_direction" in row.cells:
                direction = row.cells["effect_direction"].display_value
                if direction in directions:
                    directions[direction] += 1

        # 统计研究设计
        designs = {}
        for row in matrix.rows:
            if "study_design" in row.cells:
                design = row.cells["study_design"].display_value
                designs[design] = designs.get(design, 0) + 1

        # 统计证据质量
        qualities = {"高": 0, "中": 0, "低": 0, "很低": 0}
        for row in matrix.rows:
            if "evidence_quality" in row.cells:
                quality = row.cells["evidence_quality"].display_value
                if quality in qualities:
                    qualities[quality] += 1

        # 计算平均样本量
        sample_sizes = []
        for row in matrix.rows:
            if "sample_size" in row.cells:
                val = row.cells["sample_size"].value
                if val and isinstance(val, int):
                    sample_sizes.append(val)

        avg_sample_size = sum(sample_sizes) / len(sample_sizes) if sample_sizes else 0

        return {
            "total_studies": total_studies,
            "effect_directions": directions,
            "study_designs": designs,
            "evidence_qualities": qualities,
            "average_sample_size": round(avg_sample_size, 1),
            "sample_size_range": {
                "min": min(sample_sizes) if sample_sizes else 0,
                "max": max(sample_sizes) if sample_sizes else 0,
            },
        }


# 服务实例
_matrix_generator: Optional[EvidenceMatrixGenerator] = None


def get_matrix_generator() -> EvidenceMatrixGenerator:
    """获取矩阵生成器单例"""
    global _matrix_generator
    if _matrix_generator is None:
        _matrix_generator = EvidenceMatrixGenerator()
    return _matrix_generator
