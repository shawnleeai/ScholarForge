/**
 * 每日推荐面板组件
 */

import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, List, Spin, Empty, Typography, Space, Button, message } from 'antd'
import { ReloadOutlined, BulbOutlined } from '@ant-design/icons'

import { recommendationService } from '@/services'
import RecommendationCard from './RecommendationCard'
import type { RecommendationItem } from '@/services/recommendationService'

const { Text } = Typography

interface DailyRecommendationsProps {
  limit?: number
  compact?: boolean
  onViewArticle?: (articleId: string) => void
  onSaveArticle?: (articleId: string) => void
}

const DailyRecommendations: React.FC<DailyRecommendationsProps> = ({
  limit = 5,
  compact = false,
  onViewArticle,
  onSaveArticle,
}) => {
  const {
    data,
    isLoading,
    isError,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['dailyRecommendations', limit],
    queryFn: () => recommendationService.getDailyRecommendations(limit),
    staleTime: 5 * 60 * 1000, // 5 分钟内不重新请求
  })

  const handleViewArticle = (articleId: string) => {
    // 记录查看行为
    recommendationService.recordBehavior(articleId, 'view')
    onViewArticle?.(articleId)
  }

  const handleSaveArticle = async (articleId: string) => {
    try {
      await recommendationService.recordBehavior(articleId, 'save')
      message.success('已保存到文献库')
      onSaveArticle?.(articleId)
    } catch {
      message.error('保存失败')
    }
  }

  const recommendations = data?.data || []

  if (isLoading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin />
          <Text type="secondary" style={{ display: 'block', marginTop: 12 }}>
            正在为您生成个性化推荐...
          </Text>
        </div>
      </Card>
    )
  }

  if (isError) {
    return (
      <Card>
        <Empty
          description="获取推荐失败"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            重试
          </Button>
        </Empty>
      </Card>
    )
  }

  if (recommendations.length === 0) {
    return (
      <Card>
        <Empty
          description="暂无推荐"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    )
  }

  return (
    <Card
      title={
        <Space>
          <BulbOutlined style={{ color: '#faad14' }} />
          <span>今日推荐</span>
        </Space>
      }
      extra={
        <Button
          type="text"
          icon={<ReloadOutlined spin={isFetching} />}
          onClick={() => refetch()}
          loading={isFetching}
        >
          刷新
        </Button>
      }
    >
      <List
        dataSource={recommendations}
        renderItem={(item: RecommendationItem) => (
          <List.Item style={{ border: 'none', padding: '8px 0' }}>
            <RecommendationCard
              item={item}
              onView={handleViewArticle}
              onSave={handleSaveArticle}
              compact={compact}
            />
          </List.Item>
        )}
      />
    </Card>
  )
}

export default DailyRecommendations
