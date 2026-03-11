/**
 * Yjs Document Manager
 * 管理Yjs文档生命周期、持久化和同步
 */

import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
import { IndexeddbPersistence } from 'y-indexeddb'
import { awarenessProtocol } from 'y-protocols/awareness'

export interface UserInfo {
  id: string
  name: string
  color: string
  avatar?: string
  email?: string
}

export interface DocumentMetadata {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  ownerId: string
  version: number
}

export interface CollaborationState {
  connected: boolean
  synced: boolean
  users: UserInfo[]
  currentUser: UserInfo | null
}

export type YjsUpdateCallback = (update: Uint8Array, origin: any) => void
export type AwarenessChangeCallback = (states: Map<number, any>) => void
export type StatusChangeCallback = (status: 'connected' | 'disconnected' | 'connecting') => void
export type SyncChangeCallback = (synced: boolean) => void

/**
 * Yjs文档管理器
 * 负责管理单个文档的Yjs实例、WebSocket连接和本地持久化
 */
export class YjsDocumentManager {
  private doc: Y.Doc
  private provider: WebsocketProvider | null = null
  private indexeddbProvider: IndexeddbPersistence | null = null
  private awareness: awarenessProtocol.Awareness | null = null

  // Yjs共享类型
  private yText: Y.Text | null = null
  private yMetadata: Y.Map<any> | null = null
  private yComments: Y.Array<any> | null = null
  private yVersions: Y.Array<any> | null = null

  // 事件监听器
  private updateCallbacks: YjsUpdateCallback[] = []
  private awarenessCallbacks: AwarenessChangeCallback[] = []
  private statusCallbacks: StatusChangeCallback[] = []
  private syncCallbacks: SyncChangeCallback[] = []

  // 状态
  private documentId: string
  private currentUser: UserInfo | null = null
  private isDestroyed = false

  constructor(documentId: string) {
    this.documentId = documentId
    this.doc = new Y.Doc({
      guid: documentId,
    })

    this.initSharedTypes()
    this.setupDocListeners()
  }

  /**
   * 初始化共享类型
   */
  private initSharedTypes(): void {
    // 主文本内容
    this.yText = this.doc.getText('content')

    // 文档元数据
    this.yMetadata = this.doc.getMap('metadata')

    // 评论列表
    this.yComments = this.doc.getArray('comments')

    // 版本历史
    this.yVersions = this.doc.getArray('versions')
  }

  /**
   * 设置文档监听器
   */
  private setupDocListeners(): void {
    // 监听文档更新
    this.doc.on('update', (update: Uint8Array, origin: any) => {
      this.updateCallbacks.forEach(cb => cb(update, origin))
    })
  }

  /**
   * 连接到协作服务器
   */
  async connect(
    websocketUrl: string,
    userInfo: UserInfo,
    token?: string
  ): Promise<void> {
    if (this.isDestroyed) {
      throw new Error('Document manager has been destroyed')
    }

    this.currentUser = userInfo

    // 初始化IndexedDB持久化
    const dbName = `scholarforge-${this.documentId}`
    this.indexeddbProvider = new IndexeddbPersistence(dbName, this.doc)

    // 等待IndexedDB同步完成
    await new Promise<void>((resolve) => {
      this.indexeddbProvider!.on('synced', () => {
        console.log('[Yjs] IndexedDB synced')
        resolve()
      })

      // 超时处理
      setTimeout(() => resolve(), 2000)
    })

    // 创建WebSocket提供者
    this.provider = new WebsocketProvider(
      websocketUrl,
      this.documentId,
      this.doc,
      {
        params: token ? { token } : undefined,
        resyncInterval: 10000,
        maxBackoffTime: 10000,
        connect: true,
      }
    )

    this.awareness = this.provider.awareness

    // 设置当前用户状态
    this.awareness.setLocalStateField('user', userInfo)

    // 监听连接状态
    this.provider.on('status', (event: { status: 'connected' | 'disconnected' | 'connecting' }) => {
      this.statusCallbacks.forEach(cb => cb(event.status))
    })

    // 监听同步状态
    this.provider.on('sync', (isSynced: boolean) => {
      this.syncCallbacks.forEach(cb => cb(isSynced))
    })

    // 监听awareness变化
    this.awareness.on('change', () => {
      this.awarenessCallbacks.forEach(cb => cb(this.awareness!.getStates()))
    })

    return new Promise((resolve) => {
      this.provider!.on('synced', () => {
        console.log('[Yjs] WebSocket synced')
        resolve()
      })

      // 超时处理
      setTimeout(() => resolve(), 3000)
    })
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.provider) {
      this.provider.disconnect()
    }
  }

  /**
   * 重新连接
   */
  reconnect(): void {
    if (this.provider) {
      this.provider.connect()
    }
  }

  /**
   * 销毁文档管理器
   */
  destroy(): void {
    this.isDestroyed = true

    if (this.provider) {
      this.provider.destroy()
      this.provider = null
    }

    if (this.indexeddbProvider) {
      this.indexeddbProvider.destroy()
      this.indexeddbProvider = null
    }

    this.doc.destroy()
  }

  /**
   * 获取文本内容
   */
  getText(): string {
    return this.yText?.toString() || ''
  }

  /**
   * 设置文本内容（会覆盖原有内容）
   */
  setText(text: string): void {
    if (this.yText) {
      this.yText.delete(0, this.yText.length)
      this.yText.insert(0, text)
    }
  }

  /**
   * 在指定位置插入文本
   */
  insertText(index: number, text: string): void {
    this.yText?.insert(index, text)
  }

  /**
   * 删除指定范围的文本
   */
  deleteText(index: number, length: number): void {
    this.yText?.delete(index, length)
  }

  /**
   * 获取文档元数据
   */
  getMetadata(): DocumentMetadata | null {
    if (!this.yMetadata) return null

    return {
      id: this.yMetadata.get('id') || this.documentId,
      title: this.yMetadata.get('title') || '',
      createdAt: this.yMetadata.get('createdAt') || new Date().toISOString(),
      updatedAt: this.yMetadata.get('updatedAt') || new Date().toISOString(),
      ownerId: this.yMetadata.get('ownerId') || '',
      version: this.yMetadata.get('version') || 1,
    }
  }

  /**
   * 设置文档元数据
   */
  setMetadata(metadata: Partial<DocumentMetadata>): void {
    if (!this.yMetadata) return

    Object.entries(metadata).forEach(([key, value]) => {
      if (value !== undefined) {
        this.yMetadata!.set(key, value)
      }
    })

    // 更新更新时间
    this.yMetadata.set('updatedAt', new Date().toISOString())
  }

  /**
   * 获取Y.Text实例（用于编辑器绑定）
   */
  getYText(): Y.Text | null {
    return this.yText
  }

  /**
   * 获取Y.Doc实例
   */
  getDoc(): Y.Doc {
    return this.doc
  }

  /**
   * 获取Provider实例
   */
  getProvider(): WebsocketProvider | null {
    return this.provider
  }

  /**
   * 获取Awareness实例
   */
  getAwareness(): awarenessProtocol.Awareness | null {
    return this.awareness
  }

  /**
   * 获取当前用户列表
   */
  getUsers(): UserInfo[] {
    if (!this.awareness) return []

    const states = Array.from(this.awareness.getStates().values())
    return states
      .filter((state: any) => state.user)
      .map((state: any) => state.user as UserInfo)
  }

  /**
   * 更新当前用户状态
   */
  updateUserState(state: Partial<UserInfo>): void {
    if (!this.awareness || !this.currentUser) return

    this.currentUser = { ...this.currentUser, ...state }
    this.awareness.setLocalStateField('user', this.currentUser)
  }

  /**
   * 创建文档快照（用于版本历史）
   */
  createSnapshot(): Uint8Array {
    return Y.encodeStateAsUpdate(this.doc)
  }

  /**
   * 从快照恢复文档
   */
  applySnapshot(snapshot: Uint8Array): void {
    Y.applyUpdate(this.doc, snapshot)
  }

  /**
   * 获取文档状态向量（用于增量同步）
   */
  getStateVector(): Uint8Array {
    return Y.encodeStateVector(this.doc)
  }

  /**
   * 应用增量更新
   */
  applyUpdate(update: Uint8Array, origin?: any): void {
    Y.applyUpdate(this.doc, update, origin)
  }

  /**
   * 获取自给定状态向量以来的更新
   */
  getUpdateSince(stateVector: Uint8Array): Uint8Array {
    return Y.encodeStateAsUpdate(this.doc, stateVector)
  }

  /**
   * 清空文档内容
   */
  clear(): void {
    this.yText?.delete(0, this.yText.length)
    this.yComments?.delete(0, this.yComments.length)
  }

  /**
   * 检查是否已销毁
   */
  getIsDestroyed(): boolean {
    return this.isDestroyed
  }

  // ========== 事件监听 ==========

  /**
   * 监听文档更新
   */
  onUpdate(callback: YjsUpdateCallback): () => void {
    this.updateCallbacks.push(callback)
    return () => {
      const index = this.updateCallbacks.indexOf(callback)
      if (index > -1) {
        this.updateCallbacks.splice(index, 1)
      }
    }
  }

  /**
   * 监听awareness变化
   */
  onAwarenessChange(callback: AwarenessChangeCallback): () => void {
    this.awarenessCallbacks.push(callback)
    return () => {
      const index = this.awarenessCallbacks.indexOf(callback)
      if (index > -1) {
        this.awarenessCallbacks.splice(index, 1)
      }
    }
  }

  /**
   * 监听连接状态变化
   */
  onStatusChange(callback: StatusChangeCallback): () => void {
    this.statusCallbacks.push(callback)
    return () => {
      const index = this.statusCallbacks.indexOf(callback)
      if (index > -1) {
        this.statusCallbacks.splice(index, 1)
      }
    }
  }

  /**
   * 监听同步状态变化
   */
  onSyncChange(callback: SyncChangeCallback): () => void {
    this.syncCallbacks.push(callback)
    return () => {
      const index = this.syncCallbacks.indexOf(callback)
      if (index > -1) {
        this.syncCallbacks.splice(index, 1)
      }
    }
  }
}

/**
 * 文档管理器工厂
 * 管理多个文档实例
 */
export class YjsDocumentManagerFactory {
  private static instances: Map<string, YjsDocumentManager> = new Map()

  /**
   * 获取或创建文档管理器
   */
  static getManager(documentId: string): YjsDocumentManager {
    if (!this.instances.has(documentId)) {
      const manager = new YjsDocumentManager(documentId)
      this.instances.set(documentId, manager)
    }
    return this.instances.get(documentId)!
  }

  /**
   * 获取现有管理器（如果不存在返回null）
   */
  static getExistingManager(documentId: string): YjsDocumentManager | null {
    return this.instances.get(documentId) || null
  }

  /**
   * 销毁文档管理器
   */
  static destroyManager(documentId: string): void {
    const manager = this.instances.get(documentId)
    if (manager) {
      manager.destroy()
      this.instances.delete(documentId)
    }
  }

  /**
   * 获取所有活动文档ID
   */
  static getActiveDocumentIds(): string[] {
    return Array.from(this.instances.keys())
  }

  /**
   * 清理已销毁的管理器
   */
  static cleanup(): void {
    this.instances.forEach((manager, id) => {
      if (manager.getIsDestroyed()) {
        this.instances.delete(id)
      }
    })
  }

  /**
   * 销毁所有管理器
   */
  static destroyAll(): void {
    this.instances.forEach((manager) => {
      manager.destroy()
    })
    this.instances.clear()
  }
}

export default YjsDocumentManager
