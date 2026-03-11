/**
 * 引用质量分析面板
 * 分析引用的重要性、相关性和时效性
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Progress,
  Typography,
  Space,
  Tag,
  List,
  Tooltip,
  Badge,
  Alert,
  Tabs,
  Statistic,
  Divider,
  Button,
} from 'antd'
import {
  StarOutlined,
  ClockCircleOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  TrophyOutlined,
  BarChartOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { referenceService } from '../../services/referenceService'
import styles from './CitationQuality.module.css'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

interface CitationQualityData {
  article_id: string
  title: string
  authors: string[]
  year: number
  journal?: string
  quality_metrics: {
    relevance: number
    authority: number
    timeliness: number
    diversity: number
    accessibility: number
  }
  overall_score: number
  issues: string[]
  recommendations: string[]
}

interface CitationQualityProps {
  paperId: string
  citations?: CitationQualityData[]
}

const CitationQuality: React.FC<CitationQualityProps> = ({
  paperId,
  citations: initialCitations,
}) => {
  const [citations, setCitations] = useState<CitationQualityData[]>(initialCitations || [])
  const [loading, setLoading] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<CitationQualityData | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (!initialCitations && paperId) {
      fetchQualityData()
    }
  }, [paperId, initialCitations])

  const fetchQualityData = async () => {
    setLoading(true)
    try {
      const response = await referenceService.getCitationQuality(paperId)
      setCitations(response.citations || [])
    } catch (error) {
      console.error('获取引用质量数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#52c41a'
    if (score >= 60) return '#faad14'
    return '#ff4d4f'
  }

  const getScoreStatus = (score: number) => {
    if (score >= 80) return '优秀'
    if (score >= 60) return '良好'
    return '需改进'
  }

  const calculateAverageMetrics = () => {
    if (citations.length === 0) return null

    const metrics = ['relevance', 'authority', 'timeliness', 'diversity', 'accessibility']
    const result: Record<string, number> = {}

    metrics.forEach(metric => {
      const sum = citations.reduce((acc, c) => acc + (c.quality_metrics as any)[metric], 0)
      result[metric] = sum / citations.length
    })

    return result
  }

  const getQualityDistribution = () => {
    const excellent = citations.filter(c => c.overall_score >= 80).length
    const good = citations.filter(c => c.overall_score >= 60 && c.overall_score < 80).length
    const poor = citations.filter(c => c.overall_score < 60).length

    return { excellent, good, poor }
  }

  const avgMetrics = calculateAverageMetrics()
  const distribution = getQualityDistribution()

  const renderQualityOverview = () => (
    <div className={styles.overviewSection}>
      <Row gutter={[24, 24]}>
        <Col span={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="平均质量得分"
              value={citations.length > 0
                ? Math.round(citations.reduce((acc, c) => acc + c.overall_score, 0) / citations.length)
                : 0
              }
              suffix="/100"
              valueStyle={{
                color: getScoreColor(citations.length > 0
                  ? citations.reduce((acc, c) => acc + c.overall_score, 0) / citations.length
                  : 0
                )
              }}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="引用总数"
              value={citations.length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card className={styles.statCard}>
            <Statistic
              title="高质量引用"
              value={distribution.excellent}
              suffix={`/${citations.length}`}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
      </Row>

      {avgMetrics && (
        <Card title="质量指标分析" className={styles.metricsCard}>
          <Row gutter={[24, 16]}>
            <Col span={12}>
              <div className={styles.metricItem}>
                <Space className={styles.metricLabel}>
                  <LinkOutlined />
                  <Text>相关性</Text>
                  <Tooltip title="引用与论文主题的相关程度">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
                <Progress
                  percent={Math.round(avgMetrics.relevance * 100)}
                  status={avgMetrics.relevance >= 0.8 ? 'success' : 'active'}
                  strokeColor={getScoreColor(avgMetrics.relevance * 100)}
                />
              </div>
            </Col>
            <Col span={12}>
              <div className={styles.metricItem}>
                <Space className={styles.metricLabel}>
                  <TrophyOutlined />
                  <Text>权威性</Text>
                  <Tooltip title="来源期刊的影响力和作者的学术地位">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
                <Progress
                  percent={Math.round(avgMetrics.authority * 100)}
                  status={avgMetrics.authority >= 0.8 ? 'success' : 'active'}
                  strokeColor={getScoreColor(avgMetrics.authority * 100)}
                />
              </div>
            </Col>
            <Col span={12}>
              <div className={styles.metricItem}>
                <Space className={styles.metricLabel}>
                  <ClockCircleOutlined />
                  <Text>时效性</Text>
                  <Tooltip title="引用文献的发表时间，越新越好">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
                <Progress
                  percent={Math.round(avgMetrics.timeliness * 100)}
                  status={avgMetrics.timeliness >= 0.8 ? 'success' : 'active'}
                  strokeColor={getScoreColor(avgMetrics.timeliness * 100)}
                />
              </div>
            </Col>
            <Col span={12}>
              <div className={styles.metricItem}>
                <Space className={styles.metricLabel}>
                  <BarChartOutlined />
                  <Text>多样性</Text>
                  <Tooltip title="引用来源的多样性，避免过度集中">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
                <Progress
                  percent={Math.round(avgMetrics.diversity * 100)}
                  status={avgMetrics.diversity >= 0.8 ? 'success' : 'active'}
                  strokeColor={getScoreColor(avgMetrics.diversity * 100)}
                />
              </div>
            </Col>
            <Col span={12}>
              <div className={styles.metricItem}>
                <Space className={styles.metricLabel}>
                  <CheckCircleOutlined />
                  <Text>可获取性</Text>
                  <Tooltip title="文献的开放获取程度和获取难度">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
                <Progress
                  percent={Math.round(avgMetrics.accessibility * 100)}
                  status={avgMetrics.accessibility >= 0.8 ? 'success' : 'active'}
                  strokeColor={getScoreColor(avgMetrics.accessibility * 100)}
                />
              </div>
            </Col>
          </Row>
        </Card>
      )}

      <Card title="质量分布" className={styles.distributionCard}>
        <Row gutter={24}>
          <Col span={8}>
            <div className={styles.distributionItem}>
              <Badge color="#52c41a" text={`优秀 (${distribution.excellent})`} />
              <Progress
                percent={citations.length > 0 ? (distribution.excellent / citations.length) * 100 : 0}
                strokeColor="#52c41a"
                showInfo={false}
              />
            </div>
          </Col>
          <Col span={8}>
            <div className={styles.distributionItem}>
              <Badge color="#faad14" text={`良好 (${distribution.good})`} />
              <Progress
                percent={citations.length > 0 ? (distribution.good / citations.length) * 100 : 0}
                strokeColor="#faad14"
                showInfo={false}
              />
            </div>
          </Col>
          <Col span={8}>
            <div className={styles.distributionItem}>
              <Badge color="#ff4d4f" text={`需改进 (${distribution.poor})`} />
              <Progress
                percent={citations.length > 0 ? (distribution.poor / citations.length) * 100 : 0}
                strokeColor="#ff4d4f"
                showInfo={false}
              />
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  )

  const renderCitationList = () => (
    <List
      dataSource={citations.sort((a, b) => b.overall_score - a.overall_score)}
      renderItem={citation => (
        <List.Item
          className={styles.citationListItem}
          actions={[
            <Button
              type="link"
              onClick={() => setSelectedCitation(citation)}
            >
              查看详情
            </Button>
          ]}
        >
          <List.Item.Meta
            title={
              <Space>
                <Text strong>{citation.title}</Text>
                <Tag color={getScoreColor(citation.overall_score)}>
                  {citation.overall_score}分
                </Tag>
              </Space>
            }
            description={
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text type="secondary">
                  {citation.authors.join(', ')} · {citation.year}
                </Text>
                <Space size="small">
                  {citation.issues.length > 0 && (
                    <Tag icon={<WarningOutlined />} color="warning">
                      {citation.issues.length} 个问题
                    </Tag>
                  )}
                </Space>
              </Space>
            }
          />
        </List.Item>
      )}
    />
  )

  const renderDetailPanel = () => {
    if (!selectedCitation) return null

    return (
      <Card
        title="引用质量详情"
        className={styles.detailPanel}
        extra={
          <Button type="text" onClick={() => setSelectedCitation(null)}>
            返回列表
          </Button>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Title level={5}>{selectedCitation.title}</Title>
            <Text type="secondary">
              {selectedCitation.authors.join(', ')} · {selectedCitation.year}
            </Text>
          </div>

          <Divider />

          <div className={styles.scoreDetail}>
            <Text strong>综合评分</Text>
            <Progress
              type="circle"
              percent={selectedCitation.overall_score}
              status={selectedCitation.overall_score >= 80 ? 'success' : 'active'}
              strokeColor={getScoreColor(selectedCitation.overall_score)}
            />
            <Tag color={getScoreColor(selectedCitation.overall_score)}>
              {getScoreStatus(selectedCitation.overall_score)}
            </Tag>
          </div>

          <Divider />

          <div className={styles.metricsDetail}>
            <Text strong>详细指标</Text>
            <Row gutter={[16, 16]}>
              {Object.entries(selectedCitation.quality_metrics).map(([key, value]) => (
                <Col span={12} key={key}>
                  <div className={styles.metricDetailItem}>
                    <Text type="secondary">
                      {key === 'relevance' && '相关性'}
                      {key === 'authority' && '权威性'}
                      {key === 'timeliness' && '时效性'}
                      {key === 'diversity' && '多样性'}
                      {key === 'accessibility' && '可获取性'}
                    </Text>
                    <Progress
                      percent={Math.round((value as number) * 100)}
                      size="small"
                      strokeColor={getScoreColor((value as number) * 100)}
                    />
                  </div>
                </Col>
              ))}
            </Row>
          </div>

          {selectedCitation.issues.length > 0 && (
            <>
              <Divider />
              <Alert
                message="发现的问题"
                description={
                  <ul>
                    {selectedCitation.issues.map((issue, index) => (
                      <li key={index}>{issue}</li>
                    ))}
                  </ul>
                }
                type="warning"
                showIcon
              />
            </>
          )}

          {selectedCitation.recommendations.length > 0 && (
            <>
              <Divider />
              <Alert
                message="改进建议"
                description={
                  <ul>
                    {selectedCitation.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                }
                type="info"
                showIcon
              />
            </>
          )}
        </Space>
      </Card>
    )
  }

  return (
    <Card className={styles.qualityPanel} title="引用质量分析">
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="概览" key="overview">
          {renderQualityOverview()}
        </TabPane>
        <TabPane tab={`引用列表 (${citations.length})`} key="list">
          {selectedCitation ? renderDetailPanel() : renderCitationList()}
        </TabPane>
      </Tabs>
    </Card>
  )
}

export default CitationQuality
