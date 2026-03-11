/**
 * Word文档解析服务
 * 支持.docx文件的解析、结构识别和内容提取
 */

import type { Article } from '@/types'

// Word文档段落结构
export interface WordParagraph {
  text: string
  style?: string
  level?: number
  isHeading: boolean
  isList: boolean
  listLevel?: number
  formatting?: {
    bold?: boolean
    italic?: boolean
    underline?: boolean
    alignment?: 'left' | 'center' | 'right' | 'justify'
  }
}

// Word文档结构
export interface WordDocumentStructure {
  title?: string
  abstract?: string
  keywords?: string[]
  headings: WordHeading[]
  paragraphs: WordParagraph[]
  tables: WordTable[]
  images: WordImage[]
  fullText: string
}

// 标题结构
export interface WordHeading {
  level: number
  text: string
  paragraphs: WordParagraph[]
  subHeadings?: WordHeading[]
}

// 表格结构
export interface WordTable {
  rows: number
  cols: number
  cells: string[][]
  caption?: string
}

// 图片结构
export interface WordImage {
  altText?: string
  caption?: string
}

// 文档类型
export type DocumentType =
  | 'thesis_proposal'  // 开题报告
  | 'thesis'           // 毕业论文
  | 'literature_review' // 文献综述
  | 'research_report'  // 研究报告
  | 'journal_paper'    // 期刊论文
  | 'conference_paper' // 会议论文
  | 'other'            // 其他

// 模板要求
export interface TemplateRequirement {
  type: DocumentType
  name: string
  description: string
  requiredSections: RequiredSection[]
  formatRules: FormatRule[]
}

// 必需章节
export interface RequiredSection {
  name: string
  level: number
  required: boolean
  minLength?: number
  maxLength?: number
  description?: string
}

// 格式规则
export interface FormatRule {
  type: 'font' | 'spacing' | 'margin' | 'alignment'
  property: string
  value: string | number
  description: string
}

// 解析结果
export interface WordParseResult {
  success: boolean
  document?: WordDocumentStructure
  documentType?: DocumentType
  matchedTemplate?: TemplateRequirement
  structureValidation?: StructureValidationResult
  error?: string
}

// 结构验证结果
export interface StructureValidationResult {
  isValid: boolean
  missingSections: string[]
  formatIssues: FormatIssue[]
  suggestions: string[]
}

// 格式问题
export interface FormatIssue {
  type: 'error' | 'warning' | 'info'
  message: string
  location?: string
  suggestion?: string
}

// 是否使用模拟模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// 开题报告模板要求
const THESIS_PROPOSAL_TEMPLATE: TemplateRequirement = {
  type: 'thesis_proposal',
  name: '开题报告',
  description: '研究生学位论文开题报告标准格式',
  requiredSections: [
    { name: '选题背景与意义', level: 1, required: true, description: '阐述研究背景和选题意义' },
    { name: '国内外研究现状', level: 1, required: true, description: '文献综述部分' },
    { name: '研究内容', level: 1, required: true, description: '主要研究内容介绍' },
    { name: '研究方法', level: 1, required: true, description: '采用的研究方法和技术路线' },
    { name: '技术路线', level: 1, required: true, description: '研究实施步骤' },
    { name: '预期成果', level: 1, required: true, description: '预期取得的成果' },
    { name: '进度安排', level: 1, required: true, description: '研究时间规划' },
    { name: '参考文献', level: 1, required: true, description: '引用文献列表' }
  ],
  formatRules: [
    { type: 'font', property: 'title', value: '黑体,小二号', description: '一级标题使用黑体小二号' },
    { type: 'font', property: 'heading1', value: '黑体,三号', description: '一级标题使用黑体三号' },
    { type: 'font', property: 'heading2', value: '楷体,四号', description: '二级标题使用楷体四号' },
    { type: 'font', property: 'body', value: '宋体,小四', description: '正文使用宋体小四号' },
    { type: 'spacing', property: 'lineHeight', value: 1.5, description: '1.5倍行距' },
    { type: 'margin', property: 'top', value: 2.54, description: '上边距2.54cm' },
    { type: 'margin', property: 'bottom', value: 2.54, description: '下边距2.54cm' },
    { type: 'margin', property: 'left', value: 3.17, description: '左边距3.17cm' },
    { type: 'margin', property: 'right', value: 3.17, description: '右边距3.17cm' }
  ]
}

// 毕业论文模板
const THESIS_TEMPLATE: TemplateRequirement = {
  type: 'thesis',
  name: '毕业论文',
  description: '研究生学位论文标准格式',
  requiredSections: [
    { name: '摘要', level: 1, required: true, minLength: 300, maxLength: 800, description: '中文摘要' },
    { name: 'Abstract', level: 1, required: true, description: '英文摘要' },
    { name: '目录', level: 1, required: true, description: '章节目录' },
    { name: '绪论', level: 1, required: true, description: '研究背景、意义、现状' },
    { name: '相关理论与技术', level: 1, required: true, description: '理论基础' },
    { name: '研究方法', level: 1, required: true, description: '研究方法设计' },
    { name: '实验与分析', level: 1, required: true, description: '实验和数据分析' },
    { name: '结论与展望', level: 1, required: true, description: '研究总结' },
    { name: '参考文献', level: 1, required: true, description: '参考文献列表' },
    { name: '致谢', level: 1, required: true, description: '致谢部分' }
  ],
  formatRules: [
    { type: 'font', property: 'title', value: '黑体,二号', description: '论文题目黑体二号' },
    { type: 'font', property: 'heading1', value: '黑体,三号', description: '一级标题黑体三号' },
    { type: 'font', property: 'heading2', value: '黑体,四号', description: '二级标题黑体四号' },
    { type: 'font', property: 'heading3', value: '黑体,小四', description: '三级标题黑体小四号' },
    { type: 'font', property: 'body', value: '宋体,小四', description: '正文宋体小四号' },
    { type: 'spacing', property: 'lineHeight', value: 1.5, description: '1.5倍行距' }
  ]
}

// 模板库
const TEMPLATES: Record<DocumentType, TemplateRequirement> = {
  thesis_proposal: THESIS_PROPOSAL_TEMPLATE,
  thesis: THESIS_TEMPLATE,
  literature_review: {
    type: 'literature_review',
    name: '文献综述',
    description: '文献综述标准格式',
    requiredSections: [
      { name: '摘要', level: 1, required: true },
      { name: '引言', level: 1, required: true },
      { name: '文献回顾', level: 1, required: true },
      { name: '研究现状', level: 1, required: true },
      { name: '发展趋势', level: 1, required: true },
      { name: '结论', level: 1, required: true },
      { name: '参考文献', level: 1, required: true }
    ],
    formatRules: []
  },
  research_report: {
    type: 'research_report',
    name: '研究报告',
    description: '研究报告标准格式',
    requiredSections: [
      { name: '摘要', level: 1, required: true },
      { name: '研究背景', level: 1, required: true },
      { name: '研究方法', level: 1, required: true },
      { name: '研究结果', level: 1, required: true },
      { name: '讨论', level: 1, required: true },
      { name: '结论', level: 1, required: true }
    ],
    formatRules: []
  },
  journal_paper: {
    type: 'journal_paper',
    name: '期刊论文',
    description: '学术论文标准格式',
    requiredSections: [
      { name: 'Abstract', level: 1, required: true },
      { name: 'Introduction', level: 1, required: true },
      { name: 'Related Work', level: 1, required: true },
      { name: 'Methodology', level: 1, required: true },
      { name: 'Experiments', level: 1, required: true },
      { name: 'Conclusion', level: 1, required: true },
      { name: 'References', level: 1, required: true }
    ],
    formatRules: []
  },
  conference_paper: {
    type: 'conference_paper',
    name: '会议论文',
    description: '会议论文标准格式',
    requiredSections: [
      { name: 'Abstract', level: 1, required: true },
      { name: 'Introduction', level: 1, required: true },
      { name: 'Method', level: 1, required: true },
      { name: 'Results', level: 1, required: true },
      { name: 'Conclusion', level: 1, required: true }
    ],
    formatRules: []
  },
  other: {
    type: 'other',
    name: '其他文档',
    description: '通用文档格式',
    requiredSections: [],
    formatRules: []
  }
}

export const wordParserService = {
  /**
   * 解析Word文档
   * @param file Word文件
   * @returns 解析结果
   */
  async parseDocument(file: File): Promise<WordParseResult> {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 1500))
      return this.getMockParseResult(file.name)
    }

    try {
      // 检查文件类型
      if (!file.name.match(/\.(docx|doc)$/i)) {
        return {
          success: false,
          error: '不支持的文件格式，请上传.docx或.doc文件'
        }
      }

      // 读取文件内容
      const arrayBuffer = await file.arrayBuffer()

      // 使用mammoth.js解析（实际项目中需要安装mammoth）
      // const result = await mammoth.extractRawText({ arrayBuffer })

      // 这里模拟解析结果
      const structure = await this.extractStructure(arrayBuffer, file.name)

      // 识别文档类型
      const documentType = this.detectDocumentType(structure)

      // 匹配模板
      const matchedTemplate = TEMPLATES[documentType]

      // 验证结构
      const structureValidation = this.validateStructure(structure, matchedTemplate)

      return {
        success: true,
        document: structure,
        documentType,
        matchedTemplate,
        structureValidation
      }
    } catch (error) {
      console.error('Word解析失败:', error)
      return {
        success: false,
        error: '文档解析失败，请检查文件是否损坏'
      }
    }
  },

  /**
   * 提取文档结构
   */
  async extractStructure(arrayBuffer: ArrayBuffer, fileName: string): Promise<WordDocumentStructure> {
    // 模拟结构提取
    // 实际实现中应该解析docx的XML结构

    const mockStructure: WordDocumentStructure = {
      title: fileName.replace(/\.docx?$/i, ''),
      headings: [],
      paragraphs: [],
      tables: [],
      images: [],
      fullText: ''
    }

    return mockStructure
  },

  /**
   * 检测文档类型
   */
  detectDocumentType(structure: WordDocumentStructure): DocumentType {
    const text = structure.fullText.toLowerCase()
    const headings = structure.headings.map(h => h.text.toLowerCase())

    // 根据关键词和结构判断文档类型
    if (text.includes('开题报告') || headings.some(h => h.includes('选题背景'))) {
      return 'thesis_proposal'
    }

    if (text.includes('学位论文') || headings.some(h => h.includes('绪论') && h.includes('结论'))) {
      return 'thesis'
    }

    if (text.includes('文献综述') || headings.some(h => h.includes('文献回顾'))) {
      return 'literature_review'
    }

    if (headings.some(h => h.includes('abstract') && h.includes('introduction'))) {
      if (headings.some(h => h.includes('methodology') || h.includes('experiments'))) {
        return 'journal_paper'
      }
      return 'conference_paper'
    }

    return 'other'
  },

  /**
   * 验证文档结构
   */
  validateStructure(
    structure: WordDocumentStructure,
    template: TemplateRequirement
  ): StructureValidationResult {
    const missingSections: string[] = []
    const formatIssues: FormatIssue[] = []
    const suggestions: string[] = []

    // 检查必需章节
    template.requiredSections.forEach(section => {
      if (section.required) {
        const found = structure.headings.some(
          h => h.text.includes(section.name) ||
               section.name.includes(h.text)
        )
        if (!found) {
          missingSections.push(section.name)
        }
      }
    })

    // 检查摘要
    if (!structure.abstract) {
      formatIssues.push({
        type: 'warning',
        message: '未检测到摘要部分',
        suggestion: '建议添加中英文摘要'
      })
    }

    // 检查关键词
    if (!structure.keywords || structure.keywords.length === 0) {
      formatIssues.push({
        type: 'info',
        message: '未检测到关键词',
        suggestion: '建议添加3-5个关键词'
      })
    }

    // 生成建议
    if (missingSections.length > 0) {
      suggestions.push(`缺少以下必需章节：${missingSections.join('、')}`)
    }

    if (structure.headings.length < 3) {
      suggestions.push('文档结构较为简单，建议增加更多细分章节')
    }

    return {
      isValid: missingSections.length === 0 && formatIssues.filter(i => i.type === 'error').length === 0,
      missingSections,
      formatIssues,
      suggestions
    }
  },

  /**
   * 获取所有可用模板
   */
  getTemplates(): TemplateRequirement[] {
    return Object.values(TEMPLATES)
  },

  /**
   * 获取特定模板
   */
  getTemplate(type: DocumentType): TemplateRequirement | undefined {
    return TEMPLATES[type]
  },

  /**
   * 模拟解析结果
   */
  getMockParseResult(fileName: string): WordParseResult {
    const mockStructure: WordDocumentStructure = {
      title: fileName.replace(/\.docx?$/i, ''),
      abstract: '本文研究了基于深度学习的自然语言处理方法，提出了一种新的模型架构...',
      keywords: ['深度学习', '自然语言处理', '神经网络'],
      headings: [
        { level: 1, text: '选题背景与意义', paragraphs: [] },
        { level: 1, text: '国内外研究现状', paragraphs: [] },
        { level: 2, text: '国外研究现状', paragraphs: [] },
        { level: 2, text: '国内研究现状', paragraphs: [] },
        { level: 1, text: '研究内容', paragraphs: [] },
        { level: 1, text: '研究方法', paragraphs: [] },
        { level: 1, text: '技术路线', paragraphs: [] },
        { level: 1, text: '预期成果', paragraphs: [] },
        { level: 1, text: '进度安排', paragraphs: [] },
        { level: 1, text: '参考文献', paragraphs: [] }
      ],
      paragraphs: [
        { text: '随着人工智能技术的发展...', isHeading: false, isList: false },
        { text: '本研究旨在解决...', isHeading: false, isList: false }
      ],
      tables: [],
      images: [],
      fullText: '这是模拟的开题报告全文内容...'
    }

    return {
      success: true,
      document: mockStructure,
      documentType: 'thesis_proposal',
      matchedTemplate: THESIS_PROPOSAL_TEMPLATE,
      structureValidation: {
        isValid: true,
        missingSections: [],
        formatIssues: [
          {
            type: 'info',
            message: '建议补充更多图表说明',
            suggestion: '在技术路线章节添加流程图'
          }
        ],
        suggestions: [
          '文档结构完整，符合开题报告要求',
          '建议在研究方法章节增加对比实验设计'
        ]
      }
    }
  },

  /**
   * 将解析结果转换为文章对象
   */
  convertToArticle(structure: WordDocumentStructure, userId: string): Partial<Article> {
    return {
      title: structure.title || '未命名文档',
      abstract: structure.abstract,
      keywords: structure.keywords,
      authors: [{ name: '导入用户', affiliation: '' }],
      content: structure.fullText,
      sourceType: 'word_import',
    }
  },

  /**
   * 分析文档大纲
   */
  analyzeOutline(structure: WordDocumentStructure): {
    totalSections: number
    maxDepth: number
    sectionDistribution: Record<number, number>
  } {
    const sectionDistribution: Record<number, number> = {}

    structure.headings.forEach(h => {
      sectionDistribution[h.level] = (sectionDistribution[h.level] || 0) + 1
    })

    return {
      totalSections: structure.headings.length,
      maxDepth: Math.max(...structure.headings.map(h => h.level), 1),
      sectionDistribution
    }
  }
}

export default wordParserService
