/**
 * 智能文献推荐与Word自动排版服务
 * 结合用户写作内容实时推荐文献，并支持一键引用到Word
 */

import type { Article } from '@/types'

export interface WritingContext {
  paperId: string
  currentSection: string
  recentText: string
  keywords: string[]
  citedReferences: string[]
  topic?: string
}

export interface SmartRecommendation {
  id: string
  article: Article
  relevanceScore: number
  recommendationReason: string
  citationStyle: 'apa' | 'mla' | 'chicago' | 'gb7714'
  formattedCitation: string
  formattedBibliography: string
  inTextCitation: string
  suggestedLocation?: 'introduction' | 'literature' | 'methodology' | 'discussion' | 'conclusion'
  quoteSuggestion?: string
}

export interface CitationFormat {
  style: 'apa' | 'mla' | 'chicago' | 'gb7714'
  inTextTemplate: string
  bibliographyTemplate: string
}

export interface FormatTemplate {
  id: string
  name: string
  description: string
  citationStyle: CitationFormat['style']
  fontSettings: {
    mainFont: string
    englishFont: string
    fontSize: number
    lineSpacing: number
    paragraphSpacing: number
  }
  pageSettings: {
    paperSize: 'A4' | 'Letter'
    margins: {
      top: number
      bottom: number
      left: number
      right: number
    }
  }
  headingStyles: {
    level: number
    fontSize: number
    bold: boolean
    alignment: 'left' | 'center' | 'right'
  }[]
}

// 引用格式模板
const CITATION_TEMPLATES: Record<string, CitationFormat> = {
  apa: {
    style: 'apa',
    inTextTemplate: '({author}, {year})',
    bibliographyTemplate: '{author}. ({year}). {title}. {source}.'
  },
  mla: {
    style: 'mla',
    inTextTemplate: '({author} {page})',
    bibliographyTemplate: '{author}. "{title}." {source}, {year}.'
  },
  chicago: {
    style: 'chicago',
    inTextTemplate: '{author}, {title}, {year}',
    bibliographyTemplate: '{author}. {title}. {source}, {year}.'
  },
  gb7714: {
    style: 'gb7714',
    inTextTemplate: '[{number}]',
    bibliographyTemplate: '[{number}] {author}. {title}[J]. {source}, {year}.'
  }
}

// 预定义格式模板
export const FORMAT_TEMPLATES: FormatTemplate[] = [
  {
    id: 'thesis_standard',
    name: '标准学位论文',
    description: '适用于硕士/博士学位论文，GB7714引用格式',
    citationStyle: 'gb7714',
    fontSettings: {
      mainFont: 'SimSun',
      englishFont: 'Times New Roman',
      fontSize: 12,
      lineSpacing: 1.5,
      paragraphSpacing: 6
    },
    pageSettings: {
      paperSize: 'A4',
      margins: { top: 25.4, bottom: 25.4, left: 31.7, right: 31.7 }
    },
    headingStyles: [
      { level: 1, fontSize: 16, bold: true, alignment: 'center' },
      { level: 2, fontSize: 14, bold: true, alignment: 'left' },
      { level: 3, fontSize: 12, bold: true, alignment: 'left' }
    ]
  },
  {
    id: 'journal_submission',
    name: '期刊投稿格式',
    description: '适用于期刊论文投稿，APA引用格式',
    citationStyle: 'apa',
    fontSettings: {
      mainFont: 'Times New Roman',
      englishFont: 'Times New Roman',
      fontSize: 11,
      lineSpacing: 2,
      paragraphSpacing: 0
    },
    pageSettings: {
      paperSize: 'A4',
      margins: { top: 25.4, bottom: 25.4, left: 25.4, right: 25.4 }
    },
    headingStyles: [
      { level: 1, fontSize: 14, bold: true, alignment: 'left' },
      { level: 2, fontSize: 12, bold: true, alignment: 'left' },
      { level: 3, fontSize: 11, bold: true, alignment: 'left' }
    ]
  },
  {
    id: 'conference_paper',
    name: '会议论文格式',
    description: '适用于学术会议论文，IEEE引用格式',
    citationStyle: 'gb7714',
    fontSettings: {
      mainFont: 'Times New Roman',
      englishFont: 'Times New Roman',
      fontSize: 10,
      lineSpacing: 1,
      paragraphSpacing: 3
    },
    pageSettings: {
      paperSize: 'Letter',
      margins: { top: 19, bottom: 19, left: 19, right: 19 }
    },
    headingStyles: [
      { level: 1, fontSize: 12, bold: true, alignment: 'center' },
      { level: 2, fontSize: 10, bold: true, alignment: 'left' }
    ]
  }
]

class LiteratureRecommendationService {
  private currentContext: WritingContext | null = null
  private citationCounter: number = 0
  private usedReferences: Set<string> = new Set()

  // 分析写作上下文
  analyzeContext(paperId: string, recentText: string, currentSection: string): WritingContext {
    // 提取关键词
    const keywords = this.extractKeywords(recentText)

    // 提取已引用文献
    const citedReferences = this.extractCitations(recentText)

    this.currentContext = {
      paperId,
      currentSection,
      recentText,
      keywords,
      citedReferences,
      topic: this.inferTopic(keywords)
    }

    return this.currentContext
  }

  // 提取关键词
  private extractKeywords(text: string): string[] {
    // 简单的关键词提取逻辑
    const commonWords = new Set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])

    const words = text.split(/\s+|[，。！？、；：""''（）【】《》]/)
    const wordFreq: Record<string, number> = {}

    words.forEach(word => {
      if (word.length >= 2 && !commonWords.has(word)) {
        wordFreq[word] = (wordFreq[word] || 0) + 1
      }
    })

    return Object.entries(wordFreq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([word]) => word)
  }

  // 提取已引用文献
  private extractCitations(text: string): string[] {
    const citations: string[] = []

    // 匹配 [1], [2,3], [1-3] 等格式
    const bracketPattern = /\[(\d+(?:[-,]\d+)*)\]/g
    let match
    while ((match = bracketPattern.exec(text)) !== null) {
      citations.push(match[1])
    }

    // 匹配 (Author, Year) 格式
    const authorYearPattern = /\(([A-Za-z\s]+),?\s*(\d{4})\)/g
    while ((match = authorYearPattern.exec(text)) !== null) {
      citations.push(`${match[1]}_${match[2]}`)
    }

    return citations
  }

  // 推断主题
  private inferTopic(keywords: string[]): string {
    // 基于关键词推断研究主题
    const topicKeywords: Record<string, string[]> = {
      '人工智能': ['AI', '机器学习', '深度学习', '神经网络', '智能'],
      '项目管理': ['项目', '管理', '进度', '风险', '资源'],
      '数据分析': ['数据', '分析', '统计', '挖掘', '大数据'],
      '教育技术': ['教育', '学习', '教学', '在线', '课程']
    }

    for (const [topic, topicKeys] of Object.entries(topicKeywords)) {
      if (keywords.some(k => topicKeys.includes(k))) {
        return topic
      }
    }

    return '综合研究'
  }

  // 获取智能推荐
  async getSmartRecommendations(
    context: WritingContext,
    style: CitationFormat['style'] = 'gb7714',
    limit: number = 5
  ): Promise<SmartRecommendation[]> {
    // 模拟API调用获取推荐
    await new Promise(resolve => setTimeout(resolve, 500))

    // 基于上下文生成推荐
    const mockArticles: Article[] = [
      {
        id: 'rec_1',
        title: `${context.topic || '相关'}领域的最新研究进展`,
        abstract: `本文探讨了${context.keywords[0] || '该领域'}的最新发展...`,
        authors: ['张三', '李四'],
        source: '计算机学报',
        publicationYear: 2024,
        keywords: context.keywords,
        citationCount: 45
      },
      {
        id: 'rec_2',
        title: `基于${context.keywords[1] || '新方法'}的优化算法研究`,
        abstract: '提出了一种创新的方法，显著提升了性能...',
        authors: ['Wang, J.', 'Smith, A.'],
        source: 'IEEE Transactions',
        publicationYear: 2023,
        keywords: ['algorithm', 'optimization'],
        citationCount: 78
      },
      {
        id: 'rec_3',
        title: `${context.currentSection || '研究'}方法论综述`,
        abstract: '系统梳理了该领域的研究方法...',
        authors: ['刘五', '赵六', '孙七'],
        source: '管理世界',
        publicationYear: 2023,
        keywords: ['methodology', 'review'],
        citationCount: 120
      }
    ]

    return mockArticles.map((article, index) => {
      this.citationCounter++
      return this.formatRecommendation(article, style, this.citationCounter, context)
    })
  }

  // 格式化推荐
  private formatRecommendation(
    article: Article,
    style: CitationFormat['style'],
    number: number,
    context: WritingContext
  ): SmartRecommendation {
    const format = CITATION_TEMPLATES[style]

    // 生成格式化引用
    const formattedCitation = this.formatCitation(article, format, number)
    const formattedBibliography = this.formatBibliography(article, format, number)
    const inTextCitation = this.formatInTextCitation(article, format, number)

    // 确定推荐位置
    const suggestedLocation = this.suggestLocation(context.currentSection)

    // 生成引用建议
    const quoteSuggestion = this.generateQuoteSuggestion(article, context)

    return {
      id: `rec_${article.id}`,
      article,
      relevanceScore: Math.round(85 + Math.random() * 15),
      recommendationReason: this.generateReason(article, context),
      citationStyle: style,
      formattedCitation,
      formattedBibliography,
      inTextCitation,
      suggestedLocation,
      quoteSuggestion
    }
  }

  // 格式化引用
  private formatCitation(article: Article, format: CitationFormat, number: number): string {
    const authorNames = article.authors?.map(a => a.name) || []
    const authorStr = this.formatAuthors(authorNames, format.style)
    return format.bibliographyTemplate
      .replace('{number}', number.toString())
      .replace('{author}', authorStr)
      .replace('{title}', article.title)
      .replace('{source}', article.sourceName || '')
      .replace('{year}', (article.publicationYear || 2024).toString())
  }

  // 格式化参考文献
  private formatBibliography(article: Article, format: CitationFormat, number: number): string {
    return this.formatCitation(article, format, number)
  }

  // 格式化文内引用
  private formatInTextCitation(article: Article, format: CitationFormat, number: number): string {
    const authorNames = article.authors?.map(a => a.name) || []
    const authorStr = this.formatAuthors(authorNames, format.style, true)
    return format.inTextTemplate
      .replace('{number}', number.toString())
      .replace('{author}', authorStr)
      .replace('{year}', (article.publicationYear || 2024).toString())
  }

  // 格式化作者
  private formatAuthors(authors: string[], style: string, firstOnly: boolean = false): string {
    if (!authors || authors.length === 0) return 'Unknown'

    if (style === 'gb7714') {
      // 国标格式：姓在前
      return authors.slice(0, 3).join(', ') + (authors.length > 3 ? ' 等' : '')
    }

    const mainAuthor = authors[0]
    if (firstOnly || authors.length === 1) return mainAuthor

    if (style === 'apa') {
      return authors.length > 2
        ? `${mainAuthor} et al.`
        : authors.join(' & ')
    }

    return authors.join(', ')
  }

  // 推荐引用位置
  private suggestLocation(currentSection: string): SmartRecommendation['suggestedLocation'] {
    const sectionMap: Record<string, SmartRecommendation['suggestedLocation']> = {
      'introduction': 'introduction',
      'literature': 'literature',
      'methodology': 'methodology',
      'discussion': 'discussion',
      'conclusion': 'conclusion'
    }
    return sectionMap[currentSection] || 'literature'
  }

  // 生成引用建议
  private generateQuoteSuggestion(article: Article, context: WritingContext): string {
    const firstAuthor = article.authors?.[0]?.name || 'Unknown'
    return `${article.title}（${firstAuthor}等，${article.publicationYear || 2024}）指出，${article.abstract?.slice(0, 50)}...`
  }

  // 生成推荐理由
  private generateReason(article: Article, context: WritingContext): string {
    const reasons = [
      `与您正在撰写的${context.currentSection || '内容'}高度相关`,
      `补充了${context.topic || '该领域'}的重要观点`,
      '高被引文献，具有较高参考价值',
      '最新发表的前沿研究'
    ]
    return reasons[Math.floor(Math.random() * reasons.length)]
  }

  // 生成Word格式指令
  generateWordFormattingInstructions(template: FormatTemplate): string {
    return `
格式设置指令：
================
字体设置：
- 中文字体：${template.fontSettings.mainFont}
- 英文字体：${template.fontSettings.englishFont}
- 字号：${template.fontSettings.fontSize}pt
- 行距：${template.fontSettings.lineSpacing}倍
- 段间距：${template.fontSettings.paragraphSpacing}pt

页面设置：
- 纸张：${template.pageSettings.paperSize}
- 页边距：上${template.pageSettings.margins.top}mm，下${template.pageSettings.margins.bottom}mm，左${template.pageSettings.margins.left}mm，右${template.pageSettings.margins.right}mm

标题样式：
${template.headingStyles.map(h => `- ${h.level}级标题：${h.fontSize}pt ${h.bold ? '加粗' : ''} ${h.alignment === 'center' ? '居中' : '左对齐'}`).join('\n')}

引用格式：${template.citationStyle.toUpperCase()}
================
    `.trim()
  }

  // 导出参考文献列表
  exportBibliography(recommendations: SmartRecommendation[]): string {
    return recommendations
      .map(rec => rec.formattedBibliography)
      .join('\n')
  }

  // 一键插入Word
  async insertToWord(recommendation: SmartRecommendation): Promise<boolean> {
    // 模拟Word集成
    console.log('插入Word:', {
      inTextCitation: recommendation.inTextCitation,
      bibliography: recommendation.formattedBibliography
    })

    // 记录已使用
    this.usedReferences.add(recommendation.id)

    return true
  }

  // 获取已使用引用
  getUsedReferences(): string[] {
    return Array.from(this.usedReferences)
  }

  // 重置服务
  reset(): void {
    this.citationCounter = 0
    this.usedReferences.clear()
    this.currentContext = null
  }
}

export const literatureRecommendationService = new LiteratureRecommendationService()
export default literatureRecommendationService
