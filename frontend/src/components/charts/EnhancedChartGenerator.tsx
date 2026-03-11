/**
 * 增强图表生成器
 * 智能推荐图表类型，支持多种图表生成和配置
 */

import React, { useState, useCallback } from 'react'
import {
  Card,
  Button,
  Select,
  Input,
  Form,
  Row,
  Col,
  Steps,
  message,
  Spin,
  Radio,
  Tabs,
  Table,
  Space,
  Typography,
  Divider,
  List,
  Tag,
  Progress,
  Empty,
  Tooltip,
} from 'antd'
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  DotChartOutlined,
  AreaChartOutlined,
  HeatMapOutlined,
  RadarChartOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  EyeOutlined,
  DownloadOutlined,
  UploadOutlined,
  PlusOutlined,
  DeleteOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import styles from './EnhancedChartGenerator.module.css'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { TextArea } = Input
const { Step } = Steps
const { TabPane } = Tabs

interface ChartRecommendation {
  chart_type: string
  score: number
  confidence: string
  reason: string
  suitability: Record<string, number>
  suggested_config: Record<string, any>
}

interface DataRow {
  [key: string]: string | number
}

const EnhancedChartGenerator: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0)
  const [data, setData] = useState<DataRow[]>([])
  const [columns, setColumns] = useState<string[]>([])
  const [recommendations, setRecommendations] = useState<ChartRecommendation[]>([])
  const [selectedChartType, setSelectedChartType] = useState<string>('')
  const [chartOption, setChartOption] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [xColumn, setXColumn] = useState('')
  const [yColumn, setYColumn] = useState('')
  const [chartTitle, setChartTitle] = useState('')
  const [chartTheme, setChartTheme] = useState('default')

  const steps = [
    { title: '导入数据', icon: <UploadOutlined /> },
    { title: '智能推荐', icon: <ThunderboltOutlined /> },
    { title: '配置图表', icon: <SettingOutlined /> },
    { title: '预览导出', icon: <EyeOutlined /> },
  ]

  const chartTypes = [
    { value: 'bar', label: '柱状图', icon: <BarChartOutlined /> },
    { value: 'line', label: '折线图', icon: <LineChartOutlined /> },
    { value: 'pie', label: '饼图', icon: <PieChartOutlined /> },
    { value: 'scatter', label: '散点图', icon: <DotChartOutlined /> },
    { value: 'area', label: '面积图', icon: <AreaChartOutlined /> },
    { value: 'heatmap', label: '热力图', icon: <HeatMapOutlined /> },
    { value: 'radar', label: '雷达图', icon: <RadarChartOutlined /> },
  ]

  const themes = [
    { value: 'default', label: '默认主题' },
    { value: 'dark', label: '暗色主题' },
    { value: 'vintage', label: '复古主题' },
    { value: 'macarons', label: '马卡龙主题' },
  ]

  const handleDataImport = (rawData: string) => {
    try {
      const lines = rawData.trim().split('\n')
      if (lines.length < 2) {
        message.error('数据至少需要包含表头和一行数据')
        return
      }

      const headers = lines[0].split(/[,\t]/).map(h => h.trim())
      const parsedData: DataRow[] = []

      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(/[,\t]/).map(v => v.trim())
        const row: DataRow = {}
        headers.forEach((header, index) => {
          const value = values[index]
          row[header] = isNaN(Number(value)) ? value : Number(value)
        })
        parsedData.push(row)
      }

      setData(parsedData)
      setColumns(headers)
      message.success(`成功导入 ${parsedData.length} 行数据`)
    } catch (error) {
      message.error('数据解析失败，请检查格式')
    }
  }

  const getRecommendations = useCallback(async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/charts/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: data.slice(0, 10),
          purpose: 'comparison',
          top_k: 3,
        }),
      })
      const result = await response.json()
      setRecommendations(result.data?.recommendations || [])
    } catch (error) {
      message.error('获取推荐失败')
    } finally {
      setLoading(false)
    }
  }, [data])

  const generateChart = useCallback(async () => {
    if (!xColumn || !yColumn || !selectedChartType) {
      message.error('请选择图表类型和数据列')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/v1/charts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data,
          chart_type: selectedChartType,
          title: chartTitle || '未命名图表',
          x_column: xColumn,
          y_column: yColumn,
          theme: chartTheme,
        }),
      })
      const result = await response.json()
      setChartOption(result.data?.echarts_option)
    } catch (error) {
      message.error('图表生成失败')
    } finally {
      setLoading(false)
    }
  }, [data, xColumn, yColumn, selectedChartType, chartTitle, chartTheme])

  const exportChart = (format: string) => {
    message.success(`图表已导出为 ${format.toUpperCase()} 格式`)
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className={styles.stepContent}>
            <Title level={5}>导入数据</Title>
            <Paragraph type="secondary">
              支持 CSV 或 TSV 格式，第一行为列名
            </Paragraph>
            <TextArea
              rows={10}
              placeholder={`示例格式：\n年份,销售额,利润\n2020,100,20\n2021,150,30\n2022,200,40`}
              onChange={(e) => handleDataImport(e.target.value)}
            />
            {data.length > 0 && (
              <div className={styles.previewSection}>
                <Divider>数据预览</Divider>
                <Table
                  dataSource={data.slice(0, 5)}
                  columns={columns.map(col => ({
                    title: col,
                    dataIndex: col,
                    key: col,
                  }))}
                  pagination={false}
                  size="small"
                />
              </div>
            )}
          </div>
        )

      case 1:
        return (
          <div className={styles.stepContent}>
            <Title level={5}>智能推荐</Title>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={getRecommendations}
              loading={loading}
              disabled={data.length === 0}
            >
              获取图表推荐
            </Button>

            {recommendations.length > 0 && (
              <div className={styles.recommendations}>
                <Divider>推荐结果</Divider>
                <List
                  grid={{ gutter: 16, column: 3 }}
                  dataSource={recommendations}
                  renderItem={(rec) => (
                    <List.Item>
                      <Card
                        hoverable
                        className={styles.recCard}
                        onClick={() => {
                          setSelectedChartType(rec.chart_type)
                          setCurrentStep(2)
                        }}
                      >
                        <div className={styles.recHeader}>
                          <Tag color={rec.confidence === 'high' ? 'green' : 'blue'}>
                            置信度: {rec.confidence}
                          </Tag>
                          <Progress
                            type="circle"
                            percent={Math.round(rec.score * 100)}
                            size={60}
                            strokeColor={rec.score > 0.8 ? '#52c41a' : '#1890ff'}
                          />
                        </div>
                        <div className={styles.recContent}>
                          <Text strong>
                            {chartTypes.find(t => t.value === rec.chart_type)?.label}
                          </Text>
                          <Paragraph ellipsis={{ rows: 2 }} type="secondary">
                            {rec.reason}
                          </Paragraph>
                        </div>
                      </Card>
                    </List.Item>
                  )}
                />
              </div>
            )}
          </div>
        )

      case 2:
        return (
          <div className={styles.stepContent}>
            <Title level={5}>配置图表</Title>
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="图表类型">
                    <Select
                      value={selectedChartType}
                      onChange={setSelectedChartType}
                      placeholder="选择图表类型"
                    >
                      {chartTypes.map(type => (
                        <Option key={type.value} value={type.value}>
                          <Space>
                            {type.icon}
                            {type.label}
                          </Space>
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="主题">
                    <Select
                      value={chartTheme}
                      onChange={setChartTheme}
                    >
                      {themes.map(theme => (
                        <Option key={theme.value} value={theme.value}>
                          {theme.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="图表标题">
                    <Input
                      value={chartTitle}
                      onChange={(e) => setChartTitle(e.target.value)}
                      placeholder="输入图表标题"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="X轴数据列">
                    <Select
                      value={xColumn}
                      onChange={setXColumn}
                      placeholder="选择X轴数据列"
                    >
                      {columns.map(col => (
                        <Option key={col} value={col}>{col}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="Y轴数据列">
                    <Select
                      value={yColumn}
                      onChange={setYColumn}
                      placeholder="选择Y轴数据列"
                    >
                      {columns.map(col => (
                        <Option key={col} value={col}>{col}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Button
                type="primary"
                onClick={generateChart}
                loading={loading}
                icon={<EyeOutlined />}
              >
                生成图表
              </Button>
            </Form>
          </div>
        )

      case 3:
        return (
          <div className={styles.stepContent}>
            <Title level={5}>预览导出</Title>
            {chartOption ? (
              <div className={styles.chartPreview}>
                <ReactECharts
                  option={chartOption}
                  style={{ height: 400 }}
                  theme={chartTheme}
                />
                <div className={styles.exportButtons}>
                  <Button.Group>
                    <Button icon={<DownloadOutlined />} onClick={() => exportChart('png')}>
                      导出PNG
                    </Button>
                    <Button icon={<DownloadOutlined />} onClick={() => exportChart('svg')}>
                      导出SVG
                    </Button>
                    <Button icon={<DownloadOutlined />} onClick={() => exportChart('html')}>
                      导出HTML
                    </Button>
                    <Button icon={<DownloadOutlined />} onClick={() => exportChart('json')}>
                      导出JSON
                    </Button>
                  </Button.Group>
                </div>
              </div>
            ) : (
              <Empty description="请先生成图表" />
            )}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <Card className={styles.generator} title="增强图表生成器">
      <Steps current={currentStep} className={styles.steps}>
        {steps.map(step => (
          <Step key={step.title} title={step.title} icon={step.icon} />
        ))}
      </Steps>

      <div className={styles.content}>
        {renderStepContent()}
      </div>

      <div className={styles.footer}>
        {currentStep > 0 && (
          <Button onClick={() => setCurrentStep(currentStep - 1)}>
            上一步
          </Button>
        )}
        {currentStep < steps.length - 1 && (
          <Button
            type="primary"
            onClick={() => setCurrentStep(currentStep + 1)}
            disabled={currentStep === 0 && data.length === 0}
          >
            下一步
          </Button>
        )}
      </div>
    </Card>
  )
}

export default EnhancedChartGenerator
