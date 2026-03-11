/**
 * 导师协同审阅与批注服务
 * 支持实时协同、批注管理、审阅工作流
 */

export type ReviewStatus = 'pending' | 'in_progress' | 'completed' | 'resolved'
export type CommentType = 'suggestion' | 'question' | 'praise' | 'correction' | 'general'
export type ReviewerRole = 'advisor' | 'committee' | 'peer' | 'student'

export interface Reviewer {
  id: string
  name: string
  avatar: string
  role: ReviewerRole
  title: string
  expertise: string[]
  color: string
}

export interface Comment {
  id: string
  reviewerId: string
  paperId: string
  sectionId: string
  paragraphId?: string
  type: CommentType
  content: string
  selectedText?: string
  position: {
    start: number
    end: number
  }
  status: ReviewStatus
  createdAt: string
  updatedAt: string
  replies: Reply[]
  reactions: Reaction[]
}

export interface Reply {
  id: string
  commentId: string
  reviewerId: string
  content: string
  createdAt: string
}

export interface Reaction {
  reviewerId: string
  type: 'agree' | 'disagree' | 'helpful' | 'resolved'
}

export interface ReviewSection {
  id: string
  title: string
  status: ReviewStatus
  commentCount: number
  lastReviewedAt?: string
}

export interface ReviewRound {
  id: string
  roundNumber: number
  status: 'active' | 'completed'
  startedAt: string
  completedAt?: string
  reviewers: string[]
  summary?: string
}

export interface ReviewStats {
  totalComments: number
  resolvedComments: number
  pendingComments: number
  byType: Record<CommentType, number>
  byReviewer: Record<string, number>
}

export interface ReviewTemplate {
  id: string
  name: string
  description: string
  checklist: string[]
}

// 审阅模板
export const REVIEW_TEMPLATES: ReviewTemplate[] = [
  {
    id: 'thesis_comprehensive',
    name: '学位论文综合审阅',
    description: '适用于硕士/博士学位论文的全面审阅',
    checklist: [
      '选题意义和创新性',
      '文献综述的全面性',
      '研究方法的适当性',
      '数据分析的准确性',
      '结论的合理性',
      '论文结构的逻辑性',
      '语言表达的规范性',
      '格式规范的符合度'
    ]
  },
  {
    id: 'journal_review',
    name: '期刊论文审稿',
    description: '适用于期刊论文的同行评议',
    checklist: [
      '原创性和创新性',
      '研究设计的科学性',
      '结果的可靠性',
      '讨论的深度',
      '引用的恰当性',
      '语言和写作质量'
    ]
  },
  {
    id: 'proposal_review',
    name: '开题报告审阅',
    description: '适用于研究计划/开题报告的审阅',
    checklist: [
      '研究问题的明确性',
      '理论基础扎实度',
      '研究方案可行性',
      '预期成果合理性',
      '时间安排合理性'
    ]
  }
]

// 模拟导师数据
export const MOCK_REVIEWERS: Reviewer[] = [
  {
    id: 'advisor_1',
    name: '张教授',
    avatar: '👨‍🏫',
    role: 'advisor',
    title: '博士生导师',
    expertise: ['人工智能', '机器学习'],
    color: '#ff4d4f'
  },
  {
    id: 'advisor_2',
    name: '李教授',
    avatar: '👩‍💻',
    role: 'committee',
    title: '答辩委员',
    expertise: ['数据挖掘', '算法设计'],
    color: '#1890ff'
  },
  {
    id: 'peer_1',
    name: '王同学',
    avatar: '👨‍🎓',
    role: 'peer',
    title: '同门师兄',
    expertise: ['自然语言处理'],
    color: '#52c41a'
  }
]

class CollaborativeReviewService {
  private comments: Map<string, Comment> = new Map()
  private reviewers: Map<string, Reviewer> = new Map()
  private reviewRounds: Map<string, ReviewRound> = new Map()
  private currentRound: ReviewRound | null = null
  private listeners: Set<(comments: Comment[]) => void> = new Set()

  constructor() {
    // 初始化模拟数据
    MOCK_REVIEWERS.forEach(r => this.reviewers.set(r.id, r))
  }

  // 开始新的审阅轮次
  startReviewRound(paperId: string, reviewerIds: string[]): ReviewRound {
    const roundNumber = this.currentRound ? this.currentRound.roundNumber + 1 : 1

    const round: ReviewRound = {
      id: `round_${Date.now()}`,
      roundNumber,
      status: 'active',
      startedAt: new Date().toISOString(),
      reviewers: reviewerIds
    }

    this.currentRound = round
    this.reviewRounds.set(round.id, round)

    return round
  }

  // 添加批注
  addComment(comment: Omit<Comment, 'id' | 'createdAt' | 'updatedAt' | 'replies' | 'reactions'>): Comment {
    const newComment: Comment = {
      ...comment,
      id: `comment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      replies: [],
      reactions: []
    }

    this.comments.set(newComment.id, newComment)
    this.notifyListeners()

    return newComment
  }

  // 回复批注
  addReply(commentId: string, reviewerId: string, content: string): Reply {
    const comment = this.comments.get(commentId)
    if (!comment) throw new Error('Comment not found')

    const reply: Reply = {
      id: `reply_${Date.now()}`,
      commentId,
      reviewerId,
      content,
      createdAt: new Date().toISOString()
    }

    comment.replies.push(reply)
    comment.updatedAt = new Date().toISOString()
    this.notifyListeners()

    return reply
  }

  // 更新批注状态
  updateCommentStatus(commentId: string, status: ReviewStatus): Comment {
    const comment = this.comments.get(commentId)
    if (!comment) throw new Error('Comment not found')

    comment.status = status
    comment.updatedAt = new Date().toISOString()
    this.notifyListeners()

    return comment
  }

  // 添加反应
  addReaction(commentId: string, reviewerId: string, type: Reaction['type']): void {
    const comment = this.comments.get(commentId)
    if (!comment) return

    const existingIndex = comment.reactions.findIndex(r => r.reviewerId === reviewerId)
    if (existingIndex >= 0) {
      comment.reactions[existingIndex].type = type
    } else {
      comment.reactions.push({ reviewerId, type })
    }

    this.notifyListeners()
  }

  // 获取论文的所有批注
  getPaperComments(paperId: string): Comment[] {
    return Array.from(this.comments.values())
      .filter(c => c.paperId === paperId)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  }

  // 获取指定段落的批注
  getSectionComments(paperId: string, sectionId: string): Comment[] {
    return this.getPaperComments(paperId)
      .filter(c => c.sectionId === sectionId)
  }

  // 获取审阅统计
  getReviewStats(paperId: string): ReviewStats {
    const comments = this.getPaperComments(paperId)

    const byType: Record<CommentType, number> = {
      suggestion: 0,
      question: 0,
      praise: 0,
      correction: 0,
      general: 0
    }

    const byReviewer: Record<string, number> = {}

    comments.forEach(c => {
      byType[c.type] = (byType[c.type] || 0) + 1
      byReviewer[c.reviewerId] = (byReviewer[c.reviewerId] || 0) + 1
    })

    return {
      totalComments: comments.length,
      resolvedComments: comments.filter(c => c.status === 'resolved').length,
      pendingComments: comments.filter(c => c.status === 'pending').length,
      byType,
      byReviewer
    }
  }

  // 获取所有审阅者
  getReviewers(): Reviewer[] {
    return Array.from(this.reviewers.values())
  }

  // 获取审阅者信息
  getReviewer(reviewerId: string): Reviewer | undefined {
    return this.reviewers.get(reviewerId)
  }

  // 获取当前审阅轮次
  getCurrentRound(): ReviewRound | null {
    return this.currentRound
  }

  // 完成审阅轮次
  completeReviewRound(roundId: string, summary: string): void {
    const round = this.reviewRounds.get(roundId)
    if (round) {
      round.status = 'completed'
      round.completedAt = new Date().toISOString()
      round.summary = summary
    }
  }

  // 订阅批注变化
  subscribe(callback: (comments: Comment[]) => void): () => void {
    this.listeners.add(callback)
    return () => this.listeners.delete(callback)
  }

  // 通知所有监听器
  private notifyListeners(): void {
    const allComments = Array.from(this.comments.values())
    this.listeners.forEach(cb => cb(allComments))
  }

  // 导出审阅报告
  exportReviewReport(paperId: string): string {
    const comments = this.getPaperComments(paperId)
    const stats = this.getReviewStats(paperId)

    return `
# 论文审阅报告

## 统计概览
- 总批注数：${stats.totalComments}
- 已解决：${stats.resolvedComments}
- 待处理：${stats.pendingComments}

## 批注详情
${comments.map(c => {
  const reviewer = this.getReviewer(c.reviewerId)
  return `
### ${reviewer?.name || '未知审阅者'} - ${this.getCommentTypeLabel(c.type)}
**位置**：${c.sectionId}
**状态**：${c.status}
**内容**：${c.content}
${c.replies.length > 0 ? `
**回复**：
${c.replies.map(r => `- ${this.getReviewer(r.reviewerId)?.name}: ${r.content}`).join('\n')}
` : ''}
`
}).join('\n')}

---
生成时间：${new Date().toLocaleString('zh-CN')}
    `.trim()
  }

  // 获取批注类型标签
  private getCommentTypeLabel(type: CommentType): string {
    const labels: Record<CommentType, string> = {
      suggestion: '建议',
      question: '问题',
      praise: '表扬',
      correction: '修改',
      general: '一般'
    }
    return labels[type]
  }

  // 模拟实时协作 - 生成随机批注
  simulateIncomingComment(paperId: string): void {
    const reviewers = this.getReviewers().filter(r => r.role !== 'student')
    const randomReviewer = reviewers[Math.floor(Math.random() * reviewers.length)]

    const types: CommentType[] = ['suggestion', 'question', 'praise', 'correction']
    const randomType = types[Math.floor(Math.random() * types.length)]

    const suggestions = [
      '这里需要补充更多文献支撑',
      '建议增加数据分析的深度',
      '这个论点很有说服力',
      '请检查格式是否符合规范',
      '可以考虑从另一个角度阐述',
      '这部分逻辑需要加强',
      '表述清晰，继续保持'
    ]

    this.addComment({
      reviewerId: randomReviewer.id,
      paperId,
      sectionId: 'section_1',
      type: randomType,
      content: suggestions[Math.floor(Math.random() * suggestions.length)],
      position: { start: 0, end: 0 },
      status: 'pending'
    })
  }
}

export const collaborativeReviewService = new CollaborativeReviewService()
export default collaborativeReviewService
