/**
 * 实时协作服务
 * 基于 Yjs 实现，支持断线重连和离线存储
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
import { IndexeddbPersistence } from 'y-indexeddb'

export interface CollaborationUser {
  id: string
  name: string
  color: string
  clientId: number
}

export interface CursorPosition {
  sectionId: string
  position: number
  selection?: { from: number; to: number }
}

export interface CollaborationConfig {
  /** WebSocket 服务器地址 */
  serverUrl?: string
  /** 是否启用离线支持 */
  enableOffline?: boolean
  /** 重连间隔（毫秒） */
  reconnectInterval?: number
  /** 最大重连次数 */
  maxReconnectAttempts?: number
}

const COLORS = [
  '#f5222d', '#fa8c16', '#fadb14', '#52c41a', '#13c2c2',
  '#1890ff', '#722ed1', '#eb2f96', '#faad14', '#a0d911',
]

/**
 * 获取用户颜色
 */
export function getUserColor(index: number): string {
  return COLORS[index % COLORS.length]
}

/**
 * 默认配置
 */
const defaultConfig: CollaborationConfig = {
  serverUrl: import.meta.env.VITE_WS_SERVER || 'wss://ws.scholarforge.io',
  enableOffline: true,
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
}

/**
 * 协作管理器类
 */
export class CollaborationManager {
  private doc: Y.Doc | null = null
  private provider: WebsocketProvider | null = null
  private persistence: IndexeddbPersistence | null = null
  private config: CollaborationConfig
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private roomId: string = ''
  private user: { id: string; name: string } | null = null

  // 状态回调
  private onConnectionChange?: (connected: boolean) => void
  private onUsersChange?: (users: CollaborationUser[]) => void
  private onError?: (error: Error) => void

  constructor(config: CollaborationConfig = {}) {
    this.config = { ...defaultConfig, ...config }
  }

  /**
   * 连接到协作房间
   */
  connect(
    roomId: string,
    user: { id: string; name: string },
    callbacks?: {
      onConnectionChange?: (connected: boolean) => void
      onUsersChange?: (users: CollaborationUser[]) => void
      onError?: (error: Error) => void
    }
  ): Y.Doc {
    this.roomId = roomId
    this.user = user
    this.onConnectionChange = callbacks?.onConnectionChange
    this.onUsersChange = callbacks?.onUsersChange
    this.onError = callbacks?.onError

    // 创建 Yjs 文档
    this.doc = new Y.Doc()

    // 设置离线持久化
    if (this.config.enableOffline) {
      this.setupPersistence()
    }

    // 连接 WebSocket
    this.connectWebSocket()

    return this.doc
  }

  /**
   * 设置 IndexedDB 持久化
   */
  private setupPersistence(): void {
    if (!this.doc) return

    try {
      this.persistence = new IndexeddbPersistence(this.roomId, this.doc)

      this.persistence.on('synced', () => {
        console.log('[Collaboration] Offline data synced')
      })
    } catch (error) {
      console.warn('[Collaboration] Failed to setup offline persistence:', error)
    }
  }

  /**
   * 连接 WebSocket
   */
  private connectWebSocket(): void {
    if (!this.doc || !this.user) return

    const color = getUserColor(Math.floor(Math.random() * COLORS.length))

    try {
      this.provider = new WebsocketProvider(
        this.config.serverUrl!,
        this.roomId,
        this.doc,
        { connect: false }
      )

      // 设置用户信息
      this.provider.awareness.setLocalStateField('user', {
        id: this.user.id,
        name: this.user.name,
        color,
      })

      // 监听连接状态
      this.provider.on('status', (event: { status: string }) => {
        const connected = event.status === 'connected'
        this.onConnectionChange?.(connected)

        if (connected) {
          this.reconnectAttempts = 0
        } else if (event.status === 'disconnected') {
          this.scheduleReconnect()
        }
      })

      // 监听用户变化
      this.provider.awareness.on('change', () => {
        const users = this.getUsers()
        this.onUsersChange?.(users)
      })

      // 连接
      this.provider.connect()
    } catch (error) {
      console.error('[Collaboration] Connection failed:', error)
      this.onError?.(error as Error)
      this.scheduleReconnect()
    }
  }

  /**
   * 计划重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= (this.config.maxReconnectAttempts || 10)) {
      console.error('[Collaboration] Max reconnect attempts reached')
      this.onError?.(new Error('Max reconnect attempts reached'))
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectAttempts++
    console.log(`[Collaboration] Reconnecting in ${this.config.reconnectInterval}ms (attempt ${this.reconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      if (this.provider) {
        this.provider.connect()
      } else {
        this.connectWebSocket()
      }
    }, this.config.reconnectInterval)
  }

  /**
   * 手动重连
   */
  reconnect(): void {
    this.reconnectAttempts = 0
    if (this.provider) {
      this.provider.connect()
    }
  }

  /**
   * 获取当前用户列表
   */
  private getUsers(): CollaborationUser[] {
    if (!this.provider) return []

    const states = this.provider.awareness.getStates()
    const users: CollaborationUser[] = []

    states.forEach((state: { user?: { id: string; name: string; color: string } }, clientId: number) => {
      if (state.user) {
        users.push({
          ...state.user,
          clientId,
        })
      }
    })

    return users
  }

  /**
   * 获取 Y.Doc 实例
   */
  getDoc(): Y.Doc | null {
    return this.doc
  }

  /**
   * 获取 WebSocket Provider 实例
   */
  getProvider(): WebsocketProvider | null {
    return this.provider
  }

  /**
   * 获取用户信息用于协作光标
   */
  getUserInfo(): { name: string; color: string } | null {
    if (!this.provider) return null
    const state = this.provider.awareness.getLocalState()
    return state?.user || null
  }

  /**
   * 断开连接并清理资源
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.provider) {
      this.provider.disconnect()
      this.provider.destroy()
      this.provider = null
    }

    if (this.persistence) {
      this.persistence.destroy()
      this.persistence = null
    }

    if (this.doc) {
      this.doc.destroy()
      this.doc = null
    }
  }
}

/**
 * 协作 Hook
 */
export function useCollaboration(
  roomId: string,
  userId: string,
  userName: string,
  config?: CollaborationConfig
) {
  const [isConnected, setIsConnected] = useState(false)
  const [users, setUsers] = useState<CollaborationUser[]>([])
  const managerRef = useRef<CollaborationManager | null>(null)
  const docRef = useRef<Y.Doc | null>(null)
  const providerRef = useRef<WebsocketProvider | null>(null)

  useEffect(() => {
    if (!roomId || !userId) return

    // 创建协作管理器
    const manager = new CollaborationManager(config)
    managerRef.current = manager

    // 连接
    const doc = manager.connect(roomId, { id: userId, name: userName }, {
      onConnectionChange: setIsConnected,
      onUsersChange: setUsers,
      onError: (error) => {
        console.error('[Collaboration] Error:', error)
      },
    })

    docRef.current = doc
    providerRef.current = manager.getProvider()

    return () => {
      manager.disconnect()
      managerRef.current = null
      docRef.current = null
      providerRef.current = null
    }
  }, [roomId, userId, userName, config])

  const getDoc = useCallback(() => docRef.current, [])
  const getProvider = useCallback(() => providerRef.current, [])
  const reconnect = useCallback(() => {
    managerRef.current?.reconnect()
  }, [])

  return {
    isConnected,
    users,
    getDoc,
    getProvider,
    reconnect,
    manager: managerRef.current,
  }
}

/**
 * 获取文本内容
 */
export function getText(doc: Y.Doc | null, key: string = 'content'): Y.Text | null {
  if (!doc) return null
  return doc.getText(key)
}

/**
 * 更新文本内容
 */
export function updateText(doc: Y.Doc | null, key: string, content: string): void {
  if (!doc) return
  const text = doc.getText(key)
  doc.transact(() => {
    text.delete(0, text.length)
    text.insert(0, content)
  })
}

/**
 * 观察文本变化
 */
export function observeText(
  doc: Y.Doc | null,
  key: string,
  callback: (content: string) => void,
): (() => void) | null {
  if (!doc) return null

  const text = doc.getText(key)
  const observer = () => {
    callback(text.toString())
  }

  text.observe(observer)

  return () => {
    text.unobserve(observer)
  }
}
