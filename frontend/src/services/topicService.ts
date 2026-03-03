/**
 * 选题助手服务
 */

import api from './api'

export interface TopicSuggestionRequest {
  field: string
  keywords: string[]
  interests?: string[]
  degree_level: 'bachelor' | 'master' | 'doctor'
}

export interface TopicIdea {
  id: string
  title: string
  description: string
  keywords: string[]
  research_gaps: Array<{
    type: string
    description: string
    significance: string
  }>
  feasibility_score: number
  feasibility_level: 'high' | 'medium' | 'low' | 'risky'
  required_resources: Array<{
    resource_type: string
    description: string
    availability: string
    estimated_cost?: string
  }>
  estimated_duration_months: number
  risks: string[]
  mitigation_strategies: string[]
  related_papers: string[]
  recent_trends: string[]
}

export interface ResearchPlan {
  topic: string
  total_weeks: number
  phases: Array<{
    name: string
    start_week: number
    end_week: number
  }>
  tasks: Array<{
    id: string
    title: string
    description: string
    phase: string
    start_week: number
    end_week: number
    dependencies: string[]
    status: string
    priority: string
  }>
  milestones: Array<{
    week: number
    name: string
    type: string
  }>
  gantt_chart: {
    tasks: Array<{
      id: string
      name: string
      start: string
      end: string
      progress: number
      dependencies: string[]
    }>
    milestones: Array<{
      name: string
      date: string
    }>
  }
}

export interface TrendAnalysis {
  field: string
  trends: Array<{
    keyword: string
    trend_data: Array<{
      year: number
      count: number
      growth_rate: number
    }>
    current_hotness: number
    predicted_trend: 'rising' | 'stable' | 'declining'
    related_keywords: string[]
  }>
  hot_topics: string[]
  emerging_topics: string[]
  declining_topics: string[]
}

export const topicService = {
  // 获取选题建议
  suggestTopics: (data: TopicSuggestionRequest) =>
    api.post('/topics/suggest', data),

  // 深度可行性分析
  analyzeFeasibility: (topicId: string, detailed?: boolean) =>
    api.post(`/topics/analyze/${topicId}`, null, {
      params: { detailed },
    }),

  // 生成开题报告大纲
  generateProposal: (params: {
    topic: string
    field: string
    keywords?: string
  }) => api.post('/topics/proposal/generate', null, { params }),

  // 研究趋势分析
  analyzeTrends: (params: {
    field: string
    keywords?: string
    years?: number
  }) => api.get('/topics/trends', { params }),

  // 生成研究计划
  generateResearchPlan: (params: {
    topic: string
    start_date?: string
    duration_months?: number
  }) => api.post('/topics/plan/generate', null, { params }),

  // 收藏选题
  saveTopic: (topicId: string) =>
    api.post(`/topics/favorites/${topicId}`),

  // 获取收藏的选题
  getSavedTopics: (params?: { page?: number; pageSize?: number }) =>
    api.get('/topics/favorites', { params }),
}

export default topicService
