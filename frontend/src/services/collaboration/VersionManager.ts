/**
 * 版本历史管理器
 * 管理文档版本历史、快照和回滚
 */

import * as Y from 'yjs'
import { IndexeddbPersistence } from 'y-indexeddb'
import dayjs from 'dayjs'

export interface VersionInfo {
  id: string
  timestamp: number
  author: string
  authorId: string
  message: string
  snapshot: Uint8Array
  diff?: VersionDiff
}

export interface VersionDiff {
  added: number
  removed: number
  modified: number
}

export interface VersionCompareResult {
  oldVersion: VersionInfo
  newVersion: VersionInfo
  changes: Array<{
    type: 'add' | 'remove' | 'modify'
    position: number
    content?: string
  }>
}

/**
 * 版本历史管理器
 */
export class VersionManager {
  private ydoc: Y.Doc
  private versionsDb: IndexeddbPersistence | null = null
  private versions: Y.Array<any> | null = null

  constructor(ydoc: Y.Doc, dbName: string = 'versions') {
    this.ydoc = ydoc
    this.versions = ydoc.getArray('versions')

    // 创建独立的IndexedDB用于版本历史
    this.versionsDb = new IndexeddbPersistence(`${dbName}-versions`, ydoc)
  }

  /**
   * 创建新版本快照
   */
  createVersion(
    author: string,
    authorId: string,
    message: string = ''
  ): VersionInfo {
    const snapshot = Y.encodeStateAsUpdate(this.ydoc)
    const version: VersionInfo = {
      id: `v_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      author,
      authorId,
      message,
      snapshot,
    }

    // 计算与上一个版本的差异
    const prevVersion = this.getLatestVersion()
    if (prevVersion) {
      version.diff = this.calculateDiff(prevVersion.snapshot, snapshot)
    }

    // 添加到版本历史
    this.versions?.push([version])

    return version
  }

  /**
   * 获取所有版本
   */
  getVersions(): VersionInfo[] {
    return (this.versions?.toArray() as VersionInfo[]) || []
  }

  /**
   * 获取最新版本
   */
  getLatestVersion(): VersionInfo | null {
    const versions = this.getVersions()
    return versions.length > 0 ? versions[versions.length - 1] : null
  }

  /**
   * 获取指定版本
   */
  getVersion(versionId: string): VersionInfo | null {
    const versions = this.getVersions()
    return versions.find((v) => v.id === versionId) || null
  }

  /**
   * 恢复到指定版本
   */
  async restoreVersion(versionId: string): Promise<boolean> {
    const version = this.getVersion(versionId)
    if (!version) return false

    // 先创建当前版本的备份
    this.createVersion('System', 'system', `Backup before restoring to ${versionId}`)

    // 应用快照
    Y.applyUpdate(this.ydoc, version.snapshot)

    return true
  }

  /**
   * 比较两个版本
   */
  compareVersions(
    oldVersionId: string,
    newVersionId: string
  ): VersionCompareResult | null {
    const oldVersion = this.getVersion(oldVersionId)
    const newVersion = this.getVersion(newVersionId)

    if (!oldVersion || !newVersion) return null

    // 创建临时文档进行比较
    const oldDoc = new Y.Doc()
    Y.applyUpdate(oldDoc, oldVersion.snapshot)

    const newDoc = new Y.Doc()
    Y.applyUpdate(newDoc, newVersion.snapshot)

    // 获取文本内容进行比较
    const oldText = oldDoc.getText('content').toString()
    const newText = newDoc.getText('content').toString()

    // 计算差异
    const changes = this.computeTextDiff(oldText, newText)

    return {
      oldVersion,
      newVersion,
      changes,
    }
  }

  /**
   * 计算文本差异（简化版）
   */
  private computeTextDiff(
    oldText: string,
    newText: string
  ): Array<{ type: 'add' | 'remove' | 'modify'; position: number; content?: string }> {
    const changes: Array<{ type: 'add' | 'remove' | 'modify'; position: number; content?: string }> = []

    // 简化的行级比较
    const oldLines = oldText.split('\n')
    const newLines = newText.split('\n')

    let oldIndex = 0
    let newIndex = 0

    while (oldIndex < oldLines.length || newIndex < newLines.length) {
      const oldLine = oldLines[oldIndex]
      const newLine = newLines[newIndex]

      if (oldLine === newLine) {
        oldIndex++
        newIndex++
      } else if (oldIndex < oldLines.length && !newLines.slice(newIndex).includes(oldLine)) {
        changes.push({
          type: 'remove',
          position: oldIndex,
          content: oldLine,
        })
        oldIndex++
      } else if (newIndex < newLines.length && !oldLines.slice(oldIndex).includes(newLine)) {
        changes.push({
          type: 'add',
          position: newIndex,
          content: newLine,
        })
        newIndex++
      } else {
        // 修改
        changes.push({
          type: 'modify',
          position: newIndex,
          content: newLine,
        })
        oldIndex++
        newIndex++
      }
    }

    return changes
  }

  /**
   * 计算两个快照的差异统计
   */
  private calculateDiff(
    oldSnapshot: Uint8Array,
    newSnapshot: Uint8Array
  ): VersionDiff {
    const oldDoc = new Y.Doc()
    Y.applyUpdate(oldDoc, oldSnapshot)

    const newDoc = new Y.Doc()
    Y.applyUpdate(newDoc, newSnapshot)

    const oldText = oldDoc.getText('content').toString()
    const newText = newDoc.getText('content').toString()

    // 统计增删改
    const oldLength = oldText.length
    const newLength = newText.length

    return {
      added: Math.max(0, newLength - oldLength),
      removed: Math.max(0, oldLength - newLength),
      modified: Math.min(oldLength, newLength),
    }
  }

  /**
   * 导出版本历史
   */
  exportVersions(): string {
    const versions = this.getVersions()
    return JSON.stringify(
      versions.map((v) => ({
        ...v,
        snapshot: Array.from(v.snapshot),
      })),
      null,
      2
    )
  }

  /**
   * 导入版本历史
   */
  importVersions(json: string): boolean {
    try {
      const versions = JSON.parse(json)
      this.versions?.delete(0, this.versions.length)
      versions.forEach((v: any) => {
        v.snapshot = new Uint8Array(v.snapshot)
        this.versions?.push([v])
      })
      return true
    } catch (e) {
      console.error('Failed to import versions:', e)
      return false
    }
  }

  /**
   * 清理旧版本（保留最近N个）
   */
  cleanupOldVersions(keepCount: number = 50): number {
    const versions = this.getVersions()
    if (versions.length <= keepCount) return 0

    const toRemove = versions.length - keepCount
    this.versions?.delete(0, toRemove)
    return toRemove
  }

  /**
   * 按日期范围查询版本
   */
  getVersionsByDateRange(startDate: Date, endDate: Date): VersionInfo[] {
    const versions = this.getVersions()
    return versions.filter((v) => {
      const timestamp = v.timestamp
      return timestamp >= startDate.getTime() && timestamp <= endDate.getTime()
    })
  }

  /**
   * 获取版本统计信息
   */
  getStats(): {
    totalVersions: number
    totalAuthors: number
    firstVersionDate: Date | null
    lastVersionDate: Date | null
  } {
    const versions = this.getVersions()
    const authors = new Set(versions.map((v) => v.authorId))

    return {
      totalVersions: versions.length,
      totalAuthors: authors.size,
      firstVersionDate: versions.length > 0 ? new Date(versions[0].timestamp) : null,
      lastVersionDate:
        versions.length > 0 ? new Date(versions[versions.length - 1].timestamp) : null,
    }
  }

  /**
   * 销毁管理器
   */
  destroy(): void {
    if (this.versionsDb) {
      this.versionsDb.destroy()
      this.versionsDb = null
    }
  }
}

/**
 * 格式化版本时间
 */
export function formatVersionTime(timestamp: number): string {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(timestamp: number): string {
  return dayjs(timestamp).fromNow()
}

export default VersionManager
