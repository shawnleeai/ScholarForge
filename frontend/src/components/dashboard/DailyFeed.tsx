/**
 * 每日推荐仪表板小部件
 * 在Dashboard中显示今日推荐概览
 */

import React, { useState, useEffect } from 'react'
import { Card, List, Tag, Button, Space, Typography, Badge, Skeleton, Empty } from 'antd'
import { FireOutlined, ArrowRightOutlined, CalendarOutlined, EyeOutlined, BookOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import styles from './DailyFeed.module.css'

const { Text, Title } = Typography

interface Recommendation {
  id: string
  title: string
  authors: string[]
  reason: string
  isNew: boolean
}

const DailyFeed: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    loadRecommendations()
  }, [])

  const loadRecommendations = async () => {
    try {
      setLoading(true)
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 600))

      // 模拟数据
      const mockData: Recommendation[] = [
        {
          id: '1',
          title: 'Large Language Models: A Survey of Methods and Applications',
          authors: ['Y. Liu', 'M. Chen', 'S. Wang'],
          reason: '兴趣匹配',
          isNew: true
        },
        {
          id: '2',
          title: 'RAGFlow: A Novel Framework for Knowledge-Intensive Tasks',
          authors: ['J. Zhang', 'A. Kumar'],
          reason: '阅读历史',
          isNew: true
        },
        {
          id: '3',
          title: 'Efficient Fine-tuning of LLMs for Domain Adaptation',
          authors: ['R. Brown', 'L. Taylor'],
          reason: '关键词匹配',
          isNew: false
        }
      ]

      setRecommendations(mockData)
      setTotalCount(25)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    } finally {
      setLoading(false)
    }
  }

  const getReasonColor = (reason: string) => {
    const colorMap: Record<string, string> = {
      '兴趣匹配': 'blue',
      '阅读历史': 'green',
      '关注作者': 'purple',
      '关键词匹配': 'cyan',
      '热门趋势': 'red'
    }
    return colorMap[reason] || 'default'
  }

  if (loading) {
    return (
      <Card className={styles.card}>
        <Skeleton active paragraph={{ rows: 3 }} />
      </Card>
    )
  }

  return (
    <Card
      className={styles.card}
      title={
        <Space>
          <FireOutlined className={styles.icon} />
          <span>每日论文推荐</span>
          <Badge count={totalCount} style={{ backgroundColor: '#52c41a' }} />
        </Space>
      }
      extra={
        <Button
          type="link"
          onClick={() => navigate('/daily')}
          icon={<ArrowRightOutlined />}
        >
          查看全部
        </Button>
      }
    >
      {recommendations.length > 0 ? (
        <List
          dataSource={recommendations}
          renderItem={(item) => (
            <List.Item
              className={styles.listItem}
              onClick={() => navigate(`/daily`)}
            >
              <div className={styles.itemContent}>
                <div className={styles.itemHeader}>
                  <Space size={4}>
                    {item.isNew && <Badge color="red" text="新" />}
                    <Tag size="small" color={getReasonColor(item.reason)}>
                      {item.reason}
                    </Tag>
                  </Space>
                </div>
                <Text className={styles.title} ellipsis={{ tooltip: item.title }}>
                  {item.title}
                </Text>
                <Text type="secondary" className={styles.authors}>
                  {item.authors.join(', ')}
                </Text>
              </div>
            </List.Item>
          )}
        />
      ) : (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无推荐"
        >
          <Button
            type="primary"
            onClick={() => navigate('/settings/interests')}
          >
            设置兴趣
          </Button>
        </Empty>
      )}

      <div className={styles.footer}>
        <Space>
          <Button
            icon={<CalendarOutlined />}
            onClick={() => navigate('/daily')}
          >
            今日推荐 ({totalCount})
          </Button>
          <Button
            icon={<BookOutlined />}
            onClick={() => navigate('/library')}
          >
            我的文献库
          </Button>
        </Space>
      </div>
    </Card>
  )
}

export default DailyFeed
