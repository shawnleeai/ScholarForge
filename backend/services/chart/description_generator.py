"""
图表描述生成服务
使用AI生成专业的图表标题和说明文字
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ChartDescription:
    """图表描述"""
    title: str                          # 图表标题
    subtitle: Optional[str]             # 副标题
    caption: str                        # 图注说明
    interpretation: str                 # 数据解读
    key_insights: List[str]             # 关键发现
    methodology_note: Optional[str]     # 方法说明
    limitations: Optional[str]          # 局限性说明


class ChartDescriptionGenerator:
    """
    图表描述生成器
    基于图表数据生成专业的学术描述
    """

    def __init__(self, llm_service=None):
        self.llm = llm_service
        self._templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, Any]:
        """初始化描述模板"""
        return {
            "bar_comparison": {
                "title": "{category}对比分析",
                "caption": "图X展示了不同{category}在{metric}方面的比较。数据结果显示，{top_category}的{metric}最高，达到{top_value}，而{bottom_category}最低，为{bottom_value}。",
                "interpretation": "从整体分布来看，{category}间存在显著差异，最大值是最小值的{ratio}倍。",
            },
            "line_trend": {
                "title": "{metric}随时间的变化趋势",
                "caption": "图X显示了{metric}在{time_range}期间的变化情况。整体呈现{trend_direction}趋势，{key_point}。",
                "interpretation": "数据表明{metric}在{time_period}期间{change_description}，这可能与{potential_factor}有关。",
            },
            "pie_distribution": {
                "title": "{category}分布比例",
                "caption": "图X展示了{category}的构成情况。其中{largest_category}占比最高，达到{largest_percentage}%，其次是{second_category}（{second_percentage}%）。",
                "interpretation": "{largest_category}在整体中占据主导地位，表明{implication}。",
            },
            "scatter_correlation": {
                "title": "{var_x}与{var_y}的相关性分析",
                "caption": "图X展示了{var_x}与{var_y}的散点分布。两者的相关系数为{correlation}，呈现{correlation_strength}的{correlation_direction}相关关系。",
                "interpretation": "{var_x}与{var_y}之间存在{correlation_strength}的关联，{var_x}的变化可以解释{var_y}变化的{r_squared}的变异。",
            },
        }

    def generate(
        self,
        chart_type: str,
        data: List[Dict[str, Any]],
        x_column: str,
        y_column: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ChartDescription:
        """
        生成图表描述

        Args:
            chart_type: 图表类型
            data: 图表数据
            x_column: X轴列名
            y_column: Y轴列名
            context: 上下文信息

        Returns:
            图表描述
        """
        context = context or {}

        # 分析数据特征
        stats = self._analyze_data(data, y_column)

        # 生成各部分描述
        title = self._generate_title(chart_type, x_column, y_column, context)
        caption = self._generate_caption(chart_type, data, x_column, y_column, stats, context)
        interpretation = self._generate_interpretation(chart_type, stats, context)
        key_insights = self._extract_insights(data, x_column, y_column, stats)

        return ChartDescription(
            title=title,
            subtitle=context.get("subtitle"),
            caption=caption,
            interpretation=interpretation,
            key_insights=key_insights,
            methodology_note=context.get("methodology"),
            limitations=context.get("limitations"),
        )

    def _analyze_data(self, data: List[Dict], value_column: str) -> Dict[str, Any]:
        """分析数据特征"""
        values = [float(row.get(value_column, 0)) for row in data
                 if row.get(value_column) is not None]

        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(values)

        return {
            "count": n,
            "sum": sum(values),
            "mean": sum(values) / n,
            "median": sorted_values[n // 2],
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "std": (sum((x - sum(values) / n) ** 2 for x in values) / n) ** 0.5,
        }

    def _generate_title(self, chart_type: str, x_col: str, y_col: str,
                       context: Dict) -> str:
        """生成标题"""
        # 根据图表类型选择模板
        if chart_type == "bar":
            return f"{y_col}对比分析"
        elif chart_type == "line":
            return f"{y_col}的变化趋势"
        elif chart_type == "pie":
            return f"{x_col}分布情况"
        elif chart_type == "scatter":
            return f"{x_col}与{y_col}的相关性"
        else:
            return f"{y_col}分析"

    def _generate_caption(self, chart_type: str, data: List[Dict],
                         x_col: str, y_col: str, stats: Dict,
                         context: Dict) -> str:
        """生成图注"""
        if chart_type == "bar" and data:
            # 找出最大和最小值
            sorted_data = sorted(data, key=lambda x: float(x.get(y_col, 0)), reverse=True)
            if len(sorted_data) >= 2:
                top = sorted_data[0]
                bottom = sorted_data[-1]
                return (
                    f"图展示了不同{x_col}在{y_col}方面的比较。"
                    f"{top[x_col]}的{y_col}最高（{top[y_col]}），"
                    f"而{bottom[x_col]}最低（{bottom[y_col]}）。"
                )

        elif chart_type == "line" and data:
            first_val = float(data[0].get(y_col, 0))
            last_val = float(data[-1].get(y_col, 0))
            change = ((last_val - first_val) / first_val * 100) if first_val else 0
            trend = "上升" if change > 0 else "下降" if change < 0 else "平稳"
            return (
                f"图显示了{y_col}的变化趋势。"
                f"整体呈现{trend}趋势，变化幅度为{abs(change):.1f}%。"
            )

        elif chart_type == "pie" and data:
            total = sum(float(row.get(y_col, 0)) for row in data)
            if total > 0:
                largest = max(data, key=lambda x: float(x.get(y_col, 0)))
                percentage = float(largest[y_col]) / total * 100
                return (
                    f"图展示了{x_col}的分布情况。"
                    f"其中{largest[x_col]}占比最高，达到{percentage:.1f}%。"
                )

        elif chart_type == "scatter":
            return f"图展示了{x_col}与{y_col}的散点分布及相关关系。"

        return f"图展示了{y_col}的数据分布情况。"

    def _generate_interpretation(self, chart_type: str, stats: Dict,
                                context: Dict) -> str:
        """生成解读"""
        interpretations = []

        if stats.get("mean"):
            interpretations.append(f"平均值为{stats['mean']:.2f}")

        if stats.get("range"):
            interpretations.append(f"范围为{stats['range']:.2f}")

        if stats.get("std"):
            cv = stats["std"] / stats["mean"] if stats["mean"] else 0
            if cv < 0.1:
                interpretations.append("数据较为集中")
            elif cv > 0.3:
                interpretations.append("数据离散程度较大")

        return "；".join(interpretations) + "。" if interpretations else ""

    def _extract_insights(self, data: List[Dict], x_col: str, y_col: str,
                         stats: Dict) -> List[str]:
        """提取关键发现"""
        insights = []

        if not data:
            return insights

        # 最大值和最小值
        sorted_data = sorted(data, key=lambda x: float(x.get(y_col, 0)), reverse=True)
        if len(sorted_data) >= 2:
            top = sorted_data[0]
            insights.append(f"{top[x_col]}达到最高值{top[y_col]}")

            if len(sorted_data) >= 3:
                # 检查是否有异常值
                values = [float(row.get(y_col, 0)) for row in data]
                mean = sum(values) / len(values)
                std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5

                outliers = [row for row in data
                           if abs(float(row.get(y_col, 0)) - mean) > 2 * std]
                if outliers:
                    insights.append(f"发现{len(outliers)}个潜在异常值")

        # 增长/下降趋势
        if len(data) >= 3:
            values = [float(row.get(y_col, 0)) for row in data]
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

            if second_half > first_half * 1.1:
                insights.append("整体呈现上升趋势")
            elif second_half < first_half * 0.9:
                insights.append("整体呈现下降趋势")

        return insights[:3]  # 最多返回3条

    def generate_with_llm(
        self,
        chart_type: str,
        data_summary: str,
        research_context: str,
    ) -> ChartDescription:
        """
        使用LLM生成描述

        Args:
            chart_type: 图表类型
            data_summary: 数据摘要
            research_context: 研究背景

        Returns:
            图表描述
        """
        if not self.llm:
            raise ValueError("LLM service not configured")

        prompt = f"""请为以下学术图表生成专业的描述：

图表类型：{chart_type}
研究背景：{research_context}
数据摘要：{data_summary}

请生成以下内容（以JSON格式返回）：
1. title: 图表标题（简洁明了）
2. subtitle: 副标题（可选）
3. caption: 图注说明（2-3句话，说明图表内容）
4. interpretation: 数据解读（学术角度的分析）
5. key_insights: 关键发现（3-5条要点列表）
6. methodology_note: 方法说明（数据收集或处理方法）
7. limitations: 局限性说明（数据或分析的局限）

要求：
- 使用学术中文
- 客观准确
- 突出研究发现的意义"""

        # 这里应该调用LLM服务
        # 模拟返回
        return ChartDescription(
            title="数据分析结果",
            subtitle=None,
            caption="图表展示了相关数据。",
            interpretation="数据分析表明存在显著差异。",
            key_insights=["发现1", "发现2", "发现3"],
            methodology_note="数据采用标准方法收集。",
            limitations="样本量有限。",
        )

    def improve_caption(
        self,
        current_caption: str,
        improvement_type: str,  # clarity/conciseness/impact/academic
    ) -> str:
        """
        改进现有描述

        Args:
            current_caption: 当前描述
            improvement_type: 改进类型

        Returns:
            改进后的描述
        """
        improvements = {
            "clarity": "请改写以下内容，使其更清晰易懂：",
            "conciseness": "请精简以下内容，去除冗余表达：",
            "impact": "请增强以下内容的表现力，突出关键发现：",
            "academic": "请使用更正式的学术语言改写：",
        }

        prompt = f"""{improvements.get(improvement_type, "请改进以下内容：")}

{current_caption}

要求保持原意，但提升表达质量。"""

        # 这里应该调用LLM服务
        return current_caption  # 模拟返回原内容

    def check_caption_quality(self, caption: str) -> Dict[str, Any]:
        """
        检查描述质量

        Args:
            caption: 图表描述

        Returns:
            质量评估结果
        """
        issues = []
        suggestions = []

        # 长度检查
        if len(caption) < 20:
            issues.append("描述过短")
            suggestions.append("增加更多细节说明")
        elif len(caption) > 200:
            issues.append("描述过长")
            suggestions.append("精简表达")

        # 内容检查
        if "图" not in caption:
            suggestions.append("建议使用'图X'开头")

        if not any(word in caption for word in ["显示", "展示", "表明", "反映"]):
            suggestions.append("建议添加描述性动词")

        # 检查是否包含数值
        has_number = any(c.isdigit() for c in caption)
        if not has_number:
            suggestions.append("建议包含具体数值")

        return {
            "score": max(0, 100 - len(issues) * 20 - len(suggestions) * 10),
            "issues": issues,
            "suggestions": suggestions,
            "is_qualified": len(issues) == 0,
        }
