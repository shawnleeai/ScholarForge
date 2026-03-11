/**
 * 智能模拟答辩系统 V2
 * 支持语音交互、实时评分、多导师 panel
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Avatar,
  Progress,
  Badge,
  Input,
  Row,
  Col,
  Statistic,
  Timeline,
  Tag,
  Alert,
  Spin,
  Tooltip,
  Radio,
  Divider,
  Result,
  Slider,
  Switch,
  message
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  AudioOutlined,
  AudioMutedOutlined,
  MessageOutlined,
  TrophyOutlined,
  FireOutlined,
  ClockCircleOutlined,
  TeamOutlined,
  BarChartOutlined,
  ReloadOutlined,
  DownloadOutlined,
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons'
import {
  defenseSimulationService,
  type DefenseSessionV2,
  type DefenseAdvisor,
  type DefenseQuestion,
  type DefenseEvaluation,
  type EvaluationDimension,
  DEFENSE_ADVISORS
} from '@/services/defenseSimulationService'
import styles from './DefenseSimulationV2.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

interface DefenseSimulationV2Props {
  paperTitle?: string
  paperAbstract?: string
}

const DIMENSION_LABELS: Record<EvaluationDimension, string> = {
  content_depth: '内容深度',
  logical_clarity: '逻辑清晰度',
  response_quality: '回答质量',
  presentation: '表达能力',
  technical_accuracy: '技术准确性',
  innovation: '创新性'
}

const DefenseSimulationV2: React.FC<DefenseSimulationV2Props> = ({
  paperTitle = '',
  paperAbstract = ''
}) => {
  const [session, setSession] = useState<DefenseSessionV2 | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [evaluation, setEvaluation] = useState<DefenseEvaluation | null>(null)
  const [advisorCount, setAdvisorCount] = useState(3)
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [showReport, setShowReport] = useState(false)
  const [pressureMode, setPressureMode] = useState(false)

  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const [elapsedTime, setElapsedTime] = useState(0)

  // 开始答辩
  const startDefense = useCallback(() => {
    if (!paperTitle.trim()) {
      message.warning('请先输入论文标题')
      return
    }

    const newSession = defenseSimulationService.startSession(
      paperTitle,
      paperAbstract,
      advisorCount
    )
    setSession(newSession)
    setEvaluation(null)
    setShowReport(false)
    setElapsedTime(0)
    setTranscript('')

    message.success(`答辩开始！共有 ${advisorCount} 位导师参与`)

    // 播报开场
    if (voiceEnabled) {
      defenseSimulationService.speak(
        `答辩正式开始。首先请简要介绍一下你的研究。`,
        newSession.advisors[0]
      )
    }
  }, [paperTitle, paperAbstract, advisorCount, voiceEnabled])

  // 计时器
  useEffect(() => {
    if (session && !session.isCompleted) {
      timerRef.current = setInterval(() => {
        setElapsedTime(prev => prev + 1)
      }, 1000)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [session])

  // 开始语音识别
  const startRecording = useCallback(() => {
    try {
      defenseSimulationService.startVoiceRecognition((text, isFinal) => {
        if (isFinal) {
          setTranscript(prev => prev + text)
          setInterimTranscript('')
        } else {
          setInterimTranscript(text)
        }
      })
      setIsRecording(true)
      message.info('开始录音，请回答导师的问题')
    } catch (error) {
      message.error('无法启动语音识别，请检查麦克风权限')
    }
  }, [])

  // 停止语音识别
  const stopRecording = useCallback(() => {
    defenseSimulationService.stopVoiceRecognition()
    setIsRecording(false)
    setInterimTranscript('')
  }, [])

  // 提交回答
  const submitResponse = useCallback(() => {
    if (!transcript.trim()) {
      message.warning('请输入或说出你的回答')
      return
    }

    setIsProcessing(true)

    // 模拟处理延迟
    setTimeout(() => {
      defenseSimulationService.submitResponse(transcript, undefined, elapsedTime)
      setTranscript('')
      setIsProcessing(false)

      const currentSession = defenseSimulationService.getSession()
      setSession(currentSession)

      if (currentSession?.isCompleted) {
        const evalResult = defenseSimulationService.endSession()
        setEvaluation(evalResult)
        message.success('答辩完成！请查看评价报告')
      } else if (voiceEnabled && currentSession) {
        // 播报下一个问题
        const nextQuestion = defenseSimulationService.getCurrentQuestion()
        if (nextQuestion) {
          const advisor = currentSession.advisors.find(a => a.id === nextQuestion.advisorId)
          setTimeout(() => {
            defenseSimulationService.speak(nextQuestion.content, advisor)
          }, 500)
        }
      }
    }, 1000)
  }, [transcript, elapsedTime, voiceEnabled])

  // 获取当前问题
  const currentQuestion = session
    ? defenseSimulationService.getCurrentQuestion()
    : null

  // 获取当前导师
  const currentAdvisor = currentQuestion && session
    ? session.advisors.find(a => a.id === currentQuestion.advisorId)
    : null

  // 格式化时间
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // 渲染设置界面
  const renderSetup = () => (
    <div className={styles.setupPanel}>
      <Alert
        message="智能答辩模拟 V2"
        description="体验真实的答辩场景，支持语音交互、实时评分和多导师 panel。系统将根据你的回答给出专业评价和改进建议。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Row gutter={[24, 24]}>
        <Col xs={24} md={12}>
          <Card title="答辩设置" size="small">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <Text type="secondary">导师人数</Text>
                <Radio.Group
                  value={advisorCount}
                  onChange={e => setAdvisorCount(e.target.value)}
                  buttonStyle="solid"
                >
                  <Radio.Button value={2}>2位</Radio.Button>
                  <Radio.Button value={3}>3位</Radio.Button>
                  <Radio.Button value={4}>4位</Radio.Button>
                </Radio.Group>
              </div>

              <div>
                <Text type="secondary">语音播报</Text>
                <br />
                <Switch
                  checked={voiceEnabled}
                  onChange={setVoiceEnabled}
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                />
              </div>

              <div>
                <Text type="secondary">压力测试模式</Text>
                <br />
                <Switch
                  checked={pressureMode}
                  onChange={setPressureMode}
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                />
                {pressureMode && (
                  <Text type="warning" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
                    <FireOutlined /> 开启后导师会更加严格，追问更密集
                  </Text>
                )}
              </div>
            </Space>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title="可选导师" size="small">
            <div className={styles.advisorList}>
              {DEFENSE_ADVISORS.map(advisor => (
                <div key={advisor.id} className={styles.advisorPreview}>
                  <Avatar style={{ backgroundColor: advisor.color }}>
                    {advisor.avatar}
                  </Avatar>
                  <div>
                    <Text strong>{advisor.name}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {advisor.title}
                    </Text>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      <Button
        type="primary"
        size="large"
        icon={<PlayCircleOutlined />}
        onClick={startDefense}
        disabled={!paperTitle.trim()}
        block
        style={{ marginTop: 24 }}
      >
        开始模拟答辩
      </Button>
    </div>
  )

  // 渲染答辩界面
  const renderDefense = () => (
    <div className={styles.defensePanel}>
      {/* 顶部状态栏 */}
      <div className={styles.statusBar}>
        <Space size="large">
          <Statistic
            title="已进行"
            value={formatTime(elapsedTime)}
            prefix={<ClockCircleOutlined />}
            valueStyle={{ fontSize: 18, fontFamily: 'monospace' }}
          />
          <Statistic
            title="问题进度"
            value={`${session?.currentQuestionIndex}/${session?.questions.length}`}
            prefix={<MessageOutlined />}
            valueStyle={{ fontSize: 18 }}
          />
        </Space>

        <Progress
          percent={Math.round(((session?.currentQuestionIndex || 0) / (session?.questions.length || 1)) * 100)}
          size="small"
          style={{ width: 200 }}
        />
      </div>

      {/* 导师 Panel */}
      <div className={styles.advisorPanel}>
        {session?.advisors.map((advisor, index) => (
          <div
            key={advisor.id}
            className={`${styles.advisorBadge} ${currentAdvisor?.id === advisor.id ? styles.active : ''}`}
          >
            <Badge
              dot={currentAdvisor?.id === advisor.id}
              color={advisor.color}
            >
              <Avatar
                size="large"
                style={{
                  backgroundColor: advisor.color,
                  opacity: currentAdvisor?.id === advisor.id ? 1 : 0.5
                }}
              >
                {advisor.avatar}
              </Avatar>
            </Badge>
            <div className={styles.advisorInfo}>
              <Text strong style={{ fontSize: 12 }}>{advisor.name}</Text>
              <Text type="secondary" style={{ fontSize: 10 }}>{advisor.title}</Text>
            </div>
          </div>
        ))}
      </div>

      {/* 当前问题 */}
      {currentQuestion && currentAdvisor && (
        <Card
          className={styles.questionCard}
          title={
            <Space>
              <Avatar style={{ backgroundColor: currentAdvisor.color }}>
                {currentAdvisor.avatar}
              </Avatar>
              <span>{currentAdvisor.name} 提问</span>
              <Tag color={currentQuestion.difficulty > 3 ? 'red' : 'blue'}>
                难度 {currentQuestion.difficulty}
              </Tag>
            </Space>
          }
        >
          <Paragraph className={styles.questionText}>
            {currentQuestion.content}
          </Paragraph>

          {currentQuestion.expectedPoints.length > 0 && (
            <div className={styles.expectedPoints}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                回答要点提示：
              </Text>
              <Space wrap size="small">
                {currentQuestion.expectedPoints.map((point, i) => (
                  <Tag key={i} size="small" style={{ fontSize: 11 }}>
                    {point}
                  </Tag>
                ))}
              </Space>
            </div>
          )}
        </Card>
      )}

      {/* 回答区域 */}
      <div className={styles.responseArea}>
        <div className={styles.inputWrapper}>
          <TextArea
            value={transcript + interimTranscript}
            onChange={e => setTranscript(e.target.value)}
            placeholder={isRecording ? '正在录音，请说话...' : '点击麦克风开始语音回答，或直接输入文字'}
            rows={4}
            className={isRecording ? styles.recording : ''}
          />
          {isRecording && (
            <div className={styles.recordingIndicator}>
              <span className={styles.pulse} />
              <Text type="danger">录音中...</Text>
            </div>
          )}
        </div>

        <div className={styles.controls}>
          <Button
            type={isRecording ? 'default' : 'primary'}
            danger={isRecording}
            icon={isRecording ? <AudioMutedOutlined /> : <AudioOutlined />}
            onClick={isRecording ? stopRecording : startRecording}
            size="large"
          >
            {isRecording ? '停止录音' : '语音回答'}
          </Button>

          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={submitResponse}
            disabled={!transcript.trim() || isProcessing}
            loading={isProcessing}
            size="large"
          >
            提交回答
          </Button>
        </div>
      </div>

      {/* 历史记录 */}
      {session && session.responses.length > 0 && (
        <div className={styles.historySection}>
          <Divider orientation="left">回答记录</Divider>
          <Timeline
            items={session.responses.map((resp, index) => ({
              color: 'blue',
              children: (
                <div className={styles.historyItem}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    问题 {index + 1}
                  </Text>
                  <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>
                    {resp.content}
                  </Paragraph>
                  {resp.confidence && (
                    <Tag size="small" color={resp.confidence > 80 ? 'success' : 'warning'}>
                      信心度 {resp.confidence}%
                    </Tag>
                  )}
                </div>
              )
            }))}
          />
        </div>
      )}
    </div>
  )

  // 渲染评价报告
  const renderEvaluation = () => {
    if (!evaluation) return null

    return (
      <div className={styles.evaluationPanel}>
        <Result
          status={evaluation.overallScore >= 80 ? 'success' : evaluation.overallScore >= 60 ? 'info' : 'warning'}
          title="答辩模拟完成！"
          subTitle={`总体得分：${evaluation.overallScore}/100`}
          extra={[
            <Button
              key="restart"
              icon={<ReloadOutlined />}
              onClick={() => {
                setSession(null)
                setEvaluation(null)
              }}
            >
              重新开始
            </Button>,
            <Button
              key="export"
              type="primary"
              icon={<DownloadOutlined />}
              onClick={() => {
                const report = defenseSimulationService.exportReport()
                const blob = new Blob([report], { type: 'text/markdown' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `答辩模拟报告_${new Date().toLocaleDateString('zh-CN')}.md`
                a.click()
                message.success('报告已下载')
              }}
            >
              导出报告
            </Button>
          ]}
        />

        <Row gutter={[16, 16]} className={styles.statsGrid}>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="总字数"
                value={evaluation.wordCount}
                suffix="字"
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="总时长"
                value={Math.round(evaluation.totalDuration)}
                suffix="分钟"
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="平均语速"
                value={evaluation.fluencyScore}
                suffix="字/分"
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="超越用户"
                value={evaluation.comparisonToAverage.betterThan}
                suffix="%"
              />
            </Card>
          </Col>
        </Row>

        <Card title="各维度评分" className={styles.dimensionCard}>
          <Row gutter={[16, 16]}>
            {evaluation.dimensionScores.map(dim => (
              <Col xs={24} sm={12} md={8} key={dim.dimension}>
                <div className={styles.dimensionItem}>
                  <div className={styles.dimensionHeader}>
                    <Text strong>{DIMENSION_LABELS[dim.dimension]}</Text>
                    <Text type={dim.score >= 80 ? 'success' : dim.score >= 60 ? 'warning' : 'danger'}>
                      {dim.score}分
                    </Text>
                  </div>
                  <Progress
                    percent={dim.score}
                    status={dim.score >= 80 ? 'success' : dim.score >= 60 ? 'normal' : 'exception'}
                    size="small"
                    showInfo={false}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {dim.feedback}
                  </Text>
                </div>
              </Col>
            ))}
          </Row>
        </Card>

        <Card title="改进建议" className={styles.suggestionsCard}>
          <Timeline
            items={evaluation.improvementPlan.map((suggestion, index) => ({
              color: 'blue',
              children: (
                <Text>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                  {suggestion}
                </Text>
              )
            }))}
          />
        </Card>
      </div>
    )
  }

  return (
    <Card
      className={styles.defenseSimulationV2}
      title={
        <Space>
          <TrophyOutlined />
          <span>智能答辩模拟 V2</span>
          {session && (
            <Badge
              status={session.isCompleted ? 'default' : 'processing'}
              text={session.isCompleted ? '已完成' : '进行中'}
            />
          )}
        </Space>
      }
    >
      {!session && renderSetup()}
      {session && !session.isCompleted && renderDefense()}
      {session?.isCompleted && renderEvaluation()}
    </Card>
  )
}

export default DefenseSimulationV2
