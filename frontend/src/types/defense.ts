/**
 * 答辩准备类型定义
 */

export interface ChecklistItem {
  id: string
  category: string
  content: string
  completed: boolean
  order: number
}

export interface DefenseChecklist {
  id: string
  paperId: string
  items: ChecklistItem[]
  progress: number
  createdAt: string
  updatedAt: string
}

export interface PPTSlide {
  id: string
  type: 'title' | 'content' | 'thanks' | string
  title: string
  content: string
  order: number
  duration?: number
}

export interface PPTOutline {
  title: string
  slides: PPTSlide[]
}

export interface DefensePPT {
  id: string
  paperId: string
  template: string
  outline: PPTOutline
  status: 'draft' | 'generated' | 'finalized'
  createdAt: string
  updatedAt: string
}

export interface DefenseQA {
  id: string
  question: string
  answer: string
  category: string
  difficulty: 'easy' | 'medium' | 'hard'
  paperId?: string
}

export interface MockQuestion {
  id: string
  question: string
  difficulty: string
}

export interface MockSession {
  id: string
  paperId: string
  status: 'ongoing' | 'completed'
  questions: MockQuestion[]
  createdAt: string
}

export interface MockResult {
  sessionId: string
  totalScore: number
  grade: string
  suggestions: string[]
}
