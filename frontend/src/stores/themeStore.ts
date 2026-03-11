/**
 * 主题管理 Store
 * 支持多种主题切换和自定义主题
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemeMode = 'light' | 'dark' | 'system'
export type ThemePreset = 'default' | 'academic' | 'nature' | 'tech' | 'warm' | 'cool' | 'eyeCare'

export interface ThemeConfig {
  // 基础颜色
  primaryColor: string
  successColor: string
  warningColor: string
  errorColor: string
  infoColor: string

  // 背景色
  bgColor: string
  bgSecondary: string
  bgTertiary: string

  // 文字色
  textPrimary: string
  textSecondary: string
  textTertiary: string

  // 边框色
  borderColor: string
  dividerColor: string

  // 特效
  borderRadius: number
  shadowStrength: 'light' | 'medium' | 'strong'
  animationSpeed: 'slow' | 'normal' | 'fast'
}

// 预设主题配置
export const themePresets: Record<ThemePreset, ThemeConfig> = {
  // 默认主题
  default: {
    primaryColor: '#1890ff',
    successColor: '#52c41a',
    warningColor: '#faad14',
    errorColor: '#f5222d',
    infoColor: '#1890ff',
    bgColor: '#f0f2f5',
    bgSecondary: '#ffffff',
    bgTertiary: '#fafafa',
    textPrimary: 'rgba(0, 0, 0, 0.85)',
    textSecondary: 'rgba(0, 0, 0, 0.65)',
    textTertiary: 'rgba(0, 0, 0, 0.45)',
    borderColor: '#d9d9d9',
    dividerColor: '#f0f0f0',
    borderRadius: 6,
    shadowStrength: 'medium',
    animationSpeed: 'normal',
  },

  // 学术蓝
  academic: {
    primaryColor: '#1e3a5f',
    successColor: '#2e7d32',
    warningColor: '#ed6c02',
    errorColor: '#d32f2f',
    infoColor: '#0288d1',
    bgColor: '#f5f7fa',
    bgSecondary: '#ffffff',
    bgTertiary: '#f8f9fa',
    textPrimary: '#1a1a2e',
    textSecondary: '#4a4a6a',
    textTertiary: '#7a7a9a',
    borderColor: '#e1e4e8',
    dividerColor: '#eaecef',
    borderRadius: 4,
    shadowStrength: 'light',
    animationSpeed: 'normal',
  },

  // 自然绿
  nature: {
    primaryColor: '#2e7d32',
    successColor: '#4caf50',
    warningColor: '#ff9800',
    errorColor: '#e53935',
    infoColor: '#00acc1',
    bgColor: '#f1f8e9',
    bgSecondary: '#ffffff',
    bgTertiary: '#f9fbe7',
    textPrimary: '#1b5e20',
    textSecondary: '#2e7d32',
    textTertiary: '#558b2f',
    borderColor: '#dcedc8',
    dividerColor: '#c5e1a5',
    borderRadius: 8,
    shadowStrength: 'light',
    animationSpeed: 'slow',
  },

  // 科技紫
  tech: {
    primaryColor: '#7c4dff',
    successColor: '#00e676',
    warningColor: '#ffea00',
    errorColor: '#ff1744',
    infoColor: '#00b0ff',
    bgColor: '#0d1117',
    bgSecondary: '#161b22',
    bgTertiary: '#21262d',
    textPrimary: '#e6edf3',
    textSecondary: '#7d8590',
    textTertiary: '#484f58',
    borderColor: '#30363d',
    dividerColor: '#21262d',
    borderRadius: 6,
    shadowStrength: 'strong',
    animationSpeed: 'fast',
  },

  // 暖色调
  warm: {
    primaryColor: '#e65100',
    successColor: '#43a047',
    warningColor: '#fb8c00',
    errorColor: '#e53935',
    infoColor: '#1e88e5',
    bgColor: '#fff3e0',
    bgSecondary: '#ffffff',
    bgTertiary: '#ffe0b2',
    textPrimary: '#3e2723',
    textSecondary: '#5d4037',
    textTertiary: '#8d6e63',
    borderColor: '#ffcc80',
    dividerColor: '#ffe0b2',
    borderRadius: 8,
    shadowStrength: 'medium',
    animationSpeed: 'normal',
  },

  // 冷色调
  cool: {
    primaryColor: '#1565c0',
    successColor: '#00897b',
    warningColor: '#ffa726',
    errorColor: '#ef5350',
    infoColor: '#42a5f5',
    bgColor: '#e3f2fd',
    bgSecondary: '#ffffff',
    bgTertiary: '#bbdefb',
    textPrimary: '#0d47a1',
    textSecondary: '#1976d2',
    textTertiary: '#42a5f5',
    borderColor: '#90caf9',
    dividerColor: '#bbdefb',
    borderRadius: 6,
    shadowStrength: 'light',
    animationSpeed: 'slow',
  },

  // 护眼模式
  eyeCare: {
    primaryColor: '#5d7a52',
    successColor: '#7da453',
    warningColor: '#c4a35a',
    errorColor: '#b86e6e',
    infoColor: '#5a7a8c',
    bgColor: '#c7c7b0',
    bgSecondary: '#d4d4c0',
    bgTertiary: '#e0e0d0',
    textPrimary: '#3a3a2e',
    textSecondary: '#5a5a4e',
    textTertiary: '#7a7a6e',
    borderColor: '#b0b0a0',
    dividerColor: '#c0c0b0',
    borderRadius: 4,
    shadowStrength: 'light',
    animationSpeed: 'slow',
  },
}

// 深色模式覆盖
export const darkModeOverride: Partial<ThemeConfig> = {
  bgColor: '#141414',
  bgSecondary: '#1f1f1f',
  bgTertiary: '#2a2a2a',
  textPrimary: 'rgba(255, 255, 255, 0.85)',
  textSecondary: 'rgba(255, 255, 255, 0.65)',
  textTertiary: 'rgba(255, 255, 255, 0.45)',
  borderColor: '#434343',
  dividerColor: '#303030',
}

interface ThemeState {
  // 当前主题设置
  mode: ThemeMode
  preset: ThemePreset
  customConfig?: Partial<ThemeConfig>

  // 派生状态
  isDark: boolean
  currentTheme: ThemeConfig

  // 操作方法
  setMode: (mode: ThemeMode) => void
  setPreset: (preset: ThemePreset) => void
  setCustomConfig: (config: Partial<ThemeConfig>) => void
  resetToDefault: () => void
  applyTheme: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'light',
      preset: 'default',
      customConfig: {},
      isDark: false,
      currentTheme: themePresets.default,

      setMode: (mode) => {
        const isDark = mode === 'dark' ||
          (mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

        set({ mode, isDark })
        get().applyTheme()
      },

      setPreset: (preset) => {
        set({ preset, customConfig: {} })
        get().applyTheme()
      },

      setCustomConfig: (config) => {
        set((state) => ({
          customConfig: { ...state.customConfig, ...config },
        }))
        get().applyTheme()
      },

      resetToDefault: () => {
        set({
          mode: 'light',
          preset: 'default',
          customConfig: {},
          isDark: false,
        })
        get().applyTheme()
      },

      applyTheme: () => {
        const { preset, customConfig, isDark, mode } = get()

        // 基础主题
        let theme = { ...themePresets[preset] }

        // 应用自定义配置
        if (customConfig) {
          theme = { ...theme, ...customConfig }
        }

        // 应用深色模式
        if (isDark && mode !== 'light') {
          theme = { ...theme, ...darkModeOverride }
        }

        set({ currentTheme: theme })

        // 应用到 CSS 变量
        const root = document.documentElement
        root.style.setProperty('--sf-primary', theme.primaryColor)
        root.style.setProperty('--sf-success', theme.successColor)
        root.style.setProperty('--sf-warning', theme.warningColor)
        root.style.setProperty('--sf-error', theme.errorColor)
        root.style.setProperty('--sf-info', theme.infoColor)
        root.style.setProperty('--sf-bg', theme.bgColor)
        root.style.setProperty('--sf-bg-secondary', theme.bgSecondary)
        root.style.setProperty('--sf-bg-tertiary', theme.bgTertiary)
        root.style.setProperty('--sf-text-primary', theme.textPrimary)
        root.style.setProperty('--sf-text-secondary', theme.textSecondary)
        root.style.setProperty('--sf-text-tertiary', theme.textTertiary)
        root.style.setProperty('--sf-border', theme.borderColor)
        root.style.setProperty('--sf-divider', theme.dividerColor)
        root.style.setProperty('--sf-radius', `${theme.borderRadius}px`)

        // 设置 data-theme 属性
        document.body.setAttribute('data-theme', isDark ? 'dark' : 'light')
        document.body.setAttribute('data-preset', preset)

        // 更新 Ant Design 主题
        window.dispatchEvent(new CustomEvent('themeChange', { detail: theme }))
      },
    }),
    {
      name: 'scholarforge-theme',
      partialize: (state) => ({
        mode: state.mode,
        preset: state.preset,
        customConfig: state.customConfig,
      }),
      onRehydrateStorage: () => (state) => {
        // 恢复时重新应用主题
        if (state) {
          setTimeout(() => state.applyTheme(), 0)
        }
      },
    }
  )
)

// 监听系统主题变化
if (typeof window !== 'undefined') {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', (e) => {
    const store = useThemeStore.getState()
    if (store.mode === 'system') {
      store.setMode('system')
    }
  })
}

export default useThemeStore
