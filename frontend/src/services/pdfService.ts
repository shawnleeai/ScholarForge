/**
 * PDF解析服务
 */

import { request } from './api'
import type { ApiResponse } from './api'

export interface PDFParseRequest {
  enable_ai?: boolean
  extract_references?: boolean
  extract_figures?: boolean
}

export interface PDFParseTask {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  file_name: string
  file_size: number
  message: string
  estimated_seconds: number
}

export interface PDFMetadata {
  title?: string
  authors: string[]
  abstract?: string
  keywords: string[]
  doi?: string
  publication_year?: number
  journal?: string
  pages?: number
  language: string
}

export interface Reference {
  id: string
  raw_text: string
  authors: string[]
  title?: string
  journal?: string
  year?: number
  doi?: string
  url?: string
}

export interface Section {
  title: string
  content: string
  level: number
  page_start?: number
  page_end?: number
}

export interface AIAnalysisResult {
  summary: string
  key_points: string[]
  methodology?: {
    research_type?: string
    data_collection?: string
    analysis_method?: string
  }
  research_gaps: string[]
}

export interface PDFParseResult {
  task_id: string
  status: string
  file_name: string
  metadata: PDFMetadata
  page_count: number
  reference_count: number
  figure_count: number
  ai_summary?: string
  ai_key_points?: string[]
  ai_methodology?: AIAnalysisResult['methodology']
  sections: Array<{
    title: string
    page_start?: number
  }>
  references: Reference[]
}

export interface PDFTextResult {
  full_text: string
  sections: Section[]
}

export interface PDFReferencesResult {
  total: number
  references: Reference[]
}

export const pdfService = {
  /**
   * 上传并解析PDF
   */
  async upload(
    file: File,
    options: PDFParseRequest = {},
    onProgress?: (percent: number) => void
  ): Promise<PDFParseTask> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('enable_ai', String(options.enable_ai ?? true))
    formData.append('extract_references', String(options.extract_references ?? true))
    formData.append('extract_figures', String(options.extract_figures ?? false))

    const response = await fetch('/api/v1/pdf/upload', {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('scholarforge-auth') ? JSON.parse(localStorage.getItem('scholarforge-auth')!).accessToken : ''}`
      }
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || '上传失败')
    }

    const result: ApiResponse<PDFParseTask> = await response.json()
    return result.data
  },

  /**
   * 查询解析状态
   */
  async getStatus(taskId: string): Promise<{
    task_id: string
    status: string
    file_name: string
    file_size: number
    processing_time_ms?: number
    error_message?: string
    created_at: string
    completed_at?: string
  }> {
    const response = await request.get<{ task_id: string; status: string; file_name: string; file_size: number; processing_time_ms?: number; error_message?: string; created_at: string; completed_at?: string }>(`/pdf/status/${taskId}`)
    return response.data
  },

  /**
   * 获取解析结果
   */
  async getResult(taskId: string): Promise<PDFParseResult> {
    const response = await request.get<PDFParseResult>(`/pdf/result/${taskId}`)
    return response.data
  },

  /**
   * 获取全文
   */
  async getFullText(taskId: string): Promise<PDFTextResult> {
    const response = await request.get<PDFTextResult>(`/pdf/result/${taskId}/text`)
    return response.data
  },

  /**
   * 获取参考文献
   */
  async getReferences(taskId: string): Promise<PDFReferencesResult> {
    const response = await request.get<PDFReferencesResult>(`/pdf/result/${taskId}/references`)
    return response.data
  },

  /**
   * 删除解析任务
   */
  async deleteTask(taskId: string): Promise<void> {
    await request.delete(`/pdf/tasks/${taskId}`)
  },

  /**
   * 轮询等待解析完成
   */
  async waitForCompletion(
    taskId: string,
    options: {
      interval?: number
      maxAttempts?: number
      onProgress?: (status: string) => void
    } = {}
  ): Promise<PDFParseResult> {
    const { interval = 2000, maxAttempts = 60, onProgress } = options

    for (let i = 0; i < maxAttempts; i++) {
      const status = await this.getStatus(taskId)
      onProgress?.(status.status)

      if (status.status === 'completed') {
        return this.getResult(taskId)
      }

      if (status.status === 'failed') {
        throw new Error(status.error_message || '解析失败')
      }

      await new Promise(resolve => setTimeout(resolve, interval))
    }

    throw new Error('解析超时，请稍后查询结果')
  }
}
