/**
 * 评论线程组件
 * 显示单条评论及其回复
 */

import React, { useState } from 'react'
import { Card, Avatar, Typography, Space, Button, Input, Dropdown, Tag } from 'antd'
import {
  UserOutlined,
  LikeOutlined,
  CheckCircleOutlined,
  MoreOutlined,
  DeleteOutlined,
  RollbackOutlined,
  SendOutlined,
} from '@ant-design/icons'

import type { Comment, CommentReply } from '@/types/comment'
import styles from './Comments.module.css'

const { Text, Paragraph } = Typography
const { TextArea } = Input

interface CommentThreadProps {
  comment: Comment
  onResolve?: (commentId: string) => void
  onReopen?: (commentId: string) => void
  onDelete?: (commentId: string) => void
  onReply?: (commentId: string, content: string) => void
  onDeleteReply?: (commentId: string, replyId: string) => void
}

const CommentThread: React.FC<CommentThreadProps> = ({
  comment,
  onResolve,
  onReopen,
  onDelete,
  onReply,
  onDeleteReply,
}) => {
  const [replyVisible, setReplyVisible] = useState(false)
  const [replyContent, setReplyContent] = useState('')
  const [replySubmitting, setReplySubmitting] = useState(false)

  const handleReply = async () => {
    if (!replyContent.trim()) return
    setReplySubmitting(true)
    try {
      onReply?.(comment.id, replyContent.trim())
      setReplyContent('')
      setReplyVisible(false)
    } finally {
      setReplySubmitting(false)
    }
  }

  const menuItems = [
    {
      key: 'resolve',
      label: comment.resolved ? '重新打开' : '标记为已解决',
      icon: comment.resolved ? <RollbackOutlined /> : <CheckCircleOutlined />,
      onClick: () => comment.resolved ? onReopen?.(comment.id) : onResolve?.(comment.id),
    },
    {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: () => onDelete?.(comment.id),
    },
  ]

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes} 分钟前`
    if (hours < 24) return `${hours} 小时前`
    if (days < 7) return `${days} 天前`
    return date.toLocaleDateString()
  }

  return (
    <Card
      size="small"
      className={`${styles.commentCard} ${comment.resolved ? styles.resolved : ''}`}
    >
      {/* 评论头部 */}
      <div className={styles.commentHeader}>
        <Space>
          <Avatar
            size="small"
            icon={<UserOutlined />}
            src={comment.userAvatar}
            style={{ backgroundColor: comment.userAvatar ? undefined : '#1890ff' }}
          >
            {comment.userName.charAt(0)}
          </Avatar>
          <Text strong>{comment.userName}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {formatTime(comment.createdAt)}
          </Text>
        </Space>
        <Space>
          {comment.resolved && (
            <Tag icon={<CheckCircleOutlined />} color="success">
              已解决
            </Tag>
          )}
          <Dropdown menu={{ items: menuItems }} trigger={['click']}>
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      </div>

      {/* 引用文本 */}
      {comment.position.selectedText && (
        <div className={styles.quoteText}>
          <Text type="secondary" italic>
            "{comment.position.selectedText}"
          </Text>
        </div>
      )}

      {/* 评论内容 */}
      <Paragraph className={styles.commentContent}>
        {comment.content}
      </Paragraph>

      {/* 评论操作 */}
      <div className={styles.commentActions}>
        <Space>
          <Button
            type="text"
            size="small"
            icon={<LikeOutlined />}
          >
            赞同
          </Button>
          <Button
            type="text"
            size="small"
            onClick={() => setReplyVisible(!replyVisible)}
          >
            回复
          </Button>
          {!comment.resolved && (
            <Button
              type="text"
              size="small"
              icon={<CheckCircleOutlined />}
              onClick={() => onResolve?.(comment.id)}
            >
              解决
            </Button>
          )}
        </Space>
      </div>

      {/* 回复列表 */}
      {comment.replies && comment.replies.length > 0 && (
        <div className={styles.repliesList}>
          {comment.replies.map((reply) => (
            <ReplyItem
              key={reply.id}
              reply={reply}
              onDelete={() => onDeleteReply?.(comment.id, reply.id)}
            />
          ))}
        </div>
      )}

      {/* 回复输入框 */}
      {replyVisible && (
        <div className={styles.replyInput}>
          <TextArea
            rows={2}
            placeholder="输入回复..."
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault()
                handleReply()
              }
            }}
          />
          <div className={styles.replyActions}>
            <Button size="small" onClick={() => setReplyVisible(false)}>
              取消
            </Button>
            <Button
              type="primary"
              size="small"
              icon={<SendOutlined />}
              onClick={handleReply}
              loading={replySubmitting}
              disabled={!replyContent.trim()}
            >
              发送
            </Button>
          </div>
        </div>
      )}
    </Card>
  )
}

// 回复项组件
interface ReplyItemProps {
  reply: CommentReply
  onDelete?: () => void
}

const ReplyItem: React.FC<ReplyItemProps> = ({ reply, onDelete }) => {
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)

    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes} 分钟前`
    if (hours < 24) return `${hours} 小时前`
    return date.toLocaleDateString()
  }

  return (
    <div className={styles.replyItem}>
      <div className={styles.replyHeader}>
        <Space size={4}>
          <Avatar
            size="small"
            icon={<UserOutlined />}
            src={reply.userAvatar}
            style={{ width: 20, height: 20, fontSize: 10 }}
          >
            {reply.userName.charAt(0)}
          </Avatar>
          <Text strong style={{ fontSize: 12 }}>{reply.userName}</Text>
          <Text type="secondary" style={{ fontSize: 11 }}>
            {formatTime(reply.createdAt)}
          </Text>
        </Space>
        <Button
          type="text"
          size="small"
          icon={<DeleteOutlined />}
          danger
          onClick={onDelete}
          style={{ fontSize: 12 }}
        />
      </div>
      <Text style={{ fontSize: 13 }}>{reply.content}</Text>
    </div>
  )
}

export default CommentThread
