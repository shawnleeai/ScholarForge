/**
 * 对话历史侧边栏组件
 * 显示历史会话列表，支持搜索和管理
 */

import React, { useState, useCallback } from 'react'
import {
  List,
  Button,
  Input,
  Empty,
  Dropdown,
  Modal,
  message,
  Tooltip,
  Badge,
  Skeleton,
  Typography,
  Space,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  MoreOutlined,
  DeleteOutlined,
  EditOutlined,
  PushpinOutlined,
  MessageOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import styles from './ChatHistory.module.css'

const { Text, Paragraph } = Typography

export interface Conversation {
  id: string
  title: string
  status: 'active' | 'archived' | 'deleted'
  messageCount: number
  lastMessageAt: string
  createdAt: string
  context?: {
    researchField?: string
    researchQuestion?: string
    paperIds?: string[]
    articleIds?: string[]
  }
}

interface ChatHistoryProps {
  currentConversationId?: string
  onSelectConversation: (id: string) => void
  onCreateConversation: () => void
  onDeleteConversation?: (id: string) => void
  onRenameConversation?: (id: string, newTitle: string) => void
}

const ChatHistory: React.FC<ChatHistoryProps> = ({
  currentConversationId,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
  onRenameConversation,
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const queryClient = useQueryClient()

  // 获取会话列表
  const { data: conversationsData, isLoading } = useQuery({
    queryKey: ['conversations', searchQuery],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/ai/chat?limit=50&search=${encodeURIComponent(searchQuery)}`
      )
      const data = await response.json()
      return data.data as {
        conversations: Conversation[]
        total: number
      }
    },
  })

  const conversations = conversationsData?.conversations || []

  // 删除会话
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await fetch(`/api/v1/ai/chat/${id}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('删除失败')
      return id
    },
    onSuccess: (id) => {
      message.success('会话已删除')
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      onDeleteConversation?.(id)
    },
    onError: () => {
      message.error('删除失败')
    },
  })

  // 重命名会话
  const renameMutation = useMutation({
    mutationFn: async ({ id, title }: { id: string; title: string }) => {
      const response = await fetch(`/api/v1/ai/chat/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      })
      if (!response.ok) throw new Error('重命名失败')
      return { id, title }
    },
    onSuccess: ({ id, title }) => {
      message.success('重命名成功')
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      onRenameConversation?.(id, title)
      setEditingId(null)
    },
    onError: () => {
      message.error('重命名失败')
    },
  })

  // 处理删除
  const handleDelete = useCallback(
    (id: string, title: string) => {
      Modal.confirm({
        title: '删除会话',
        content: `确定要删除 "${title}" 吗？此操作不可恢复。`,
        okText: '删除',
        okType: 'danger',
        cancelText: '取消',
        onOk: () => deleteMutation.mutate(id),
      })
    },
    [deleteMutation]
  )

  // 处理重命名
  const handleRename = useCallback((conv: Conversation) => {
    setEditingId(conv.id)
    setEditingTitle(conv.title)
  }, [])

  // 保存重命名
  const saveRename = useCallback(() => {
    if (editingId && editingTitle.trim()) {
      renameMutation.mutate({ id: editingId, title: editingTitle.trim() })
    } else {
      setEditingId(null)
    }
  }, [editingId, editingTitle, renameMutation])

  // 操作菜单
  const getDropdownItems = useCallback(
    (conv: Conversation) => [
      {
        key: 'rename',
        icon: <EditOutlined />,
        label: '重命名',
        onClick: () => handleRename(conv),
      },
      {
        key: 'delete',
        icon: <DeleteOutlined />,
        label: '删除',
        danger: true,
        onClick: () => handleDelete(conv.id, conv.title),
      },
    ],
    [handleDelete, handleRename]
  )

  // 格式化时间
  const formatTime = useCallback((dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), {
        addSuffix: true,
        locale: zhCN,
      })
    } catch {
      return dateString
    }
  }, [])

  return (
    <div className={styles.chatHistory}>
      {/* 头部 */}
      <div className={styles.header}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={onCreateConversation}
          className={styles.newChatButton}
        >
          新对话
        </Button>
      </div>

      {/* 搜索 */}
      <div className={styles.searchBox}>
        <Input
          placeholder="搜索对话历史..."
          prefix={<SearchOutlined />}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          allowClear
        />
      </div>

      {/* 会话列表 */}
      <div className={styles.conversationList}>
        {isLoading ? (
          <div className={styles.loading}>
            <Skeleton active paragraph={{ rows: 5 }} />
          </div>
        ) : conversations.length === 0 ? (
          <Empty
            description={searchQuery ? '没有找到匹配的对话' : '暂无对话历史'}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            className={styles.empty}
          />
        ) : (
          <List
            dataSource={conversations}
            renderItem={(conv) => (
              <List.Item
                className={`${styles.conversationItem} ${
                  conv.id === currentConversationId ? styles.active : ''
                }`}
                onClick={() => onSelectConversation(conv.id)}
                actions={[
                  <Dropdown
                    key="more"
                    menu={{ items: getDropdownItems(conv) }}
                    trigger={['click']}
                    placement="bottomRight"
                  >
                    <Button
                      type="text"
                      size="small"
                      icon={<MoreOutlined />}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Dropdown>,
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <Badge
                      count={conv.messageCount}
                      offset={[-4, 4]}
                      size="small"
                    >
                      <div className={styles.avatar}>
                        <MessageOutlined />
                      </div>
                    </Badge>
                  }
                  title={
                    editingId === conv.id ? (
                      <Input
                        size="small"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onBlur={saveRename}
                        onPressEnter={saveRename}
                        onClick={(e) => e.stopPropagation()}
                        autoFocus
                      />
                    ) : (
                      <Text
                        ellipsis={{ tooltip: true }}
                        className={styles.conversationTitle}
                      >
                        {conv.title}
                      </Text>
                    )
                  }
                  description={
                    <Space size="small" className={styles.metaInfo}>
                      <Tooltip title={new Date(conv.lastMessageAt).toLocaleString()}>
                        <Text type="secondary" className={styles.time}>
                          <ClockCircleOutlined /> {formatTime(conv.lastMessageAt)}
                        </Text>
                      </Tooltip>
                      {conv.context?.researchField && (
                        <Text type="secondary" className={styles.field}>
                          · {conv.context.researchField}
                        </Text>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </div>

      {/* 底部信息 */}
      <div className={styles.footer}>
        <Text type="secondary" className={styles.footerText}>
          共 {conversationsData?.total || 0} 个对话
        </Text>
      </div>
    </div>
  )
}

export default ChatHistory
