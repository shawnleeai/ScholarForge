/**
 * 演示数据
 */

export interface DemoStep {
  id: string
  target: string
  title: string
  content: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
  action?: () => void
}

export const demoSteps: DemoStep[] = [
  {
    id: 'welcome',
    target: '.dashboard-welcome',
    title: '欢迎使用 ScholarForge',
    content: 'ScholarForge 是您的一站式学术研究平台。让我带您了解主要功能。',
    placement: 'bottom'
  },
  {
    id: 'daily-feed',
    target: '.daily-feed-card',
    title: '每日论文推荐',
    content: '基于您的研究兴趣，我们每天为您推荐最新、最相关的学术论文。',
    placement: 'right'
  },
  {
    id: 'library',
    target: '[href="/library"]',
    title: '文献库',
    content: '管理和组织您的文献收藏。支持PDF批注、标签分类和智能搜索。',
    placement: 'right'
  },
  {
    id: 'ai-assistant',
    target: '.ai-panel-trigger',
    title: 'AI研究助手',
    content: '随时向AI助手提问，获取基于您文献库的智能回答。',
    placement: 'left'
  },
  {
    id: 'paper-writing',
    target: '[href="/papers"]',
    title: '论文写作',
    content: '使用AI辅助的编辑器撰写论文，包括大纲生成、智能续写和引用管理。',
    placement: 'right'
  }
]

export const samplePapers = [
  {
    id: 'paper_001',
    title: 'Attention Is All You Need',
    authors: ['Ashish Vaswani', 'Noam Shazeer', 'Niki Parmar'],
    year: 2017,
    abstract: 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
    citations: 85000
  },
  {
    id: 'paper_002',
    title: 'BERT: Pre-training of Deep Bidirectional Transformers',
    authors: ['Jacob Devlin', 'Ming-Wei Chang', 'Kenton Lee'],
    year: 2019,
    abstract: 'We introduce a new language representation model called BERT.',
    citations: 65000
  },
  {
    id: 'paper_003',
    title: 'Language Models are Few-Shot Learners',
    authors: ['Tom B. Brown', 'Benjamin Mann', 'Nick Ryder'],
    year: 2020,
    abstract: 'We demonstrate that scaling up language models greatly improves task-agnostic performance.',
    citations: 28000
  }
]

export const demoQA = [
  {
    question: 'Transformer架构的核心创新是什么？',
    answer: 'Transformer的核心创新在于完全基于注意力机制（Attention Mechanism），摒弃了传统的循环（RNN）和卷积（CNN）结构。主要创新点包括：\n\n1. **自注意力机制（Self-Attention）**：允许模型同时关注输入序列的所有位置，捕捉长距离依赖关系。\n\n2. **多头注意力（Multi-Head Attention）**：通过多个注意力头并行学习不同的子空间表示。\n\n3. **位置编码（Positional Encoding）**：由于没有递归结构，通过位置编码注入序列位置信息。\n\n4. **残差连接和层归一化**：帮助训练深层网络。',
    sources: ['paper_001', 'paper_002']
  },
  {
    question: '大语言模型如何进行预训练？',
    answer: '大语言模型通常采用以下预训练策略：\n\n1. **掩码语言模型（MLM）**：如BERT，随机掩盖输入中的部分词汇，让模型预测被掩盖的词。\n\n2. **因果语言模型（CLM）**：如GPT，基于前文预测下一个词。\n\n3. **去噪自动编码**：在损坏的输入上重建原始文本。\n\n预训练数据通常包括大量的网页文本、书籍、学术论文等，通过在大规模无标注数据上学习，模型获得了丰富的语言知识和世界知识。',
    sources: ['paper_002', 'paper_003']
  }
]
