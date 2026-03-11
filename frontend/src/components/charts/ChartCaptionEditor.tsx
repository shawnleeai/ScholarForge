/**
 * 图表描述编辑器
 * 生成和编辑学术图表标题和描述
 */

import React, { useState, useCallback } from 'react'
import {
  Card,
  Button,
  Input,
  Form,
  Row,
  Col,
  message,
  Spin,
  Tabs,
  Typography,
  Divider,
  Space,
  Tag,
  List,
  Badge,
  Tooltip,
  Alert,
  Slider,
  Select,
  Checkbox,
} from 'antd'
import {
  EditOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  BulbOutlined,
  CopyOutlined,
  ReloadOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import styles from './ChartCaptionEditor.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { TabPane } = Tabs
const { Option } = Select

interface CaptionSuggestion {
  id: string
  caption: string
  description: string
  quality_score: number
  strengths: string[]
  suggestions: string[]
}

interface ChartData {
  chart_type: string
  title: string
  x_label?: string
  y_label?: string
  data_summary: {
    row_count: number
    column_count: number
    numeric_columns: string[]
    categorical_columns: string[]
  }
}

interface ChartCaptionEditorProps {
  chartData?: ChartData
  chartOption?: any
  onCaptionSave?: (caption: string, description: string) => void
}

const ChartCaptionEditor: React.FC<ChartCaptionEditorProps> = ({
  chartData,
  chartOption,
  onCaptionSave,
}) => {
  const [activeTab, setActiveTab] = useState('generate')
  const [loading, setLoading] = useState(false)
  const [caption, setCaption] = useState('')
  const [description, setDescription] = useState('')
  const [suggestions, setSuggestions] = useState<CaptionSuggestion[]>([])
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null)
  const [qualityReport, setQualityReport] = useState<any>(null)
  const [audience, setAudience] = useState('academic')
  const [style, setStyle] = useState('formal')
  const [includeStats, setIncludeStats] = useState(true)
  const [language, setLanguage] = useState('zh')

  const generateCaption = useCallback(async () => {
    if (!chartData) {
      message.error('请先提供图表数据')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/v1/charts/caption/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chart_data: chartData,
          options: {
            audience,
            style,
            include_stats: includeStats,
            language,
          },
        }),
      })
      const result = await response.json()

      if (result.data) {
        setCaption(result.data.caption)
        setDescription(result.data.description)
        setSuggestions(result.data.alternatives || [])
        message.success('描述生成成功')
      }
    } catch (error) {
      message.error('生成失败')
    } finally {
      setLoading(false)
    }
  }, [chartData, audience, style, includeStats, language])

  const checkQuality = useCallback(async () => {
    if (!caption) {
      message.error('请先生成或输入标题')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/v1/charts/caption/quality', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          caption,
          description,
          chart_type: chartData?.chart_type,
        }),
      })
      const result = await response.json()

      if (result.data) {
        setQualityReport(result.data)
        setActiveTab('quality')
        message.success('质量检查完成')
      }
    } catch (error) {
      message.error('检查失败')
    } finally {
      setLoading(false)
    }
  }, [caption, description, chartData])

  const improveCaption = useCallback(async () => {
    if (!caption) return

    setLoading(true)
    try {
      const response = await fetch('/api/v1/charts/caption/improve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          caption,
          description,
          suggestions: qualityReport?.improvements || [],
        }),
      })
      const result = await response.json()

      if (result.data) {
        setCaption(result.data.caption)
        setDescription(result.data.description)
        message.success('优化完成')
      }
    } catch (error) {
      message.error('优化失败')
    } finally {
      setLoading(false)
    }
  }, [caption, description, qualityReport])

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  }

  const exportCaption = () => {
    const content = `图表标题: ${caption}\n\n图表描述:\n${description}`
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'chart-caption.txt'
    a.click()
    URL.revokeObjectURL(url)
    message.success('导出成功')
  }

  const applySuggestion = (suggestion: CaptionSuggestion) => {
    setCaption(suggestion.caption)
    setDescription(suggestion.description)
    setSelectedSuggestion(suggestion.id)
    message.success('已应用建议')
  }

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'green'
    if (score >= 0.6) return 'blue'
    if (score >= 0.4) return 'orange'
    return 'red'
  }

  const getQualityLabel = (score: number) => {
    if (score >= 0.8) return '优秀'
    if (score >= 0.6) return '良好'
    if (score >= 0.4) return '一般'
    return '需改进'
  }

  return (
    <Card className={styles.editor} title="图表描述编辑器">
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={<span><BarChartOutlined /> 图表预览</span>}
          key="preview"
        >
          {chartOption ? (
            <div className={styles.chartPreview}>
              <ReactECharts
                option={chartOption}
                style={{ height: 350 }}
              />
              {chartData && (
                <div className={styles.chartInfo}>
                  <Space>
                    <Tag>类型: {chartData.chart_type}</Tag>
                    <Tag>数据行: {chartData.data_summary.row_count}</Tag>
                    <Tag>数据列: {chartData.data_summary.column_count}</Tag>
                  </Space>
                </div>
              )}
            </div>
          ) : (
            <Alert
              message="暂无图表"
              description="请先创建图表"
              type="info"
              showIcon
            />
          )}
        </TabPane>

        <TabPane
          tab={<span><BulbOutlined /> 生成描述</span>}
          key="generate"
        >
          <div className={styles.generatePanel}>
            <Row gutter={16} className={styles.optionsRow}>
              <Col span={8}>
                <Form.Item label="目标读者">
                  <Select value={audience} onChange={setAudience}>
                    <Option value="academic">学术界</Option>
                    <Option value="general">普通读者</Option>
                    <Option value="expert">领域专家</Option>
                    <Option value="student">学生</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="语言风格">
                  <Select value={style} onChange={setStyle}>
                    <Option value="formal">正式学术</Option>
                    <Option value="concise">简洁明了</Option>
                    <Option value="detailed">详细描述</Option>
                    <Option value="narrative">叙述性</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="语言">
                  <Select value={language} onChange={setLanguage}>
                    <Option value="zh">中文</Option>
                    <Option value="en">English</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Checkbox
              checked={includeStats}
              onChange={(e) => setIncludeStats(e.target.checked)}
              className={styles.statsCheckbox}
            >
              包含关键统计数据
            </Checkbox>

            <Button
              type="primary"
              icon={<BulbOutlined />}
              onClick={generateCaption}
              loading={loading}
              disabled={!chartData}
              className={styles.generateBtn}
            >
              生成智能描述
            </Button>

            {suggestions.length > 0 && (
              <div className={styles.suggestionsSection}>
                <Divider>备选方案</Divider>
                <List
                  dataSource={suggestions}
                  renderItem={(item) => (
                    <List.Item
                      className={`${styles.suggestionItem} ${
                        selectedSuggestion === item.id ? styles.selected : ''
                      }`}
                      onClick={() => applySuggestion(item)}
                      actions={[
                        <Badge
                          key="score"
                          count={`${Math.round(item.quality_score * 100)}分`}
                          style={{
                            backgroundColor:
                              item.quality_score >= 0.8 ? '#52c41a' : '#1890ff',
                          }}
                        />,
                      ]}
                    >
                      <List.Item.Meta
                        title={item.caption}
                        description={item.description}
                      />
                    </List.Item>
                  )}
                />
              </div>
            )}
          </div>
        </TabPane>

        <TabPane
          tab={<span><EditOutlined /> 编辑描述</span>}
          key="edit"
        >
          <div className={styles.editPanel}>
            <Form layout="vertical">
              <Form.Item label="图表标题">
                <Input
                  value={caption}
                  onChange={(e) => setCaption(e.target.value)}
                  placeholder="输入图表标题"
                  maxLength={200}
                  showCount
                />
              </Form.Item>

              <Form.Item label="详细描述">
                <TextArea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="输入图表的详细描述，解释数据含义和关键发现..."
                  rows={8}
                  maxLength={2000}
                  showCount
                />
              </Form.Item>
            </Form>

            <div className={styles.editActions}>
              <Space>
                <Button
                  icon={<CheckCircleOutlined />}
                  onClick={checkQuality}
                  disabled={!caption}
                >
                  质量检查
                </Button>
                <Button
                  icon={<CopyOutlined />}
                  onClick={() => copyToClipboard(`${caption}\n\n${description}`)}
                  disabled={!caption}
                >
                  复制
                </Button>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={exportCaption}
                  disabled={!caption}
                >
                  导出
                </Button>
              </Space>
            </div>

            {onCaptionSave && (
              <Button
                type="primary"
                block
                onClick={() => onCaptionSave(caption, description)}
                disabled={!caption}
                className={styles.saveBtn}
              >
                保存描述
              </Button>
            )}
          </div>
        </TabPane>

        <TabPane
          tab={<span><CheckCircleOutlined /> 质量分析</span>}
          key="quality"
        >
          {qualityReport ? (
            <div className={styles.qualityPanel}>
              <div className={styles.qualityScore}>
                <Title level={3}>
                  <Badge
                    count={getQualityLabel(qualityReport.overall_score)}
                    style={{
                      backgroundColor: getQualityColor(qualityReport.overall_score),
                    }}
                  />
                  <span className={styles.scoreValue}>
                    {Math.round(qualityReport.overall_score * 100)}分
                  </span>
                </Title>
              </div>

              <Divider />

              <div className={styles.qualityDimensions}>
                <Title level={5}>各维度评分</Title>
                {Object.entries(qualityReport.dimensions || {}).map(([key, value]: [string, any]) => (
                  <div key={key} className={styles.dimensionItem}>
                    <div className={styles.dimensionHeader}>
                      <Text strong>{value.label}</Text>
                      <Tag color={getQualityColor(value.score)}>
                        {Math.round(value.score * 100)}分
                      </Tag>
                    </div>
                    <Slider
                      value={value.score * 100}
                      disabled
                      className={styles.dimensionSlider}
                    />
                    <Text type="secondary" className={styles.dimensionComment}>
                      {value.comment}
                    </Text>
                  </div>
                ))}
              </div>

              {qualityReport.improvements?.length > 0 && (
                <>
                  <Divider />
                  <div className={styles.improvements}>
                    <Title level={5}>
                      <WarningOutlined /> 改进建议
                    </Title>
                    <List
                      dataSource={qualityReport.improvements}
                      renderItem={(item: string) => (
                        <List.Item>
                          <Text>{item}</Text>
                        </List.Item>
                      )}
                    />
                    <Button
                      icon={<ReloadOutlined />}
                      onClick={improveCaption}
                      loading={loading}
                      className={styles.improveBtn}
                    >
                      自动优化
                    </Button>
                  </div>
                </>
              )}

              {qualityReport.strengths?.length > 0 && (
                <>
                  <Divider />
                  <div className={styles.strengths}>
                    <Title level={5}>
                      <CheckCircleOutlined /> 优点
                    </Title>
                    <List
                      dataSource={qualityReport.strengths}
                      renderItem={(item: string) => (
                        <List.Item>
                          <Text type="success">{item}</Text>
                        </List.Item>
                      )}
                    />
                  </div>
                </>
              )}
            </div>
          ) : (
            <Alert
              message="暂无质量报告"
              description="请先生成或编辑描述，然后点击质量检查"
              type="info"
              showIcon
            />
          )}
        </TabPane>

        <TabPane
          tab={<span><FileTextOutlined /> 最佳实践</span>}
          key="guidelines"
        >
          <div className={styles.guidelines}>
            <Alert
              message="学术图表描述最佳实践"
              description="良好的图表描述应该清晰、准确、完整"
              type="info"
              showIcon
              className={styles.guidelineAlert}
            />

            <List
              header={<Title level={5}>关键要素检查清单</Title>}
              bordered
              dataSource={[
                { key: 'title', text: '标题简洁明了，概括图表主要内容', important: true },
                { key: 'variables', text: '说明所有变量及其单位', important: true },
                { key: 'trends', text: '描述主要趋势和模式', important: true },
                { key: 'extremes', text: '指出极值、异常值或关键点', important: true },
                { key: 'relationship', text: '解释变量间的关系', important: false },
                { key: 'context', text: '提供必要的背景信息', important: false },
                { key: 'stats', text: '包含关键统计数据（如适用）', important: false },
                { key: 'conclusion', text: '总结图表的主要含义', important: true },
              ]}
              renderItem={(item) => (
                <List.Item>
                  <Space>
                    <CheckCircleOutlined
                      style={{ color: item.important ? '#52c41a' : '#8c8c8c' }}
                    />
                    <Text>{item.text}</Text>
                    {item.important && <Tag color="red">必需</Tag>}
                  </Space>
                </List.Item>
              )}
            />

            <Divider />

            <Title level={5}>示例模板</Title>
            <Card size="small" className={styles.templateCard}>
              <Paragraph>
                <Text strong>柱状图模板：</Text>
                <br />
                图X展示了[时间段/范围]内[主题]的[比较/变化]情况。
                从图中可以看出，[类别A]的[指标]最高，达到[数值][单位]，
                而[类别B]最低，为[数值][单位]。总体而言，[主要趋势描述]。
              </Paragraph>
            </Card>
            <Card size="small" className={styles.templateCard}>
              <Paragraph>
                <Text strong>折线图模板：</Text>
                <br />
                图X显示了[时间段]内[变量]的变化趋势。[变量]从[起始值]
                [增长/下降]至[结束值]，年均[增长/下降]率为[X]%。
                值得注意的是，在[时间点]出现了[峰值/谷值]，
                这可能与[原因]有关。
              </Paragraph>
            </Card>
          </div>
        </TabPane>
      </Tabs>
    </Card>
  )
}

export default ChartCaptionEditor
