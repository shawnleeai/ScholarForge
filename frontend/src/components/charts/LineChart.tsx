/**
 * 折线图组件
 */

import React from 'react'
import ReactECharts from 'echarts-for-react'

interface LineChartProps {
  data: Array<{ x: string; y: number; name?: string }>
  title?: string
  config?: any
}

const LineChart: React.FC<LineChartProps> = ({ data, title, config = {} }) => {
  const option = {
    title: {
      text: title,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map((d) => d.x),
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: config.seriesName || '数值',
        type: 'line',
        data: data.map((d) => d.y),
        smooth: config.smooth !== false,
        itemStyle: {
          color: config.color || '#1890ff',
        },
        areaStyle: config.area ? { opacity: 0.3 } : undefined,
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

export default LineChart
