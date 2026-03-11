/**
 * 智能投稿推荐组件
 * 根据论文内容推荐合适的期刊/会议
 */

import React, { useState } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Tag,
  List,
  Input,
  Select,
  Slider,
  Switch,
  Badge,
  Collapse,
  Empty,
  Spin,
  Statistic,
  Row,
  Col,
  Divider,
  message,
  Tooltip,
  Progress
} from 'antd'
import {
  TrophyOutlined,
  FileTextOutlined,
  GlobalOutlined,
  DollarOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  StarOutlined,
  ExportOutlined,
  SearchOutlined,
  BarChartOutlined,
  ArrowRightOutlined,
  LinkOutlined,
  PieChartOutlined
} from '@ant-design/icons'
import {
  journalRecommendationService,
  type SubmissionRecommendation,
  type PaperProfile
} from '@/services/journalRecommendationService'
import styles from './JournalRecommender.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Panel } = Collapse
const { Option } = Select

const JournalRecommender: React.FC = () => {
  const [title, setTitle] = useState('')
  const [abstract, setAbstract] = useState('')
  const [keywords, setKeywords] = useState('')
  const [domain, setDomain] = useState('')
  const [isReview, setIsReview] = useState(false)
  const [hasEmpiricalData, setHasEmpiricalData] = useState(true)
  const [maxAPC, setMaxAPC] = useState<number | undefined>(undefined)
  const [requireOpenAccess, setRequireOpenAccess] = useState(false)
  const [preferredType, setPreferredType] = useState<'journal' | 'conference' | 'all'>('all')
  const [recommendations, setRecommendations] = useState<SubmissionRecommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [strategy, setStrategy] = useState<{
    tier1: SubmissionRecommendation[]
    tier2: SubmissionRecommendation[]
    tier3: SubmissionRecommendation[]
  } | null>(null)

  // 获取推荐
  const handleRecommend = async () => {
    if (!title.trim()) {
      message.warning('请输入论文标题')
      return
    }

    setLoading(true)
    try {
      const paperProfile: PaperProfile = {
        title,
        abstract,
        keywords: keywords.split(/[,，]/).map(k => k.trim()).filter(Boolean),
        references: [],
        domain: domain || 'Computer Science',
        hasEmpiricalData,
        isReview
      }

      const prefs = {
        maxAPC,
        requireOpenAccess,
        preferredType
      }

      const recs = await journalRecommendationService.recommendJournals(paperProfile, prefs)
      setRecommendations(recs)

      // 分析策略
      const strategyResult = journalRecommendationService.analyzeSubmissionStrategy(recs)
      setStrategy(strategyResult)

      message.success(`为您推荐 ${recs.length} 个合适的期刊/会议`)
    } catch (error) {
      message.error('获取推荐失败')
    } finally {
      setLoading(false)
    }
  }

  // 导出计划
  const handleExportPlan = () => {
    if (!strategy) return

    const plan = journalRecommendationService.generateSubmissionPlan(recommendations)
    const blob = new Blob([plan], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `投稿推荐计划_${title.slice(0, 20)}.md`
    a.click()
    message.success('投稿计划已导出')
  }

  // 获取排名颜色
  const getRankingColor = (ranking: string) => {
    const colors: Record<string, string> = {
      Q1: '#ff4d4f',
      Q2: '#faad14',
      Q3: '#52c41a',
      Q4: '#1890ff',
      unranked: '#d9d9d9'
    }
    return colors[ranking] || '#d9d9d9'
  }

  // 渲染推荐卡片
  const renderRecommendationCard = (rec: SubmissionRecommendation) => {
    const { journal } = rec

    return (
      <Card
        className={styles.recommendationCard}
        title={
          <Space>
            <Text strong>{journal.name}</Text>
            <Tag color={getRankingColor(journal.ranking)}>{journal.ranking}</Tag>
            <Tag color={journal.journalType === 'journal' ? 'blue' : 'purple'}>
              {journal.journalType === 'journal' ? '期刊' : '会议'}
            </Tag>
          </Space>
        }
        extra={
          <Tooltip title="匹配度">
            <Progress
              type="circle"
              percent={rec.matchScore}
              width={50}
              strokeColor={rec.suitability === 'high' ? '#52c41a' : rec.suitability === 'medium' ? '#faad14' : '#ff4d4f'}
            />
          </Tooltip>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          {/* 关键指标 */}
          <Row gutter={16} className={styles.metrics}>
            {journal.impactFactor && (
              <Col span={8}>
                <Statistic
                  title="影响因子"
                  value={journal.impactFactor}
                  prefix={<BarChartOutlined />}
                  valueStyle={{ fontSize: 16 }}
                />
              </Col>
            )}
            {journal.acceptanceRate && (
              <Col span={8}>
                <Statistic
                  title="接受率"
                  value={journal.acceptanceRate}
                  suffix="%"
                  valueStyle={{ fontSize: 16, color: journal.acceptanceRate < 20 ? '#ff4d4f' : '#52c41a' }}
                />
              </Col>
            )}
            {journal.timeToFirstDecision && (
              <Col span={8}>
                <Statistic
                  title="初审周期"
                  value={journal.timeToFirstDecision}
                  suffix="天"
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ fontSize: 16 }}
                />
              </Col>
            )}
          </Row>

          {/* 推荐理由 */}
          <div className={styles.reasons}>
            <Text type="secondary">推荐理由：</Text>
            <ul>
              {rec.matchReasons.map((reason, idx) => (
                <li key={idx}><Text>{reason}</Text></li>
              ))}
            </ul>
          </div>

          {/* 预估接受概率 */}
          <div className={styles.acceptanceProb}>
            <Text type="secondary">预估接受概率：</Text>
            <Progress
              percent={rec.estimatedAcceptanceProbability}
              status={rec.estimatedAcceptanceProbability > 50 ? 'success' : 'exception'}
              size="small"
            />
          </div>

          {/* 优劣势 */}
          <Row gutter={16}>
            <Col span={12}>
              <div className={styles.pros}>
                <Text type="success" strong><CheckCircleOutlined /> 优势</Text>
                <ul>
                  {rec.pros.map((pro, idx) => (
                    <li key={idx}><Text style={{ fontSize: 12 }}>{pro}</Text></li>
                  ))}
                </ul>
              </div>
            </Col>
            <Col span={12}>
              <div className={styles.cons}>
                <Text type="warning" strong>⚠️ 劣势</Text>
                <ul>
                  {rec.cons.map((con, idx) => (
                    <li key={idx}><Text style={{ fontSize: 12 }}>{con}</Text></li>
                  ))}
                </ul>
              </div>
            </Col>
          </Row>

          {/* 费用信息 */}
          <div className={styles.feeInfo}>
            <Space>
              {journal.openAccess ? (
                <Tag color="green" icon={<GlobalOutlined />}>开放获取</Tag>
              ) : (
                <Tag>订阅制</Tag>
              )}
              {journal.apc !== undefined && (
                <Tag color={journal.apc === 0 ? 'green' : journal.apc > 5000 ? 'red' : 'orange'}>
                  <DollarOutlined /> {journal.apc === 0 ? '无版面费' : `APC: $${journal.apc}`}
                </Tag>
              )}
            </Space>
          </div>

          {/* 操作按钮 */}
          <div className={styles.actions}>
            <Button
              type="link"
              icon={<LinkOutlined />}
              href={journal.url}
              target="_blank"
            >
              查看期刊
            </Button>
            {journal.submissionUrl && (
              <Button
                type="primary"
                icon={<ArrowRightOutlined />}
                href={journal.submissionUrl}
                target="_blank"
              >
                投稿入口
              </Button>
            )}
          </div>
        </Space>
      </Card>
    )
  }

  // 渲染投稿策略
  const renderSubmissionStrategy = () => {
    if (!strategy) return null

    return (
      <Card title="智能投稿策略" className={styles.strategyCard}>
        <Collapse defaultActiveKey={['tier1']}>
          <Panel
            header={
              <Space>
                <TrophyOutlined style={{ color: '#ffd700' }} />
                <Text strong>Tier 1 - 冲刺期刊</Text>
                <Tag color="red">高难度</Tag>
              </Space>
            }
            key="tier1"
          >
            <Paragraph type="secondary">
              这些期刊影响因子高，但竞争激烈。如果您时间充裕且对自己的研究有信心，可以尝试。
            </Paragraph>
            <List
              dataSource={strategy.tier1}
              renderItem={rec => (
                <List.Item>
                  <Text strong>{rec.journal.name}</Text>
                  <Tag color="blue">匹配度 {rec.matchScore}%</Tag>
                </List.Item>
              )}
            />
          </Panel>

          <Panel
            header={
              <Space>
                <StarOutlined style={{ color: '#1890ff' }} />
                <Text strong>Tier 2 - 目标期刊</Text>
                <Tag color="orange">适中</Tag>
              </Space>
            }
            key="tier2"
          >
            <Paragraph type="secondary">
              这些期刊与您的研究匹配度较高，是主要投稿目标。
            </Paragraph>
            <List
              dataSource={strategy.tier2}
              renderItem={rec => (
                <List.Item>
                  <Text>{rec.journal.name}</Text>
                  <Tag color="blue">匹配度 {rec.matchScore}%</Tag>
                </List.Item>
              )}
            />
          </Panel>

          <Panel
            header={
              <Space>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                <Text strong>Tier 3 - 保底期刊</Text>
                <Tag color="green">较易</Tag>
              </Space>
            }
            key="tier3"
          >
            <Paragraph type="secondary">
              这些期刊接受率较高，可作为保底选择。
            </Paragraph>
            <List
              dataSource={strategy.tier3}
              renderItem={rec => (
                <List.Item>
                  <Text>{rec.journal.name}</Text>
                  <Tag color="blue">匹配度 {rec.matchScore}%</Tag>
                </List.Item>
              )}
            />
          </Panel>
        </Collapse>

        <Divider />

        <Button
          type="primary"
          icon={<ExportOutlined />}
          onClick={handleExportPlan}
          block
        >
          导出投稿计划
        </Button>
      </Card>
    )
  }

  return (
    <Card
      className={styles.journalRecommender}
      title={
        <Space>
          <TrophyOutlined />
          <span>智能投稿推荐</span>
        </Space>
      }
    >
      <Collapse defaultActiveKey={['input']}>
        <Panel header="论文信息" key="input">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Text strong>论文标题</Text>
              <Input
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="输入论文标题..."
                prefix={<FileTextOutlined />}
              />
            </div>

            <div>
              <Text strong>摘要</Text>
              <TextArea
                value={abstract}
                onChange={e => setAbstract(e.target.value)}
                placeholder="粘贴论文摘要..."
                rows={4}
              />
            </div>

            <Row gutter={16}>
              <Col span={12}>
                <div>
                  <Text strong>关键词</Text>
                  <Input
                    value={keywords}
                    onChange={e => setKeywords(e.target.value)}
                    placeholder="关键词1, 关键词2, 关键词3..."
                  />
                </div>
              </Col>
              <Col span={12}>
                <div>
                  <Text strong>研究领域</Text>
                  <Select
                    value={domain}
                    onChange={setDomain}
                    style={{ width: '100%' }}
                    placeholder="选择研究领域"
                  >
                    <Option value="">自动识别</Option>
                    <Option value="Computer Science">计算机科学</Option>
                    <Option value="AI">人工智能</Option>
                    <Option value="Data Science">数据科学</Option>
                    <Option value="Engineering">工程技术</Option>
                  </Select>
                </div>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <div>
                  <Text strong>文章类型</Text>
                  <br />
                  <Space>
                    <Switch
                      checked={isReview}
                      onChange={setIsReview}
                    />
                    <Text>综述文章</Text>
                  </Space>
                </div>
              </Col>
              <Col span={12}>
                <div>
                  <Text strong>数据类型</Text>
                  <br />
                  <Space>
                    <Switch
                      checked={hasEmpiricalData}
                      onChange={setHasEmpiricalData}
                    />
                    <Text>包含实证数据</Text>
                  </Space>
                </div>
              </Col>
            </Row>

            <Divider />

            <Text strong>偏好设置</Text>
            <Row gutter={16}>
              <Col span={12}>
                <div>
                  <Text type="secondary">目标类型</Text>
                  <Select
                    value={preferredType}
                    onChange={setPreferredType}
                    style={{ width: '100%' }}
                  >
                    <Option value="all">全部</Option>
                    <Option value="journal">期刊</Option>
                    <Option value="conference">会议</Option>
                  </Select>
                </div>
              </Col>
              <Col span={12}>
                <div>
                  <Text type="secondary">最高版面费 ($)</Text>
                  <Slider
                    min={0}
                    max={10000}
                    step={500}
                    value={maxAPC}
                    onChange={setMaxAPC}
                    tooltip={{ formatter: val => `$${val}` }}
                  />
                </div>
              </Col>
            </Row>

            <div>
              <Space>
                <Switch
                  checked={requireOpenAccess}
                  onChange={setRequireOpenAccess}
                />
                <Text>仅显示开放获取期刊</Text>
              </Space>
            </div>

            <Button
              type="primary"
              size="large"
              icon={<SearchOutlined />}
              onClick={handleRecommend}
              loading={loading}
              block
            >
              {loading ? 'AI正在分析中...' : '获取投稿推荐'}
            </Button>
          </Space>
        </Panel>

        <Panel header="推荐结果" key="results">
          {loading ? (
            <div className={styles.loadingState}>
              <Spin size="large" />
              <Text type="secondary" style={{ marginTop: 16 }}>
                AI正在分析您的论文特征，匹配合适的期刊...
              </Text>
            </div>
          ) : recommendations.length === 0 ? (
            <Empty description="输入论文信息后点击获取推荐" />
          ) : (
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {renderSubmissionStrategy()}

              <Divider orientation="left">
                <Text strong>详细推荐 ({recommendations.length})</Text>
              </Divider>

              <List
                grid={{ gutter: 16, xs: 1, sm: 1, md: 1, lg: 1, xl: 1 }}
                dataSource={recommendations}
                renderItem={rec => (
                  <List.Item>
                    {renderRecommendationCard(rec)}
                  </List.Item>
                )}
              />
            </Space>
          )}
        </Panel>
      </Collapse>
    </Card>
  )
}

export default JournalRecommender
