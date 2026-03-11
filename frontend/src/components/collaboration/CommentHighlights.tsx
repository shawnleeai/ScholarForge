/**
 * 评论高亮组件
 * 在编辑器中高亮显示带有评论的文本段落
 */

import React, { useMemo } from 'react'
import { Tooltip, Badge } from 'antd'
import { CommentOutlined, CheckCircleFilled } from '@ant-design/icons'
import type { Comment } from '../../services/collaboration/CommentManager'
import styles from './Collaboration.module.css'

interface CommentHighlightsProps {
  comments: Comment[]
  text: string
  highlightedCommentId?: string | null
  onCommentClick?: (comment: Comment) => void
}

interface HighlightSegment {
  from: number
  to: number
  type: 'normal' | 'comment'
  comment?: Comment
}

export const CommentHighlights: React.FC<CommentHighlightsProps> = ({
  comments,
  text,
  highlightedCommentId,
  onCommentClick,
}) => {
  // 计算高亮段落
  const segments = useMemo(() => {
    // 按位置排序评论
    const sortedComments = [...comments]
      .filter((c) => c.status !== 'resolved') // 可选：隐藏已解决的评论高亮
      .sort((a, b) => a.position.from - b.position.from)

    const segs: HighlightSegment[] = []
    let lastPos = 0

    for (const comment of sortedComments) {
      // 添加评论前的正常文本
      if (comment.position.from > lastPos) {
        segs.push({
          from: lastPos,
          to: comment.position.from,
          type: 'normal',
        })
      }

      // 添加评论段落
      segs.push({
        from: comment.position.from,
        to: comment.position.to,
        type: 'comment',
        comment,
      })

      lastPos = Math.max(lastPos, comment.position.to)
    }

    // 添加剩余文本
    if (lastPos < text.length) {
      segs.push({
        from: lastPos,
        to: text.length,
        type: 'normal',
      })
    }

    return segs
  }, [comments, text])

  // 按优先级选择评论颜色
  const getCommentColor = (comment: Comment, isHighlighted: boolean): string => {
    if (isHighlighted) return '#ff4d4f'
    if (comment.status === 'resolved') return '#52c41a'
    return comment.author.color || '#faad14'
  }

  return (
    <>
      {segments.map((segment, index) => {
        const segmentText = text.slice(segment.from, segment.to)

        if (segment.type === 'normal') {
          return <span key={index}>{segmentText}</span>
        }

        const comment = segment.comment!
        const isHighlighted = highlightedCommentId === comment.id
        const color = getCommentColor(comment, isHighlighted)

        return (
          <Tooltip
            key={index}
            title={
              <div style={{ maxWidth: 300 }}>
                <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                  {comment.status === 'resolved' ? (
                    <CheckCircleFilled style={{ color: '#52c41a', marginRight: 4 }} />
                  ) : (
                    <CommentOutlined style={{ marginRight: 4 }} />
                  )}
                  {comment.author.name} 的评论
                </div>
                <div style={{
                  background: 'rgba(255,255,255,0.1)',
                  padding: 8,
                  borderRadius: 4,
                  marginBottom: 4
                }}>
                  {comment.content.slice(0, 100)}
                  {comment.content.length > 100 ? '...' : ''}
                </div>
                {comment.replies.length > 0 && (
                  <div style={{ fontSize: 12, opacity: 0.8 }}>
                    {comment.replies.length} 条回复
                  </div>
                )}
              </div>
            }
          >
            <span
              className={`${styles.commentHighlight} ${
                isHighlighted ? styles.highlighted : ''
              }`}
              style={{
                backgroundColor: `${color}33`, // 20% opacity
                borderBottom: `3px solid ${color}`,
                cursor: 'pointer',
                transition: 'all 0.2s',
                padding: '2px 0',
                borderRadius: '2px',
              }}
              onClick={() => onCommentClick?.(comment)}
            >
              {segmentText}
              <Badge
                count={comment.replies.length + 1}
                size="small"
                style={{
                  backgroundColor: color,
                  marginLeft: 4,
                  fontSize: 10,
                }}
              />
            </span>
          </Tooltip>
        )
      })}
    </>
  )
}

/**
 * 评论标记（侧边显示）
 * 在文档边缘显示评论标记点
 */
interface CommentMarkersProps {
  comments: Comment[]
  containerHeight: number
  textLength: number
  onMarkerClick?: (comment: Comment) => void
}

export const CommentMarkers: React.FC<CommentMarkersProps> = ({
  comments,
  containerHeight,
  textLength,
  onMarkerClick,
}) => {
  // 计算每个评论标记的位置
  const markers = useMemo(() => {
    return comments.map((comment) => {
      // 计算评论在文本中的相对位置（0-1）
      const relativePos = comment.position.from / (textLength || 1)
      // 转换为像素位置
      const top = relativePos * containerHeight

      return {
        comment,
        top: Math.min(top, containerHeight - 20),
        color: comment.author.color || '#1890ff',
      }
    })
  }, [comments, containerHeight, textLength])

  return (
    <div
      style={{
        position: 'absolute',
        right: 0,
        top: 0,
        width: 24,
        height: containerHeight,
        pointerEvents: 'none',
      }}
    >
      {markers.map(({ comment, top, color }) => (
        <Tooltip
          key={comment.id}
          title={`${comment.author.name}: ${comment.content.slice(0, 30)}...`}
          placement="right"
        >
          <div
            style={{
              position: 'absolute',
              top,
              right: 4,
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: color,
              cursor: 'pointer',
              pointerEvents: 'auto',
              border: '2px solid white',
              boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
              transition: 'transform 0.2s',
            }}
            onClick={() => onMarkerClick?.(comment)}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.3)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)'
            }}
          />
        </Tooltip>
      ))}
    </div>
  )
}

export default CommentHighlights
