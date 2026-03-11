/**
 * 仪表盘页面
 */

import React from 'react'
import { Row, Col, Card, Statistic, List, Button, Tag, Space, Typography, message } from 'antd'
import {
  FileTextOutlined,
  BookOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  EditOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { paperService, articleService } from '@/services'
import { useAuthStore } from '@/stores'
import { DailyRecommendations } from '@/components'
import { RecommendationCard } from '@/components/recommendation'
import type { Paper, PaginatedResponse, LibraryItem } from '@/types'
import type { RecommendedPaper } from '@/services/recommendationService'
import { DemoLauncher } from '@/components/demo'
import styles from './Dashboard.module.css'

const { Title, Text } = Typography

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()

  const { data: papersData } = useQuery({
    queryKey: ['papers'],
    queryFn: () => paperService.getPapers({ page: 1, pageSize: 5 }),
  })

  const { data: libraryData } = useQuery({
    queryKey: ['library'],
    queryFn: () => articleService.getLibrary(),
  })

  const papers = (papersData?.data as PaginatedResponse<Paper>)?.items || []
  const totalPapers = (papersData?.data as PaginatedResponse<Paper>)?.total || 0
  const totalLibrary = (libraryData?.data as PaginatedResponse<LibraryItem>)?.total || 0

  const stats = [
    {
      title: '我的论文',
      value: totalPapers,
      icon: <FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />,
      color: '#1890ff',
    },
    {
      title: '文献库',
      value: totalLibrary,
      icon: <BookOutlined style={{ fontSize: 24, color: '#52c41a' }} />,
      color: '#52c41a',
    },
    {
      title: '协作项目',
      value: 3,
      icon: <TeamOutlined style={{ fontSize: 24, color: '#722ed1' }} />,
      color: '#722ed1',
    },
    {
      title: '本周写作',
      value: 2340,
      suffix: '字',
      icon: <ClockCircleOutlined style={{ fontSize: 24, color: '#fa8c16' }} />,
      color: '#fa8c16',
    },
  ]

  const statusColors: Record<string, string> = {
    draft: 'default',
    in_progress: 'processing',
    review: 'warning',
    submitted: 'blue',
    published: 'green',
  }

  const statusLabels: Record<string, string> = {
    draft: '草稿',
    in_progress: '写作中',
    review: '审核中',
    submitted: '已提交',
    published: '已发表',
  }

  const handleViewArticle = (articleId: string) => {
    navigate(`/library?id=${articleId}`)
  }

  const handleSaveArticle = (articleId: string) => {
    console.log('保存文章:', articleId)
  }

  return (
    <div className={styles.dashboard}>
      <div className={`${styles.welcome} dashboard-welcome`}>
        <div>
          <Title level={3} style={{ margin: 0 }}>
            欢迎回来，{user?.fullName || user?.username}！
          </Title>
          <Text type="secondary">今天是继续学术研究的好日子</Text>
        </div>
        <Space>
          <DemoLauncher />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="large"
            onClick={() => navigate('/papers')}
          >
            新建论文
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} className={styles.statsRow}>
        {stats.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card className={styles.statCard}>
              <div className={styles.statIcon} style={{ backgroundColor: `${stat.color}15` }}>
                {stat.icon}
              </div>
              <Statistic
                title={stat.title}
                value={stat.value}
                suffix={stat.suffix}
                valueStyle={{ fontSize: 28, fontWeight: 600 }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card
            title="最近论文"
            extra={<Button type="link" onClick={() => navigate('/papers')}>查看全部</Button>}
          >
            <List
              dataSource={papers}
              renderItem={(paper: Paper) => (
                <List.Item
                  className={styles.listItem}
                  onClick={() => navigate(`/papers/${paper.id}`)}
                >
                  <List.Item.Meta
                    avatar={
                      <div className={styles.paperIcon}>
                        <FileTextOutlined />
                      </div>
                    }
                    title={
                      <Space>
                        <span>{paper.title}</span>
                        <Tag color={statusColors[paper.status]}>
                          {statusLabels[paper.status]}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Space split={<span style={{ color: '#d9d9d9' }}>|</span>}>
                        <span>{paper.wordCount} 字</span>
                        <span>更新于 {new Date(paper.updatedAt).toLocaleDateString()}</span>
                      </Space>
                    }
                  />
                  <Button type="text" icon={<EditOutlined />} />
                </List.Item>
              )}
              locale={{ emptyText: '暂无论文' }}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <DailyRecommendations
            limit={4}
            compact
            onViewArticle={handleViewArticle}
            onSaveArticle={handleSaveArticle}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="快捷操作">
            <Row gutter={16}>
              <Col span={8}>
                <Button block icon={<FileTextOutlined />} onClick={() => navigate('/papers')} size="large">
                  新建论文
                </Button>
              </Col>
              <Col span={8}>
                <Button block icon={<BookOutlined />} onClick={() => navigate('/library/search')} size="large">
                  搜索文献
                </Button>
              </Col>
              <Col span={8}>
                <Button block icon={<TeamOutlined />} size="large" onClick={() => message.info('协作功能开发中，敬请期待！')}>
                  邀请协作者
                </Button>
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={8}>
                <Button block icon={<TrophyOutlined />} onClick={() => navigate('/analytics')} size="large" type="primary">
                  学术影响力
                </Button>
              </Col>
              <Col span={8}>
                <Button block icon={<ThunderboltOutlined />} onClick={() => navigate('/review')} size="large" type="primary">
                  生成综述
                </Button>
              </Col>
              <Col span={8}>
                <Button block icon={<BookOutlined />} onClick={() => navigate('/library')} size="large">
                  文献库
                </Button>
              </Col>
            </Row>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="写作进度">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text type="secondary">本周完成 2,340 字</Text>
              <Text type="secondary">连续写作 5 天</Text>
              <Text type="secondary">距离目标还差 7,660 字</Text>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
