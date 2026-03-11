/**
 * 智能答辩模拟服务 V2
 * 支持语音交互、多导师 panel、AI 评价、压力测试等
 */

export type EvaluationDimension =
  | 'content_depth'      // 内容深度
  | 'logical_clarity'    // 逻辑清晰度
  | 'response_quality'   // 回答质量
  | 'presentation'       // 表达能力
  | 'technical_accuracy' // 技术准确性
  | 'innovation'         // 创新性

export interface EvaluationScore {
  dimension: EvaluationDimension
  score: number // 0-100
  feedback: string
  suggestions: string[]
}

export interface DefenseAdvisor {
  id: string
  name: string
  title: string
  avatar: string
  personality: 'strict' | 'gentle' | 'sharp' | 'encouraging' | 'socratic'
  expertise: string[]
  color: string
  voiceConfig?: SpeechSynthesisVoice
}

export interface DefenseQuestion {
  id: string
  advisorId: string
  content: string
  type: 'opening' | 'technical' | 'challenge' | 'followup' | 'concluding'
  difficulty: 1 | 2 | 3 | 4 | 5
  expectedPoints: string[]
  followUpQuestions?: string[]
}

export interface DefenseResponse {
  questionId: string
  content: string
  audioBlob?: Blob
  duration: number
  confidence?: number
}

export interface DefenseSessionV2 {
  id: string
  paperTitle: string
  paperAbstract: string
  startTime: Date
  advisors: DefenseAdvisor[]
  currentAdvisorIndex: number
  questions: DefenseQuestion[]
  responses: DefenseResponse[]
  currentQuestionIndex: number
  isCompleted: boolean
  evaluation?: DefenseEvaluation
}

export interface DefenseEvaluation {
  overallScore: number
  dimensionScores: EvaluationScore[]
  totalDuration: number
  wordCount: number
  fluencyScore: number
  strengths: string[]
  weaknesses: string[]
  improvementPlan: string[]
  comparisonToAverage: {
    percentile: number
    betterThan: number
  }
}

export interface PressureTestConfig {
  enabled: boolean
  rapidFire: boolean // 连续追问
  hostileMode: boolean // 严厉模式
  randomInterruptions: boolean // 随机打断
  timePressure: boolean // 时间压力
}

// 导师库
export const DEFENSE_ADVISORS: DefenseAdvisor[] = [
  {
    id: 'chair_strict',
    name: '张教授',
    title: '答辩委员会主席',
    avatar: '👨‍🏫',
    personality: 'strict',
    expertise: ['方法论', '理论框架', '学术规范'],
    color: '#ff4d4f'
  },
  {
    id: 'tech_expert',
    name: '李教授',
    title: '技术专家',
    avatar: '👩‍💻',
    personality: 'sharp',
    expertise: ['算法', '实验设计', '数据分析'],
    color: '#1890ff'
  },
  {
    id: 'field_expert',
    name: '王教授',
    title: '领域专家',
    avatar: '👨‍🔬',
    personality: 'socratic',
    expertise: ['前沿研究', '应用场景', '创新点'],
    color: '#52c41a'
  },
  {
    id: 'young_advisor',
    name: '陈副教授',
    title: '青年教师',
    avatar: '👩‍🎓',
    personality: 'encouraging',
    expertise: ['新兴方法', '跨学科', '实用价值'],
    color: '#faad14'
  }
]

// 问题库
const QUESTION_TEMPLATES: Omit<DefenseQuestion, 'id' | 'advisorId'>[] = [
  {
    content: '请用三句话概括你的研究贡献。',
    type: 'opening',
    difficulty: 2,
    expectedPoints: ['核心发现', '方法论创新', '理论/实践贡献']
  },
  {
    content: '你的研究问题是如何确定的？为什么这个问题值得研究？',
    type: 'opening',
    difficulty: 3,
    expectedPoints: ['文献缺口', '现实意义', '理论价值']
  },
  {
    content: '请解释你选择这个理论框架的原因，以及它的适用性。',
    type: 'technical',
    difficulty: 4,
    expectedPoints: ['理论匹配度', '替代方案对比', '局限性说明']
  },
  {
    content: '你的实验设计如何保证内部效度和外部效度？',
    type: 'technical',
    difficulty: 4,
    expectedPoints: ['控制变量', '样本代表性', '测量工具信效度']
  },
  {
    content: '如果其他研究者无法复现你的结果，可能是什么原因？',
    type: 'challenge',
    difficulty: 5,
    expectedPoints: ['数据可用性', '方法细节', '边界条件']
  },
  {
    content: '你的研究发现与现有文献有什么矛盾之处？如何解释？',
    type: 'challenge',
    difficulty: 5,
    expectedPoints: ['对比分析', '可能原因', '理论启示']
  },
  {
    content: '基于你的研究发现，对实践者有什么具体建议？',
    type: 'followup',
    difficulty: 3,
    expectedPoints: ['可操作性', '适用场景', '注意事项']
  },
  {
    content: '如果你的研究预算增加十倍，你会如何改进研究设计？',
    type: 'followup',
    difficulty: 4,
    expectedPoints: ['样本扩展', '方法升级', '长期追踪']
  },
  {
    content: '这个领域未来3-5年的研究趋势会是什么？你的研究如何融入？',
    type: 'concluding',
    difficulty: 4,
    expectedPoints: ['趋势判断', '研究定位', '后续计划']
  },
  {
    content: '如果让你重新做这个研究，你会在哪些方面改进？',
    type: 'concluding',
    difficulty: 3,
    expectedPoints: ['方法改进', '数据收集', '理论深化']
  }
]

class DefenseSimulationService {
  private currentSession: DefenseSessionV2 | null = null
  private recognition: SpeechRecognition | null = null
  private synthesis: SpeechSynthesis = window.speechSynthesis

  // 开始新会话
  startSession(paperTitle: string, paperAbstract: string, advisorCount: number = 3): DefenseSessionV2 {
    const selectedAdvisors = this.selectAdvisors(advisorCount)
    const questions = this.generateQuestions(selectedAdvisors)

    this.currentSession = {
      id: Date.now().toString(),
      paperTitle,
      paperAbstract,
      startTime: new Date(),
      advisors: selectedAdvisors,
      currentAdvisorIndex: 0,
      questions,
      responses: [],
      currentQuestionIndex: 0,
      isCompleted: false
    }

    return this.currentSession
  }

  // 选择导师
  private selectAdvisors(count: number): DefenseAdvisor[] {
    const shuffled = [...DEFENSE_ADVISORS].sort(() => Math.random() - 0.5)
    return shuffled.slice(0, Math.min(count, shuffled.length))
  }

  // 生成问题
  private generateQuestions(advisors: DefenseAdvisor[]): DefenseQuestion[] {
    const questions: DefenseQuestion[] = []

    // 每个导师问2-3个问题
    advisors.forEach((advisor, advisorIndex) => {
      const questionCount = 2 + Math.floor(Math.random() * 2)
      const shuffled = [...QUESTION_TEMPLATES].sort(() => Math.random() - 0.5)

      for (let i = 0; i < questionCount; i++) {
        const template = shuffled[i % shuffled.length]
        questions.push({
          ...template,
          id: `q_${advisorIndex}_${i}`,
          advisorId: advisor.id,
          // 根据导师性格调整难度
          difficulty: this.adjustDifficulty(template.difficulty, advisor.personality)
        })
      }
    })

    // 打乱顺序，但保证开场和结束问题在合适位置
    return this.arrangeQuestions(questions)
  }

  private adjustDifficulty(base: number, personality: DefenseAdvisor['personality']): 1 | 2 | 3 | 4 | 5 {
    const adjustments: Record<typeof personality, number> = {
      strict: 1,
      sharp: 1,
      socratic: 0,
      gentle: -1,
      encouraging: -1
    }
    const adjusted = Math.max(1, Math.min(5, base + adjustments[personality]))
    return adjusted as 1 | 2 | 3 | 4 | 5
  }

  private arrangeQuestions(questions: DefenseQuestion[]): DefenseQuestion[] {
    const opening = questions.filter(q => q.type === 'opening')
    const concluding = questions.filter(q => q.type === 'concluding')
    const middle = questions.filter(q => q.type !== 'opening' && q.type !== 'concluding')
      .sort(() => Math.random() - 0.5)

    return [...opening, ...middle, ...concluding]
  }

  // 获取当前问题
  getCurrentQuestion(): DefenseQuestion | null {
    if (!this.currentSession) return null
    return this.currentSession.questions[this.currentSession.currentQuestionIndex] || null
  }

  // 提交回答
  submitResponse(content: string, audioBlob?: Blob, duration: number = 0): DefenseResponse {
    if (!this.currentSession) throw new Error('No active session')

    const currentQuestion = this.getCurrentQuestion()
    if (!currentQuestion) throw new Error('No current question')

    const response: DefenseResponse = {
      questionId: currentQuestion.id,
      content,
      audioBlob,
      duration,
      confidence: this.analyzeConfidence(content)
    }

    this.currentSession.responses.push(response)
    this.currentSession.currentQuestionIndex++

    // 检查是否完成
    if (this.currentSession.currentQuestionIndex >= this.currentSession.questions.length) {
      this.currentSession.isCompleted = true
    }

    return response
  }

  // 分析回答信心度
  private analyzeConfidence(content: string): number {
    const confidenceIndicators = [
      '我认为', '我相信', '确实', '显然', '毫无疑问',
      '数据表明', '实验证明', '结果显示'
    ]
    const hesitationIndicators = [
      '可能', '也许', '大概', '不太确定', '我觉得',
      '应该是', '好像', '似乎'
    ]

    let score = 70 // 基础分

    confidenceIndicators.forEach(indicator => {
      if (content.includes(indicator)) score += 3
    })

    hesitationIndicators.forEach(indicator => {
      if (content.includes(indicator)) score -= 5
    })

    // 回答长度
    const wordCount = content.length
    if (wordCount < 50) score -= 10
    if (wordCount > 200) score += 5

    return Math.max(0, Math.min(100, score))
  }

  // 开始语音识别
  startVoiceRecognition(onResult: (text: string, isFinal: boolean) => void): void {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      throw new Error('浏览器不支持语音识别')
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    this.recognition = new SpeechRecognition()

    this.recognition.lang = 'zh-CN'
    this.recognition.continuous = true
    this.recognition.interimResults = true

    this.recognition.onresult = (event) => {
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }

      onResult(finalTranscript || interimTranscript, !!finalTranscript)
    }

    this.recognition.start()
  }

  // 停止语音识别
  stopVoiceRecognition(): void {
    this.recognition?.stop()
    this.recognition = null
  }

  // 语音合成播报
  speak(text: string, advisor?: DefenseAdvisor): void {
    if (!this.synthesis) return

    // 取消之前的播报
    this.synthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'zh-CN'
    utterance.rate = 0.9
    utterance.pitch = advisor?.personality === 'gentle' ? 1.1 :
                      advisor?.personality === 'strict' ? 0.9 : 1

    this.synthesis.speak(utterance)
  }

  // 停止播报
  stopSpeaking(): void {
    this.synthesis?.cancel()
  }

  // 生成评价
  generateEvaluation(): DefenseEvaluation {
    if (!this.currentSession) throw new Error('No active session')

    const { responses, questions, startTime } = this.currentSession
    const totalDuration = (Date.now() - startTime.getTime()) / 1000 / 60 // 分钟
    const totalWords = responses.reduce((sum, r) => sum + r.content.length, 0)

    // 各维度评分
    const dimensionScores: EvaluationScore[] = [
      this.evaluateContentDepth(responses, questions),
      this.evaluateLogicalClarity(responses),
      this.evaluateResponseQuality(responses, questions),
      this.evaluatePresentation(totalWords, totalDuration),
      this.evaluateTechnicalAccuracy(responses, questions),
      this.evaluateInnovation(responses)
    ]

    const overallScore = Math.round(
      dimensionScores.reduce((sum, d) => sum + d.score, 0) / dimensionScores.length
    )

    const allStrengths = dimensionScores.flatMap(d => d.score > 75 ? [d.dimension] : [])
    const allWeaknesses = dimensionScores.flatMap(d => d.score < 60 ? [d.dimension] : [])

    return {
      overallScore,
      dimensionScores,
      totalDuration,
      wordCount: totalWords,
      fluencyScore: Math.round(totalWords / Math.max(totalDuration, 1)),
      strengths: allStrengths,
      weaknesses: allWeaknesses,
      improvementPlan: this.generateImprovementPlan(dimensionScores),
      comparisonToAverage: {
        percentile: Math.round(overallScore),
        betterThan: Math.round(overallScore * 0.9)
      }
    }
  }

  private evaluateContentDepth(responses: DefenseResponse[], questions: DefenseQuestion[]): EvaluationScore {
    const avgLength = responses.reduce((sum, r) => sum + r.content.length, 0) / responses.length
    let score = Math.min(100, avgLength / 3)

    // 检查是否回答了预期要点
    let pointsCovered = 0
    let totalPoints = 0
    responses.forEach(r => {
      const q = questions.find(q => q.id === r.questionId)
      if (q) {
        totalPoints += q.expectedPoints.length
        pointsCovered += q.expectedPoints.filter(p => r.content.includes(p)).length
      }
    })

    if (totalPoints > 0) {
      score = score * 0.5 + (pointsCovered / totalPoints * 100) * 0.5
    }

    return {
      dimension: 'content_depth',
      score: Math.round(score),
      feedback: score > 80 ? '内容详实，论证充分' : score > 60 ? '内容基本完整，可进一步深化' : '内容较为单薄，需要补充',
      suggestions: ['增加具体案例分析', '补充更多数据支撑', '深化理论讨论']
    }
  }

  private evaluateLogicalClarity(responses: DefenseResponse[]): EvaluationScore {
    const logicIndicators = ['首先', '其次', '因此', '所以', '但是', '然而', '综上所述']
    let logicScore = 60

    responses.forEach(r => {
      logicIndicators.forEach(indicator => {
        if (r.content.includes(indicator)) logicScore += 2
      })
    })

    return {
      dimension: 'logical_clarity',
      score: Math.min(100, logicScore),
      feedback: logicScore > 80 ? '逻辑清晰，层次分明' : '逻辑结构有待加强',
      suggestions: ['使用更多的连接词', '采用总分总结构', '每段一个核心观点']
    }
  }

  private evaluateResponseQuality(responses: DefenseResponse[], questions: DefenseQuestion[]): EvaluationScore {
    const confidenceAvg = responses.reduce((sum, r) => sum + (r.confidence || 70), 0) / responses.length

    return {
      dimension: 'response_quality',
      score: Math.round(confidenceAvg),
      feedback: confidenceAvg > 80 ? '回答自信，专业度高' : '回答略显犹豫，需要增强信心',
      suggestions: ['使用更确定的表达', '准备更多备用答案', '进行更多模拟练习']
    }
  }

  private evaluatePresentation(wordCount: number, duration: number): EvaluationScore {
    const wordsPerMinute = wordCount / Math.max(duration, 1)
    let score = 70

    // 理想的语速是每分钟120-180字
    if (wordsPerMinute >= 120 && wordsPerMinute <= 180) {
      score = 90
    } else if (wordsPerMinute >= 100 && wordsPerMinute <= 200) {
      score = 75
    } else {
      score = 60
    }

    return {
      dimension: 'presentation',
      score,
      feedback: score > 80 ? '表达流畅，语速适中' : wordsPerMinute > 180 ? '语速偏快，需要放慢' : '语速偏慢，可以精简',
      suggestions: ['控制语速在每分钟120-180字', '多使用停顿强调重点', '练习时间控制']
    }
  }

  private evaluateTechnicalAccuracy(responses: DefenseResponse[], questions: DefenseQuestion[]): EvaluationScore {
    const technicalTerms = ['算法', '模型', '假设', '显著性', '相关性', '回归', '变量', '样本']
    let termCount = 0

    responses.forEach(r => {
      technicalTerms.forEach(term => {
        if (r.content.includes(term)) termCount++
      })
    })

    const score = Math.min(100, 60 + termCount * 3)

    return {
      dimension: 'technical_accuracy',
      score,
      feedback: score > 80 ? '术语使用准确，专业性强' : '可以适当增加专业术语',
      suggestions: ['准确使用学科术语', '解释复杂概念', '注意概念的精确性']
    }
  }

  private evaluateInnovation(responses: DefenseResponse[]): EvaluationScore {
    const innovationKeywords = ['创新', '首次', '新颖', '突破', '独特', '原创', '改进', '优化']
    let innovationScore = 60

    responses.forEach(r => {
      innovationKeywords.forEach(kw => {
        if (r.content.includes(kw)) innovationScore += 5
      })
    })

    return {
      dimension: 'innovation',
      score: Math.min(100, innovationScore),
      feedback: innovationScore > 80 ? '突出了创新点和贡献' : '需要更好地展示创新价值',
      suggestions: ['明确阐述创新点', '对比现有研究', '强调独特贡献']
    }
  }

  private generateImprovementPlan(scores: EvaluationScore[]): string[] {
    const plan: string[] = []
    const lowScores = scores.filter(s => s.score < 70)

    lowScores.forEach(s => {
      plan.push(...s.suggestions.slice(0, 2))
    })

    return plan.slice(0, 5)
  }

  // 获取当前会话
  getSession(): DefenseSessionV2 | null {
    return this.currentSession
  }

  // 结束会话
  endSession(): DefenseEvaluation {
    const evaluation = this.generateEvaluation()
    if (this.currentSession) {
      this.currentSession.evaluation = evaluation
      this.currentSession.isCompleted = true
    }
    this.stopVoiceRecognition()
    this.stopSpeaking()
    return evaluation
  }

  // 导出报告
  exportReport(): string {
    if (!this.currentSession) return ''

    const { paperTitle, startTime, advisors, evaluation } = this.currentSession

    return `
# 答辩模拟报告

## 基本信息
- 论文标题：${paperTitle}
- 模拟时间：${startTime.toLocaleString('zh-CN')}
- 答辩委员会：${advisors.map(a => a.name).join('、')}

## 综合评价
- 总分：${evaluation?.overallScore}/100
- 排名：超过${evaluation?.comparisonToAverage.percentile}%的参与者

## 各维度得分
${evaluation?.dimensionScores.map(d => `- ${d.dimension}: ${d.score}分 - ${d.feedback}`).join('\n')}

## 改进建议
${evaluation?.improvementPlan.map((p, i) => `${i + 1}. ${p}`).join('\n')}

---
生成时间：${new Date().toLocaleString('zh-CN')}
    `.trim()
  }
}

export const defenseSimulationService = new DefenseSimulationService()
export default defenseSimulationService
