/**
 * 应用主组件 - 支持代码分割和懒加载
 */

import { useEffect, Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Spin } from 'antd'

import { useAuthStore } from '@/stores'
import { authService } from '@/services'

// 布局组件
import MainLayout from '@/components/layout/MainLayout'
import AuthLayout from '@/components/layout/AuthLayout'

// 核心页面（不懒加载）
import Login from '@/pages/auth/Login'
import Register from '@/pages/auth/Register'
import Dashboard from '@/pages/Dashboard'

// 懒加载页面组件
const PaperList = lazy(() => import('@/pages/paper/PaperList'))
const PaperEditor = lazy(() => import('@/pages/paper/PaperEditor'))
const Library = lazy(() => import('@/pages/library/Library'))
const Search = lazy(() => import('@/pages/library/Search'))
const Settings = lazy(() => import('@/pages/Settings'))
const TemplateList = lazy(() => import('@/pages/templates').then(m => ({ default: m.TemplateList })))
const TopicAssistant = lazy(() => import('@/pages/topic').then(m => ({ default: m.TopicAssistant })))
const ProgressManager = lazy(() => import('@/pages/progress').then(m => ({ default: m.ProgressManager })))
const KnowledgeGraph = lazy(() => import('@/pages/knowledge').then(m => ({ default: m.KnowledgeGraph })))
const JournalMatcher = lazy(() => import('@/pages/journal').then(m => ({ default: m.JournalMatcher })))
const ReferenceManagement = lazy(() => import('@/pages/reference/ReferenceManagement'))
const PlagiarismCheck = lazy(() => import('@/pages/plagiarism/PlagiarismCheck'))
const FormatCheck = lazy(() => import('@/pages/format/FormatCheck'))
const DefenseAssistant = lazy(() => import('@/pages/defense/DefenseAssistant'))

// 路由守卫
import ProtectedRoute from '@/components/ProtectedRoute'

// 错误边界
import { ErrorBoundary } from '@/components'

// 懒加载 fallback 组件
const PageLoading = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
  }}>
    <Spin size="large" tip="页面加载中..." />
  </div>
)

function App() {
  const { isAuthenticated, accessToken, setUser, setLoading, logout } = useAuthStore()

  // 获取当前用户信息
  useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      try {
        const response = await authService.getCurrentUser()
        setUser(response.data)
        setLoading(false)
        return response.data
      } catch (error) {
        logout()
        setLoading(false)
        throw error
      }
    },
    enabled: !!accessToken && !isAuthenticated,
  })

  // 初始化加载状态
  useEffect(() => {
    if (!accessToken) {
      setLoading(false)
    }
  }, [accessToken, setLoading])

  if (accessToken && !isAuthenticated) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div className="animate-spin" style={{
            width: 40,
            height: 40,
            border: '3px solid #f0f0f0',
            borderTopColor: '#1890ff',
            borderRadius: '50%',
            margin: '0 auto 16px',
          }} />
          <div style={{ color: '#666' }}>加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundary>
      <Suspense fallback={<PageLoading />}>
        <Routes>
          {/* 认证相关页面 */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
          </Route>

          {/* 主应用页面 */}
          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />

            {/* 论文管理 */}
            <Route path="/papers" element={<PaperList />} />
            <Route path="/papers/:paperId" element={<PaperEditor />} />
            <Route path="/papers/:paperId/sections/:sectionId" element={<PaperEditor />} />

            {/* 文献库 */}
            <Route path="/library" element={<Library />} />
            <Route path="/library/search" element={<Search />} />

            {/* 模板中心 */}
            <Route path="/templates" element={<TemplateList />} />

            {/* 选题助手 */}
            <Route path="/topic" element={<TopicAssistant />} />

            {/* 进度管理 */}
            <Route path="/progress" element={<ProgressManager />} />

            {/* 知识图谱 */}
            <Route path="/knowledge" element={<KnowledgeGraph />} />

            {/* 期刊匹配 */}
            <Route path="/journal" element={<JournalMatcher />} />

            {/* 参考文献管理 */}
            <Route path="/references" element={<ReferenceManagement />} />

            {/* 查重检测 */}
            <Route path="/plagiarism" element={<PlagiarismCheck />} />
            <Route path="/plagiarism/:paperId" element={<PlagiarismCheck />} />

            {/* 格式检测 */}
            <Route path="/format" element={<FormatCheck />} />
            <Route path="/format/:paperId" element={<FormatCheck />} />

            {/* 答辩准备 */}
            <Route path="/defense" element={<DefenseAssistant />} />
            <Route path="/defense/:paperId" element={<DefenseAssistant />} />

            {/* 设置 */}
            <Route path="/settings" element={<Settings />} />
          </Route>

          {/* 404 页面 */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  )
}

export default App
