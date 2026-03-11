/**
 * 图表格式模板自动生成组件
 * 根据数据类型和论文要求自动生成符合学术规范的图表模板
 */

import React, { useState } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Select,
  Input,
  List,
  Tag,
  Badge,
  Collapse,
  Row,
  Col,
  Empty,
  message,
  Divider,
  Tooltip,
  ColorPicker,
  Slider,
  Switch,
  Alert
} from 'antd'
import {
  LineChartOutlined,
  BarChartOutlined,
  DotChartOutlined,
  PieChartOutlined,
  HeatMapOutlined,
  BoxPlotOutlined,
  DownloadOutlined,
  CopyOutlined,
  CheckCircleOutlined,
  PictureOutlined,
  SettingOutlined,
  FileImageOutlined,
  FilePdfOutlined,
  CodeOutlined
} from '@ant-design/icons'
import {
  chartTemplateService,
  PREDEFINED_TEMPLATES,
  ACADEMIC_COLOR_PALETTES,
  type ChartTemplate,
  type ChartType,
  type DataType
} from '@/services/chartTemplateService'
import styles from './ChartTemplateGenerator.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Panel } = Collapse
const { Option } = Select

const CHART_TYPE_ICONS: Record<ChartType, React.ReactNode> = {
  line: <LineChartOutlined />,
  bar: <BarChartOutlined />,
  scatter: <DotChartOutlined />,
  pie: <PieChartOutlined />,
  heatmap: <HeatMapOutlined />,
  box: <BoxPlotOutlined />,
  violin: <BoxPlotOutlined />,
  histogram: <BarChartOutlined />
}

const ChartTemplateGenerator: React.FC = () => {
  const [dataDescription, setDataDescription] = useState('')
  const [selectedType, setSelectedType] = useState<DataType | 'all'>('all')
  const [recommendations, setRecommendations] = useState<ChartTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<ChartTemplate | null>(null)
  const [exportFormat, setExportFormat] = useState<'json' | 'python' | 'r'>('python')
  const [generatedCode, setGeneratedCode] = useState('')

  // 获取推荐
  const handleRecommend = () => {
    if (!dataDescription.trim()) {
      message.warning('请描述您的数据')
      return
    }

    const type = selectedType === 'all' ? undefined : selectedType
    const recs = chartTemplateService.recommendTemplate(dataDescription, type)
    setRecommendations(recs)

    if (recs.length > 0) {
      message.success(`为您推荐 ${recs.length} 个图表模板`)
    } else {
      message.info('未找到匹配的模板，显示所有可用模板')
      setRecommendations(PREDEFINED_TEMPLATES)
    }
  }

  // 选择模板
  const handleSelectTemplate = (template: ChartTemplate) => {
    setSelectedTemplate(template)
    // 生成代码
    const code = chartTemplateService.exportTemplate(template, exportFormat)
    setGeneratedCode(code)
    message.success(`已选择「${template.name}」`)
  }

  // 复制代码
  const handleCopyCode = () => {
    navigator.clipboard.writeText(generatedCode)
    message.success('代码已复制')
  }

  // 导出模板
  const handleExport = () => {
    if (!selectedTemplate) return

    const blob = new Blob([generatedCode], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chart_template.${exportFormat === 'json' ? 'json' : exportFormat}`
    a.click()
    message.success('模板已导出')
  }

  // 渲染模板卡片
  const renderTemplateCard = (template: ChartTemplate) => {
    const isSelected = selectedTemplate?.id === template.id

    return (
      <Card
        className={`${styles.templateCard} ${isSelected ? styles.selected : ''}`}
        hoverable
        onClick={() => handleSelectTemplate(template)}
        title={
          <Space>
            <span style={{ fontSize: 20 }}>{CHART_TYPE_ICONS[template.chartType]}</span>
            <Text strong>{template.name}</Text>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text type="secondary">{template.description}</Text>

          <div>
            <Text type="secondary" style={{ fontSize: 12 }}>适用场景：</Text>
            <Space wrap size="small">
              {template.recommendedFor.map((use, idx) => (
                <Tag key={idx}>{use}</Tag>
              ))}
            </Space>
          </div>

          <Row gutter={8}>
            <Col span={12}>
              <Text type="secondary" style={{ fontSize: 12 }}>尺寸: {template.dimensions.width}x{template.dimensions.height}</Text>
            </Col>
            <Col span={12}>
              <Text type="secondary" style={{ fontSize: 12 }}>DPI: {template.dimensions.dpi}</Text>
            </Col>
          </Row>

          <div className={styles.colorPreview}>
            {template.colors.primary.map((color, idx) => (
              <span
                key={idx}
                className={styles.colorDot}
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
        </Space>
      </Card>
    )
  }

  return (
    <Card
      className={styles.chartTemplateGenerator}
      title={
        <Space>
          <PictureOutlined />
          <span>图表格式模板生成器</span>
        </Space>
      }
    >
      <Collapse defaultActiveKey={['input']}>
        <Panel header="数据描述" key="input">
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Alert
              message="描述您的数据特征，AI将推荐最适合的图表类型和样式"
              type="info"
              showIcon
            />

            <TextArea
              value={dataDescription}
              onChange={e => setDataDescription(e.target.value)}
              placeholder="例如：我要展示过去5年的销售数据趋势变化..."
              rows={3}
            />

            <Select
              value={selectedType}
              onChange={setSelectedType}
              style={{ width: 200 }}
              placeholder="数据类型（可选）"
            >
              <Option value="all">所有类型</Option>
              <Option value="continuous">连续型数据</Option>
              <Option value="categorical">分类型数据</Option>
              <Option value="time_series">时间序列</Option>
              <Option value="correlation">相关性数据</Option>
              <Option value="distribution">分布数据</Option>
            </Select>

            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={handleRecommend}
              block
            >
              获取推荐模板
            </Button>
          </Space>
        </Panel>

        <Panel header="推荐模板" key="templates">
          {recommendations.length === 0 ? (
            <Empty description="先描述您的数据以获取推荐" />
          ) : (
            <List
              grid={{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 3, xl: 3 }}
              dataSource={recommendations}
              renderItem={template => (
                <List.Item>
                  {renderTemplateCard(template)}
                </List.Item>
              )}
            />
          )}
        </Panel>

        {selectedTemplate && (
          <Panel header="模板详情与导出" key="details">
            <Row gutter={24}>
              <Col xs={24} lg={12}>
                <Card title="模板设置" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>字体设置</Text>
                      <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                        <li><Text type="secondary">字体: {selectedTemplate.font.family}</Text></li>
                        <li><Text type="secondary">标题: {selectedTemplate.font.titleSize}pt</Text></li>
                        <li><Text type="secondary">轴标签: {selectedTemplate.font.axisLabelSize}pt</Text></li>
                        <li><Text type="secondary">刻度: {selectedTemplate.font.tickLabelSize}pt</Text></li>
                      </ul>
                    </div>

                    <Divider style={{ margin: '12px 0' }} />

                    <div>
                      <Text strong>颜色方案</Text>
                      <div className={styles.colorPalette}>
                        {selectedTemplate.colors.primary.map((color, idx) => (
                          <Tooltip key={idx} title={color}>
                            <span
                              className={styles.colorBlock}
                              style={{ backgroundColor: color }}
                            />
                          </Tooltip>
                        ))}
                      </div>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {selectedTemplate.colors.paletteName}
                      </Text>
                    </div>

                    <Divider style={{ margin: '12px 0' }} />

                    <div>
                      <Text strong>导出设置</Text>
                      <Select
                        value={exportFormat}
                        onChange={(val: 'json' | 'python' | 'r') => {
                          setExportFormat(val)
                          const code = chartTemplateService.exportTemplate(selectedTemplate, val)
                          setGeneratedCode(code)
                        }}
                        style={{ width: '100%', marginTop: 8 }}
                      >
                        <Option value="python">
                          <CodeOutlined /> Python (matplotlib)
                        </Option>
                        <Option value="r">
                          <CodeOutlined /> R (ggplot2)
                        </Option>
                        <Option value="json">
                          <FileImageOutlined /> JSON 配置
                        </Option>
                      </Select>
                    </div>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card
                  title="生成代码"
                  extra={
                    <Space>
                      <Button
                        icon={<CopyOutlined />}
                        size="small"
                        onClick={handleCopyCode}
                      >
                        复制
                      </Button>
                      <Button
                        type="primary"
                        icon={<DownloadOutlined />}
                        size="small"
                        onClick={handleExport}
                      >
                        导出
                      </Button>
                    </Space>
                  }
                  size="small"
                >
                  <pre className={styles.codeBlock}>
                    <code>{generatedCode}</code>
                  </pre>
                </Card>
              </Col>
            </Row>

            <Divider />

            <Alert
              message="学术图表最佳实践"
              description={
                <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
                  <li>确保图表标题清晰且自明</li>
                  <li>所有轴标签必须包含单位</li>
                  <li>图例位置应避免遮挡数据</li>
                  <li>导出分辨率不低于300 DPI</li>
                  <li>使用期刊推荐的配色方案</li>
                </ul>
              }
              type="success"
              showIcon
            />
          </Panel>
        )}

        <Panel header="配色方案参考" key="colors">
          <List
            grid={{ gutter: 16, xs: 1, sm: 2 }}
            dataSource={ACADEMIC_COLOR_PALETTES}
            renderItem={palette => (
              <List.Item>
                <Card size="small" title={palette.name}>
                  <div className={styles.colorPaletteLarge}>
                    {palette.colors.map((color, idx) => (
                      <Tooltip key={idx} title={color}>
                        <div
                          className={styles.colorSwatch}
                          style={{ backgroundColor: color }}
                        />
                      </Tooltip>
                    ))}
                  </div>
                </Card>
              </List.Item>
            )}
          />
        </Panel>
      </Collapse>
    </Card>
  )
}

export default ChartTemplateGenerator
