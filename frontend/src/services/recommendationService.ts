/**
 * 推荐服务 API
 * 智能文献推荐
 */

import { request } from './api'
import type { Article } from '@/types'

// 推荐项类型
export interface RecommendationItem {
  article_id: string
  score: number
  scores: Record<string, number>
  explanation: string
  article?: Partial<Article>
}

// 相似文献类型
export interface SimilarArticle {
  article_id: string
  similarity: number
  article?: Partial<Article>
}

// 热门文献类型
export interface TrendingArticle {
  article_id: string
  popularity: number
  article?: Partial<Article>
}

// 用户兴趣类型
export interface UserInterests {
  interests: Record<string, number>
}

// 是否使用 mock 数据
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.DEV

// Mock 数据
const mockDailyRecommendations: RecommendationItem[] = [
  {
    article_id: 'r1',
    score: 0.92,
    scores: { relevance: 0.9, timeliness: 0.95, authority: 0.88 },
    explanation: '与您的研究方向高度相关；近期发表的新研究',
    article: {
      id: 'r1',
      title: '人工智能在项目管理中的应用研究',
      abstract: '本文探讨了人工智能技术在项目管理领域的应用...',
      authors: [{ name: '张三' }, { name: '李四' }],
      sourceName: '管理科学学报',
      publicationYear: 2024,
      keywords: ['人工智能', '项目管理', '机器学习'],
      citationCount: 45,
    },
  },
  {
    article_id: 'r2',
    score: 0.87,
    scores: { relevance: 0.85, timeliness: 0.9, authority: 0.85 },
    explanation: '与您的研究领域相关；时效性较好',
    article: {
      id: 'r2',
      title: '基于深度学习的工程管理优化方法',
      abstract: '深度学习技术在工程管理中的应用日益广泛...',
      authors: [{ name: '王五' }, { name: '赵六' }],
      sourceName: '系统工程理论与实践',
      publicationYear: 2024,
      keywords: ['深度学习', '工程管理', '优化'],
      citationCount: 32,
    },
  },
  {
    article_id: 'r3',
    score: 0.82,
    scores: { relevance: 0.8, timeliness: 0.85, authority: 0.8 },
    explanation: '与您的研究方向相关',
    article: {
      id: 'r3',
      title: 'Machine Learning for Project Risk Prediction',
      abstract: 'This paper presents a machine learning approach...',
      authors: [{ name: 'John Smith' }, { name: 'Jane Doe' }],
      sourceName: 'Journal of Construction Engineering',
      publicationYear: 2023,
      keywords: ['Machine Learning', 'Risk Prediction', 'Project Management'],
      citationCount: 78,
    },
  },
]

const mockUserInterests: UserInterests = {
  interests: {
    '人工智能': 0.95,
    '项目管理': 0.88,
    '机器学习': 0.75,
    '风险管理': 0.65,
    '数据挖掘': 0.55,
  },
}

// 模拟延迟
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export const recommendationService = {
  /**
   * 获取每日推荐
   */
  getDailyRecommendations: async (limit: number = 10): Promise<{ data: RecommendationItem[] }> => {
    if (USE_MOCK) {
      await delay(500)
      return { data: mockDailyRecommendations.slice(0, limit) }
    }

    return request.get<RecommendationItem[]>('/recommendations/daily', { limit })
  },

  /**
   * 获取相似文献
   */
  getSimilarArticles: async (articleId: string, limit: number = 5): Promise<{ data: SimilarArticle[] }> => {
    if (USE_MOCK) {
      await delay(300)
      return {
        data: [
          { article_id: 's1', similarity: 0.85 },
          { article_id: 's2', similarity: 0.78 },
          { article_id: 's3', similarity: 0.72 },
        ].slice(0, limit),
      }
    }

    return request.get<SimilarArticle[]>(`/recommendations/similar/${articleId}`, { limit })
  },

  /**
   * 获取热门文献
   */
  getTrendingArticles: async (days: number = 7, limit: number = 10): Promise<{ data: TrendingArticle[] }> => {
    if (USE_MOCK) {
      await delay(300)
      return {
        data: [
          { article_id: 't1', popularity: 156 },
          { article_id: 't2', popularity: 142 },
          { article_id: 't3', popularity: 128 },
          { article_id: 't4', popularity: 115 },
          { article_id: 't5', popularity: 98 },
        ].slice(0, limit),
      }
    }

    return request.get<TrendingArticle[]>('/recommendations/trending', { days, limit })
  },

  /**
   * 记录用户行为
   */
  recordBehavior: async (articleId: string, behaviorType: string, duration: number = 0): Promise<{ message: string }> => {
    if (USE_MOCK) {
      await delay(100)
      console.log(`[Mock] 记录行为: ${behaviorType} on ${articleId}, duration: ${duration}`)
      return { message: '行为已记录' }
    }

    return request.post('/recommendations/behavior', {
      article_id: articleId,
      behavior_type: behaviorType,
      duration,
    })
  },

  /**
   * 获取用户兴趣
   */
  getUserInterests: async (): Promise<{ data: UserInterests }> => {
    if (USE_MOCK) {
      await delay(200)
      return { data: mockUserInterests }
    }

    return request.get<UserInterests>('/recommendations/interests')
  },

  /**
   * 更新用户兴趣
   */
  updateInterests: async (interests: Record<string, number>): Promise<{ message: string }> => {
    if (USE_MOCK) {
      await delay(200)
      console.log('[Mock] 更新兴趣:', interests)
      return { message: '兴趣已更新' }
    }

    return request.put('/recommendations/interests', interests)
  },
}

export default recommendationService

// 增强版推荐服务（新API）
export interface RecommendedPaper {
  id: string
  title: string
  authors: string[]
  abstract: string
  publication_year?: number
  source_name: string
  citation_count?: number
  relevance_score: number
  recommendation_reason: string
  recommendation_type: 'content_based' | 'collaborative' | 'trending' | 'recent' | 'related' | 'citation_based'
  pdf_url?: string
  source_url?: string
}

export interface RecommendationFeedback {
  paper_id: string
  feedback: 'like' | 'dislike' | 'neutral'
  reason?: string
}

export interface RecommendationSettings {
  research_interests: string[]
  preferred_sources: string[]
  exclude_read: boolean
  min_citation_count?: number
  year_range?: {
    start: number
    end: number
  }
}

export const enhancedRecommendationService = {
  /**
   * 获取个性化推荐
   */
  async getPersonalizedRecommendations(
    limit: number = 10
  ): Promise<RecommendedPaper[]> {
    const response = await request.get<RecommendedPaper[]>(
      '/recommendations/personalized',
      { limit }
    )
    return response.data
  },

  /**
   * 获取相关论文推荐
   */
  async getRelatedPapers(
    paperId: string,
    limit: number = 10
  ): Promise<RecommendedPaper[]> {
    const response = await request.get<RecommendedPaper[]>(
      `/recommendations/related/${paperId}`,
      { limit }
    )
    return response.data
  },

  /**
   * 获取热门论文
   */
  async getTrendingPapers(limit: number = 10): Promise<RecommendedPaper[]> {
    const response = await request.get<RecommendedPaper[]>(
      '/recommendations/trending',
      { limit }
    )
    return response.data
  },

  /**
   * 提交推荐反馈
   */
  async submitFeedback(
    feedback: RecommendationFeedback
  ): Promise<void> {
    await request.post('/recommendations/feedback', feedback)
  },

  /**
   * 获取推荐设置
   */
  async getSettings(): Promise<RecommendationSettings> {
    const response = await request.get<RecommendationSettings>(
      '/recommendations/settings'
    )
    return response.data
  },

  /**
   * 更新推荐设置
   */
  async updateSettings(
    settings: RecommendationSettings
  ): Promise<void> {
    await request.put('/recommendations/settings', settings)
  },

  /**
   * 解释推荐原因
   */
  async explainRecommendation(
    paperId: string
  ): Promise<{ explanation: string }> {
    const response = await request.get<{ explanation: string }>(
      `/recommendations/explain/${paperId}`
    )
    return response.data
  },
}
