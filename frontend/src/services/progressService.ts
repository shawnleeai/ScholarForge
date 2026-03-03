/**
 * 进度管理服务
 */

import api from './api'

export interface Milestone {
  id: string
  paper_id: string
  title: string
  description?: string
  planned_date: string
  actual_date?: string
  status: 'pending' | 'in_progress' | 'completed' | 'delayed'
  completion_percentage: number
  created_at: string
  updated_at: string
}

export interface Task {
  id: string
  paper_id: string
  title: string
  description?: string
  milestone_id?: string
  assignee_id?: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  progress: number
  priority: 'low' | 'medium' | 'high' | 'urgent'
  planned_start?: string
  planned_end?: string
  actual_start?: string
  actual_end?: string
  created_at: string
  updated_at: string
}

export interface GanttItem {
  id: string
  name: string
  start: string
  end: string
  progress: number
  status: string
  dependencies: string[]
}

export interface GanttChart {
  paper_id: string
  items: GanttItem[]
  milestones: Array<{
    date: string
    name: string
  }>
  start_date: string
  end_date: string
}

export interface Alert {
  id: string
  paper_id: string
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  affected_items: string[]
  suggestions: string[]
  is_read: boolean
  created_at: string
}

export interface ProgressReport {
  paper_id: string
  paper_title: string
  generated_at: string
  stats: {
    total_milestones: number
    completed_milestones: number
    in_progress_milestones: number
    delayed_milestones: number
    at_risk_milestones: number
    total_tasks: number
    completed_tasks: number
    overall_progress: number
    days_remaining: number
    on_track: boolean
  }
  milestones: Milestone[]
  alerts: Alert[]
  recommendations: string[]
  next_actions: string[]
}

export const progressService = {
  // 获取里程碑列表
  getMilestones: (paperId: string, status?: string) =>
    api.get(`/progress/papers/${paperId}/milestones`, { params: { status } }),

  // 创建里程碑
  createMilestone: (paperId: string, data: {
    title: string
    description?: string
    planned_date: string
  }) => api.post('/progress/milestones', data, { params: { paper_id: paperId } }),

  // 更新里程碑
  updateMilestone: (milestoneId: string, data: Partial<Milestone>) =>
    api.put(`/progress/milestones/${milestoneId}`, data),

  // 获取任务列表
  getTasks: (paperId: string, params?: { milestone_id?: string; status?: string }) =>
    api.get(`/progress/papers/${paperId}/tasks`, { params }),

  // 创建任务
  createTask: (paperId: string, data: {
    title: string
    description?: string
    milestone_id?: string
    priority?: string
    planned_start?: string
    planned_end?: string
  }) => api.post('/progress/tasks', data, { params: { paper_id: paperId } }),

  // 更新任务
  updateTask: (taskId: string, data: Partial<Task>) =>
    api.put(`/progress/tasks/${taskId}`, data),

  // 获取甘特图
  getGanttChart: (paperId: string, params?: { start_date?: string; end_date?: string }) =>
    api.get(`/progress/papers/${paperId}/gantt`, { params }),

  // 获取预警列表
  getAlerts: (paperId: string, params?: { severity?: string; unread_only?: boolean }) =>
    api.get(`/progress/papers/${paperId}/alerts`, { params }),

  // 解决预警
  resolveAlert: (alertId: string, resolution_note: string) =>
    api.post(`/progress/alerts/${alertId}/resolve`, null, { params: { resolution_note } }),

  // 获取进度报告
  getProgressReport: (paperId: string) =>
    api.get(`/progress/papers/${paperId}/report`),

  // 获取周报告
  getWeeklyReport: (paperId: string, weekNumber?: number) =>
    api.get(`/progress/papers/${paperId}/report/weekly`, { params: { week_number: weekNumber } }),

  // 获取进度设置
  getSettings: (paperId: string) =>
    api.get(`/progress/papers/${paperId}/settings`),

  // 更新进度设置
  updateSettings: (paperId: string, settings: {
    start_date?: string
    target_completion_date?: string
    working_days_per_week?: number
    reminder_enabled?: boolean
    reminder_days_before?: number
    auto_alert_enabled?: boolean
  }) => api.put(`/progress/papers/${paperId}/settings`, settings),
}

export default progressService
