/**
 * API 客户端配置
 * 包含完善的错误处理和重试机制
 */

import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios'

// 后端响应格式
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
  timestamp?: string
}

// 自定义错误类
export class ApiError extends Error {
  code: number
  details?: Record<string, unknown>
  isNetworkError: boolean
  isTimeout: boolean

  constructor(message: string, code: number = 500, details?: Record<string, unknown>) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
    this.isNetworkError = code === 0
    this.isTimeout = code === 408
  }
}

// 错误消息映射
const ERROR_MESSAGES: Record<number, string> = {
  0: '网络连接失败，请检查您的网络设置',
  400: '请求参数错误',
  401: '登录已过期，请重新登录',
  403: '没有权限访问此资源',
  404: '请求的资源不存在',
  408: '请求超时，请稍后重试',
  409: '资源冲突，请刷新后重试',
  422: '提交的数据验证失败',
  429: '请求过于频繁，请稍后再试',
  500: '服务器内部错误',
  502: '网关错误',
  503: '服务暂时不可用',
  504: '网关超时',
}

// 获取友好的错误消息
function getErrorMessage(error: AxiosError<{ message?: string; details?: Record<string, unknown> }>): string {
  // 优先使用后端返回的错误消息
  if (error.response?.data?.message) {
    return error.response.data.message
  }

  // 根据 HTTP 状态码返回对应消息
  const status = error.response?.status || 0
  return ERROR_MESSAGES[status] || `请求失败 (${status})`
}

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求重试配置
const MAX_RETRIES = 3
const RETRY_DELAY = 1000
const RETRYABLE_STATUS = [408, 429, 500, 502, 503, 504]

// 请求拦截器
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStr = localStorage.getItem('scholarforge-auth')
    if (authStr && config.headers) {
      const auth = JSON.parse(authStr)
      config.headers.Authorization = `Bearer ${auth.accessToken}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(new ApiError('请求发送失败', 0))
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 返回后端的完整响应 { code, message, data, timestamp }
    return response.data
  },
  async (error: AxiosError<{ message?: string; details?: Record<string, unknown> }>) => {
    const status = error.response?.status || 0
    const config = error.config

    // Token 过期处理
    if (status === 401) {
      localStorage.removeItem('scholarforge-auth')
      // 避免在登录页面重复跳转
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login?expired=1'
      }
      return Promise.reject(new ApiError('登录已过期', 401))
    }

    // 可重试的错误
    if (config && RETRYABLE_STATUS.includes(status)) {
      const retryCount = (config as unknown as { _retryCount?: number })._retryCount || 0
      if (retryCount < MAX_RETRIES) {
        (config as unknown as { _retryCount?: number })._retryCount = retryCount + 1
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * (retryCount + 1)))
        return apiClient.request(config)
      }
    }

    // 构造错误对象
    const apiError = new ApiError(
      getErrorMessage(error),
      status,
      error.response?.data?.details
    )

    // 开发环境下输出详细错误
    if (import.meta.env.DEV) {
      console.error('[API Error]', {
        url: config?.url,
        method: config?.method,
        status,
        message: apiError.message,
        details: apiError.details,
      })
    }

    return Promise.reject(apiError)
  }
)

// 导出 API 客户端
export default apiClient

// 封装请求方法 - 返回后端响应格式
export const request = {
  get: <T>(url: string, params?: Record<string, unknown>) =>
    apiClient.get<unknown, ApiResponse<T>>(url, { params }),

  post: <T>(url: string, data?: unknown) =>
    apiClient.post<unknown, ApiResponse<T>>(url, data),

  put: <T>(url: string, data?: unknown) =>
    apiClient.put<unknown, ApiResponse<T>>(url, data),

  patch: <T>(url: string, data?: unknown) =>
    apiClient.patch<unknown, ApiResponse<T>>(url, data),

  delete: <T>(url: string) =>
    apiClient.delete<unknown, ApiResponse<T>>(url),
}
