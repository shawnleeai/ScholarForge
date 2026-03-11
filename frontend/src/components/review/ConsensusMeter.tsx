/**
 * 共识度仪表盘组件
 * 可视化展示学术界对特定问题的共识程度
 */

import React from 'react'
import {
  Card,
  Progress,
  Statistic,
  Row,
  Col,
  List,
  Tag,
  Typography,
  Space,
  Divider,
  Alert,
  Tooltip,
  Badge,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
  QuestionCircleOutlined,
  BarChartOutlined,
  InfoCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import styles from './ConsensusMeter.module.css'

const { Title, Text, Paragraph } = Typography

interface StudyStance {
  article_id: string
  article_title: string
  stance: 'support' | 'oppose' | 'neutral' | 'uncertain'
  confidence: number
  evidence_quality: string
  key_arguments: string[]
}

interface ConsensusAnalysis {
  id: string
  question: string
  consensus_level: string
  consensus_score: number
  statistics: {
    total_studies: number
    supporting: number
    opposing: number
    neutral: number
    uncertain: number
  }
  stances: StudyStance[]
  supporting_evidence: string[]
  opposing_evidence: string[]
  key_disagreements: string[]
  potential_sources: string[]
}

interface ConsensusMeterProps {
  analysis?: ConsensusAnalysis
  loading?: boolean
}

const ConsensusMeter: React.FC<ConsensusMeterProps> = ({
  analysis,
  loading = false,
}) => {
  if (!analysis) {
    return (
      <Alert
        message="暂无共识度分析"
        description="请先选择研究问题和相关文献进行分析"
        type="info"
        showIcon
      />
    )
  }

  // 获取共识级别信息
  const getConsensusInfo = (level: string) => {
    const infoMap: Record<string, { color: string; text: string; desc: string }> = {
      unanimous: { color: '#52c41a', text: '完全一致', desc: '学术界对此问题达成高度一致' },
      strong: { color: '#73d13d', text: '强共识', desc: '大多数研究支持同一观点' },
      moderate: { color: '#95de64', text: '中等共识', desc: '多数研究达成一致，但存在分歧' },
      mixed: { color: '#faad14', text: '混合', desc: '学术界对此存在明显分歧' },
      controversial: { color: '#ff7875', text: '争议', desc: '学术界对此有激烈争议' },
      fragmented: { color: '#f5222d', text: '高度分歧', desc: '学术界对此高度分歧' },
    }
    return infoMap[level] || { color: '#8c8c8c', text: '未知', desc: '' }
  }

  const consensusInfo = getConsensusInfo(analysis.consensus_level)

  // 立场图标
  const stanceIcons: Record<string, React.ReactNode> = {
    support: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    oppose: <CloseCircleOutlined style={{ color: '#f5222d' }} />,
    neutral: <MinusCircleOutlined style={{ color: '#8c8c8c' }} />,
    uncertain: <QuestionCircleOutlined style={{ color: '#faad14' }} />,
  }

  const stanceLabels: Record<string, string> = {
    support: '支持',
    oppose: '反对',
    neutral: '中立',
    uncertain: '不确定',
  }

  const stanceColors: Record<string, string> = {
    support: 'green',
    oppose: 'red',
    neutral: 'default',
    uncertain: 'orange',
  }

  return (
    <div className={styles.consensusMeter}>
      {/* 主仪表盘 */}
      <Card className={styles.mainCard}>
        <div className={styles.questionSection}>
          <Text type="secondary">研究问题</Text>
          <Title level={5} className={styles.question}>
            {analysis.question}
          </Title>
        </div>

        <Row gutter={24} className={styles.meterRow}>
          <Col span={8}>
            <div className={styles.gaugeSection}>
              <Progress
                type="dashboard"
                percent={Math.round(analysis.consensus_score * 100)}
                strokeColor={consensusInfo.color}
                format={(percent) => (
                  <div className={styles.gaugeContent}>
                    <span className={styles.score}>{percent}%</span>
                    <span className={styles.level}>{consensusInfo.text}</span>
                  </div>
                )}
              />
            </div>
          </Col>

          <Col span={16}>
            <div className={styles.statsSection}>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="总研究数"
                    value={analysis.statistics.total_studies}
                    prefix={<BarChartOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="支持"
                    value={analysis.statistics.supporting}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="反对"
                    value={analysis.statistics.opposing}
                    valueStyle={{ color: '#f5222d' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="中立/不确定"
                    value={
                      analysis.statistics.neutral +
                      analysis.statistics.uncertain
                    }
                  />
                </Col>
              </Row>

              <div className={styles.consensusDesc}>
                <Alert
                  message={consensusInfo.text}
                  description={consensusInfo.desc}
                  type={
                    analysis.consensus_level === 'unanimous' ||
                    analysis.consensus_level === 'strong'
                      ? 'success'
                      : analysis.consensus_level === 'moderate'
                      ? 'info'
                      : 'warning'
                  }
                  showIcon
                />
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      <Row gutter={16} className={styles.detailRow}>
        {/* 立场分布 */}
        <Col span={12}>
          <Card
            title="研究立场分布"
            className={styles.detailCard}
          >
            <List
              dataSource={analysis.stances}
              renderItem={(stance) => (
                <List.Item
                  key={stance.article_id}
                  className={styles.stanceItem}
                >
                  <List.Item.Meta
                    avatar={stanceIcons[stance.stance]}
                    title={
                      <Text ellipsis style={{ maxWidth: 250 }}>
                        {stance.article_title}
                      </Text>
                    }
                    description={
                      <Space size="small">
                        <Tag color={stanceColors[stance.stance]}>
                          {stanceLabels[stance.stance]}
                        </Tag>
                        <Tag>置信度: {(stance.confidence * 100).toFixed(0)}%</Tag>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {/* 证据对比 */}
        <Col span={12}>
          <Card title="支持与反对证据" className={styles.detailCard}>
            <div className={styles.evidenceSection}>
              <div className={styles.supportingEvidence}>
                <Text type="success" strong>
                  <CheckCircleOutlined /> 支持证据
                </Text>
                <List
                  size="small"
                  dataSource={analysis.supporting_evidence}
                  renderItem={(item) => (
                    <List.Item>
                      <Text type="secondary">• {item}</Text>
                    </List.Item>
                  )}
                />
              </div>

              <Divider />

              <div className={styles.opposingEvidence}>
                <Text type="danger" strong>
                  <CloseCircleOutlined /> 反对证据
                </Text>
                <List
                  size="small"
                  dataSource={analysis.opposing_evidence}
                  renderItem={(item) => (
                    <List.Item>
                      <Text type="secondary">• {item}</Text>
                    </List.Item>
                  )}
                />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 分歧分析 */}
      {(analysis.key_disagreements.length > 0 ||
        analysis.potential_sources.length > 0) && (
        <Card title="分歧分析" className={styles.disagreementCard}>
          {analysis.key_disagreements.length > 0 && (
            <div className={styles.disagreementSection}>
              <Text strong>
                <ExclamationCircleOutlined /> 主要分歧点
              </Text>
              <List
                size="small"
                dataSource={analysis.key_disagreements}
                renderItem={(item) => (
                  <List.Item>
                    <Badge status="warning" text={item} />
                  </List.Item>
                )}
              />
            </div>
          )}

          {analysis.potential_sources.length > 0 && (
            <div className={styles.sourcesSection}>
              <Text strong>
                <InfoCircleOutlined /> 分歧可能来源
              </Text>
              <List
                size="small"
                dataSource={analysis.potential_sources}
                renderItem={(item) => (
                  <List.Item>
                    <Badge status="default" text={item} />
                  </List.Item>
                )}
              />
            </div>
          )}
        </Card>
      )}
    </div>
  )
}

export default ConsensusMeter
