/**
 * 模板服务 API
 */

import { request } from './api'

// 是否使用模拟模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export interface PaperTemplate {
  id: string
  name: string
  description: string
  type: 'thesis' | 'journal' | 'conference' | 'report'
  institution?: string
  thumbnail?: string
  author?: string
  downloadCount: number
  rating: number
  tags: string[]
  sections: TemplateSection[]
  format: TemplateFormat
  createdAt: string
  updatedAt: string
}

export interface TemplateSection {
  id: string
  title: string
  orderIndex: number
  required: boolean
  placeholder?: string
}

export interface TemplateFormat {
  fontFamily: string
  fontSize: number
  lineHeight: number
  margins: {
    top: number
    bottom: number
    left: number
    right: number
  }
  headingStyles: Record<string, { fontSize: number; bold: boolean }>
}

// 模拟模板数据
const mockTemplates: PaperTemplate[] = [
  {
    id: 't1',
    name: '浙江大学硕士学位论文',
    description: '浙江大学硕士学位论文标准模板，符合学校格式要求',
    type: 'thesis',
    institution: '浙江大学',
    author: 'ScholarForge',
    downloadCount: 1250,
    rating: 4.8,
    tags: ['硕士', '浙大', '理工科'],
    sections: [
      { id: 's1', title: '摘要', orderIndex: 0, required: true },
      { id: 's2', title: 'Abstract', orderIndex: 1, required: true },
      { id: 's3', title: '目录', orderIndex: 2, required: true },
      { id: 's4', title: '第一章 绪论', orderIndex: 3, required: true },
      { id: 's5', title: '第二章 文献综述', orderIndex: 4, required: true },
      { id: 's6', title: '第三章 研究方法', orderIndex: 5, required: true },
      { id: 's7', title: '第四章 研究结果', orderIndex: 6, required: true },
      { id: 's8', title: '第五章 结论与展望', orderIndex: 7, required: true },
      { id: 's9', title: '参考文献', orderIndex: 8, required: true },
      { id: 's10', title: '附录', orderIndex: 9, required: false },
      { id: 's11', title: '致谢', orderIndex: 10, required: false },
    ],
    format: {
      fontFamily: 'SimSun',
      fontSize: 12,
      lineHeight: 1.5,
      margins: { top: 2.5, bottom: 2.5, left: 3, right: 2.5 },
      headingStyles: {
        h1: { fontSize: 16, bold: true },
        h2: { fontSize: 14, bold: true },
        h3: { fontSize: 12, bold: true },
      },
    },
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-02-15T00:00:00Z',
  },
  {
    id: 't2',
    name: 'GB/T 7714-2015 参考文献格式',
    description: '国家标准 GB/T 7714-2015 参考文献著录规则模板',
    type: 'thesis',
    author: 'ScholarForge',
    downloadCount: 3200,
    rating: 4.9,
    tags: ['国标', '参考文献', '通用'],
    sections: [],
    format: {
      fontFamily: 'SimSun',
      fontSize: 10.5,
      lineHeight: 1.25,
      margins: { top: 2.5, bottom: 2.5, left: 2.5, right: 2.5 },
      headingStyles: {},
    },
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-02-01T00:00:00Z',
  },
  {
    id: 't3',
    name: 'IEEE 会议论文模板',
    description: 'IEEE 会议论文标准格式模板',
    type: 'conference',
    institution: 'IEEE',
    author: 'ScholarForge',
    downloadCount: 890,
    rating: 4.7,
    tags: ['IEEE', '会议', '英文'],
    sections: [
      { id: 's1', title: 'Abstract', orderIndex: 0, required: true },
      { id: 's2', title: 'Introduction', orderIndex: 1, required: true },
      { id: 's3', title: 'Related Work', orderIndex: 2, required: true },
      { id: 's4', title: 'Methodology', orderIndex: 3, required: true },
      { id: 's5', title: 'Experiments', orderIndex: 4, required: true },
      { id: 's6', title: 'Conclusion', orderIndex: 5, required: true },
      { id: 's7', title: 'References', orderIndex: 6, required: true },
    ],
    format: {
      fontFamily: 'Times New Roman',
      fontSize: 10,
      lineHeight: 1.2,
      margins: { top: 1.9, bottom: 2.5, left: 1.78, right: 1.78 },
      headingStyles: {
        h1: { fontSize: 10, bold: true },
        h2: { fontSize: 10, bold: true },
      },
    },
    createdAt: '2026-01-15T00:00:00Z',
    updatedAt: '2026-02-10T00:00:00Z',
  },
  {
    id: 't4',
    name: 'ACM 期刊论文模板',
    description: 'ACM 期刊论文标准格式模板',
    type: 'journal',
    institution: 'ACM',
    author: 'ScholarForge',
    downloadCount: 560,
    rating: 4.6,
    tags: ['ACM', '期刊', '英文'],
    sections: [],
    format: {
      fontFamily: 'Times New Roman',
      fontSize: 9,
      lineHeight: 1.0,
      margins: { top: 2.0, bottom: 2.0, left: 1.9, right: 1.9 },
      headingStyles: {},
    },
    createdAt: '2026-01-20T00:00:00Z',
    updatedAt: '2026-02-05T00:00:00Z',
  },
]

export const templateService = {
  /**
   * 获取模板列表
   */
  getTemplates: async (params?: {
    type?: string
    institution?: string
    keyword?: string
  }): Promise<{ data: PaperTemplate[] }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      let filtered = [...mockTemplates]
      if (params?.type) {
        filtered = filtered.filter(t => t.type === params.type)
      }
      if (params?.institution) {
        filtered = filtered.filter(t => t.institution === params.institution)
      }
      if (params?.keyword) {
        const keyword = params.keyword.toLowerCase()
        filtered = filtered.filter(t =>
          t.name.toLowerCase().includes(keyword) ||
          t.description.toLowerCase().includes(keyword) ||
          t.tags.some(tag => tag.toLowerCase().includes(keyword))
        )
      }
      return { data: filtered }
    }
    return request.get('/templates', params)
  },

  /**
   * 获取模板详情
   */
  getTemplate: async (templateId: string): Promise<{ data: PaperTemplate }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const template = mockTemplates.find(t => t.id === templateId)
      if (!template) throw { code: 404, message: '模板不存在' }
      return { data: template }
    }
    return request.get(`/templates/${templateId}`)
  },

  /**
   * 使用模板创建论文
   */
  createPaperFromTemplate: async (
    templateId: string,
    data: { title: string }
  ): Promise<{ data: { paperId: string } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500))
      return {
        data: {
          paperId: Date.now().toString(36),
        }
      }
    }
    return request.post(`/templates/${templateId}/create-paper`, data)
  },

  /**
   * 获取推荐的模板
   */
  getRecommendedTemplates: async (): Promise<{ data: PaperTemplate[] }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      return { data: mockTemplates.slice(0, 3) }
    }
    return request.get('/templates/recommended')
  },

  /**
   * 获取筛选选项
   */
  getFilterOptions: async (): Promise<{ data: any }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 100))
      return {
        data: {
          types: [
            { value: 'thesis', label: '学位论文' },
            { value: 'journal', label: '期刊论文' },
            { value: 'conference', label: '会议论文' },
            { value: 'report', label: '研究报告' },
            { value: 'proposal', label: '开题报告' },
            { value: 'review', label: '综述文章' },
          ],
          institutions: ['浙江大学', 'IEEE', 'ACM', 'Nature', 'Science'],
          disciplines: ['计算机科学', '工程学', '医学', '物理学', '经济学'],
          languages: ['zh', 'en'],
          difficulties: ['beginner', 'intermediate', 'advanced'],
          tags: ['硕士', '博士', '本科', '英文', '中文', '理工科', '社科'],
        }
      }
    }
    return request.get('/templates/filters')
  },

  /**
   * 获取收藏列表
   */
  getFavorites: async (): Promise<{ data: PaperTemplate[] }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 100))
      return { data: mockTemplates.slice(0, 2) }
    }
    return request.get('/templates/favorites/my')
  },

  /**
   * 添加收藏
   */
  addFavorite: async (templateId: string): Promise<void> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 100))
      return
    }
    await request.post(`/templates/${templateId}/favorite`)
  },

  /**
   * 取消收藏
   */
  removeFavorite: async (templateId: string): Promise<void> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 100))
      return
    }
    await request.delete(`/templates/${templateId}/favorite`)
  },

  /**
   * 使用模板
   */
  useTemplate: async (templateId: string, data: { title: string }): Promise<any> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      return { success: true }
    }
    return request.post(`/templates/${templateId}/use`, data)
  },

  /**
   * AI填充模板
   */
  fillTemplateWithAI: async (templateId: string, data: any): Promise<any> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 2000))
      return {
        data: {
          filled_sections: [
            {
              section_id: 's1',
              section_title: '摘要',
              content: '【AI生成的摘要内容示例】',
              word_count: 800,
              confidence: 0.85,
              suggestions: ['建议补充更多研究细节'],
              references: ['Smith, 2023'],
            }
          ],
          total_word_count: 800,
          estimated_quality: 0.82,
        }
      }
    }
    return request.post(`/templates/${templateId}/fill`, data)
  },
}
