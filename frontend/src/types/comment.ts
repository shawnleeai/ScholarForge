/**
 * 评论/批注类型定义
 */

export interface CommentPosition {
  /** 起始位置 */
  from: number
  /** 结束位置 */
  to: number
  /** 选中的文本 */
  selectedText?: string
}

export interface Comment {
  /** 评论 ID */
  id: string
  /** 论文 ID */
  paperId: string
  /** 章节 ID */
  sectionId: string
  /** 用户 ID */
  userId: string
  /** 用户名 */
  userName: string
  /** 用户头像 */
  userAvatar?: string
  /** 评论内容 */
  content: string
  /** 评论位置 */
  position: CommentPosition
  /** 是否已解决 */
  resolved: boolean
  /** 创建时间 */
  createdAt: string
  /** 更新时间 */
  updatedAt: string
  /** 回复列表 */
  replies?: CommentReply[]
}

export interface CommentReply {
  /** 回复 ID */
  id: string
  /** 评论 ID */
  commentId: string
  /** 用户 ID */
  userId: string
  /** 用户名 */
  userName: string
  /** 用户头像 */
  userAvatar?: string
  /** 回复内容 */
  content: string
  /** 创建时间 */
  createdAt: string
}

export interface CreateCommentRequest {
  paperId: string
  sectionId: string
  content: string
  position: CommentPosition
}

export interface CreateReplyRequest {
  commentId: string
  content: string
}

export interface UpdateCommentRequest {
  content?: string
  resolved?: boolean
}

export interface CommentThread {
  comment: Comment
  replies: CommentReply[]
}
