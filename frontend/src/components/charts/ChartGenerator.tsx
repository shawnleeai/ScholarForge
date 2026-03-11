/**
 * 图表生成器组件
 * 支持多种图表类型、文件导入、样式自定义和高清导出
 */

import React, { useState, useRef, useCallback, lazy, Suspense } from 'react'
import { Card, Form, Input, Button, Space, message, Divider, Select, ColorPicker, Upload, Dropdown, Tooltip, Row, Col, Slider, Switch } from 'antd'
import {
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  AreaChartOutlined,
  DotChartOutlined,
  RadarChartOutlined,
  HeatMapOutlined,
  UploadOutlined,
  DownloadOutlined,
  SettingOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import type { UploadProps } from 'antd'
import ReactECharts from 'echarts-for-react'

import LineChart from './LineChart'
import BarChart from './BarChart'
import PieChart from './PieChart'
import DataInput from './DataInput'
import styles from './Charts.module.css'

interface ChartDataItem {
  x: string
  y: number
  name?: string
  series?: string
}

interface ChartStyle {
  primaryColor: string
  backgroundColor: string
  fontFamily: string
  fontSize: number
  showLegend: boolean
  showGrid: boolean
  smooth: boolean
}

interface ChartGeneratorProps {
  onInsert?: (config: unknown) => void
}

const defaultStyle: ChartStyle = {
  primaryColor: '#1890ff',
  backgroundColor: '#ffffff',
  fontFamily: 'sans-serif',
  fontSize: 12,
  showLegend: true,
  showGrid: true,
  smooth: true,
}

const ChartGenerator: React.FC<ChartGeneratorProps> = ({ onInsert }) => {
  const [chartType, setChartType] = useState('bar')
  const [data, setData] = useState<ChartDataItem[]>([])
  const [title, setTitle] = useState('')
  const [style, setStyle] = useState<ChartStyle>(defaultStyle)
  const [styleVisible, setStyleVisible] = useState(false)
  const chartRef = useRef<HTMLDivElement>(null)

  const handleDataChange = (newData: ChartDataItem[]) => {
    setData(newData)
  }

  const handleInsert = () => {
    if (onInsert) {
      onInsert({
        type: chartType,
        title,
        data,
        style,
      })
      message.success('图表已插入')
    }
  }

  // 文件导入处理
  const uploadProps: UploadProps = {
    accept: '.csv,.xlsx,.xls,.json',
    showUploadList: false,
    beforeUpload: (file) => {
      const extension = file.name.split('.').pop()?.toLowerCase()

      if (extension === 'csv') {
        parseCSV(file)
      } else if (extension === 'json') {
        parseJSON(file)
      } else if (['xlsx', 'xls'].includes(extension || '')) {
        message.info('Excel 文件需要 xlsx 库支持，请使用 CSV 或 JSON 格式')
      } else {
        message.error('不支持的文件格式')
      }

      return false
    },
  }

  const parseCSV = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string
        const lines = text.split('\n').filter(line => line.trim())

        // 检测是否有表头
        const firstLine = lines[0].split(',')
        const hasHeader = isNaN(parseFloat(firstLine[1]?.trim()))

        const startIndex = hasHeader ? 1 : 0
        const parsedData: ChartDataItem[] = []

        for (let i = startIndex; i < lines.length; i++) {
          const parts = lines[i].split(',')
          if (parts.length >= 2) {
            parsedData.push({
              x: parts[0]?.trim() || '',
              y: parseFloat(parts[1]) || 0,
              name: parts[2]?.trim(),
              series: parts[3]?.trim(),
            })
          }
        }

        setData(parsedData)
        message.success(`已导入 ${parsedData.length} 条数据`)
      } catch {
        message.error('CSV 解析失败')
      }
    }
    reader.readAsText(file)
  }

  const parseJSON = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target?.result as string)
        if (Array.isArray(json)) {
          setData(json)
          message.success(`已导入 ${json.length} 条数据`)
        } else {
          message.error('JSON 格式应为数组')
        }
      } catch {
        message.error('JSON 解析失败')
      }
    }
    reader.readAsText(file)
  }

  // 导出图片
  const handleExportImage = useCallback(() => {
    const chartElement = chartRef.current?.querySelector('canvas')
    if (!chartElement) {
      message.error('没有可导出的图表')
      return
    }

    const canvas = chartElement as HTMLCanvasElement
    const link = document.createElement('a')
    link.download = `${title || 'chart'}_${Date.now()}.png`
    link.href = canvas.toDataURL('image/png', 1.0)
    link.click()
    message.success('图片已导出')
  }, [title])

  // 导出配置
  const handleExportConfig = () => {
    const config = { type: chartType, title, data, style }
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.download = `${title || 'chart'}_config.json`
    link.href = url
    link.click()
    URL.revokeObjectURL(url)
    message.success('配置已导出')
  }

  const chartTypes = [
    { key: 'bar', icon: <BarChartOutlined />, label: '柱状图' },
    { key: 'line', icon: <LineChartOutlined />, label: '折线图' },
    { key: 'pie', icon: <PieChartOutlined />, label: '饼图' },
    { key: 'area', icon: <AreaChartOutlined />, label: '面积图' },
    { key: 'scatter', icon: <DotChartOutlined />, label: '散点图' },
    { key: 'radar', icon: <RadarChartOutlined />, label: '雷达图' },
  ]

  const renderChart = () => {
    if (data.length === 0) {
      return (
        <div className={styles.empty}>
          <div className={styles.emptyText}>
            请先输入或导入数据
          </div>
        </div>
      )
    }

    const commonProps = {
      data,
      title,
      config: {
        color: style.primaryColor,
        smooth: style.smooth,
        area: chartType === 'area',
        showLegend: style.showLegend,
        showGrid: style.showGrid,
        fontFamily: style.fontFamily,
        fontSize: style.fontSize,
      },
    }

    switch (chartType) {
      case 'bar':
        return <BarChart {...commonProps} />
      case 'line':
      case 'area':
        return <LineChart {...commonProps} />
      case 'pie':
        return <PieChart {...commonProps} />
      case 'scatter':
        return <ScatterChart {...commonProps} />
      case 'radar':
        return <RadarChart {...commonProps} />
      default:
        return <BarChart {...commonProps} />
    }
  }

  const exportMenuItems = [
    { key: 'png', label: 'PNG 图片', onClick: handleExportImage },
    { key: 'config', label: '配置文件 (JSON)', onClick: handleExportConfig },
  ]

  return (
    <div className={styles.generator}>
      <Card
        title={
          <Space>
            <span>图表生成器</span>
            <Tooltip title="样式设置">
              <Button
                type="text"
                icon={<SettingOutlined />}
                onClick={() => setStyleVisible(!styleVisible)}
                className={styleVisible ? styles.activeButton : ''}
              />
            </Tooltip>
          </Space>
        }
        className={styles.card}
        extra={
          <Space>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>导入数据</Button>
            </Upload>
          </Space>
        }
      >
        <div className={styles.toolbar}>
          <Space wrap>
            {chartTypes.map((t) => (
              <Button
                key={t.key}
                type={chartType === t.key ? 'primary' : 'default'}
                icon={t.icon}
                onClick={() => setChartType(t.key)}
              >
                {t.label}
              </Button>
            ))}
          </Space>
        </div>

        <Divider />

        {/* 样式设置面板 */}
        {styleVisible && (
          <Card size="small" className={styles.stylePanel}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Form.Item label="主色调">
                  <ColorPicker
                    value={style.primaryColor}
                    onChange={(color) => setStyle({ ...style, primaryColor: color.toHexString() })}
                    showText
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="背景色">
                  <ColorPicker
                    value={style.backgroundColor}
                    onChange={(color) => setStyle({ ...style, backgroundColor: color.toHexString() })}
                    showText
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="字体">
                  <Select
                    value={style.fontFamily}
                    onChange={(v) => setStyle({ ...style, fontFamily: v })}
                    options={[
                      { value: 'sans-serif', label: '无衬线' },
                      { value: 'serif', label: '衬线' },
                      { value: 'monospace', label: '等宽' },
                    ]}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label={`字号: ${style.fontSize}px`}>
                  <Slider
                    min={10}
                    max={20}
                    value={style.fontSize}
                    onChange={(v) => setStyle({ ...style, fontSize: v })}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="显示图例">
                  <Switch
                    checked={style.showLegend}
                    onChange={(v) => setStyle({ ...style, showLegend: v })}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="显示网格">
                  <Switch
                    checked={style.showGrid}
                    onChange={(v) => setStyle({ ...style, showGrid: v })}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="平滑曲线">
                  <Switch
                    checked={style.smooth}
                    onChange={(v) => setStyle({ ...style, smooth: v })}
                  />
                </Form.Item>
              </Col>
            </Row>
            <Button
              icon={<SyncOutlined />}
              onClick={() => setStyle(defaultStyle)}
              size="small"
            >
              重置样式
            </Button>
          </Card>
        )}

        <div className={styles.content}>
          <div className={styles.left}>
            <Form layout="vertical">
              <Form.Item label="图表标题">
                <Input
                  placeholder="输入图表标题"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </Form.Item>

              <Form.Item label="数据输入">
                <DataInput onChange={handleDataChange} />
              </Form.Item>
            </Form>
          </div>

          <div className={styles.right}>
            <div className={styles.preview} ref={chartRef}>
              {renderChart()}
            </div>

            <div className={styles.actions}>
              <Button type="primary" onClick={handleInsert} disabled={!onInsert}>
                插入文档
              </Button>
              <Dropdown menu={{ items: exportMenuItems }}>
                <Button icon={<DownloadOutlined />}>导出</Button>
              </Dropdown>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

// 散点图组件
const ScatterChart: React.FC<{ data: ChartDataItem[]; title?: string; config?: Record<string, unknown> }> = ({
  data,
  title,
  config = {},
}) => {
  const option = {
    title: { text: title, left: 'center' },
    tooltip: { trigger: 'item' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value' },
    yAxis: { type: 'value' },
    series: [{
      type: 'scatter',
      data: data.map((d, i) => [i, d.y]),
      symbolSize: 10,
      itemStyle: { color: (config as { color?: string }).color || '#1890ff' },
    }],
  }

  return <ReactECharts option={option} style={{ height: 300 }} notMerge lazyUpdate />
}

// 雷达图组件
const RadarChart: React.FC<{ data: ChartDataItem[]; title?: string; config?: Record<string, unknown> }> = ({
  data,
  title,
  config = {},
}) => {
  const maxValue = Math.max(...data.map(d => d.y)) * 1.2

  const option = {
    title: { text: title, left: 'center' },
    tooltip: {},
    radar: {
      indicator: data.map(d => ({ name: d.x, max: maxValue })),
    },
    series: [{
      type: 'radar',
      data: [{
        value: data.map(d => d.y),
        name: (config as { seriesName?: string }).seriesName || '数值',
        areaStyle: { opacity: 0.3 },
        lineStyle: { color: (config as { color?: string }).color || '#1890ff' },
        itemStyle: { color: (config as { color?: string }).color || '#1890ff' },
      }],
    }],
  }

  return <ReactECharts option={option} style={{ height: 300 }} notMerge lazyUpdate />
}

export default ChartGenerator
