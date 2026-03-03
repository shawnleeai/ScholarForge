/**
 * 模拟 API 响应（用于开发测试）
 */

// 延迟函数
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// 模拟数据
const mockData = {
  login: {
    code: 200,
    data: {
      user: {
        id: '1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'student',
        fullName: '测试用户',
        university: '浙江大学',
        major: '工程管理',
        subscriptionTier: 'free',
        isActive: true,
        isVerified: true,
        createdAt: new Date().toISOString(),
      },
      token: {
        accessToken: 'mock-token-12345',
        refreshToken: 'mock-refresh-12345',
        tokenType: 'Bearer',
        expiresIn: 86400,
      },
    },
  },
  papers: {
    code: 200,
    data: {
      items: [
        {
          id: '1',
          title: 'AI协同项目管理在学术论文辅助工具开发中的应用研究',
          abstract: '本研究探讨人工智能技术如何提升学术论文写作效率...',
          status: 'in_progress',
          paperType: 'thesis',
          wordCount: 15000,
          referenceCount: 45,
          figureCount: 8,
          createdAt: '2026-02-01T00:00:00Z',
          updatedAt: '2026-02-28T00:00:00Z',
        },
        {
          id: '2',
          title: '基于深度学习的工程管理决策支持系统研究',
          abstract: '本文研究深度学习在工程管理决策中的应用...',
          status: 'draft',
          paperType: 'thesis',
          wordCount: 5000,
          referenceCount: 20,
          figureCount: 3,
          createdAt: '2026-01-15T00:00:00Z',
          updatedAt: '2026-02-20T00:00:00Z',
        },
      ],
      total: 2,
      page: 1,
      pageSize: 20,
      totalPages: 1,
    },
  },
  sections: {
    code: 200,
    data: [
      { id: '1', paperId: '1', title: '摘要', content: '本文研究了AI协同项目管理...', orderIndex: 0, sectionType: 'abstract', wordCount: 300, status: 'completed' },
      { id: '2', paperId: '1', title: '第一章 绪论', content: '## 1.1 研究背景\n\n随着人工智能技术的快速发展...', orderIndex: 1, sectionType: 'chapter', wordCount: 2500, status: 'in_progress' },
      { id: '3', paperId: '1', title: '第二章 文献综述', content: '', orderIndex: 2, sectionType: 'chapter', wordCount: 0, status: 'draft' },
    ],
  },
  library: {
    code: 200,
    data: {
      items: [
        {
          id: '1',
          article: {
            id: 'a1',
            title: 'Artificial Intelligence in Project Management',
            authors: [{ name: 'John Smith' }],
            sourceName: 'Int. J. of Project Management',
            sourceDb: 'wos',
            publicationYear: 2024,
            citationCount: 45,
          },
          isFavorite: true,
          isRead: true,
          tags: ['重要'],
          addedAt: '2026-02-15T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      pageSize: 20,
      totalPages: 1,
    },
  },
  aiWriting: {
    code: 200,
    data: {
      generatedText: '基于上述研究背景，本研究将采用混合研究方法...',
      taskType: 'continue',
      provider: 'mock',
      tokensUsed: 150,
    },
  },
}

// 模拟 API 请求
export const mockApi = {
  async post(url: string, _data?: unknown) {
    await delay(300)
    if (url.includes('/auth/login')) {
      return mockData.login
    }
    if (url.includes('/ai/writing')) {
      return mockData.aiWriting
    }
    return { code: 200, data: {} }
  },

  async get(url: string, _params?: unknown) {
    await delay(200)
    if (url.includes('/users/me')) {
      const auth = localStorage.getItem('scholarforge-auth')
      if (auth) {
        const parsed = JSON.parse(auth)
        return { code: 200, data: parsed.user }
      }
      throw { code: 401, message: 'Unauthorized' }
    }
    if (url.includes('/papers') && !url.includes('sections')) {
      return mockData.papers
    }
    if (url.includes('/sections')) {
      return mockData.sections
    }
    if (url.includes('/library')) {
      return mockData.library
    }
    return { code: 200, data: {} }
  },

  async put(_url: string, data?: unknown) {
    await delay(200)
    return { code: 200, data: data ? { ...data as object, id: '1' } : { id: '1' } }
  },

  async delete(_url: string) {
    await delay(200)
    return { code: 200, message: 'Success' }
  },
}
