/**
 * 智能摘要面板组件
 */

import React, { useState } from 'react'
import { Card, Button, Typography, Space, Tag, Spin, message, List, Checkbox, Divider } from 'antd'
import {
  FileTextOutlined,
  CopyOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'

import { aiService, type SummaryResponse } from '@/services/aiService'
import styles from './AIComponents.module.css'

const { Text, Paragraph } = Typography

interface SummaryPanelProps {
  paperId: string
  paperTitle?: string
  onApply?: (summary: string, keywords: string[]) => void
}

const SummaryPanel: React.FC<SummaryPanelProps> = ({
  paperId,
  paperTitle,
  onApply,
}) => {
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [options, setOptions] = useState({
    includeKeywords: true,
    includeMainPoints: true,
  })

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const response = await aiService.generateSummary({
        paperId,
        maxLength: 300,
        includeKeywords: options.includeKeywords,
      })
      setSummary(response.data)
      message.success('摘要生成完成')
    } catch {
      message.error('生成摘要失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (!summary) return

    let text = summary.summary
    if (options.includeKeywords && summary.keywords.length > 0) {
      text += `\n\n关键词：${summary.keywords.join('、')}`
    }
    if (options.includeMainPoints && summary.mainPoints.length > 0) {
      text += '\n\n主要观点：\n' + summary.mainPoints.map((p, i) => `${i + 1}. ${p}`).join('\n')
    }

    navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  }

  const handleApply = () => {
    if (summary && onApply) {
      onApply(summary.summary, summary.keywords)
      message.success('已应用到论文')
    }
  }

  return (
    <div className={styles.summaryPanel}>
      <div className={styles.header}>
        <Text type="secondary">
          <FileTextOutlined style={{ marginRight: 8 }} />
          {paperTitle || '论文摘要生成'}
        </Text>
      </div>

      <div className={styles.options}>
        <Checkbox
          checked={options.includeKeywords}
          onChange={(e) => setOptions({ ...options, includeKeywords: e.target.checked })}
        >
          包含关键词
        </Checkbox>
        <Checkbox
          checked={options.includeMainPoints}
          onChange={(e) => setOptions({ ...options, includeMainPoints: e.target.checked })}
        >
          包含主要观点
        </Checkbox>
      </div>

      <Button
        type="primary"
        icon={<FileTextOutlined />}
        onClick={handleGenerate}
        loading={loading}
        block
      >
        生成智能摘要
      </Button>

      {loading && (
        <div className={styles.loadingContainer}>
          <Spin tip="正在分析论文内容..." />
        </div>
      )}

      {summary && !loading && (
        <div className={styles.resultSection}>
          <Divider>生成结果</Divider>

          <Card size="small" className={styles.summaryCard}>
            <div className={styles.summaryHeader}>
              <Text strong>摘要</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {summary.wordCount} 字
              </Text>
            </div>
            <Paragraph style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>
              {summary.summary}
            </Paragraph>
          </Card>

          {options.includeKeywords && summary.keywords.length > 0 && (
            <div className={styles.keywordsSection}>
              <Text type="secondary">关键词：</Text>
              <Space wrap size={[4, 4]}>
                {summary.keywords.map((keyword, index) => (
                  <Tag key={index} color="blue">
                    {keyword}
                  </Tag>
                ))}
              </Space>
            </div>
          )}

          {options.includeMainPoints && summary.mainPoints.length > 0 && (
            <div className={styles.mainPointsSection}>
              <Text type="secondary">主要观点：</Text>
              <List
                size="small"
                dataSource={summary.mainPoints}
                renderItem={(point) => (
                  <List.Item className={styles.mainPointItem}>
                    <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                    <Text>{point}</Text>
                  </List.Item>
                )}
              />
            </div>
          )}

          <div className={styles.actions}>
            <Button icon={<ReloadOutlined />} onClick={handleGenerate}>
              重新生成
            </Button>
            <Button icon={<CopyOutlined />} onClick={handleCopy}>
              复制
            </Button>
            {onApply && (
              <Button type="primary" onClick={handleApply}>
                应用到论文
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default SummaryPanel
