/**
 * Awareness光标组件
 * 显示协作者的光标位置和选区
 */

import React, { useEffect, useState, useCallback } from 'react'
import { awarenessProtocol } from 'y-protocols/awareness'
import { Tooltip } from 'antd'
import styles from './Collaboration.module.css'

interface CursorPosition {
  index: number
  length: number
}

interface AwarenessState {
  user?: {
    id: string
    name: string
    color: string
    avatar?: string
  }
  cursor?: CursorPosition
  selection?: CursorPosition
}

interface AwarenessCursorsProps {
  awareness: awarenessProtocol.Awareness | null
  editorRef: React.RefObject<HTMLDivElement>
}

interface CursorInfo {
  clientId: number
  user: {
    id: string
    name: string
    color: string
    avatar?: string
  }
  position: { top: number; left: number }
  selection?: CursorPosition
}

export const AwarenessCursors: React.FC<AwarenessCursorsProps> = ({
  awareness,
  editorRef,
}) => {
  const [cursors, setCursors] = useState<CursorInfo[]>([])

  /**
   * 计算光标在编辑器中的位置
   */
  const calculateCursorPosition = useCallback(
    (index: number): { top: number; left: number } | null => {
      const editor = editorRef.current
      if (!editor) return null

      // 获取编辑器中的所有文本节点
      const walker = document.createTreeWalker(
        editor,
        NodeFilter.SHOW_TEXT,
        null,
        false
      )

      let currentIndex = 0
      let node: Node | null

      while ((node = walker.nextNode())) {
        const textNode = node as Text
        const textLength = textNode.textContent?.length || 0

        if (currentIndex + textLength >= index) {
          // 找到对应的文本节点
          const offset = index - currentIndex
          const range = document.createRange()
          range.setStart(textNode, Math.min(offset, textLength))
          range.setEnd(textNode, Math.min(offset, textLength))

          const rect = range.getBoundingClientRect()
          const editorRect = editor.getBoundingClientRect()

          return {
            top: rect.top - editorRect.top + editor.scrollTop,
            left: rect.left - editorRect.left,
          }
        }

        currentIndex += textLength
      }

      return null
    },
    [editorRef]
  )

  /**
   * 更新光标位置
   */
  const updateCursors = useCallback(() => {
    if (!awareness) {
      setCursors([])
      return
    }

    const states = awareness.getStates()
    const localClientId = awareness.clientID
    const newCursors: CursorInfo[] = []

    states.forEach((state: AwarenessState, clientId: number) => {
      // 跳过本地用户
      if (clientId === localClientId) return

      if (state.user && state.cursor) {
        const position = calculateCursorPosition(state.cursor.index)

        if (position) {
          newCursors.push({
            clientId,
            user: state.user,
            position,
            selection: state.selection,
          })
        }
      }
    })

    setCursors(newCursors)
  }, [awareness, calculateCursorPosition])

  // 监听awareness变化
  useEffect(() => {
    if (!awareness) return

    awareness.on('change', updateCursors)

    // 初始更新
    updateCursors()

    // 监听编辑器滚动，更新光标位置
    const editor = editorRef.current
    const handleScroll = () => {
      updateCursors()
    }

    editor?.addEventListener('scroll', handleScroll)

    return () => {
      awareness.off('change', updateCursors)
      editor?.removeEventListener('scroll', handleScroll)
    }
  }, [awareness, updateCursors, editorRef])

  // 定期更新光标位置（处理编辑器内容变化）
  useEffect(() => {
    const interval = setInterval(() => {
      updateCursors()
    }, 100)

    return () => clearInterval(interval)
  }, [updateCursors])

  return (
    <>
      {cursors.map((cursor) => (
        <Tooltip
          key={cursor.clientId}
          title={cursor.user.name}
          placement="top"
        >
          <div
            className={styles.awarenessCursor}
            style={{
              position: 'absolute',
              top: cursor.position.top,
              left: cursor.position.left,
              pointerEvents: 'none',
              zIndex: 1000,
            }}
          >
            {/* 光标竖线 */}
            <div
              className={styles.cursorCaret}
              style={{
                width: '2px',
                height: '1.2em',
                backgroundColor: cursor.user.color,
              }}
            />

            {/* 用户名标签 */}
            <div
              className={styles.cursorLabel}
              style={{
                position: 'absolute',
                top: '-1.5em',
                left: 0,
                backgroundColor: cursor.user.color,
                color: '#fff',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '12px',
                whiteSpace: 'nowrap',
              }}
            >
              {cursor.user.name}
            </div>

            {/* 选区高亮 */}
            {cursor.selection && cursor.selection.length > 0 && (
              <SelectionHighlight
                start={cursor.selection.index}
                length={cursor.selection.length}
                color={cursor.user.color}
                editorRef={editorRef}
              />
            )}
          </div>
        </Tooltip>
      ))}
    </>
  )
}

/**
 * 选区高亮组件
 */
interface SelectionHighlightProps {
  start: number
  length: number
  color: string
  editorRef: React.RefObject<HTMLDivElement>
}

const SelectionHighlight: React.FC<SelectionHighlightProps> = ({
  start,
  length,
  color,
  editorRef,
}) => {
  const [rects, setRects] = useState<DOMRect[]>([])

  useEffect(() => {
    const editor = editorRef.current
    if (!editor || length <= 0) return

    // 创建选区
    const range = document.createRange()
    const walker = document.createTreeWalker(
      editor,
      NodeFilter.SHOW_TEXT,
      null,
      false
    )

    let currentIndex = 0
    let startNode: Node | null = null
    let startOffset = 0
    let endNode: Node | null = null
    let endOffset = 0

    let node: Node | null
    while ((node = walker.nextNode())) {
      const textNode = node as Text
      const textLength = textNode.textContent?.length || 0

      if (!startNode && currentIndex + textLength > start) {
        startNode = textNode
        startOffset = start - currentIndex
      }

      if (!endNode && currentIndex + textLength >= start + length) {
        endNode = textNode
        endOffset = start + length - currentIndex
        break
      }

      currentIndex += textLength
    }

    if (startNode && endNode) {
      try {
        range.setStart(startNode, startOffset)
        range.setEnd(endNode, endOffset)
        const clientRects = range.getClientRects()
        setRects(Array.from(clientRects))
      } catch (e) {
        console.error('Failed to create selection range:', e)
      }
    }
  }, [start, length, editorRef])

  const editor = editorRef.current
  if (!editor) return null

  const editorRect = editor.getBoundingClientRect()

  return (
    <>
      {rects.map((rect, index) => (
        <div
          key={index}
          style={{
            position: 'absolute',
            top: rect.top - editorRect.top + editor.scrollTop,
            left: rect.left - editorRect.left,
            width: rect.width,
            height: rect.height,
            backgroundColor: `${color}33`, // 20% opacity
            pointerEvents: 'none',
          }}
        />
      ))}
    </>
  )
}

/**
 * Awareness用户列表
 */
interface AwarenessUserListProps {
  awareness: awarenessProtocol.Awareness | null
}

export const AwarenessUserList: React.FC<AwarenessUserListProps> = ({
  awareness,
}) => {
  const [users, setUsers] = useState<
    Array<{
      clientId: number
      user: {
        id: string
        name: string
        color: string
        avatar?: string
      }
    }>
  >([])

  useEffect(() => {
    if (!awareness) return

    const updateUsers = () => {
      const states = awareness.getStates()
      const localClientId = awareness.clientID
      const newUsers: Array<{
        clientId: number
        user: {
          id: string
          name: string
          color: string
          avatar?: string
        }
      }> = []

      states.forEach((state: AwarenessState, clientId: number) => {
        if (state.user && clientId !== localClientId) {
          newUsers.push({
            clientId,
            user: state.user,
          })
        }
      })

      setUsers(newUsers)
    }

    awareness.on('change', updateUsers)
    updateUsers()

    return () => {
      awareness.off('change', updateUsers)
    }
  }, [awareness])

  if (users.length === 0) {
    return null
  }

  return (
    <div className={styles.awarenessUserList}>
      {users.map(({ clientId, user }) => (
        <div key={clientId} className={styles.awarenessUser}>
          <div
            className={styles.userIndicator}
            style={{ backgroundColor: user.color }}
          />
          <span className={styles.userName}>{user.name}</span>
        </div>
      ))}
    </div>
  )
}

/**
 * 更新本地光标位置的Hook
 */
export function useAwarenessCursor(
  awareness: awarenessProtocol.Awareness | null
) {
  /**
   * 更新光标位置
   */
  const updateCursor = useCallback(
    (index: number, length: number = 0) => {
      if (!awareness) return

      awareness.setLocalStateField('cursor', { index, length })
    },
    [awareness]
  )

  /**
   * 更新选区
   */
  const updateSelection = useCallback(
    (index: number, length: number) => {
      if (!awareness) return

      awareness.setLocalStateField('selection', { index, length })
    },
    [awareness]
  )

  /**
   * 清除光标
   */
  const clearCursor = useCallback(() => {
    if (!awareness) return

    const state = awareness.getLocalState()
    if (state) {
      delete (state as AwarenessState).cursor
      delete (state as AwarenessState).selection
      awareness.setLocalState(state)
    }
  }, [awareness])

  return { updateCursor, updateSelection, clearCursor }
}

export default AwarenessCursors
