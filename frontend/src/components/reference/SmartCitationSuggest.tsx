/**
 * 智能引用推荐组件
 * 根据当前编辑内容智能推荐相关文献引用
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  List,
  Typography,
  Space,
  Tag,
  Button,
  Tooltip,
  Badge,
  Spin,
  Empty,
  Input,
  Tabs,
  Popover,
  Progress,
  Divider,
} from 'antd'
import {
  BookOutlined,
  PlusOutlined,
  StarOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  CloseOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { referenceService } from '../../services/referenceService'
import styles from './SmartCitationSuggest.module.css'

const { Text, Paragraph, Title } = Typography
const { TextArea } = Input
const { TabPane } = Tabs

interface CitationSuggestion {
  article_id: string
  title: string
  authors: string[]
  year: number
  journal?: string
  relevance_score: number
  context_match: number
  importance_score: number
  reason: string
  snippet?: string
  cited_count: number
}

interface SmartCitationSuggestProps {
  paperId: string
  currentSection?: string
  currentText?: string
  onInsertCitation: (citation: CitationSuggestion) => void
  visible?: boolean
  onClose?: () => void
}

const SmartCitationSuggest: React.FC<SmartCitationSuggestProps> = ({
  paperId,
  currentSection = 'introduction',
  currentText = '',
  onInsertCitation,
  visible = true,
  onClose,
}) => {
  const [suggestions, setSuggestions] = useState<CitationSuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('context')
  const [selectedCitation, setSelectedCitation] = useState<CitationSuggestion | null>(null)
  const [customQuery, setCustomQuery] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  // 获取推荐引用
  const fetchSuggestions = useCallback(async () => {
    setLoading(true)
    try {
      const response = await referenceService.getSmartRecommendations({
        paper_id: paperId,
        section: currentSection,
        context: currentText.slice(-500), // 最近500字符
        limit: 10,
      })
      setSuggestions(response.suggestions || [])
    } catch (error) {
      console.error('获取引用推荐失败:', error)
    } finally {
      setLoading(false)
    }
  }, [paperId, currentSection, currentText, refreshKey])

  // 搜索引用
  const searchCitations = async () => {
    if (!customQuery.trim()) return
    setLoading(true)
    try {
      const response = await referenceService.searchReferences({
        query: customQuery,
        limit: 10,
      })
      setSuggestions(response.results || [])
      setActiveTab('search')
    } catch (error) {
      console.error('搜索引用失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (visible && currentText) {
      fetchSuggestions()
    }
  }, [visible, currentText, fetchSuggestions])

  const handleInsert = (citation: CitationSuggestion) => {
    onInsertCitation(citation)
    // 标记为已使用
    setSuggestions(prev =>
      prev.map(s =>
        s.article_id === citation.article_id
          ? { ...s, used: true }
          : s
      )
    )
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#52c41a'
    if (score >= 0.6) return '#faad14'
    return '#ff4d4f'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 0.8) return '高相关'
    if (score >= 0.6) return '中等'
    return '一般'
  }

  const renderCitationCard = (citation: CitationSuggestion) => (
    <Card
      size="small"
      className={styles.citationCard}
      actions={[
        <Tooltip title="插入引用">
          <Button
            type="primary"
            size="small"
            icon={<PlusOutlined />}
            onClick={() => handleInsert(citation)}
          >
            插入
          </Button>
        </Tooltip>,
        <Tooltip title="查看详情">
          <Button
            size="small"
            icon={<BookOutlined />}
            onClick={() => setSelectedCitation(citation)}
          >
            详情
          </Button>
        </Tooltip>,
      ]}
    >
      <div className={styles.citationHeader}>
        <Space>
          <Badge
            count={Math.round(citation.relevance_score * 100)}
            style={{ backgroundColor: getScoreColor(citation.relevance_score) }}
          />
          <Text strong className={styles.citationTitle} ellipsis>
            {citation.title}
          </Text>
        </Space>
      </div>

      <div className={styles.citationMeta}>
        <Space wrap size="small">
          <Text type="secondary">
            {citation.authors.slice(0, 3).join(', ')}
            {citation.authors.length > 3 && ' et al.'}
          </Text>
          <Tag size="small" color="blue">{citation.year}</Tag>
          {citation.journal && (
            <Tag size="small">{citation.journal}</Tag>
          )}
        </Space>
      </div>

      {citation.snippet && (
        <Paragraph type="secondary" className={styles.snippet} ellipsis={{ rows: 2 }}>
          "{citation.snippet}"
        </Paragraph>
      )}

      <div className={styles.citationReason}>
        <ThunderboltOutlined style={{ color: '#faad14' }} />
        <Text type="secondary" className={styles.reasonText}>
          {citation.reason}
        </Text>
      </div>

      <div className={styles.citationStats}>
        <Space size="small">
          <Tooltip title="被引次数">
            <Tag icon={<BarChartOutlined />} size="small">
              {citation.cited_count}
            </Tag>
          </Tooltip>
          <Tooltip title="上下文匹配度">
            <Progress
              percent={Math.round(citation.context_match * 100)}
              size="small"
              style={{ width: 60 }}
              showInfo={false}
            />
          </Tooltip>
        </Space>
      </div>
    </Card>
  )

  if (!visible) return null

  return (
    <Card
      className={styles.suggestPanel}
      title={
        <Space>
          <ThunderboltOutlined style={{ color: '#faad14' }} />
          <span>智能引用推荐</span>
          {loading && <Spin size="small" />}
        </Space>
      }
      extra={
        <Space>
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={() => setRefreshKey(k => k + 1)}
            loading={loading}
          >
            刷新
          </Button>
          {onClose && (
            <Button type="text" icon={<CloseOutlined />} onClick={onClose} />
          )}
        </Space>
      }
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <span>
              <ThunderboltOutlined />
              智能推荐
            </span>
          }
          key="context"
        >
          <div className={styles.contextInfo}>
            <Text type="secondary">
              基于「{currentSection}」章节内容智能推荐
            </Text>
          </div>

          {suggestions.length > 0 ? (
            <List
              dataSource={suggestions}
              renderItem={item => (
                <List.Item className={styles.listItem}>
                  {renderCitationCard(item)}
                </List.Item>
              )}
            />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无推荐引用"
            >
              <Button onClick={fetchSuggestions}>重新获取</Button>
            </Empty>
          )}
        </TabPane>

        <TabPane
          tab={
            <span>
              <LinkOutlined />
              我的文献库
            </span>
          }
          key="library"
        >
          <Empty description="从您的文献库中推荐" />
        </TabPane>

        <TabPane
          tab={
            <span>
              <CheckCircleOutlined />
              已使用
            </span>
          }
          key="used"
        >
          <Empty description="已插入的引用将显示在这里" />
        </TabPane>

        <TabPane
          tab={
            <span>
              <BarChartOutlined />
              搜索
            </span>
          }
          key="search"
        >
          <div className={styles.searchBox}>
            <Input.Search
              placeholder="搜索文献标题、作者、关键词..."
              value={customQuery}
              onChange={e => setCustomQuery(e.target.value)}
              onSearch={searchCitations}
              loading={loading}
              enterButton
            />
          </div>

          {suggestions.length > 0 && activeTab === 'search' && (
            <List
              dataSource={suggestions}
              renderItem={item => (
                <List.Item className={styles.listItem}>
                  {renderCitationCard(item)}
                </List.Item>
              )}
            />
          )}
        </TabPane>
      </Tabs>

      {/* 引用详情弹窗 */}
      {selectedCitation && (
        <CitationDetailModal
          citation={selectedCitation}
          visible={!!selectedCitation}
          onClose={() => setSelectedCitation(null)}
          onInsert={() => handleInsert(selectedCitation)}
        />
      )}
    </Card>
  )
}

// 引用详情弹窗组件
interface CitationDetailModalProps {
  citation: CitationSuggestion
  visible: boolean
  onClose: () => void
  onInsert: () => void
}

const CitationDetailModal: React.FC<CitationDetailModalProps> = ({
  citation,
  visible,
  onClose,
  onInsert,
}) => {
  return (
    <Card className={styles.detailModal}>
      <div className={styles.detailHeader}>
        <Title level={5}>{citation.title}</Title>
        <Button type="text" icon={<CloseOutlined />} onClick={onClose} />
      </div>

      <Divider />

      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <Text type="secondary">作者：</Text>
          <Text>{citation.authors.join(', ')}</Text>
        </div>

        <div>
          <Text type="secondary">发表年份：</Text>
          <Tag color="blue">{citation.year}</Tag>
        </div>

        {citation.journal && (
          <div>
            <Text type="secondary">期刊：</Text>
            <Text>{citation.journal}</Text>
          </div>
        )}

        <Divider />

        <div className={styles.scoreSection}>
          <Text strong>推荐评分</Text>
          <div className={styles.scores}>
            <div className={styles.scoreItem}>
              <Text type="secondary">相关度</Text>
              <Progress
                percent={Math.round(citation.relevance_score * 100)}
                status="active"
              />
            </div>
            <div className={styles.scoreItem}>
              <Text type="secondary">上下文匹配</Text>
              <Progress
                percent={Math.round(citation.context_match * 100)}
                status="active"
              />
            </div>
            <div className={styles.scoreItem}>
              <Text type="secondary">重要性</Text>
              <Progress
                percent={Math.round(citation.importance_score * 100)}
                status="active"
              />
            </div>
          </div>
        </div>

        <Divider />

        <div className={styles.actionButtons}>
          <Button onClick={onClose}>关闭</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={onInsert}>
            插入引用
          </Button>
        </div>
      </Space>
    </Card>
  )
}

export default SmartCitationSuggest
