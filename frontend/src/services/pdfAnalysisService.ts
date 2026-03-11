/**
 * PDF文献分析服务
 * 提供翻译、总结、关联性分析等功能
 */

import { aiService } from './aiService'
import type { Article } from '@/types'

// 是否使用模拟模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// 分析结果接口
export interface PDFAnalysisResult {
  summary: string
  keyPoints: string[]
  keywords: string[]
  methodology: string
  conclusions: string
  relevance: RelevanceAnalysis
  translatable: boolean
}

// 关联性分析
export interface RelevanceAnalysis {
  score: number
  topicMatch: string
  methodologyInsight: string
  referenceValue: string
  researchGap: string
}

// 翻译结果
export interface TranslationResult {
  translatedText: string
  detectedLanguage: string
  confidence: number
}

// Mock分析结果
const mockAnalysis: PDFAnalysisResult = {
  summary: `本文提出了一种基于深度学习的自然语言处理方法，通过引入注意力机制显著提升了模型性能。研究在多个基准数据集上进行了验证，取得了 state-of-the-art 的结果。`,
  keyPoints: [
    '提出了新的注意力机制架构',
    '在GLUE基准上取得SOTA性能',
    '模型参数量减少30%，推理速度提升2倍',
    '开源代码和预训练模型'
  ],
  keywords: ['深度学习', '注意力机制', '自然语言处理', 'Transformer'],
  methodology: `研究采用实验对比方法，主要包含：
1. 模型架构设计与改进
2. 大规模数据集预训练
3. 下游任务微调
4. 与现有方法的系统对比实验`,
  conclusions: '研究表明，所提出的方法在准确率和效率之间取得了良好平衡，为实际应用提供了可行方案。',
  relevance: {
    score: 0.85,
    topicMatch: '与您当前研究的"AI在学术写作中的应用"高度相关，提供了最新的技术方法论参考',
    methodologyInsight: '论文中的实验设计方法值得借鉴，特别是对比实验的设置',
    referenceValue: '可作为技术背景章节的重要引用，支撑您的技术选型论证',
    researchGap: '该研究主要关注英语场景，您可以探索其在中文学术写作中的适配和优化'
  },
  translatable: true
}

// Mock翻译
const mockTranslation = (text: string): TranslationResult => ({
  translatedText: `[中文翻译] ${text}\n\n[这是一段模拟翻译文本，实际使用时会调用AI翻译API]`,
  detectedLanguage: 'en',
  confidence: 0.95
})

export const pdfAnalysisService = {
  /**
   * 分析PDF文献
   * @param article 文章信息
   * @param userTopic 用户当前研究主题
   * @param content PDF文本内容（如果有）
   */
  async analyzeArticle(
    article: Article,
    userTopic?: string,
    content?: string
  ): Promise<PDFAnalysisResult> {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 1500))
      return {
        ...mockAnalysis,
        relevance: {
          ...mockAnalysis.relevance,
          topicMatch: userTopic
            ? `与您当前研究的"${userTopic}"高度相关，提供了重要的理论基础和方法论参考`
            : mockAnalysis.relevance.topicMatch
        }
      }
    }

    // 构建分析提示
    const prompt = this.buildAnalysisPrompt(article, userTopic, content)

    try {
      // 调用AI服务进行分析
      const response = await aiService.writing({
        taskType: 'continue',
        text: prompt,
        context: content?.slice(0, 2000)
      })

      // 解析AI返回的结构化数据
      return this.parseAnalysisResult(response.data.generatedText)
    } catch (error) {
      console.error('PDF分析失败:', error)
      throw new Error('文献分析失败，请稍后重试')
    }
  },

  /**
   * 翻译PDF内容
   * @param text 要翻译的文本
   * @param targetLang 目标语言
   */
  async translateContent(
    text: string,
    targetLang: 'zh' | 'en' = 'zh'
  ): Promise<TranslationResult> {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 1000))
      return mockTranslation(text)
    }

    try {
      const response = await aiService.writing({
        taskType: 'translate',
        text,
        targetLanguage: targetLang
      })

      return {
        translatedText: response.data.generatedText,
        detectedLanguage: targetLang === 'zh' ? 'en' : 'zh',
        confidence: 0.9
      }
    } catch (error) {
      console.error('翻译失败:', error)
      throw new Error('翻译失败，请稍后重试')
    }
  },

  /**
   * 流式翻译（用于大文本）
   */
  translateStream(
    text: string,
    targetLang: 'zh' | 'en',
    onChunk: (chunk: string) => void,
    onComplete: (fullText: string) => void,
    onError: (error: Error) => void
  ): () => void {
    if (USE_MOCK) {
      const result = mockTranslation(text)
      const chars = result.translatedText.split('')
      let index = 0
      let fullText = ''

      const interval = setInterval(() => {
        if (index < chars.length) {
          const chunk = chars[index]
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

    return aiService.writingStream(
      {
        taskType: 'translate',
        text,
        targetLanguage: targetLang
      },
      onChunk,
      onComplete,
      onError
    )
  },

  /**
   * 生成阅读建议
   */
  generateReadingGuide(analysis: PDFAnalysisResult): string {
    const sections: string[] = []

    sections.push(`📊 **关联度评分**: ${Math.round(analysis.relevance.score * 100)}/100`)
    sections.push('')
    sections.push('📝 **阅读建议**:')
    sections.push('')

    if (analysis.relevance.score >= 0.8) {
      sections.push('✅ **强烈推荐** - 这篇文献与您的研究高度相关，建议精读')
    } else if (analysis.relevance.score >= 0.6) {
      sections.push('📖 **建议阅读** - 有一定参考价值，可速读重点章节')
    } else {
      sections.push('📎 **参考价值有限** - 可作为背景资料快速浏览')
    }

    sections.push('')
    sections.push('🔍 **重点关注**:')
    sections.push(`• ${analysis.relevance.methodologyInsight}`)
    sections.push(`• ${analysis.relevance.referenceValue}`)

    if (analysis.relevance.researchGap) {
      sections.push('')
      sections.push('💡 **研究启发**:')
      sections.push(`• ${analysis.relevance.researchGap}`)
    }

    return sections.join('\n')
  },

  /**
   * 构建分析提示词
   */
  buildAnalysisPrompt(
    article: Article,
    userTopic?: string,
    content?: string
  ): string {
    const hasContent = content && content.length > 100

    return `请对以下学术文献进行专业分析：

【文献信息】
标题: ${article.title}
作者: ${article.authors?.map(a => typeof a === 'string' ? a : a.name).join(', ') || 'Unknown'}
年份: ${article.publicationYear || 'N/A'}
期刊: ${article.sourceName || 'N/A'}
摘要: ${article.abstract || 'N/A'}
${hasContent ? `正文片段: ${content.slice(0, 2000)}...` : ''}

${userTopic ? `【用户研究主题】\n${userTopic}\n` : ''}

请提供以下分析（使用结构化格式）：
1. 一句话总结
2. 核心创新点（3-5点）
3. 研究方法
4. 主要结论
${userTopic ? '5. 与用户研究主题的关联性分析' : ''}`
  },

  /**
   * 解析AI返回的分析结果
   */
  parseAnalysisResult(text: string): PDFAnalysisResult {
    // 简单的解析逻辑，实际项目中可以使用更严格的JSON解析
    const lines = text.split('\n')

    return {
      summary: lines[0] || '暂无总结',
      keyPoints: lines.filter(l => l.trim().startsWith('-') || l.trim().startsWith('•')).map(l => l.replace(/^[\s\-\•]+/, '')),
      keywords: [],
      methodology: '',
      conclusions: '',
      relevance: {
        score: 0.7,
        topicMatch: '解析失败，使用默认评分',
        methodologyInsight: '',
        referenceValue: '',
        researchGap: ''
      },
      translatable: true
    }
  }
}

export default pdfAnalysisService
