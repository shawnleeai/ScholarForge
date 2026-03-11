/**
 * 每日论文推荐页面
 * 展示个性化论文推荐列表
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  List,
  Tag,
  Button,
  Space,
  Typography,
  Badge,
  Skeleton,
  Empty,
  message,
  Tabs,
  Tooltip,
  Popover,
  Divider,
  DatePicker,
  Row,
  Col,
  Statistic,
  Affix
} from 'antd'
import {
  BookOutlined,
  FireOutlined,
  ReloadOutlined,
  SettingOutlined,
  CalendarOutlined,
  EyeOutlined,
  StarOutlined,
  ShareAltOutlined,
  CloseCircleOutlined,
  ReadOutlined,
  ClockCircleOutlined,
  UserOutlined,
  TagOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import styles from './DailyPapers.module.css'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

interface Author {
  name: string
  affiliation?: string
}

interface Paper {
  id: string
  title: string
  abstract?: string
  authors: Author[]
  url?: string
  pdf_url?: string
  doi?: string
  arxiv_id?: string
  published_at?: string
  categories: string[]
  keywords: string[]
  journal?: string
  year?: number
  citation_count: number
  source: string
}

interface Recommendation {
  id: string
  paper: Paper
  score: number
  reason: string
  reason_detail: string
  rank: number
  is_new: boolean
}

interface DailyFeedResponse {
  date: string
  total: number
  recommendations: Recommendation[]
  has_more: boolean
}

type FilterType = 'all' | 'unread' | 'saved' | 'dismissed'
type SortType = 'recommend' | 'date' | 'citations'

const DailyPapers: React.FC = () => {
  const navigate = useNavigate()

  // 状态
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [selectedDate, setSelectedDate] = useState<dayjs.Dayjs>(dayjs())
  const [filter, setFilter] = useState<FilterType>('all')
  const [sortBy, setSortBy] = useState<SortType>('recommend')
  const [totalCount, setTotalCount] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [offset, setOffset] = useState(0)

  // 加载推荐数据
  const loadRecommendations = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true)
      } else if (offset === 0) {
        setLoading(true)
      }

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800))

      // 模拟数据
      const mockData: Recommendation[] = [
        {
          id: 'rec_1',
          paper: {
            id: 'paper_1',
            title: 'Large Language Models: A Survey of Methods, Applications, and Challenges',
            abstract: 'This comprehensive survey examines the current state of large language models (LLMs), covering architectures, training methodologies, evaluation benchmarks, and diverse applications across natural language processing tasks. We analyze over 100 recent papers and identify key trends and future directions.',
            authors: [
              { name: 'Y. Liu', affiliation: 'Stanford University' },
              { name: 'M. Chen', affiliation: 'MIT' },
              { name: 'S. Wang', affiliation: 'Google Research' }
            ],
            url: 'https://arxiv.org/abs/2401.12345',
            pdf_url: 'https://arxiv.org/pdf/2401.12345.pdf',
            arxiv_id: '2401.12345',
            published_at: '2024-01-15',
            categories: ['cs.CL', 'cs.AI', 'cs.LG'],
            keywords: ['large language models', 'survey', 'NLP'],
            journal: 'arXiv preprint',
            year: 2024,
            citation_count: 156,
            source: 'arxiv'
          },
          score: 0.95,
          reason: 'based_on_interest',
          reason_detail: '匹配您的研究兴趣: Natural Language Processing, Large Language Models',
          rank: 1,
          is_new: true
        },
        {
          id: 'rec_2',
          paper: {
            id: 'paper_2',
            title: 'RAGFlow: A Retrieval-Augmented Generation Framework for Knowledge-Intensive Tasks',
            abstract: 'We propose RAGFlow, a novel framework that optimizes the retrieval-augmented generation pipeline through dynamic document chunking, adaptive retrieval strategies, and iterative refinement. Experimental results on 5 benchmarks show 15% improvement over baseline methods.',
            authors: [
              { name: 'J. Zhang', affiliation: 'Tsinghua University' },
              { name: 'A. Kumar', affiliation: 'Microsoft Research' }
            ],
            url: 'https://arxiv.org/abs/2401.12346',
            pdf_url: 'https://arxiv.org/pdf/2401.12346.pdf',
            arxiv_id: '2401.12346',
            published_at: '2024-01-14',
            categories: ['cs.IR', 'cs.CL', 'cs.AI'],
            keywords: ['RAG', 'retrieval-augmented generation', 'knowledge base'],
            journal: 'arXiv preprint',
            year: 2024,
            citation_count: 42,
            source: 'arxiv'
          },
          score: 0.88,
          reason: 'based_on_reading',
          reason_detail: '基于您的阅读历史推荐',
          rank: 2,
          is_new: true
        },
        {
          id: 'rec_3',
          paper: {
            id: 'paper_3',
            title: 'Efficient Fine-tuning of Large Language Models for Domain Adaptation',
            abstract: 'This paper introduces LoRA-X, an extension to Low-Rank Adaptation that achieves superior domain adaptation with 50% fewer parameters. We demonstrate effectiveness on medical, legal, and scientific domains.',
            authors: [
              { name: 'R. Brown', affiliation: 'DeepMind' },
              { name: 'L. Taylor', affiliation: 'OpenAI' },
              { name: 'K. Lee', affiliation: 'Meta AI' }
            ],
            url: 'https://arxiv.org/abs/2401.12347',
            pdf_url: 'https://arxiv.org/pdf/2401.12347.pdf',
            arxiv_id: '2401.12347',
            published_at: '2024-01-13',
            categories: ['cs.LG', 'cs.CL', 'cs.AI'],
            keywords: ['fine-tuning', 'domain adaptation', 'LoRA', 'parameter efficiency'],
            journal: 'arXiv preprint',
            year: 2024,
            citation_count: 89,
            source: 'arxiv'
          },
          score: 0.82,
          reason: 'keyword_match',
          reason_detail: '与您关注的关键词相关: machine learning, deep learning',
          rank: 3,
          is_new: false
        }
      ]

      if (isRefresh || offset === 0) {
        setRecommendations(mockData)
      } else {
        setRecommendations(prev => [...prev, ...mockData])
      }

      setTotalCount(25)
      setHasMore(true)
    } catch (error) {
      message.error('加载推荐失败')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [offset, selectedDate])

  // 初始加载
  useEffect(() => {
    loadRecommendations()
  }, [loadRecommendations])

  // 刷新推荐
  const handleRefresh = async () => {
    setOffset(0)
    await loadRecommendations(true)
    message.success('推荐已刷新')
  }

  // 加载更多
  const handleLoadMore = () => {
    setOffset(prev => prev + 10)
    loadRecommendations()
  }

  // 保存论文
  const handleSave = (rec: Recommendation) => {
    message.success(`已保存: ${rec.paper.title.substring(0, 30)}...`)
  }

  // 忽略推荐
  const handleDismiss = (recId: string) => {
    setRecommendations(prev => prev.filter(r => r.id !== recId))
    message.success('已忽略该推荐')
  }

  // 分享
  const handleShare = (rec: Recommendation) => {
    // 复制链接到剪贴板
    navigator.clipboard.writeText(rec.paper.url || '')
    message.success('链接已复制到剪贴板')
  }

  // 渲染推荐理由标签
  const renderReasonTag = (reason: string) => {
    const reasonMap: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
      'based_on_interest': { color: 'blue', text: '兴趣匹配', icon: <StarOutlined /> },
      'based_on_reading': { color: 'green', text: '阅读历史', icon: <ReadOutlined /> },
      'follow_author': { color: 'purple', text: '关注作者', icon: <UserOutlined /> },
      'similar_to_saved': { color: 'orange', text: '相似收藏', icon: <BookOutlined /> },
      'keyword_match': { color: 'cyan', text: '关键词匹配', icon: <TagOutlined /> },
      'trending': { color: 'red', text: '热门趋势', icon: <FireOutlined /> },
    }

    const info = reasonMap[reason] || { color: 'default', text: reason, icon: null }

    return (
      <Tag color={info.color} icon={info.icon}>
        {info.text}
      </Tag>
    )
  }

  // 渲染作者
  const renderAuthors = (authors: Author[]) => {
    const displayAuthors = authors.slice(0, 3)
    const remaining = authors.length - 3

    return (
      <Space size={4}>
        {displayAuthors.map((author, idx) => (
          <Text key={idx} type="secondary" className={styles.author}>
            {author.name}{idx < displayAuthors.length - 1 ? ',' : ''}
          </Text>
        ))}
        {remaining > 0 && (
          <Tooltip title={authors.slice(3).map(a => a.name).join(', ')}>
            <Text type="secondary">+{remaining}</Text>
          </Tooltip>
        )}
      </Space>
    )
  }

  // 渲染论文卡片
  const renderPaperCard = (rec: Recommendation) => (
    <Card
      className={styles.paperCard}
      key={rec.id}
      bodyStyle={{ padding: 20 }}
    >
      <div className={styles.cardHeader}>
        <Space>
          {renderReasonTag(rec.reason)}
          {rec.is_new && <Badge color="red" text="新" />}
          <Text type="secondary" className={styles.rank}>#{rec.rank}</Text>
        </Space>
        <Space>
          <Tooltip title="保存到文献库">
            <Button
              type="text"
              icon={<BookOutlined />}
              onClick={() => handleSave(rec)}
            />
          </Tooltip>
          <Tooltip title="分享">
            <Button
              type="text"
              icon={<ShareAltOutlined />}
              onClick={() => handleShare(rec)}
            />
          </Tooltip>
          <Tooltip title="忽略">
            <Button
              type="text"
              danger
              icon={<CloseCircleOutlined />}
              onClick={() => handleDismiss(rec.id)}
            />
          </Tooltip>
        </Space>
      </div>

      <Title level={5} className={styles.title}>
        <a
          href={rec.paper.pdf_url || rec.paper.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          {rec.paper.title}
        </a>
      </Title>

      <div className={styles.meta}>
        {renderAuthors(rec.paper.authors)}
      </div>

      <div className={styles.meta}>
        <Space size={16}>
          {rec.paper.journal && (
            <Text type="secondary">
              <BookOutlined /> {rec.paper.journal}
            </Text>
          )}
          {rec.paper.published_at && (
            <Text type="secondary">
              <CalendarOutlined /> {rec.paper.published_at}
            </Text>
          )}
          <Text type="secondary">
            <FireOutlined /> {rec.paper.citation_count} 引用
          </Text>
        </Space>
      </div>

      <Paragraph
        className={styles.abstract}
        ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
      >
        {rec.paper.abstract}
      </Paragraph>

      <div className={styles.tags}>
        {rec.paper.categories.map(cat => (
          <Tag key={cat} size="small">{cat}</Tag>
        ))}
      </div>

      <div className={styles.footer}>
        <Space>
          <Button
            type="primary"
            icon={<EyeOutlined />}
            href={rec.paper.pdf_url}
            target="_blank"
          >
            查看PDF
          </Button>
          <Button
            icon={<ReadOutlined />}
            onClick={() => navigate(`/articles/${rec.paper.id}`)}
          >
            阅读详情
          </Button>
        </Space>
        <Tooltip title={`匹配度: ${(rec.score * 100).toFixed(1)}%`}>
          <div className={styles.scoreBar}>
            <div
              className={styles.scoreFill}
              style={{ width: `${rec.score * 100}%` }}
            />
          </div>
        </Tooltip>
      </div>
    </Card>
  )

  return (
    <div className={styles.container}>
      {/* 页面头部 */}
      <Affix offsetTop={0}>
        <div className={styles.header}>
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={3} className={styles.pageTitle}>
                <FireOutlined /> 每日论文推荐
                <Text type="secondary" className={styles.date}>
                  {selectedDate.format('YYYY年MM月DD日')}
                </Text>
              </Title>
            </Col>
            <Col>
              <Space>
                <DatePicker
                  value={selectedDate}
                  onChange={(date) => {
                    if (date) {
                      setSelectedDate(date)
                      setOffset(0)
                      loadRecommendations()
                    }
                  }}
                  disabledDate={(date) => date.isAfter(dayjs())}
                />
                <Button
                  icon={<ReloadOutlined spin={refreshing} />}
                  onClick={handleRefresh}
                  loading={refreshing}
                >
                  刷新推荐
                </Button>
                <Button
                  icon={<SettingOutlined />}
                  onClick={() => navigate('/settings/interests')}
                >
                  兴趣设置
                </Button>
              </Space>
            </Col>
          </Row>

          {/* 统计信息 */}
          <Row gutter={16} className={styles.stats}>
            <Col>
              <Statistic
                title="今日推荐"
                value={totalCount}
                prefix={<BookOutlined />}
              />
            </Col>
            <Col>
              <Statistic
                title="新论文"
                value={recommendations.filter(r => r.is_new).length}
                prefix={<FireOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
            <Col>
              <Statistic
                title="平均匹配度"
                value={recommendations.length > 0
                  ? (recommendations.reduce((acc, r) => acc + r.score, 0) / recommendations.length * 100).toFixed(1)
                  : 0
                }
                suffix="%"
                prefix={<StarOutlined />}
              />
            </Col>
          </Row>

          {/* 筛选标签 */}
          <Tabs
            activeKey={filter}
            onChange={(key) => setFilter(key as FilterType)}
            className={styles.tabs}
          >
            <TabPane tab="全部推荐" key="all" />
            <TabPane tab="未读" key="unread" />
            <TabPane tab="已保存" key="saved" />
            <TabPane tab="已忽略" key="dismissed" />
          </Tabs>
        </div>
      </Affix>

      {/* 推荐列表 */}
      <div className={styles.content}>
        {loading ? (
          <Card>
            <Skeleton active avatar paragraph={{ rows: 4 }} />
            <Divider />
            <Skeleton active avatar paragraph={{ rows: 4 }} />
            <Divider />
            <Skeleton active avatar paragraph={{ rows: 4 }} />
          </Card>
        ) : recommendations.length > 0 ? (
          <>
            <List
              dataSource={recommendations}
              renderItem={(rec) => (
                <List.Item>{renderPaperCard(rec)}</List.Item>
              )}
              split={false}
            />
            {hasMore && (
              <div className={styles.loadMore}>
                <Button onClick={handleLoadMore} size="large">
                  加载更多
                </Button>
              </div>
            )}
          </>
        ) : (
          <Empty
            description="暂无推荐，请调整兴趣设置"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button
              type="primary"
              onClick={() => navigate('/settings/interests')}
            >
              设置兴趣
            </Button>
          </Empty>
        )}
      </div>
    </div>
  )
}

export default DailyPapers
