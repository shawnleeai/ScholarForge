/**
 * 期刊匹配服务
 */

import api from './api'

export interface Journal {
  id: string
  name: string
  issn?: string
  publisher?: string
  subject_areas: string[]
  impact_factor?: number
  h_index?: number
  acceptance_rate?: number
  review_cycle_days?: number
  is_open_access: boolean
  submission_url?: string
}

export interface JournalDetail extends Journal {
  description?: string
  scope?: string
  language: string
  keywords: string[]
  sjr?: number
  publication_fee?: number
  apc?: number
}

export interface MatchRequest {
  paper_id: string
  title?: string
  abstract?: string
  keywords?: string[]
  field?: string
}

export interface MatchResult {
  journal: Journal
  match_score: number
  match_reasons: string[]
  recommendations: string[]
  estimated_acceptance_rate?: number
  estimated_review_time?: number
}

export interface SubmissionRecord {
  id: string
  paper_id: string
  journal_id: string
  journal_name: string
  status: 'draft' | 'submitted' | 'under_review' | 'revision_required' | 'accepted' | 'rejected' | 'withdrawn'
  manuscript_id?: string
  submitted_at?: string
  first_decision_at?: string
  final_decision_at?: string
  decision?: string
  notes?: string
}

export interface JournalStats {
  total_journals: number
  by_type: Record<string, number>
  by_ranking: Record<string, number>
  by_subject: Record<string, number>
  average_impact_factor: number
  average_acceptance_rate: number
}

export const journalService = {
  // 期刊匹配
  matchJournals: (data: MatchRequest) =>
    api.post('/journals/match', data),

  // 基于论文ID匹配
  matchByPaperId: (paperId: string) =>
    api.post(`/journals/match/${paperId}`),

  // 获取期刊列表
  getJournals: (params?: {
    subject_area?: string
    min_impact_factor?: number
    max_impact_factor?: number
    search?: string
    page?: number
    page_size?: number
  }) => api.get('/journals', { params }),

  // 获取期刊详情
  getJournal: (journalId: string) =>
    api.get(`/journals/${journalId}`),

  // 对比期刊
  compareJournals: (journalIds: string[]) =>
    api.post('/journals/compare', null, { params: { journal_ids: journalIds } }),

  // 获取投稿记录
  getSubmissions: (params?: {
    status?: string
    page?: number
    page_size?: number
  }) => api.get('/submissions', { params }),

  // 创建投稿记录
  createSubmission: (data: {
    paper_id: string
    journal_id: string
    manuscript_id?: string
    notes?: string
  }) => api.post('/submissions', data),

  // 更新投稿记录
  updateSubmission: (submissionId: string, data: Partial<SubmissionRecord>) =>
    api.put(`/submissions/${submissionId}`, data),

  // 删除投稿记录
  deleteSubmission: (submissionId: string) =>
    api.delete(`/submissions/${submissionId}`),

  // 获取匹配历史
  getMatchHistory: (params?: { paper_id?: string; limit?: number }) =>
    api.get('/journals/matches/history', { params }),

  // 获取期刊统计
  getStats: () =>
    api.get('/journals/stats/overview'),
}

export default journalService
