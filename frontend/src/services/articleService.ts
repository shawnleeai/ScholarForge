/**
 * 文献服务 API
 */

import { request } from './api'
import type { Article, LibraryItem, LibraryFolder, PaginationParams } from '@/types'

// 是否使用模拟API
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

const mockArticles: Article[] = [
  {
    id: 'a1',
    doi: '10.1016/j.ijproman.2024.01.001',
    title: 'Artificial Intelligence in Project Management: A Systematic Review',
    authors: [{ name: 'John Smith' }, { name: 'Jane Doe' }],
    abstract: 'This paper provides a comprehensive review...',
    keywords: ['AI', 'Project Management'],
    sourceType: 'journal',
    sourceName: 'Int. J. of Project Management',
    sourceDb: 'wos',
    publicationYear: 2024,
    citationCount: 45,
    indexedAt: '2024-01-15T00:00:00Z',
    updatedAt: '2024-01-15T00:00:00Z',
  },
  {
    id: 'a2',
    title: '基于人工智能的项目管理方法研究',
    authors: [{ name: '张三' }, { name: '李四' }],
    abstract: '本文研究了人工智能技术在项目管理中的应用...',
    keywords: ['人工智能', '项目管理'],
    sourceType: 'journal',
    sourceName: '管理科学学报',
    sourceDb: 'cnki',
    publicationYear: 2023,
    citationCount: 35,
    indexedAt: '2023-03-01T00:00:00Z',
    updatedAt: '2023-03-01T00:00:00Z',
  },
]

const getLocalLibrary = (): LibraryItem[] => {
  const stored = localStorage.getItem('scholarforge-library')
  if (stored) return JSON.parse(stored)
  return [
    {
      id: 'l1',
      article: mockArticles[0],
      isFavorite: true,
      isRead: true,
      tags: ['重要'],
      addedAt: '2026-02-15T00:00:00Z',
    },
  ]
}

const saveLocalLibrary = (items: LibraryItem[]) => {
  localStorage.setItem('scholarforge-library', JSON.stringify(items))
}

export const articleService = {
  /**
   * 搜索文献
   */
  search: async (params: {
    q: string
    sources?: string
    yearFrom?: number
    yearTo?: number
    page?: number
    pageSize?: number
  }) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500))
      const query = params.q.toLowerCase()
      const results = mockArticles.filter(a =>
        a.title.toLowerCase().includes(query) ||
        a.abstract?.toLowerCase().includes(query)
      )
      return {
        data: {
          items: results,
          total: results.length,
          page: params.page || 1,
          pageSize: params.pageSize || 20,
          totalPages: 1,
        }
      }
    }
    return request.get('/articles/search', {
      q: params.q,
      sources: params.sources,
      year_from: params.yearFrom,
      year_to: params.yearTo,
      page: params.page || 1,
      page_size: params.pageSize || 20,
    })
  },

  /**
   * 获取文献详情
   */
  getArticle: async (articleId: string) => {
    if (USE_MOCK) {
      const article = mockArticles.find(a => a.id === articleId)
      if (!article) throw { code: 404, message: '文献不存在' }
      return { data: article }
    }
    return request.get(`/articles/${articleId}`)
  },

  /**
   * 通过DOI获取文献
   */
  getByDoi: async (doi: string) => {
    if (USE_MOCK) {
      const article = mockArticles.find(a => a.doi === doi)
      if (!article) throw { code: 404, message: '文献不存在' }
      return { data: article }
    }
    return request.get(`/articles/doi/${encodeURIComponent(doi)}`)
  },

  /**
   * 获取文献库
   */
  getLibrary: async (params?: { folderId?: string; page?: number; pageSize?: number }) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      const items = getLocalLibrary()
      return {
        data: {
          items,
          total: items.length,
          page: params?.page || 1,
          pageSize: params?.pageSize || 20,
          totalPages: 1,
        }
      }
    }
    return request.get('/library', {
      folder_id: params?.folderId,
      page: params?.page || 1,
      page_size: params?.pageSize || 20,
    })
  },

  /**
   * 添加到文献库
   */
  addToLibrary: async (data: { articleId: string; folderId?: string; tags?: string[]; notes?: string }) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const article = mockArticles.find(a => a.id === data.articleId)
      if (!article) throw { code: 404, message: '文献不存在' }

      const items = getLocalLibrary()
      const newItem: LibraryItem = {
        id: generateId(),
        article,
        isFavorite: false,
        isRead: false,
        tags: data.tags || [],
        notes: data.notes,
        addedAt: new Date().toISOString(),
      }
      items.unshift(newItem)
      saveLocalLibrary(items)
      return { data: newItem }
    }
    return request.post('/library', {
      article_id: data.articleId,
      folder_id: data.folderId,
      tags: data.tags,
      notes: data.notes,
    })
  },

  /**
   * 更新文献库项
   */
  updateLibraryItem: async (articleId: string, data: Partial<LibraryItem>) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const items = getLocalLibrary()
      const index = items.findIndex(i => i.article.id === articleId)
      if (index !== -1) {
        items[index] = { ...items[index], ...data }
        saveLocalLibrary(items)
        return { data: items[index] }
      }
      return { data: null }
    }
    return request.put(`/library/${articleId}`, data)
  },

  /**
   * 从文献库移除
   */
  removeFromLibrary: async (articleId: string) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const items = getLocalLibrary()
      saveLocalLibrary(items.filter(i => i.article.id !== articleId))
      return { code: 200 }
    }
    return request.delete(`/library/${articleId}`)
  },

  /**
   * 获取文件夹列表
   */
  getFolders: async () => {
    if (USE_MOCK) {
      return {
        data: [
          { id: 'f1', name: '重要文献', color: '#f5222d', createdAt: new Date().toISOString(), articleCount: 1 },
          { id: 'f2', name: '待阅读', color: '#1890ff', createdAt: new Date().toISOString(), articleCount: 0 },
        ] as LibraryFolder[]
      }
    }
    return request.get('/library/folders')
  },

  /**
   * 创建文件夹
   */
  createFolder: async (data: { name: string; description?: string; color?: string }) => {
    if (USE_MOCK) {
      return {
        data: {
          id: generateId(),
          ...data,
          createdAt: new Date().toISOString(),
          articleCount: 0,
        } as LibraryFolder
      }
    }
    return request.post('/library/folders', data)
  },

  /**
   * 更新文件夹
   */
  updateFolder: async (folderId: string, data: Partial<LibraryFolder>) => {
    if (USE_MOCK) {
      return { data: { id: folderId, ...data } }
    }
    return request.put(`/library/folders/${folderId}`, data)
  },

  /**
   * 删除文件夹
   */
  deleteFolder: async (folderId: string) => {
    if (USE_MOCK) {
      return { code: 200 }
    }
    return request.delete(`/library/folders/${folderId}`)
  },
}
