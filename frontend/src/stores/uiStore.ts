/**
 * UI 状态管理
 */

import { create } from 'zustand'

type SidebarMode = 'expanded' | 'collapsed'
type ThemeMode = 'light' | 'dark' | 'system'

interface UIState {
  // 侧边栏
  sidebarCollapsed: boolean
  sidebarMode: SidebarMode

  // 主题
  theme: ThemeMode

  // AI 助手面板
  aiPanelVisible: boolean
  aiPanelWidth: number

  // 全局加载
  globalLoading: boolean

  // 通知
  notifications: Array<{
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    message: string
    description?: string
  }>

  // 操作
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setTheme: (theme: ThemeMode) => void
  toggleAIPanel: () => void
  setAIPanelVisible: (visible: boolean) => void
  setAIPanelWidth: (width: number) => void
  setGlobalLoading: (loading: boolean) => void
  addNotification: (notification: Omit<UIState['notifications'][0], 'id'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
}

export const useUIStore = create<UIState>((set) => ({
  // 初始状态
  sidebarCollapsed: false,
  sidebarMode: 'expanded',
  theme: 'light',
  aiPanelVisible: false,
  aiPanelWidth: 400,
  globalLoading: false,
  notifications: [],

  // 切换侧边栏
  toggleSidebar: () =>
    set((state) => ({
      sidebarCollapsed: !state.sidebarCollapsed,
      sidebarMode: state.sidebarCollapsed ? 'expanded' : 'collapsed',
    })),

  // 设置侧边栏状态
  setSidebarCollapsed: (collapsed) =>
    set({
      sidebarCollapsed: collapsed,
      sidebarMode: collapsed ? 'collapsed' : 'expanded',
    }),

  // 设置主题
  setTheme: (theme) =>
    set({ theme }),

  // 切换 AI 面板
  toggleAIPanel: () =>
    set((state) => ({
      aiPanelVisible: !state.aiPanelVisible,
    })),

  // 设置 AI 面板可见性
  setAIPanelVisible: (visible) =>
    set({ aiPanelVisible: visible }),

  // 设置 AI 面板宽度
  setAIPanelWidth: (width) =>
    set({ aiPanelWidth: width }),

  // 设置全局加载
  setGlobalLoading: (loading) =>
    set({ globalLoading: loading }),

  // 添加通知
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { ...notification, id: Date.now().toString() },
      ],
    })),

  // 移除通知
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  // 清除所有通知
  clearNotifications: () =>
    set({ notifications: [] }),
}))
