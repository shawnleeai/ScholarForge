/**
 * 查重检测类型定义
 */

export type PlagiarismStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface PlagiarismMatch {
  /** 匹配 ID */
  id: string
  /** 匹配文本 */
  text: string
  /** 起始位置 */
  from: number
  /** 结束位置 */
  to: number
  /** 相似度百分比 */
  similarity: number
  /** 来源 */
  source: {
    type: 'web' | 'paper' | 'database'
    title: string
    url?: string
    author?: string
  }
}

export interface PlagiarismSection {
  /** 章节 ID */
  sectionId: string
  /** 章节标题 */
  sectionTitle: string
  /** 章节相似度 */
  similarity: number
  /** 匹配详情 */
  matches: PlagiarismMatch[]
}

export interface PlagiarismReport {
  /** 报告 ID */
  id: string
  /** 论文 ID */
  paperId: string
  /** 总体相似度 */
  overallSimilarity: number
  /** 状态 */
  status: PlagiarismStatus
  /** 检测时间 */
  checkedAt: string
  /** 检测字数 */
  wordCount: number
  /** 章节报告 */
  sections: PlagiarismSection[]
  /** 建议 */
  suggestions: string[]
}

export interface PlagiarismCheckRequest {
  paperId: string
  options?: {
    checkWeb?: boolean
    checkDatabase?: boolean
    checkPapers?: boolean
    excludeQuotes?: boolean
    excludeReferences?: boolean
  }
}

export interface PlagiarismCheckResponse {
  reportId: string
  status: PlagiarismStatus
  estimatedTime: number
}
