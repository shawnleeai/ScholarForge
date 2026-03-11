/**
 * ScholarForge 前端类型定义
 */

// ============== 用户相关 ==============

export interface User {
  id: string
  email: string
  username: string
  role: 'student' | 'teacher' | 'researcher' | 'institution' | 'admin'
  fullName?: string
  avatarUrl?: string
  bio?: string
  university?: string
  department?: string
  major?: string
  researchInterests?: string[]
  subscriptionTier: 'free' | 'pro' | 'team' | 'enterprise'
  isActive: boolean
  isVerified: boolean
  createdAt: string
  lastLoginAt?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  fullName?: string
  university?: string
  major?: string
}

export interface TokenResponse {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
}

export interface AuthResponse {
  user: User
  token: TokenResponse
}

// ============== 论文相关 ==============

export interface Paper {
  id: string
  title: string
  abstract?: string
  keywords?: string[]
  paperType: 'thesis' | 'journal' | 'conference' | 'report'
  status: 'draft' | 'in_progress' | 'review' | 'revision' | 'submitted' | 'accepted' | 'published'
  language: string
  ownerId: string
  teamId?: string
  templateId?: string
  citationStyle: string
  wordCount: number
  pageCount: number
  figureCount: number
  tableCount: number
  referenceCount: number
  createdAt: string
  updatedAt: string
  submittedAt?: string
  publishedAt?: string
}

export interface PaperSection {
  id: string
  paperId: string
  parentId?: string
  title?: string
  content?: string
  orderIndex: number
  sectionType?: string
  wordCount: number
  status: string
  createdAt: string
  updatedAt: string
  children?: PaperSection[]
}

export interface PaperCollaborator {
  id: string
  userId: string
  role: 'owner' | 'editor' | 'reviewer' | 'viewer'
  canEdit: boolean
  canComment: boolean
  canShare: boolean
  invitedAt: string
  acceptedAt?: string
  user?: User
}

// ============== 文献相关 ==============

export interface Article {
  id: string
  doi?: string
  title: string
  authors?: ArticleAuthor[]
  abstract?: string
  keywords?: string[]
  sourceType?: string
  sourceName?: string
  sourceDb?: 'cnki' | 'wos' | 'ieee' | 'arxiv'
  publicationYear?: number
  publicationDate?: string
  volume?: string
  issue?: string
  pages?: string
  citationCount: number
  impactFactor?: number
  pdfUrl?: string
  sourceUrl?: string
  indexedAt: string
  updatedAt: string
}

export interface ArticleAuthor {
  name: string
  orcid?: string
  affiliation?: string
}

export interface LibraryItem {
  id: string
  article: Article
  isFavorite: boolean
  isRead: boolean
  readAt?: string
  notes?: string
  tags?: string[]
  folderId?: string
  addedAt: string
}

export interface LibraryFolder {
  id: string
  name: string
  description?: string
  parentId?: string
  color?: string
  createdAt: string
  articleCount: number
}

// ============== AI 相关 ==============

export type WritingTaskType = 'continue' | 'rewrite' | 'polish' | 'expand' | 'summarize' | 'translate'

export interface Citation {
  id: string
  title: string
  authors: string[]
  journal?: string
  year?: number
  doi?: string
  url?: string
  abstract?: string
  source?: string
  similarity?: number
  relevance_score?: number
  snippet?: string
}

export interface WritingRequest {
  taskType: WritingTaskType
  text?: string
  context?: string
  paperId?: string
  sectionId?: string
  maxTokens?: number
  temperature?: number
  sourceLanguage?: string
  targetLanguage?: string
}

export interface WritingResponse {
  generatedText: string
  taskType: WritingTaskType
  provider: string
  tokensUsed: number
  suggestions?: string[]
}

// ============== 通用类型 ==============

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data?: T
  timestamp: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface PaginationParams {
  page: number
  pageSize: number
}

export interface ApiError {
  code: string
  message: string
  details?: unknown
}

// ============== 评论相关 ==============

export * from './comment'

// ============== 查重相关 ==============

export * from './plagiarism'

// ============== 格式检查相关 ==============

export * from './format'
