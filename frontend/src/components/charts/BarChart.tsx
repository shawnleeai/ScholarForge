/**
 * 柱状图组件
 */

import React from 'react'
import ReactECharts from 'echarts-for-react'

interface BarChartProps {
  data: Array<{ x: string; y: number; name?: string }>
  title?: string
  config?: any
}

const BarChart: React.FC<BarChartProps> = ({ data, title, config = {} }) => {
  const option = {
    title: {
      text: title,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.x),
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: config.seriesName || '数值',
        type: 'bar',
        data: data.map((d) => d.y),
        itemStyle: {
          color: config.color || '#1890ff',
        },
        ...config.series,
      },
    ],
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: 300 }}
      notMerge
      lazyUpdate
    />
  )
}

export default BarChart
