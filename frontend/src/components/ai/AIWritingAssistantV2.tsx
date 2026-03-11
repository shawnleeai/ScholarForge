/**
 * AI写作助手2.0
 * 增强版智能写作助手，集成多种AI功能
 */

import React, { useState, useRef, useEffect } from 'react'
import {
  Card,
  Button,
  Input,
  Space,
  Typography,
  Tabs,
  List,
  Tag,
  Divider,
  Alert,
  Badge,
  Tooltip,
  message,
  Empty,
  Spin,
  Drawer,
  Popover,
  Progress,
  Segmented,
  Modal
} from 'antd'
import {
  RobotOutlined,
  SendOutlined,
  EditOutlined,
  FormatPainterOutlined,
  BookOutlined,
  BulbOutlined,
  CheckCircleOutlined,
  CopyOutlined,
  ReloadOutlined,
  HistoryOutlined,
  SettingOutlined,
  CloseOutlined,
  ExpandOutlined,
  CompressOutlined,
  TranslationOutlined,
  FileSearchOutlined,
  HighlightOutlined
} from '@ant-design/icons'
import { aiService } from '@/services/aiService'
import styles from './AIWritingAssistantV2.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { TabPane } = Tabs

// 写作模式
type WritingMode = 'chat' | 'polish' | 'expand' | 'condense' | 'translate' | 'reference' | 'check'

// 消息类型
interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  type?: 'text' | 'suggestion' | 'citation' | 'warning'
  timestamp: Date
  actions?: { label: string; action: () => void }[]
}

// AI功能模块
interface AIFeature {
  key: WritingMode
  label: string
  icon: React.ReactNode
  description: string
  placeholder: string
}

const features: AIFeature[] = [
  {
    key: 'chat',
    label: '对话',
    icon: <RobotOutlined />,
    description: '与AI助手自由对话，获取写作建议',
    placeholder: '输入你的问题，例如：如何改进这段话的逻辑？'
  },
  {
    key: 'polish',
    label: '润色',
    icon: <FormatPainterOutlined />,
    description: '优化语言表达，提升学术规范性',
    placeholder: '输入需要润色的段落...'
  },
  {
    key: 'expand',
    label: '扩写',
    icon: <ExpandOutlined />,
    description: '扩展思路，丰富内容细节',
    placeholder: '输入需要扩展的要点...'
  },
  {
    key: 'condense',
    label: '精简',
    icon: <CompressOutlined />,
    description: '精简冗余内容，突出重点',
    placeholder: '输入需要精简的段落...'
  },
  {
    key: 'translate',
    label: '翻译',
    icon: <TranslationOutlined />,
    description: '中英互译，保持学术风格',
    placeholder: '输入需要翻译的内容...'
  },
  {
    key: 'reference',
    label: '引用',
    icon: <BookOutlined />,
    description: '查找相关文献，生成引用',
    placeholder: '输入研究主题或关键词...'
  },
  {
    key: 'check',
    label: '检查',
    icon: <CheckCircleOutlined />,
    description: '检查逻辑、语法、格式问题',
    placeholder: '输入需要检查的段落...'
  }
]

interface AIWritingAssistantV2Props {
  paperId?: string
  currentContent?: string
  onInsertContent?: (content: string) => void
  onReplaceContent?: (oldContent: string, newContent: string) => void
}

const AIWritingAssistantV2: React.FC<AIWritingAssistantV2Props> = ({
  paperId,
  currentContent,
  onInsertContent,
  onReplaceContent
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [activeMode, setActiveMode] = useState<WritingMode>('chat')
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '你好！我是你的AI写作助手。我可以帮助你润色文字、扩展思路、查找引用、检查逻辑等。请选择上方的功能开始使用。',
      type: 'text',
      timestamp: new Date()
    }
  ])
  const [history, setHistory] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [usageStats, setUsageStats] = useState({ used: 45, total: 100 })

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 发送消息
  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // 模拟AI响应
      await new Promise(r => setTimeout(r, 1500))

      let response = ''
      let type: Message['type'] = 'text'

      switch (activeMode) {
        case 'polish':
          response = `【润色版本】\n\n${input}\n\n[这段文字已经过学术润色，提升了表达的规范性和流畅度。建议在实际使用时根据上下文进一步调整。]`
          break
        case 'expand':
          response = `【扩展内容】\n\n基于你提供的要点，我进行了如下扩展：\n\n1. 首先，我们需要明确研究背景和意义...\n2. 其次，从理论角度来看...\n3. 此外，实证研究表明...\n\n这样扩展后，内容更加充实，论证更加完整。`
          break
        case 'condense':
          response = `【精简版本】\n\n原文核心要点可以概括为：\n\n[精简后的内容]\n\n保留了关键信息，去除了冗余表达。`
          break
        case 'translate':
          response = `【Translation】\n\n${input}\n\n[This is the translated version maintaining academic style and terminology.]`
          break
        case 'reference':
          response = `【相关文献推荐】\n\n1. Smith, J., & Jones, M. (2024). Advanced methods in academic writing. Journal of Academic Research, 45(2), 123-145.\n\n2. Wang, L., et al. (2023). Writing strategies for scientific papers. Science Communication, 12(3), 67-89.\n\n这些文献与你的研究主题高度相关。`
          type = 'citation'
          break
        case 'check':
          response = `【检查结果】\n\n✅ 语法检查：未发现明显语法错误\n⚠️ 逻辑建议：第3句与第2句的衔接可以更紧密\n💡 改进建议：考虑在第4句前增加过渡词\n\n整体质量不错，小幅调整后会更好。`
          type = 'warning'
          break
        default:
          response = `我理解你的问题。关于"${input.slice(0, 50)}..."，我有以下建议：\n\n1. 从学术写作的角度，建议...\n2. 从逻辑结构来看，可以考虑...\n3. 如果这是引言部分，建议增加...\n\n希望这些建议对你有帮助！`
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        type,
        timestamp: new Date(),
        actions: [
          { label: '复制', action: () => {
            navigator.clipboard.writeText(response)
            message.success('已复制')
          }},
          { label: '插入', action: () => {
            onInsertContent?.(response)
            message.success('已插入')
          }}
        ]
      }

      setMessages(prev => [...prev, assistantMessage])
      setHistory(prev => [input, ...prev].slice(0, 10))
    } catch (error) {
      message.error('请求失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 清空对话
  const handleClear = () => {
    Modal.confirm({
      title: '清空对话',
      content: '确定要清空所有对话记录吗？',
      onOk: () => {
        setMessages([{
          id: 'welcome',
          role: 'assistant',
          content: '对话已清空。有什么我可以帮你的吗？',
          type: 'text',
          timestamp: new Date()
        }])
        message.success('已清空')
      }
    })
  }

  // 快速操作
  const quickActions = [
    { label: '改进表达', action: () => setInput('请改进这段话的表达：') },
    { label: '增加引用', action: () => setInput('请为这段内容推荐相关文献：') },
    { label: '检查逻辑', action: () => setInput('请检查这段论述的逻辑：') },
    { label: '生成摘要', action: () => setInput('请基于以下内容生成摘要：') }
  ]

  return (
    <>
      {/* 悬浮按钮 */}
      <Tooltip title="AI写作助手">
        <Button
          type="primary"
          shape="circle"
          size="large"
          icon={<RobotOutlined />}
          className={styles.floatButton}
          onClick={() => setIsOpen(true)}
        />
      </Tooltip>

      {/* 主面板 */}
      <Drawer
        title={
          <Space>
            <BulbOutlined />
            <span>AI写作助手 2.0</span>
            <Badge count={messages.length - 1} style={{ marginLeft: 8 }} />
          </Space>
        }
        placement="right"
        width={520}
        open={isOpen}
        onClose={() => setIsOpen(false)}
        className={styles.drawer}
        extra={
          <Space>
            <Tooltip title="使用统计">
              <Progress
                type="circle"
                percent={(usageStats.used / usageStats.total) * 100}
                size={32}
                format={() => `${usageStats.used}/${usageStats.total}`}
              />
            </Tooltip>
            <Tooltip title="清空对话">
              <Button icon={<CloseOutlined />} onClick={handleClear} />
            </Tooltip>
          </Space>
        }
      >
        {/* 功能选择 */}
        <div className={styles.modeSelector}>
          <Segmented
            value={activeMode}
            onChange={v => setActiveMode(v as WritingMode)}
            options={features.map(f => ({
              label: (
                <Tooltip title={f.description}>
                  <Space>
                    {f.icon}
                    <span>{f.label}</span>
                  </Space>
                </Tooltip>
              ),
              value: f.key
            }))}
          />
        </div>

        {/* 消息列表 */}
        <div className={styles.messages}>
          <List
            dataSource={messages}
            renderItem={msg => (
              <List.Item
                className={`${styles.messageItem} ${styles[msg.role]}`}
              >
                <div className={styles.messageContent}>
                  {msg.role === 'assistant' && (
                    <Avatar icon={<RobotOutlined />} className={styles.avatar} />
                  )}
                  <div className={styles.bubble}>
                    {msg.type === 'citation' && (
                      <Tag color="blue" className={styles.typeTag}>引用建议</Tag>
                    )}
                    {msg.type === 'warning' && (
                      <Tag color="orange" className={styles.typeTag}>检查报告</Tag>
                    )}
                    <Paragraph className={styles.text}>{msg.content}</Paragraph>
                    {msg.actions && (
                      <Space className={styles.actions}>
                        {msg.actions.map((action, i) => (
                          <Button
                            key={i}
                            type="link"
                            size="small"
                            onClick={action.action}
                          >
                            {action.label}
                          </Button>
                        ))}
                      </Space>
                    )}
                  </div>
                </div>
              </List.Item>
            )}
          />
          {loading && (
            <div className={styles.loading}>
              <Spin size="small" />
              <Text type="secondary">AI思考中...</Text>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 快速操作 */}
        {activeMode === 'chat' && (
          <div className={styles.quickActions}>
            {quickActions.map((action, i) => (
              <Button
                key={i}
                size="small"
                onClick={action.action}
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}

        {/* 输入区域 */}
        <div className={styles.inputArea}>
          <TextArea
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={features.find(f => f.key === activeMode)?.placeholder}
            rows={3}
            className={styles.input}
            onPressEnter={e => {
              if (!e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
          />
          <div className={styles.inputActions}>
            <Text type="secondary" className={styles.hint}>
              Shift + Enter 换行
            </Text>
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={loading}
              disabled={!input.trim()}
            >
              发送
            </Button>
          </div>
        </div>

        {/* 历史记录 */}
        {history.length > 0 && (
          <div className={styles.history}>
            <Divider orientation="left">
              <HistoryOutlined /> 最近查询
            </Divider>
            <Space wrap>
              {history.map((h, i) => (
                <Tag
                  key={i}
                  className={styles.historyTag}
                  onClick={() => setInput(h)}
                >
                  {h.slice(0, 20)}...
                </Tag>
              ))}
            </Space>
          </div>
        )}
      </Drawer>
    </>
  )
}

// 需要导入Avatar
import { Avatar } from 'antd'

export default AIWritingAssistantV2
