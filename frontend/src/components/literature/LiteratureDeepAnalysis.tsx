/**
 * 文献深度解析助手组件
 * 提供论文的深度分析、摘要生成、关键信息提取等功能
 */

import React, { useState } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Tag,
  Tabs,
  List,
  Spin,
  Alert,
  Empty,
  Progress,
  Collapse,
  Tooltip,
  Divider,
  Badge,
  message,
  Input,
  Select
} from 'antd'
import {
  FileTextOutlined,
  ReadOutlined,
  BarChartOutlined,
  KeyOutlined,
  ExperimentOutlined,
  ExportOutlined,
  ReloadOutlined,
  BookOutlined,
  BulbOutlined,
  WarningOutlined,
  RocketOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DiffOutlined,
  TrendChartOutlined
} from '@ant-design/icons'
import {
  literatureAnalysisService,
  type LiteratureInsight,
  type AnalysisType,
  type AnalysisResult
} from '@/services/literatureAnalysisService'
import styles from './LiteratureDeepAnalysis.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { TabPane } = Tabs
const { Panel } = Collapse
const { Option } = Select

const ANALYSIS_TYPE_CONFIG: Record<AnalysisType, { icon: React.ReactNode; color: string; label: string }> = {
  summary: { icon: <FileTextOutlined />, color: 'blue', label: '智能摘要' },
  key_findings: { icon: <KeyOutlined />, color: 'green', label: '关键发现' },
  methodology: { icon: <ExperimentOutlined />, color: 'purple', label: '方法论' },
  contribution: { icon: <BulbOutlined />, color: 'gold', label: '贡献分析' },
  limitations: { icon: <WarningOutlined />, color: 'orange', label: '局限性' },
  future_work: { icon: <RocketOutlined />, color: 'cyan', label: '未来工作' },
  citation_context: { icon: <LinkOutlined />, color: 'geekblue', label: '引用分析' },
  comparison: { icon: <DiffOutlined />, color: 'magenta', label: '对比分析' }
}

const DIFFICULTY_LABELS: Record<string, { label: string; color: string }> = {
  beginner: { label: '入门级', color: 'green' },
  intermediate: { label: '进阶级', color: 'blue' },
  advanced: { label: '专家级', color: 'red' }
}

interface LiteratureDeepAnalysisProps {
  paperId?: string
  paperTitle?: string
}

const LiteratureDeepAnalysis: React.FC<LiteratureDeepAnalysisProps> = ({
  paperId,
  paperTitle: initialTitle = ''
}) => {
  const [paperTitle, setPaperTitle] = useState(initialTitle)
  const [paperContent, setPaperContent] = useState('')
  const [insight, setInsight] = useState<LiteratureInsight | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedTypes, setSelectedTypes] = useState<AnalysisType[]>([])

  // 开始分析
  const handleAnalyze = async () => {
    if (!paperTitle.trim()) {
      message.warning('请输入论文标题')
      return
    }

    setLoading(true)
    try {
      const result = await literatureAnalysisService.analyzePaper(
        paperId || `paper_${Date.now()}`,
        paperTitle,
        paperContent
      )
      setInsight(result)
      message.success('分析完成！')
    } catch (error) {
      message.error('分析失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 导出报告
  const handleExport = () => {
    if (!insight) return

    const report = literatureAnalysisService.exportAnalysisReport(insight)
    const blob = new Blob([report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `文献解析_${insight.paperTitle.slice(0, 20)}.md`
    a.click()
    message.success('报告已导出')
  }

  // 生成阅读笔记
  const handleGenerateNotes = () => {
    if (!insight) return

    const notes = literatureAnalysisService.generateReadingNotes(insight)
    navigator.clipboard.writeText(notes)
    message.success('阅读笔记已复制到剪贴板')
  }

  // 渲染分析结果卡片
  const renderAnalysisCard = (analysis: AnalysisResult) => {
    const config = ANALYSIS_TYPE_CONFIG[analysis.type]

    return (
      <Card
        key={analysis.type}
        className={styles.analysisCard}
        title={
          <Space>
            <span style={{ color: config.color }}>{config.icon}</span>
            <span>{analysis.title}</span>
            <Tag color={config.color}>{config.label}</Tag>
          </Space>
        }
        extra={
          <Tooltip title="置信度">
            <Progress
              type="circle"
              percent={Math.round(analysis.confidence * 100)}
              width={40}
              strokeColor={analysis.confidence > 0.8 ? '#52c41a' : '#faad14'}
            />
          </Tooltip>
        }
      >
        <Paragraph style={{ whiteSpace: 'pre-line' }}>
          {analysis.content}
        </Paragraph>

        {analysis.highlights && analysis.highlights.length > 0 && (
          <div className={styles.highlights}>
            <Text type="secondary" style={{ fontSize: 12 }}>要点：</Text>
            <Space wrap size="small">
              {analysis.highlights.map((h, i) => (
                <Tag key={i} color="blue" style={{ fontSize: 11 }}>{h}</Tag>
              ))}
            </Space>
          </div>
        )}
      </Card>
    )
  }

  // 渲染输入界面
  const renderInput = () => (
    <div className={styles.inputSection}>
      <Alert
        message="文献深度解析"
        description="AI将自动分析论文的核心内容，提取关键发现、方法论、研究贡献等重要信息，帮助您快速理解文献精髓。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <div>
          <Text strong>论文标题</Text>
          <Input
            value={paperTitle}
            onChange={e => setPaperTitle(e.target.value)}
            placeholder="输入论文标题..."
            size="large"
            prefix={<BookOutlined />}
          />
        </div>

        <div>
          <Text strong>论文内容（可选）</Text>
          <TextArea
            value={paperContent}
            onChange={e => setPaperContent(e.target.value)}
            placeholder="粘贴论文摘要或全文，AI将进行更精准的分析..."
            rows={8}
          />
        </div>

        <Button
          type="primary"
          size="large"
          icon={<ReadOutlined />}
          onClick={handleAnalyze}
          loading={loading}
          block
        >
          {loading ? 'AI正在深度解析中...' : '开始深度解析'}
        </Button>
      </Space>

      {loading && (
        <div className={styles.loadingState}>
          <Spin size="large" />
          <Text type="secondary" style={{ marginTop: 16 }}>
            AI正在分析论文结构、提取关键信息、生成深度洞察...
          </Text>
        </div>
      )}
    </div>
  )

  // 渲染概览
  const renderOverview = () => {
    if (!insight) return null

    const difficulty = DIFFICULTY_LABELS[insight.difficulty]

    return (
      <div className={styles.overview}>
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="相关度"
                value={Math.round(insight.relevanceScore * 100)}
                suffix="%"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="预计阅读"
                value={insight.readingTime}
                suffix="分钟"
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="关键发现"
                value={insight.keyFindings.length}
                prefix={<KeyOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="难度"
                value={difficulty.label}
                valueStyle={{ color: difficulty.color }}
              />
            </Card>
          </Col>
        </Row>

        <div className={styles.actions}>
          <Space>
            <Button icon={<ExportOutlined />} onClick={handleExport}>
              导出报告
            </Button>
            <Button icon={<FileTextOutlined />} onClick={handleGenerateNotes}>
              生成阅读笔记
            </Button>
          </Space>
        </div>
      </div>
    )
  }

  // 渲染关键发现
  const renderKeyFindings = () => {
    if (!insight) return null

    return (
      <List
        dataSource={insight.keyFindings}
        renderItem={(finding, index) => (
          <List.Item>
            <Card style={{ width: '100%' }}>
              <div className={styles.findingHeader}>
                <Badge count={index + 1} style={{ backgroundColor: '#1890ff' }} />
                <Tag color={finding.significance === 'high' ? 'red' : finding.significance === 'medium' ? 'orange' : 'green'}>
                  {finding.significance === 'high' ? '重要' : finding.significance === 'medium' ? '一般' : '次要'}
                </Tag>
              </div>
              <Paragraph strong style={{ marginTop: 8 }}>
                {finding.statement}
              </Paragraph>
              <Paragraph type="secondary" style={{ fontSize: 13 }}>
                <Text type="secondary">证据：</Text>
                {finding.evidence}
              </Paragraph>
            </Card>
          </List.Item>
        )}
      />
    )
  }

  // 渲染方法论分析
  const renderMethodology = () => {
    if (!insight?.methodology) return null

    const { methodology } = insight

    return (
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text type="secondary">研究类型</Text>
            <br />
            <Text strong>{methodology.approach}</Text>
          </div>

          <div>
            <Text type="secondary">研究方法</Text>
            <br />
            <Space wrap>
              {methodology.methods.map((m, i) => (
                <Tag key={i}>{m}</Tag>
              ))}
            </Space>
          </div>

          {methodology.dataset && (
            <div>
              <Text type="secondary">数据集</Text>
              <br />
              <Text>{methodology.dataset}</Text>
            </div>
          )}

          <div>
            <Text type="secondary">评估指标</Text>
            <br />
            <Space wrap>
              {methodology.metrics.map((m, i) => (
                <Tag key={i} color="blue">{m}</Tag>
              ))}
            </Space>
          </div>

          {methodology.tools && (
            <div>
              <Text type="secondary">工具/平台</Text>
              <br />
              <Space wrap>
                {methodology.tools.map((t, i) => (
                  <Tag key={i} color="purple">{t}</Tag>
                ))}
              </Space>
            </div>
          )}

          <div>
            <Text type="secondary">可复现性</Text>
            <br />
            <Tag color={methodology.reproducibility === 'high' ? 'green' : methodology.reproducibility === 'medium' ? 'orange' : 'red'}>
              {methodology.reproducibility === 'high' ? '高' : methodology.reproducibility === 'medium' ? '中' : '低'}
            </Tag>
          </div>
        </Space>
      </Card>
    )
  }

  // 渲染研究空白
  const renderResearchGaps = () => {
    if (!insight?.researchGaps || insight.researchGaps.length === 0) {
      return <Empty description="暂无研究空白分析" />
    }

    return (
      <Collapse>
        {insight.researchGaps.map((gap, index) => (
          <Panel
            key={index}
            header={
              <Space>
                <WarningOutlined style={{ color: '#faad14' }} />
                <span>研究空白 {index + 1}</span>
              </Space>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text type="secondary">描述：</Text>
                <Paragraph>{gap.description}</Paragraph>
              </div>
              <div>
                <Text type="secondary">证据：</Text>
                <Paragraph>{gap.evidence}</Paragraph>
              </div>
              <div>
                <Text type="secondary">研究机会：</Text>
                <Paragraph style={{ color: '#1890ff' }}>{gap.opportunity}</Paragraph>
              </div>
            </Space>
          </Panel>
        ))}
      </Collapse>
    )
  }

  // 渲染分析结果
  const renderResults = () => {
    if (!insight) return null

    return (
      <Tabs activeKey={activeTab} onChange={setActiveTab} className={styles.resultsTabs}>
        <TabPane
          tab={<span><BarChartOutlined />概览</span>}
          key="overview"
        >
          {renderOverview()}
        </TabPane>

        <TabPane
          tab={<span><KeyOutlined />关键发现 ({insight.keyFindings.length})</span>}
          key="findings"
        >
          {renderKeyFindings()}
        </TabPane>

        <TabPane
          tab={<span><FileTextOutlined />详细分析 ({insight.analyses.length})</span>}
          key="analysis"
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            {insight.analyses.map(renderAnalysisCard)}
          </Space>
        </TabPane>

        <TabPane
          tab={<span><ExperimentOutlined />方法论</span>}
          key="methodology"
        >
          {renderMethodology()}
        </TabPane>

        <TabPane
          tab={<span><WarningOutlined />研究空白 ({insight.researchGaps?.length || 0})</span>}
          key="gaps"
        >
          {renderResearchGaps()}
        </TabPane>
      </Tabs>
    )
  }

  return (
    <Card
      className={styles.literatureDeepAnalysis}
      title={
        <Space>
          <ReadOutlined />
          <span>文献深度解析助手</span>
          {insight && (
            <Tag color="green">已分析</Tag>
          )}
        </Space>
      }
      extra={
        insight && (
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              setInsight(null)
              setActiveTab('overview')
            }}
            size="small"
          >
            重新分析
          </Button>
        )
      }
    >
      {!insight ? renderInput() : renderResults()}
    </Card>
  )
}

export default LiteratureDeepAnalysis
