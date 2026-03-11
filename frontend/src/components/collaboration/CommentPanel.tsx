/**
 * 评论面板组件
 * 显示和管理文档评论
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  List,
  Input,
  Button,
  Avatar,
  Space,
  Typography,
  Badge,
  Popconfirm,
  Empty,
  Tooltip,
  Tag,
} from 'antd'
import {
  MessageOutlined,
  SendOutlined,
  CheckOutlined,
  DeleteOutlined,
  EditOutlined,
  CloseOutlined,
} from '@ant-design/icons'

const { Text, TextArea } = Input
const { Title } = Typography

interface Comment {
  id: string
  user_id: string
  user_name: string
  content: string
  created_at: string
  resolved: boolean
  selection?: string
  position?: {
    from: number
    to: number
  }
  replies?: Comment[]
}

interface CommentPanelProps {
  documentId: string
  currentUser: {
    id: string
    name: string
  }
  comments?: Comment[]
  onAddComment?: (content: string, selection?: string) => void
  onResolve?: (commentId: string) => void
  onDelete?: (commentId: string) => void
  onReply?: (commentId: string, content: string) => void
}

export const CommentPanel: React.FC<CommentPanelProps> = ({
  documentId,
  currentUser,
  comments = [],
  onAddComment,
  onResolve,
  onDelete,
  onReply,
}) => {
  const [newComment, setNewComment] = useState('')
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const [replyContent, setReplyContent] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')

  const unresolvedCount = comments.filter((c) => !c.resolved).length

  const handleSubmit = () => {
    if (!newComment.trim()) return
    onAddComment?.(newComment)
    setNewComment('')
  }

  const handleReply = (commentId: string) => {
    if (!replyContent.trim()) return
    onReply?.(commentId, replyContent)
    setReplyContent('')
    setReplyingTo(null)
  }

  return (
    <Card
      title={
        <Space>
          <MessageOutlined />
          <span>评论与批注</span>
          {unresolvedCount > 0 && (
            <Badge count={unresolvedCount} style={{ backgroundColor: '#ff4d4f' }} />
          )}
        </Space>
      }
      bodyStyle={{ padding: 0, maxHeight: 600, overflow: 'auto' }}
    >
      {/* 添加新评论 */}
      <div style={{ padding: 16, borderBottom: '1px solid #f0f0f0' }}>
        <TextArea
          placeholder="添加评论..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          rows={3}
          style={{ marginBottom: 8 }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSubmit}
          disabled={!newComment.trim()}
          block
        >
          发表评论
        </Button>
      </div>

      {/* 评论列表 */}
      <List
        dataSource={comments}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无评论，发表第一条评论吧"
            />
          ),
        }}
        renderItem={(comment) => (
          <List.Item
            key={comment.id}
            style={{
              padding: 16,
              backgroundColor: comment.resolved ? '#f6ffed' : '#fff',
              borderBottom: '1px solid #f0f0f0',
              opacity: comment.resolved ? 0.7 : 1,
            }}
          >
            <div style={{ width: '100%' }}>
              {/* 评论头部 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <Space>
                  <Avatar size="small">{comment.user_name[0]}</Avatar>
                  <Text strong>{comment.user_name}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {new Date(comment.created_at).toLocaleString()}
                  </Text>
                  {comment.resolved && <Tag color="success">已解决</Tag>}
                </Space>

                <Space>
                  {!comment.resolved && (
                    <Tooltip title="标记为已解决">
                      <Button
                        type="text"
                        size="small"
                        icon={<CheckOutlined />}
                        onClick={() => onResolve?.(comment.id)}
                      />
                    </Tooltip>
                  )}
                  <Tooltip title="删除">
                    <Popconfirm
                      title="确定删除此评论？"
                      onConfirm={() => onDelete?.(comment.id)}
                    >
                      <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                    </Popconfirm>
                  </Tooltip>
                </Space>
              </div>

              {/* 选中的文本 */}
              {comment.selection && (
                <div
                  style={{
                    padding: 8,
                    backgroundColor: '#fffbe6',
                    borderLeft: '3px solid #faad14',
                    marginBottom: 8,
                    fontStyle: 'italic',
                    fontSize: 12,
                  }}
                >
                  "{comment.selection}"
                </div>
              )}

              {/* 评论内容 */}
              <div style={{ marginBottom: 8 }}>{comment.content}</div>

              {/* 回复按钮 */}
              <Button
                type="link"
                size="small"
                onClick={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
              >
                {replyingTo === comment.id ? '取消回复' : '回复'}
              </Button>

              {/* 回复输入框 */}
              {replyingTo === comment.id && (
                <div style={{ marginTop: 8, marginLeft: 24 }}>
                  <TextArea
                    placeholder="回复评论..."
                    value={replyContent}
                    onChange={(e) => setReplyContent(e.target.value)}
                    rows={2}
                    style={{ marginBottom: 8 }}
                  />
                  <Space>
                    <Button
                      type="primary"
                      size="small"
                      onClick={() => handleReply(comment.id)}
                    >
                      发送
                    </Button>
                    <Button size="small" onClick={() => setReplyingTo(null)}>取消</Button>
                  </Space>
                </div>
              )}

              {/* 回复列表 */}
              {comment.replies && comment.replies.length > 0 && (
                <div style={{ marginTop: 8, marginLeft: 24 }}>
                  {comment.replies.map((reply) => (
                    <div
                      key={reply.id}
                      style={{
                        padding: 8,
                        backgroundColor: '#f5f5f5',
                        borderRadius: 4,
                        marginBottom: 8,
                      }}
                    >
                      <Space>
                        <Text strong style={{ fontSize: 12 }}>{reply.user_name}</Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {new Date(reply.created_at).toLocaleString()}
                        </Text>
                      </Space>
                      <div style={{ fontSize: 13, marginTop: 4 }}>{reply.content}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </List.Item>
        )}
      />
    </Card>
  )
}

export default CommentPanel
