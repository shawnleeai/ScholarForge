/**
 * 数据预览组件
 * 数据集表格预览和可视化
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Tabs,
  Statistic,
  Row,
  Col,
  Select,
  Space,
  Tag,
  Empty,
  Spin,
  Alert,
  Button,
  Tooltip,
} from 'antd'
import {
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  DotChartOutlined,
  TableOutlined,
  InfoCircleOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import styles from './DataPreview.module.css'

const { TabPane } = Tabs
const { Option } = Select

interface DataPreviewProps {
  datasetId: string
  versionId?: string
}

interface ColumnInfo {
  name: string
  data_type: string
  description?: string
  nullable: boolean
  unique: boolean
  stats: {
    min?: number
    max?: number
    mean?: number
    null_count?: number
    unique_count?: number
  }
}

interface PreviewData {
  columns: ColumnInfo[]
  sample_data: Record<string, any>[]
  total_rows: number
  total_columns: number
  memory_usage?: number
}

const DataPreview: React.FC<DataPreviewProps> = ({ datasetId, versionId }) => {
  const [loading, setLoading] = useState(false)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [activeTab, setActiveTab] = useState('table')
  const [selectedChart, setSelectedChart] = useState('histogram')
  const [xColumn, setXColumn] = useState('')
  const [yColumn, setYColumn] = useState('')

  useEffect(() => {
    loadPreviewData()
  }, [datasetId, versionId])

  const loadPreviewData = async () => {
    setLoading(true)
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800))

      const mockData: PreviewData = {
        columns: [
          {
            name: 'area',
            data_type: 'float',
            description: '房屋面积（平方米）',
            nullable: false,
            unique: false,
            stats: { min: 20, max: 500, mean: 120, null_count: 0, unique_count: 450 },
          },
          {
            name: 'bedrooms',
            data_type: 'int',
            description: '卧室数量',
            nullable: false,
            unique: false,
            stats: { min: 1, max: 6, mean: 2.5, null_count: 0, unique_count: 6 },
          },
          {
            name: 'price',
            data_type: 'float',
            description: '房屋价格（万元）',
            nullable: false,
            unique: false,
            stats: { min: 50, max: 2000, mean: 350, null_count: 0, unique_count: 890 },
          },
          {
            name: 'location',
            data_type: 'string',
            description: '位置区域',
            nullable: false,
            unique: false,
            stats: { null_count: 0, unique_count: 15 },
          },
        ],
        sample_data: Array.from({ length: 20 }, (_, i) => ({
          area: 50 + Math.random() * 150,
          bedrooms: 1 + Math.floor(Math.random() * 5),
          price: 100 + Math.random() * 800,
          location: ['市中心', '郊区', '开发区', '老城区'][Math.floor(Math.random() * 4)],
        })),
        total_rows: 1000,
        total_columns: 4,
        memory_usage: 1024 * 1024 * 2,
      }

      setPreviewData(mockData)
      if (mockData.columns.length > 0) {
        setXColumn(mockData.columns[0].name)
      }
    } catch (error) {
      console.error('加载预览数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes?: number) => {
    if (!bytes) return '0 B'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const generateHistogramOption = () => {
    if (!previewData) return {}

    const column = previewData.columns.find(c => c.name === xColumn)
    if (!column || column.data_type === 'string') return {}

    const values = previewData.sample_data.map(row => row[xColumn])
    const min = column.stats.min || Math.min(...values)
    const max = column.stats.max || Math.max(...values)
    const bins = 10
    const binSize = (max - min) / bins

    const histogram = new Array(bins).fill(0)
    values.forEach(v => {
      const bin = Math.min(Math.floor((v - min) / binSize), bins - 1)
      histogram[bin]++
    })

    return {
      title: { text: `${xColumn} 分布直方图` },
      xAxis: {
        type: 'category',
        data: Array.from({ length: bins }, (_, i) =>
          `${(min + i * binSize).toFixed(0)}-${(min + (i + 1) * binSize).toFixed(0)}`
        ),
      },
      yAxis: { type: 'value', name: '频数' },
      series: [{
        data: histogram,
        type: 'bar',
        itemStyle: { color: '#1890ff' },
      }],
      tooltip: { trigger: 'axis' },
    }
  }

  const generateScatterOption = () => {
    if (!previewData || !xColumn || !yColumn) return {}

    const data = previewData.sample_data
      .filter(row => row[xColumn] !== null && row[yColumn] !== null)
      .map(row => [row[xColumn], row[yColumn]])

    return {
      title: { text: `${xColumn} vs ${yColumn} 散点图` },
      xAxis: { type: 'value', name: xColumn, scale: true },
      yAxis: { type: 'value', name: yColumn, scale: true },
      series: [{
        data,
        type: 'scatter',
        symbolSize: 10,
        itemStyle: { color: '#52c41a' },
      }],
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => `${xColumn}: ${params.value[0]}<br/>${yColumn}: ${params.value[1]}`,
      },
    }
  }

  const generateChartOption = () => {
    switch (selectedChart) {
      case 'histogram':
        return generateHistogramOption()
      case 'scatter':
        return generateScatterOption()
      default:
        return {}
    }
  }

  const numericColumns = previewData?.columns.filter(c =>
    ['int', 'float', 'number'].includes(c.data_type)
  ) || []

  return (
    <Card className={styles.previewCard} loading={loading}>
      {previewData && (
        <>
          <div className={styles.previewHeader}>
            <Row gutter={24}>
              <Col span={6}>
                <Statistic title="总行数" value={previewData.total_rows} />
              </Col>
              <Col span={6}>
                <Statistic title="总列数" value={previewData.total_columns} />
              </Col>
              <Col span={6}>
                <Statistic title="内存占用" value={formatBytes(previewData.memory_usage)} />
              </Col>
              <Col span={6}>
                <Statistic title="样本数" value={previewData.sample_data.length} />
              </Col>
            </Row>
          </div>

          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane
              tab={<span><TableOutlined /> 数据预览</span>}
              key="table"
            >
              <Alert
                message="显示前 20 行数据"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Table
                dataSource={previewData.sample_data.map((row, i) => ({ ...row, key: i }))}
                columns={previewData.columns.map(col => ({
                  title: (
                    <Tooltip title={`${col.description || ''} (${col.data_type})`}>
                      <span>{col.name} <InfoCircleOutlined /></span>
                    </Tooltip>
                  ),
                  dataIndex: col.name,
                  key: col.name,
                  sorter: (a: any, b: any) => {
                    if (typeof a[col.name] === 'number') {
                      return a[col.name] - b[col.name]
                    }
                    return String(a[col.name]).localeCompare(String(b[col.name]))
                  },
                }))}
                scroll={{ x: 'max-content' }}
                size="small"
                pagination={false}
              />
            </TabPane>

            <TabPane
              tab={<span><BarChartOutlined /> 数据可视化</span>}
              key="charts"
            >
              <div className={styles.chartControls}>
                <Space>
                  <Select
                    value={selectedChart}
                    onChange={setSelectedChart}
                    style={{ width: 150 }}
                  >
                    <Option value="histogram">直方图</Option>
                    <Option value="scatter">散点图</Option>
                    <Option value="boxplot">箱线图</Option>
                  </Select>

                  <Select
                    value={xColumn}
                    onChange={setXColumn}
                    placeholder="选择 X 轴"
                    style={{ width: 150 }}
                  >
                    {previewData.columns.map(col => (
                      <Option key={col.name} value={col.name}>{col.name}</Option>
                    ))}
                  </Select>

                  {selectedChart === 'scatter' && (
                    <Select
                      value={yColumn}
                      onChange={setYColumn}
                      placeholder="选择 Y 轴"
                      style={{ width: 150 }}
                    >
                      {numericColumns.map(col => (
                        <Option key={col.name} value={col.name}>{col.name}</Option>
                      ))}
                    </Select>
                  )}
                </Space>
              </div>

              <div className={styles.chartContainer}>
                <ReactECharts
                  option={generateChartOption()}
                  style={{ height: 400 }}
                />
              </div>
            </TabPane>

            <TabPane
              tab={<span><InfoCircleOutlined /> 字段统计</span>}
              key="stats"
            >
              <Row gutter={[16, 16]}>
                {previewData.columns.map(col => (
                  <Col span={12} key={col.name}>
                    <Card size="small" title={col.name}>
                      <div className={styles.columnStats}>
                        <Tag color="blue">{col.data_type}</Tag>
                        {col.nullable && <Tag>可空</Tag>}
                        {col.unique && <Tag color="green">唯一</Tag>}

                        {col.stats && (
                          <div className={styles.statsGrid}>
                            {col.stats.min !== undefined && (
                              <div className={styles.statItem}>
                                <span className={styles.statLabel}>最小值</span>
                                <span className={styles.statValue}>{col.stats.min.toFixed(2)}</span>
                              </div>
                            )}
                            {col.stats.max !== undefined && (
                              <div className={styles.statItem}>
                                <span className={styles.statLabel}>最大值</span>
                                <span className={styles.statValue}>{col.stats.max.toFixed(2)}</span>
                              </div>
                            )}
                            {col.stats.mean !== undefined && (
                              <div className={styles.statItem}>
                                <span className={styles.statLabel}>平均值</span>
                                <span className={styles.statValue}>{col.stats.mean.toFixed(2)}</span>
                              </div>
                            )}
                            {col.stats.null_count !== undefined && (
                              <div className={styles.statItem}>
                                <span className={styles.statLabel}>空值数</span>
                                <span className={styles.statValue}>{col.stats.null_count}</span>
                              </div>
                            )}
                            {col.stats.unique_count !== undefined && (
                              <div className={styles.statItem}>
                                <span className={styles.statLabel}>唯一值</span>
                                <span className={styles.statValue}>{col.stats.unique_count}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </TabPane>
          </Tabs>
        </>
      )}
    </Card>
  )
}

export default DataPreview
