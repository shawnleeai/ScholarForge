/**
 * 推荐卡片组件
 * 展示推荐论文和反馈按钮
 */

import React, { useState } from 'react'
import {
  Card,
  Tag,
  Space,
  Typography,
  Button,
  Tooltip,
  message,
  Badge,
} from 'antd'
import {
  LikeOutlined,
  LikeFilled,
  DislikeOutlined,
  DislikeFilled,
  BookOutlined,
  FileTextOutlined,
  FireOutlined,
  EyeOutlined,
  ExportOutlined,
} from '@ant-design/icons'
import type { Article } from '@/types'
import type { RecommendationItem } from '@/services/recommendationService'

const { Text, Paragraph } = Typography

interface RecommendationCardProps {
  item?: RecommendationItem
  paper?: Partial<Article> & { id: string; title: string }
  onFeedback?: (paperId: string, feedback: 'like' | 'dislike') => void
  onView?: (paperId: string) => void
  onSave?: (paperId: string) => void
  compact?: boolean
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  item,
  paper,
  onFeedback,
  onView,
  onSave,
  compact = false,
}) => {
  const [liked, setLiked] = useState(false)
  const [disliked, setDisliked] = useState(false)

  // 支持两种数据格式
  const articleData = paper || item?.article
  const paperId = paper?.id || item?.article_id

  if (!articleData || !paperId) {
    return null
  }

  const handleLike = () => {
    setLiked(!liked)
    setDisliked(false)
    onFeedback?.(paperId, 'like')
    message.success(liked ? '已取消推荐' : '感谢您的反馈，将推荐更多相似文献')
  }

  const handleDislike = () => {
    setDisliked(!disliked)
    setLiked(false)
    onFeedback?.(paperId, 'dislike')
    message.success(disliked ? '已取消反馈' : '感谢您的反馈，将减少推荐此类文献')
  }

  const handleView = () => {
    onView?.(paperId)
  }

  const handleSave = () => {
    onSave?.(paperId)
    message.success('已保存到文献库')
  }

  // 计算分数等级
  const score = item?.score || 0.8
  const getScoreBadge = () => {
    if (score >= 0.9) return { color: '#f5222d', text: '强烈推荐' }
    if (score >= 0.8) return { color: '#fa8c16', text: '高度匹配' }
    if (score >= 0.7) return { color: '#1890ff', text: '可能相关' }
    return { color: '#8c8c8c', text: '相关' }
  }

  const scoreBadge = getScoreBadge()

  return (
    <Card
      size={compact ? 'small' : 'default'}
      className="recommendation-card"
      hoverable
      onClick={handleView}
      style={{ cursor: 'pointer', marginBottom: 8 }}
      actions={compact ? undefined : [
        <Tooltip title="查看详情" key="view">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              handleView()
            }}
          />
        </Tooltip>,
        <Tooltip title="保存到文献库" key="save">
          <Button
            type="text"
            icon={<BookOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              handleSave()
            }}
          />
        </Tooltip>,
        <Tooltip title="有用" key="like">
          <Button
            type="text"
            icon={liked ? <LikeFilled style={{ color: '#1890ff' }} /> : <LikeOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              handleLike()
            }}
          />
        </Tooltip>,
        <Tooltip title="不感兴趣" key="dislike">
          <Button
            type="text"
            icon={disliked ? <DislikeFilled style={{ color: '#ff4d4f' }} /> : <DislikeOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              handleDislike()
            }}
          />
        </Tooltip>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {/* 标题行 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Text strong style={{ flex: 1, marginRight: 8 }}>
            {articleData.title}
          </Text>
          {item && (
            <Badge
              count={scoreBadge.text}
              style={{ backgroundColor: scoreBadge.color, fontSize: 10 }}
            />
          )}
        </div>

        {/* 作者和来源 */}
        <Text type="secondary" style={{ fontSize: 12 }}>
          {articleData.authors?.map(a => typeof a === 'string' ? a : a.name).join(', ') || '未知作者'}
          {articleData.sourceName && ` · ${articleData.sourceName}`}
          {articleData.publicationYear && ` · ${articleData.publicationYear}`}
        </Text>

        {/* 摘要 */}
        {!compact && articleData.abstract && (
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{ marginBottom: 0, fontSize: 13, color: '#595959' }}
          >
            {articleData.abstract}
          </Paragraph>
        )}

        {/* 关键词 */}
        {!compact && articleData.keywords && articleData.keywords.length > 0 && (
          <Space size="small" wrap>
            {articleData.keywords.slice(0, 4).map((keyword, idx) => (
              <Tag key={idx} size="small" style={{ fontSize: 11 }}>
                {keyword}
              </Tag>
            ))}
          </Space>
        )}

        {/* 底部信息 */}
        <Space size="middle" style={{ marginTop: 4 }}>
          {articleData.citationCount !== undefined && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              <FireOutlined style={{ marginRight: 4 }} />
              被引 {articleData.citationCount} 次
            </Text>
          )}
          {item?.explanation && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              <FileTextOutlined style={{ marginRight: 4 }} />
              {item.explanation}
            </Text>
          )}
        </Space>
      </Space>
    </Card>
  )
}

export default RecommendationCard
