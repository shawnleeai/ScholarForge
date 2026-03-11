/**
 * AI智能引用审查与自动排版服务
 * 引用格式检查、自动排版、引用完整性验证
 */

export type CitationStyle = 'apa' | 'mla' | 'chicago' | 'gb7714' | 'ieee'
export type CitationType = 'journal' | 'book' | 'conference' | 'thesis' | 'website' | 'report'

export interface Citation {
  id: string
  type: CitationType
  rawText: string
  formattedText?: string
  authors: string[]
  title: string
  year?: number
  source?: string
  volume?: string
  issue?: string
  pages?: string
  doi?: string
  url?: string
  accessDate?: string
  isValid: boolean
  errors: CitationError[]
}

export interface CitationError {
  type: 'format' | 'missing_field' | 'invalid_date' | 'incomplete' | 'style'
  message: string
  suggestion: string
  severity: 'error' | 'warning' | 'info'
}

export interface CitationReview {
  totalCitations: number
  validCitations: number
  invalidCitations: number
  missingCitations: number
  styleConsistency: number // 0-100
  completeness: number // 0-100
  byType: Record<CitationType, number>
  errors: CitationError[]
  suggestions: string[]
}

export interface FormatRule {
  field: string
  required: boolean
  pattern?: RegExp
  message: string
}

// 引用格式规则
const CITATION_RULES: Record<CitationStyle, FormatRule[]> = {
  gb7714: [
    { field: 'authors', required: true, message: '作者信息缺失' },
    { field: 'title', required: true, message: '标题缺失' },
    { field: 'source', required: true, message: '出版物信息缺失' },
    { field: 'year', required: true, pattern: /^\d{4}$/, message: '年份格式应为4位数字' }
  ],
  apa: [
    { field: 'authors', required: true, message: 'Author information required' },
    { field: 'year', required: true, message: 'Publication year required' },
    { field: 'title', required: true, message: 'Title required' },
    { field: 'source', required: true, message: 'Source required' }
  ],
  mla: [
    { field: 'authors', required: true, message: 'Author required' },
    { field: 'title', required: true, message: 'Title required' },
    { field: 'source', required: true, message: 'Container required' },
    { field: 'year', required: true, message: 'Year required' }
  ],
  chicago: [
    { field: 'authors', required: true, message: 'Author required' },
    { field: 'title', required: true, message: 'Title required' },
    { field: 'source', required: true, message: 'Publication info required' }
  ],
  ieee: [
    { field: 'authors', required: true, message: 'Author required' },
    { field: 'title', required: true, message: 'Title required' },
    { field: 'source', required: true, message: 'Source required' },
    { field: 'year', required: true, message: 'Year required' }
  ]
}

// 格式模板
const FORMAT_TEMPLATES: Record<CitationStyle, Record<CitationType, string>> = {
  gb7714: {
    journal: '[{index}] {authors}. {title}[J]. {source}, {year}, {volume}({issue}): {pages}.',
    book: '[{index}] {authors}. {title}[M]. {source}, {year}.',
    conference: '[{index}] {authors}. {title}[C]//{source}. {year}: {pages}.',
    thesis: '[{index}] {authors}. {title}[D]. {source}, {year}.',
    website: '[{index}] {authors}. {title}[EB/OL]. {url}, {accessDate}.',
    report: '[{index}] {authors}. {title}[R]. {source}, {year}.'
  },
  apa: {
    journal: '{authors}. ({year}). {title}. {source}, {volume}({issue}), {pages}.',
    book: '{authors}. ({year}). {title}. {source}.',
    conference: '{authors}. ({year}). {title}. In {source} (pp. {pages}).',
    thesis: '{authors}. ({year}). {title} [{type}]. {source}.',
    website: '{authors}. ({year}, {accessDate}). {title}. {url}',
    report: '{authors}. ({year}). {title}. {source}.'
  },
  mla: {
    journal: '{authors}. "{title}." {source}, vol. {volume}, no. {issue}, {year}, pp. {pages}.',
    book: '{authors}. {title}. {source}, {year}.',
    conference: '{authors}. "{title}." {source}, {year}, pp. {pages}.',
    thesis: '{authors}. {title}. {source}, {year}.',
    website: '{authors}. "{title}." {source}, {year}, {url}.',
    report: '{authors}. {title}. {source}, {year}.'
  },
  chicago: {
    journal: '{authors}. "{title}." {source} {volume}, no. {issue} ({year}): {pages}.',
    book: '{authors}. {title}. {source}, {year}.',
    conference: '{authors}. "{title}." In {source}, {year}.',
    thesis: '{authors}. "{title}." {type}, {source}, {year}.',
    website: '{authors}. "{title}." {source}. {url} (accessed {accessDate}).',
    report: '{authors}. {title}. {source}, {year}.'
  },
  ieee: {
    journal: '[{index}] {authors}, "{title}," {source}, vol. {volume}, no. {issue}, pp. {pages}, {year}.',
    book: '[{index}] {authors}, {title}. {source}, {year}.',
    conference: '[{index}] {authors}, "{title}," in {source}, {year}, pp. {pages}.',
    thesis: '[{index}] {authors}, "{title}," {type}, {source}, {year}.',
    website: '[{index}] {authors}, "{title}," {source}. {url}, {accessDate}.',
    report: '[{index}] {authors}, {title}. {source}, {year}.'
  }
}

class CitationReviewService {
  private citations: Map<string, Citation> = new Map()

  /**
   * 解析引用文本
   */
  parseCitation(text: string, index: number = 1): Citation {
    // 简单的解析逻辑 - 实际项目中应使用更复杂的解析器
    const citation: Citation = {
      id: `cite_${Date.now()}_${index}`,
      type: 'journal',
      rawText: text,
      authors: this.extractAuthors(text),
      title: this.extractTitle(text),
      year: this.extractYear(text),
      isValid: false,
      errors: []
    }

    return citation
  }

  /**
   * 提取作者
   */
  private extractAuthors(text: string): string[] {
    // 匹配常见的作者格式
    const patterns = [
      /([^,]+(?:,\s*[A-Z]\.?)+)/g,  // 姓, 名首字母
      /([A-Z][a-z]+\s+[A-Z][a-z]+)/g, // 全名
      /([^,]+?),/ // 逗号分隔
    ]

    for (const pattern of patterns) {
      const matches = text.match(pattern)
      if (matches && matches.length > 0) {
        return matches.slice(0, 5).map(a => a.trim().replace(/,$/, ''))
      }
    }

    return ['Unknown']
  }

  /**
   * 提取标题
   */
  private extractTitle(text: string): string {
    // 尝试提取引号内的内容或特定位置的文字
    const quotedMatch = text.match(/"([^"]+)"/)
    if (quotedMatch) return quotedMatch[1]

    // 国标格式 [N] 作者. 标题[J].
    const gbMatch = text.match(/\]\s*([^[\.]+)/)
    if (gbMatch) return gbMatch[1].trim()

    return 'Unknown Title'
  }

  /**
   * 提取年份
   */
  private extractYear(text: string): number | undefined {
    const match = text.match(/\b(19|20)\d{2}\b/)
    return match ? parseInt(match[0]) : undefined
  }

  /**
   * 检查引用格式
   */
  reviewCitation(citation: Citation, style: CitationStyle): Citation {
    const rules = CITATION_RULES[style]
    const errors: CitationError[] = []

    // 检查必填字段
    rules.forEach(rule => {
      if (rule.required) {
        const value = (citation as any)[rule.field]
        if (!value || (Array.isArray(value) && value.length === 0)) {
          errors.push({
            type: 'missing_field',
            message: rule.message,
            suggestion: `请补充${rule.field}信息`,
            severity: 'error'
          })
        } else if (rule.pattern && !rule.pattern.test(String(value))) {
          errors.push({
            type: 'format',
            message: `${rule.field}格式不正确`,
            suggestion: rule.message,
            severity: 'error'
          })
        }
      }
    })

    // 检查DOI
    if (citation.doi && !citation.doi.match(/^10\.\d{4,}\/.+/)) {
      errors.push({
        type: 'format',
        message: 'DOI格式可能不正确',
        suggestion: 'DOI应以10.开头',
        severity: 'warning'
      })
    }

    // 检查年份合理性
    if (citation.year) {
      const currentYear = new Date().getFullYear()
      if (citation.year > currentYear) {
        errors.push({
          type: 'invalid_date',
          message: '年份超出当前年份',
          suggestion: `请检查年份，当前年份为${currentYear}`,
          severity: 'error'
        })
      } else if (citation.year < 1900) {
        errors.push({
          type: 'invalid_date',
          message: '年份过于久远',
          suggestion: '请确认该文献的出版年份',
          severity: 'warning'
        })
      }
    }

    citation.errors = errors
    citation.isValid = errors.filter(e => e.severity === 'error').length === 0

    return citation
  }

  /**
   * 格式化引用
   */
  formatCitation(citation: Citation, style: CitationStyle, index: number = 1): string {
    const template = FORMAT_TEMPLATES[style][citation.type]
    if (!template) return citation.rawText

    const authorStr = this.formatAuthors(citation.authors, style)

    return template
      .replace('{index}', index.toString())
      .replace('{authors}', authorStr)
      .replace('{title}', citation.title)
      .replace('{source}', citation.source || '')
      .replace('{year}', citation.year?.toString() || '')
      .replace('{volume}', citation.volume || '')
      .replace('{issue}', citation.issue || '')
      .replace('{pages}', citation.pages || '')
      .replace('{doi}', citation.doi || '')
      .replace('{url}', citation.url || '')
      .replace('{accessDate}', citation.accessDate || '')
      .replace('{type}', citation.type)
  }

  /**
   * 格式化作者
   */
  private formatAuthors(authors: string[], style: CitationStyle): string {
    if (!authors || authors.length === 0) return 'Unknown'

    switch (style) {
      case 'gb7714':
        return authors.slice(0, 3).join(', ') + (authors.length > 3 ? ', 等' : '')
      case 'apa':
        if (authors.length === 1) return authors[0]
        if (authors.length === 2) return `${authors[0]} & ${authors[1]}`
        if (authors.length > 2) return `${authors[0]} et al.`
        return authors[0]
      case 'mla':
        return authors[0]
      case 'ieee':
        return authors.slice(0, 6).join(', ') + (authors.length > 6 ? ', et al.' : '')
      default:
        return authors.join(', ')
    }
  }

  /**
   * 批量审查引用
   */
  reviewCitations(citations: Citation[], style: CitationStyle): CitationReview {
    const reviewed = citations.map(c => this.reviewCitation(c, style))
    const allErrors = reviewed.flatMap(c => c.errors)

    const byType: Record<CitationType, number> = {
      journal: 0, book: 0, conference: 0, thesis: 0, website: 0, report: 0
    }

    reviewed.forEach(c => {
      byType[c.type]++
    })

    const styleConsistency = this.calculateStyleConsistency(reviewed, style)
    const completeness = this.calculateCompleteness(reviewed)

    return {
      totalCitations: reviewed.length,
      validCitations: reviewed.filter(c => c.isValid).length,
      invalidCitations: reviewed.filter(c => !c.isValid).length,
      missingCitations: 0, // 需要通过正文引用分析得出
      styleConsistency,
      completeness,
      byType,
      errors: allErrors,
      suggestions: this.generateSuggestions(reviewed, allErrors)
    }
  }

  /**
   * 计算格式一致性
   */
  private calculateStyleConsistency(citations: Citation[], targetStyle: CitationStyle): number {
    // 简化的计算逻辑
    const validCount = citations.filter(c => c.isValid).length
    return Math.round((validCount / citations.length) * 100)
  }

  /**
   * 计算完整性
   */
  private calculateCompleteness(citations: Citation[]): number {
    let totalFields = 0
    let filledFields = 0

    const requiredFields = ['authors', 'title', 'year', 'source']

    citations.forEach(c => {
      requiredFields.forEach(field => {
        totalFields++
        const value = (c as any)[field]
        if (value && (!Array.isArray(value) || value.length > 0)) {
          filledFields++
        }
      })
    })

    return totalFields > 0 ? Math.round((filledFields / totalFields) * 100) : 0
  }

  /**
   * 生成改进建议
   */
  private generateSuggestions(citations: Citation[], errors: CitationError[]): string[] {
    const suggestions: string[] = []

    // 统计各类错误
    const errorTypes = new Map<string, number>()
    errors.forEach(e => {
      errorTypes.set(e.type, (errorTypes.get(e.type) || 0) + 1)
    })

    if (errorTypes.get('missing_field') || 0 > 0) {
      suggestions.push(`补充缺失的字段信息（${errorTypes.get('missing_field')}处）`)
    }

    if (errorTypes.get('format') || 0 > 0) {
      suggestions.push('检查引用格式是否符合规范要求')
    }

    if (errorTypes.get('invalid_date') || 0 > 0) {
      suggestions.push('核实出版年份的准确性')
    }

    if (suggestions.length === 0) {
      suggestions.push('引用格式基本正确，建议再次核对细节')
    }

    return suggestions
  }

  /**
   * 自动修复引用
   */
  autoFixCitation(citation: Citation, style: CitationStyle): Citation {
    const fixed = { ...citation }

    // 修复作者格式
    if (fixed.authors) {
      fixed.authors = fixed.authors.map(a => a.trim())
    }

    // 修复年份
    if (!fixed.year) {
      const extracted = this.extractYear(fixed.rawText)
      if (extracted) fixed.year = extracted
    }

    // 重新审查
    return this.reviewCitation(fixed, style)
  }

  /**
   * 导出格式化后的引用列表
   */
  exportFormattedCitations(citations: Citation[], style: CitationStyle): string {
    return citations
      .map((c, i) => this.formatCitation(c, style, i + 1))
      .join('\n')
  }

  /**
   * 检查正文引用与参考文献的一致性
   */
  checkCitationConsistency(text: string, citations: Citation[]): {
    citedInText: string[]
    notCited: Citation[]
    notInReference: string[]
  } {
    // 提取正文中的引用标记
    const citedInText: string[] = []
    const bracketPattern = /\[(\d+(?:[-,]\d+)*)\]/g
    let match
    while ((match = bracketPattern.exec(text)) !== null) {
      citedInText.push(match[1])
    }

    // 找出未被引用的文献
    const notCited = citations.filter((_, index) => {
      const num = (index + 1).toString()
      return !citedInText.some(c => c.includes(num))
    })

    return {
      citedInText,
      notCited,
      notInReference: []
    }
  }
}

export const citationReviewService = new CitationReviewService()
export default citationReviewService
