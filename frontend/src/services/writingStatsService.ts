/**
 * 论文写作统计服务
 * 记录每日写作时间、字数产出，生成GitHub风格的码力值热力图
 */

// 每日写作数据
export interface DailyWritingData {
  date: string // YYYY-MM-DD
  wordCount: number
  writingTime: number // 分钟
  sessions: WritingSession[]
  achievements: string[]
}

// 写作会话
export interface WritingSession {
  startTime: string
  endTime?: string
  duration: number // 分钟
  wordCount: number
  paperId?: string
  paperTitle?: string
}

// 写作统计
export interface WritingStats {
  totalDays: number
  totalWordCount: number
  totalWritingTime: number // 分钟
  currentStreak: number // 连续写作天数
  longestStreak: number
  averageDailyWords: number
  averageDailyTime: number
  mostProductiveDay?: DailyWritingData
  mostProductiveHour: number
  weeklyData: WeeklyData[]
}

// 周数据
export interface WeeklyData {
  weekStart: string
  totalWords: number
  totalTime: number
  daysActive: number
}

// 成就徽章
export interface Achievement {
  id: string
  name: string
  description: string
  icon: string
  condition: string
  unlockedAt?: string
}

// 成就列表
const ACHIEVEMENTS: Achievement[] = [
  { id: 'first_word', name: '初出茅庐', description: '写下第一个字', icon: '✍️', condition: 'wordCount >= 1' },
  { id: 'hundred_words', name: '百字成章', description: '累计写作100字', icon: '📝', condition: 'wordCount >= 100' },
  { id: 'thousand_words', name: '千字文', description: '累计写作1000字', icon: '📄', condition: 'wordCount >= 1000' },
  { id: 'ten_thousand', name: '万字长文', description: '累计写作10000字', icon: '📚', condition: 'wordCount >= 10000' },
  { id: 'first_day', name: '良好开端', description: '完成第一天的写作', icon: '🌅', condition: 'days >= 1' },
  { id: 'week_streak', name: '一周坚持', description: '连续写作7天', icon: '🔥', condition: 'streak >= 7' },
  { id: 'month_streak', name: '月度达人', description: '连续写作30天', icon: '💎', condition: 'streak >= 30' },
  { id: 'early_bird', name: '早起的鸟儿', description: '早上6点前开始写作', icon: '🐦', condition: 'earlyStart' },
  { id: 'night_owl', name: '夜猫子', description: '晚上11点后仍在写作', icon: '🦉', condition: 'lateNight' },
  { id: 'marathon', name: '马拉松', description: '单次写作超过3小时', icon: '🏃', condition: 'longSession' },
  { id: 'sprint', name: '百米冲刺', description: '一小时内写出500字', icon: '⚡', condition: 'fastWriting' },
  { id: 'weekend_warrior', name: '周末战士', description: '周末写作超过2000字', icon: '🎯', condition: 'weekendWarrior' }
]

const STORAGE_KEY = 'scholarforge_writing_stats'
const SESSION_STORAGE_KEY = 'scholarforge_current_session'

class WritingStatsService {
  private data: Record<string, DailyWritingData> = {}
  private currentSession: WritingSession | null = null
  private wordCountBeforeSession = 0

  constructor() {
    this.loadData()
  }

  /**
   * 加载数据
   */
  private loadData() {
    if (typeof window === 'undefined') return

    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      this.data = JSON.parse(stored)
    }

    const sessionStored = sessionStorage.getItem(SESSION_STORAGE_KEY)
    if (sessionStored) {
      this.currentSession = JSON.parse(sessionStored)
    }
  }

  /**
   * 保存数据
   */
  private saveData() {
    if (typeof window === 'undefined') return
    localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data))
  }

  /**
   * 开始写作会话
   */
  startSession(paperId?: string, paperTitle?: string, initialWordCount = 0): WritingSession {
    this.wordCountBeforeSession = initialWordCount
    this.currentSession = {
      startTime: new Date().toISOString(),
      duration: 0,
      wordCount: 0,
      paperId,
      paperTitle
    }

    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(this.currentSession))
    return this.currentSession
  }

  /**
   * 结束写作会话
   */
  endSession(finalWordCount = 0): WritingSession | null {
    if (!this.currentSession) return null

    const endTime = new Date()
    const startTime = new Date(this.currentSession.startTime)
    const duration = Math.floor((endTime.getTime() - startTime.getTime()) / 60000)
    const wordCount = Math.max(0, finalWordCount - this.wordCountBeforeSession)

    const completedSession: WritingSession = {
      ...this.currentSession,
      endTime: endTime.toISOString(),
      duration,
      wordCount
    }

    // 记录到今日数据
    this.recordSession(completedSession)

    this.currentSession = null
    sessionStorage.removeItem(SESSION_STORAGE_KEY)

    return completedSession
  }

  /**
   * 记录会话
   */
  private recordSession(session: WritingSession) {
    const today = new Date().toISOString().split('T')[0]

    if (!this.data[today]) {
      this.data[today] = {
        date: today,
        wordCount: 0,
        writingTime: 0,
        sessions: [],
        achievements: []
      }
    }

    this.data[today].sessions.push(session)
    this.data[today].wordCount += session.wordCount
    this.data[today].writingTime += session.duration

    // 检查成就
    this.checkAchievements(today)

    this.saveData()
  }

  /**
   * 检查成就
   */
  private checkAchievements(date: string) {
    const dayData = this.data[date]
    const stats = this.getStats()
    const newAchievements: string[] = []

    ACHIEVEMENTS.forEach(achievement => {
      if (dayData.achievements.includes(achievement.id)) return

      let unlocked = false

      switch (achievement.id) {
        case 'first_word':
          unlocked = dayData.wordCount >= 1
          break
        case 'hundred_words':
          unlocked = stats.totalWordCount >= 100
          break
        case 'thousand_words':
          unlocked = stats.totalWordCount >= 1000
          break
        case 'ten_thousand':
          unlocked = stats.totalWordCount >= 10000
          break
        case 'first_day':
          unlocked = stats.totalDays >= 1
          break
        case 'week_streak':
          unlocked = stats.currentStreak >= 7
          break
        case 'month_streak':
          unlocked = stats.currentStreak >= 30
          break
        case 'early_bird':
          unlocked = dayData.sessions.some(s => new Date(s.startTime).getHours() < 6)
          break
        case 'night_owl':
          unlocked = dayData.sessions.some(s => new Date(s.startTime).getHours() >= 23)
          break
        case 'marathon':
          unlocked = dayData.sessions.some(s => s.duration >= 180)
          break
        case 'sprint':
          unlocked = dayData.sessions.some(s => s.wordCount >= 500 && s.duration <= 60)
          break
        case 'weekend_warrior':
          const day = new Date(date).getDay()
          if (day === 0 || day === 6) {
            unlocked = dayData.wordCount >= 2000
          }
          break
      }

      if (unlocked) {
        dayData.achievements.push(achievement.id)
        newAchievements.push(achievement.name)
      }
    })

    return newAchievements
  }

  /**
   * 获取统计数据
   */
  getStats(): WritingStats {
    const dates = Object.keys(this.data).sort()
    const totalDays = dates.length

    let totalWordCount = 0
    let totalWritingTime = 0
    let maxWords = 0
    let mostProductiveDay: DailyWritingData | undefined
    const hourCounts: Record<number, number> = {}

    dates.forEach(date => {
      const day = this.data[date]
      totalWordCount += day.wordCount
      totalWritingTime += day.writingTime

      if (day.wordCount > maxWords) {
        maxWords = day.wordCount
        mostProductiveDay = day
      }

      day.sessions.forEach(session => {
        const hour = new Date(session.startTime).getHours()
        hourCounts[hour] = (hourCounts[hour] || 0) + session.wordCount
      })
    })

    // 计算连续写作天数
    let currentStreak = 0
    let longestStreak = 0
    let tempStreak = 0
    let prevDate: Date | null = null

    dates.forEach(dateStr => {
      const date = new Date(dateStr)
      if (prevDate) {
        const diffDays = (date.getTime() - prevDate.getTime()) / (1000 * 3600 * 24)
        if (diffDays === 1) {
          tempStreak++
        } else {
          longestStreak = Math.max(longestStreak, tempStreak)
          tempStreak = 1
        }
      } else {
        tempStreak = 1
      }
      prevDate = date
    })

    longestStreak = Math.max(longestStreak, tempStreak)

    // 检查今天是否写作
    const today = new Date().toISOString().split('T')[0]
    const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]

    if (this.data[today]) {
      currentStreak = tempStreak
    } else if (this.data[yesterday]) {
      currentStreak = tempStreak
    } else {
      currentStreak = 0
    }

    // 找出最高产时段
    let mostProductiveHour = 9
    let maxHourWords = 0
    Object.entries(hourCounts).forEach(([hour, words]) => {
      if (words > maxHourWords) {
        maxHourWords = words
        mostProductiveHour = parseInt(hour)
      }
    })

    // 计算周数据
    const weeklyData: WeeklyData[] = []
    const weekMap: Record<string, WeeklyData> = {}

    dates.forEach(date => {
      const d = new Date(date)
      const weekStart = new Date(d.getTime() - d.getDay() * 86400000).toISOString().split('T')[0]

      if (!weekMap[weekStart]) {
        weekMap[weekStart] = {
          weekStart,
          totalWords: 0,
          totalTime: 0,
          daysActive: 0
        }
      }

      weekMap[weekStart].totalWords += this.data[date].wordCount
      weekMap[weekStart].totalTime += this.data[date].writingTime
      weekMap[weekStart].daysActive++
    })

    Object.values(weekMap).forEach(week => weeklyData.push(week))

    return {
      totalDays,
      totalWordCount,
      totalWritingTime,
      currentStreak,
      longestStreak,
      averageDailyWords: totalDays > 0 ? Math.round(totalWordCount / totalDays) : 0,
      averageDailyTime: totalDays > 0 ? Math.round(totalWritingTime / totalDays) : 0,
      mostProductiveDay,
      mostProductiveHour,
      weeklyData
    }
  }

  /**
   * 获取热力图数据
   */
  getHeatmapData(year?: number): Array<{ date: string; count: number; level: number }> {
    const targetYear = year || new Date().getFullYear()
    const data: Array<{ date: string; count: number; level: number }> = []

    // 生成全年日期
    const startDate = new Date(targetYear, 0, 1)
    const endDate = new Date(targetYear, 11, 31)

    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
      const dateStr = d.toISOString().split('T')[0]
      const dayData = this.data[dateStr]
      const count = dayData ? dayData.wordCount : 0

      // 计算等级 (0-4)
      let level = 0
      if (count > 0) level = 1
      if (count >= 500) level = 2
      if (count >= 1000) level = 3
      if (count >= 2000) level = 4

      data.push({ date: dateStr, count, level })
    }

    return data
  }

  /**
   * 获取今日数据
   */
  getTodayData(): DailyWritingData {
    const today = new Date().toISOString().split('T')[0]
    return this.data[today] || {
      date: today,
      wordCount: 0,
      writingTime: 0,
      sessions: [],
      achievements: []
    }
  }

  /**
   * 获取当前会话
   */
  getCurrentSession(): WritingSession | null {
    return this.currentSession
  }

  /**
   * 获取所有成就
   */
  getAchievements(): Achievement[] {
    const unlockedIds = new Set<string>()

    Object.values(this.data).forEach(day => {
      day.achievements.forEach(id => unlockedIds.add(id))
    })

    return ACHIEVEMENTS.map(achievement => ({
      ...achievement,
      unlockedAt: unlockedIds.has(achievement.id)
        ? Object.entries(this.data)
            .find(([_, day]) => day.achievements.includes(achievement.id))?.[0]
        : undefined
    }))
  }

  /**
   * 导出数据
   */
  exportData(): string {
    return JSON.stringify({
      data: this.data,
      exportDate: new Date().toISOString()
    }, null, 2)
  }

  /**
   * 导入数据
   */
  importData(jsonString: string): boolean {
    try {
      const imported = JSON.parse(jsonString)
      if (imported.data) {
        this.data = { ...this.data, ...imported.data }
        this.saveData()
        return true
      }
      return false
    } catch (error) {
      console.error('导入数据失败:', error)
      return false
    }
  }

  /**
   * 清空数据
   */
  clearData() {
    this.data = {}
    this.saveData()
  }
}

export const writingStatsService = new WritingStatsService()
export default writingStatsService
