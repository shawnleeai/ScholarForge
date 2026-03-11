/**
 * 图表格式模板自动生成服务
 * 根据数据类型和论文要求自动生成符合学术规范的图表模板
 */

export type ChartType = 'line' | 'bar' | 'scatter' | 'pie' | 'heatmap' | 'box' | 'violin' | 'histogram'
export type DataType = 'continuous' | 'categorical' | 'time_series' | 'correlation' | 'distribution'
export type ExportFormat = 'png' | 'svg' | 'pdf' | 'eps'

export interface ChartTemplate {
  id: string
  name: string
  description: string
  chartType: ChartType
  dataType: DataType
  recommendedFor: string[]
  style: ChartStyle
  dimensions: ChartDimensions
  font: FontSettings
  colors: ColorScheme
  grid: GridSettings
  axes: AxisSettings
  legend: LegendSettings
}

export interface ChartStyle {
  backgroundColor: string
  plotBackgroundColor: string
  border: boolean
  borderColor?: string
  borderWidth?: number
  roundedCorners: boolean
}

export interface ChartDimensions {
  width: number
  height: number
  dpi: number
  aspectRatio: string
}

export interface FontSettings {
  family: string
  titleSize: number
  axisLabelSize: number
  tickLabelSize: number
  legendSize: number
  annotationSize: number
}

export interface ColorScheme {
  primary: string[]
  secondary?: string[]
  background: string
  text: string
  grid: string
  paletteName: string
}

export interface GridSettings {
  show: boolean
  style: 'solid' | 'dashed' | 'dotted'
  width: number
  color: string
  majorLines: boolean
  minorLines: boolean
}

export interface AxisSettings {
  x: SingleAxisSettings
  y: SingleAxisSettings
}

export interface SingleAxisSettings {
  show: boolean
  label: string
  labelFontSize: number
  tickFontSize: number
  showGrid: boolean
  lineWidth: number
  color: string
  scale: 'linear' | 'log' | 'time'
}

export interface LegendSettings {
  show: boolean
  position: 'top' | 'bottom' | 'left' | 'right' | 'inside'
  orientation: 'horizontal' | 'vertical'
  fontSize: number
  backgroundColor: string
  border: boolean
}

export interface ChartExportOptions {
  format: ExportFormat
  width: number
  height: number
  dpi: number
  transparent?: boolean
  quality?: number
}

// 预定义图表模板
export const PREDEFINED_TEMPLATES: ChartTemplate[] = [
  {
    id: 'line_time_series',
    name: '时间序列线图',
    description: '适用于展示随时间变化的趋势数据',
    chartType: 'line',
    dataType: 'time_series',
    recommendedFor: ['趋势分析', '历史数据', '预测结果'],
    style: {
      backgroundColor: '#ffffff',
      plotBackgroundColor: '#fafafa',
      border: true,
      borderColor: '#e8e8e8',
      borderWidth: 1,
      roundedCorners: false
    },
    dimensions: {
      width: 1200,
      height: 600,
      dpi: 300,
      aspectRatio: '16:9'
    },
    font: {
      family: 'Times New Roman, serif',
      titleSize: 14,
      axisLabelSize: 12,
      tickLabelSize: 10,
      legendSize: 10,
      annotationSize: 9
    },
    colors: {
      primary: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
      background: '#ffffff',
      text: '#333333',
      grid: '#e0e0e0',
      paletteName: '学术蓝'
    },
    grid: {
      show: true,
      style: 'dashed',
      width: 0.5,
      color: '#e0e0e0',
      majorLines: true,
      minorLines: false
    },
    axes: {
      x: {
        show: true,
        label: '时间',
        labelFontSize: 12,
        tickFontSize: 10,
        showGrid: true,
        lineWidth: 1,
        color: '#333333',
        scale: 'time'
      },
      y: {
        show: true,
        label: '数值',
        labelFontSize: 12,
        tickFontSize: 10,
        showGrid: true,
        lineWidth: 1,
        color: '#333333',
        scale: 'linear'
      }
    },
    legend: {
      show: true,
      position: 'bottom',
      orientation: 'horizontal',
      fontSize: 10,
      backgroundColor: 'transparent',
      border: false
    }
  },
  {
    id: 'bar_comparison',
    name: '对比柱状图',
    description: '适用于类别间的数值比较',
    chartType: 'bar',
    dataType: 'categorical',
    recommendedFor: ['分类比较', '组间差异', '排名展示'],
    style: {
      backgroundColor: '#ffffff',
      plotBackgroundColor: '#ffffff',
      border: false,
      roundedCorners: false
    },
    dimensions: {
      width: 800,
      height: 600,
      dpi: 300,
      aspectRatio: '4:3'
    },
    font: {
      family: 'Arial, sans-serif',
      titleSize: 16,
      axisLabelSize: 12,
      tickLabelSize: 11,
      legendSize: 11,
      annotationSize: 9
    },
    colors: {
      primary: ['#4a90a4', '#81c784', '#ffb74d', '#e57373', '#9575cd'],
      background: '#ffffff',
      text: '#333333',
      grid: '#f0f0f0',
      paletteName: '柔和彩'
    },
    grid: {
      show: true,
      style: 'solid',
      width: 0.5,
      color: '#f0f0f0',
      majorLines: true,
      minorLines: false
    },
    axes: {
      x: {
        show: true,
        label: '类别',
        labelFontSize: 12,
        tickFontSize: 11,
        showGrid: false,
        lineWidth: 1,
        color: '#333333',
        scale: 'linear'
      },
      y: {
        show: true,
        label: '数值',
        labelFontSize: 12,
        tickFontSize: 11,
        showGrid: true,
        lineWidth: 1,
        color: '#333333',
        scale: 'linear'
      }
    },
    legend: {
      show: true,
      position: 'top',
      orientation: 'horizontal',
      fontSize: 11,
      backgroundColor: 'transparent',
      border: false
    }
  },
  {
    id: 'scatter_correlation',
    name: '散点相关性图',
    description: '适用于展示两个连续变量之间的关系',
    chartType: 'scatter',
    dataType: 'correlation',
    recommendedFor: ['相关性分析', '回归分析', '分布模式'],
    style: {
      backgroundColor: '#ffffff',
      plotBackgroundColor: '#ffffff',
      border: false,
      roundedCorners: false
    },
    dimensions: {
      width: 700,
      height: 700,
      dpi: 300,
      aspectRatio: '1:1'
    },
    font: {
      family: 'Times New Roman, serif',
      titleSize: 14,
      axisLabelSize: 12,
      tickLabelSize: 10,
      legendSize: 10,
      annotationSize: 9
    },
    colors: {
      primary: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
      background: '#ffffff',
      text: '#333333',
      grid: '#e8e8e8',
      paletteName: '经典学术'
    },
    grid: {
      show: true,
      style: 'dashed',
      width: 0.5,
      color: '#e8e8e8',
      majorLines: true,
      minorLines: true
    },
    axes: {
      x: {
        show: true,
        label: 'X 变量',
        labelFontSize: 12,
        tickFontSize: 10,
        showGrid: true,
        lineWidth: 1,
        color: '#333333',
        scale: 'linear'
      },
      y: {
        show: true,
        label: 'Y 变量',
        labelFontSize: 12,
        tickFontSize: 10,
        showGrid: true,
        lineWidth: 1,
        color: '#333333',
        scale: 'linear'
      }
    },
    legend: {
      show: true,
      position: 'right',
      orientation: 'vertical',
      fontSize: 10,
      backgroundColor: 'rgba(255,255,255,0.9)',
      border: true
    }
  },
  {
    id: 'box_distribution',
    name: '箱线图分布',
    description: '适用于展示数据分布和统计特征',
    chartType: 'box',
    dataType: 'distribution',
    recommendedFor: ['分布比较', '异常值检测', '统计摘要'],
    style: {
      backgroundColor: '#ffffff',
      plotBackgroundColor: '#ffffff',
      border: false,
      roundedCorners: false
    },
    dimensions: {
      width: 900,
      height: 500,
      dpi: 300,
      aspectRatio: '16:9'
    },
    font: {
      family: 'Arial, sans-serif',
      titleSize: 14,
      axisLabelSize: 12,
      tickLabelSize: 10,
      legendSize: 10,
      annotationSize: 9
    },
    colors: {
      primary: ['#5c6bc0', '#26a69a', '#ef5350', '#ffa726'],
      background: '#ffffff',
      text: '#333333',
      grid: '#f0f0f0',
      paletteName: '统计彩'
    },
    grid: {
      show: true,
      style: 'solid',
      width: 0.5,
      color: '#f0f0f0',
      majorLines: true,
      minorLines: false
    },
    axes: {
      x: {
        show: true,
        label: '分组',
        labelFontSize: 12,
        tickFontSize: 10,
        showGrid: false,
        lineWidth: 1,
        color: '#333333',
        scale: 'linear'
      },
      y: {
        show: true,
        label: '数值',
        labelFontSize: 12,
        tickFontSize: 10,
        showGrid: true,
        lineWidth: 1,
        color: '#333333',
        scale: 'linear'
      }
    },
    legend: {
      show: false,
      position: 'bottom',
      orientation: 'horizontal',
      fontSize: 10,
      backgroundColor: 'transparent',
      border: false
    }
  },
  {
    id: 'heatmap_correlation',
    name: '热力相关系数图',
    description: '适用于展示多变量间的相关矩阵',
    chartType: 'heatmap',
    dataType: 'correlation',
    recommendedFor: ['多变量相关', '特征选择', '模式识别'],
    style: {
      backgroundColor: '#ffffff',
      plotBackgroundColor: '#ffffff',
      border: false,
      roundedCorners: false
    },
    dimensions: {
      width: 800,
      height: 800,
      dpi: 300,
      aspectRatio: '1:1'
    },
    font: {
      family: 'Arial, sans-serif',
      titleSize: 14,
      axisLabelSize: 11,
      tickLabelSize: 9,
      legendSize: 10,
      annotationSize: 8
    },
    colors: {
      primary: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#fee090', '#fdae61', '#f46d43', '#d73027'],
      background: '#ffffff',
      text: '#333333',
      grid: '#e0e0e0',
      paletteName: '冷暖渐变'
    },
    grid: {
      show: true,
      style: 'solid',
      width: 0.5,
      color: '#e0e0e0',
      majorLines: true,
      minorLines: false
    },
    axes: {
      x: {
        show: true,
        label: '',
        labelFontSize: 11,
        tickFontSize: 9,
        showGrid: false,
        lineWidth: 1,
        color: '#333333',
        scale: 'linear'
      },
      y: {
        show: true,
        label: '',
        labelFontSize: 11,
        tickFontSize: 9,
        showGrid: false,
        lineWidth: 1,
        color: '#333333',
        scale: 'linear'
      }
    },
    legend: {
      show: true,
      position: 'right',
      orientation: 'vertical',
      fontSize: 10,
      backgroundColor: 'transparent',
      border: false
    }
  }
]

// 学术配色方案
export const ACADEMIC_COLOR_PALETTES = [
  {
    name: '学术蓝',
    colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
  },
  {
    name: '柔和彩',
    colors: ['#4a90a4', '#81c784', '#ffb74d', '#e57373', '#9575cd', '#4dd0e1']
  },
  {
    name: '灰度系',
    colors: ['#333333', '#666666', '#999999', '#cccccc', '#e5e5e5', '#f5f5f5']
  },
  {
    name: '冷暖渐变',
    colors: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#fee090', '#fdae61', '#f46d43', '#d73027']
  }
]

class ChartTemplateService {
  private templates: ChartTemplate[] = [...PREDEFINED_TEMPLATES]

  /**
   * 获取所有模板
   */
  getAllTemplates(): ChartTemplate[] {
    return this.templates
  }

  /**
   * 根据图表类型获取模板
   */
  getTemplatesByType(chartType: ChartType): ChartTemplate[] {
    return this.templates.filter(t => t.chartType === chartType)
  }

  /**
   * 根据数据类型获取推荐模板
   */
  getRecommendedTemplates(dataType: DataType): ChartTemplate[] {
    return this.templates.filter(t => t.dataType === dataType)
  }

  /**
   * 智能推荐模板
   */
  recommendTemplate(
    dataDescription: string,
    dataType?: DataType
  ): ChartTemplate[] {
    // 简单的关键词匹配
    const keywords: Record<string, ChartType[]> = {
      '趋势': ['line'],
      '时间': ['line'],
      '变化': ['line', 'bar'],
      '比较': ['bar'],
      '对比': ['bar'],
      '相关': ['scatter', 'heatmap'],
      '关系': ['scatter'],
      '分布': ['box', 'violin', 'histogram'],
      '比例': ['pie'],
      '占比': ['pie']
    }

    // 匹配关键词
    let matchedTypes: ChartType[] = []
    for (const [keyword, types] of Object.entries(keywords)) {
      if (dataDescription.includes(keyword)) {
        matchedTypes = [...matchedTypes, ...types]
      }
    }

    // 去重
    matchedTypes = [...new Set(matchedTypes)]

    if (matchedTypes.length === 0) {
      matchedTypes = ['bar', 'line', 'scatter'] // 默认推荐
    }

    // 返回匹配的模板
    return this.templates.filter(t =>
      matchedTypes.includes(t.chartType) &&
      (!dataType || t.dataType === dataType)
    )
  }

  /**
   * 自定义模板
   */
  createCustomTemplate(
    baseTemplate: ChartTemplate,
    customizations: Partial<ChartTemplate>
  ): ChartTemplate {
    return {
      ...baseTemplate,
      ...customizations,
      id: `custom_${Date.now()}`,
      name: customizations.name || `${baseTemplate.name} (自定义)`
    }
  }

  /**
   * 导出模板配置
   */
  exportTemplate(template: ChartTemplate, format: 'json' | 'python' | 'r'): string {
    switch (format) {
      case 'json':
        return JSON.stringify(template, null, 2)

      case 'python':
        return this.generatePythonCode(template)

      case 'r':
        return this.generateRCode(template)

      default:
        return JSON.stringify(template)
    }
  }

  /**
   * 生成 Python (matplotlib) 代码
   */
  private generatePythonCode(template: ChartTemplate): string {
    return `
import matplotlib.pyplot as plt
import numpy as np

# 创建图表
fig, ax = plt.subplots(figsize=(${template.dimensions.width / 100}, ${template.dimensions.height / 100}), dpi=${template.dimensions.dpi})

# 设置字体
plt.rcParams['font.family'] = '${template.font.family}'
plt.rcParams['font.size'] = ${template.font.tickLabelSize}

# 设置颜色
colors = ${JSON.stringify(template.colors.primary)}

# 绘制图表 (示例数据)
# ax.plot(x, y, color=colors[0])

# 设置标题
ax.set_title('图表标题', fontsize=${template.font.titleSize})

# 设置轴标签
ax.set_xlabel('${template.axes.x.label}', fontsize=${template.font.axisLabelSize})
ax.set_ylabel('${template.axes.y.label}', fontsize=${template.font.axisLabelSize})

# 设置网格
ax.grid(${template.grid.show}, linestyle='${template.grid.style}', alpha=0.3)

# 设置图例
ax.legend(loc='${template.legend.position}', fontsize=${template.font.legendSize})

# 调整布局
plt.tight_layout()

# 保存
plt.savefig('figure.png', dpi=${template.dimensions.dpi}, bbox_inches='tight')
plt.show()
    `.trim()
  }

  /**
   * 生成 R (ggplot2) 代码
   */
  private generateRCode(template: ChartTemplate): string {
    return `
library(ggplot2)
library(ggthemes)

# 创建图表
ggplot(data, aes(x = x_var, y = y_var)) +
  geom_line(color = "${template.colors.primary[0]}") +
  theme_${template.style.border ? 'bw' : 'minimal'}() +
  labs(
    title = "图表标题",
    x = "${template.axes.x.label}",
    y = "${template.axes.y.label}"
  ) +
  theme(
    text = element_text(family = "${template.font.family}", size = ${template.font.tickLabelSize}),
    plot.title = element_text(size = ${template.font.titleSize}, face = "bold"),
    axis.title = element_text(size = ${template.font.axisLabelSize}),
    legend.position = "${template.legend.position}"
  )

# 保存
ggsave("figure.png", width = ${template.dimensions.width / 100}, height = ${template.dimensions.height / 100}, dpi = ${template.dimensions.dpi})
    `.trim()
  }

  /**
   * 获取导出设置建议
   */
  getExportRecommendations(journalType: 'journal' | 'conference' | 'thesis'): ChartExportOptions {
    const recommendations: Record<string, ChartExportOptions> = {
      journal: {
        format: 'eps',
        width: 1200,
        height: 800,
        dpi: 300,
        transparent: false
      },
      conference: {
        format: 'pdf',
        width: 800,
        height: 600,
        dpi: 300,
        transparent: false
      },
      thesis: {
        format: 'png',
        width: 1600,
        height: 1200,
        dpi: 300,
        transparent: false
      }
    }

    return recommendations[journalType]
  }
}

export const chartTemplateService = new ChartTemplateService()
export default chartTemplateService
