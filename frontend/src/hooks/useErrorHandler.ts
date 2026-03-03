/**
 * 全局错误处理 Hook
 * 统一处理 API 错误和全局异常
 */

import { useCallback } from 'react'
import { message, notification } from 'antd'
import { ApiError } from '@/services/api'

export interface UseErrorHandlerOptions {
  /** 是否显示错误通知 */
  showNotification?: boolean
  /** 自定义错误处理 */
  onError?: (error: Error) => void
}

export function useErrorHandler(options: UseErrorHandlerOptions = {}) {
  const { showNotification = true, onError } = options

  const handleError = useCallback((error: unknown, fallbackMessage?: string) => {
    // 转换为 Error 对象
    const err = error instanceof Error ? error : new Error(String(error))

    // 调用自定义错误处理
    onError?.(err)

    // 显示错误通知
    if (showNotification) {
      if (err instanceof ApiError) {
        // API 错误
        if (err.code === 401) {
          // 401 错误已在拦截器中处理，这里不再重复提示
          return
        }

        if (err.isNetworkError) {
          notification.error({
            message: '网络错误',
            description: '无法连接到服务器，请检查您的网络连接',
            duration: 5,
          })
        } else if (err.isTimeout) {
          notification.warning({
            message: '请求超时',
            description: '服务器响应时间过长，请稍后重试',
            duration: 5,
          })
        } else {
          message.error(err.message || fallbackMessage || '操作失败')
        }
      } else {
        // 其他错误
        notification.error({
          message: '发生错误',
          description: err.message || fallbackMessage || '未知错误',
          duration: 5,
        })
      }
    }

    // 开发环境打印错误堆栈
    if (import.meta.env.DEV) {
      console.error('[Error Handler]', err)
    }
  }, [showNotification, onError])

  const handleAsyncError = useCallback(async <T,>(
    promise: Promise<T>,
    fallbackMessage?: string
  ): Promise<[T | null, Error | null]> => {
    try {
      const data = await promise
      return [data, null]
    } catch (error) {
      handleError(error, fallbackMessage)
      return [null, error instanceof Error ? error : new Error(String(error))]
    }
  }, [handleError])

  return {
    handleError,
    handleAsyncError,
  }
}

/**
 * 全局未捕获错误处理
 * 在应用入口调用
 */
export function setupGlobalErrorHandler() {
  // 处理未捕获的 Promise rejection
  window.addEventListener('unhandledrejection', (event) => {
    console.error('[Unhandled Rejection]', event.reason)

    // 避免重复处理 API 错误（已在拦截器中处理）
    if (event.reason instanceof ApiError) {
      event.preventDefault()
      return
    }

    notification.error({
      message: '程序错误',
      description: '发生了一个未预期的错误，请刷新页面重试',
      duration: 5,
    })
  })

  // 处理全局 JavaScript 错误
  window.addEventListener('error', (event) => {
    console.error('[Global Error]', event.error)

    // 忽略资源加载错误
    if (event.target !== window) {
      return
    }

    notification.error({
      message: '程序错误',
      description: '发生了一个未预期的错误，请刷新页面重试',
      duration: 5,
    })
  })
}

export default useErrorHandler
