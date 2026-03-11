/**
 * 增强版答辩模拟组件
 * 支持多角色导师、趣味梗、随机事件等
 */

import React, { useState, useCallback } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Avatar,
  List,
  Tag,
  Progress,
  Select,
  message,
  Divider,
  Modal,
  Input
} from 'antd'
import {
  MessageOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  SmileOutlined,
  ReloadOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import {
  advisorCharacters,
  randomEvents,
  evaluationTemplates,
  type AdvisorCharacter,
  type RandomEvent
} from './defenseCharacters'
import styles from './EnhancedDefenseSimulation.module.css'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { TextArea } = Input

interface DefenseSession {
  advisor: AdvisorCharacter
  currentRound: number
  totalRounds: number
  score: number
  history: DefenseMessage[]
  triggeredEvents: RandomEvent[]
}

interface DefenseMessage {
  id: string
  role: 'advisor' | 'student' | 'system' | 'event'
  content: string
  type?: 'greeting' | 'question' | 'praise' | 'criticism' | 'followup' | 'concluding' | 'event'
  timestamp: Date
}

const EnhancedDefenseSimulation: React.FC = () => {
  const [selectedAdvisor, setSelectedAdvisor] = useState<AdvisorCharacter>(advisorCharacters[0])
  const [session, setSession] = useState<DefenseSession | null>(null)
  const [isSimulating, setIsSimulating] = useState(false)
  const [currentMessage, setCurrentMessage] = useState('')
  const [showAdvisorInfo, setShowAdvisorInfo] = useState(false)

  // 开始答辩
  const startDefense = useCallback(() => {
    const newSession: DefenseSession = {
      advisor: selectedAdvisor,
      currentRound: 0,
      totalRounds: 5,
      score: 100,
      history: [],
      triggeredEvents: []
    }

    // 添加开场白
    const greeting = selectedAdvisor.speakingStyle.greeting[
      Math.floor(Math.random() * selectedAdvisor.speakingStyle.greeting.length)
    ]

    newSession.history.push({
      id: Date.now().toString(),
      role: 'advisor',
      content: `${selectedAdvisor.avatar} ${selectedAdvisor.name}：${greeting}`,
      type: 'greeting',
      timestamp: new Date()
    })

    setSession(newSession)
    setIsSimulating(true)
    setCurrentMessage('')

    message.success(`答辩开始！导师：${selectedAdvisor.name} - ${selectedAdvisor.description}`)
  }, [selectedAdvisor])

  // 生成导师提问
  const generateAdvisorMessage = useCallback((): DefenseMessage | null => {
    if (!session) return null

    const { advisor, currentRound, totalRounds } = session
    const styles = advisor.speakingStyle

    let content = ''
    let type: DefenseMessage['type'] = 'question'

    if (currentRound === 0) {
      content = styles.questions[Math.floor(Math.random() * styles.questions.length)]
    } else if (currentRound >= totalRounds - 1) {
      content = styles.concluding[Math.floor(Math.random() * styles.concluding.length)]
      type = 'concluding'
    } else {
      const rand = Math.random()
      if (rand < 0.4) {
        content = styles.questions[Math.floor(Math.random() * styles.questions.length)]
        type = 'question'
      } else if (rand < 0.6) {
        content = styles.praise[Math.floor(Math.random() * styles.praise.length)]
        type = 'praise'
      } else if (rand < 0.8) {
        content = styles.criticism[Math.floor(Math.random() * styles.criticism.length)]
        type = 'criticism'
      } else {
        content = styles.followUp[Math.floor(Math.random() * styles.followUp.length)]
        type = 'followup'
      }
    }

    // 随机添加口头禅
    if (Math.random() < 0.3) {
      const phrase = advisor.catchphrases[Math.floor(Math.random() * advisor.catchphrases.length)]
      content = `${phrase} ${content}`
    }

    return {
      id: Date.now().toString(),
      role: 'advisor',
      content: `${advisor.avatar} ${advisor.name}：${content}`,
      type,
      timestamp: new Date()
    }
  }, [session])

  // 触发随机事件
  const triggerRandomEvent = useCallback((): RandomEvent | null => {
    const rand = Math.random()
    let cumulativeProb = 0

    for (const event of randomEvents) {
      cumulativeProb += event.probability
      if (rand < cumulativeProb) {
        return event
      }
    }
    return null
  }, [])

  // 学生回复
  const handleStudentReply = useCallback(() => {
    if (!session || !currentMessage.trim()) return

    const studentMsg: DefenseMessage = {
      id: Date.now().toString(),
      role: 'student',
      content: `🎓 你：${currentMessage}`,
      timestamp: new Date()
    }

    setSession(prev => {
      if (!prev) return null
      return {
        ...prev,
        history: [...prev.history, studentMsg],
        currentRound: prev.currentRound + 1
      }
    })

    setCurrentMessage('')

    // 延迟后生成导师回复
    setTimeout(() => {
      // 检查是否触发随机事件
      const event = triggerRandomEvent()
      if (event) {
        const eventMsg: DefenseMessage = {
          id: Date.now().toString(),
          role: 'event',
          content: `⚡ 突发事件：${event.title}\n${event.description}\n\n${selectedAdvisor.name}反应：${event.advisorResponses[selectedAdvisor.personality]}`,
          type: 'event',
          timestamp: new Date()
        }

        setSession(prev => {
          if (!prev) return null
          return {
            ...prev,
            history: [...prev.history, eventMsg],
            triggeredEvents: [...prev.triggeredEvents, event]
          }
        })
      }

      // 生成导师回复
      const advisorMsg = generateAdvisorMessage()
      if (advisorMsg) {
        setSession(prev => {
          if (!prev) return null
          return {
            ...prev,
            history: [...prev.history, advisorMsg]
          }
        })
      }

      // 检查是否结束
      if (session.currentRound >= session.totalRounds - 1) {
        setIsSimulating(false)
      }
    }, 1000)
  }, [session, currentMessage, selectedAdvisor, generateAdvisorMessage, triggerRandomEvent])

  // 获取评价
  const getEvaluation = useCallback(() => {
    if (!session) return ''

    const { score, triggeredEvents } = session
    let level: keyof typeof evaluationTemplates = 'pass'

    if (score >= 90) level = 'excellent'
    else if (score >= 80) level = 'good'
    else if (score >= 60) level = 'pass'
    else level = 'fail'

    const baseEval = evaluationTemplates[level][
      Math.floor(Math.random() * evaluationTemplates[level].length)
    ]

    let bonus = ''
    if (triggeredEvents.length > 0) {
      bonus = `\n\n🎮 本次答辩触发了 ${triggeredEvents.length} 个随机事件！`
    }

    return baseEval + bonus
  }, [session])

  // 渲染消息
  const renderMessage = (msg: DefenseMessage) => {
    const isAdvisor = msg.role === 'advisor'
    const isEvent = msg.role === 'event'

    return (
      <List.Item
        className={`${styles.messageItem} ${isAdvisor ? styles.advisorMessage : isEvent ? styles.eventMessage : styles.studentMessage}`}
      >
        <div className={styles.messageContent}>
          <div className={styles.messageHeader}>
            {isAdvisor && msg.type && (
              <Tag
                color={
                  msg.type === 'praise' ? 'success' :
                  msg.type === 'criticism' ? 'error' :
                  msg.type === 'question' ? 'blue' :
                  msg.type === 'concluding' ? 'purple' :
                  'default'
                }
                size="small"
              >
                {msg.type === 'praise' ? '表扬' :
                 msg.type === 'criticism' ? '批评' :
                 msg.type === 'question' ? '提问' :
                 msg.type === 'concluding' ? '总结' :
                 '追问'}
              </Tag>
            )}
            {isEvent && <Tag color="orange">突发事件</Tag>}
          </div>
          <Paragraph className={styles.messageText}>{msg.content}</Paragraph>
        </div>
      </List.Item>
    )
  }

  return (
    <div className={styles.defenseSimulation}>
      <Card
        title={
          <Space>
            <TrophyOutlined />
            <span>AI答辩模拟器 - 趣味版</span>
          </Space>
        }
        className={styles.mainCard}
      >
        {!isSimulating && !session && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div className={styles.setupSection}>
              <Title level={5}>选择你的答辩导师</Title>
              <Select
                value={selectedAdvisor.id}
                onChange={(value) => {
                  const advisor = advisorCharacters.find(a => a.id === value)
                  if (advisor) setSelectedAdvisor(advisor)
                }}
                style={{ width: 300 }}
              >
                {advisorCharacters.map(advisor => (
                  <Option key={advisor.id} value={advisor.id}>
                    {advisor.avatar} {advisor.name} - {advisor.title}
                  </Option>
                ))}
              </Select>

              <Button
                type="link"
                icon={<InfoCircleOutlined />}
                onClick={() => setShowAdvisorInfo(true)}
              >
                查看导师详情
              </Button>
            </div>

            <div className={styles.advisorPreview}>
              <Card size="small" className={styles.advisorCard}>
                <div className={styles.advisorHeader}>
                  <Avatar size={64} className={styles.advisorAvatar}>
                    {selectedAdvisor.avatar}
                  </Avatar>
                  <div>
                    <Title level={4} style={{ margin: 0 }}>
                      {selectedAdvisor.name}
                    </Title>
                    <Text type="secondary">{selectedAdvisor.title}</Text>
                  </div>
                </div>
                <Paragraph>{selectedAdvisor.description}</Paragraph>
                <Space wrap>
                  <Tag color={selectedAdvisor.difficulty >= 4 ? 'red' : selectedAdvisor.difficulty >= 3 ? 'orange' : 'green'}>
                    难度: {'⭐'.repeat(selectedAdvisor.difficulty)}
                  </Tag>
                  <Tag>风格: {selectedAdvisor.questionStyle}</Tag>
                </Space>
              </Card>
            </div>

            <Button
              type="primary"
              size="large"
              icon={<ThunderboltOutlined />}
              onClick={startDefense}
              block
            >
              开始模拟答辩
            </Button>
          </Space>
        )}

        {session && (
          <div className={styles.defenseSession}>
            <div className={styles.sessionHeader}>
              <div className={styles.advisorInfo}>
                <Avatar size={40}>{session.advisor.avatar}</Avatar>
                <div>
                  <Text strong>{session.advisor.name}</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    第 {session.currentRound + 1}/{session.totalRounds} 轮
                  </Text>
                </div>
              </div>
              <Progress
                percent={((session.currentRound + 1) / session.totalRounds) * 100}
                size="small"
                style={{ width: 200 }}
              />
            </div>

            <List
              className={styles.messageList}
              dataSource={session.history}
              renderItem={renderMessage}
              locale={{ emptyText: '答辩即将开始...' }}
            />

            {isSimulating ? (
              <div className={styles.inputArea}>
                <TextArea
                  className={styles.textInput}
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  placeholder="输入你的回答..."
                  rows={3}
                />
                <Button
                  type="primary"
                  icon={<MessageOutlined />}
                  onClick={handleStudentReply}
                  disabled={!currentMessage.trim()}
                  block
                >
                  回复
                </Button>
              </div>
            ) : (
              <div className={styles.resultSection}>
                <Divider />
                <Title level={4}>
                  <SmileOutlined /> 答辩结果
                </Title>
                <Paragraph className={styles.evaluation}>
                  {getEvaluation()}
                </Paragraph>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    setSession(null)
                    setIsSimulating(false)
                  }}
                >
                  重新开始
                </Button>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* 导师详情弹窗 */}
      <Modal
        title="导师详情"
        open={showAdvisorInfo}
        onCancel={() => setShowAdvisorInfo(false)}
        footer={null}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          {advisorCharacters.map(advisor => (
            <Card key={advisor.id} size="small">
              <Space>
                <Avatar size={48}>{advisor.avatar}</Avatar>
                <div>
                  <Text strong>{advisor.name}</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {advisor.description}
                  </Text>
                  <br />
                  <Tag size="small">
                    {'⭐'.repeat(advisor.difficulty)}
                  </Tag>
                </div>
              </Space>
            </Card>
          ))}
        </Space>
      </Modal>
    </div>
  )
}

export default EnhancedDefenseSimulation
