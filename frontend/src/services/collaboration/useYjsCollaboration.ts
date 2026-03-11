/**
 * Yjs协作Hook
 * 封装YjsDocumentManager，提供React友好的协作功能
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import * as Y from 'yjs'
import { Editor } from '@tiptap/core'

import {
  YjsDocumentManager,
  YjsDocumentManagerFactory,
  UserInfo,
  DocumentMetadata,
} from './YjsDocumentManager'

export interface UseYjsCollaborationOptions {
  documentId: string
  userInfo: UserInfo
  websocketUrl: string
  token?: string
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Error) => void
}

export interface UseYjsCollaborationReturn {
  // 状态
  connected: boolean
  syncing: boolean
  synced: boolean
  users: UserInfo[]
  error: Error | null

  // 文档操作
  getText: () => string
  setText: (text: string) => void
  getMetadata: () => DocumentMetadata | null
  setMetadata: (metadata: Partial<DocumentMetadata>) => void

  // Yjs实例
  ydoc: Y.Doc | null
  ytext: Y.Text | null
  manager: YjsDocumentManager | null

  // 连接控制
  connect: () => Promise<void>
  disconnect: () => void
  reconnect: () => void

  // 版本历史
  createSnapshot: () => Uint8Array | null
  applySnapshot: (snapshot: Uint8Array) => void
}

/**
 * Yjs协作Hook
 */
export function useYjsCollaboration(
  options: UseYjsCollaborationOptions
): UseYjsCollaborationReturn {
  const {
    documentId,
    userInfo,
    websocketUrl,
    token,
    onConnect,
    onDisconnect,
    onError,
  } = options

  // 内部状态
  const [connected, setConnected] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [synced, setSynced] = useState(false)
  const [users, setUsers] = useState<UserInfo[]>([])
  const [error, setError] = useState<Error | null>(null)

  // 引用管理器
  const managerRef = useRef<YjsDocumentManager | null>(null)

  // 获取或创建管理器
  const manager = useMemo(() => {
    return YjsDocumentManagerFactory.getManager(documentId)
  }, [documentId])

  // 保存引用
  useEffect(() => {
    managerRef.current = manager
  }, [manager])

  // 连接函数
  const connect = useCallback(async () => {
    if (!manager || connected) return

    setSyncing(true)
    setError(null)

    try {
      await manager.connect(websocketUrl, userInfo, token)
      setConnected(true)
      onConnect?.()
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error)
      onError?.(error)
    } finally {
      setSyncing(false)
    }
  }, [manager, websocketUrl, userInfo, token, connected, onConnect, onError])

  // 断开连接
  const disconnect = useCallback(() => {
    manager?.disconnect()
    setConnected(false)
    onDisconnect?.()
  }, [manager, onDisconnect])

  // 重新连接
  const reconnect = useCallback(() => {
    manager?.reconnect()
  }, [manager])

  // 文档操作
  const getText = useCallback(() => {
    return manager?.getText() || ''
  }, [manager])

  const setText = useCallback(
    (text: string) => {
      manager?.setText(text)
    },
    [manager]
  )

  const getMetadata = useCallback(() => {
    return manager?.getMetadata() || null
  }, [manager])

  const setMetadata = useCallback(
    (metadata: Partial<DocumentMetadata>) => {
      manager?.setMetadata(metadata)
    },
    [manager]
  )

  // 版本历史
  const createSnapshot = useCallback(() => {
    return manager?.createSnapshot() || null
  }, [manager])

  const applySnapshot = useCallback(
    (snapshot: Uint8Array) => {
      manager?.applySnapshot(snapshot)
    },
    [manager]
  )

  // 监听事件
  useEffect(() => {
    if (!manager) return

    // 监听状态变化
    const unsubscribeStatus = manager.onStatusChange((status) => {
      setConnected(status === 'connected')
      if (status === 'disconnected') {
        onDisconnect?.()
      }
    })

    // 监听同步状态
    const unsubscribeSync = manager.onSyncChange((isSynced) => {
      setSynced(isSynced)
      setSyncing(false)
    })

    // 监听用户变化
    const unsubscribeAwareness = manager.onAwarenessChange(() => {
      const currentUsers = manager.getUsers()
      setUsers(currentUsers)
    })

    return () => {
      unsubscribeStatus()
      unsubscribeSync()
      unsubscribeAwareness()
    }
  }, [manager, onDisconnect])

  // 组件卸载时断开连接
  useEffect(() => {
    return () => {
      // 注意：这里不销毁manager，以便页面切换后能恢复
      manager?.disconnect()
    }
  }, [manager])

  // 自动连接
  useEffect(() => {
    if (!connected && !syncing) {
      connect()
    }
  }, [connected, syncing, connect])

  return {
    // 状态
    connected,
    syncing,
    synced,
    users,
    error,

    // 文档操作
    getText,
    setText,
    getMetadata,
    setMetadata,

    // Yjs实例
    ydoc: manager?.getDoc() || null,
    ytext: manager?.getYText() || null,
    manager,

    // 连接控制
    connect,
    disconnect,
    reconnect,

    // 版本历史
    createSnapshot,
    applySnapshot,
  }
}

/**
 * 为Tiptap编辑器提供Yjs协作支持的Hook
 */
export interface UseYjsTiptapOptions extends UseYjsCollaborationOptions {
  editor: Editor | null
}

export function useYjsTiptap(options: UseYjsTiptapOptions) {
  const { editor, ...collaborationOptions } = options
  const collaboration = useYjsCollaboration(collaborationOptions)

  // 当编辑器准备好后，绑定Yjs
  useEffect(() => {
    if (!editor || !collaboration.manager) return

    // 注意：Tiptap的Collaboration扩展会自动绑定Yjs
    // 这里可以添加额外的同步逻辑

    return () => {
      // 清理逻辑
    }
  }, [editor, collaboration.manager])

  return collaboration
}

/**
 * 批量更新用户光标位置
 */
export function useAwarenessCursors(manager: YjsDocumentManager | null) {
  const [cursors, setCursors] = useState<Map<number, any>>(new Map())

  useEffect(() => {
    if (!manager) return

    const awareness = manager.getAwareness()
    if (!awareness) return

    const updateCursors = () => {
      const states = awareness.getStates()
      const cursorMap = new Map<number, any>()

      states.forEach((state, clientId) => {
        if (state.cursor || state.selection) {
          cursorMap.set(clientId, {
            user: state.user,
            cursor: state.cursor,
            selection: state.selection,
          })
        }
      })

      setCursors(cursorMap)
    }

    awareness.on('change', updateCursors)
    updateCursors()

    return () => {
      awareness.off('change', updateCursors)
    }
  }, [manager])

  /**
   * 更新当前用户光标位置
   */
  const updateCursor = useCallback(
    (position: { index: number; length: number } | null) => {
      const awareness = manager?.getAwareness()
      if (!awareness) return

      if (position) {
        awareness.setLocalStateField('cursor', position)
      } else {
        const state = awareness.getLocalState()
        if (state) {
          delete state.cursor
          awareness.setLocalState(state)
        }
      }
    },
    [manager]
  )

  return { cursors, updateCursor }
}

export default useYjsCollaboration
