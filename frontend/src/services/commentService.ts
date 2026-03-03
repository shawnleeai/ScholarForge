/**
 * 评论服务 API
 */

import { request } from './api'
import type {
  Comment,
  CommentReply,
  CreateCommentRequest,
  CreateReplyRequest,
  UpdateCommentRequest,
} from '@/types/comment'

// 是否使用模拟模式（开发环境且没有配置后端API时）
const USE_MOCK = import.meta.env.DEV && !import.meta.env.VITE_API_URL

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

// 本地存储的评论数据（Mock 模式使用）
const getLocalComments = (paperId: string): Comment[] => {
  const stored = localStorage.getItem(`scholarforge-comments-${paperId}`)
  return stored ? JSON.parse(stored) : []
}

const saveLocalComments = (paperId: string, comments: Comment[]) => {
  localStorage.setItem(`scholarforge-comments-${paperId}`, JSON.stringify(comments))
}

// 转换后端响应到前端格式
const transformComment = (data: Record<string, unknown>): Comment => ({
  id: data.id as string,
  paperId: data.paper_id as string,
  sectionId: data.section_id as string,
  userId: data.user_id as string,
  userName: (data.user_name as string) || '未知用户',
  userAvatar: data.user_avatar as string | undefined,
  content: data.content as string,
  position: data.position as Comment['position'],
  resolved: data.resolved as boolean,
  createdAt: data.created_at as string,
  updatedAt: data.updated_at as string,
  replies: (data.replies as Record<string, unknown>[] || []).map(transformReply),
})

const transformReply = (data: Record<string, unknown>): CommentReply => ({
  id: data.id as string,
  commentId: data.comment_id as string,
  userId: data.user_id as string,
  userName: (data.user_name as string) || '未知用户',
  userAvatar: data.user_avatar as string | undefined,
  content: data.content as string,
  createdAt: data.created_at as string,
})

export const commentService = {
  /**
   * 获取论文章节的评论列表
   */
  getComments: async (paperId: string, sectionId?: string): Promise<{ data: Comment[] }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      let comments = getLocalComments(paperId)
      if (sectionId) {
        comments = comments.filter(c => c.sectionId === sectionId)
      }
      return { data: comments }
    }

    const params = sectionId ? { section_id: sectionId } : {}
    const response = await request.get<Record<string, unknown>[]>(`/papers/${paperId}/comments`, params)
    return {
      data: (response.data || []).map(transformComment),
    }
  },

  /**
   * 创建评论
   */
  createComment: async (data: CreateCommentRequest): Promise<{ data: Comment }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const newComment: Comment = {
        id: generateId(),
        paperId: data.paperId,
        sectionId: data.sectionId,
        userId: 'current-user',
        userName: '当前用户',
        content: data.content,
        position: data.position,
        resolved: false,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        replies: [],
      }
      const comments = getLocalComments(data.paperId)
      comments.push(newComment)
      saveLocalComments(data.paperId, comments)
      return { data: newComment }
    }

    const requestData = {
      paper_id: data.paperId,
      section_id: data.sectionId,
      content: data.content,
      position: {
        from: data.position.from,
        to: data.position.to,
        section_id: data.sectionId,
        selected_text: data.position.selectedText,
      },
    }
    const response = await request.post<Record<string, unknown>>(`/papers/${data.paperId}/comments`, requestData)
    return { data: transformComment(response.data) }
  },

  /**
   * 更新评论
   */
  updateComment: async (
    paperId: string,
    commentId: string,
    data: UpdateCommentRequest
  ): Promise<{ data: Comment }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const comments = getLocalComments(paperId)
      const index = comments.findIndex(c => c.id === commentId)
      if (index === -1) throw { code: 404, message: '评论不存在' }
      comments[index] = {
        ...comments[index],
        ...data,
        updatedAt: new Date().toISOString(),
      }
      saveLocalComments(paperId, comments)
      return { data: comments[index] }
    }

    const response = await request.put<Record<string, unknown>>(`/papers/${paperId}/comments/${commentId}`, data)
    return { data: transformComment(response.data) }
  },

  /**
   * 删除评论
   */
  deleteComment: async (paperId: string, commentId: string): Promise<{ code: number }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const comments = getLocalComments(paperId)
      const filtered = comments.filter(c => c.id !== commentId)
      saveLocalComments(paperId, filtered)
      return { code: 200 }
    }

    await request.delete(`/papers/${paperId}/comments/${commentId}`)
    return { code: 200 }
  },

  /**
   * 解决评论
   */
  resolveComment: async (paperId: string, commentId: string): Promise<{ data: Comment }> => {
    return commentService.updateComment(paperId, commentId, { resolved: true })
  },

  /**
   * 重新打开评论
   */
  reopenComment: async (paperId: string, commentId: string): Promise<{ data: Comment }> => {
    return commentService.updateComment(paperId, commentId, { resolved: false })
  },

  /**
   * 创建回复
   */
  createReply: async (
    paperId: string,
    commentId: string,
    data: CreateReplyRequest
  ): Promise<{ data: CommentReply }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const newReply: CommentReply = {
        id: generateId(),
        commentId,
        userId: 'current-user',
        userName: '当前用户',
        content: data.content,
        createdAt: new Date().toISOString(),
      }
      const comments = getLocalComments(paperId)
      const index = comments.findIndex(c => c.id === commentId)
      if (index !== -1) {
        if (!comments[index].replies) {
          comments[index].replies = []
        }
        comments[index].replies.push(newReply)
        saveLocalComments(paperId, comments)
      }
      return { data: newReply }
    }

    const response = await request.post<Record<string, unknown>>(
      `/papers/${paperId}/comments/${commentId}/replies`,
      { content: data.content }
    )
    return { data: transformReply(response.data) }
  },

  /**
   * 删除回复
   */
  deleteReply: async (
    paperId: string,
    commentId: string,
    replyId: string
  ): Promise<{ code: number }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const comments = getLocalComments(paperId)
      const index = comments.findIndex(c => c.id === commentId)
      if (index !== -1 && comments[index].replies) {
        comments[index].replies = comments[index].replies!.filter(r => r.id !== replyId)
        saveLocalComments(paperId, comments)
      }
      return { code: 200 }
    }

    await request.delete(`/papers/${paperId}/comments/${commentId}/replies/${replyId}`)
    return { code: 200 }
  },
}

export default commentService
