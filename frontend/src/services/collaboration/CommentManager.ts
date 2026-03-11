/**
 * 评论管理系统
 * 基于Yjs Y.Array实现实时同步的评论数据
 */

import * as Y from 'yjs'
import { IndexeddbPersistence } from 'y-indexeddb'

export interface CommentAuthor {
  id: string
  name: string
  color: string
  avatar?: string
}

export interface CommentPosition {
  from: number
  to: number
}

export type CommentStatus = 'open' | 'resolved' | 'rejected'

export interface CommentReply {
  id: string
  content: string
  author: CommentAuthor
  createdAt: number
  updatedAt?: number
}

export interface Comment {
  id: string
  content: string
  author: CommentAuthor
  position: CommentPosition
  status: CommentStatus
  replies: CommentReply[]
  createdAt: number
  updatedAt?: number
  resolvedAt?: number
  resolvedBy?: string
  mentions: string[]  // 被@的用户ID列表
}

export interface CreateCommentInput {
  content: string
  author: CommentAuthor
  position: CommentPosition
  mentions?: string[]
}

export interface AddReplyInput {
  commentId: string
  content: string
  author: CommentAuthor
  mentions?: string[]
}

export type CommentChangeCallback = (comments: Comment[]) => void

/**
 * 评论管理器
 * 管理文档中的所有评论，基于Yjs实现多用户实时同步
 */
export class CommentManager {
  private ydoc: Y.Doc
  private yComments: Y.Array<any>
  private persistence: IndexeddbPersistence | null = null
  private changeCallbacks: CommentChangeCallback[] = []

  constructor(docId: string, ydoc?: Y.Doc) {
    // 使用现有的Y.Doc或创建新的
    this.ydoc = ydoc || new Y.Doc({ guid: `comments-${docId}` })
    this.yComments = this.ydoc.getArray('comments')

    // 设置IndexedDB持久化
    this.persistence = new IndexeddbPersistence(
      `scholarforge-comments-${docId}`,
      this.ydoc
    )

    // 监听变化
    this.yComments.observe(() => {
      this.notifyChange()
    })
  }

  /**
   * 创建新评论
   */
  createComment(input: CreateCommentInput): Comment {
    const comment: Comment = {
      id: this.generateId(),
      content: input.content,
      author: input.author,
      position: input.position,
      status: 'open',
      replies: [],
      createdAt: Date.now(),
      mentions: input.mentions || this.extractMentions(input.content),
    }

    this.yComments.push([this.toYjsComment(comment)])
    return comment
  }

  /**
   * 添加评论回复
   */
  addReply(input: AddReplyInput): CommentReply | null {
    const index = this.findCommentIndex(input.commentId)
    if (index === -1) return null

    const reply: CommentReply = {
      id: this.generateId(),
      content: input.content,
      author: input.author,
      createdAt: Date.now(),
    }

    const yComment = this.yComments.get(index)
    const yReplies = yComment.get('replies') as Y.Array<any>
    yReplies.push([this.toYjsReply(reply)])

    // 更新评论的updatedAt
    yComment.set('updatedAt', Date.now())

    return reply
  }

  /**
   * 更新评论内容
   */
  updateComment(commentId: string, content: string): boolean {
    const index = this.findCommentIndex(commentId)
    if (index === -1) return false

    const yComment = this.yComments.get(index)
    yComment.set('content', content)
    yComment.set('updatedAt', Date.now())
    yComment.set('mentions', this.extractMentions(content))

    return true
  }

  /**
   * 删除评论
   */
  deleteComment(commentId: string): boolean {
    const index = this.findCommentIndex(commentId)
    if (index === -1) return false

    this.yComments.delete(index, 1)
    return true
  }

  /**
   * 解决评论
   */
  resolveComment(commentId: string, userId: string): boolean {
    const index = this.findCommentIndex(commentId)
    if (index === -1) return false

    const yComment = this.yComments.get(index)
    yComment.set('status', 'resolved')
    yComment.set('resolvedAt', Date.now())
    yComment.set('resolvedBy', userId)
    yComment.set('updatedAt', Date.now())

    return true
  }

  /**
   * 重新打开已解决的评论
   */
  reopenComment(commentId: string): boolean {
    const index = this.findCommentIndex(commentId)
    if (index === -1) return false

    const yComment = this.yComments.get(index)
    yComment.set('status', 'open')
    yComment.delete('resolvedAt')
    yComment.delete('resolvedBy')
    yComment.set('updatedAt', Date.now())

    return true
  }

  /**
   * 拒绝评论
   */
  rejectComment(commentId: string): boolean {
    const index = this.findCommentIndex(commentId)
    if (index === -1) return false

    const yComment = this.yComments.get(index)
    yComment.set('status', 'rejected')
    yComment.set('updatedAt', Date.now())

    return true
  }

  /**
   * 获取所有评论
   */
  getAllComments(): Comment[] {
    return this.yComments.toArray().map((yComment) =>
      this.fromYjsComment(yComment)
    )
  }

  /**
   * 获取指定状态的评论
   */
  getCommentsByStatus(status: CommentStatus): Comment[] {
    return this.getAllComments().filter((c) => c.status === status)
  }

  /**
   * 获取指定位置的评论
   */
  getCommentsByPosition(from: number, to: number): Comment[] {
    return this.getAllComments().filter(
      (c) => c.position.from === from && c.position.to === to
    )
  }

  /**
   * 获取包含某位置的评论
   */
  getCommentsAtPosition(pos: number): Comment[] {
    return this.getAllComments().filter(
      (c) => pos >= c.position.from && pos <= c.position.to
    )
  }

  /**
   * 获取指定用户的评论
   */
  getCommentsByUser(userId: string): Comment[] {
    return this.getAllComments().filter((c) => c.author.id === userId)
  }

  /**
   * 获取提到指定用户的评论
   */
  getCommentsMentioningUser(userId: string): Comment[] {
    return this.getAllComments().filter((c) => c.mentions.includes(userId))
  }

  /**
   * 根据ID获取评论
   */
  getCommentById(commentId: string): Comment | null {
    const index = this.findCommentIndex(commentId)
    if (index === -1) return null

    return this.fromYjsComment(this.yComments.get(index))
  }

  /**
   * 获取评论统计
   */
  getStats(): {
    total: number
    open: number
    resolved: number
    rejected: number
    totalReplies: number
  } {
    const comments = this.getAllComments()
    return {
      total: comments.length,
      open: comments.filter((c) => c.status === 'open').length,
      resolved: comments.filter((c) => c.status === 'resolved').length,
      rejected: comments.filter((c) => c.status === 'rejected').length,
      totalReplies: comments.reduce((sum, c) => sum + c.replies.length, 0),
    }
  }

  /**
   * 监听评论变化
   */
  onChange(callback: CommentChangeCallback): () => void {
    this.changeCallbacks.push(callback)
    return () => {
      const index = this.changeCallbacks.indexOf(callback)
      if (index > -1) {
        this.changeCallbacks.splice(index, 1)
      }
    }
  }

  /**
   * 销毁管理器
   */
  destroy(): void {
    if (this.persistence) {
      this.persistence.destroy()
      this.persistence = null
    }
    // 注意：不销毁ydoc，因为它可能是共享的
  }

  // ========== 私有方法 ==========

  private notifyChange(): void {
    const comments = this.getAllComments()
    this.changeCallbacks.forEach((cb) => cb(comments))
  }

  private findCommentIndex(commentId: string): number {
    for (let i = 0; i < this.yComments.length; i++) {
      const yComment = this.yComments.get(i)
      if (yComment.get('id') === commentId) {
        return i
      }
    }
    return -1
  }

  private generateId(): string {
    return `comment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private extractMentions(content: string): string[] {
    const mentionRegex = /@(\w+)/g
    const mentions: string[] = []
    let match
    while ((match = mentionRegex.exec(content)) !== null) {
      mentions.push(match[1])
    }
    return mentions
  }

  private toYjsComment(comment: Comment): Y.Map<any> {
    const yComment = new Y.Map()

    yComment.set('id', comment.id)
    yComment.set('content', comment.content)
    yComment.set('author', this.toYjsAuthor(comment.author))
    yComment.set('position', this.toYjsPosition(comment.position))
    yComment.set('status', comment.status)
    yComment.set('replies', new Y.Array())
    yComment.set('createdAt', comment.createdAt)
    yComment.set('mentions', comment.mentions)

    if (comment.updatedAt) yComment.set('updatedAt', comment.updatedAt)
    if (comment.resolvedAt) yComment.set('resolvedAt', comment.resolvedAt)
    if (comment.resolvedBy) yComment.set('resolvedBy', comment.resolvedBy)

    // 添加回复
    const yReplies = yComment.get('replies') as Y.Array<any>
    comment.replies.forEach((reply) => {
      yReplies.push([this.toYjsReply(reply)])
    })

    return yComment
  }

  private fromYjsComment(yComment: Y.Map<any>): Comment {
    const replies: CommentReply[] = []
    const yReplies = yComment.get('replies') as Y.Array<any>
    if (yReplies) {
      for (let i = 0; i < yReplies.length; i++) {
        replies.push(this.fromYjsReply(yReplies.get(i)))
      }
    }

    return {
      id: yComment.get('id'),
      content: yComment.get('content'),
      author: this.fromYjsAuthor(yComment.get('author')),
      position: this.fromYjsPosition(yComment.get('position')),
      status: yComment.get('status'),
      replies,
      createdAt: yComment.get('createdAt'),
      updatedAt: yComment.get('updatedAt'),
      resolvedAt: yComment.get('resolvedAt'),
      resolvedBy: yComment.get('resolvedBy'),
      mentions: yComment.get('mentions') || [],
    }
  }

  private toYjsReply(reply: CommentReply): Y.Map<any> {
    const yReply = new Y.Map()
    yReply.set('id', reply.id)
    yReply.set('content', reply.content)
    yReply.set('author', this.toYjsAuthor(reply.author))
    yReply.set('createdAt', reply.createdAt)
    if (reply.updatedAt) yReply.set('updatedAt', reply.updatedAt)
    return yReply
  }

  private fromYjsReply(yReply: Y.Map<any>): CommentReply {
    return {
      id: yReply.get('id'),
      content: yReply.get('content'),
      author: this.fromYjsAuthor(yReply.get('author')),
      createdAt: yReply.get('createdAt'),
      updatedAt: yReply.get('updatedAt'),
    }
  }

  private toYjsAuthor(author: CommentAuthor): Y.Map<any> {
    const yAuthor = new Y.Map()
    yAuthor.set('id', author.id)
    yAuthor.set('name', author.name)
    yAuthor.set('color', author.color)
    if (author.avatar) yAuthor.set('avatar', author.avatar)
    return yAuthor
  }

  private fromYjsAuthor(yAuthor: Y.Map<any>): CommentAuthor {
    return {
      id: yAuthor.get('id'),
      name: yAuthor.get('name'),
      color: yAuthor.get('color'),
      avatar: yAuthor.get('avatar'),
    }
  }

  private toYjsPosition(position: CommentPosition): Y.Map<any> {
    const yPos = new Y.Map()
    yPos.set('from', position.from)
    yPos.set('to', position.to)
    return yPos
  }

  private fromYjsPosition(yPos: Y.Map<any>): CommentPosition {
    return {
      from: yPos.get('from'),
      to: yPos.get('to'),
    }
  }
}

/**
 * 评论管理器工厂
 */
export class CommentManagerFactory {
  private static instances: Map<string, CommentManager> = new Map()

  static getManager(docId: string, ydoc?: Y.Doc): CommentManager {
    if (!this.instances.has(docId)) {
      const manager = new CommentManager(docId, ydoc)
      this.instances.set(docId, manager)
    }
    return this.instances.get(docId)!
  }

  static destroyManager(docId: string): void {
    const manager = this.instances.get(docId)
    if (manager) {
      manager.destroy()
      this.instances.delete(docId)
    }
  }
}

export default CommentManager
