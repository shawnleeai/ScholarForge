/**
 * 逻辑检查面板组件
 * 分析文本的逻辑连贯性，提供改进建议
 */

import React, { useState, useCallback } from 'react'
import { Card, Button, Space, Typography, List, Tag, Spin, Empty, message, Tooltip, Progress } from 'antd'
import {
  CheckCircleOutlined,
  WarningOutlined,
  BulbOutlined,
  SyncOutlined,
  CopyOutlined,
  CheckOutlined,
} from '@ant-design/icons'

import { aiService } from '@/services'
import styles from './AIPanel.module.css'

const { Text, Paragraph } = Typography

interface LogicIssue {
  type: 'error' | 'warning' | 'suggestion'
  message: string
  position?: { start: number; end: number }
  suggestion?: string
}

interface LogicCheckResult {
  score: number
  issues: LogicIssue[]
  summary: string
}

interface LogicCheckPanelProps {
  text: string
  onApplySuggestion?: (original: string, suggestion: string) => void
}

const LogicCheckPanel: React.FC<LogicCheckPanelProps> = ({ text, onApplySuggestion }) => {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<LogicCheckResult | null>(null)

  const handleCheck = useCallback(async () => {
    if (!text.trim()) {
      message.warning('请输入需要检查的文本')
      return
    }

    setLoading(true)
    try {
      const response = await aiService.checkLogic({
        text,
        language: 'zh',
      })

      // 解析返回结果
      const data = response.data as Record<string, unknown>
      setResult({
        score: (data.score as number) || 0.8,
        issues: (data.issues as LogicIssue[]) || [],
        summary: (data.summary as string) || (data.analysis as string) || '',
      })
    } catch (error) {
      message.error('逻辑检查失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }, [text])

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#52c41a'
    if (score >= 0.6) return '#faad14'
    return '#ff4d4f'
  }

  const getIssueIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <WarningOutlined style={{ color: '#ff4d4f' }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />
      case 'suggestion':
        return <BulbOutlined style={{ color: '#1890ff' }} />
      default:
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
    }
  }

  const getIssueTag = (type: string) => {
    const colors: Record<string, string> = {
      error: 'error',
      warning: 'warning',
      suggestion: 'processing',
    }
    const labels: Record<string, string> = {
      error: '错误',
      warning: '警告',
      suggestion: '建议',
    }
    return <Tag color={colors[type] || 'default'}>{labels[type] || type}</Tag>
  }

  const handleCopySuggestion = (suggestion: string) => {
    navigator.clipboard.writeText(suggestion)
    message.success('已复制建议')
  }

  const handleApplySuggestion = (issue: LogicIssue) => {
    if (issue.suggestion && onApplySuggestion) {
      onApplySuggestion(text.substring(issue.position?.start || 0, issue.position?.end || text.length), issue.suggestion)
      message.success('已应用建议')
    }
  }

  return (
    <div className={styles.logicCheckPanel}>
      <div className={styles.checkHeader}>
        <Button
          type="primary"
          icon={<SyncOutlined spin={loading} />}
          onClick={handleCheck}
          loading={loading}
        >
          {loading ? '检查中...' : '开始检查'}
        </Button>
      </div>

      {loading && (
        <div className={styles.loadingContainer}>
          <Spin size="large" />
          <Text type="secondary" style={{ marginTop: 16 }}>
            正在分析文本逻辑...
          </Text>
        </div>
      )}

      {!loading && !result && (
        <Empty
          description="点击上方按钮开始逻辑检查"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      )}

      {result && !loading && (
        <div className={styles.resultContainer}>
          {/* 评分 */}
          <Card size="small" className={styles.scoreCard}>
            <div className={styles.scoreSection}>
              <Text strong>逻辑评分</Text>
              <Progress
                type="circle"
                percent={Math.round(result.score * 100)}
                strokeColor={getScoreColor(result.score)}
                format={(percent) => (
                  <span style={{ color: getScoreColor(result.score), fontSize: 20, fontWeight: 'bold' }}>
                    {percent}
                  </span>
                )}
                width={80}
              />
            </div>
          </Card>

          {/* 总体评价 */}
          {result.summary && (
            <Card size="small" title="总体评价" className={styles.summaryCard}>
              <Paragraph style={{ margin: 0 }}>{result.summary}</Paragraph>
            </Card>
          )}

          {/* 问题列表 */}
          {result.issues.length > 0 && (
            <Card size="small" title={`发现 ${result.issues.length} 个问题`} className={styles.issuesCard}>
              <List
                dataSource={result.issues}
                renderItem={(issue) => (
                  <List.Item className={styles.issueItem}>
                    <div className={styles.issueContent}>
                      <div className={styles.issueHeader}>
                        {getIssueIcon(issue.type)}
                        {getIssueTag(issue.type)}
                      </div>
                      <Paragraph style={{ margin: '8px 0' }}>{issue.message}</Paragraph>
                      {issue.suggestion && (
                        <div className={styles.suggestionBox}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            修改建议：
                          </Text>
                          <Paragraph
                            style={{
                              margin: '4px 0',
                              padding: 8,
                              background: '#f6ffed',
                              borderRadius: 4,
                              border: '1px solid #b7eb8f',
                            }}
                          >
                            {issue.suggestion}
                          </Paragraph>
                          <Space>
                            <Tooltip title="复制建议">
                              <Button
                                type="text"
                                size="small"
                                icon={<CopyOutlined />}
                                onClick={() => handleCopySuggestion(issue.suggestion || '')}
                              />
                            </Tooltip>
                            {onApplySuggestion && (
                              <Tooltip title="应用建议">
                                <Button
                                  type="text"
                                  size="small"
                                  icon={<CheckOutlined />}
                                  onClick={() => handleApplySuggestion(issue)}
                                />
                              </Tooltip>
                            )}
                          </Space>
                        </div>
                      )}
                    </div>
                  </List.Item>
                )}
              />
            </Card>
          )}

          {result.issues.length === 0 && (
            <div className={styles.noIssues}>
              <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              <Text>未发现明显的逻辑问题</Text>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default LogicCheckPanel
