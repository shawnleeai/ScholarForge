/**
 * 查重检测服务 API
 */

import api, { request } from './api'
import type {
  PlagiarismReport,
  PlagiarismCheckRequest,
  PlagiarismCheckResponse,
} from '@/types/plagiarism'

export type CheckStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical'

export interface SimilarityMatch {
  text: string
  start_index: number
  end_index: number
  similarity: number
  source_id: string
  source_title?: string
  source_url?: string
}

export interface SimilaritySource {
  id: string
  title: string
  type: string
  url?: string
  similarity: number
  match_count: number
}

export interface PlagiarismCheck {
  id: string
  user_id: string
  paper_id?: string
  task_name?: string
  status: CheckStatus
  engine: string
  overall_similarity?: number
  internet_similarity?: number
  publications_similarity?: number
  student_papers_similarity?: number
  matches?: SimilarityMatch[]
  sources?: SimilaritySource[]
  report_url?: string
  error_message?: string
  submitted_at: string
  completed_at?: string
}

export interface PlagiarismSettings {
  default_engine: string
  exclude_bibliography: boolean
  exclude_quotes: boolean
  exclude_small_sources: boolean
  small_source_threshold: number
  sensitivity: 'low' | 'medium' | 'high'
  notify_on_complete: boolean
  notify_threshold: number
}

export interface PlagiarismStatistics {
  total_checks: number
  completed_checks: number
  failed_checks: number
  average_similarity: number
  max_similarity: number
  min_similarity: number
  recent_trend: Array<{ date: string; similarity: number }>
}

// 是否使用模拟模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

// 模拟报告数据
const mockReport: PlagiarismReport = {
  id: 'report-1',
  paperId: '1',
  overallSimilarity: 15.8,
  status: 'completed',
  checkedAt: new Date().toISOString(),
  wordCount: 15000,
  sections: [
    {
      sectionId: 's1',
      sectionTitle: '摘要',
      similarity: 5.2,
      matches: [],
    },
    {
      sectionId: 's2',
      sectionTitle: '第一章 绪论',
      similarity: 18.5,
      matches: [
        {
          id: 'm1',
          text: '随着人工智能技术的快速发展，其在各个领域的应用越来越广泛。',
          from: 100,
          to: 150,
          similarity: 95,
          source: {
            type: 'web',
            title: 'AI技术发展报告 2024',
            url: 'https://example.com/ai-report',
            author: '张三',
          },
        },
        {
          id: 'm2',
          text: '深度学习作为机器学习的一个重要分支，近年来取得了显著的突破。',
          from: 200,
          to: 260,
          similarity: 88,
          source: {
            type: 'paper',
            title: '深度学习研究综述',
            author: '李四',
          },
        },
      ],
    },
    {
      sectionId: 's3',
      sectionTitle: '第二章 文献综述',
      similarity: 25.3,
      matches: [
        {
          id: 'm3',
          text: '项目管理是指运用专门的知识、技能、工具和方法，使项目能够在有限资源限定条件下，实现或超过设定的需求和期望的过程。',
          from: 50,
          to: 180,
          similarity: 92,
          source: {
            type: 'database',
            title: '项目管理知识体系指南',
          },
        },
      ],
    },
  ],
  suggestions: [
    '建议对第一章的 AI 技术发展部分进行改写，加入更多原创观点',
    '文献综述部分引用较多，建议增加自己的分析和评述',
    '部分段落可以添加引用标注，避免被判定为抄袭',
  ],
}

export const plagiarismService = {
  /**
   * 发起查重检测
   */
  startCheck: async (
    data: PlagiarismCheckRequest
  ): Promise<{ data: PlagiarismCheckResponse }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500))
      return {
        data: {
          reportId: generateId(),
          status: 'processing',
          estimatedTime: 120,
        }
      }
    }
    return request.post(`/papers/${data.paperId}/plagiarism/check`, data.options)
  },

  /**
   * 获取查重报告
   */
  getReport: async (
    paperId: string,
    reportId?: string
  ): Promise<{ data: PlagiarismReport }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      return {
        data: {
          ...mockReport,
          paperId,
          id: reportId || mockReport.id,
        }
      }
    }
    const url = reportId
      ? `/papers/${paperId}/plagiarism/reports/${reportId}`
      : `/papers/${paperId}/plagiarism/reports/latest`
    return request.get(url)
  },

  /**
   * 获取查重历史
   */
  getReportHistory: async (
    paperId: string
  ): Promise<{ data: { id: string; checkedAt: string; similarity: number }[] }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      return {
        data: [
          { id: 'r1', checkedAt: '2026-02-28T10:00:00Z', similarity: 15.8 },
          { id: 'r2', checkedAt: '2026-02-25T14:30:00Z', similarity: 18.2 },
          { id: 'r3', checkedAt: '2026-02-20T09:15:00Z', similarity: 22.5 },
        ]
      }
    }
    return request.get(`/papers/${paperId}/plagiarism/reports`)
  },

  /**
   * 下载查重报告
   */
  downloadReport: async (
    paperId: string,
    reportId: string
  ): Promise<{ data: { downloadUrl: string } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      return {
        data: {
          downloadUrl: `https://storage.scholarforge.cn/plagiarism/${reportId}.pdf`,
        }
      }
    }
    return request.get(`/papers/${paperId}/plagiarism/reports/${reportId}/download`)
  },

  /**
   * 获取降重建议
   */
  getRewriteSuggestions: async (
    text: string
  ): Promise<{ data: { original: string; suggestions: Array<{ text: string; type: string; reduction: number }> } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 800))

      // 模拟降重建议
      const suggestions = []

      // 生成几个改写版本
      suggestions.push({
        text: text
          .replace(/随着/g, '伴随')
          .replace(/快速发展/g, '迅猛进步')
          .replace(/越来越/g, '日益')
          .replace(/应用/g, '运用'),
        type: 'paraphrase',
        reduction: 35,
      })

      suggestions.push({
        text: `研究表明，${text.replace(/。$/, '')}。这一趋势在近年来尤为明显。`,
        type: 'expand',
        reduction: 20,
      })

      suggestions.push({
        text: text.split('，').reverse().join('，').replace(/^(.)/g, (m) => m),
        type: 'restructure',
        reduction: 45,
      })

      return {
        data: {
          original: text,
          suggestions,
        }
      }
    }

    return request.post('/plagiarism/rewrite-suggestions', { text })
  },

  /**
   * 应用降重修改
   */
  applyRewrite: async (
    paperId: string,
    sectionId: string,
    data: { original: string; rewritten: string }
  ): Promise<{ data: { success: boolean } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      return { data: { success: true } }
    }

    return request.put(`/papers/${paperId}/sections/${sectionId}/rewrite`, data)
  },

  // ========== 新增 API ==========

  submitCheck: (data: { paper_id?: string; task_name?: string; engine?: string }) =>
    api.post('/plagiarism/check', data),

  uploadAndCheck: (file: File, engine: string = 'local', paperId?: string, taskName?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('engine', engine)
    if (paperId) formData.append('paper_id', paperId)
    if (taskName) formData.append('task_name', taskName)

    return api.post('/plagiarism/check/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  getChecks: (params?: { paper_id?: string; status?: string; page?: number; page_size?: number }) =>
    api.get('/plagiarism/checks', { params }),

  getCheck: (id: string) =>
    api.get(`/plagiarism/check/${id}`),

  getCheckStatus: (id: string) =>
    api.get(`/plagiarism/check/${id}/status`),

  getCheckReport: (id: string) =>
    api.get(`/plagiarism/check/${id}/report`),

  deleteCheck: (id: string) =>
    api.delete(`/plagiarism/check/${id}`),

  getReduceSuggestions: (checkId: string, segmentIds?: string[]) =>
    api.post('/plagiarism/reduce', { check_id: checkId, segment_ids: segmentIds }),

  getWhitelist: (paperId?: string) =>
    api.get('/plagiarism/whitelist', { params: { paper_id: paperId } }),

  addWhitelist: (data: { paper_id?: string; content: string; reason?: string; source?: string }) =>
    api.post('/plagiarism/whitelist', data),

  deleteWhitelist: (id: string) =>
    api.delete(`/plagiarism/whitelist/${id}`),

  getSettings: () =>
    api.get('/plagiarism/settings'),

  updateSettings: (data: Partial<PlagiarismSettings>) =>
    api.put('/plagiarism/settings', data),

  getHistory: (params?: { paper_id?: string; page?: number; page_size?: number }) =>
    api.get('/plagiarism/history', { params }),

  getPaperHistory: (paperId: string) =>
    api.get(`/plagiarism/paper/${paperId}/history`),

  getStatistics: () =>
    api.get('/plagiarism/statistics'),

  getAvailableEngines: () =>
    api.get('/plagiarism/engines'),
}
