/**
 * 推荐列表组件
 * 展示个性化推荐论文列表
 */

import React, { useState, useEffect } from 'react'
import { Card, List, Spin, Empty, Button, Space, Typography, Segmented } from 'antd'
import { ReloadOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { RecommendationCard } from './RecommendationCard'
import { enhancedRecommendationService, type RecommendedPaper } from '@/services/recommendationService'

const { Text, Title } = Typography

interface RecommendationListProps {
  limit?: number
  showFilters?: boolean
}

export const RecommendationList: React.FC<RecommendationListProps> = ({
  limit = 10,
  showFilters = true,
}) => {
  const [recommendations, setRecommendations] = useState<RecommendedPaper[]>([])
  const [loading, setLoading] = useState(false)
  const [activeFilter, setActiveFilter] = useState<string>('all')
  const [refreshing, setRefreshing] = useState(false)

  const fetchRecommendations = async () => {
    setLoading(true)
    try {
      const data = await enhancedRecommendationService.getPersonalizedRecommendations(limit)
      setRecommendations(data)
    } catch (error) {
      console.error('获取推荐失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRecommendations()
  }, [limit])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchRecommendations()
    setRefreshing(false)
  }

  const handleFeedback = (paperId: string, feedback: 'like' | 'dislike') => {
    // 更新本地状态，优化UI
    setRecommendations(prev =>
      prev.map(paper =>
        paper.id === paperId
          ? { ...paper, userFeedback: feedback }
          : paper
      )
    )
  }

  const filteredRecommendations = recommendations.filter(paper => {
    if (activeFilter === 'all') return true
    return paper.recommendation_type === activeFilter
  })

  const filterOptions = [
    { label: '全部', value: 'all' },
    { label: '热门', value: 'trending' },
    { label: '最新', value: 'recent' },
    { label: '相关', value: 'related' },
  ]

  return (
    <Card
      title={
        <Space>
          <ThunderboltOutlined style={{ color: '#faad14' }} />
          <Title level={5} style={{ margin: 0 }}>为您推荐</Title>
        </Space>
      }
      extra={
        <Button
          icon={<ReloadOutlined spin={refreshing} />}
          onClick={handleRefresh}
          loading={refreshing}
          type="text"
        >
          刷新
        </Button>
      }
    >
      {showFilters && (
        <div style={{ marginBottom: 16 }}>
          <Segmented
            options={filterOptions}
            value={activeFilter}
            onChange={setActiveFilter}
            block
          />
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <Text type="secondary" style={{ display: 'block', marginTop: 16 }}>
            AI正在分析您的研究兴趣...
          </Text>
        </div>
      ) : filteredRecommendations.length === 0 ? (
        <Empty
          description="暂无推荐"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <List
          grid={{ gutter: 16, xs: 1, sm: 1, md: 1, lg: 1, xl: 1 }}
          dataSource={filteredRecommendations}
          renderItem={(paper) => (
            <List.Item>
              <RecommendationCard
                paper={paper}
                onFeedback={handleFeedback}
                onView={(p) => console.log('View paper:', p.id)}
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  )
}

export default RecommendationList
