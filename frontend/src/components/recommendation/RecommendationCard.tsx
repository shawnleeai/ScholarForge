/**
 * 推荐文献卡片组件
 */

import React from 'react'
import { Card, Space, Tag, Typography, Progress, Tooltip, Button } from 'antd'
import {
  StarOutlined,
  DownloadOutlined,
  EyeOutlined,
  FireOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons'

import type { RecommendationItem } from '@/services/recommendationService'

const { Text, Paragraph } = Typography

interface RecommendationCardProps {
  item: RecommendationItem
  onView?: (articleId: string) => void
  onSave?: (articleId: string) => void
  compact?: boolean
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({
  item,
  onView,
  onSave,
  compact = false,
}) => {
  const article = item.article
  const scores = item.scores

  // 获取最高分的维度
  const getTopScoreDimension = () => {
    if (!scores) return null
    const entries = Object.entries(scores)
    entries.sort((a, b) => b[1] - a[1])
    return entries[0]
  }

  const topDimension = getTopScoreDimension()

  const dimensionLabels: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
    relevance: { label: '相关度', icon: <StarOutlined />, color: '#1890ff' },
    timeliness: { label: '时效性', icon: <ClockCircleOutlined />, color: '#52c41a' },
    authority: { label: '权威性', icon: <TrophyOutlined />, color: '#722ed1' },
    practice: { label: '实用性', icon: <FireOutlined />, color: '#fa8c16' },
  }

  if (compact) {
    return (
      <Card
        size="small"
        className="recommendation-card-compact"
        hoverable
        onClick={() => onView?.(item.article_id)}
        styles={{
          body: { padding: '12px 16px' },
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <Paragraph
              ellipsis={{ rows: 1 }}
              style={{ margin: 0, fontWeight: 500 }}
            >
              {article?.title || `文献 ${item.article_id}`}
            </Paragraph>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {article?.sourceName} · {article?.publicationYear || '未知年份'}
            </Text>
          </div>
          <Tag color="blue">{Math.round(item.score * 100)}%</Tag>
        </div>
      </Card>
    )
  }

  return (
    <Card
      className="recommendation-card"
      hoverable
      styles={{
        body: { padding: 16 },
      }}
      actions={[
        <Tooltip key="view" title="查看详情">
          <Button type="text" icon={<EyeOutlined />} onClick={() => onView?.(item.article_id)}>
            查看
          </Button>
        </Tooltip>,
        <Tooltip key="save" title="保存到文献库">
          <Button type="text" icon={<DownloadOutlined />} onClick={() => onSave?.(item.article_id)}>
            保存
          </Button>
        </Tooltip>,
      ]}
    >
      {/* 标题和分数 */}
      <div style={{ marginBottom: 12 }}>
        <Paragraph
          ellipsis={{ rows: 2 }}
          style={{ margin: 0, fontSize: 16, fontWeight: 500 }}
        >
          {article?.title || `文献 ${item.article_id}`}
        </Paragraph>
      </div>

      {/* 作者和来源 */}
      <Space direction="vertical" size={4} style={{ marginBottom: 12 }}>
        {article?.authors && article.authors.length > 0 && (
          <Text type="secondary" style={{ fontSize: 13 }}>
            {article.authors.slice(0, 3).map(a => a.name).join(', ')}
            {article.authors.length > 3 && ' 等'}
          </Text>
        )}
        <Text type="secondary" style={{ fontSize: 12 }}>
          {article?.sourceName}
          {article?.publicationYear && ` · ${article.publicationYear}`}
          {article?.citationCount && ` · 被引 ${article.citationCount}`}
        </Text>
      </Space>

      {/* 推荐分数 */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <Text strong>推荐指数</Text>
          <Text style={{ color: '#1890ff', fontWeight: 600 }}>
            {Math.round(item.score * 100)}%
          </Text>
        </div>
        <Progress
          percent={item.score * 100}
          showInfo={false}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          size="small"
        />
      </div>

      {/* 维度分数 */}
      {scores && (
        <div style={{ marginBottom: 12 }}>
          <Space size={[4, 8]} wrap>
            {Object.entries(scores).slice(0, 3).map(([key, value]) => {
              const dim = dimensionLabels[key]
              if (!dim) return null
              return (
                <Tooltip key={key} title={`${dim.label}: ${Math.round(value * 100)}%`}>
                  <Tag
                    icon={dim.icon}
                    color={value > 0.7 ? dim.color : 'default'}
                    style={{ margin: 0 }}
                  >
                    {dim.label} {Math.round(value * 100)}
                  </Tag>
                </Tooltip>
              )
            })}
          </Space>
        </div>
      )}

      {/* 推荐理由 */}
      <div
        style={{
          background: '#f6f8fa',
          padding: '8px 12px',
          borderRadius: 6,
          fontSize: 12,
        }}
      >
        <Text type="secondary">
          {topDimension && dimensionLabels[topDimension[0]]?.icon} {item.explanation}
        </Text>
      </div>

      {/* 关键词 */}
      {article?.keywords && article.keywords.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <Space size={[4, 8]} wrap>
            {article.keywords.slice(0, 5).map((kw, idx) => (
              <Tag key={idx} style={{ margin: 0, fontSize: 11 }}>
                {kw}
              </Tag>
            ))}
          </Space>
        </div>
      )}
    </Card>
  )
}

export default RecommendationCard
