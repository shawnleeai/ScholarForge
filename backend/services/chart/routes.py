"""
图表服务 API 路由
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any

from shared.responses import success_response

from .recommendation import ChartRecommendationEngine, ChartType, DataProfile
from .description_generator import ChartDescriptionGenerator
from .generator import ChartGenerator, ChartConfig

router = APIRouter(prefix="/api/v1/charts", tags=["图表生成"])

# 初始化服务
recommendation_engine = ChartRecommendationEngine()
description_generator = ChartDescriptionGenerator()
chart_generator = ChartGenerator()


@router.post("/recommend", summary="推荐图表类型")
async def recommend_chart_type(
    data: List[Dict[str, Any]],
    purpose: Optional[str] = None,
    top_k: int = 3,
):
    """
    根据数据特征推荐最适合的图表类型

    - **data**: 数据样本（至少5行）
    - **purpose**: 图表目的 (comparison/trend/distribution/correlation/proportion)
    - **top_k**: 返回推荐数量
    """
    try:
        # 分析数据特征
        data_profile = recommendation_engine.analyze_data(data)

        # 获取推荐
        recommendations = recommendation_engine.recommend(
            data_profile=data_profile,
            purpose=purpose,
            top_k=top_k,
        )

        return success_response(data={
            "recommendations": [
                {
                    "chart_type": r.chart_type.value,
                    "score": r.score,
                    "confidence": r.confidence,
                    "reason": r.reason,
                    "suitability": r.suitability,
                    "suggested_config": r.suggested_config,
                    "alternatives": [a.value for a in r.alternatives],
                }
                for r in recommendations
            ],
            "data_profile": {
                "row_count": data_profile.row_count,
                "column_count": data_profile.column_count,
                "columns": [
                    {
                        "name": c.name,
                        "data_type": c.data_type.value,
                        "unique_count": c.unique_count,
                    }
                    for c in data_profile.columns
                ],
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@router.post("/generate", summary="生成图表")
async def generate_chart(
    data: List[Dict[str, Any]],
    chart_type: ChartType,
    title: str,
    x_column: Optional[str] = None,
    y_column: Optional[str] = None,
    subtitle: Optional[str] = None,
    theme: str = "default",
    width: int = 800,
    height: int = 600,
):
    """
    生成图表

    - **data**: 图表数据
    - **chart_type**: 图表类型
    - **title**: 图表标题
    - **x_column**: X轴列名
    - **y_column**: Y轴列名
    - **theme**: 主题 (default/warm/cool/nature)
    """
    try:
        config = ChartConfig(
            title=title,
            subtitle=subtitle,
            x_axis_label=x_column,
            y_axis_label=y_column,
            width=width,
            height=height,
            theme=theme,
        )

        chart = chart_generator.generate(
            chart_type=chart_type,
            data=data,
            config=config,
            x_column=x_column,
            y_column=y_column,
        )

        return success_response(data={
            "chart_type": chart.chart_type.value,
            "config": {
                "title": chart.config.title,
                "subtitle": chart.config.subtitle,
                "width": chart.config.width,
                "height": chart.config.height,
            },
            "echarts_option": chart.echarts_option,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图表生成失败: {str(e)}")


@router.post("/describe", summary="生成图表描述")
async def generate_chart_description(
    chart_type: str,
    data: List[Dict[str, Any]],
    x_column: str,
    y_column: str,
    context: Optional[Dict[str, Any]] = None,
):
    """
    为图表生成专业的学术描述

    - **chart_type**: 图表类型
    - **data**: 图表数据
    - **x_column**: X轴列名
    - **y_column**: Y轴列名
    - **context**: 研究背景等上下文信息
    """
    try:
        description = description_generator.generate(
            chart_type=chart_type,
            data=data,
            x_column=x_column,
            y_column=y_column,
            context=context,
        )

        return success_response(data={
            "title": description.title,
            "subtitle": description.subtitle,
            "caption": description.caption,
            "interpretation": description.interpretation,
            "key_insights": description.key_insights,
            "methodology_note": description.methodology_note,
            "limitations": description.limitations,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"描述生成失败: {str(e)}")


@router.post("/describe/check", summary="检查描述质量")
async def check_description_quality(
    caption: str,
):
    """检查图表描述的质量"""
    try:
        result = description_generator.check_caption_quality(caption)
        return success_response(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"质量检查失败: {str(e)}")


@router.post("/describe/improve", summary="改进图表描述")
async def improve_description(
    caption: str,
    improvement_type: str = "clarity",  # clarity/conciseness/impact/academic
):
    """
    改进现有的图表描述

    - **improvement_type**: 改进类型
        - clarity: 提升清晰度
        - conciseness: 精简表达
        - impact: 增强影响力
        - academic: 学术化表达
    """
    try:
        improved = description_generator.improve_caption(caption, improvement_type)
        return success_response(data={
            "original": caption,
            "improved": improved,
            "improvement_type": improvement_type,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"改进失败: {str(e)}")


@router.post("/export", summary="导出图表")
async def export_chart(
    chart_option: Dict[str, Any],
    format: str = "html",  # html/json
    filename: Optional[str] = None,
):
    """
    导出图表到指定格式

    - **chart_option**: ECharts配置
    - **format**: 导出格式 (html/json)
    - **filename**: 文件名
    """
    try:
        from .generator import GeneratedChart, ChartConfig, ChartType

        # 创建临时图表对象
        chart = GeneratedChart(
            chart_type=ChartType.BAR,
            config=ChartConfig(title=chart_option.get("title", {}).get("text", "Chart")),
            data=None,
            echarts_option=chart_option,
        )

        if format == "html":
            content = chart_generator.export_to_format(chart, "html")
            return success_response(data={
                "format": "html",
                "content": content,
                "filename": filename or "chart.html",
            })
        elif format == "json":
            content = chart_generator.export_to_format(chart, "json")
            return success_response(data={
                "format": "json",
                "content": content,
                "filename": filename or "chart.json",
            })
        else:
            raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/types", summary="获取图表类型列表")
async def get_chart_types():
    """获取所有支持的图表类型"""
    types = [
        {
            "value": t.value,
            "label": {
                "bar": "柱状图",
                "line": "折线图",
                "pie": "饼图",
                "scatter": "散点图",
                "area": "面积图",
                "heatmap": "热力图",
                "radar": "雷达图",
                "treemap": "树图",
                "boxplot": "箱线图",
                "histogram": "直方图",
            }.get(t.value, t.value),
            "category": {
                "bar": "基础图表",
                "line": "基础图表",
                "pie": "基础图表",
                "scatter": "基础图表",
                "area": "基础图表",
                "heatmap": "高级图表",
                "radar": "高级图表",
                "treemap": "高级图表",
                "boxplot": "统计图表",
                "histogram": "统计图表",
            }.get(t.value, "其他"),
        }
        for t in ChartType
    ]

    return success_response(data={"types": types})


@router.get("/themes", summary="获取图表主题列表")
async def get_chart_themes():
    """获取可用的图表主题"""
    themes = [
        {"value": "default", "label": "默认", "colors": ["#5470c6", "#91cc75", "#fac858"]},
        {"value": "warm", "label": "暖色", "colors": ["#ff6b6b", "#f9ca24", "#f0932b"]},
        {"value": "cool", "label": "冷色", "colors": ["#4834d4", "#686de0", "#30336b"]},
        {"value": "nature", "label": "自然", "colors": ["#2ecc71", "#27ae60", "#16a085"]},
    ]

    return success_response(data={"themes": themes})
