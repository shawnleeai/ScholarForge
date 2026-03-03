/**
 * 格式检查类型定义
 */

export type FormatCheckStatus = 'pending' | 'checking' | 'completed' | 'failed'
export type FormatIssueSeverity = 'error' | 'warning' | 'info'

export interface FormatRule {
  id: string
  name: string
  description: string
  category: 'structure' | 'citation' | 'typography' | 'language' | 'figure'
}

export interface FormatIssue {
  id: string
  ruleId: string
  ruleName: string
  severity: FormatIssueSeverity
  message: string
  sectionId?: string
  position?: {
    from: number
    to: number
  }
  suggestion?: string
}

export interface FormatCheckResult {
  id: string
  paperId: string
  paperTitle?: string
  templateId?: string
  templateName?: string
  status: FormatCheckStatus
  checkedAt: string
  score: number
  issues: FormatIssue[]
  summary: {
    errorCount: number
    warningCount: number
    infoCount: number
  }
  passedRules: string[]
  failedRules: string[]
  previewUrl?: string
}

export interface FormatCheckRequest {
  paperId: string
  templateId?: string
  rules?: string[]
}

export interface FormatConfig {
  fontFamily?: string
  fontSize?: number
  lineSpacing?: number
  marginTop?: number
  marginBottom?: number
  marginLeft?: number
  marginRight?: number
  paragraphIndent?: number
  heading1Font?: string
  heading1Size?: number
  heading2Font?: string
  heading2Size?: number
  heading3Font?: string
  heading3Size?: number
}

export interface FormatTemplate {
  id: string
  name: string
  description: string
  type: 'thesis' | 'journal' | 'conference'
  institution?: string
  rules: FormatRule[]
  config?: FormatConfig
  isDefault?: boolean
}
