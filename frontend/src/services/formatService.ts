/**
 * 格式检查服务 API
 */

import { request } from './api'
import type {
  FormatCheckResult,
  FormatCheckRequest,
  FormatTemplate,
} from '@/types/format'

// 是否使用模拟模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

// 模拟格式检查结果
const mockFormatResult: FormatCheckResult = {
  id: 'format-1',
  paperId: '1',
  status: 'completed',
  checkedAt: new Date().toISOString(),
  score: 85,
  issues: [
    {
      id: 'i1',
      ruleId: 'r1',
      ruleName: '标题格式',
      severity: 'warning',
      message: '标题 2 应使用 1.1 格式而非 1.1.1',
      sectionId: 's2',
      position: { from: 10, to: 50 },
      suggestion: '将标题修改为 1.1 研究背景',
    },
    {
      id: 'i2',
      ruleId: 'r2',
      ruleName: '字体大小',
      severity: 'error',
      message: '正文字体大小应为小四号（12pt）',
      sectionId: 's2',
      suggestion: '请在模板设置中调整正文字体大小',
    },
    {
      id: 'i3',
      ruleId: 'r3',
      ruleName: '行间距',
      severity: 'warning',
      message: '行间距应为 1.5 倍',
      suggestion: '建议调整行间距为 1.5',
    },
    {
      id: 'i4',
      ruleId: 'r4',
      ruleName: '参考文献格式',
      severity: 'info',
      message: '参考文献格式基本正确，但有 2 处格式不规范',
      suggestion: '请检查参考文献 [3] 和 [5] 的格式',
    },
    {
      id: 'i5',
      ruleId: 'r5',
      ruleName: '图表编号',
      severity: 'warning',
      message: '图 3 缺少标题',
      sectionId: 's4',
      suggestion: '请为图 3 添加标题',
    },
  ],
  summary: {
    errorCount: 1,
    warningCount: 3,
    infoCount: 1,
  },
  passedRules: ['r6', 'r7', 'r8', 'r9', 'r10'],
  failedRules: ['r1', 'r2', 'r3', 'r4', 'r5'],
}

// 模拟模板数据
const mockTemplates: FormatTemplate[] = [
  {
    id: 'cn_thesis',
    name: '中文论文标准格式',
    description: '符合大多数国内高校要求的学位论文格式',
    type: 'thesis',
    institution: '通用',
    rules: [],
    config: {
      fontFamily: 'SimSun',
      fontSize: 12,
      lineSpacing: 1.5,
      marginTop: 25.4,
      marginBottom: 25.4,
      marginLeft: 31.7,
      marginRight: 31.7,
      paragraphIndent: 24,
    },
    isDefault: true,
  },
  {
    id: 'cn_journal',
    name: '中文期刊论文格式',
    description: '常见中文学术期刊格式',
    type: 'journal',
    institution: '通用',
    rules: [],
    config: {
      fontFamily: 'SimSun',
      fontSize: 10.5,
      lineSpacing: 1.0,
      marginTop: 25.4,
      marginBottom: 25.4,
      marginLeft: 25.4,
      marginRight: 25.4,
      paragraphIndent: 24,
    },
  },
  {
    id: 'ieee',
    name: 'IEEE 会议/期刊格式',
    description: 'IEEE 标准论文格式',
    type: 'conference',
    institution: 'IEEE',
    rules: [],
    config: {
      fontFamily: 'Times New Roman',
      fontSize: 10,
      lineSpacing: 1.0,
      marginTop: 19.0,
      marginBottom: 19.0,
      marginLeft: 19.0,
      marginRight: 19.0,
      paragraphIndent: 0,
    },
  },
]

export const formatService = {
  /**
   * 发起格式检查
   */
  startCheck: async (
    data: FormatCheckRequest
  ): Promise<{ data: { checkId: string; status: string } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500))
      return {
        data: {
          checkId: generateId(),
          status: 'checking',
        }
      }
    }
    return request.post(`/papers/${data.paperId}/format/check`, data)
  },

  /**
   * 获取格式检查结果
   */
  getCheckResult: async (
    paperId: string,
    checkId?: string
  ): Promise<{ data: FormatCheckResult }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      return {
        data: {
          ...mockFormatResult,
          paperId,
          id: checkId || mockFormatResult.id,
        }
      }
    }
    const url = checkId
      ? `/papers/${paperId}/format/checks/${checkId}`
      : `/papers/${paperId}/format/checks/latest`
    return request.get(url)
  },

  /**
   * 获取格式模板列表
   */
  getTemplates: async (): Promise<{ data: FormatTemplate[] }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      return { data: mockTemplates }
    }
    return request.get('/format/templates')
  },

  /**
   * 获取模板详情
   */
  getTemplate: async (
    templateId: string
  ): Promise<{ data: FormatTemplate }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      const template = mockTemplates.find(t => t.id === templateId)
      if (!template) throw { code: 404, message: '模板不存在' }
      return { data: template }
    }
    return request.get(`/format/templates/${templateId}`)
  },

  /**
   * 检查格式（新方法）
   */
  checkFormat: async (
    paperId: string,
    templateId: string
  ): Promise<{ data: FormatCheckResult }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 800))
      return {
        data: {
          ...mockFormatResult,
          paperId,
          templateName: mockTemplates.find(t => t.id === templateId)?.name || '默认模板',
        }
      }
    }
    return request.post(`/format/check`, { paperId, templateId })
  },

  /**
   * 自动排版
   */
  autoFormat: async (
    paperId: string,
    templateId: string
  ): Promise<{ data: { success: boolean; taskId: string } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 2000))
      return {
        data: {
          success: true,
          taskId: generateId(),
        }
      }
    }
    return request.post(`/format/auto-format`, { paperId, templateId })
  },
}
