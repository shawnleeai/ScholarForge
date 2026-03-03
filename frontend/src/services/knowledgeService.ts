/**
 * 知识图谱服务
 */

import api from './api'

export type NodeType = 'concept' | 'method' | 'theory' | 'person' | 'paper' | 'institution' | 'keyword' | 'domain'
export type RelationType = 'related_to' | 'part_of' | 'derived_from' | 'applies' | 'cites' | 'authored_by' | 'belongs_to' | 'uses'

export interface GraphNode {
  id: string
  label: string
  type: NodeType
  properties: Record<string, any>
  importance: number
  x?: number
  y?: number
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: RelationType
  weight: number
  properties: Record<string, any>
}

export interface KnowledgeGraph {
  id: string
  name: string
  description?: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  stats: {
    node_count: number
    edge_count: number
  }
  created_at: string
}

export interface ConceptExtraction {
  concept: string
  type: NodeType
  confidence: number
  context: string
  position: {
    start: number
    end: number
  }
}

export interface GraphPath {
  nodes: Array<{
    id: string
    label: string
    type: NodeType
  }>
  edges: Array<{
    type: RelationType
    properties?: Record<string, any>
  }>
  length: number
  weight: number
}

export interface GraphStatistics {
  total_nodes: number
  total_edges: number
  node_types: Record<string, number>
  relation_types: Record<string, number>
  avg_degree: number
  density: number
  hub_nodes: Array<{
    id: string
    label: string
    degree: number
  }>
  clusters: Array<{
    id: string
    name: string
    size: number
  }>
}

export interface ResearchLineage {
  topic: string
  timeline: Array<{
    year: number
    paper_count: number
    key_events: string[]
    hot_keywords: string[]
  }>
  key_papers: Array<{
    title: string
    year: number
    citations: number
    authors: string[]
  }>
  evolution: Array<{
    period: string
    focus: string
    methods: string[]
  }>
  future_directions: string[]
}

export const knowledgeService = {
  // 构建知识图谱
  buildGraph: (data: {
    paper_id?: string
    text?: string
    keywords: string[]
    depth?: number
    max_nodes?: number
  }) => api.post('/knowledge/build', data),

  // 获取知识图谱
  getGraph: (graphId: string) =>
    api.get(`/knowledge/${graphId}`),

  // 抽取概念实体
  extractConcepts: (text: string) =>
    api.post('/knowledge/extract', null, { params: { text } }),

  // 查询概念路径
  queryPath: (data: {
    start_node: string
    end_node: string
    max_depth?: number
    relation_types?: RelationType[]
  }) => api.post('/knowledge/path', data),

  // 获取节点邻域
  getNeighborhood: (graphId: string, nodeId: string, depth?: number) =>
    api.get(`/knowledge/${graphId}/neighborhood`, { params: { node_id: nodeId, depth } }),

  // 获取图谱统计
  getGraphStats: (graphId: string) =>
    api.get(`/knowledge/${graphId}/stats`),

  // 获取研究脉络
  getResearchLineage: (topic: string, years?: number) =>
    api.get('/knowledge/lineage', { params: { topic, years } }),

  // 跨领域关联发现
  discoverCrossDomain: (domain1: string, domain2: string) =>
    api.get('/knowledge/cross-domain', { params: { domain1, domain2 } }),

  // 获取我的图谱
  getMyGraphs: () =>
    api.get('/knowledge/my'),
}

export default knowledgeService
