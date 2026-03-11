"""
智能图表推荐服务
根据数据特征推荐最合适的图表类型
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ChartType(str, Enum):
    """图表类型"""
    # 基础图表
    BAR = "bar"                      # 柱状图
    LINE = "line"                    # 折线图
    PIE = "pie"                      # 饼图
    SCATTER = "scatter"              # 散点图
    AREA = "area"                    # 面积图

    # 高级图表
    HEATMAP = "heatmap"              # 热力图
    RADAR = "radar"                  # 雷达图
    TREEMAP = "treemap"              # 树图
    SUNBURST = "sunburst"            # 旭日图
    SANKEY = "sankey"                # 桑基图
    FUNNEL = "funnel"                # 漏斗图
    GAUGE = "gauge"                  # 仪表盘

    # 统计图表
    BOXPLOT = "boxplot"              # 箱线图
    HISTOGRAM = "histogram"          # 直方图
    VIOLIN = "violin"                # 小提琴图
    ERROR_BAR = "error_bar"          # 误差线图

    # 关系图表
    GRAPH = "graph"                  # 关系图
    TREE = "tree"                    # 树图

    # 地理图表
    MAP = "map"                      # 地图
    GEO = "geo"                      # 地理坐标图


class DataType(str, Enum):
    """数据类型"""
    CATEGORICAL = "categorical"      # 分类数据
    NUMERICAL = "numerical"          # 数值数据
    TEMPORAL = "temporal"            # 时间数据
    ORDINAL = "ordinal"              # 有序数据
    NOMINAL = "nominal"              # 名义数据


@dataclass
class DataColumn:
    """数据列"""
    name: str
    data_type: DataType
    unique_count: int
    sample_values: List[Any]
    is_nullable: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class DataProfile:
    """数据特征"""
    row_count: int
    column_count: int
    columns: List[DataColumn]
    has_time_series: bool = False
    has_categories: bool = False
    has_multiple_series: bool = False
    correlation_matrix: Optional[List[List[float]]] = None


@dataclass
class ChartRecommendation:
    """图表推荐结果"""
    chart_type: ChartType
    score: float                       # 匹配分数 0-1
    confidence: str                    # high/medium/low
    reason: str                        # 推荐理由
    suitability: Dict[str, float]      # 各维度适用性
    suggested_config: Dict[str, Any]   # 建议配置
    alternatives: List[ChartType]      # 替代方案


class ChartRecommendationEngine:
    """
    图表推荐引擎
    基于数据特征智能推荐图表类型
    """

    def __init__(self):
        self._initialize_rules()

    def _initialize_rules(self):
        """初始化推荐规则"""
        self.rules = {
            ChartType.BAR: {
                "min_columns": 2,
                "ideal_columns": 2,
                "required_types": [DataType.CATEGORICAL, DataType.NUMERICAL],
                "max_categories": 50,
                "suitability_weights": {
                    "comparison": 0.9,
                    "ranking": 0.9,
                    "distribution": 0.6,
                    "trend": 0.3,
                }
            },
            ChartType.LINE: {
                "min_columns": 2,
                "ideal_columns": 2,
                "required_types": [DataType.TEMPORAL, DataType.NUMERICAL],
                "suitability_weights": {
                    "trend": 0.95,
                    "comparison": 0.7,
                    "distribution": 0.4,
                }
            },
            ChartType.PIE: {
                "min_columns": 2,
                "ideal_columns": 2,
                "required_types": [DataType.CATEGORICAL, DataType.NUMERICAL],
                "max_categories": 8,
                "suitability_weights": {
                    "proportion": 0.95,
                    "comparison": 0.5,
                    "distribution": 0.3,
                }
            },
            ChartType.SCATTER: {
                "min_columns": 2,
                "ideal_columns": 2,
                "required_types": [DataType.NUMERICAL, DataType.NUMERICAL],
                "suitability_weights": {
                    "correlation": 0.95,
                    "distribution": 0.8,
                    "comparison": 0.6,
                }
            },
            ChartType.HEATMAP: {
                "min_columns": 3,
                "ideal_columns": 3,
                "required_types": [DataType.CATEGORICAL, DataType.CATEGORICAL, DataType.NUMERICAL],
                "suitability_weights": {
                    "correlation": 0.9,
                    "pattern": 0.85,
                    "distribution": 0.7,
                }
            },
            ChartType.RADAR: {
                "min_columns": 4,
                "required_types": [DataType.NUMERICAL],
                "suitability_weights": {
                    "multivariate": 0.9,
                    "comparison": 0.7,
                }
            },
            ChartType.BOXPLOT: {
                "min_columns": 2,
                "required_types": [DataType.CATEGORICAL, DataType.NUMERICAL],
                "suitability_weights": {
                    "distribution": 0.95,
                    "outlier": 0.9,
                    "comparison": 0.7,
                }
            },
        }

    def recommend(self, data_profile: DataProfile,
                  purpose: Optional[str] = None,
                  top_k: int = 3) -> List[ChartRecommendation]:
        """
        推荐图表类型

        Args:
            data_profile: 数据特征
            purpose: 图表目的 (comparison/trend/distribution/correlation/proportion)
            top_k: 返回推荐数量

        Returns:
            推荐结果列表
        """
        recommendations = []

        for chart_type in ChartType:
            score, reason, config = self._evaluate_chart_type(
                chart_type, data_profile, purpose
            )

            if score > 0:
                confidence = self._get_confidence_level(score)
                suitability = self._calculate_suitability(chart_type, purpose)
                alternatives = self._get_alternatives(chart_type, data_profile)

                recommendations.append(ChartRecommendation(
                    chart_type=chart_type,
                    score=score,
                    confidence=confidence,
                    reason=reason,
                    suitability=suitability,
                    suggested_config=config,
                    alternatives=alternatives,
                ))

        # 排序并返回前k个
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:top_k]

    def _evaluate_chart_type(self, chart_type: ChartType,
                             data_profile: DataProfile,
                             purpose: Optional[str]) -> tuple[float, str, Dict]:
        """评估图表类型匹配度"""

        if chart_type not in self.rules:
            return 0.0, "不支持的数据配置", {}

        rule = self.rules[chart_type]
        score = 0.5  # 基础分
        reasons = []
        config = {}

        # 检查列数
        if data_profile.column_count < rule["min_columns"]:
            return 0.0, f"列数不足，需要至少{rule['min_columns']}列", {}

        if data_profile.column_count == rule.get("ideal_columns", 2):
            score += 0.2
            reasons.append("列数理想")

        # 检查数据类型匹配
        data_types = [col.data_type for col in data_profile.columns]
        required_types = rule.get("required_types", [])

        type_match = sum(1 for t in required_types if any(
            dt.value.startswith(t.value) for dt in data_types
        )) / len(required_types) if required_types else 1.0

        score += type_match * 0.3

        # 检查目的匹配
        if purpose and purpose in rule.get("suitability_weights", {}):
            purpose_score = rule["suitability_weights"][purpose]
            score += purpose_score * 0.2
            reasons.append(f"适合{purpose}")

        # 特定图表类型的额外检查
        if chart_type == ChartType.BAR:
            categorical_cols = [c for c in data_profile.columns
                               if c.data_type == DataType.CATEGORICAL]
            if categorical_cols and categorical_cols[0].unique_count <= rule.get("max_categories", 50):
                score += 0.1
                config["orientation"] = "vertical"

        elif chart_type == ChartType.PIE:
            categorical_cols = [c for c in data_profile.columns
                               if c.data_type == DataType.CATEGORICAL]
            if categorical_cols and categorical_cols[0].unique_count <= rule.get("max_categories", 8):
                score += 0.1
                reasons.append("类别数量适中")
            else:
                score -= 0.2
                reasons.append("类别过多，建议使用柱状图")

        elif chart_type == ChartType.LINE:
            if data_profile.has_time_series:
                score += 0.2
                reasons.append("包含时间序列数据")
                config["time_axis"] = True

        elif chart_type == ChartType.SCATTER:
            numerical_cols = [c for c in data_profile.columns
                            if c.data_type == DataType.NUMERICAL]
            if len(numerical_cols) >= 2 and data_profile.correlation_matrix:
                # 检查相关性
                corr = data_profile.correlation_matrix[0][1]
                if abs(corr) > 0.5:
                    score += 0.15
                    reasons.append(f"变量相关性较强 (r={corr:.2f})")

        # 生成配置建议
        config.update(self._generate_config(chart_type, data_profile))

        final_score = min(score, 1.0)
        reason_text = "；".join(reasons) if reasons else "基本匹配"

        return final_score, reason_text, config

    def _get_confidence_level(self, score: float) -> str:
        """获取置信度级别"""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        else:
            return "low"

    def _calculate_suitability(self, chart_type: ChartType,
                               purpose: Optional[str]) -> Dict[str, float]:
        """计算各维度适用性"""
        rule = self.rules.get(chart_type, {})
        weights = rule.get("suitability_weights", {})

        dimensions = ["comparison", "trend", "distribution", "correlation",
                     "proportion", "ranking", "pattern", "multivariate"]

        return {
            dim: weights.get(dim, 0.3) for dim in dimensions
        }

    def _get_alternatives(self, chart_type: ChartType,
                         data_profile: DataProfile) -> List[ChartType]:
        """获取替代方案"""
        alternatives_map = {
            ChartType.BAR: [ChartType.LINE, ChartType.PIE],
            ChartType.LINE: [ChartType.BAR, ChartType.AREA],
            ChartType.PIE: [ChartType.BAR, ChartType.TREEMAP],
            ChartType.SCATTER: [ChartType.BOXPLOT, ChartType.HEATMAP],
            ChartType.HEATMAP: [ChartType.SCATTER, ChartType.BAR],
        }

        return alternatives_map.get(chart_type, [])[:2]

    def _generate_config(self, chart_type: ChartType,
                        data_profile: DataProfile) -> Dict[str, Any]:
        """生成图表配置建议"""
        config = {
            "chart_type": chart_type.value,
            "animation": True,
            "tooltip": True,
        }

        # 根据数据特征添加配置
        numerical_cols = [c for c in data_profile.columns
                         if c.data_type == DataType.NUMERICAL]
        categorical_cols = [c for c in data_profile.columns
                           if c.data_type == DataType.CATEGORICAL]

        if numerical_cols:
            config["y_axis"] = {
                "name": numerical_cols[0].name,
                "min": numerical_cols[0].min_value,
                "max": numerical_cols[0].max_value,
            }

        if categorical_cols:
            config["x_axis"] = {
                "name": categorical_cols[0].name,
                "type": "category",
            }

        # 图表特定配置
        if chart_type == ChartType.BAR:
            config["bar_width"] = "60%"
            if data_profile.row_count > 20:
                config["data_zoom"] = True

        elif chart_type == ChartType.LINE:
            config["smooth"] = True
            config["symbol"] = "circle"

        elif chart_type == ChartType.PIE:
            config["radius"] = ["40%", "70%"]
            config["rose_type"] = "area"

        return config

    def analyze_data(self, data: List[Dict[str, Any]]) -> DataProfile:
        """
        分析数据特征

        Args:
            data: 数据列表

        Returns:
            数据特征分析结果
        """
        if not data:
            return DataProfile(row_count=0, column_count=0, columns=[])

        # 获取列信息
        columns = []
        sample_row = data[0]

        for col_name, sample_value in sample_row.items():
            col_values = [row.get(col_name) for row in data if row.get(col_name) is not None]
            unique_values = list(set(col_values))

            # 推断数据类型
            data_type = self._infer_data_type(col_values, col_name)

            # 计算数值范围
            min_val = None
            max_val = None
            if data_type == DataType.NUMERICAL:
                try:
                    numeric_values = [float(v) for v in col_values if v is not None]
                    if numeric_values:
                        min_val = min(numeric_values)
                        max_val = max(numeric_values)
                except:
                    pass

            columns.append(DataColumn(
                name=col_name,
                data_type=data_type,
                unique_count=len(unique_values),
                sample_values=unique_values[:5],
                is_nullable=any(row.get(col_name) is None for row in data),
                min_value=min_val,
                max_value=max_val,
            ))

        # 检查是否有时间序列
        has_time_series = any(c.data_type == DataType.TEMPORAL for c in columns)

        # 检查是否有分类数据
        has_categories = any(c.data_type == DataType.CATEGORICAL for c in columns)

        # 计算相关性矩阵（仅数值列）
        correlation_matrix = None
        numerical_cols = [c for c in columns if c.data_type == DataType.NUMERICAL]
        if len(numerical_cols) >= 2:
            correlation_matrix = self._calculate_correlation(data, numerical_cols)

        return DataProfile(
            row_count=len(data),
            column_count=len(columns),
            columns=columns,
            has_time_series=has_time_series,
            has_categories=has_categories,
            correlation_matrix=correlation_matrix,
        )

    def _infer_data_type(self, values: List[Any], col_name: str) -> DataType:
        """推断数据类型"""
        # 检查列名暗示
        time_keywords = ['time', 'date', 'year', 'month', 'day', 'timestamp']
        if any(keyword in col_name.lower() for keyword in time_keywords):
            return DataType.TEMPORAL

        # 检查样本值
        non_null_values = [v for v in values if v is not None]
        if not non_null_values:
            return DataType.NOMINAL

        # 尝试解析为数值
        numeric_count = 0
        for v in non_null_values[:10]:
            try:
                float(v)
                numeric_count += 1
            except:
                pass

        if numeric_count >= len(non_null_values[:10]) * 0.8:
            return DataType.NUMERICAL

        # 检查是否为日期格式
        date_count = 0
        for v in non_null_values[:5]:
            if isinstance(v, str) and ('-' in v or '/' in v):
                date_count += 1

        if date_count >= 3:
            return DataType.TEMPORAL

        # 检查唯一值数量
        unique_ratio = len(set(non_null_values)) / len(non_null_values) if non_null_values else 0
        if unique_ratio < 0.1:
            return DataType.CATEGORICAL

        return DataType.NOMINAL

    def _calculate_correlation(self, data: List[Dict],
                               numerical_cols: List[DataColumn]) -> List[List[float]]:
        """计算相关性矩阵"""
        n = len(numerical_cols)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    # 简化的相关性计算
                    col_i = numerical_cols[i].name
                    col_j = numerical_cols[j].name

                    values_i = [float(row.get(col_i, 0)) for row in data if row.get(col_i) is not None]
                    values_j = [float(row.get(col_j, 0)) for row in data if row.get(col_j) is not None]

                    if len(values_i) == len(values_j) and len(values_i) > 0:
                        mean_i = sum(values_i) / len(values_i)
                        mean_j = sum(values_j) / len(values_j)

                        numerator = sum((a - mean_i) * (b - mean_j) for a, b in zip(values_i, values_j))
                        denominator = (sum((a - mean_i) ** 2 for a in values_i) *
                                     sum((b - mean_j) ** 2 for b in values_j)) ** 0.5

                        if denominator > 0:
                            matrix[i][j] = numerator / denominator

        return matrix
