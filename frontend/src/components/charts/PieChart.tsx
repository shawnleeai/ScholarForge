/**
 * 饼图组件
 */

import React from 'react'
import ReactECharts from 'echarts-for-react'

interface PieChartProps {
  data: Array<{ x: string; y: number; name?: string }>
  title?: string
  config?: any
}

const PieChart: React.FC<PieChartProps> = ({ data, title, config = {} }) => {
  const pieData = data.map((d) => ({
    name: d.name || d.x,
    value: d.y,
  }))

  const option = {
    title: {
      text: title,
      left: 'center',
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
    },
    series: [
      {
        name: config.seriesName || '占比',
        type: 'pie',
        radius: config.radius || ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data: pieData,
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

export default PieChart
