/**
 * AI 服务 API
 * 支持真实后端 API 对接和流式响应 (SSE)
 */

import { request } from './api'
import type { WritingRequest, WritingResponse } from '@/types'

// AI 服务基础路径
const AI_BASE_PATH = '/ai'

// 流式响应回调类型
export type StreamCallback = (chunk: string) => void
export type StreamCompleteCallback = (fullText: string) => void
export type StreamErrorCallback = (error: Error) => void

// 引用建议请求
export interface ReferenceSuggestionRequest {
  text: string
  paperId?: string
  maxResults?: number
}

// 引用建议响应
export interface ReferenceSuggestion {
  id: string
  title: string
  authors: string[]
  year: number
  source: string
  doi?: string
  relevance: number
  reason: string
}

// 智能摘要请求
export interface SummaryRequest {
  paperId: string
  maxLength?: number
  includeKeywords?: boolean
}

// 智能摘要响应
export interface SummaryResponse {
  summary: string
  keywords: string[]
  mainPoints: string[]
  wordCount: number
}

// 图表生成请求
export interface ChartGenerationRequest {
  description: string
  dataHint?: string
  chartType?: 'bar' | 'line' | 'pie' | 'scatter' | 'area'
}

// 图表生成响应
export interface ChartGenerationResponse {
  chartConfig: Record<string, unknown>
  suggestedTitle: string
  dataInterpretation: string
}

// 是否使用模拟模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// 模拟响应（仅在开发/测试时使用）
const mockResponses = {
  continue: () => `基于上述内容，本研究将进一步探讨以下方面：

首先，在理论框架层面，需要深入分析核心机制，包括任务分配、进度跟踪等关键环节。

其次，在方法设计上，本研究将采用混合研究方法，结合定量分析与案例研究。

最后，在实践应用层面，将探讨如何将研究成果转化为可操作的管理建议。`,

  polish: (text: string) => {
    // 模拟润色：改进用词和句式
    return text
      .replace(/很/g, '极为')
      .replace(/非常/g, '极为')
      .replace(/好的/g, '良好的')
      .replace(/很多/g, '众多')
      .replace(/然后/g, '随后')
  },

  rewrite: (text: string) => {
    // 模拟重写：调整表达方式
    return text
      .replace(/研究/g, '探讨')
      .replace(/分析/g, '剖析')
      .replace(/方法/g, '途径')
      .replace(/结果/g, '发现')
  },

  translate: (text: string, targetLang: string) => {
    if (targetLang === 'en') {
      return `[English Translation]\n${text.split('').map(c => /[^\x00-\x7F]/.test(c) ? c : c).join('')}\n\nNote: This is a simulated translation.`
    }
    return `[Translated to ${targetLang}] ${text}`
  },
}

/**
 * 创建 SSE 连接进行流式请求
 */
function createStreamingRequest(
  url: string,
  data: unknown,
  onChunk: StreamCallback,
  onComplete: StreamCompleteCallback,
  onError: StreamErrorCallback
): () => void {
  const controller = new AbortController()

  // 获取认证 token
  const authStr = localStorage.getItem('scholarforge-auth')
  const token = authStr ? JSON.parse(authStr).accessToken : ''

  fetch(`/api/v1${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify(data),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              onComplete(fullText)
              return
            }
            try {
              const parsed = JSON.parse(data)
              if (parsed.text) {
                fullText += parsed.text
                onChunk(parsed.text)
              }
            } catch {
              // 非 JSON 数据，直接作为文本处理
              fullText += data
              onChunk(data)
            }
          }
        }
      }

      onComplete(fullText)
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        onError(error)
      }
    })

  return () => controller.abort()
}

export const aiService = {
  /**
   * 写作助手（非流式）
   */
  writing: async (data: WritingRequest): Promise<{ data: WritingResponse }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 800))

      let generatedText = ''
      switch (data.taskType) {
        case 'continue':
          generatedText = mockResponses.continue()
          break
        case 'polish':
          generatedText = mockResponses.polish(data.text || '')
          break
        case 'rewrite':
          generatedText = mockResponses.rewrite(data.text || '')
          break
        case 'translate':
          generatedText = mockResponses.translate(data.text || '', data.targetLanguage || 'en')
          break
        default:
          generatedText = mockResponses.continue()
      }

      return {
        data: {
          generatedText,
          taskType: data.taskType,
          provider: 'mock',
          tokensUsed: Math.floor(generatedText.length * 1.5),
        }
      }
    }

    return request.post(`${AI_BASE_PATH}/writing`, data)
  },

  /**
   * 写作助手（流式响应）
   */
  writingStream: (
    data: WritingRequest,
    onChunk: StreamCallback,
    onComplete: StreamCompleteCallback,
    onError: StreamErrorCallback
  ): (() => void) => {
    if (USE_MOCK) {
      // 模拟流式响应
      let fullText = ''
      const mockText = data.taskType === 'continue'
        ? mockResponses.continue()
        : data.taskType === 'polish'
          ? mockResponses.polish(data.text || '')
          : data.taskType === 'rewrite'
            ? mockResponses.rewrite(data.text || '')
            : mockResponses.translate(data.text || '', data.targetLanguage || 'en')

      const words = mockText.split('')
      let index = 0

      const interval = setInterval(() => {
        if (index < words.length) {
          const chunk = words[index]
          fullText += chunk
          onChunk(chunk)
          index++
        } else {
          clearInterval(interval)
          onComplete(fullText)
        }
      }, 20)

      return () => clearInterval(interval)
    }

    return createStreamingRequest(
      `${AI_BASE_PATH}/writing/stream`,
      data,
      onChunk,
      onComplete,
      onError
    )
  },

  /**
   * 问答助手
   */
  qa: async (question: string): Promise<{ data: { answer: string; confidence: number } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 700))
      return {
        data: {
          answer: `关于"${question}"，根据学术研究的一般原则，建议您查阅相关领域的高质量文献获取更具体的指导。`,
          confidence: 0.82,
        }
      }
    }

    return request.post(`${AI_BASE_PATH}/qa`, { question })
  },

  /**
   * 生成大纲
   */
  generateOutline: async (topic: string): Promise<{ data: { topic: string; outline: string[] } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500))
      return {
        data: {
          topic,
          outline: ['摘要', '第一章 绪论', '第二章 文献综述', '第三章 研究方法', '第四章 研究结果', '第五章 结论与展望', '参考文献'],
        }
      }
    }

    return request.post(`${AI_BASE_PATH}/outline`, { topic })
  },

  /**
   * 引用建议
   */
  suggestReferences: async (
    data: ReferenceSuggestionRequest
  ): Promise<{ data: { suggestions: ReferenceSuggestion[] } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 600))
      return {
        data: {
          suggestions: [
            {
              id: '1',
              title: '人工智能在学术写作中的应用研究',
              authors: ['张三', '李四'],
              year: 2024,
              source: '计算机学报',
              doi: '10.1000/xxx001',
              relevance: 0.95,
              reason: '与您的研究主题高度相关，探讨了 AI 技术在学术写作场景的具体应用',
            },
            {
              id: '2',
              title: '基于大语言模型的文本生成技术研究进展',
              authors: ['王五', '赵六'],
              year: 2023,
              source: '软件学报',
              doi: '10.1000/xxx002',
              relevance: 0.88,
              reason: '提供了 LLM 技术的全面综述，适合作为技术背景引用',
            },
            {
              id: '3',
              title: '协作编辑系统的设计与实现',
              authors: ['钱七'],
              year: 2024,
              source: 'IEEE Transactions on Software Engineering',
              relevance: 0.82,
              reason: '讨论了实时协作的技术实现，与您的系统设计相关',
            },
          ],
        }
      }
    }

    return request.post(`${AI_BASE_PATH}/references/suggest`, data)
  },

  /**
   * 智能摘要生成
   */
  generateSummary: async (
    data: SummaryRequest
  ): Promise<{ data: SummaryResponse }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 800))
      return {
        data: {
          summary: '本文研究了人工智能技术在学术论文写作辅助工具中的应用。通过分析现有工具的局限性，提出了一个集成 AI 写作助手、实时协作和质量保障功能的综合平台。实验结果表明，该平台能够显著提升学术写作效率。',
          keywords: ['人工智能', '学术写作', '协作编辑', '文本生成'],
          mainPoints: [
            '提出了 ScholarForge 学术研究协作平台的整体架构',
            '实现了基于 LLM 的智能写作辅助功能',
            '设计了支持多人实时协作的编辑系统',
            '集成了查重检测和格式检查等质量保障功能',
          ],
          wordCount: 150,
        }
      }
    }

    return request.post(`${AI_BASE_PATH}/summary`, data)
  },

  /**
   * 图表生成建议
   */
  suggestChart: async (
    data: ChartGenerationRequest
  ): Promise<{ data: ChartGenerationResponse }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500))
      return {
        data: {
          chartConfig: {
            type: data.chartType || 'bar',
            data: {
              labels: ['样本1', '样本2', '样本3', '样本4', '样本5'],
              datasets: [{
                label: '数据值',
                data: [65, 59, 80, 81, 56],
              }],
            },
            options: {
              responsive: true,
              plugins: {
                title: {
                  display: true,
                  text: data.description.slice(0, 30),
                },
              },
            },
          },
          suggestedTitle: `关于"${data.description.slice(0, 20)}..."的图表`,
          dataInterpretation: '根据您的描述，建议使用柱状图来展示数据对比关系。',
        }
      }
    }

    return request.post(`${AI_BASE_PATH}/chart/suggest`, data)
  },

  /**
   * 逻辑检查
   */
  checkLogic: async (data: {
    text: string
    language?: string
  }): Promise<{ data: { score: number; issues: Array<{ type: string; message: string; suggestion?: string }>; analysis: string } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 1000))

      // 模拟逻辑检查结果
      const issues = []

      // 简单的规则检查
      if (data.text.includes('应该') && !data.text.includes('因为')) {
        issues.push({
          type: 'warning',
          message: '提出建议时缺少原因说明，可能影响论证的说服力',
          suggestion: '建议在提出建议前先说明原因，例如："由于...，因此应该..."',
        })
      }

      if (data.text.length > 500 && !data.text.includes('首先') && !data.text.includes('第一')) {
        issues.push({
          type: 'suggestion',
          message: '长文本建议使用序号或过渡词来组织结构',
          suggestion: '可以考虑使用"首先...其次...最后..."等过渡词来组织内容',
        })
      }

      if (data.text.includes('非常非常') || data.text.includes('很很')) {
        issues.push({
          type: 'error',
          message: '存在重复修饰词，影响表达的规范性',
          suggestion: '建议使用更精准的形容词替代重复修饰',
        })
      }

      const score = Math.max(0.5, 1 - issues.length * 0.15)

      return {
        data: {
          score,
          issues,
          analysis: issues.length === 0
            ? '文本逻辑清晰，论证连贯，符合学术写作规范。'
            : `共发现 ${issues.length} 个潜在问题，建议进行相应修改以提升文本质量。`,
        }
      }
    }

    return request.post(`${AI_BASE_PATH}/logic/check`, data)
  },
}
