/**
 * 导师协同审阅与批注组件
 * 支持实时协作、批注管理、审阅工作流
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  List,
  Tag,
  Badge,
  Avatar,
  Tooltip,
  Input,
  Select,
  Tabs,
  Statistic,
  Row,
  Col,
  Empty,
  Popover,
  Divider,
  Progress,
  Alert,
  message,
  Dropdown,
  Menu
} from 'antd'
import {
  MessageOutlined,
  CheckCircleOutlined,
  TeamOutlined,
  FileTextOutlined,
  PlusOutlined,
  ExportOutlined,
  MoreOutlined,
  LikeOutlined,
  DislikeOutlined,
  QuestionCircleOutlined,
  EditOutlined,
  CheckOutlined,
  ReloadOutlined,
  FilterOutlined,
  CommentOutlined,
  UserOutlined,
  ClockCircleOutlined,
  PieChartOutlined
} from '@ant-design/icons'
import {
  collaborativeReviewService,
  REVIEW_TEMPLATES,
  type Comment,
  type Reviewer,
  type ReviewStats,
  type CommentType,
  type ReviewStatus
} from '@/services/collaborativeReviewService'
import styles from './CollaborativeReview.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { TabPane } = Tabs
const { Option } = Select

interface CollaborativeReviewProps {
  paperId: string
  paperTitle?: string
}

const COMMENT_TYPE_CONFIG: Record<CommentType, { color: string; icon: React.ReactNode; label: string }> = {
  suggestion: { color: 'blue', icon: <EditOutlined />, label: '建议' },
  question: { color: 'orange', icon: <QuestionCircleOutlined />, label: '问题' },
  praise: { color: 'green', icon: <LikeOutlined />, label: '表扬' },
  correction: { color: 'red', icon: <EditOutlined />, label: '修改' },
  general: { color: 'default', icon: <MessageOutlined />, label: '一般' }
}

const STATUS_CONFIG: Record<ReviewStatus, { color: string; label: string }> = {
  pending: { color: 'warning', label: '待处理' },
  in_progress: { color: 'processing', label: '进行中' },
  completed: { color: 'success', label: '已完成' },
  resolved: { color: 'success', label: '已解决' }
}

const CollaborativeReview: React.FC<CollaborativeReviewProps> = ({
  paperId,
  paperTitle = '未命名论文'
}) => {
  const [comments, setComments] = useState<Comment[]>([])
  const [reviewers, setReviewers] = useState<Reviewer[]>([])
  const [stats, setStats] = useState<ReviewStats | null>(null)
  const [selectedReviewer, setSelectedReviewer] = useState<string>('all')
  const [selectedType, setSelectedType] = useState<CommentType | 'all'>('all')
  const [selectedStatus, setSelectedStatus] = useState<ReviewStatus | 'all'>('all')
  const [isAddingComment, setIsAddingComment] = useState(false)
  const [newComment, setNewComment] = useState('')
  const [newCommentType, setNewCommentType] = useState<CommentType>('general')
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const [replyContent, setReplyContent] = useState('')
  const [activeTab, setActiveTab] = useState('comments')

  // 加载数据
  const loadData = useCallback(() => {
    const paperComments = collaborativeReviewService.getPaperComments(paperId)
    const allReviewers = collaborativeReviewService.getReviewers()
    const reviewStats = collaborativeReviewService.getReviewStats(paperId)

    setComments(paperComments)
    setReviewers(allReviewers)
    setStats(reviewStats)
  }, [paperId])

  useEffect(() => {
    loadData()

    // 订阅实时更新
    const unsubscribe = collaborativeReviewService.subscribe(() => {
      loadData()
    })

    return () => unsubscribe()
  }, [loadData])

  // 筛选批注
  const filteredComments = comments.filter(comment => {
    if (selectedReviewer !== 'all' && comment.reviewerId !== selectedReviewer) return false
    if (selectedType !== 'all' && comment.type !== selectedType) return false
    if (selectedStatus !== 'all' && comment.status !== selectedStatus) return false
    return true
  })

  // 添加批注
  const handleAddComment = () => {
    if (!newComment.trim()) {
      message.warning('请输入批注内容')
      return
    }

    collaborativeReviewService.addComment({
      reviewerId: reviewers[0]?.id || 'unknown',
      paperId,
      sectionId: 'section_1',
      type: newCommentType,
      content: newComment,
      position: { start: 0, end: 0 },
      status: 'pending'
    })

    setNewComment('')
    setIsAddingComment(false)
    message.success('批注已添加')
  }

  // 回复批注
  const handleReply = (commentId: string) => {
    if (!replyContent.trim()) return

    collaborativeReviewService.addReply(commentId, reviewers[0]?.id || 'unknown', replyContent)
    setReplyContent('')
    setReplyingTo(null)
    message.success('回复已添加')
  }

  // 更新批注状态
  const handleStatusChange = (commentId: string, status: ReviewStatus) => {
    collaborativeReviewService.updateCommentStatus(commentId, status)
    message.success('状态已更新')
  }

  // 导出报告
  const handleExport = () => {
    const report = collaborativeReviewService.exportReviewReport(paperId)
    const blob = new Blob([report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `审阅报告_${paperTitle}.md`
    a.click()
    message.success('报告已导出')
  }

  // 模拟实时协作
  const simulateCollaboration = () => {
    collaborativeReviewService.simulateIncomingComment(paperId)
    message.info('收到新的批注')
  }

  // 渲染批注项
  const renderComment = (comment: Comment) => {
    const reviewer = reviewers.find(r => r.id === comment.reviewerId)
    const typeConfig = COMMENT_TYPE_CONFIG[comment.type]
    const statusConfig = STATUS_CONFIG[comment.status]

    return (
      <List.Item
        className={styles.commentItem}
        actions={[
          <Tooltip title="标记为已解决">
            <Button
              type="text"
              icon={<CheckCircleOutlined />}
              onClick={() => handleStatusChange(comment.id, 'resolved')}
              disabled={comment.status === 'resolved'}
            />
          </Tooltip>,
          <Tooltip title="回复">
            <Button
              type="text"
              icon={<MessageOutlined />}
              onClick={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
            />
          </Tooltip>
        ]}
      >
        <div className={styles.commentContent}>
          <div className={styles.commentHeader}>
            <Space>
              <Avatar style={{ backgroundColor: reviewer?.color }}>
                {reviewer?.avatar}
              </Avatar>
              <div>
                <Text strong>{reviewer?.name}</Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {reviewer?.title}
                </Text>
              </div>
              <Tag color={typeConfig.color} icon={typeConfig.icon}>
                {typeConfig.label}
              </Tag>
              <Tag color={statusConfig.color}>{statusConfig.label}</Tag>
            </Space>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {new Date(comment.createdAt).toLocaleString('zh-CN')}
            </Text>
          </div>

          <Paragraph className={styles.commentText}>{comment.content}</Paragraph>

          {comment.selectedText && (
            <div className={styles.selectedText}>
              <Text type="secondary" style={{ fontSize: 12 }}>引用：</Text>
              <Text italic>"{comment.selectedText}"</Text>
            </div>
          )}

          {/* 反应 */}
          {comment.reactions.length > 0 && (
            <div className={styles.reactions}>
              {comment.reactions.map((reaction, idx) => {
                const r = reviewers.find(rv => rv.id === reaction.reviewerId)
                return (
                  <Tooltip key={idx} title={r?.name}>
                    <span className={styles.reaction}>
                      {reaction.type === 'agree' && <LikeOutlined style={{ color: '#52c41a' }} />}
                      {reaction.type === 'helpful' && <CheckOutlined style={{ color: '#1890ff' }} />}
                      {reaction.type === 'resolved' && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                    </span>
                  </Tooltip>
                )
              })}
            </div>
          )}

          {/* 回复列表 */}
          {comment.replies.length > 0 && (
            <div className={styles.replies}>
              {comment.replies.map(reply => {
                const replyReviewer = reviewers.find(r => r.id === reply.reviewerId)
                return (
                  <div key={reply.id} className={styles.reply}>
                    <Avatar size="small" style={{ backgroundColor: replyReviewer?.color }}>
                      {replyReviewer?.avatar}
                    </Avatar>
                    <div className={styles.replyContent}>
                      <Text strong style={{ fontSize: 12 }}>{replyReviewer?.name}</Text>
                      <Text style={{ fontSize: 13 }}>{reply.content}</Text>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* 回复输入框 */}
          {replyingTo === comment.id && (
            <div className={styles.replyInput}>
              <TextArea
                value={replyContent}
                onChange={e => setReplyContent(e.target.value)}
                placeholder="输入回复..."
                rows={2}
                size="small"
              />
              <Space style={{ marginTop: 8 }}>
                <Button type="primary" size="small" onClick={() => handleReply(comment.id)}>
                  发送
                </Button>
                <Button size="small" onClick={() => setReplyingTo(null)}>
                  取消
                </Button>
              </Space>
            </div>
          )}
        </div>
      </List.Item>
    )
  }

  return (
    <Card
      className={styles.collaborativeReview}
      title={
        <Space>
          <TeamOutlined />
          <span>协同审阅</span>
          {stats && (
            <Badge
              count={stats.pendingComments}
              style={{ backgroundColor: '#ff4d4f' }}
              overflowCount={99}
            />
          )}
        </Space>
      }
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={simulateCollaboration}
            size="small"
          >
            模拟新批注
          </Button>
          <Button
            icon={<ExportOutlined />}
            onClick={handleExport}
            size="small"
          >
            导出报告
          </Button>
        </Space>
      }
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <span>
              <MessageOutlined />
              批注 ({comments.length})
            </span>
          }
          key="comments"
        >
          {/* 统计概览 */}
          {stats && (
            <div className={styles.statsOverview}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="总批注"
                    value={stats.totalComments}
                    prefix={<CommentOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="已解决"
                    value={stats.resolvedComments}
                    valueStyle={{ color: '#52c41a' }}
                    prefix={<CheckCircleOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="待处理"
                    value={stats.pendingComments}
                    valueStyle={{ color: '#ff4d4f' }}
                    prefix={<ClockCircleOutlined />}
                  />
                </Col>
              </Row>

              {/* 进度条 */}
              <div className={styles.progressSection}>
                <Text type="secondary">审阅进度</Text>
                <Progress
                  percent={stats.totalComments > 0
                    ? Math.round((stats.resolvedComments / stats.totalComments) * 100)
                    : 0
                  }
                  status="active"
                />
              </div>
            </div>
          )}

          <Divider />

          {/* 筛选器 */}
          <div className={styles.filters}>
            <Space wrap>
              <Select
                value={selectedReviewer}
                onChange={setSelectedReviewer}
                style={{ width: 120 }}
                size="small"
                placeholder="审阅者"
              >
                <Option value="all">全部审阅者</Option>
                {reviewers.map(r => (
                  <Option key={r.id} value={r.id}>{r.name}</Option>
                ))}
              </Select>

              <Select
                value={selectedType}
                onChange={setSelectedType}
                style={{ width: 100 }}
                size="small"
                placeholder="类型"
              >
                <Option value="all">全部类型</Option>
                {Object.entries(COMMENT_TYPE_CONFIG).map(([key, config]) => (
                  <Option key={key} value={key}>{config.label}</Option>
                ))}
              </Select>

              <Select
                value={selectedStatus}
                onChange={setSelectedStatus}
                style={{ width: 100 }}
                size="small"
                placeholder="状态"
              >
                <Option value="all">全部状态</Option>
                {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                  <Option key={key} value={key}>{config.label}</Option>
                ))}
              </Select>
            </Space>
          </div>

          {/* 添加批注 */}
          <div className={styles.addCommentSection}>
            {!isAddingComment ? (
              <Button
                type="dashed"
                icon={<PlusOutlined />}
                onClick={() => setIsAddingComment(true)}
                block
              >
                添加批注
              </Button>
            ) : (
              <div className={styles.newCommentForm}>
                <Select
                  value={newCommentType}
                  onChange={setNewCommentType}
                  style={{ width: 120, marginBottom: 8 }}
                  size="small"
                >
                  {Object.entries(COMMENT_TYPE_CONFIG).map(([key, config]) => (
                    <Option key={key} value={key}>{config.label}</Option>
                  ))}
                </Select>
                <TextArea
                  value={newComment}
                  onChange={e => setNewComment(e.target.value)}
                  placeholder="输入批注内容..."
                  rows={3}
                />
                <Space style={{ marginTop: 8 }}>
                  <Button type="primary" onClick={handleAddComment}>
                    提交
                  </Button>
                  <Button onClick={() => setIsAddingComment(false)}>
                    取消
                  </Button>
                </Space>
              </div>
            )}
          </div>

          {/* 批注列表 */}
          <List
            className={styles.commentsList}
            dataSource={filteredComments}
            renderItem={renderComment}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="暂无批注"
                />
              )
            }}
          />
        </TabPane>

        <TabPane
          tab={
            <span>
              <TeamOutlined />
              审阅者 ({reviewers.length})
            </span>
          }
          key="reviewers"
        >
          <List
            dataSource={reviewers}
            renderItem={reviewer => (
              <List.Item>
                <List.Item.Meta
                  avatar={
                    <Avatar style={{ backgroundColor: reviewer.color, fontSize: 24 }}>
                      {reviewer.avatar}
                    </Avatar>
                  }
                  title={reviewer.name}
                  description={
                    <Space direction="vertical" size="small">
                      <Text type="secondary">{reviewer.title}</Text>
                      <Space wrap>
                        {reviewer.expertise.map(exp => (
                          <Tag key={exp} size="small">{exp}</Tag>
                        ))}
                      </Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        批注数: {stats?.byReviewer[reviewer.id] || 0}
                      </Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </TabPane>

        <TabPane
          tab={
            <span>
              <PieChartOutlined />
              统计
            </span>
          }
          key="stats"
        >
          {stats && (
            <div className={styles.statsDetail}>
              <Title level={5}>按类型分布</Title>
              <Row gutter={[16, 16]}>
                {Object.entries(stats.byType).map(([type, count]) => (
                  <Col span={12} key={type}>
                    <Card size="small">
                      <Statistic
                        title={COMMENT_TYPE_CONFIG[type as CommentType].label}
                        value={count}
                        prefix={COMMENT_TYPE_CONFIG[type as CommentType].icon}
                      />
                    </Card>
                  </Col>
                ))}
              </Row>

              <Title level={5} style={{ marginTop: 24 }}>按审阅者分布</Title>
              {Object.entries(stats.byReviewer).map(([reviewerId, count]) => {
                const reviewer = reviewers.find(r => r.id === reviewerId)
                return (
                  <div key={reviewerId} className={styles.reviewerStat}>
                    <Space>
                      <Avatar size="small" style={{ backgroundColor: reviewer?.color }}>
                        {reviewer?.avatar}
                      </Avatar>
                      <Text>{reviewer?.name}</Text>
                      <Progress
                        percent={Math.round((count / stats.totalComments) * 100)}
                        size="small"
                        style={{ width: 200 }}
                      />
                      <Text type="secondary">{count}条</Text>
                    </Space>
                  </div>
                )
              })}
            </div>
          )}
        </TabPane>

        <TabPane
          tab={
            <span>
              <FileTextOutlined />
              模板
            </span>
          }
          key="templates"
        >
          <List
            dataSource={REVIEW_TEMPLATES}
            renderItem={template => (
              <List.Item>
                <Card title={template.name} style={{ width: '100%' }}>
                  <Paragraph type="secondary">{template.description}</Paragraph>
                  <Divider />
                  <Text strong>检查清单：</Text>
                  <ul>
                    {template.checklist.map((item, idx) => (
                      <li key={idx}><Text>{item}</Text></li>
                    ))}
                  </ul>
                </Card>
              </List.Item>
            )}
          />
        </TabPane>
      </Tabs>
    </Card>
  )
}

export default CollaborativeReview
