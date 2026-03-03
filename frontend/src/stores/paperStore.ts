/**
 * 论文状态管理
 */

import { create } from 'zustand'
import { Paper, PaperSection } from '@/types'

interface PaperState {
  // 当前编辑的论文
  currentPaper: Paper | null
  sections: PaperSection[]

  // 论文列表
  papers: Paper[]
  totalPapers: number

  // 当前选中的章节
  activeSectionId: string | null

  // 编辑器状态
  isSaving: boolean
  lastSavedAt: Date | null
  hasUnsavedChanges: boolean

  // 操作
  setCurrentPaper: (paper: Paper | null) => void
  setSections: (sections: PaperSection[]) => void
  updateSection: (sectionId: string, content: Partial<PaperSection>) => void
  setPapers: (papers: Paper[], total: number) => void
  setActiveSection: (sectionId: string | null) => void
  setSaving: (saving: boolean) => void
  setLastSaved: (date: Date) => void
  setHasUnsavedChanges: (hasChanges: boolean) => void
  clearCurrentPaper: () => void
}

export const usePaperStore = create<PaperState>((set) => ({
  // 初始状态
  currentPaper: null,
  sections: [],
  papers: [],
  totalPapers: 0,
  activeSectionId: null,
  isSaving: false,
  lastSavedAt: null,
  hasUnsavedChanges: false,

  // 设置当前论文
  setCurrentPaper: (paper) =>
    set({
      currentPaper: paper,
      activeSectionId: null,
      hasUnsavedChanges: false,
    }),

  // 设置章节列表
  setSections: (sections) =>
    set({ sections }),

  // 更新章节
  updateSection: (sectionId, content) =>
    set((state) => ({
      sections: state.sections.map((section) =>
        section.id === sectionId ? { ...section, ...content } : section
      ),
      hasUnsavedChanges: true,
    })),

  // 设置论文列表
  setPapers: (papers, total) =>
    set({
      papers,
      totalPapers: total,
    }),

  // 设置活动章节
  setActiveSection: (sectionId) =>
    set({ activeSectionId: sectionId }),

  // 设置保存状态
  setSaving: (isSaving) =>
    set({ isSaving }),

  // 设置最后保存时间
  setLastSaved: (date) =>
    set({
      lastSavedAt: date,
      hasUnsavedChanges: false,
    }),

  // 设置未保存状态
  setHasUnsavedChanges: (hasChanges) =>
    set({ hasUnsavedChanges: hasChanges }),

  // 清除当前论文
  clearCurrentPaper: () =>
    set({
      currentPaper: null,
      sections: [],
      activeSectionId: null,
      hasUnsavedChanges: false,
    }),
}))
