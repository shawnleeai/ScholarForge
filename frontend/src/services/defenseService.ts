/**
 * 答辩准备服务 API
 */

import api, { request } from './api'
import type { DefenseChecklist, DefensePPT, DefenseQA, MockSession } from '@/types/defense'

// 是否使用模拟模式
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

// 模拟检查清单
const mockChecklist: DefenseChecklist = {
  id: 'checklist-1',
  paperId: '1',
  items: [
    { id: '1', category: '文档', content: '论文终稿定稿并导师签字', completed: true, order: 1 },
    { id: '2', category: '文档', content: '查重报告（符合学校要求）', completed: true, order: 2 },
    { id: '3', category: '文档', content: '答辩申请表填写完整', completed: false, order: 3 },
    { id: '4', category: '文档', content: '答辩决议书准备', completed: false, order: 4 },
    { id: '5', category: 'PPT', content: '答辩PPT初稿完成', completed: true, order: 5 },
    { id: '6', category: 'PPT', content: 'PPT时长控制在规定范围内', completed: false, order: 6 },
    { id: '7', category: 'PPT', content: 'PPT视觉效果优化', completed: false, order: 7 },
    { id: '8', category: '演练', content: '完成自我陈述演练', completed: false, order: 8 },
    { id: '9', category: '演练', content: '模拟问答3次以上', completed: false, order: 9 },
    { id: '10', category: '准备', content: '熟悉答辩委员会成员研究方向', completed: false, order: 10 },
    { id: '11', category: '准备', content: '准备纸笔记录问题', completed: true, order: 11 },
    { id: '12', category: '准备', content: '准备论文副本供评委翻阅', completed: false, order: 12 },
  ],
  progress: 33.3,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
}

// 模拟PPT大纲
const mockPPT: DefensePPT = {
  id: 'ppt-1',
  paperId: '1',
  template: 'academic',
  outline: {
    title: '基于深度学习的图像分类方法研究',
    slides: [
      { id: 's1', type: 'title', title: '封面', content: '基于深度学习的图像分类方法研究\n答辩人：张三\n导师：李四教授', order: 0 },
      { id: 's2', type: 'content', title: '研究背景与意义', content: '• 图像分类是计算机视觉的基础任务\n• 传统方法的局限性\n• 深度学习的优势与应用前景', order: 1, duration: 120 },
      { id: 's3', type: 'content', title: '国内外研究现状', content: '• 经典网络结构回顾\n• 最新研究进展\n• 现有方法的不足', order: 2, duration: 120 },
      { id: 's4', type: 'content', title: '研究内容与方法', content: '• 网络架构设计\n• 损失函数优化\n• 数据增强策略', order: 3, duration: 180 },
      { id: 's5', type: 'content', title: '主要创新点', content: '• 创新点一：提出新的注意力机制\n• 创新点二：设计轻量级网络结构\n• 创新点三：改进训练策略', order: 4, duration: 150 },
      { id: 's6', type: 'content', title: '实验结果与分析', content: '• 数据集介绍\n• 与SOTA方法对比\n• 消融实验分析', order: 5, duration: 180 },
      { id: 's7', type: 'content', title: '结论与展望', content: '• 工作总结\n• 主要贡献\n• 未来研究方向', order: 6, duration: 90 },
      { id: 's8', type: 'thanks', title: '致谢', content: '感谢导师的悉心指导\n感谢各位评委老师\n恳请各位老师批评指正', order: 7, duration: 30 },
    ]
  },
  status: 'generated',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
}

// 模拟问答
const mockQA: DefenseQA[] = [
  {
    id: 'qa1',
    question: '你的研究的主要创新点是什么？',
    answer: '本研究的主要创新点有三个方面：第一，提出了一种新的注意力机制，能够有效捕捉图像中的关键特征；第二，设计了轻量级的网络结构，在保持精度的同时显著降低了计算复杂度；第三，改进了训练策略，提高了模型的泛化能力。',
    category: '创新点',
    difficulty: 'medium',
  },
  {
    id: 'qa2',
    question: '你的研究方法与其他方法相比有什么优势？',
    answer: '相比传统方法，本研究采用的方法具有以下优势：首先，在准确率方面有显著提升，在标准数据集上达到了SOTA水平；其次，推理速度更快，适合实际部署；最后，模型更加轻量，可以在资源受限的设备上运行。',
    category: '方法',
    difficulty: 'medium',
  },
  {
    id: 'qa3',
    question: '你的研究结果的实际应用价值是什么？',
    answer: '研究结果可以在以下方面得到应用：第一，智能安防领域的实时监控；第二，医学影像的自动诊断辅助；第三，工业质检的自动化检测；第四，自动驾驶的环境感知。这些应用都能够从本研究的方法中获益。',
    category: '应用',
    difficulty: 'easy',
  },
  {
    id: 'qa4',
    question: '实验结果是否充分证明了你的方法的有效性？',
    answer: '是的。我们从多个角度验证了方法的有效性：首先，在多个公开数据集上与主流方法进行了对比实验；其次，进行了详细的消融实验，验证了各个组件的贡献；最后，还进行了鲁棒性测试，证明方法在不同条件下都能保持稳定性能。',
    category: '实验',
    difficulty: 'hard',
  },
  {
    id: 'qa5',
    question: '如果继续研究，你会从哪些方面改进？',
    answer: '未来研究可以从以下几个方向展开：第一，探索更高效的特征提取方式；第二，研究模型的可解释性；第三，将该方法扩展到其他视觉任务；第四，研究半监督和自监督学习范式下的模型训练。',
    category: '展望',
    difficulty: 'medium',
  },
]

export const defenseService = {
  /**
   * 获取答辩检查清单
   */
  getChecklist: async (paperId: string): Promise<{ data: DefenseChecklist }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      return { data: { ...mockChecklist, paperId } }
    }
    return api.get(`/defense/checklist/${paperId}`)
  },

  /**
   * 更新检查清单
   */
  updateChecklist: async (checklistId: string, items: any[]): Promise<{ data: { success: boolean } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      return { data: { success: true } }
    }
    return api.put(`/defense/checklist/${checklistId}`, { items })
  },

  /**
   * 获取PPT大纲
   */
  getPPT: async (paperId: string): Promise<{ data: DefensePPT }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      return { data: { ...mockPPT, paperId } }
    }
    return api.get(`/defense/ppt/${paperId}`)
  },

  /**
   * 生成PPT大纲
   */
  generatePPT: async (paperId: string, template: string = 'academic'): Promise<{ data: DefensePPT }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 1500))
      return { data: mockPPT }
    }
    return api.post(`/defense/ppt/generate/${paperId}`, null, { params: { template } })
  },

  /**
   * 更新PPT大纲
   */
  updatePPT: async (pptId: string, outline: any): Promise<{ data: { success: boolean } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200))
      return { data: { success: true } }
    }
    return api.put(`/defense/ppt/${pptId}`, { outline })
  },

  /**
   * 获取问答列表
   */
  getQAList: async (params?: { paperId?: string; category?: string; difficulty?: string }): Promise<{ data: DefenseQA[] }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 300))
      return { data: mockQA }
    }
    return api.get('/defense/qa', { params })
  },

  /**
   * 生成问答
   */
  generateQA: async (paperId: string, count: number = 10): Promise<{ data: { generated: number; questions: DefenseQA[] } }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 1000))
      return { data: { generated: mockQA.length, questions: mockQA } }
    }
    return api.post(`/defense/qa/generate/${paperId}`, null, { params: { count } })
  },

  /**
   * 开始模拟答辩
   */
  startMock: async (paperId: string): Promise<{ data: MockSession }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500))
      return {
        data: {
          id: generateId(),
          paperId,
          status: 'ongoing',
          questions: mockQA.slice(0, 3).map(q => ({
            id: q.id,
            question: q.question,
            difficulty: q.difficulty,
          })),
          createdAt: new Date().toISOString(),
        }
      }
    }
    return api.post(`/defense/mock/start/${paperId}`)
  },

  /**
   * 提交回答
   */
  submitAnswer: async (sessionId: string, data: { questionId: string; question: string; answer: string }): Promise<{
    data: { answerId: string; score: number; feedback: string }
  }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 800))
      const score = Math.floor(Math.random() * 30) + 70  // 70-100
      return {
        data: {
          answerId: generateId(),
          score,
          feedback: score >= 85
            ? '回答很好，逻辑清晰，内容充实。建议可以适当补充更多具体案例。'
            : '回答基本正确，但有些地方不够深入。建议加强对核心概念的理解。',
        }
      }
    }
    return api.post(`/defense/mock/answer/${sessionId}`, data)
  },

  /**
   * 完成模拟答辩
   */
  completeMock: async (sessionId: string): Promise<{
    data: { sessionId: string; totalScore: number; grade: string; suggestions: string[] }
  }> => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500))
      return {
        data: {
          sessionId,
          totalScore: 85,
          grade: '良好',
          suggestions: [
            '继续保持对研究内容的深入理解',
            '注意控制回答时间，简洁明了',
            '建议多准备几个具体案例',
          ],
        }
      }
    }
    return api.post(`/defense/mock/complete/${sessionId}`)
  },
}
