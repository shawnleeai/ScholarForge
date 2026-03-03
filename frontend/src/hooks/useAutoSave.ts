/**
 * 自动保存 Hook
 * 提供优化的自动保存功能，包括防抖、本地备份和重试机制
 */

import { useEffect, useRef, useCallback, useState } from 'react'
import { debounce } from 'lodash'

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'

interface UseAutoSaveOptions {
  /** 保存函数 */
  onSave: () => Promise<void>
  /** 防抖延迟时间（毫秒） */
  debounceMs?: number
  /** 是否启用本地备份 */
  enableLocalBackup?: boolean
  /** 本地备份的 key */
  backupKey?: string
  /** 最大重试次数 */
  maxRetries?: number
  /** 重试延迟（毫秒） */
  retryDelay?: number
}

interface UseAutoSaveReturn {
  /** 当前保存状态 */
  status: SaveStatus
  /** 最后保存时间 */
  lastSavedAt: Date | null
  /** 是否有未保存的更改 */
  hasUnsavedChanges: boolean
  /** 手动触发保存 */
  save: () => Promise<void>
  /** 标记有未保存的更改 */
  markDirty: () => void
  /** 从本地备份恢复 */
  restoreFromBackup: () => string | null
  /** 清除本地备份 */
  clearBackup: () => void
  /** 保存错误信息 */
  error: Error | null
}

export function useAutoSave({
  onSave,
  debounceMs = 2000,
  enableLocalBackup = true,
  backupKey,
  maxRetries = 3,
  retryDelay = 1000,
}: UseAutoSaveOptions): UseAutoSaveReturn {
  const [status, setStatus] = useState<SaveStatus>('idle')
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const retryCountRef = useRef(0)
  const isSavingRef = useRef(false)

  // 实际执行保存的函数
  const performSave = useCallback(async () => {
    if (isSavingRef.current) return

    isSavingRef.current = true
    setStatus('saving')
    setError(null)

    try {
      await onSave()
      setStatus('saved')
      setLastSavedAt(new Date())
      setHasUnsavedChanges(false)
      retryCountRef.current = 0

      // 清除本地备份
      if (enableLocalBackup && backupKey) {
        localStorage.removeItem(backupKey)
      }

      // 3秒后恢复 idle 状态
      setTimeout(() => {
        if (status === 'saved') {
          setStatus('idle')
        }
      }, 3000)
    } catch (err) {
      const saveError = err instanceof Error ? err : new Error('保存失败')
      setError(saveError)
      setStatus('error')

      // 重试逻辑
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current++
        setTimeout(() => {
          setStatus('idle')
          performSave()
        }, retryDelay * retryCountRef.current)
      }
    } finally {
      isSavingRef.current = false
    }
  }, [onSave, enableLocalBackup, backupKey, maxRetries, retryDelay, status])

  // 防抖保存函数
  const debouncedSave = useRef(
    debounce(performSave, debounceMs, { leading: false, trailing: true })
  ).current

  // 清理防抖函数
  useEffect(() => {
    return () => {
      debouncedSave.cancel()
    }
  }, [debouncedSave])

  // 触发保存
  const save = useCallback(async () => {
    debouncedSave.cancel()
    await performSave()
  }, [debouncedSave, performSave])

  // 标记有未保存的更改
  const markDirty = useCallback(() => {
    setHasUnsavedChanges(true)
    debouncedSave()
  }, [debouncedSave])

  // 保存到本地备份（供外部使用）
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const saveToBackup = useCallback((content: string) => {
    if (enableLocalBackup && backupKey) {
      localStorage.setItem(backupKey, JSON.stringify({
        content,
        savedAt: new Date().toISOString(),
      }))
    }
  }, [enableLocalBackup, backupKey])

  // 从本地备份恢复
  const restoreFromBackup = useCallback((): string | null => {
    if (!enableLocalBackup || !backupKey) return null

    const backup = localStorage.getItem(backupKey)
    if (!backup) return null

    try {
      const { content } = JSON.parse(backup)
      return content
    } catch {
      return null
    }
  }, [enableLocalBackup, backupKey])

  // 清除本地备份
  const clearBackup = useCallback(() => {
    if (backupKey) {
      localStorage.removeItem(backupKey)
    }
  }, [backupKey])

  // 组件卸载时保存
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      if (hasUnsavedChanges) {
        debouncedSave.flush()
      }
    }
  }, [hasUnsavedChanges, debouncedSave])

  return {
    status,
    lastSavedAt,
    hasUnsavedChanges,
    save,
    markDirty,
    restoreFromBackup,
    clearBackup,
    error,
  }
}

export default useAutoSave
