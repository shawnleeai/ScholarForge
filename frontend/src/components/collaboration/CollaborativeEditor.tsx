/**
 * 增强版协作编辑器组件 (集成评论系统)
 * 基于Yjs CRDT的实时协作编辑
 * 特性：
 * - 多用户实时同步
 * - 光标/选区显示
 * - 版本历史
 * - 行内评论系统
 * - 离线支持
 * - IndexedDB持久化
 */

import React, { useEffect, useState, useCallback, useRef } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Collaboration from '@tiptap/extension-collaboration'
import CollaborationCursor from '@tiptap/extension-collaboration-cursor'
import Placeholder from '@tiptap/extension-placeholder'
import { Card, Avatar, Space, Tag, Badge, Button, Tooltip, message, Spin, Row, Col } from 'antd'
import { TeamOutlined, SyncOutlined, DisconnectOutlined, HistoryOutlined, CommentOutlined } from '@ant-design/icons'

import {
  YjsDocumentManager,
  YjsDocumentManagerFactory,
  VersionManager,
  UserInfo,
  formatVersionTime,
} from '../../services/collaboration'
import { CommentManager, CommentManagerFactory, CommentAuthor } from '../../services/collaboration/CommentManager'
import { VersionHistoryPanel } from './VersionHistoryPanel'
import { CommentSidebar } from './CommentSidebar'
import styles from './Collaboration.module.css'

interface CollaborativeEditorProps {
  documentId: string
  currentUser: UserInfo
  placeholder?: string
  onSave?: (content: string) => void
}

// 生成用户颜色
const generateUserColor = (userId: string): string => {
  const colors = [
    '#F87171', '#FB923C', '#FBBF24', '#A3E635', '#34D399',
    '#22D3EE', '#60A5FA', '#818CF8', '#A78BFA', '#F472B6',
  ]
  let hash = 0
  for (let i = 0; i < userId.length; i++) {
    hash = userId.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

export const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  documentId,
  currentUser,
  placeholder = '开始协作写作...',
  onSave,
}) => {
  // 状态
  const [connected, setConnected] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [synced, setSynced] = useState(false)
  const [users, setUsers] = useState<UserInfo[]>([])
  const [error, setError] = useState<Error | null>(null)
  const [showVersionPanel, setShowVersionPanel] = useState(false)
  const [showCommentSidebar, setShowCommentSidebar] = useState(true)

  // 选中状态（用于评论）
  const [selectedText, setSelectedText] = useState<{
    from: number
    to: number
    text: string
  } | null>(null)

  // 引用
  const managerRef = useRef<YjsDocumentManager | null>(null)
  const versionManagerRef = useRef<VersionManager | null>(null)
  const commentManagerRef = useRef<CommentManager | null>(null)
  const autoSaveIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const changeCountRef = useRef(0)
  const editorRef = useRef<HTMLDivElement>(null)

  // 获取或创建Yjs文档管理器
  useEffect(() => {
    const manager = YjsDocumentManagerFactory.getManager(documentId)
    managerRef.current = manager

    // 创建版本管理器
    versionManagerRef.current = new VersionManager(manager.getDoc(), documentId)

    // 创建评论管理器 - 复用同一个Y.Doc
    commentManagerRef.current = CommentManagerFactory.getManager(documentId, manager.getDoc())

    return () => {
      manager.disconnect()
    }
  }, [documentId])

  // 连接到协作服务器
  useEffect(() => {
    const manager = managerRef.current
    if (!manager) return

    const connect = async () => {
      setSyncing(true)

      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
      const token = localStorage.getItem('scholarforge-auth')
        ? JSON.parse(localStorage.getItem('scholarforge-auth')!).accessToken
        : ''

      const userWithColor = {
        ...currentUser,
        color: currentUser.color || generateUserColor(currentUser.id),
      }

      try {
        await manager.connect(wsUrl, userWithColor, token)
        message.success('已连接到协作服务器')
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err))
        setError(error)
        message.error(`连接失败: ${error.message}`)
      } finally {
        setSyncing(false)
      }
    }

    connect()

    const unsubscribeStatus = manager.onStatusChange((status) => {
      setConnected(status === 'connected')
      if (status === 'disconnected') {
        message.warning('连接已断开，正在尝试重连...')
      }
    })

    const unsubscribeSync = manager.onSyncChange((isSynced) => {
      setSynced(isSynced)
    })

    const unsubscribeAwareness = manager.onAwarenessChange(() => {
      const currentUsers = manager.getUsers()
      setUsers(currentUsers)
    })

    return () => {
      unsubscribeStatus()
      unsubscribeSync()
      unsubscribeAwareness()
    }
  }, [documentId, currentUser])

  // 创建Tiptap编辑器
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        history: false,
      }),
      Collaboration.configure({
        document: managerRef.current?.getDoc(),
      }),
      CollaborationCursor.configure({
        provider: managerRef.current?.getProvider(),
        user: {
          name: currentUser.name,
          color: currentUser.color || generateUserColor(currentUser.id),
        },
      }),
      Placeholder.configure({
        placeholder,
      }),
    ],
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none',
      },
      handleDOMEvents: {
        mouseup: (view) => {
          // 检测选中文本
          const { state } = view
          const { selection } = state
          const { from, to } = selection

          if (from !== to) {
            const text = state.doc.textBetween(from, to, ' ')
            setSelectedText({ from, to, text })
          } else {
            setSelectedText(null)
          }
          return false
        },
      },
    },
    onUpdate: ({ editor }) => {
      onSave?.(editor.getHTML())

      changeCountRef.current++
      if (changeCountRef.current >= 100) {
        const versionManager = versionManagerRef.current
        if (versionManager) {
          const currentText = managerRef.current?.getText() || ''
          if (currentText.length >= 10) {
            versionManager.createVersion(
              currentUser.name,
              currentUser.id,
              '自动保存(100次变更)'
            )
            changeCountRef.current = 0
          }
        }
      }
    },
  })

  // 处理重新连接
  const handleReconnect = useCallback(() => {
    managerRef.current?.reconnect()
  }, [])

  // 处理断开连接
  const handleDisconnect = useCallback(() => {
    managerRef.current?.disconnect()
    message.info('已断开连接')
  }, [])

  // 自动保存版本
  const autoSaveVersion = useCallback(() => {
    const versionManager = versionManagerRef.current
    if (!versionManager) return

    const currentText = managerRef.current?.getText() || ''
    if (currentText.length < 10) return

    const version = versionManager.createVersion(
      currentUser.name,
      currentUser.id,
      '自动保存'
    )

    console.log(`[AutoSave] 版本已保存: ${formatVersionTime(version.timestamp)}`)
    changeCountRef.current = 0
  }, [currentUser])

  // 设置自动保存定时器
  useEffect(() => {
    if (!connected) return

    autoSaveIntervalRef.current = setInterval(() => {
      autoSaveVersion()
    }, 5 * 60 * 1000)

    return () => {
      if (autoSaveIntervalRef.current) {
        clearInterval(autoSaveIntervalRef.current)
      }
    }
  }, [connected, autoSaveVersion])

  // 创建版本快照
  const handleCreateVersion = useCallback(() => {
    const versionManager = versionManagerRef.current
    if (!versionManager) return

    const version = versionManager.createVersion(
      currentUser.name,
      currentUser.id,
      '手动保存版本'
    )

    message.success(`版本已保存: ${formatVersionTime(version.timestamp)}`)
  }, [currentUser])

  // 显示版本面板
  const handleShowVersions = useCallback(() => {
    setShowVersionPanel(true)
  }, [])

  // 处理评论选择（高亮文本）
  const handleSelectComment = useCallback((commentId: string, position: { from: number; to: number }) => {
    if (!editor) return

    // 设置编辑器选区
    editor.chain().focus().setTextSelection({ from: position.from, to: position.to }).run()
  }, [editor])

  // 统计
  const stats = versionManagerRef.current?.getStats()
  const commentStats = commentManagerRef.current?.getStats()

  // 转换UserInfo为CommentAuthor
  const currentCommentAuthor: CommentAuthor = {
    id: currentUser.id,
    name: currentUser.name,
    color: currentUser.color || generateUserColor(currentUser.id),
    avatar: currentUser.avatar,
  }

  return (
    <Card
      className={styles.collaborativeEditor}
      title={
        <Space>
          <span>协作编辑</span>
          <Badge
            status={connected ? 'success' : 'error'}
            text={connected ? '已连接' : '未连接'}
          />
          {syncing && <Spin size="small" />}
          {synced && <Tag color="blue" icon={<SyncOutlined />}>已同步</Tag>}
          {stats && stats.totalVersions > 0 && (
            <Tag color="purple">
              <HistoryOutlined /> {stats.totalVersions} 个版本
            </Tag>
          )}
          {commentStats && commentStats.open > 0 && (
            <Tag color="orange">
              <CommentOutlined /> {commentStats.open} 条评论
            </Tag>
          )}
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="评论">
            <Button
              icon={<CommentOutlined />}
              onClick={() => setShowCommentSidebar(!showCommentSidebar)}
              type={showCommentSidebar ? 'primary' : 'default'}
              size="small"
            >
              {commentStats?.open || 0}
            </Button>
          </Tooltip>
          <Tooltip title="保存版本">
            <Button
              icon={<HistoryOutlined />}
              onClick={handleCreateVersion}
              size="small"
            >
              保存版本
            </Button>
          </Tooltip>
          <Tooltip title="版本历史">
            <Button
              icon={<HistoryOutlined />}
              onClick={handleShowVersions}
              size="small"
            >
              历史
            </Button>
          </Tooltip>
          <Tooltip title="协作用户">
            <Button icon={<TeamOutlined />} size="small">
              {users.length} 人在线
            </Button>
          </Tooltip>
          {connected ? (
            <Button
              icon={<DisconnectOutlined />}
              onClick={handleDisconnect}
              danger
              size="small"
            >
              断开
            </Button>
          ) : (
            <Button
              icon={<SyncOutlined />}
              onClick={handleReconnect}
              type="primary"
              size="small"
            >
              重连
            </Button>
          )}
        </Space>
      }
    >
      {/* 在线用户头像 */}
      {users.length > 0 && (
        <div className={styles.userBar}>
          <Space>
            <TeamOutlined />
            <span>在线用户:</span>
            <Avatar.Group
              maxCount={5}
              maxStyle={{ color: '#f56a00', backgroundColor: '#fde3cf' }}
            >
              {users.map((user) => (
                <Tooltip key={user.id} title={user.name}>
                  <Avatar
                    style={{ backgroundColor: user.color }}
                    src={user.avatar}
                  >
                    {user.name[0]}
                  </Avatar>
                </Tooltip>
              ))}
            </Avatar.Group>
          </Space>
        </div>
      )}

      {/* 编辑器主体区域 */}
      <Row gutter={16}>
        <Col flex={showCommentSidebar ? '1' : '100%'}>
          <div className={styles.editorContainer} ref={editorRef}>
            {editor && <EditorContent editor={editor} />}
          </div>
        </Col>

        {/* 评论侧边栏 */}
        {showCommentSidebar && commentManagerRef.current && (
          <Col flex="320px">
            <CommentSidebar
              commentManager={commentManagerRef.current}
              currentUser={currentCommentAuthor}
              documentId={documentId}
              selectedText={selectedText}
              onSelectComment={handleSelectComment}
            />
          </Col>
        )}
      </Row>

      {/* 版本历史面板 */}
      {showVersionPanel && managerRef.current && versionManagerRef.current && (
        <VersionHistoryPanel
          versionManager={versionManagerRef.current}
          ydoc={managerRef.current.getDoc()}
          currentUser={currentUser}
          onClose={() => setShowVersionPanel(false)}
          visible={showVersionPanel}
        />
      )}
    </Card>
  )
}

export default CollaborativeEditor
