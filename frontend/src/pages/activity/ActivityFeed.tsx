/**
 * 研究动态页面
 * 展示学术社交动态流
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  List,
  Avatar,
  Button,
  Input,
  Tabs,
  Tag,
  Space,
  Typography,
  Divider,
  Empty,
  Skeleton,
  Tooltip,
  Badge,
  Dropdown,
  Menu,
  message,
} from 'antd'
import {
  HeartOutlined,
  HeartFilled,
  MessageOutlined,
  ShareAltOutlined,
  MoreOutlined,
  TeamOutlined,
  FileTextOutlined,
  ProjectOutlined,
  BookOutlined,
  StarOutlined,
  UserOutlined,
  ReloadOutlined,
  FilterOutlined,
  FireOutlined,
  RiseOutlined,
} from '@ant-design/icons'
import styles from './ActivityFeed.module.css'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs
const { TextArea } = Input

interface FeedItem {
  id: string
  user_id: string
  username: string
  user_avatar?: string
  activity_type: string
  target_type: string
  target_id: string
  target_title: string
  target_url?: string
  content?: string
  metadata: Record<string, any>
  created_at: string
  likes_count: number
  comments_count: number
  shares_count: number
  is_liked: boolean
}

interface TrendingTopic {
  name: string
  mentions: number
  activity: number
}

interface RecommendedUser {
  user_id: string
  username: string
  avatar?: string
  activities: number
  research_fields: string[]
}

const ActivityFeed: React.FC = () => {
  const [feedItems, setFeedItems] = useState<FeedItem[]>([])
  const [trendingTopics, setTrendingTopics] = useState<TrendingTopic[]>([])
  const [recommendedUsers, setRecommendedUsers] = useState<RecommendedUser[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('all')
  const [commentVisible, setCommentVisible] = useState<string | null>(null)
  const [commentText, setCommentText] = useState('')

  const activityTypeLabels: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
    publish_paper: { label: '发表论文', icon: <FileTextOutlined />, color: 'blue' },
    cite_paper: { label: '引用文献', icon: <BookOutlined />, color: 'green' },
    add_to_library: { label: '添加文献', icon: <BookOutlined />, color: 'cyan' },
    write_note: { label: '写笔记', icon: <FileTextOutlined />, color: 'purple' },
    create_draft: { label: '创建草稿', icon: <FileTextOutlined />, color: 'orange' },
    complete_draft: { label: '完成草稿', icon: <FileTextOutlined />, color: 'green' },
    share_draft: { label: '分享草稿', icon: <ShareAltOutlined />, color: 'geekblue' },
    join_team: { label: '加入团队', icon: <TeamOutlined />, color: 'magenta' },
    create_team: { label: '创建团队', icon: <TeamOutlined />, color: 'volcano' },
    start_project: { label: '开始项目', icon: <ProjectOutlined />, color: 'gold' },
    complete_project: { label: '完成项目', icon: <ProjectOutlined />, color: 'lime' },
    comment: { label: '评论', icon: <MessageOutlined />, color: 'default' },
    like: { label: '点赞', icon: <HeartOutlined />, color: 'red' },
    share: { label: '分享', icon: <ShareAltOutlined />, color: 'default' },
  }

  useEffect(() => {
    loadFeedData()
    loadTrendingTopics()
    loadRecommendedUsers()
  }, [activeTab])

  const loadFeedData = async () => {
    setLoading(true)
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800))

      const mockData: FeedItem[] = [
        {
          id: '1',
          user_id: 'user_001',
          username: '张教授',
          user_avatar: undefined,
          activity_type: 'publish_paper',
          target_type: 'paper',
          target_id: 'paper_001',
          target_title: '深度学习在医学影像诊断中的应用',
          content: '我们的新论文刚刚被接收！探索了Transformer架构在医学影像中的创新应用。',
          metadata: {
            journal: 'Nature Medicine',
            coauthors: ['李博士', '王同学'],
          },
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          likes_count: 45,
          comments_count: 12,
          shares_count: 8,
          is_liked: false,
        },
        {
          id: '2',
          user_id: 'user_002',
          username: '李博士',
          user_avatar: undefined,
          activity_type: 'complete_project',
          target_type: 'project',
          target_id: 'proj_001',
          target_title: '多模态学习框架开发',
          content: '历时8个月，我们的多模态学习框架终于完成了！支持文本、图像、音频的统一处理。',
          metadata: {
            team_name: '机器学习研究组',
            duration_days: 240,
          },
          created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          likes_count: 32,
          comments_count: 8,
          shares_count: 5,
          is_liked: true,
        },
        {
          id: '3',
          user_id: 'user_003',
          username: '王同学',
          user_avatar: undefined,
          activity_type: 'write_note',
          target_type: 'paper',
          target_id: 'paper_002',
          target_title: 'Attention Is All You Need',
          content: '重读经典，对位置编码有了更深的理解。分享一下我的笔记。',
          metadata: {
            note_length: 2500,
            key_insights: ['位置编码', '多头注意力', '残差连接'],
          },
          created_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
          likes_count: 28,
          comments_count: 15,
          shares_count: 3,
          is_liked: false,
        },
        {
          id: '4',
          user_id: 'user_004',
          username: '陈研究员',
          user_avatar: undefined,
          activity_type: 'join_team',
          target_type: 'team',
          target_id: 'team_002',
          target_title: '自然语言处理实验室',
          content: '',
          metadata: {
            institution: '某某大学',
            research_fields: ['NLP', '大语言模型'],
          },
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          likes_count: 15,
          comments_count: 3,
          shares_count: 0,
          is_liked: false,
        },
        {
          id: '5',
          user_id: 'user_001',
          username: '张教授',
          user_avatar: undefined,
          activity_type: 'share_draft',
          target_type: 'draft',
          target_id: 'draft_001',
          target_title: '大语言模型微调综述',
          content: '初稿完成，欢迎同行提出宝贵意见！涵盖了最新的PEFT方法。',
          metadata: {
            word_count: 8500,
            sections: 6,
            progress: 70,
          },
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          likes_count: 56,
          comments_count: 23,
          shares_count: 12,
          is_liked: true,
        },
      ]

      setFeedItems(mockData)
    } catch (error) {
      message.error('加载动态失败')
    } finally {
      setLoading(false)
    }
  }

  const loadTrendingTopics = async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 300))
      const topics: TrendingTopic[] = [
        { name: '大语言模型', mentions: 128, activity: 456 },
        { name: 'Transformer', mentions: 98, activity: 324 },
        { name: '多模态学习', mentions: 76, activity: 289 },
        { name: '强化学习', mentions: 65, activity: 198 },
        { name: '联邦学习', mentions: 54, activity: 167 },
      ]
      setTrendingTopics(topics)
    } catch (error) {
      console.error('加载热门话题失败:', error)
    }
  }

  const loadRecommendedUsers = async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 400))
      const users: RecommendedUser[] = [
        {
          user_id: 'user_005',
          username: '刘博士后',
          activities: 45,
          research_fields: ['计算机视觉', '深度学习'],
        },
        {
          user_id: 'user_006',
          username: '赵研究员',
          activities: 38,
          research_fields: ['自然语言处理', '知识图谱'],
        },
        {
          user_id: 'user_007',
          username: '孙教授',
          activities: 52,
          research_fields: ['机器学习', '数据挖掘'],
        },
      ]
      setRecommendedUsers(users)
    } catch (error) {
      console.error('加载推荐用户失败:', error)
    }
  }

  const handleLike = async (itemId: string) => {
    setFeedItems(prev =>
      prev.map(item => {
        if (item.id === itemId) {
          return {
            ...item,
            is_liked: !item.is_liked,
            likes_count: item.is_liked ? item.likes_count - 1 : item.likes_count + 1,
          }
        }
        return item
      })
    )
  }

  const handleComment = (itemId: string) => {
    setCommentVisible(commentVisible === itemId ? null : itemId)
  }

  const handleSubmitComment = () => {
    if (!commentText.trim()) return
    message.success('评论已发布')
    setCommentText('')
    setCommentVisible(null)
  }

  const handleFollowUser = (userId: string) => {
    message.success('已关注该用户')
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`

    return date.toLocaleDateString('zh-CN')
  }

  const renderFeedItem = (item: FeedItem) => {
    const activityType = activityTypeLabels[item.activity_type] || {
      label: '动态',
      icon: <RiseOutlined />,
      color: 'default',
    }

    return (
      <List.Item
        key={item.id}
        className={styles.feedItem}
        actions={[
          <Button
            key="like"
            type="text"
            icon={item.is_liked ? <HeartFilled style={{ color: '#ff4d4f' }} /> : <HeartOutlined />}
            onClick={() => handleLike(item.id)}
          >
            {item.likes_count}
          </Button>,
          <Button
            key="comment"
            type="text"
            icon={<MessageOutlined />}
            onClick={() => handleComment(item.id)}
          >
            {item.comments_count}
          </Button>,
          <Button key="share" type="text" icon={<ShareAltOutlined />}>
            {item.shares_count}
          </Button>,
          <Dropdown
            key="more"
            overlay={
              <Menu>
                <Menu.Item key="follow">关注作者</Menu.Item>
                <Menu.Item key="save">收藏</Menu.Item>
                <Menu.Divider />
                <Menu.Item key="report">举报</Menu.Item>
              </Menu>
            }
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>,
        ]}
      >
        <List.Item.Meta
          avatar={<Avatar src={item.user_avatar} icon={<UserOutlined />} size={48} />}
          title={
            <Space>
              <Text strong>{item.username}</Text>
              <Tag icon={activityType.icon} color={activityType.color}>
                {activityType.label}
              </Tag>
              <Text type="secondary" className={styles.timeText}>
                {formatTime(item.created_at)}
              </Text>
            </Space>
          }
          description={
            <div className={styles.feedContent}>
              {item.content && (
                <Paragraph className={styles.contentText}>{item.content}</Paragraph>
              )}
              <Card size="small" className={styles.targetCard}>
                <div className={styles.targetTitle}>{item.target_title}</div>
                {item.metadata.journal && (
                  <div className={styles.targetMeta}>📚 {item.metadata.journal}</div>
                )}
                {item.metadata.team_name && (
                  <div className={styles.targetMeta}>👥 {item.metadata.team_name}</div>
                )}
                {item.metadata.key_insights && (
                  <div className={styles.targetMeta}>
                    💡 {item.metadata.key_insights.join(', ')}
                  </div>
                )}
              </Card>

              {commentVisible === item.id && (
                <div className={styles.commentSection}>
                  <TextArea
                    rows={2}
                    placeholder="写下你的评论..."
                    value={commentText}
                    onChange={e => setCommentText(e.target.value)}
                  />
                  <Space className={styles.commentActions}>
                    <Button size="small" onClick={() => setCommentVisible(null)}>
                      取消
                    </Button>
                    <Button type="primary" size="small" onClick={handleSubmitComment}>
                      发布
                    </Button>
                  </Space>
                </div>
              )}
            </div>
          }
        />
      </List.Item>
    )
  }

  return (
    <div className={styles.container}>
      <Row gutter={[24, 24]}>
        <Col span={16}>
          <Card className={styles.feedCard}>
            <div className={styles.feedHeader}>
              <Title level={4}>
                <FireOutlined /> 研究动态
              </Title>
              <Space>
                <Button icon={<FilterOutlined />}>筛选</Button>
                <Button icon={<ReloadOutlined />} onClick={loadFeedData}>
                  刷新
                </Button>
              </Space>
            </div>

            <Tabs activeKey={activeTab} onChange={setActiveTab} className={styles.feedTabs}>
              <TabPane tab="全部" key="all" />
              <TabPane tab="关注" key="following" />
              <TabPane tab="论文" key="papers" />
              <TabPane tab="项目" key="projects" />
              <TabPane tab="团队" key="teams" />
            </Tabs>

            {loading ? (
              <Skeleton active paragraph={{ rows: 4 }} />
            ) : feedItems.length === 0 ? (
              <Empty description="暂无动态" />
            ) : (
              <List
                dataSource={feedItems}
                renderItem={renderFeedItem}
                split
                className={styles.feedList}
              />
            )}

            <div className={styles.loadMore}>
              <Button type="link">加载更多</Button>
            </div>
          </Card>
        </Col>

        <Col span={8}>
          {/* 热门话题 */}
          <Card className={styles.sideCard} title={<><FireOutlined /> 热门话题</>}>
            <List
              dataSource={trendingTopics}
              renderItem={(topic, index) => (
                <List.Item className={styles.topicItem}>
                  <div className={styles.topicRank}>{index + 1}</div>
                  <div className={styles.topicInfo}>
                    <div className={styles.topicName}>{topic.name}</div>
                    <div className={styles.topicStats}>
                      {topic.mentions} 提及 · {topic.activity} 互动
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>

          {/* 推荐关注 */}
          <Card
            className={styles.sideCard}
            title={<><StarOutlined /> 推荐关注</>}
          >
            <List
              dataSource={recommendedUsers}
              renderItem={user => (
                <List.Item
                  className={styles.userItem}
                  actions={[
                    <Button
                      type="primary"
                      size="small"
                      onClick={() => handleFollowUser(user.user_id)}
                    >
                      关注
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Avatar icon={<UserOutlined />} />}
                    title={user.username}
                    description={
                      <Space wrap size={4}>
                        {user.research_fields.map(field => (
                          <Tag key={field} size="small">
                            {field}
                          </Tag>
                        ))}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>

          {/* 快捷操作 */}
          <Card className={styles.sideCard} title="快捷操作">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button block icon={<FileTextOutlined />}>
                发布论文
              </Button>
              <Button block icon={<ProjectOutlined />}>
                创建项目
              </Button>
              <Button block icon={<TeamOutlined />}>
                创建团队
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default ActivityFeed
