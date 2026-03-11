"""
数据可视化预览服务
生成数据集的统计摘要和可视化
"""

from typing import List, Dict, Any, Optional
from enum import Enum

from models import DatasetColumn, DataPreview, DataType


class ChartType(str, Enum):
    """图表类型"""
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    PIE_CHART = "pie_chart"


class DataPreviewService:
    """数据预览服务"""

    def __init__(self):
        pass

    async def generate_preview(
        self,
        data: List[Dict[str, Any]],
        columns: List[DatasetColumn],
        max_rows: int = 1000
    ) -> DataPreview:
        """生成数据预览"""
        # 截取样本数据
        sample_data = data[:max_rows]

        # 更新列统计
        for col in columns:
            col.stats = self._calculate_stats(
                [row.get(col.name) for row in data if col.name in row],
                col.data_type
            )

        return DataPreview(
            columns=columns,
            sample_data=sample_data,
            total_rows=len(data),
            total_columns=len(columns),
            memory_usage=self._estimate_memory(data)
        )

    async def generate_visualization(
        self,
        preview: DataPreview,
        chart_type: ChartType,
        x_column: str,
        y_column: Optional[str] = None,
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成可视化配置"""
        x_col = next((c for c in preview.columns if c.name == x_column), None)
        if not x_col:
            raise ValueError(f"列 {x_column} 不存在")

        config = {
            "chart_type": chart_type.value,
            "title": f"{x_column} 可视化",
            "x_axis": {"name": x_column, "type": x_col.data_type},
            "series": []
        }

        if chart_type == ChartType.HISTOGRAM:
            config["series"] = self._generate_histogram(preview, x_column)
        elif chart_type == ChartType.BAR_CHART:
            config["series"] = self._generate_bar_chart(preview, x_column, y_column)
        elif chart_type == ChartType.SCATTER_PLOT:
            config["series"] = self._generate_scatter(preview, x_column, y_column)
        elif chart_type == ChartType.BOX_PLOT:
            config["series"] = self._generate_box_plot(preview, x_column)

        return config

    async def generate_profile(
        self,
        preview: DataPreview
    ) -> Dict[str, Any]:
        """生成数据画像"""
        profile = {
            "overview": {
                "total_rows": preview.total_rows,
                "total_columns": preview.total_columns,
                "memory_usage": preview.memory_usage,
                "data_quality_score": 0
            },
            "columns": [],
            "warnings": [],
            "recommendations": []
        }

        total_quality = 0
        for col in preview.columns:
            col_profile = self._profile_column(col, preview.sample_data)
            profile["columns"].append(col_profile)
            total_quality += col_profile.get("quality_score", 100)

            # 检查问题
            if col_profile.get("missing_ratio", 0) > 0.5:
                profile["warnings"].append(f"列 '{col.name}' 缺失值过多")

        profile["overview"]["data_quality_score"] = total_quality / len(preview.columns) if preview.columns else 100

        return profile

    def _calculate_stats(
        self,
        values: List[Any],
        data_type: str
    ) -> Dict[str, Any]:
        """计算列统计信息"""
        if not values:
            return {}

        stats = {
            "count": len(values),
            "null_count": sum(1 for v in values if v is None or v == ""),
            "unique_count": len(set(values))
        }

        # 数值类型统计
        if data_type in ["int", "float", "number"]:
            numeric_values = [float(v) for v in values if v is not None]
            if numeric_values:
                stats["min"] = min(numeric_values)
                stats["max"] = max(numeric_values)
                stats["mean"] = sum(numeric_values) / len(numeric_values)

        # 字符串类型统计
        elif data_type in ["string", "text"]:
            str_values = [str(v) for v in values if v is not None]
            if str_values:
                stats["avg_length"] = sum(len(s) for s in str_values) / len(str_values)
                stats["max_length"] = max(len(s) for s in str_values)

        return stats

    def _profile_column(
        self,
        column: DatasetColumn,
        sample_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析单列特征"""
        values = [row.get(column.name) for row in sample_data]

        profile = {
            "name": column.name,
            "type": column.data_type,
            "stats": column.stats,
            "quality_score": 100
        }

        # 计算缺失率
        null_count = sum(1 for v in values if v is None or v == "")
        missing_ratio = null_count / len(values) if values else 0
        profile["missing_ratio"] = missing_ratio

        # 根据缺失率调整质量分
        profile["quality_score"] -= int(missing_ratio * 50)

        return profile

    def _estimate_memory(self, data: List[Dict[str, Any]]) -> int:
        """估计内存占用"""
        import sys
        return sys.getsizeof(data)

    def _generate_histogram(
        self,
        preview: DataPreview,
        column: str
    ) -> List[Dict[str, Any]]:
        """生成直方图数据"""
        values = [row.get(column) for row in preview.sample_data if row.get(column) is not None]

        # 简单分桶
        if not values:
            return []

        min_val = min(values)
        max_val = max(values)
        bucket_count = min(10, len(set(values)))
        bucket_size = (max_val - min_val) / bucket_count if max_val != min_val else 1

        buckets = [0] * bucket_count
        for v in values:
            idx = int((v - min_val) / bucket_size)
            idx = min(idx, bucket_count - 1)
            buckets[idx] += 1

        return [{
            "name": f"{min_val + i * bucket_size:.2f}-{min_val + (i + 1) * bucket_size:.2f}",
            "value": count
        } for i, count in enumerate(buckets)]

    def _generate_bar_chart(
        self,
        preview: DataPreview,
        x_column: str,
        y_column: Optional[str]
    ) -> List[Dict[str, Any]]:
        """生成柱状图数据"""
        if y_column:
            # 聚合数据
            agg = {}
            for row in preview.sample_data:
                x = row.get(x_column)
                y = row.get(y_column, 0)
                if x not in agg:
                    agg[x] = 0
                agg[x] += float(y) if y else 0
            return [{"name": k, "value": v} for k, v in agg.items()]
        else:
            # 计数
            counts = {}
            for row in preview.sample_data:
                x = row.get(x_column)
                counts[x] = counts.get(x, 0) + 1
            return [{"name": k, "value": v} for k, v in counts.items()]

    def _generate_scatter(
        self,
        preview: DataPreview,
        x_column: str,
        y_column: Optional[str]
    ) -> List[Dict[str, Any]]:
        """生成散点图数据"""
        if not y_column:
            return []

        return [
            {
                "x": row.get(x_column),
                "y": row.get(y_column)
            }
            for row in preview.sample_data
            if row.get(x_column) is not None and row.get(y_column) is not None
        ]

    def _generate_box_plot(
        self,
        preview: DataPreview,
        column: str
    ) -> List[Dict[str, Any]]:
        """生成箱线图数据"""
        values = sorted([row.get(column) for row in preview.sample_data if row.get(column) is not None])

        if not values:
            return []

        n = len(values)
        q1 = values[n // 4]
        median = values[n // 2]
        q3 = values[3 * n // 4]
        min_val = values[0]
        max_val = values[-1]

        return [{
            "name": column,
            "min": min_val,
            "q1": q1,
            "median": median,
            "q3": q3,
            "max": max_val
        }]


# 服务实例
preview_service = DataPreviewService()
