/**
 * 推荐面板组件
 */

import React, { useState } from 'react'
import { Card, List, Avatar, Tag, Button, Space, Empty, Spin, Tabs } from 'antd'
import {
  FileTextOutlined,
  PlusOutlined,
  FireOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { recommendationService } from '@/services/recommendationService'
import { articleService } from '@/services/articleService'
import { message } from 'antd'
import styles from './Recommendation.module.css'

const RecommendationPanel: React.FC = () => {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('daily')

  // 获取每日推荐
  const { data: dailyData, isLoading: dailyLoading } = useQuery({
    queryKey: ['recommendations', 'daily'],
    queryFn: async () => {
      const res = await recommendationService.getDailyRecommendations(5)
      return res.data || []
    },
  })

  // 获取热门文献
  const { data: trendingData, isLoading: trendingLoading } = useQuery({
    queryKey: ['recommendations', 'trending'],
    queryFn: async () => {
      const res = await recommendationService.getTrendingArticles(7, 5)
      return res.data || []
    },
  })

  // 添加到文献库
  const addToLibraryMutation = useMutation({
    mutationFn: (articleId: string) =>
      articleService.addToLibrary({ articleId }),
    onSuccess: () => {
      message.success('已添加到文献库')
      queryClient.invalidateQueries({ queryKey: ['library'] })
    },
  })

  const handleAddToLibrary = (articleId: string) => {
    addToLibraryMutation.mutate(articleId)
  }

  const renderDailyList = () => {
    if (dailyLoading) return <Spin />
    const items = dailyData || []

    if (items.length === 0) return <Empty description="暂无推荐" />

    return (
      <List
        dataSource={items}
        renderItem={(item: any) => (
          <List.Item className={styles.item}>
            <List.Item.Meta
              avatar={
                <Avatar
                  shape="square"
                  size={48}
                  style={{ backgroundColor: '#f0f5ff' }}
                  icon={<FileTextOutlined style={{ color: '#1890ff' }} />}
                />
              }
              title={<div className={styles.title}>{item.article?.title}</div>}
              description={
                <div className={styles.meta}>
                  <div className={styles.explanation}>{item.explanation}</div>
                  <Tag color="blue">相关度 {(item.score * 100).toFixed(0)}%</Tag>
                </div>
              }
            />
            <Button
              type="text"
              icon={<PlusOutlined />}
              onClick={() => handleAddToLibrary(item.article_id)}
            />
          </List.Item>
        )}
      />
    )
  }

  const renderTrendingList = () => {
    if (trendingLoading) return <Spin />
    const items = trendingData || []

    if (items.length === 0) return <Empty description="暂无数据" />

    return (
      <List
        dataSource={items}
        renderItem={(item: any) => (
          <List.Item className={styles.item}>
            <List.Item.Meta
              avatar={
                <Avatar
                  shape="square"
                  size={48}
                  style={{ backgroundColor: '#fff7e6' }}
                  icon={<FireOutlined style={{ color: '#fa8c16' }} />}
                />
              }
              title={<div className={styles.title}>文献 {item.article_id}</div>}
              description={
                <Tag color="orange">
                  <FireOutlined /> 热度 {item.popularity}
                </Tag>
              }
            />
            <Button
              type="text"
              icon={<PlusOutlined />}
              onClick={() => handleAddToLibrary(item.article_id)}
            />
          </List.Item>
        )}
      />
    )
  }

  const tabItems = [
    {
      key: 'daily',
      label: (
        <Space>
          <BulbOutlined />
          每日推荐
        </Space>
      ),
      children: renderDailyList(),
    },
    {
      key: 'trending',
      label: (
        <Space>
          <FireOutlined />
          热门文献
        </Space>
      ),
      children: renderTrendingList(),
    },
  ]

  return (
    <Card className={styles.panel}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="small"
      />
    </Card>
  )
}

export default RecommendationPanel
