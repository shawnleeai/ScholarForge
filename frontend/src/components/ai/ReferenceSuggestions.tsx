/**
 * 引用建议组件
 */

import React, { useState } from 'react'
import { Card, List, Button, Input, Space, Tag, Typography, Spin, Empty, message, Tooltip } from 'antd'
import {
  SearchOutlined,
  PlusOutlined,
  CopyOutlined,
  ExportOutlined,
  BookOutlined,
} from '@ant-design/icons'

import { aiService, type ReferenceSuggestion } from '@/services/aiService'
import styles from './AIComponents.module.css'

const { TextArea } = Input
const { Text, Paragraph } = Typography

interface ReferenceSuggestionsProps {
  paperId?: string
  onInsert?: (reference: ReferenceSuggestion) => void
}

const ReferenceSuggestions: React.FC<ReferenceSuggestionsProps> = ({
  paperId,
  onInsert,
}) => {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<ReferenceSuggestion[]>([])

  const handleSearch = async () => {
    if (!text.trim()) {
      message.warning('请输入需要查找引用的文本')
      return
    }

    setLoading(true)
    try {
      const response = await aiService.suggestReferences({
        text: text.trim(),
        paperId,
        maxResults: 5,
      })
      setSuggestions(response.data.suggestions)
    } catch {
      message.error('获取引用建议失败')
    } finally {
      setLoading(false)
    }
  }

  const handleInsert = (ref: ReferenceSuggestion) => {
    if (onInsert) {
      onInsert(ref)
      message.success('已添加到引用列表')
    } else {
      // 复制引用格式
      const citation = `${ref.authors.join(', ')} (${ref.year}). ${ref.title}. ${ref.source}.`
      navigator.clipboard.writeText(citation)
      message.success('引用已复制到剪贴板')
    }
  }

  const handleCopyCitation = (ref: ReferenceSuggestion) => {
    const citation = `${ref.authors.join(', ')} (${ref.year}). ${ref.title}. ${ref.source}.`
    navigator.clipboard.writeText(citation)
    message.success('引用已复制')
  }

  const getRelevanceColor = (relevance: number) => {
    if (relevance >= 0.9) return 'green'
    if (relevance >= 0.8) return 'blue'
    if (relevance >= 0.7) return 'orange'
    return 'default'
  }

  return (
    <div className={styles.referenceSuggestions}>
      <div className={styles.inputSection}>
        <TextArea
          rows={3}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="输入需要查找引用的段落或关键词，AI 将推荐相关的学术文献..."
          className={styles.textInput}
        />
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={handleSearch}
          loading={loading}
          className={styles.searchButton}
        >
          查找引用
        </Button>
      </div>

      {loading && (
        <div className={styles.loadingContainer}>
          <Spin tip="正在分析并搜索相关文献..." />
        </div>
      )}

      {!loading && suggestions.length === 0 && text && (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="点击查找引用获取推荐"
        />
      )}

      {!loading && suggestions.length > 0 && (
        <List
          className={styles.suggestionList}
          dataSource={suggestions}
          renderItem={(item) => (
            <List.Item className={styles.suggestionItem}>
              <Card
                size="small"
                className={styles.suggestionCard}
                title={
                  <Space direction="vertical" size={0}>
                    <Text strong ellipsis className={styles.title}>
                      <BookOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                      {item.title}
                    </Text>
                    <Space size={4} wrap>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {item.authors.join(', ')}
                      </Text>
                      <Tag color="blue">{item.year}</Tag>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {item.source}
                      </Text>
                    </Space>
                  </Space>
                }
                extra={
                  <Tag color={getRelevanceColor(item.relevance)}>
                    相关度 {(item.relevance * 100).toFixed(0)}%
                  </Tag>
                }
              >
                <Paragraph
                  type="secondary"
                  style={{ fontSize: 12, marginBottom: 8 }}
                  ellipsis={{ rows: 2 }}
                >
                  {item.reason}
                </Paragraph>
                <Space>
                  <Button
                    type="primary"
                    size="small"
                    icon={<PlusOutlined />}
                    onClick={() => handleInsert(item)}
                  >
                    添加引用
                  </Button>
                  <Tooltip title="复制引用格式">
                    <Button
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={() => handleCopyCitation(item)}
                    />
                  </Tooltip>
                  {item.doi && (
                    <Tooltip title="查看原文">
                      <Button
                        size="small"
                        icon={<ExportOutlined />}
                        href={`https://doi.org/${item.doi}`}
                        target="_blank"
                      />
                    </Tooltip>
                  )}
                </Space>
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  )
}

export default ReferenceSuggestions
