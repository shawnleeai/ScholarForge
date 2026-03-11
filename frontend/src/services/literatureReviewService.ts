/**
 * 文献综述服务
 */

import { request } from './api'
import type { ApiResponse } from './api'

export interface LiteratureReviewRequest {
  article_ids: string[]
  focus_area: 'general' | 'methodology' | 'findings' | 'trends' | 'gaps'
  output_length: 'short' | 'medium' | 'long'
  language?: string
  include_citations?: boolean
  include_references?: boolean
  custom_prompt?: string
}

export interface LiteratureReviewTask {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  current_step: string
  error_message?: string
  created_at: string
  completed_at?: string
  result?: LiteratureReview
}

export interface LiteratureReview {
  id: string
  title: string
  abstract: string
  sections: LiteratureReviewSection[]
  themes: ThemeAnalysis[]
  comparisons: ComparisonPoint[]
  research_gaps: string[]
  future_directions: string[]
  references: Reference[]
  generated_at: string
  word_count: number
  metadata: {
    article_count: number
    focus_area: string
    output_length: string
  }
}

export interface LiteratureReviewSection {
  title: string
  content: string
  subsections?: LiteratureReviewSection[]
  cited_articles?: string[]
}

export interface ThemeAnalysis {
  theme: string
  description: string
  related_articles: string[]
  key_points: string[]
}

export interface ComparisonPoint {
  aspect: string
  comparisons: Record<string, string>
  consensus?: string
  differences: string[]
}

export interface Reference {
  id: string
  title: string
  authors: string[]
  year?: number
  journal?: string
  doi?: string
  url?: string
}

export interface QuickReviewRequest {
  topic: string
  keywords?: string[]
  max_articles?: number
  focus_area?: string
  output_length?: string
}

export interface ReviewOutline {
  title: string
  sections: Array<{
    title: string
    description?: string
    subsections?: Array<{ title: string; description?: string }>
  }>
  estimated_word_count: number
  key_themes: string[]
}

export const literatureReviewService = {
  /**
   * 生成文献综述
   */
  async generate(data: LiteratureReviewRequest): Promise<{ task_id: string; status: string }> {
    const response = await request.post<{ task_id: string; status: string }>('/literature-review/generate', data)
    return response.data
  },

  /**
   * 快速生成综述（自动检索文献）
   */
  async quickGenerate(data: QuickReviewRequest): Promise<{ task_id: string; status: string; message: string }> {
    const response = await request.post<{ task_id: string; status: string; message: string }>(
      '/literature-review/quick-generate',
      data
    )
    return response.data
  },

  /**
   * 查询任务状态
   */
  async getTaskStatus(taskId: string): Promise<LiteratureReviewTask> {
    const response = await request.get<LiteratureReviewTask>(`/literature-review/tasks/${taskId}`)
    return response.data
  },

  /**
   * 等待任务完成
   */
  async waitForCompletion(
    taskId: string,
    options: {
      interval?: number
      maxAttempts?: number
      onProgress?: (task: LiteratureReviewTask) => void
    } = {}
  ): Promise<LiteratureReview> {
    const { interval = 2000, maxAttempts = 150, onProgress } = options

    for (let i = 0; i < maxAttempts; i++) {
      const task = await this.getTaskStatus(taskId)
      onProgress?.(task)

      if (task.status === 'completed' && task.result) {
        return task.result
      }

      if (task.status === 'failed') {
        throw new Error(task.error_message || '生成失败')
      }

      await new Promise(resolve => setTimeout(resolve, interval))
    }

    throw new Error('生成超时，请稍后查询结果')
  },

  /**
   * 导出综述
   */
  async exportReview(
    taskId: string,
    format: 'markdown' | 'docx' | 'pdf' = 'markdown'
  ): Promise<{ format: string; content: string; filename: string }> {
    const response = await request.get<{ format: string; content: string; filename: string }>(
      `/literature-review/tasks/${taskId}/export`,
      { format }
    )
    return response.data
  },

  /**
   * 删除任务
   */
  async deleteTask(taskId: string): Promise<void> {
    await request.delete(`/literature-review/tasks/${taskId}`)
  },

  /**
   * 分析研究主题
   */
  async analyzeThemes(articleIds: string[]): Promise<{ themes: Array<{ name: string; description: string; article_count: number }> }> {
    const response = await request.post<{ themes: Array<{ name: string; description: string; article_count: number }> }>(
      '/literature-review/analyze-themes',
      articleIds
    )
    return response.data
  },

  /**
   * 对比文献
   */
  async compareArticles(
    articleIds: string[],
    aspects?: string[]
  ): Promise<{ comparison: Record<string, string> }> {
    const response = await request.post<{ comparison: Record<string, string> }>('/literature-review/compare', {
      article_ids: articleIds,
      comparison_aspects: aspects,
    })
    return response.data
  },

  /**
   * 生成大纲预览
   */
  async generateOutline(articles: Array<{ id: string; title: string; abstract: string }>): Promise<ReviewOutline> {
    // 这里可以调用后端API，暂时使用本地模拟
    const themes = await this.extractThemes(articles)

    return {
      title: `文献综述：${themes[0] || '相关研究进展'}`,
      sections: [
        { title: '1. 引言', description: '研究背景和综述目的' },
        { title: '2. 文献综述', description: '相关研究梳理', subsections: themes.map(t => ({ title: t, description: '' })) },
        { title: '3. 讨论', description: '研究发现讨论' },
        { title: '4. 结论与展望', description: '总结与未来方向' },
      ],
      estimated_word_count: 3000,
      key_themes: themes,
    }
  },

  /**
   * 提取主题（本地辅助函数）
   */
  async extractThemes(articles: Array<{ title: string; abstract: string }>): Promise<string[]> {
    const keywords = articles
      .flatMap(a => `${a.title} ${a.abstract}`.split(/[\s,;.]+/))
      .filter(w => w.length > 2)
      .reduce((acc, w) => {
        acc[w] = (acc[w] || 0) + 1
        return acc
      }, {} as Record<string, number>)

    return Object.entries(keywords)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([w]) => w)
  },
}
