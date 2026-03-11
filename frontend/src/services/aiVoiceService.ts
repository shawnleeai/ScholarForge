/**
 * AI语音对话服务
 * 支持语音识别、语音合成、实时对话
 */

// 导师性格类型
export type AdvisorVoiceType = 'poisonous' | 'gentle' | 'strict' | 'humorous' | 'encouraging'

// 语音配置
export interface VoiceConfig {
  type: AdvisorVoiceType
  name: string
  avatar: string
  description: string
  voiceSettings: {
    pitch: number // 音高 0-2
    rate: number // 语速 0.5-2
    volume: number // 音量 0-1
  }
  speakingStyle: {
    greeting: string[]
    interruptions: string[] // 打断语
    questions: string[]
    summaries: string[]
  }
}

// 对话状态
export interface DialogueState {
  sessionId: string
  currentTopic?: string
  discussedPoints: string[]
  suggestedDirections: string[]
  userConcerns: string[]
  startTime: Date
  duration: number // 秒
}

// 语音消息
export interface VoiceMessage {
  id: string
  role: 'user' | 'advisor'
  text: string
  audioUrl?: string
  timestamp: Date
  duration?: number // 音频时长
}

// 通话状态
type CallState = 'idle' | 'connecting' | 'connected' | 'ended'

// 导师配置
const ADVISOR_VOICES: Record<AdvisorVoiceType, VoiceConfig> = {
  poisonous: {
    type: 'poisonous',
    name: '毒舌教授',
    avatar: '🐍',
    description: '说话尖锐毒舌，但能一针见血指出问题',
    voiceSettings: {
      pitch: 1.1,
      rate: 1.2,
      volume: 0.9
    },
    speakingStyle: {
      greeting: [
        '又来了？这次准备了多少干货？别又像上次那样让我失望。',
        '希望你的准备配得上我的时间。说吧，想聊什么？',
        '我时间很宝贵，直接说重点，别说那些废话。'
      ],
      interruptions: [
        '停停停，你这个想法本身就有问题。',
        '打住，你确定要往这个方向走？',
        '等等，你没发现这里逻辑不通吗？'
      ],
      questions: [
        '你的创新点在哪？别告诉我就是换个数据集跑一遍。',
        '这个问题你思考了多久？不会是一拍脑袋吧？',
        '你知道这个方向有多少人做过了吗？你的差异化在哪？'
      ],
      summaries: [
        '总结一下你的问题：想法太大，基础太差。先把基本功练好再说吧。',
        '虽然被我说得很惨，但至少有进步了。下次希望能让我少吐槽一点。'
      ]
    }
  },
  gentle: {
    type: 'gentle',
    name: '温和导师',
    avatar: '🌸',
    description: '温和耐心，循序渐进引导',
    voiceSettings: {
      pitch: 1.0,
      rate: 0.9,
      volume: 0.8
    },
    speakingStyle: {
      greeting: [
        '你好呀，今天想聊聊什么方向呢？',
        '很高兴和你交流，慢慢来，不用着急。',
        '让我们一起梳理一下你的思路吧。'
      ],
      interruptions: [
        '这个想法很有意思，我们可以多聊聊。',
        '稍等一下，我想确认一下你的意思。'
      ],
      questions: [
        '你觉得这个方向最吸引你的是什么呢？',
        '在研究过程中，你最担心遇到什么困难呢？'
      ],
      summaries: [
        '今天聊了很多，我觉得你的思路越来越清晰了。',
        '继续保持，我相信你能找到适合自己的方向。'
      ]
    }
  },
  strict: {
    type: 'strict',
    name: '严格教授',
    avatar: '👨‍🏫',
    description: '严谨认真，要求严格',
    voiceSettings: {
      pitch: 0.9,
      rate: 1.0,
      volume: 1.0
    },
    speakingStyle: {
      greeting: [
        '开始吧，我只有一个小时。',
        '希望你这次准备充分了。'
      ],
      interruptions: [
        '这个论证不够严谨。',
        '数据支撑在哪里？'
      ],
      questions: [
        '你的假设成立的前提是什么？',
        '这个方法的可复现性如何保证？'
      ],
      summaries: [
        '还有很多问题需要解决，继续改进。'
      ]
    }
  },
  humorous: {
    type: 'humorous',
    name: '幽默导师',
    avatar: '😄',
    description: '轻松幽默，寓教于乐',
    voiceSettings: {
      pitch: 1.2,
      rate: 1.1,
      volume: 0.9
    },
    speakingStyle: {
      greeting: [
        '又来学术闲聊了？说吧，这次是啥脑洞？',
        '哈哈，看到你我就想起我当年博士时候的样子。'
      ],
      interruptions: [
        '这个想法有点意思，虽然有点疯狂。',
        '等等，你这是在写论文还是在写科幻小说？'
      ],
      questions: [
        '如果实验失败了，你打算怪谁？怪我吗？',
        '你觉得审稿人会为你的幽默买单吗？'
      ],
      summaries: [
        '虽然笑料百出，但至少方向是对的。'
      ]
    }
  },
  encouraging: {
    type: 'encouraging',
    name: '鼓励型导师',
    avatar: '💪',
    description: '善于鼓励，激发潜能',
    voiceSettings: {
      pitch: 1.1,
      rate: 1.0,
      volume: 0.9
    },
    speakingStyle: {
      greeting: [
        '太棒了！很高兴见到你！',
        '相信今天一定会有收获的！'
      ],
      interruptions: [
        '这个想法很有潜力！',
        '继续说，我觉得你在正确的道路上！'
      ],
      questions: [
        '你最想在这个研究中实现什么突破？',
        '如果没有任何限制，你想做什么样的研究？'
      ],
      summaries: [
        '你今天的表现太棒了！继续加油！'
      ]
    }
  }
}

// 是否使用模拟模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

class AIVoiceService {
  private recognition: any = null
  private synthesis: SpeechSynthesis | null = null
  private currentAdvisor: VoiceConfig = ADVISOR_VOICES.poisonous
  private dialogueState: DialogueState | null = null
  private messageHistory: VoiceMessage[] = []
  private onMessageCallback: ((message: VoiceMessage) => void) | null = null
  private onStateChangeCallback: ((state: CallState) => void) | null = null

  constructor() {
    if (typeof window !== 'undefined') {
      // 初始化语音识别
      const SpeechRecognition = (window as any).SpeechRecognition ||
                               (window as any).webkitSpeechRecognition
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition()
        this.recognition.continuous = true
        this.recognition.interimResults = true
        this.recognition.lang = 'zh-CN'
      }

      // 初始化语音合成
      this.synthesis = window.speechSynthesis
    }
  }

  /**
   * 设置导师类型
   */
  setAdvisor(type: AdvisorVoiceType) {
    this.currentAdvisor = ADVISOR_VOICES[type]
  }

  /**
   * 获取所有导师类型
   */
  getAdvisors(): VoiceConfig[] {
    return Object.values(ADVISOR_VOICES)
  }

  /**
   * 开始语音对话
   */
  async startDialogue(): Promise<boolean> {
    if (USE_MOCK) {
      this.dialogueState = {
        sessionId: Date.now().toString(),
        discussedPoints: [],
        suggestedDirections: [],
        userConcerns: [],
        startTime: new Date(),
        duration: 0
      }
      this.messageHistory = []
      this.onStateChangeCallback?.('connected')

      // 模拟开场白
      setTimeout(() => {
        this.addAdvisorMessage(this.getRandomGreeting())
      }, 1000)

      return true
    }

    try {
      // 请求麦克风权限
      await navigator.mediaDevices.getUserMedia({ audio: true })

      this.dialogueState = {
        sessionId: Date.now().toString(),
        discussedPoints: [],
        suggestedDirections: [],
        userConcerns: [],
        startTime: new Date(),
        duration: 0
      }

      this.messageHistory = []
      this.onStateChangeCallback?.('connected')

      // 开始语音识别
      this.startListening()

      // 播放开场白
      setTimeout(() => {
        const greeting = this.getRandomGreeting()
        this.speak(greeting)
        this.addAdvisorMessage(greeting)
      }, 1000)

      return true
    } catch (error) {
      console.error('启动语音对话失败:', error)
      return false
    }
  }

  /**
   * 结束对话
   */
  endDialogue(): DialogueState | null {
    if (this.dialogueState) {
      this.dialogueState.duration = Math.floor(
        (new Date().getTime() - this.dialogueState.startTime.getTime()) / 1000
      )
    }

    this.stopListening()
    this.onStateChangeCallback?.('ended')

    return this.dialogueState
  }

  /**
   * 开始监听语音输入
   */
  private startListening() {
    if (!this.recognition) return

    this.recognition.onresult = (event: any) => {
      const results = event.results
      if (results.length > 0) {
        const lastResult = results[results.length - 1]
        if (lastResult.isFinal) {
          const text = lastResult[0].transcript
          this.handleUserInput(text)
        }
      }
    }

    this.recognition.onerror = (event: any) => {
      console.error('语音识别错误:', event.error)
    }

    this.recognition.start()
  }

  /**
   * 停止监听
   */
  private stopListening() {
    if (this.recognition) {
      this.recognition.stop()
    }
    if (this.synthesis) {
      this.synthesis.cancel()
    }
  }

  /**
   * 处理用户输入
   */
  private async handleUserInput(text: string) {
    // 添加用户消息
    this.addUserMessage(text)

    // 更新对话状态
    this.dialogueState?.discussedPoints.push(text)

    // 生成AI回复
    const response = await this.generateResponse(text)

    // 播放回复
    this.speak(response)

    // 添加AI消息
    this.addAdvisorMessage(response)
  }

  /**
   * 生成AI回复
   */
  private async generateResponse(userText: string): Promise<string> {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 1500))

      // 简单的规则匹配回复
      const lowerText = userText.toLowerCase()

      if (lowerText.includes('方向') || lowerText.includes('选题')) {
        return this.generateDirectionResponse()
      }

      if (lowerText.includes('问题') || lowerText.includes('困难')) {
        return this.generateProblemResponse()
      }

      if (lowerText.includes('方法') || lowerText.includes('怎么做')) {
        return this.generateMethodResponse()
      }

      return this.generateGeneralResponse()
    }

    // 实际项目中调用AI API
    return '这是一个模拟回复'
  }

  /**
   * 生成方向相关回复
   */
  private generateDirectionResponse(): string {
    const responses: Record<AdvisorVoiceType, string[]> = {
      poisonous: [
        '方向？你的方向就是太宽泛！深度学习是个方向，自然语言处理也是个方向，你能不能说具体点？',
        '听好了，选方向要看三点：第一，有没有人做过；第二，你能不能做出新意；第三，你的导师能不能指导。你都考虑了吗？',
        '你这个方向...说实话，已经有100篇论文在做同样的事情了。你凭什么觉得你能做得更好？'
      ],
      gentle: [
        '确定研究方向是个很重要的决定。我们可以一起分析一下你的兴趣和优势。',
        '这个方向听起来很有意思。我们可以探讨一下具体可以研究哪些子问题。'
      ],
      strict: [
        '方向选择需要基于充分的文献调研。你调研了多少篇相关论文？',
        '确定方向前，请先回答：这个方向的学术价值在哪？'
      ],
      humorous: [
        '方向很重要，但更重要的是别把自己搞丢了。',
        '选题就像找对象，要门当户对，还要有点激情。'
      ],
      encouraging: [
        '相信自己，你一定能找到最适合的方向！',
        '不管选什么方向，重要的是你投入的激情和坚持！'
      ]
    }

    const typeResponses = responses[this.currentAdvisor.type]
    return typeResponses[Math.floor(Math.random() * typeResponses.length)]
  }

  /**
   * 生成问题相关回复
   */
  private generateProblemResponse(): string {
    const responses: Record<AdvisorVoiceType, string[]> = {
      poisonous: [
        '遇到困难就对了，说明你在思考。要是觉得容易，那说明这题太简单，不值一做。',
        '数据不好？代码跑不通？这些都是借口。真正的研究者是在限制条件下找解决方案。'
      ],
      gentle: [
        '遇到困难是正常的，我们可以一起想办法解决。',
        '把问题具体化，我们一步一步来。'
      ],
      strict: [
        '请具体描述你遇到的技术问题。',
        '解决方案需要基于充分的实验验证。'
      ],
      humorous: [
        'bug就像前任，总会不期而遇。',
        '实验失败？恭喜，你离成功又近了一步！'
      ],
      encouraging: [
        '每个困难都是成长的机会！',
        '你一定能克服这些困难的！'
      ]
    }

    const typeResponses = responses[this.currentAdvisor.type]
    return typeResponses[Math.floor(Math.random() * typeResponses.length)]
  }

  /**
   * 生成方法相关回复
   */
  private generateMethodResponse(): string {
    const responses: Record<AdvisorVoiceType, string[]> = {
      poisonous: [
        '方法不是拍脑袋想的，是要读论文学来的。你读了几篇顶会论文？',
        '别总想搞个大新闻，先把baseline跑通再说。'
      ],
      gentle: [
        '方法选择要根据你的具体问题来定。',
        '我们可以参考一下相关领域的主流方法。'
      ],
      strict: [
        '方法选择需要严格的理论支撑。',
        '请先论证你选择的方法的合理性。'
      ],
      humorous: [
        '方法就像工具，关键是要知道什么时候用螺丝刀，什么时候用锤子。',
        '别重复造轮子，但要知道轮子是怎么转的。'
      ],
      encouraging: [
        '相信你的直觉，同时也要多参考前人的经验！',
        '大胆尝试，小心验证！'
      ]
    }

    const typeResponses = responses[this.currentAdvisor.type]
    return typeResponses[Math.floor(Math.random() * typeResponses.length)]
  }

  /**
   * 生成通用回复
   */
  private generateGeneralResponse(): string {
    const responses: Record<AdvisorVoiceType, string[]> = {
      poisonous: [
        '继续说，我听着呢。希望接下来的内容能比刚才更有价值。',
        '嗯...我需要提醒你，我们已经聊了5分钟了，但还没聊到什么实质内容。',
        '你的思路有点跳跃，能不能先想清楚自己要说什么？'
      ],
      gentle: [
        '我在听，请继续说。',
        '这个想法很有意思，可以多展开讲讲。'
      ],
      strict: [
        '请围绕核心问题展开。',
        '请提供更具体的论证。'
      ],
      humorous: [
        '哈哈，你这思路比我当年还跳跃。',
        '有趣，继续继续！'
      ],
      encouraging: [
        '说得很好！继续！',
        '你的思路越来越清晰了！'
      ]
    }

    const typeResponses = responses[this.currentAdvisor.type]
    return typeResponses[Math.floor(Math.random() * typeResponses.length)]
  }

  /**
   * 语音合成
   */
  private speak(text: string) {
    if (!this.synthesis) return

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'zh-CN'
    utterance.pitch = this.currentAdvisor.voiceSettings.pitch
    utterance.rate = this.currentAdvisor.voiceSettings.rate
    utterance.volume = this.currentAdvisor.voiceSettings.volume

    this.synthesis.speak(utterance)
  }

  /**
   * 添加用户消息
   */
  private addUserMessage(text: string) {
    const message: VoiceMessage = {
      id: Date.now().toString(),
      role: 'user',
      text,
      timestamp: new Date()
    }
    this.messageHistory.push(message)
    this.onMessageCallback?.(message)
  }

  /**
   * 添加导师消息
   */
  private addAdvisorMessage(text: string) {
    const message: VoiceMessage = {
      id: Date.now().toString(),
      role: 'advisor',
      text,
      timestamp: new Date()
    }
    this.messageHistory.push(message)
    this.onMessageCallback?.(message)
  }

  /**
   * 获取随机开场白
   */
  private getRandomGreeting(): string {
    const greetings = this.currentAdvisor.speakingStyle.greeting
    return greetings[Math.floor(Math.random() * greetings.length)]
  }

  /**
   * 设置消息回调
   */
  onMessage(callback: (message: VoiceMessage) => void) {
    this.onMessageCallback = callback
  }

  /**
   * 设置状态回调
   */
  onStateChange(callback: (state: CallState) => void) {
    this.onStateChangeCallback = callback
  }

  /**
   * 获取消息历史
   */
  getMessageHistory(): VoiceMessage[] {
    return this.messageHistory
  }

  /**
   * 获取对话总结
   */
  async generateSummary(): Promise<{
    title: string
    keyPoints: string[]
    suggestedDirections: string[]
    nextSteps: string[]
  }> {
    // 模拟生成总结
    return {
      title: '关于研究方向探讨的总结',
      keyPoints: [
        '用户关注深度学习在自然语言处理中的应用',
        '对模型效率和可解释性有顾虑',
        '希望在已有工作基础上进行创新'
      ],
      suggestedDirections: [
        '轻量化模型设计在特定领域的应用',
        '模型决策的可解释性研究',
        '跨领域知识迁移方法'
      ],
      nextSteps: [
        '深入调研相关领域的最新进展',
        '与导师讨论确定具体研究问题',
        '制定详细的文献阅读计划'
      ]
    }
  }
}

// ==================== 语音写作服务 (新增) ====================

import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class VoiceWritingService {
  private baseURL: string

  constructor() {
    this.baseURL = `${API_BASE}/voice-writing`
  }

  /**
   * 转录音频并处理为学术文本
   */
  async transcribeAndProcess(
    audioBlob: Blob,
    paperContext: string = '',
    sectionType: string = 'general'
  ): Promise<{
    success: boolean
    transcribed_text: string
    academic_text: string
    section_type: string
    error?: string
  }> {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.wav')
    formData.append('paper_context', paperContext)
    formData.append('section_type', sectionType)

    const response = await axios.post(`${this.baseURL}/transcribe`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    return response.data
  }

  /**
   * 处理语音指令
   */
  async processVoiceCommand(
    audioBlob: Blob,
    currentDocument: string = '',
    cursorPosition: number = 0
  ): Promise<{
    command_text: string
    parsed_command: {
      command_type: string
      target: string
      content: string
      position: string
    }
    timestamp: string
  }> {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'command.wav')
    formData.append('current_document', currentDocument)
    formData.append('cursor_position', cursorPosition.toString())

    const response = await axios.post(`${this.baseURL}/command`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    return response.data
  }

  /**
   * 文本转语音
   */
  async textToSpeech(
    text: string,
    voice: string = 'xiaosi',
    speed: number = 1.0
  ): Promise<Blob> {
    const formData = new FormData()
    formData.append('text', text)
    formData.append('voice', voice)
    formData.append('speed', speed.toString())

    const response = await axios.post(`${this.baseURL}/tts`, formData, {
      responseType: 'blob'
    })

    return response.data
  }

  /**
   * 创建Web Speech API识别器（用于实时预览）
   */
  createWebSpeechRecognizer(
    onResult: (text: string, isFinal: boolean) => void,
    onError: (error: any) => void,
    language: string = 'zh-CN'
  ): SpeechRecognition | null {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognitionAPI) {
      console.error('Web Speech API not supported')
      return null
    }

    const recognition = new SpeechRecognitionAPI()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = language

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimTranscript = ''
      let finalTranscript = ''

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

    recognition.onerror = onError

    return recognition
  }
}

export const voiceWritingService = new VoiceWritingService()

// ==================== 导出所有服务 ====================

export const aiVoiceService = new AIVoiceService()
export default aiVoiceService

// TypeScript declarations for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition
    webkitSpeechRecognition: typeof SpeechRecognition
  }
}
