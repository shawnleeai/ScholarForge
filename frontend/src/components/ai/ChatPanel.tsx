/**
 * AI 对话组件
 * 支持消息列表、输入框、流式响应显示
 */

import React, { useState, useRef, useCallback, useEffect } from 'react'
import {
  Input,
  Button,
  Space,
  message,
  Card,
  Typography,
  List,
  Avatar,
  Spin,
  Tag,
  Tooltip,
  Badge,
  Empty,
  Skeleton,
} from 'antd'
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  CopyOutlined,
  LikeOutlined,
  DislikeOutlined,
  SyncOutlined,
  BookOutlined,
  StopOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './ChatPanel.module.css'
import CitationCards from './CitationCards'
import type { Citation } from '@/types'

// 是否使用模拟模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// Mock响应生成器
const mockChatResponse = (question: string): string => {
  const responses: Record<string, string> = {
    '深度学习': `深度学习在项目管理中有以下主要应用：

1. **任务预测与分配**：利用LSTM等时序模型预测任务完成时间，优化资源分配
2. **风险识别**：通过神经网络分析历史项目数据，识别潜在风险因素
3. **进度优化**：基于强化学习自动调整项目计划，优化关键路径
4. **质量控制**：使用CNN检测文档和代码中的潜在问题

研究表明，引入AI辅助后，项目延期率可降低30-40%。`,

    '总结': `这篇论文的主要贡献包括：

1. **提出了新的理论框架**：构建了xxx的理论模型，填补了该领域的研究空白
2. **开发了创新方法**：设计了基于深度学习的算法，准确率较现有方法提升15%
3. **实证验证**：通过大规模实验验证了方法的有效性
4. **应用价值**：为实际应用提供了可行的解决方案`,

    '优势': `与其他方法相比，该方法具有以下优势：

| 维度 | 本方法 | 传统方法 |
|------|--------|----------|
| 准确率 | 95% | 82% |
| 处理速度 | 快 | 较慢 |
| 可解释性 | 强 | 一般 |
| 适用范围 | 广 | 有限 |

主要优势在于：
- 采用了端到端的学习架构
- 引入了注意力机制捕捉关键特征
- 支持多模态数据融合`,

    'default': `关于"${question}"，根据学术研究的最佳实践：

这是一个值得深入探索的研究方向。建议您：

1. **文献调研**：查阅近3-5年的顶级会议和期刊论文
2. **方法对比**：与现有的SOTA方法进行系统对比
3. **实验设计**：设计全面的评估指标和对比实验
4. **理论分析**：从理论上分析方法的收敛性和复杂度

如需更具体的建议，请提供更多上下文信息。`
  }

  for (const [key, response] of Object.entries(responses)) {
    if (question.includes(key)) {
      return response
    }
  }
  return responses['default']
}

const { TextArea } = Input
const { Text, Paragraph } = Typography

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  type?: 'text' | 'citation' | 'error' | 'streaming'
  citations?: Citation[]
  timestamp: Date
  isStreaming?: boolean
  metadata?: {
    retrievalInfo?: {
      retrievedCount: number
      contextTokens: number
      retrievalTimeMs: number
    }
    generationTimeMs?: number
    model?: string
  }
}

interface ChatPanelProps {
  conversationId?: string
  paperId?: string
  articleIds?: string[]
  height?: number | string
  onSendMessage?: (content: string) => void
  placeholder?: string
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  conversationId,
  paperId,
  articleIds,
  height = '100%',
  onSendMessage,
  placeholder = '输入您的问题，AI将基于您的文献库回答...',
}) => {
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentStreamingContent, setCurrentStreamingContent] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const queryClient = useQueryClient()

  // 自动滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentStreamingContent, scrollToBottom])

  // 加载历史消息
  useEffect(() => {
    if (conversationId) {
      loadHistoryMessages()
    }
  }, [conversationId])

  const loadHistoryMessages = async () => {
    try {
      const response = await fetch(
        `/api/v1/ai/chat/${conversationId}/messages?limit=100`
      )
      const data = await response.json()
      if (data.success) {
        const historyMessages: ChatMessage[] = data.data.messages.map(
          (msg: any) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            type: msg.type,
            citations: msg.citations,
            timestamp: new Date(msg.created_at),
            metadata: msg.metadata,
          })
        )
        setMessages(historyMessages)
      }
    } catch (error) {
      console.error('加载历史消息失败:', error)
    }
  }

  // 发送消息
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return

      // 创建用户消息
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMessage])
      setInputValue('')
      setIsStreaming(true)
      setCurrentStreamingContent('')

      // 回调
      onSendMessage?.(content)

      // Mock模式：模拟流式响应
      if (USE_MOCK) {
        const mockText = mockChatResponse(content)
        const chars = mockText.split('')
        let index = 0

        let fullContent = ''
        const streamInterval = setInterval(() => {
          if (index < chars.length) {
            fullContent += chars[index]
            setCurrentStreamingContent(fullContent)
            index++
          } else {
            clearInterval(streamInterval)
            setIsStreaming(false)
            setCurrentStreamingContent('')

            // 添加AI回复
            const assistantMessage: ChatMessage = {
              id: (Date.now() + 1).toString(),
              role: 'assistant',
              content: fullContent,
              type: 'text',
              citations: [],
              timestamp: new Date(),
              metadata: {
                generationTimeMs: 1200,
              },
            }
            setMessages((prev) => [...prev, assistantMessage])
          }
        }, 30)

        // 保存清理函数
        abortControllerRef.current = {
          abort: () => {
            clearInterval(streamInterval)
            setIsStreaming(false)
          },
        } as AbortController

        return
      }

      try {
        // 创建 AbortController
        abortControllerRef.current = new AbortController()

        // 构建请求URL
        let url = '/api/v1/ai/chat'
        if (conversationId) {
          url = `/api/v1/ai/chat/${conversationId}/message`
        }
        url += `?content=${encodeURIComponent(content)}&use_rag=true&stream=true`

        const response = await fetch(url, {
          method: 'POST',
          signal: abortControllerRef.current.signal,
        })

        if (!response.ok) {
          throw new Error('发送消息失败')
        }

        const reader = response.body?.getReader()
        const decoder = new TextDecoder()
        let fullContent = ''
        let citations: Citation[] = []
        let metadata: any = {}

        if (reader) {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            const chunk = decoder.decode(value)
            const lines = chunk.split('\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6)
                if (data === '[DONE]') {
                  setIsStreaming(false)
                  break
                }

                try {
                  const parsed = JSON.parse(data)
                  if (parsed.chunk) {
                    fullContent += parsed.chunk
                    setCurrentStreamingContent(fullContent)
                  }
                  if (parsed.citations) {
                    citations = parsed.citations
                  }
                  if (parsed.is_final) {
                    metadata = {
                      retrievalInfo: parsed.retrieval_info,
                      generationTimeMs: parsed.generation_time_ms,
                    }
                  }
                } catch (e) {
                  // 忽略解析错误
                }
              }
            }
          }
        }

        // 添加AI回复
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: fullContent,
          type: citations.length > 0 ? 'citation' : 'text',
          citations,
          timestamp: new Date(),
          metadata,
        }

        setMessages((prev) => [...prev, assistantMessage])
        setCurrentStreamingContent('')

        // 刷新会话列表
        queryClient.invalidateQueries({ queryKey: ['conversations'] })
      } catch (error: any) {
        if (error.name === 'AbortError') {
          message.info('已停止生成')
        } else {
          message.error('发送消息失败: ' + error.message)
          // 添加错误消息
          const errorMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: '抱歉，生成回复时出错，请稍后重试。',
            type: 'error',
            timestamp: new Date(),
          }
          setMessages((prev) => [...prev, errorMessage])
        }
      } finally {
        setIsStreaming(false)
        abortControllerRef.current = null
      }
    },
    [conversationId, isStreaming, onSendMessage, queryClient]
  )

  // 停止生成
  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsStreaming(false)
    }
  }, [])

  // 复制消息内容
  const copyMessage = useCallback((content: string) => {
    navigator.clipboard.writeText(content)
    message.success('已复制到剪贴板')
  }, [])

  // 重新生成
  const regenerateMessage = useCallback(async (messageId: string) => {
    // 找到对应的用户消息
    const messageIndex = messages.findIndex((m) => m.id === messageId)
    if (messageIndex <= 0) return

    const userMessage = messages[messageIndex - 1]
    if (userMessage.role !== 'user') return

    // 删除AI回复及之后的所有消息
    setMessages((prev) => prev.slice(0, messageIndex))

    // 重新发送
    await sendMessage(userMessage.content)
  }, [messages, sendMessage])

  // 渲染消息内容
  const renderMessageContent = (msg: ChatMessage) => {
    if (msg.isStreaming) {
      return (
        <div className={styles.streamingContent}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {currentStreamingContent}
          </ReactMarkdown>
          <span className={styles.cursor}>▊</span>
        </div>
      )
    }

    return (
      <div className={styles.messageContent}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, inline, className, children, ...props }: any) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              )
            },
          }}
        >
          {msg.content}
        </ReactMarkdown>

        {msg.citations && msg.citations.length > 0 && (
          <div className={styles.citationsSection}>
            <Text type="secondary" className={styles.citationsTitle}>
              <BookOutlined /> 参考来源
            </Text>
            <CitationCards citations={msg.citations} />
          </div>
        )}
      </div>
    )
  }

  // 渲染消息元信息
  const renderMessageMeta = (msg: ChatMessage) => {
    if (!msg.metadata) return null

    return (
      <div className={styles.messageMeta}>
        {msg.metadata.retrievalInfo && (
          <Tooltip
            title={`检索了 ${msg.metadata.retrievalInfo.retrievedCount} 篇文献，上下文 ${msg.metadata.retrievalInfo.contextTokens} tokens，检索耗时 ${msg.metadata.retrievalInfo.retrievalTimeMs}ms`}
          >
            <Tag className={styles.metaTag}>
              <BookOutlined /> {msg.metadata.retrievalInfo.retrievedCount} 文献
            </Tag>
          </Tooltip>
        )}
        {msg.metadata.generationTimeMs && (
          <Tag className={styles.metaTag}>
            {msg.metadata.generationTimeMs}ms
          </Tag>
        )}
      </div>
    )
  }

  return (
    <div className={styles.chatPanel} style={{ height }}>
      {/* 消息列表 */}
      <div className={styles.messageList}>
        {messages.length === 0 ? (
          <Empty
            description="开始一个对话吧"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            className={styles.emptyState}
          >
            <Space direction="vertical" className={styles.suggestions}>
              <Text type="secondary">你可以问：</Text>
              <Button
                type="link"
                onClick={() =>
                  sendMessage('深度学习在项目管理中有哪些应用？')
                }
              >
                深度学习在项目管理中有哪些应用？
              </Button>
              <Button
                type="link"
                onClick={() =>
                  sendMessage('总结一下这篇论文的主要贡献')
                }
              >
                总结一下这篇论文的主要贡献
              </Button>
              <Button
                type="link"
                onClick={() =>
                  sendMessage('这个方法与其他方法相比有什么优势？')
                }
              >
                这个方法与其他方法相比有什么优势？
              </Button>
            </Space>
          </Empty>
        ) : (
          <List
            dataSource={messages}
            renderItem={(msg) => (
              <List.Item
                className={`${styles.messageItem} ${
                  msg.role === 'user' ? styles.userMessage : styles.aiMessage
                }`}
              >
                <div className={styles.messageWrapper}>
                  <Avatar
                    icon={
                      msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />
                    }
                    className={
                      msg.role === 'user'
                        ? styles.userAvatar
                        : styles.aiAvatar
                    }
                  />
                  <div className={styles.messageBody}>
                    <Card
                      size="small"
                      className={styles.messageCard}
                      bordered={false}
                    >
                      {renderMessageContent(msg)}
                    </Card>

                    {/* 消息操作 */}
                    {msg.role === 'assistant' && !msg.isStreaming && (
                      <div className={styles.messageActions}>
                        <Space size="small">
                          <Tooltip title="复制">
                            <Button
                              type="text"
                              size="small"
                              icon={<CopyOutlined />}
                              onClick={() => copyMessage(msg.content)}
                            />
                          </Tooltip>
                          <Tooltip title="重新生成">
                            <Button
                              type="text"
                              size="small"
                              icon={<SyncOutlined />}
                              onClick={() => regenerateMessage(msg.id)}
                            />
                          </Tooltip>
                          <Tooltip title="有用">
                            <Button
                              type="text"
                              size="small"
                              icon={<LikeOutlined />}
                            />
                          </Tooltip>
                          <Tooltip title="无用">
                            <Button
                              type="text"
                              size="small"
                              icon={<DislikeOutlined />}
                            />
                          </Tooltip>
                        </Space>
                        {renderMessageMeta(msg)}
                      </div>
                    )}
                  </div>
                </div>
              </List.Item>
            )}
          />
        )}

        {/* 流式响应显示 */}
        {isStreaming && currentStreamingContent && (
          <List.Item className={`${styles.messageItem} ${styles.aiMessage}`}>
            <div className={styles.messageWrapper}>
              <Avatar icon={<RobotOutlined />} className={styles.aiAvatar} />
              <div className={styles.messageBody}>
                <Card size="small" className={styles.messageCard} bordered={false}>
                  <div className={styles.streamingContent}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {currentStreamingContent}
                    </ReactMarkdown>
                    <span className={styles.cursor}>▊</span>
                  </div>
                </Card>
              </div>
            </div>
          </List.Item>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className={styles.inputArea}>
        <div className={styles.inputWrapper}>
          <TextArea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={placeholder}
            autoSize={{ minRows: 1, maxRows: 6 }}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault()
                sendMessage(inputValue)
              }
            }}
            disabled={isStreaming}
            className={styles.input}
          />
          <div className={styles.inputActions}>
            {isStreaming ? (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={stopGeneration}
                className={styles.stopButton}
              >
                停止
              </Button>
            ) : (
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={() => sendMessage(inputValue)}
                disabled={!inputValue.trim()}
                className={styles.sendButton}
              >
                发送
              </Button>
            )}
          </div>
        </div>
        <Text type="secondary" className={styles.inputHint}>
          Enter 发送，Shift + Enter 换行
        </Text>
      </div>
    </div>
  )
}

export default ChatPanel
