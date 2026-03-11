/**
 * 引用卡片组件
 * 展示AI回答中的文献引用
 */

import React, { useState } from 'react'
import { Card, Typography, Tag, Space, Button, Modal, List, Tooltip } from 'antd'
import {
  BookOutlined,
  FileTextOutlined,
  ExportOutlined,
  LinkOutlined,
  CalendarOutlined,
  UserOutlined,
} from '@ant-design/icons'
import type { Citation } from '@/types'
import styles from './CitationCards.module.css'

const { Text, Paragraph, Title } = Typography

interface CitationCardsProps {
  citations: Citation[]
  maxDisplay?: number
  showExpand?: boolean
}

const CitationCards: React.FC<CitationCardsProps> = ({
  citations,
  maxDisplay = 3,
  showExpand = true,
}) => {
  const [expanded, setExpanded] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)

  const displayCitations = expanded ? citations : citations.slice(0, maxDisplay)
  const hasMore = citations.length > maxDisplay

  // 格式化作者显示
  const formatAuthors = (authors: string[]) => {
    if (!authors || authors.length === 0) return '未知作者'
    if (authors.length <= 2) return authors.join(', ')
    return `${authors[0]} et al.`
  }

  // 打开文献详情
  const openCitationDetail = (citation: Citation) => {
    setSelectedCitation(citation)
  }

  // 关闭详情弹窗
  const closeDetail = () => {
    setSelectedCitation(null)
  }

  // 跳转到文献源
  const navigateToSource = (citation: Citation) => {
    if (citation.url) {
      window.open(citation.url, '_blank')
    } else if (citation.doi) {
      window.open(`https://doi.org/${citation.doi}`, '_blank')
    }
  }

  // 复制引用格式
  const copyCitation = (citation: Citation, format: 'apa' | 'gb' = 'apa') => {
    let citationText = ''
    if (format === 'apa') {
      citationText = `${formatAuthors(citation.authors)} (${citation.year}). ${citation.title}. ${citation.journal || ''}.`
      if (citation.doi) citationText += ` https://doi.org/${citation.doi}`
    } else {
      citationText = `[${citation.authors.join(', ')}. ${citation.title}[J]. ${citation.journal || ''}, ${citation.year || ''}.]`
    }

    navigator.clipboard.writeText(citationText)
    // message.success('引用已复制') // 需要在组件外处理
  }

  if (!citations || citations.length === 0) {
    return null
  }

  return (
    <div className={styles.citationCards}>
      <List
        grid={{ gutter: 8, xs: 1, sm: 1, md: 1, lg: 1, xl: 1, xxl: 1 }}
        dataSource={displayCitations}
        renderItem={(citation, index) => (
          <List.Item className={styles.citationItem}>
            <Card
              size="small"
              className={styles.citationCard}
              onClick={() => openCitationDetail(citation)}
              hoverable
            >
              <div className={styles.citationHeader}>
                <Tag color="blue" className={styles.citationIndex}>
                  [{index + 1}]
                </Tag>
                <Text className={styles.citationTitle} ellipsis={{ tooltip: true }}>
                  {citation.title}
                </Text>
              </div>

              <div className={styles.citationMeta}>
                <Space size="small" wrap>
                  {citation.authors && citation.authors.length > 0 && (
                    <Tooltip title={citation.authors.join(', ')}>
                      <span className={styles.metaItem}>
                        <UserOutlined /> {formatAuthors(citation.authors)}
                      </span>
                    </Tooltip>
                  )}
                  {citation.year && (
                    <span className={styles.metaItem}>
                      <CalendarOutlined /> {citation.year}
                    </span>
                  )}
                  {(citation.relevance_score ?? 0) > 0 && (
                    <Tag
                      color={
                        (citation.relevance_score ?? 0) > 0.8
                          ? 'green'
                          : (citation.relevance_score ?? 0) > 0.6
                          ? 'blue'
                          : 'default'
                      }
                      className={styles.relevanceTag}
                    >
                      相关度: {((citation.relevance_score ?? 0) * 100).toFixed(0)}%
                    </Tag>
                  )}
                </Space>
              </div>

              {citation.snippet && (
                <Paragraph
                  className={styles.citationSnippet}
                  ellipsis={{ rows: 2, expandable: false }}
                >
                  "{citation.snippet}"
                </Paragraph>
              )}
            </Card>
          </List.Item>
        )}
      />

      {showExpand && hasMore && (
        <div className={styles.expandButton}>
          <Button type="link" onClick={() => setExpanded(!expanded)}>
            {expanded
              ? '收起引用'
              : `查看全部 ${citations.length} 条引用`}
          </Button>
        </div>
      )}

      {/* 文献详情弹窗 */}
      <Modal
        title="文献详情"
        open={!!selectedCitation}
        onCancel={closeDetail}
        footer={[
          <Button key="copy" onClick={() => selectedCitation && copyCitation(selectedCitation, 'apa')}>
            复制APA格式
          </Button>,
          <Button key="copy-gb" onClick={() => selectedCitation && copyCitation(selectedCitation, 'gb')}>
            复制GB格式
          </Button>,
          <Button
            key="open"
            type="primary"
            icon={<LinkOutlined />}
            onClick={() => selectedCitation && navigateToSource(selectedCitation)}
            disabled={!selectedCitation?.url && !selectedCitation?.doi}
          >
            查看原文
          </Button>,
        ]}
        width={700}
      >
        {selectedCitation && (
          <div className={styles.citationDetail}>
            <Title level={4}>{selectedCitation.title}</Title>

            <Space direction="vertical" className={styles.detailMeta}>
              <Text>
                <UserOutlined /> <strong>作者:</strong>{' '}
                {selectedCitation.authors?.join(', ') || '未知'}
              </Text>

              {selectedCitation.year && (
                <Text>
                  <CalendarOutlined /> <strong>年份:</strong> {selectedCitation.year}
                </Text>
              )}

              {selectedCitation.journal && (
                <Text>
                  <BookOutlined /> <strong>期刊:</strong> {selectedCitation.journal}
                </Text>
              )}

              {selectedCitation.doi && (
                <Text>
                  <LinkOutlined /> <strong>DOI:</strong>{' '}
                  <a
                    href={`https://doi.org/${selectedCitation.doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {selectedCitation.doi}
                  </a>
                </Text>
              )}

              {(selectedCitation.relevance_score ?? 0) > 0 && (
                <Text>
                  <strong>相关度:</strong>{' '}
                  <Tag
                    color={
                      (selectedCitation.relevance_score ?? 0) > 0.8
                        ? 'green'
                        : (selectedCitation.relevance_score ?? 0) > 0.6
                        ? 'blue'
                        : 'default'
                    }
                  >
                    {((selectedCitation.relevance_score ?? 0) * 100).toFixed(1)}%
                  </Tag>
                </Text>
              )}
            </Space>

            {selectedCitation.snippet && (
              <div className={styles.detailSnippet}>
                <Text strong>引用片段:</Text>
                <blockquote className={styles.blockquote}>
                  {selectedCitation.snippet}
                </blockquote>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default CitationCards
