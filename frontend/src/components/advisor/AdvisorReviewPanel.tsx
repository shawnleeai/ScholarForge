/**
 * 导师审阅面板
 * 提供论文评审、批注、评分等功能
 */

import React, { useState } from 'react'
import {
  Card,
  Tabs,
  Button,
  Form,
  Input,
  Select,
  Typography,
  Space,
  Tag,
  List,
  Badge,
  Alert,
  Divider,
  Rate,
  Collapse,
  // Tooltip,
  message,
  // Empty,
  // Avatar,
  // Timeline,
  // Progress,
  Statistic,
  Row,
  Col
} from 'antd'
import {
  EyeOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  // EditOutlined,
  FileTextOutlined,
  StarOutlined,
  // FlagOutlined,
  SendOutlined,
  HistoryOutlined,
  UserOutlined,
  CalendarOutlined,
  CheckOutlined
  // ExclamationCircleOutlined
} from '@ant-design/icons'
import styles from './AdvisorReviewPanel.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Option } = Select
// const { Panel } = Collapse
// const { TabPane } = Tabs

// 评审维度
interface ReviewDimension {
  id: string
  name: string
  description: string
  maxScore: number
  weight: number
}

// 评审意见
interface ReviewComment {
  id: string
  type: 'general' | 'structure' | 'methodology' | 'result' | 'discussion' | 'language'
  content: string
  severity: 'critical' | 'major' | 'minor' | 'suggestion'
  pageNumber?: number
  lineNumber?: string
  createdAt: string
  status: 'open' | 'resolved' | 'addressed'
}

// 学生提交
interface StudentSubmission {
  id: string
  studentName: string
  studentId: string
  paperTitle: string
  submitDate: string
  version: string
  abstract: string
  keywords: string[]
  status: 'pending' | 'reviewing' | 'revised' | 'approved'
  previousReviews?: number
}

interface AdvisorReviewPanelProps {
  submission: StudentSubmission
  onSubmitReview?: (review: ReviewData) => void
  onAddComment?: (comment: ReviewComment) => void
}

interface ReviewData {
  dimensions: Record<string, number>
  overallComment: string
  decision: 'accept' | 'minor_revision' | 'major_revision' | 'reject'
  comments: ReviewComment[]
}

const reviewDimensions: ReviewDimension[] = [
  { id: 'topic', name: '选题价值', description: '选题的学术价值和实际意义', maxScore: 5, weight: 0.15 },
  { id: 'innovation', name: '创新性', description: '研究的创新程度和贡献', maxScore: 5, weight: 0.2 },
  { id: 'methodology', name: '研究方法', description: '研究方法是否科学合理', maxScore: 5, weight: 0.2 },
  { id: 'data', name: '数据/论证', description: '数据充分性和论证严密性', maxScore: 5, weight: 0.15 },
  { id: 'writing', name: '写作规范', description: '论文写作和格式规范', maxScore: 5, weight: 0.15 },
  { id: 'structure', name: '结构逻辑', description: '论文结构是否合理，逻辑是否清晰', maxScore: 5, weight: 0.15 }
]

const AdvisorReviewPanel: React.FC<AdvisorReviewPanelProps> = ({
  submission,
  onSubmitReview,
  onAddComment
}) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [scores, setScores] = useState<Record<string, number>>({})
  const [overallComment, setOverallComment] = useState('')
  const [decision, setDecision] = useState<ReviewData['decision']>('minor_revision')
  const [comments, setComments] = useState<ReviewComment[]>([])
  const [newComment, setNewComment] = useState('')
  const [commentType, setCommentType] = useState<ReviewComment['type']>('general')
  const [commentSeverity, setCommentSeverity] = useState<ReviewComment['severity']>('suggestion')
  const [submitting, setSubmitting] = useState(false)

  // 计算加权总分
  const calculateTotalScore = () => {
    let total = 0
    reviewDimensions.forEach(dim => {
      const score = scores[dim.id] || 0
      total += score * dim.weight
    })
    return total.toFixed(2)
  }

  // 添加评审意见
  const handleAddComment = () => {
    if (!newComment.trim()) {
      message.warning('请输入评审意见')
      return
    }
    const comment: ReviewComment = {
      id: Date.now().toString(),
      type: commentType,
      content: newComment,
      severity: commentSeverity,
      createdAt: new Date().toISOString(),
      status: 'open'
    }
    setComments([...comments, comment])
    setNewComment('')
    message.success('意见已添加')
    onAddComment?.(comment)
  }

  // 提交评审
  const handleSubmitReview = async () => {
    if (Object.keys(scores).length < reviewDimensions.length) {
      message.warning('请完成所有维度的评分')
      return
    }
    if (!overallComment.trim()) {
      message.warning('请输入总体评价')
      return
    }

    setSubmitting(true)
    try {
      const reviewData: ReviewData = {
        dimensions: scores,
        overallComment,
        decision,
        comments
      }
      await new Promise(r => setTimeout(r, 1000)) // 模拟API调用
      message.success('评审已提交')
      onSubmitReview?.(reviewData)
    } catch (error) {
      message.error('提交失败')
    } finally {
      setSubmitting(false)
    }
  }

  // 获取决策标签
  const getDecisionTag = (d: ReviewData['decision']) => {
    const config = {
      accept: { color: 'success', text: '通过' },
      minor_revision: { color: 'processing', text: '小修' },
      major_revision: { color: 'warning', text: '大修' },
      reject: { color: 'error', text: '不通过' }
    }
    return config[d]
  }

  // 获取严重程度标签
  const getSeverityTag = (s: ReviewComment['severity']) => {
    const config = {
      critical: { color: 'red', text: '严重' },
      major: { color: 'orange', text: '重要' },
      minor: { color: 'blue', text: '一般' },
      suggestion: { color: 'default', text: '建议' }
    }
    return config[s]
  }

  // 渲染概览
  const renderOverview = () => (
    <div className={styles.overview}>
      <Alert
        message="导师审阅模式"
        description="您正在审阅学生的论文提交。请从多个维度进行评估，并提供建设性的修改意见。"
        type="info"
        showIcon
      />

      <Row gutter={24} className={styles.statsRow}>
        <Col span={8}>
          <Card>
            <Statistic
              title="当前版本"
              value={submission.version}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="提交日期"
              value={new Date(submission.submitDate).toLocaleDateString()}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="历史评审"
              value={submission.previousReviews || 0}
              prefix={<HistoryOutlined />}
              suffix="次"
            />
          </Card>
        </Col>
      </Row>

      <Card title="论文信息" className={styles.paperInfo}>
        <Title level={4}>{submission.paperTitle}</Title>
        <Space split={<Divider type="vertical" />}>
          <Text type="secondary">
            <UserOutlined /> {submission.studentName}
          </Text>
          <Text type="secondary">学号: {submission.studentId}</Text>
        </Space>
        <Divider />
        <Paragraph type="secondary">
          <strong>摘要:</strong> {submission.abstract}
        </Paragraph>
        <Space wrap>
          {submission.keywords.map(k => (
            <Tag key={k}>{k}</Tag>
          ))}
        </Space>
      </Card>
    </div>
  )

  // 渲染评分
  const renderScoring = () => (
    <div className={styles.scoring}>
      <Alert
        message={`当前总分: ${calculateTotalScore()} / 5.0`}
        type={parseFloat(calculateTotalScore()) >= 4 ? 'success' : parseFloat(calculateTotalScore()) >= 3 ? 'warning' : 'error'}
        showIcon
      />

      <List
        className={styles.dimensionList}
        dataSource={reviewDimensions}
        renderItem={dim => (
          <List.Item
            actions={[
              <Rate
                value={scores[dim.id]}
                onChange={value => setScores({ ...scores, [dim.id]: value })}
                allowClear
              />
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <Text strong>{dim.name}</Text>
                  <Tag>权重 {dim.weight * 100}%</Tag>
                </Space>
              }
              description={dim.description}
            />
          </List.Item>
        )}
      />

      <Divider />

      <Form layout="vertical">
        <Form.Item label="总体评价">
          <TextArea
            rows={6}
            placeholder="请输入对论文的总体评价，包括优点和不足之处..."
            value={overallComment}
            onChange={e => setOverallComment(e.target.value)}
          />
        </Form.Item>

        <Form.Item label="评审结论">
          <Select
            value={decision}
            onChange={setDecision}
            style={{ width: 200 }}
          >
            <Option value="accept">
              <Tag color="success">通过</Tag> - 无需修改直接通过
            </Option>
            <Option value="minor_revision">
              <Tag color="processing">小修</Tag> - 需要小幅修改
            </Option>
            <Option value="major_revision">
              <Tag color="warning">大修</Tag> - 需要重大修改
            </Option>
            <Option value="reject">
              <Tag color="error">不通过</Tag> - 未达到要求
            </Option>
          </Select>
        </Form.Item>
      </Form>
    </div>
  )

  // 渲染详细意见
  const renderComments = () => (
    <div className={styles.comments}>
      <Card title="添加评审意见" className={styles.addCommentCard}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Select
              value={commentType}
              onChange={setCommentType}
              style={{ width: 120 }}
            >
              <Option value="general">总体</Option>
              <Option value="structure">结构</Option>
              <Option value="methodology">方法</Option>
              <Option value="result">结果</Option>
              <Option value="discussion">讨论</Option>
              <Option value="language">语言</Option>
            </Select>
            <Select
              value={commentSeverity}
              onChange={setCommentSeverity}
              style={{ width: 120 }}
            >
              <Option value="critical">严重问题</Option>
              <Option value="major">重要问题</Option>
              <Option value="minor">一般问题</Option>
              <Option value="suggestion">建议</Option>
            </Select>
          </Space>
          <TextArea
            rows={4}
            placeholder="请输入具体的评审意见..."
            value={newComment}
            onChange={e => setNewComment(e.target.value)}
          />
          <Button type="primary" icon={<CheckOutlined />} onClick={handleAddComment}>
            添加意见
          </Button>
        </Space>
      </Card>

      <Divider />

      <Title level={5}>已添加意见 ({comments.length})</Title>
      <List
        dataSource={comments}
        renderItem={comment => (
          <List.Item
            actions={[
              <Button
                type="link"
                danger
                onClick={() => setComments(comments.filter(c => c.id !== comment.id))}
              >
                删除
              </Button>
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <Tag>{comment.type === 'general' ? '总体' : comment.type === 'structure' ? '结构' : comment.type === 'methodology' ? '方法' : comment.type === 'result' ? '结果' : comment.type === 'discussion' ? '讨论' : '语言'}</Tag>
                  {getSeverityTag(comment.severity) && (
                    <Tag color={getSeverityTag(comment.severity).color}>
                      {getSeverityTag(comment.severity).text}
                    </Tag>
                  )}
                </Space>
              }
              description={comment.content}
            />
          </List.Item>
        )}
        locale={{ emptyText: '暂无评审意见' }}
      />
    </div>
  )

  // 渲染预览
  const renderPreview = () => {
    const decisionConfig = getDecisionTag(decision)
    return (
      <div className={styles.preview}>
        <Alert
          message="评审报告预览"
          description="请确认以下评审内容，确认无误后提交"
          type="info"
          showIcon
        />

        <Card className={styles.previewCard}>
          <Title level={4}>评审报告</Title>
          <Divider />

          <div className={styles.previewSection}>
            <Title level={5}>评分结果</Title>
            <List
              size="small"
              dataSource={reviewDimensions}
              renderItem={dim => (
                <List.Item>
                  <Text>{dim.name}</Text>
                  <Rate disabled value={scores[dim.id] || 0} />
                </List.Item>
              )}
            />
            <div className={styles.totalScore}>
              <Text strong>总分: {calculateTotalScore()} / 5.0</Text>
            </div>
          </div>

          <Divider />

          <div className={styles.previewSection}>
            <Title level={5}>评审结论</Title>
            <Tag color={decisionConfig.color} className={styles.decisionTag}>
              {decisionConfig.text}
            </Tag>
          </div>

          <Divider />

          <div className={styles.previewSection}>
            <Title level={5}>总体评价</Title>
            <Paragraph>{overallComment || '未填写'}</Paragraph>
          </div>

          <Divider />

          <div className={styles.previewSection}>
            <Title level={5}>详细意见 ({comments.length})</Title>
            <List
              dataSource={comments}
              renderItem={comment => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Tag>{comment.type}</Tag>
                        {comment.severity && (
                          <Tag color={getSeverityTag(comment.severity)?.color}>
                            {getSeverityTag(comment.severity)?.text}
                          </Tag>
                        )}
                      </Space>
                    }
                    description={comment.content}
                  />
                </List.Item>
              )}
            />
          </div>

          <Divider />

          <Button
            type="primary"
            size="large"
            icon={<SendOutlined />}
            onClick={handleSubmitReview}
            loading={submitting}
            block
          >
            提交评审
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className={styles.advisorReviewPanel}>
      <Card
        title={
          <Space>
            <EyeOutlined />
            <span>导师审阅 - {submission.studentName}</span>
            <Badge
              status={submission.status === 'pending' ? 'default' : submission.status === 'reviewing' ? 'processing' : 'success'}
              text={submission.status === 'pending' ? '待审阅' : submission.status === 'reviewing' ? '审阅中' : '已完成'}
            />
          </Space>
        }
        className={styles.mainCard}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          items={[
            {
              key: 'overview',
              label: (
                <span>
                  <FileTextOutlined /> 论文概览
                </span>
              ),
              children: renderOverview()
            },
            {
              key: 'scoring',
              label: (
                <span>
                  <StarOutlined /> 评分
                </span>
              ),
              children: renderScoring()
            },
            {
              key: 'comments',
              label: (
                <span>
                  <MessageOutlined /> 详细意见
                  {comments.length > 0 && <Badge count={comments.length} style={{ marginLeft: 8 }} />}
                </span>
              ),
              children: renderComments()
            },
            {
              key: 'preview',
              label: (
                <span>
                  <CheckCircleOutlined /> 预览提交
                </span>
              ),
              children: renderPreview()
            }
          ]}
        />
      </Card>
    </div>
  )
}

export default AdvisorReviewPanel
