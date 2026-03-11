"""
图表生成服务
支持多种图表类型的生成和配置
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json


class ChartType(str, Enum):
    """图表类型"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    HEATMAP = "heatmap"
    RADAR = "radar"
    TREEMAP = "treemap"
    BOXPLOT = "boxplot"
    HISTOGRAM = "histogram"


@dataclass
class ChartConfig:
    """图表配置"""
    title: str
    subtitle: Optional[str] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    width: int = 800
    height: int = 600
    theme: str = "default"
    show_legend: bool = True
    show_tooltip: bool = True
    show_toolbox: bool = True
    animation: bool = True
    colors: Optional[List[str]] = None


@dataclass
class ChartData:
    """图表数据"""
    series: List[Dict[str, Any]]
    categories: Optional[List[str]] = None
    x_data: Optional[List[Any]] = None
    y_data: Optional[List[Any]] = None


@dataclass
class GeneratedChart:
    """生成的图表"""
    chart_type: ChartType
    config: ChartConfig
    data: ChartData
    echarts_option: Dict[str, Any]
    svg_code: Optional[str] = None
    png_data: Optional[bytes] = None


class ChartGenerator:
    """
    图表生成器
    生成各种图表的ECharts配置
    """

    def __init__(self):
        self._color_schemes = {
            "default": ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de", "#3ba272"],
            "warm": ["#ff6b6b", "#f9ca24", "#f0932b", "#eb4d4b", "#6c5ce7", "#a29bfe"],
            "cool": ["#4834d4", "#686de0", "#30336b", "#22a6b3", "#0984e3", "#6c5ce7"],
            "nature": ["#2ecc71", "#27ae60", "#16a085", "#1abc9c", "#3498db", "#9b59b6"],
        }

    def generate(
        self,
        chart_type: ChartType,
        data: List[Dict[str, Any]],
        config: ChartConfig,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
    ) -> GeneratedChart:
        """
        生成图表

        Args:
            chart_type: 图表类型
            data: 原始数据
            config: 图表配置
            x_column: X轴列名
            y_column: Y轴列名

        Returns:
            生成的图表对象
        """
        chart_data = self._prepare_data(data, x_column, y_column)

        if chart_type == ChartType.BAR:
            option = self._generate_bar_option(chart_data, config)
        elif chart_type == ChartType.LINE:
            option = self._generate_line_option(chart_data, config)
        elif chart_type == ChartType.PIE:
            option = self._generate_pie_option(chart_data, config)
        elif chart_type == ChartType.SCATTER:
            option = self._generate_scatter_option(chart_data, config)
        elif chart_type == ChartType.AREA:
            option = self._generate_area_option(chart_data, config)
        elif chart_type == ChartType.HEATMAP:
            option = self._generate_heatmap_option(chart_data, config)
        elif chart_type == ChartType.RADAR:
            option = self._generate_radar_option(chart_data, config)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        return GeneratedChart(
            chart_type=chart_type,
            config=config,
            data=chart_data,
            echarts_option=option,
        )

    def _prepare_data(
        self,
        data: List[Dict[str, Any]],
        x_column: Optional[str],
        y_column: Optional[str],
    ) -> ChartData:
        """准备图表数据"""
        if not data:
            return ChartData(series=[])

        # 提取X轴数据
        if x_column:
            categories = [str(row.get(x_column, "")) for row in data]
        else:
            categories = [str(i) for i in range(len(data))]

        # 提取Y轴数据
        if y_column:
            values = [float(row.get(y_column, 0)) for row in data]
        else:
            # 使用第一个数值列
            values = []
            for row in data:
                for val in row.values():
                    if isinstance(val, (int, float)):
                        values.append(float(val))
                        break
                else:
                    values.append(0)

        series = [{
            "name": y_column or "数值",
            "type": "bar",
            "data": values,
        }]

        return ChartData(
            series=series,
            categories=categories,
        )

    def _generate_bar_option(self, data: ChartData, config: ChartConfig) -> Dict:
        """生成柱状图配置"""
        colors = self._color_schemes.get(config.theme, self._color_schemes["default"])

        return {
            "title": {
                "text": config.title,
                "subtext": config.subtitle,
                "left": "center",
            },
            "tooltip": {
                "trigger": "axis",
                "show": config.show_tooltip,
            },
            "legend": {
                "show": config.show_legend,
                "bottom": 10,
            },
            "toolbox": {
                "show": config.show_toolbox,
                "feature": {
                    "saveAsImage": {"title": "保存"},
                    "dataView": {"title": "数据"},
                    "magicType": {"type": ["line", "bar"], "title": {"line": "折线", "bar": "柱状"}},
                },
            },
            "xAxis": {
                "type": "category",
                "data": data.categories,
                "name": config.x_axis_label,
                "axisLabel": {"rotate": 30 if len(data.categories or []) > 10 else 0},
            },
            "yAxis": {
                "type": "value",
                "name": config.y_axis_label,
            },
            "series": [{
                **series,
                "type": "bar",
                "itemStyle": {"color": colors[i % len(colors)]},
                "label": {"show": True, "position": "top"},
                "barWidth": "60%",
                "animation": config.animation,
            } for i, series in enumerate(data.series)],
            "color": colors,
            "grid": {
                "left": "10%",
                "right": "10%",
                "bottom": "15%",
                "containLabel": True,
            },
        }

    def _generate_line_option(self, data: ChartData, config: ChartConfig) -> Dict:
        """生成折线图配置"""
        colors = self._color_schemes.get(config.theme, self._color_schemes["default"])

        return {
            "title": {
                "text": config.title,
                "subtext": config.subtitle,
                "left": "center",
            },
            "tooltip": {
                "trigger": "axis",
                "show": config.show_tooltip,
            },
            "legend": {
                "show": config.show_legend,
                "bottom": 10,
            },
            "toolbox": {
                "show": config.show_toolbox,
                "feature": {
                    "saveAsImage": {"title": "保存"},
                    "dataZoom": {"title": {"zoom": "缩放", "back": "还原"}},
                },
            },
            "xAxis": {
                "type": "category",
                "data": data.categories,
                "name": config.x_axis_label,
                "boundaryGap": False,
            },
            "yAxis": {
                "type": "value",
                "name": config.y_axis_label,
            },
            "series": [{
                **series,
                "type": "line",
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 8,
                "lineStyle": {"width": 3},
                "itemStyle": {"color": colors[i % len(colors)]},
                "areaStyle": {"opacity": 0.1},
                "animation": config.animation,
            } for i, series in enumerate(data.series)],
            "color": colors,
            "grid": {
                "left": "10%",
                "right": "10%",
                "bottom": "15%",
                "containLabel": True,
            },
        }

    def _generate_pie_option(self, data: ChartData, config: ChartConfig) -> Dict:
        """生成饼图配置"""
        colors = self._color_schemes.get(config.theme, self._color_schemes["default"])

        pie_data = [
            {"name": cat, "value": val}
            for cat, val in zip(data.categories or [], data.series[0]["data"] if data.series else [])
        ]

        return {
            "title": {
                "text": config.title,
                "subtext": config.subtitle,
                "left": "center",
            },
            "tooltip": {
                "trigger": "item",
                "formatter": "{b}: {c} ({d}%)",
                "show": config.show_tooltip,
            },
            "legend": {
                "show": config.show_legend,
                "orient": "vertical",
                "left": "left",
            },
            "toolbox": {
                "show": config.show_toolbox,
                "feature": {
                    "saveAsImage": {"title": "保存"},
                },
            },
            "series": [{
                "name": config.y_axis_label or "数值",
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["50%", "50%"],
                "data": pie_data,
                "itemStyle": {
                    "borderRadius": 8,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {
                    "show": True,
                    "formatter": "{b}\n{c} ({d}%)",
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                    },
                },
                "animation": config.animation,
            }],
            "color": colors,
        }

    def _generate_scatter_option(self, data: ChartData, config: ChartConfig) -> Dict:
        """生成散点图配置"""
        colors = self._color_schemes.get(config.theme, self._color_schemes["default"])

        return {
            "title": {
                "text": config.title,
                "subtext": config.subtitle,
                "left": "center",
            },
            "tooltip": {
                "trigger": "item",
                "show": config.show_tooltip,
            },
            "legend": {
                "show": config.show_legend,
                "bottom": 10,
            },
            "toolbox": {
                "show": config.show_toolbox,
                "feature": {
                    "saveAsImage": {"title": "保存"},
                },
            },
            "xAxis": {
                "type": "value",
                "name": config.x_axis_label,
                "scale": True,
            },
            "yAxis": {
                "type": "value",
                "name": config.y_axis_label,
                "scale": True,
            },
            "series": [{
                "name": series.get("name", "数据"),
                "type": "scatter",
                "symbolSize": 15,
                "data": list(zip(range(len(series["data"])), series["data"])),
                "itemStyle": {"color": colors[i % len(colors)]},
                "animation": config.animation,
            } for i, series in enumerate(data.series)],
            "color": colors,
            "grid": {
                "left": "10%",
                "right": "10%",
                "bottom": "15%",
                "containLabel": True,
            },
        }

    def _generate_area_option(self, data: ChartData, config: ChartConfig) -> Dict:
        """生成面积图配置"""
        option = self._generate_line_option(data, config)
        for series in option.get("series", []):
            series["areaStyle"] = {"opacity": 0.3}
            series["stack"] = "Total"
        return option

    def _generate_heatmap_option(self, data: ChartData, config: ChartConfig) -> Dict:
        """生成热力图配置"""
        colors = self._color_schemes.get(config.theme, self._color_schemes["default"])

        return {
            "title": {
                "text": config.title,
                "subtext": config.subtitle,
                "left": "center",
            },
            "tooltip": {
                "position": "top",
                "show": config.show_tooltip,
            },
            "toolbox": {
                "show": config.show_toolbox,
                "feature": {
                    "saveAsImage": {"title": "保存"},
                },
            },
            "visualMap": {
                "min": 0,
                "max": 100,
                "calculable": True,
                "orient": "horizontal",
                "left": "center",
                "bottom": "5%",
                "inRange": {
                    "color": ["#f0f9e8", "#bae4bc", "#7bccc4", "#43a2ca", "#0868ac"],
                },
            },
            "xAxis": {
                "type": "category",
                "data": data.categories,
                "splitArea": {"show": True},
            },
            "yAxis": {
                "type": "category",
                "data": data.categories,
                "splitArea": {"show": True},
            },
            "series": [{
                "name": config.y_axis_label or "数值",
                "type": "heatmap",
                "data": [[i, j, val] for i, row in enumerate(data.series[0]["data"] if data.series else []) for j, val in enumerate([row])],
                "label": {"show": True},
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                    },
                },
                "animation": config.animation,
            }],
            "grid": {
                "left": "10%",
                "right": "10%",
                "bottom": "20%",
                "containLabel": True,
            },
        }

    def _generate_radar_option(self, data: ChartData, config: ChartConfig) -> Dict:
        """生成雷达图配置"""
        colors = self._color_schemes.get(config.theme, self._color_schemes["default"])

        indicators = [
            {"name": cat, "max": max(series["data"]) * 1.2}
            for cat, series in zip(data.categories or [], data.series)
        ]

        return {
            "title": {
                "text": config.title,
                "subtext": config.subtitle,
                "left": "center",
            },
            "tooltip": {
                "trigger": "item",
                "show": config.show_tooltip,
            },
            "legend": {
                "show": config.show_legend,
                "bottom": 10,
            },
            "toolbox": {
                "show": config.show_toolbox,
                "feature": {
                    "saveAsImage": {"title": "保存"},
                },
            },
            "radar": {
                "indicator": indicators,
                "radius": "65%",
            },
            "series": [{
                "name": config.title,
                "type": "radar",
                "data": [{
                    "value": series["data"],
                    "name": series.get("name", f"系列{i+1}"),
                    "itemStyle": {"color": colors[i % len(colors)]},
                } for i, series in enumerate(data.series)],
                "areaStyle": {"opacity": 0.2},
                "animation": config.animation,
            }],
            "color": colors,
        }

    def export_to_format(
        self,
        chart: GeneratedChart,
        format: str,  # png/svg/pdf/html/json
    ) -> Any:
        """导出图表到指定格式"""
        if format == "json":
            return json.dumps(chart.echarts_option, ensure_ascii=False, indent=2)
        elif format == "html":
            return self._generate_html(chart)
        else:
            # 其他格式需要额外的渲染库支持
            raise NotImplementedError(f"Format {format} not implemented")

    def _generate_html(self, chart: GeneratedChart) -> str:
        """生成包含图表的HTML"""
        option_json = json.dumps(chart.echarts_option, ensure_ascii=False)

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{chart.config.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; }}
        #chart {{ width: {chart.config.width}px; height: {chart.config.height}px; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        var chart = echarts.init(document.getElementById('chart'));
        var option = {option_json};
        chart.setOption(option);
    </script>
</body>
</html>"""
