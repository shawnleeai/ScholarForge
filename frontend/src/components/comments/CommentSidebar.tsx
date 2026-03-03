/**
 * 评论侧边栏组件
 * 显示论文的所有评论列表
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Drawer, List, Button, Typography, Tabs, Empty, Spin, Badge, Tag } from 'antd'
import {
  CommentOutlined,
  FilterOutlined,
} from '@ant-design/icons'

import type { Comment } from '@/types/comment'
import { commentService } from '@/services/commentService'
import CommentThread from './CommentThread'
import styles from './Comments.module.css'

const {} = Typography

interface CommentSidebarProps {
  visible: boolean
  paperId: string
  sectionId?: string
  onClose: () => void
  onCommentClick?: (comment: Comment) => void
}

const CommentSidebar: React.FC<CommentSidebarProps> = ({
  visible,
  paperId,
  sectionId,
  onClose,
  onCommentClick,
}) => {
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('all')
  const [filter, setFilter] = useState<'all' | 'unresolved' | 'resolved'>('all')

  // 加载评论
  const loadComments = useCallback(async () => {
    if (!paperId) return
    setLoading(true)
    try {
      const response = await commentService.getComments(paperId, sectionId)
      setComments(response.data)
    } catch (error) {
      console.error('Failed to load comments:', error)
    } finally {
      setLoading(false)
    }
  }, [paperId, sectionId])

  useEffect(() => {
    if (visible) {
      loadComments()
    }
  }, [visible, loadComments])

  // 处理解决评论
  const handleResolve = async (commentId: string) => {
    try {
      await commentService.resolveComment(paperId, commentId)
      loadComments()
    } catch (error) {
      console.error('Failed to resolve comment:', error)
    }
  }

  // 处理重新打开评论
  const handleReopen = async (commentId: string) => {
    try {
      await commentService.reopenComment(paperId, commentId)
      loadComments()
    } catch (error) {
      console.error('Failed to reopen comment:', error)
    }
  }

  // 处理删除评论
  const handleDelete = async (commentId: string) => {
    try {
      await commentService.deleteComment(paperId, commentId)
      loadComments()
    } catch (error) {
      console.error('Failed to delete comment:', error)
    }
  }

  // 处理回复
  const handleReply = async (commentId: string, content: string) => {
    try {
      await commentService.createReply(paperId, commentId, { commentId, content })
      loadComments()
    } catch (error) {
      console.error('Failed to reply:', error)
    }
  }

  // 处理删除回复
  const handleDeleteReply = async (commentId: string, replyId: string) => {
    try {
      await commentService.deleteReply(paperId, commentId, replyId)
      loadComments()
    } catch (error) {
      console.error('Failed to delete reply:', error)
    }
  }

  // 过滤评论
  const filteredComments = comments.filter((comment) => {
    if (filter === 'unresolved') return !comment.resolved
    if (filter === 'resolved') return comment.resolved
    return true
  })

  // 统计
  const unresolvedCount = comments.filter(c => !c.resolved).length
  const resolvedCount = comments.filter(c => c.resolved).length

  const tabItems = [
    {
      key: 'all',
      label: (
        <span>
          全部
          <Badge count={comments.length} size="small" style={{ marginLeft: 4 }} />
        </span>
      ),
    },
    {
      key: 'unresolved',
      label: (
        <span>
          待处理
          {unresolvedCount > 0 && (
            <Badge count={unresolvedCount} size="small" style={{ marginLeft: 4 }} />
          )}
        </span>
      ),
    },
    {
      key: 'resolved',
      label: (
        <span>
          已解决
          <Badge count={resolvedCount} size="small" style={{ marginLeft: 4, backgroundColor: '#52c41a' }} />
        </span>
      ),
    },
  ]

  return (
    <Drawer
      title={
        <span>
          <CommentOutlined style={{ marginRight: 8 }} />
          评论与批注
          {unresolvedCount > 0 && (
            <Tag color="orange" style={{ marginLeft: 8 }}>{unresolvedCount} 条待处理</Tag>
          )}
        </span>
      }
      placement="right"
      onClose={onClose}
      open={visible}
      width={400}
      extra={
        <Button
          icon={<FilterOutlined />}
          size="small"
          onClick={() => setFilter(filter === 'all' ? 'unresolved' : 'all')}
        >
          {filter === 'all' ? '待处理' : '全部'}
        </Button>
      }
    >
      <Tabs
        activeKey={activeTab}
        onChange={(key) => {
          setActiveTab(key)
          setFilter(key as 'all' | 'unresolved' | 'resolved')
        }}
        items={tabItems}
        size="small"
        className={styles.tabs}
      />

      {loading ? (
        <div className={styles.loading}>
          <Spin />
        </div>
      ) : filteredComments.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={filter === 'unresolved' ? '没有待处理的评论' : '暂无评论'}
        />
      ) : (
        <List
          className={styles.commentList}
          dataSource={filteredComments}
          renderItem={(comment) => (
            <div
              className={styles.commentItem}
              onClick={() => onCommentClick?.(comment)}
            >
              <CommentThread
                comment={comment}
                onResolve={handleResolve}
                onReopen={handleReopen}
                onDelete={handleDelete}
                onReply={handleReply}
                onDeleteReply={handleDeleteReply}
              />
            </div>
          )}
        />
      )}
    </Drawer>
  )
}

export default CommentSidebar
