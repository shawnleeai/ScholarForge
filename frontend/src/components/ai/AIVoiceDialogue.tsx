/**
 * AI语音对话组件
 * 类似豆包打电话的交互体验
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Card,
  Button,
  Avatar,
  Typography,
  Space,
  Tag,
  List,
  Badge,
  Spin,
  Alert,
  Drawer,
  Result,
  Timeline,
  Statistic,
  message,
  Tooltip,
  Divider
} from 'antd'
import {
  PhoneOutlined,
  CloseOutlined,
  AudioOutlined,
  AudioMutedOutlined,
  MessageOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
  DownloadOutlined,
  UserOutlined,
  SoundOutlined,
  LoadingOutlined
} from '@ant-design/icons'
import {
  aiVoiceService,
  type VoiceConfig,
  type VoiceMessage,
  type DialogueState
} from '@/services/aiVoiceService'
import styles from './AIVoiceDialogue.module.css'

const { Title, Text, Paragraph } = Typography

interface AIVoiceDialogueProps {
  visible: boolean
  onClose: () => void
  initialTopic?: string
}

const advisorColors: Record<string, string> = {
  poisonous: '#ff4d4f',
  gentle: '#52c41a',
  strict: '#1890ff',
  humorous: '#faad14',
  encouraging: '#eb2f96'
}

const AIVoiceDialogue: React.FC<AIVoiceDialogueProps> = ({
  visible,
  onClose,
  initialTopic
}) => {
  const [isCalling, setIsCalling] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [selectedAdvisor, setSelectedAdvisor] = useState<VoiceConfig | null>(null)
  const [messages, setMessages] = useState<VoiceMessage[]>([])
  const [duration, setDuration] = useState(0)
  const [callEnded, setCallEnded] = useState(false)
  const [summary, setSummary] = useState<any>(null)
  const [isMuted, setIsMuted] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const advisors = aiVoiceService.getAdvisors()

  // 滚动到最新消息
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // 通话计时
  useEffect(() => {
    if (isConnected && !callEnded) {
      timerRef.current = setInterval(() => {
        setDuration(prev => prev + 1)
      }, 1000)
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [isConnected, callEnded])

  // 设置消息监听
  useEffect(() => {
    aiVoiceService.onMessage((message) => {
      setMessages(prev => [...prev, message])
      if (message.role === 'advisor') {
        setIsSpeaking(true)
        setTimeout(() => setIsSpeaking(false), 2000)
      }
    })
  }, [])

  // 开始通话
  const startCall = async (advisor: VoiceConfig) => {
    setSelectedAdvisor(advisor)
    aiVoiceService.setAdvisor(advisor.type)
    setIsCalling(true)

    const success = await aiVoiceService.startDialogue()

    if (success) {
      setIsConnected(true)
      message.success('已连接导师')
    } else {
      message.error('连接失败，请检查麦克风权限')
      setIsCalling(false)
    }
  }

  // 结束通话
  const endCall = async () => {
    const state = aiVoiceService.endDialogue()
    setIsConnected(false)
    setCallEnded(true)

    // 生成总结
    const callSummary = await aiVoiceService.generateSummary()
    setSummary(callSummary)

    message.success('通话已结束，已生成总结')
  }

  // 格式化时间
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // 渲染导师选择
  const renderAdvisorSelection = () => (
    <div className={styles.advisorSelection}>
      <Title level={4} className={styles.selectionTitle}>
        选择一位导师进行语音咨询
      </Title>
      <Paragraph type="secondary" className={styles.selectionDesc}>
        每位导师有不同的指导风格，选择最适合你的交流方式
      </Paragraph>

      <div className={styles.advisorList}>
        {advisors.map(advisor => (
          <Card
            key={advisor.type}
            hoverable
            className={styles.advisorCard}
            onClick={() => startCall(advisor)}
          >
            <div className={styles.advisorInfo}>
              <Avatar
                size={64}
                style={{
                  backgroundColor: advisorColors[advisor.type],
                  fontSize: 32
                }}
              >
                {advisor.avatar}
              </Avatar>
              <div className={styles.advisorDetails}>
                <Title level={5} className={styles.advisorName}>
                  {advisor.name}
                </Title>
                <Paragraph type="secondary" className={styles.advisorDesc}>
                  {advisor.description}
                </Paragraph>
                <Space size={4}>
                  <Tag color="blue">语调: {advisor.voiceSettings.pitch > 1 ? '高' : advisor.voiceSettings.pitch < 1 ? '低' : '中'}</Tag>
                  <Tag color="green">语速: {advisor.voiceSettings.rate > 1 ? '快' : advisor.voiceSettings.rate < 1 ? '慢' : '正常'}</Tag>
                </Space>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )

  // 渲染通话界面
  const renderCallInterface = () => (
    <div className={styles.callInterface}>
      {/* 通话头部 */}
      <div className={styles.callHeader}>
        <Space>
          <Avatar
            size={48}
            style={{ backgroundColor: selectedAdvisor ? advisorColors[selectedAdvisor.type] : '#1890ff' }}
          >
            {selectedAdvisor?.avatar}
          </Avatar>
          <div>
            <Text strong className={styles.callName}>
              {selectedAdvisor?.name}
            </Text>
            <div>
              <Badge status={isConnected ? 'processing' : 'default'} />
              <Text type="secondary" className={styles.callStatus}>
                {isConnected ? '通话中' : '连接中...'}
              </Text>
            </div>
          </div>
        </Space>

        <Statistic
          value={formatDuration(duration)}
          className={styles.duration}
        />
      </div>

      {/* 语音波形动画 */}
      {isSpeaking && (
        <div className={styles.waveContainer}>
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={styles.waveBar}
              style={{
                animationDelay: `${i * 0.1}s`,
                backgroundColor: selectedAdvisor ? advisorColors[selectedAdvisor.type] : '#1890ff'
              }}
            />
          ))}
        </div>
      )}

      {/* 消息列表 */}
      <div className={styles.messagesContainer}>
        <List
          dataSource={messages}
          renderItem={msg => (
            <List.Item
              className={`${styles.messageItem} ${styles[msg.role]}`}
            >
              {msg.role === 'advisor' && (
                <Avatar
                  size={32}
                  style={{
                    backgroundColor: selectedAdvisor ? advisorColors[selectedAdvisor.type] : '#1890ff'
                  }}
                >
                  {selectedAdvisor?.avatar}
                </Avatar>
              )}
              <div className={styles.messageBubble}>
                <Text className={styles.messageText}>{msg.text}</Text>
                <Text type="secondary" className={styles.messageTime}>
                  {msg.timestamp.toLocaleTimeString()}
                </Text>
              </div>
              {msg.role === 'user' && (
                <Avatar size={32} icon={<UserOutlined />} />
              )}
            </List.Item>
          )}
        />
        <div ref={messagesEndRef} />
      </div>

      {/* 通话控制 */}
      <div className={styles.callControls}>
        <Button
          type="primary"
          danger
          size="large"
          shape="circle"
          icon={<CloseOutlined />}
          onClick={endCall}
          className={styles.endCallButton}
        />
        <Text type="secondary">点击结束通话</Text>
      </div>
    </div>
  )

  // 渲染通话总结
  const renderCallSummary = () => (
    <div className={styles.callSummary}>
      <Result
        status="success"
        icon={<CheckCircleOutlined />}
        title="通话已完成"
        subTitle={`与${selectedAdvisor?.name}的通话时长: ${formatDuration(duration)}`}
      />

      {summary && (
        <Card title="对话总结" className={styles.summaryCard}>
          <Title level={5}>{summary.title}</Title>

          <Divider orientation="left">关键讨论点</Divider>
          <Timeline
            items={summary.keyPoints.map((point: string, index: number) => ({
              children: point,
              color: index === 0 ? 'green' : index === 1 ? 'blue' : 'gray'
            }))}
          />

          <Divider orientation="left">建议研究方向</Divider>
          <List
            dataSource={summary.suggestedDirections}
            renderItem={(item: string) => (
              <List.Item>
                <Text>• {item}</Text>
              </List.Item>
            )}
          />

          <Divider orientation="left">下一步行动</Divider>
          <List
            dataSource={summary.nextSteps}
            renderItem={(item: string) => (
              <List.Item>
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                <Text>{item}</Text>
              </List.Item>
            )}
          />

          <div className={styles.summaryActions}>
            <Button type="primary" icon={<DownloadOutlined />} block>
              导出总结报告
            </Button>
            <Button onClick={() => {
              setCallEnded(false)
              setMessages([])
              setDuration(0)
              setSummary(null)
              setSelectedAdvisor(null)
            }} block style={{ marginTop: 8 }}>
              开始新对话
            </Button>
          </div>
        </Card>
      )}
    </div>
  )

  return (
    <Drawer
      title={
        <Space>
          <PhoneOutlined />
          <span>AI导师语音咨询</span>
        </Space>
      }
      placement="bottom"
      height="80vh"
      open={visible}
      onClose={onClose}
      className={styles.voiceDrawer}
      destroyOnClose
    >
      <div className={styles.voiceDialogue}>
        {!isCalling && !callEnded && renderAdvisorSelection()}
        {isCalling && !callEnded && renderCallInterface()}
        {callEnded && renderCallSummary()}
      </div>
    </Drawer>
  )
}

export default AIVoiceDialogue
