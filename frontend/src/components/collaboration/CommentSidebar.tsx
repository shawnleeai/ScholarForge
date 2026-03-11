/**
 * 评论侧边栏组件
 * 显示文档中的所有评论，支持添加、回复、解决评论
 */

import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Card,
  List,
  Button,
  Input,
  Avatar,
  Space,
  Tag,
  Badge,
  Tooltip,
  Popconfirm,
  Empty,
  Tabs,
  Typography,
  Divider,
  Form,
  message,
} from 'antd'
import {
  CommentOutlined,
  CheckOutlined,
  CloseOutlined,
  DeleteOutlined,
  EditOutlined,
  MessageOutlined,
  UserOutlined,
  PushpinOutlined,
  CheckCircleFilled,
  ExclamationCircleFilled,
} from '@ant-design/icons'
import type { TabsProps } from 'antd'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

import {
  CommentManager,
  Comment,
  CommentAuthor,
  CommentStatus,
  CommentReply,
} from '../../services/collaboration/CommentManager'
import styles from './Collaboration.module.css'

const { TextArea } = Input
const { Text, Title } = Typography

interface CommentSidebarProps {
  commentManager: CommentManager
  currentUser: CommentAuthor
  documentId: string
  selectedText?: { from: number; to: number; text: string } | null
  onSelectComment?: (commentId: string, position: { from: number; to: number }) => void
  onHighlightComment?: (commentId: string | null) => void
}

export const CommentSidebar: React.FC<CommentSidebarProps> = ({
  commentManager,
  currentUser,
  documentId,
  selectedText,
  onSelectComment,
  onHighlightComment,
}) => {
  const [comments, setComments] = useState<Comment[]>([])
  const [activeTab, setActiveTab] = useState('all')
  const [newCommentContent, setNewCommentContent] = useState('')
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const [replyContent, setReplyContent] = useState('')
  const [editingComment, setEditingComment] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [highlightedComment, setHighlightedComment] = useState<string | null>(null)

  // 监听评论变化
  useEffect(() => {
    const unsubscribe = commentManager.onChange((updatedComments) => {
      setComments(updatedComments)
    })

    // 初始加载
    setComments(commentManager.getAllComments())

    return unsubscribe
  }, [commentManager])

  // 创建新评论
  const handleCreateComment = useCallback(() => {
    if (!selectedText || !newCommentContent.trim()) return

    commentManager.createComment({
      content: newCommentContent.trim(),
      author: currentUser,
      position: { from: selectedText.from, to: selectedText.to },
    })

    setNewCommentContent('')
    message.success('评论已添加')
  }, [commentManager, currentUser, selectedText, newCommentContent])

  // 添加回复
  const handleAddReply = useCallback(
    (commentId: string) => {
      if (!replyContent.trim()) return

      commentManager.addReply({
        commentId,
        content: replyContent.trim(),
        author: currentUser,
      })

      setReplyContent('')
      setReplyingTo(null)
      message.success('回复已添加')
    },
    [commentManager, currentUser, replyContent]
  )

  // 解决评论
  const handleResolveComment = useCallback(
    (commentId: string) => {
      commentManager.resolveComment(commentId, currentUser.id)
      message.success('评论已标记为解决')
    },
    [commentManager, currentUser.id]
  )

  // 重新打开评论
  const handleReopenComment = useCallback(
    (commentId: string) => {
      commentManager.reopenComment(commentId)
      message.success('评论已重新打开')
    },
    [commentManager]
  )

  // 删除评论
  const handleDeleteComment = useCallback(
    (commentId: string) => {
      commentManager.deleteComment(commentId)
      message.success('评论已删除')
    },
    [commentManager]
  )

  // 更新评论
  const handleUpdateComment = useCallback(
    (commentId: string) => {
      if (!editContent.trim()) return

      commentManager.updateComment(commentId, editContent.trim())
      setEditingComment(null)
      setEditContent('')
      message.success('评论已更新')
    },
    [commentManager, editContent]
  )

  // 点击评论高亮对应文本
  const handleCommentClick = useCallback(
    (comment: Comment) => {
      setHighlightedComment(comment.id)
      onHighlightComment?.(comment.id)
      onSelectComment?.(comment.id, comment.position)

      // 3秒后取消高亮
      setTimeout(() => {
        setHighlightedComment(null)
        onHighlightComment?.(null)
      }, 3000)
    },
    [onHighlightComment, onSelectComment]
  )

  // 过滤评论
  const filteredComments = comments.filter((comment) => {
    switch (activeTab) {
      case 'open':
        return comment.status === 'open'
      case 'resolved':
        return comment.status === 'resolved'
      case 'mine':
        return comment.author.id === currentUser.id
      case 'mentions':
        return comment.mentions.includes(currentUser.id)
      default:
        return true
    }
  })

  // 排序：未解决的在前，按时间倒序
  const sortedComments = [...filteredComments].sort((a, b) => {
    if (a.status === 'open' && b.status !== 'open') return -1
    if (a.status !== 'open' && b.status === 'open') return 1
    return b.createdAt - a.createdAt
  })

  // 评论统计
  const stats = commentManager.getStats()

  // 获取状态标签
  const getStatusTag = (status: CommentStatus) => {
    switch (status) {
      case 'open':
        return <Tag icon={<ExclamationCircleFilled />} color="warning">待处理</Tag>
      case 'resolved':
        return <Tag icon={<CheckCircleFilled />} color="success">已解决</Tag>
      case 'rejected':
        return <Tag icon={<CloseOutlined />} color="error">已拒绝</Tag>
    }
  }

  // 渲染评论项
  const renderCommentItem = (comment: Comment) => {
    const isHighlighted = highlightedComment === comment.id
    const isOwner = comment.author.id === currentUser.id

    return (
      <div
        key={comment.id}
        className={`${styles.commentItem} ${
          comment.status === 'resolved' ? styles.resolved : ''
        } ${isHighlighted ? styles.highlighted : ''}`}
        onClick={() => handleCommentClick(comment)}
      >
        {/* 评论头部 */}
        <div className={styles.commentHeader}>
          <Space>
            <Avatar
              size="small"
              style={{ backgroundColor: comment.author.color }}
              src={comment.author.avatar}
            >
              {comment.author.name[0]}
            </Avatar>
            <Text strong>{comment.author.name}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {dayjs(comment.createdAt).fromNow()}
            </Text>
          </Space>
          {getStatusTag(comment.status)}
        </div>

        {/* 评论内容 */}
        <div className={styles.commentContent}>
          {editingComment === comment.id ? (
            <Space direction="vertical" style={{ width: '100%' }}>
              <TextArea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={3}
              />
              <Space>
                <Button
                  type="primary"
                  size="small"
                  onClick={() => handleUpdateComment(comment.id)}
                >
                  保存
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    setEditingComment(null)
                    setEditContent('')
                  }}
                >
                  取消
                </Button>
              </Space>
            </Space>
          ) : (
            <Text>{comment.content}</Text>
          )}
        </div>

        {/* 评论位置 */}
        <div style={{ marginBottom: 8 }}>
          <Tag size="small" icon={<PushpinOutlined />}>
            位置: {comment.position.from}-{comment.position.to}
          </Tag>
        </div>

        {/* 评论操作 */}
        <div className={styles.commentActions}>
          <Space size="small">
            {comment.status === 'open' ? (
              <Tooltip title="标记为解决">
                <Button
                  type="text"
                  size="small"
                  icon={<CheckOutlined />}
                  onClick={(e) => {
                    e.stopPropagation()
                    handleResolveComment(comment.id)
                  }}
                >
                  解决
                </Button>
              </Tooltip>
            ) : (
              <Tooltip title="重新打开">
                <Button
                  type="text"
                  size="small"
                  icon={<ExclamationCircleFilled />}
                  onClick={(e) => {
                    e.stopPropagation()
                    handleReopenComment(comment.id)
                  }}
                >
                  重开
                </Button>
              </Tooltip>
            )}

            <Tooltip title="回复">
              <Button
                type="text"
                size="small"
                icon={<MessageOutlined />}
                onClick={(e) => {
                  e.stopPropagation()
                  setReplyingTo(comment.id)
                }}
              >
                回复
              </Button>
            </Tooltip>

            {isOwner && (
              <>
                <Tooltip title="编辑">
                  <Button
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={(e) => {
                      e.stopPropagation()
                      setEditingComment(comment.id)
                      setEditContent(comment.content)
                    }}
                  />
                </Tooltip>

                <Popconfirm
                  title="确定删除这条评论吗？"
                  onConfirm={(e) => {
                    e?.stopPropagation()
                    handleDeleteComment(comment.id)
                  }}
                >
                  <Tooltip title="删除">
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Tooltip>
                </Popconfirm>
              </>
            )}
          </Space>
        </div>

        {/* 回复列表 */}
        {comment.replies.length > 0 && (
          <div style={{ marginTop: 12, paddingLeft: 24 }}>
            {comment.replies.map((reply) => (
              <ReplyItem key={reply.id} reply={reply} />
            ))}
          </div>
        )}

        {/* 回复输入框 */}
        {replyingTo === comment.id && (
          <div style={{ marginTop: 12 }}>
            <TextArea
              placeholder="写下你的回复..."
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              rows={2}
            />
            <Space style={{ marginTop: 8 }}>
              <Button
                type="primary"
                size="small"
                onClick={(e) => {
                  e.stopPropagation()
                  handleAddReply(comment.id)
                }}
              >
                发送
              </Button>
              <Button
                size="small"
                onClick={(e) => {
                  e.stopPropagation()
                  setReplyingTo(null)
                  setReplyContent('')
                }}
              >
                取消
              </Button>
            </Space>
          </div>
        )}
      </div>
    )
  }

  // Tab配置
  const tabItems: TabsProps['items'] = [
    {
      key: 'all',
      label: (
        <span>
          全部
          <Badge count={stats.total} style={{ marginLeft: 4 }} />
        </span>
      ),
    },
    {
      key: 'open',
      label: (
        <span>
          待处理
          <Badge count={stats.open} style={{ marginLeft: 4 }} color="#faad14" />
        </span>
      ),
    },
    {
      key: 'resolved',
      label: (
        <span>
          已解决
          <Badge count={stats.resolved} style={{ marginLeft: 4 }} color="#52c41a" />
        </span>
      ),
    },
    {
      key: 'mine',
      label: '我的',
    },
  ]

  return (
    <Card
      title={
        <Space>
          <CommentOutlined />
          <span>评论</span>
          <Badge count={stats.open} color="#faad14" />
        </Space>
      }
      size="small"
      className={styles.commentSidebar}
    >
      {/* 新建评论区域 */}
      {selectedText && (
        <div style={{ marginBottom: 16, padding: 12, background: '#f6ffed', borderRadius: 8 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            选中文本: {selectedText.text.slice(0, 50)}
            {selectedText.text.length > 50 ? '...' : ''}
          </Text>
          <TextArea
            placeholder="添加评论... 使用 @用户名 提及他人"
            value={newCommentContent}
            onChange={(e) => setNewCommentContent(e.target.value)}
            rows={3}
            style={{ marginTop: 8, marginBottom: 8 }}
          />
          <Button
            type="primary"
            size="small"
            block
            onClick={handleCreateComment}
            disabled={!newCommentContent.trim()}
          >
            添加评论
          </Button>
        </div>
      )}

      {/* 标签页 */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="small"
      />

      {/* 评论列表 */}
      <div className={styles.commentList}>
        {sortedComments.length > 0 ? (
          sortedComments.map(renderCommentItem)
        ) : (
          <Empty description="暂无评论" />
        )}
      </div>
    </Card>
  )
}

// 回复项组件
const ReplyItem: React.FC<{ reply: CommentReply }> = ({ reply }) => {
  return (
    <div className={styles.replyItem}>
      <div className={styles.replyHeader}>
        <Space>
          <Avatar
            size="small"
            style={{ backgroundColor: reply.author.color }}
            src={reply.author.avatar}
          >
            {reply.author.name[0]}
          </Avatar>
          <Text strong style={{ fontSize: 13 }}>{reply.author.name}</Text>
          <Text type="secondary" style={{ fontSize: 11 }}>
            {dayjs(reply.createdAt).fromNow()}
          </Text>
        </Space>
      </div>
      <div className={styles.replyContent}>
        <Text style={{ fontSize: 13 }}>{reply.content}</Text>
      </div>
    </div>
  )
}

export default CommentSidebar
