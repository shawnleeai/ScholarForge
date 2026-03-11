/**
 * 证据详情弹窗组件
 * 展示文献证据的详细信息和分析结果
 */

import React from 'react'
import {
  Modal,
  Card,
  Descriptions,
  Tag,
  Space,
  Typography,
  Divider,
  List,
  Badge,
  Tabs,
  Alert,
  Statistic,
  Row,
  Col,
} from 'antd'
import {
  FileTextOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  BulbOutlined,
  TeamOutlined,
  CalendarOutlined,
  BookOutlined,
} from '@ant-design/icons'
import styles from './EvidenceDetail.module.css'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

interface StudyDesign {
  type: string
  sample_size?: number
  duration?: string
  setting?: string
}

interface Evidence {
  article_id: string
  article_title: string
  authors: string[]
  year: number
  journal?: string
  claim: string
  evidence_type: string
  evidence_strength: 'strong' | 'moderate' | 'weak' | 'inconclusive'
  key_findings: string[]
  study_design?: StudyDesign
  sample_description?: string
  statistics?: Record<string, any>
  limitations: string[]
  quality_score?: number
}

interface EvidenceDetailProps {
  evidence: Evidence | null
  visible: boolean
  onClose: () => void
}

const EvidenceDetail: React.FC<EvidenceDetailProps> = ({
  evidence,
  visible,
  onClose,
}) => {
  if (!evidence) return null

  const getStrengthColor = (strength: string) => {
    const colors: Record<string, string> = {
      strong: 'green',
      moderate: 'blue',
      weak: 'orange',
      inconclusive: 'red',
    }
    return colors[strength] || 'default'
  }

  const getStrengthLabel = (strength: string) => {
    const labels: Record<string, string> = {
      strong: '强',
      moderate: '中等',
      weak: '弱',
      inconclusive: '不确定',
    }
    return labels[strength] || strength
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'experimental':
        return <ExperimentOutlined />
      case 'observational':
        return <BarChartOutlined />
      case 'review':
        return <BookOutlined />
      default:
        return <FileTextOutlined />
    }
  }

  return (
    <Modal
      title="证据详情"
      open={visible}
      onCancel={onClose}
      width={800}
      footer={null}
      className={styles.evidenceModal}
    >
      {/* 头部信息 */}
      <div className={styles.header}>
        <Title level={4} className={styles.title}>
          {evidence.article_title}
        </Title>
        <Space wrap>
          <Tag color={getStrengthColor(evidence.evidence_strength)} icon={<CheckCircleOutlined />}>
            证据强度: {getStrengthLabel(evidence.evidence_strength)}
          </Tag>
          <Tag icon={getTypeIcon(evidence.evidence_type)}>{evidence.evidence_type}</Tag>
          {evidence.quality_score && (
            <Badge
              count={`质量: ${Math.round(evidence.quality_score * 100)}`}
              style={{ backgroundColor: evidence.quality_score >= 0.7 ? '#52c41a' : '#faad14' }}
            />
          )}
        </Space>
      </div>

      <Divider />

      {/* 基本信息 */}
      <Descriptions title="文献信息" bordered size="small" column={2}>
        <Descriptions.Item label={<><TeamOutlined /> 作者</>}>
          {evidence.authors.join(', ')}
        </Descriptions.Item>
        <Descriptions.Item label={<><CalendarOutlined /> 发表年份</>}>
          {evidence.year}
        </Descriptions.Item>
        {evidence.journal && (
          <Descriptions.Item label={<><BookOutlined /> 期刊</>} span={2}>
            {evidence.journal}
          </Descriptions.Item>
        )}
      </Descriptions>

      <Divider />

      {/* 标签页内容 */}
      <Tabs defaultActiveKey="findings">
        <TabPane tab="主要发现" key="findings">
          <Card className={styles.findingsCard}>
            <div className={styles.claimSection}>
              <Text strong className={styles.sectionLabel}>
                <BulbOutlined /> 核心主张
              </Text>
              <Paragraph className={styles.claim}>{evidence.claim}</Paragraph>
            </div>

            <Divider />

            <div className={styles.findingsSection}>
              <Text strong className={styles.sectionLabel}>
                <CheckCircleOutlined /> 关键发现
              </Text>
              <List
                dataSource={evidence.key_findings}
                renderItem={(finding, index) => (
                  <List.Item>
                    <Space>
                      <Badge count={index + 1} style={{ backgroundColor: '#1890ff' }} />
                      <Text>{finding}</Text>
                    </Space>
                  </List.Item>
                )}
              />
            </div>
          </Card>
        </TabPane>

        <TabPane tab="研究设计" key="design">
          {evidence.study_design ? (
            <Card>
              <Descriptions bordered column={2}>
                <Descriptions.Item label="研究类型">
                  {evidence.study_design.type}
                </Descriptions.Item>
                <Descriptions.Item label="样本量">
                  {evidence.study_design.sample_size?.toLocaleString() || '未报告'}
                </Descriptions.Item>
                <Descriptions.Item label="研究时长">
                  {evidence.study_design.duration || '未报告'}
                </Descriptions.Item>
                <Descriptions.Item label="研究场景">
                  {evidence.study_design.setting || '未报告'}
                </Descriptions.Item>
              </Descriptions>

              {evidence.sample_description && (
                <>
                  <Divider />
                  <div>
                    <Text strong>样本描述:</Text>
                    <Paragraph>{evidence.sample_description}</Paragraph>
                  </div>
                </>
              )}
            </Card>
          ) : (
            <Empty description="暂无研究设计信息" />
          )}
        </TabPane>

        <TabPane tab="统计数据" key="statistics">
          {evidence.statistics && Object.keys(evidence.statistics).length > 0 ? (
            <Row gutter={[16, 16]}>
              {Object.entries(evidence.statistics).map(([key, value]) => (
                <Col span={8} key={key}>
                  <Card size="small" className={styles.statCard}>
                    <Statistic
                      title={key}
                      value={typeof value === 'number' ? value : String(value)}
                      precision={typeof value === 'number' && value < 1 ? 3 : 2}
                    />
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <Empty description="暂无统计数据" />
          )}
        </TabPane>

        <TabPane tab="局限性" key="limitations">
          {evidence.limitations.length > 0 ? (
            <Alert
              message="研究局限性"
              description={
                <List
                  dataSource={evidence.limitations}
                  renderItem={(limitation) => (
                    <List.Item>
                      <Space>
                        <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                        <Text>{limitation}</Text>
                      </Space>
                    </List.Item>
                  )}
                />
              }
              type="warning"
              showIcon
            />
          ) : (
            <Empty description="未报告局限性" />
          )}
        </TabPane>
      </Tabs>
    </Modal>
  )
}

export default EvidenceDetail
