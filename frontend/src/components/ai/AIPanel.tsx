/**
 * AI 助手面板组件
 * 集成写作助手、引用建议、智能摘要功能
 */

import React, { useState, useRef, useCallback } from 'react'
import { Layout, Input, Button, Space, message, Card, Typography, Tabs, Spin } from 'antd'
import {
  CopyOutlined,
  CloseOutlined,
  RobotOutlined,
  EditOutlined,
  TranslationOutlined,
  BookOutlined,
  FileTextOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'

import { aiService } from '@/services'
import { useUIStore, usePaperStore } from '@/stores'
import type { WritingTaskType } from '@/types'
import ReferenceSuggestions from './ReferenceSuggestions'
import SummaryPanel from './SummaryPanel'
import LogicCheckPanel from './LogicCheckPanel'
import styles from './AIPanel.module.css'

const { Sider } = Layout
const { TextArea } = Input
const { Text, Paragraph } = Typography

const AIPanel: React.FC = () => {
  const { setAIPanelVisible, aiPanelWidth } = useUIStore()
  const { currentPaper } = usePaperStore()

  const [activeTab, setActiveTab] = useState('writing')
  const [inputText, setInputText] = useState('')
  const [outputText, setOutputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<(() => void) | null>(null)

  const handleWritingTask = useCallback(async (taskType: WritingTaskType) => {
    if (!inputText.trim()) {
      message.warning('请输入文本')
      return
    }

    setLoading(true)
    setOutputText('')
    setIsStreaming(true)

    try {
      // 使用流式响应
      abortRef.current = aiService.writingStream(
        {
          taskType,
          text: inputText,
          context: currentPaper?.abstract || undefined,
          targetLanguage: taskType === 'translate' ? 'en' : undefined,
        },
        (chunk) => {
          setOutputText((prev) => prev + chunk)
        },
        (fullText) => {
          setLoading(false)
          setIsStreaming(false)
          setOutputText(fullText)
        },
        (error) => {
          setLoading(false)
          setIsStreaming(false)
          message.error(`请求失败: ${error.message}`)
        }
      )
    } catch {
      setLoading(false)
      setIsStreaming(false)
      message.error('请求失败')
    }
  }, [inputText, currentPaper?.abstract])

  const handleStopStream = useCallback(() => {
    if (abortRef.current) {
      abortRef.current()
      abortRef.current = null
      setIsStreaming(false)
      setLoading(false)
    }
  }, [])

  const handleCopy = () => {
    navigator.clipboard.writeText(outputText)
    message.success('已复制到剪贴板')
  }

  const handleClear = () => {
    setInputText('')
    setOutputText('')
  }

  const tabItems = [
    {
      key: 'writing',
      label: (
        <span>
          <EditOutlined />
          写作助手
        </span>
      ),
      children: (
        <div className={styles.tabContent}>
          <div className={styles.section}>
            <Text type="secondary">输入文本</Text>
            <TextArea
              rows={4}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="在此输入需要处理的文本..."
              style={{ marginTop: 8 }}
            />
          </div>

          <Space wrap style={{ marginBottom: 16, marginTop: 8 }}>
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleWritingTask('continue')}
              loading={loading && !isStreaming}
              disabled={isStreaming}
            >
              续写
            </Button>
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleWritingTask('polish')}
              loading={loading && !isStreaming}
              disabled={isStreaming}
            >
              润色
            </Button>
            <Button
              size="small"
              icon={<TranslationOutlined />}
              onClick={() => handleWritingTask('translate')}
              loading={loading && !isStreaming}
              disabled={isStreaming}
            >
              翻译
            </Button>
            <Button
              size="small"
              icon={<ReloadOutlined />}
              onClick={() => handleWritingTask('rewrite')}
              loading={loading && !isStreaming}
              disabled={isStreaming}
            >
              重写
            </Button>
          </Space>

          {isStreaming && (
            <Button size="small" danger onClick={handleStopStream}>
              停止生成
            </Button>
          )}

          {(outputText || loading) && (
            <div className={styles.section}>
              <div className={styles.outputHeader}>
                <Text type="secondary">
                  AI 生成结果
                  {isStreaming && <Spin size="small" style={{ marginLeft: 8 }} />}
                </Text>
                <Space>
                  <Button type="text" size="small" onClick={handleClear}>
                    清空
                  </Button>
                  <Button type="text" size="small" icon={<CopyOutlined />} onClick={handleCopy}>
                    复制
                  </Button>
                </Space>
              </div>
              <Card size="small" className={styles.outputCard}>
                <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {outputText}
                  {isStreaming && <span className={styles.cursor}>|</span>}
                </Paragraph>
              </Card>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'references',
      label: (
        <span>
          <BookOutlined />
          引用建议
        </span>
      ),
      children: (
        <ReferenceSuggestions
          paperId={currentPaper?.id}
          onInsert={(ref) => {
            // TODO: 添加到论文引用列表
            message.success(`已添加引用: ${ref.title}`)
          }}
        />
      ),
    },
    {
      key: 'summary',
      label: (
        <span>
          <FileTextOutlined />
          智能摘要
        </span>
      ),
      children: currentPaper ? (
        <SummaryPanel
          paperId={currentPaper.id}
          paperTitle={currentPaper.title}
          onApply={(_summary, _keywords) => {
            // TODO: 应用到论文摘要
            message.success('摘要已应用')
          }}
        />
      ) : (
        <div className={styles.emptyState}>
          <Text type="secondary">请先选择一篇论文</Text>
        </div>
      ),
    },
    {
      key: 'logic',
      label: (
        <span>
          <CheckCircleOutlined />
          逻辑检查
        </span>
      ),
      children: (
        <div className={styles.tabContent}>
          <div className={styles.section}>
            <Text type="secondary">输入需要检查的文本</Text>
            <TextArea
              rows={4}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="在此输入需要检查逻辑的文本..."
              style={{ marginTop: 8 }}
            />
          </div>
          <LogicCheckPanel
            text={inputText}
            onApplySuggestion={(original, suggestion) => {
              // 替换文本
              const newText = inputText.replace(original, suggestion)
              setInputText(newText)
            }}
          />
        </div>
      ),
    },
  ]

  return (
    <Sider width={aiPanelWidth} className={styles.panel} theme="light">
      <div className={styles.header}>
        <Space>
          <RobotOutlined style={{ fontSize: 18, color: '#1890ff' }} />
          <span className={styles.title}>AI 助手</span>
        </Space>
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={() => setAIPanelVisible(false)}
        />
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        className={styles.tabs}
        size="small"
      />

      <div className={styles.footer}>
        <Text type="secondary" style={{ fontSize: 11 }}>
          由 GPT-4 / Claude 提供支持
        </Text>
      </div>
    </Sider>
  )
}

export default AIPanel
