/**
 * 参考文献服务
 * 管理文献库、引用格式化、导入导出
 */

import api from './api'

export type PublicationType = 'journal' | 'conference' | 'book' | 'thesis' | 'report' | 'online' | 'other'
export type CitationStyle = 'apa' | 'mla' | 'chicago' | 'gb7714' | 'ieee' | 'harvard' | 'vancouver'

export interface Reference {
  id: string
  user_id: string
  paper_id?: string
  folder_id?: string
  title: string
  authors: string[]
  publication_year?: number
  journal_name?: string
  volume?: string
  issue?: string
  pages?: string
  doi?: string
  pmid?: string
  url?: string
  abstract?: string
  keywords: string[]
  publisher?: string
  publication_type: PublicationType
  language: string
  pdf_url?: string
  tags: string[]
  notes?: string
  rating?: number
  is_important: boolean
  is_read: boolean
  cited_times: number
  category?: string
  source_db?: string
  added_at: string
  updated_at: string
  last_accessed_at?: string
}

export interface ReferenceFilters {
  paper_id?: string
  folder_id?: string
  publication_type?: PublicationType
  is_important?: boolean
  is_read?: boolean
  year_from?: number
  year_to?: number
  tags?: string[]
  search?: string
  order_by?: string
}

export interface Folder {
  id: string
  user_id: string
  name: string
  description?: string
  color: string
  parent_id?: string
  sort_order: number
  item_count: number
  created_at: string
  updated_at: string
}

export interface Citation {
  id: string
  paper_id: string
  citing_ref_id: string
  citing_ref?: Reference
  cited_ref_id?: string
  citing_position?: string
  citation_text?: string
  citation_style: CitationStyle
  formatted_citation?: string
  citation_number: number
  created_at: string
}

export interface ImportTask {
  id: string
  user_id: string
  paper_id?: string
  source_type: string
  file_name?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_count: number
  success_count: number
  failed_count: number
  error_message?: string
  created_at: string
  completed_at?: string
}

export interface ReferenceStatistics {
  total: number
  read_count: number
  unread_count: number
  important_count: number
  by_type: Record<string, number>
  with_year_count: number
  avg_rating?: number
  year_distribution: Array<{ year: number; count: number }>
  top_authors: Array<{ author: string; count: number }>
  top_journals: Array<{ journal_name: string; count: number }>
}

export const referenceService = {
  // ========== 参考文献 CRUD ==========

  getReferences: (filters?: ReferenceFilters, page = 1, page_size = 20) =>
    api.get('/references', {
      params: {
        ...filters,
        page,
        page_size,
        tags: filters?.tags?.join(',')
      }
    }),

  getReference: (id: string) =>
    api.get(`/references/${id}`),

  createReference: (data: Partial<Reference>) =>
    api.post('/references', data),

  updateReference: (id: string, data: Partial<Reference>) =>
    api.put(`/references/${id}`, data),

  deleteReference: (id: string) =>
    api.delete(`/references/${id}`),

  // ========== 标签管理 ==========

  getTags: () =>
    api.get('/references/tags/list'),

  addTags: (referenceId: string, tags: string[]) =>
    api.post(`/references/${referenceId}/tags`, { tags }),

  removeTags: (referenceId: string, tags: string[]) =>
    api.delete(`/references/${referenceId}/tags`, { data: { tags } }),

  // ========== 阅读状态 ==========

  markAsRead: (referenceId: string, isRead: boolean) =>
    api.patch(`/references/${referenceId}/read`, null, {
      params: { is_read: isRead }
    }),

  // ========== 文件夹管理 ==========

  getFolders: () =>
    api.get('/reference-folders'),

  createFolder: (data: { name: string; description?: string; color?: string; parent_id?: string }) =>
    api.post('/reference-folders', data),

  updateFolder: (id: string, data: Partial<Folder>) =>
    api.put(`/reference-folders/${id}`, data),

  deleteFolder: (id: string) =>
    api.delete(`/reference-folders/${id}`),

  moveToFolder: (folderId: string | null, referenceIds: string[]) =>
    api.post('/references/move-to-folder', {
      folder_id: folderId,
      reference_ids: referenceIds
    }),

  // ========== 引用格式化 ==========

  formatCitations: (referenceIds: string[], style: CitationStyle) =>
    api.post('/references/format-citations', {
      reference_ids: referenceIds,
      style
    }),

  formatSingleCitation: (reference: Reference, style: CitationStyle): string => {
    // 客户端格式化（简单实现）
    const authors = reference.authors || []
    const year = reference.publication_year
    const title = reference.title
    const journal = reference.journal_name

    switch (style) {
      case 'gb7714':
        const authorStr = authors.length <= 3
          ? authors.join(', ')
          : authors.slice(0, 3).join(', ') + ', 等'
        return `${authorStr}. ${title}[J]. ${journal || ''}, ${year || ''}.`

      case 'apa':
        const apaAuthor = authors.length > 1
          ? authors[0].split(' ').pop() + ' et al.'
          : authors[0]?.split(' ').pop() || ''
        return `${apaAuthor} (${year}). ${title}. ${journal || ''}.`

      case 'ieee':
        const ieeeAuthor = authors.length > 6
          ? authors.slice(0, 6).join(', ') + ', et al.'
          : authors.join(', ')
        return `${ieeeAuthor}, "${title}," ${journal || ''}, ${year || ''}.`

      default:
        return `${authors.join(', ')}. ${title}. ${journal || ''}, ${year || ''}.`
    }
  },

  // ========== 导入导出 ==========

  previewImport: (file: File, sourceType: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('source_type', sourceType)

    return api.post('/references/import/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  importReferences: (file: File, sourceType: string, paperId?: string, folderId?: string, skipDuplicates = true) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('source_type', sourceType)
    if (paperId) formData.append('paper_id', paperId)
    if (folderId) formData.append('folder_id', folderId)
    formData.append('skip_duplicates', String(skipDuplicates))

    return api.post('/references/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  importFromZotero: (credentials: { user_id: string; api_key: string }, collectionKey?: string, paperId?: string, folderId?: string) =>
    api.post('/references/import/zotero', {
      credentials,
      collection_key: collectionKey,
      paper_id: paperId,
      folder_id: folderId
    }),

  exportReferences: (data: {
    reference_ids?: string[]
    folder_id?: string
    paper_id?: string
    format: 'bibtex' | 'ris' | 'csv' | 'json'
  }) =>
    api.post('/references/export', data),

  // ========== 统计分析 ==========

  getStatistics: (paperId?: string) =>
    api.get('/references/statistics/overview', {
      params: { paper_id: paperId }
    }),

  // ========== 元数据提取 ==========

  extractMetadata: (identifier?: string, identifierType?: 'doi' | 'pmid', text?: string) =>
    api.post('/references/extract-metadata', {
      identifier,
      identifier_type: identifierType,
      text
    }),

  // ========== 论文引用管理 ==========

  getPaperCitations: (paperId: string) =>
    api.get(`/papers/${paperId}/citations`),

  addCitation: (paperId: string, data: {
    citing_ref_id: string
    citing_position?: string
    citation_text?: string
    citation_style?: CitationStyle
  }) =>
    api.post(`/papers/${paperId}/citations`, data),

  deleteCitation: (paperId: string, citationId: string) =>
    api.delete(`/papers/${paperId}/citations/${citationId}`),
}

export default referenceService
