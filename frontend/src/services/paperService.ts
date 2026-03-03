/**
 * 论文服务 API
 */

import { request } from './api'
import type { Paper, PaperSection, PaginationParams } from '@/types'

// 是否使用模拟API
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

// 本地存储的论文数据（模拟模式使用）
const getLocalPapers = (): Paper[] => {
  const stored = localStorage.getItem('scholarforge-papers')
  if (stored) return JSON.parse(stored)
  return [
    {
      id: '1',
      title: 'AI协同项目管理在学术论文辅助工具开发中的应用研究',
      abstract: '本研究探讨人工智能技术如何提升学术论文写作效率...',
      keywords: ['AI', '项目管理', '学术论文'],
      paperType: 'thesis',
      status: 'in_progress',
      language: 'zh',
      ownerId: '1',
      citationStyle: 'gb-t-7714-2015',
      wordCount: 15000,
      pageCount: 50,
      figureCount: 8,
      tableCount: 5,
      referenceCount: 45,
      createdAt: '2026-02-01T00:00:00Z',
      updatedAt: '2026-02-28T12:00:00Z',
    },
    {
      id: '2',
      title: '基于深度学习的工程管理决策支持系统研究',
      abstract: '本文研究深度学习在工程管理决策中的应用...',
      keywords: ['深度学习', '工程管理'],
      paperType: 'thesis',
      status: 'draft',
      language: 'zh',
      ownerId: '1',
      citationStyle: 'gb-t-7714-2015',
      wordCount: 5000,
      pageCount: 20,
      figureCount: 3,
      tableCount: 2,
      referenceCount: 20,
      createdAt: '2026-01-15T00:00:00Z',
      updatedAt: '2026-02-20T00:00:00Z',
    },
  ]
}

const saveLocalPapers = (papers: Paper[]) => {
  localStorage.setItem('scholarforge-papers', JSON.stringify(papers))
}

export const paperService = {
  /**
   * 获取论文列表
   */
  getPapers: async (params: PaginationParams & { status?: string; includeCollab?: boolean }) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      const papers = getLocalPapers()
      const filtered = params.status ? papers.filter(p => p.status === params.status) : papers
      return {
        data: {
          items: filtered,
          total: filtered.length,
          page: params.page || 1,
          pageSize: params.pageSize || 20,
          totalPages: 1,
        }
      }
    }
    return request.get('/papers', params)
  },

  /**
   * 获取论文详情
   */
  getPaper: async (paperId: string) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const papers = getLocalPapers()
      const paper = papers.find(p => p.id === paperId)
      if (!paper) throw { code: 404, message: '论文不存在' }
      return { data: paper }
    }
    return request.get(`/papers/${paperId}`)
  },

  /**
   * 创建论文
   */
  createPaper: async (data: Partial<Paper>) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 400))
      const newPaper: Paper = {
        id: generateId(),
        title: data.title || '未命名论文',
        abstract: data.abstract || '',
        keywords: data.keywords || [],
        paperType: data.paperType || 'thesis',
        status: 'draft',
        language: 'zh',
        ownerId: '1',
        citationStyle: 'gb-t-7714-2015',
        wordCount: 0,
        pageCount: 0,
        figureCount: 0,
        tableCount: 0,
        referenceCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }
      const papers = getLocalPapers()
      papers.unshift(newPaper)
      saveLocalPapers(papers)
      return { data: newPaper }
    }
    return request.post('/papers', data)
  },

  /**
   * 更新论文
   */
  updatePaper: async (paperId: string, data: Partial<Paper>) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const papers = getLocalPapers()
      const index = papers.findIndex(p => p.id === paperId)
      if (index === -1) throw { code: 404, message: '论文不存在' }
      papers[index] = { ...papers[index], ...data, updatedAt: new Date().toISOString() }
      saveLocalPapers(papers)
      return { data: papers[index] }
    }
    return request.put(`/papers/${paperId}`, data)
  },

  /**
   * 删除论文
   */
  deletePaper: async (paperId: string) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const papers = getLocalPapers()
      saveLocalPapers(papers.filter(p => p.id !== paperId))
      return { code: 200 }
    }
    return request.delete(`/papers/${paperId}`)
  },

  /**
   * 获取论文章节
   */
  getSections: async (paperId: string) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      return {
        data: [
          { id: 's1', paperId: '1', title: '摘要', content: '本文研究了AI协同项目管理...', orderIndex: 0, sectionType: 'abstract', wordCount: 300, status: 'completed', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
          { id: 's2', paperId: '1', title: '第一章 绪论', content: '## 1.1 研究背景\n\n随着人工智能技术的快速发展...', orderIndex: 1, sectionType: 'chapter', wordCount: 2500, status: 'in_progress', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
          { id: 's3', paperId: '1', title: '第二章 文献综述', content: '', orderIndex: 2, sectionType: 'chapter', wordCount: 0, status: 'draft', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
          { id: 's4', paperId: '1', title: '第三章 研究方法', content: '', orderIndex: 3, sectionType: 'chapter', wordCount: 0, status: 'draft', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
          { id: 's5', paperId: '1', title: '第四章 研究结果', content: '', orderIndex: 4, sectionType: 'chapter', wordCount: 0, status: 'draft', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
          { id: 's6', paperId: '1', title: '第五章 结论与展望', content: '', orderIndex: 5, sectionType: 'chapter', wordCount: 0, status: 'draft', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
        ] as PaperSection[]
      }
    }
    return request.get(`/papers/${paperId}/sections`)
  },

  /**
   * 创建章节
   */
  createSection: async (paperId: string, data: { title?: string; content?: string }) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      return {
        data: {
          id: generateId(),
          paperId,
          title: data.title || '新章节',
          content: data.content || '',
          orderIndex: 0,
          wordCount: 0,
          status: 'draft',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
      }
    }
    return request.post(`/papers/${paperId}/sections`, data)
  },

  /**
   * 更新章节
   */
  updateSection: async (sectionId: string, data: Partial<PaperSection>) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      return {
        data: {
          id: sectionId,
          ...data,
          wordCount: data.content?.length || 0,
          updatedAt: new Date().toISOString(),
        }
      }
    }
    return request.put(`/papers/sections/${sectionId}`, data)
  },

  /**
   * 删除章节
   */
  deleteSection: async (sectionId: string) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      return { code: 200 }
    }
    return request.delete(`/papers/sections/${sectionId}`)
  },

  /**
   * 获取版本历史
   */
  getVersions: async (paperId: string) => {
    if (USE_MOCK) {
      return {
        data: [
          { id: 'v1', paperId, versionNumber: 1, changeSummary: '初始版本', createdAt: '2026-02-01T00:00:00Z' },
          { id: 'v2', paperId, versionNumber: 2, changeSummary: '完成绪论', createdAt: '2026-02-15T00:00:00Z' },
        ]
      }
    }
    return request.get(`/papers/${paperId}/versions`)
  },

  /**
   * 创建版本
   */
  createVersion: async (paperId: string, changeSummary?: string) => {
    if (USE_MOCK) {
      return { data: { id: generateId(), paperId, versionNumber: 3, changeSummary } }
    }
    return request.post(`/papers/${paperId}/versions`, { change_summary: changeSummary })
  },

  /**
   * 导出论文
   */
  exportPaper: async (paperId: string, format: string) => {
    if (USE_MOCK) {
      return {
        data: {
          download_url: `https://storage.scholarforge.cn/exports/${paperId}.${format}`,
          format,
          file_size: 1024000,
          expires_at: new Date(Date.now() + 86400000).toISOString(),
        }
      }
    }
    return request.post(`/papers/${paperId}/export`, { format })
  },

  /**
   * 获取模板列表
   */
  getTemplates: async () => {
    if (USE_MOCK) {
      return {
        data: [
          { id: 't1', name: '浙江大学硕士学位论文', description: '浙大硕士论文模板', sourceType: 'system' },
          { id: 't2', name: 'GB/T 7714-2015 参考文献格式', description: '国标参考文献格式', sourceType: 'system' },
        ]
      }
    }
    return request.get('/templates')
  },

  /**
   * 获取协作者列表
   */
  getCollaborators: async (paperId: string) => {
    if (USE_MOCK) {
      return { data: [] }
    }
    return request.get(`/papers/${paperId}/collaborators`)
  },

  /**
   * 添加协作者
   */
  addCollaborator: async (paperId: string, data: { userEmail: string; role: string }) => {
    if (USE_MOCK) {
      return { data: { id: generateId(), ...data } }
    }
    return request.post(`/papers/${paperId}/collaborators`, data)
  },
}
