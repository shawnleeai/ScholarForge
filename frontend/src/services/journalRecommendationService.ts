/**
 * 智能投稿推荐服务
 * 根据论文内容推荐合适的期刊/会议
 */

export interface Journal {
  id: string
  name: string
  publisher: string
  issn?: string
  impactFactor?: number
  citescore?: number
  hIndex?: number
  acceptanceRate?: number // 接受率
  timeToFirstDecision?: number // 初审时间(天)
  timeToPublication?: number // 发表周期(天)
  openAccess: boolean
  apc?: number // 文章处理费
  scopes: string[] // 收录范围
  journalType: 'journal' | 'conference' | 'magazine'
  ranking: 'Q1' | 'Q2' | 'Q3' | 'Q4' | 'unranked'
  url?: string
  submissionUrl?: string
}

export interface SubmissionRecommendation {
  journal: Journal
  matchScore: number // 匹配度 0-100
  matchReasons: string[] // 推荐理由
  suitability: 'high' | 'medium' | 'low'
  estimatedAcceptanceProbability: number // 预估接受概率
  pros: string[] // 优势
  cons: string[] // 劣势
  similarArticles?: string[] // 该期刊发表的相似文章
}

export interface PaperProfile {
  title: string
  abstract: string
  keywords: string[]
  references: string[]
  methodology?: string
  domain: string
  hasEmpiricalData: boolean
  isReview: boolean
  wordCount?: number
}

// 模拟期刊数据
const MOCK_JOURNALS: Journal[] = [
  {
    id: 'j1',
    name: 'Nature Machine Intelligence',
    publisher: 'Nature Publishing Group',
    impactFactor: 25.8,
    citescore: 35.2,
    hIndex: 95,
    acceptanceRate: 8,
    timeToFirstDecision: 45,
    timeToPublication: 180,
    openAccess: true,
    apc: 9500,
    scopes: ['Artificial Intelligence', 'Machine Learning', 'Neuroscience'],
    journalType: 'journal',
    ranking: 'Q1',
    url: 'https://www.nature.com/natmachintell'
  },
  {
    id: 'j2',
    name: 'IEEE Transactions on Pattern Analysis and Machine Intelligence',
    publisher: 'IEEE',
    impactFactor: 24.3,
    citescore: 38.1,
    hIndex: 340,
    acceptanceRate: 15,
    timeToFirstDecision: 60,
    timeToPublication: 240,
    openAccess: false,
    apc: 2195,
    scopes: ['Computer Vision', 'Pattern Recognition', 'Machine Learning'],
    journalType: 'journal',
    ranking: 'Q1',
    url: 'https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=34'
  },
  {
    id: 'j3',
    name: 'Journal of Machine Learning Research',
    publisher: 'JMLR',
    impactFactor: 4.3,
    citescore: 8.2,
    hIndex: 168,
    acceptanceRate: 25,
    timeToFirstDecision: 90,
    timeToPublication: 120,
    openAccess: true,
    apc: 0,
    scopes: ['Machine Learning', 'Statistical Learning', 'Optimization'],
    journalType: 'journal',
    ranking: 'Q1',
    url: 'https://www.jmlr.org'
  },
  {
    id: 'j4',
    name: 'Expert Systems with Applications',
    publisher: 'Elsevier',
    impactFactor: 8.5,
    citescore: 12.8,
    hIndex: 185,
    acceptanceRate: 20,
    timeToFirstDecision: 50,
    timeToPublication: 150,
    openAccess: true,
    apc: 2800,
    scopes: ['Expert Systems', 'AI Applications', 'Decision Support'],
    journalType: 'journal',
    ranking: 'Q1',
    url: 'https://www.sciencedirect.com/journal/expert-systems-with-applications'
  },
  {
    id: 'j5',
    name: 'Neurocomputing',
    publisher: 'Elsevier',
    impactFactor: 6.0,
    citescore: 9.5,
    hIndex: 145,
    acceptanceRate: 30,
    timeToFirstDecision: 40,
    timeToPublication: 120,
    openAccess: true,
    apc: 2500,
    scopes: ['Neural Networks', 'Deep Learning', 'Cognitive Computing'],
    journalType: 'journal',
    ranking: 'Q1',
    url: 'https://www.sciencedirect.com/journal/neurocomputing'
  },
  {
    id: 'j6',
    name: 'Applied Intelligence',
    publisher: 'Springer',
    impactFactor: 5.3,
    citescore: 7.8,
    hIndex: 78,
    acceptanceRate: 35,
    timeToFirstDecision: 35,
    timeToPublication: 100,
    openAccess: true,
    apc: 2190,
    scopes: ['AI Applications', 'Intelligent Systems', 'Machine Learning'],
    journalType: 'journal',
    ranking: 'Q2',
    url: 'https://www.springer.com/journal/10489'
  },
  {
    id: 'c1',
    name: 'NeurIPS (Conference on Neural Information Processing Systems)',
    publisher: 'NeurIPS Foundation',
    acceptanceRate: 21,
    timeToFirstDecision: 60,
    openAccess: true,
    scopes: ['Machine Learning', 'Neuroscience', 'AI'],
    journalType: 'conference',
    ranking: 'Q1',
    url: 'https://nips.cc'
  },
  {
    id: 'c2',
    name: 'ICML (International Conference on Machine Learning)',
    publisher: 'PMLR',
    acceptanceRate: 22,
    timeToFirstDecision: 45,
    openAccess: true,
    scopes: ['Machine Learning', 'Deep Learning', 'Optimization'],
    journalType: 'conference',
    ranking: 'Q1',
    url: 'https://icml.cc'
  },
  {
    id: 'c3',
    name: 'CVPR (Computer Vision and Pattern Recognition)',
    publisher: 'IEEE/CVF',
    acceptanceRate: 25,
    timeToFirstDecision: 50,
    openAccess: true,
    scopes: ['Computer Vision', 'Pattern Recognition', 'Deep Learning'],
    journalType: 'conference',
    ranking: 'Q1',
    url: 'https://cvpr.thecvf.com'
  }
]

class JournalRecommendationService {
  /**
   * 推荐期刊
   */
  async recommendJournals(
    paperProfile: PaperProfile,
    preferences?: {
      preferredRanking?: string[]
      maxAPC?: number
      requireOpenAccess?: boolean
      preferredType?: 'journal' | 'conference' | 'all'
    }
  ): Promise<SubmissionRecommendation[]> {
    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 1500))

    // 基于论文特征匹定期刊
    const recommendations = MOCK_JOURNALS.map(journal =>
      this.calculateMatchScore(journal, paperProfile)
    )

    // 应用偏好筛选
    let filtered = recommendations
    if (preferences) {
      if (preferences.preferredType && preferences.preferredType !== 'all') {
        filtered = filtered.filter(r => r.journal.journalType === preferences.preferredType)
      }
      if (preferences.requireOpenAccess) {
        filtered = filtered.filter(r => r.journal.openAccess)
      }
      if (preferences.maxAPC) {
        filtered = filtered.filter(r => !r.journal.apc || r.journal.apc <= preferences.maxAPC!)
      }
    }

    // 按匹配度排序
    return filtered.sort((a, b) => b.matchScore - a.matchScore)
  }

  /**
   * 计算匹配度
   */
  private calculateMatchScore(journal: Journal, paper: PaperProfile): SubmissionRecommendation {
    let score = 50 // 基础分
    const reasons: string[] = []
    const pros: string[] = []
    const cons: string[] = []

    // 1. 关键词匹配
    const keywordMatches = journal.scopes.filter(scope =>
      paper.keywords.some(kw =>
        scope.toLowerCase().includes(kw.toLowerCase()) ||
        kw.toLowerCase().includes(scope.toLowerCase())
      )
    )

    if (keywordMatches.length > 0) {
      score += keywordMatches.length * 10
      reasons.push(`期刊收录范围包含您的研究关键词：${keywordMatches.join(', ')}`)
    }

    // 2. 研究类型匹配
    if (paper.isReview && journal.journalType === 'journal') {
      score += 5
      reasons.push('期刊接受综述类文章')
    }

    if (!paper.isReview && paper.hasEmpiricalData) {
      score += 5
      reasons.push('期刊接受实证研究')
    }

    // 3. 期刊优势
    if (journal.impactFactor && journal.impactFactor > 10) {
      pros.push('高影响因子期刊')
    }

    if (journal.openAccess) {
      pros.push('开放获取，提高可见度')
    }

    if (journal.apc === 0) {
      pros.push('无版面费')
    }

    if (journal.timeToFirstDecision && journal.timeToFirstDecision < 45) {
      pros.push('初审周期短')
    }

    // 4. 期刊劣势
    if (journal.acceptanceRate && journal.acceptanceRate < 15) {
      cons.push('接受率较低，竞争激烈')
      score -= 5
    }

    if (journal.apc && journal.apc > 5000) {
      cons.push('版面费较高')
    }

    // 5. 预估接受概率
    let acceptanceProbability = journal.acceptanceRate || 30
    acceptanceProbability += keywordMatches.length * 5
    acceptanceProbability = Math.min(acceptanceProbability, 95)

    // 确定适合度
    let suitability: 'high' | 'medium' | 'low'
    if (score >= 80) suitability = 'high'
    else if (score >= 60) suitability = 'medium'
    else suitability = 'low'

    return {
      journal,
      matchScore: Math.min(Math.round(score), 100),
      matchReasons: reasons,
      suitability,
      estimatedAcceptanceProbability: Math.round(acceptanceProbability),
      pros,
      cons,
      similarArticles: [
        'Similar study published in 2023',
        'Related methodology paper',
        'Topic trending in this journal'
      ]
    }
  }

  /**
   * 获取期刊详情
   */
  async getJournalDetails(journalId: string): Promise<Journal | null> {
    return MOCK_JOURNALS.find(j => j.id === journalId) || null
  }

  /**
   * 分析投稿策略
   */
  analyzeSubmissionStrategy(recommendations: SubmissionRecommendation[]): {
    tier1: SubmissionRecommendation[] // 冲刺期刊
    tier2: SubmissionRecommendation[] // 目标期刊
    tier3: SubmissionRecommendation[] // 保底期刊
  } {
    const sorted = [...recommendations].sort((a, b) => b.matchScore - a.matchScore)

    return {
      tier1: sorted.filter(r => r.matchScore >= 80 && r.suitability === 'high').slice(0, 2),
      tier2: sorted.filter(r => r.matchScore >= 60 && r.matchScore < 80).slice(0, 3),
      tier3: sorted.filter(r => r.matchScore < 60 || r.suitability === 'low').slice(0, 2)
    }
  }

  /**
   * 生成投稿计划
   */
  generateSubmissionPlan(recommendations: SubmissionRecommendation[]): string {
    const strategy = this.analyzeSubmissionStrategy(recommendations)

    return `
# 智能投稿推荐计划

## 投稿策略分析

### Tier 1 - 冲刺期刊（高影响因子）
${strategy.tier1.map(r => `
**${r.journal.name}**
- 匹配度：${r.matchScore}%
- 预估接受概率：${r.estimatedAcceptanceProbability}%
- 理由：${r.matchReasons.join('；')}
`).join('\n')}

### Tier 2 - 目标期刊（适中难度）
${strategy.tier2.map(r => `
**${r.journal.name}**
- 匹配度：${r.matchScore}%
- 预估接受概率：${r.estimatedAcceptanceProbability}%
- 优势：${r.pros.join('，')}
`).join('\n')}

### Tier 3 - 保底期刊（确保发表）
${strategy.tier3.map(r => `
**${r.journal.name}**
- 匹配度：${r.matchScore}%
- 预估接受概率：${r.estimatedAcceptanceProbability}%
`).join('\n')}

## 建议投稿顺序
1. 首先尝试 Tier 1 期刊（如果时间允许）
2. 主要目标是 Tier 2 期刊
3. Tier 3 作为保底选择

## 注意事项
- 仔细核对期刊的收稿范围
- 关注期刊的最新影响因子变化
- 预留足够的审稿周期
- 准备应对修改意见

---
*计划生成时间：${new Date().toLocaleString('zh-CN')}*
    `.trim()
  }
}

export const journalRecommendationService = new JournalRecommendationService()
export default journalRecommendationService
