/**
 * 知识图谱可视化组件
 * 使用D3.js或ECharts展示知识图谱
 */

import React, { useEffect, useRef, useState, useCallback } from 'react'
import * as echarts from 'echarts'
import {
  Card,
  Space,
  Select,
  Button,
  Input,
  Tag,
  Tooltip,
  Empty,
  Spin,
  Alert,
  Tabs,
  List,
  Avatar,
  Typography,
  Badge,
} from 'antd'
import {
  ShareAltOutlined,
  SearchOutlined,
  ReloadOutlined,
  GlobalOutlined,
  UserOutlined,
  FileTextOutlined,
  BulbOutlined,
  BankOutlined,
} from '@ant-design/icons'
import { knowledgeGraphService } from '../../services/knowledgeGraphService'
import styles from './Knowledge.module.css'

const { Title, Text } = Typography
const { TabPane } = Tabs
const { Option } = Select

interface GraphNode {
  id: string
  name: string
  category: 'author' | 'paper' | 'concept' | 'institution'
  symbolSize?: number
  value?: number
  x?: number
  y?: number
}

interface GraphLink {
  source: string
  target: string
  relation: string
  value?: number
}

interface KnowledgeGraphProps {
  initialQuery?: string
  onNodeClick?: (node: GraphNode) => void
}

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({
  initialQuery,
  onNodeClick,
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState(initialQuery || '')
  const [graphType, setGraphType] = useState<'collaboration' | 'citation' | 'concept'>('collaboration')
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] } | null>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [nodeDetails, setNodeDetails] = useState<any>(null)

  // 初始化图表
  useEffect(() => {
    if (chartRef.current) {
      chartInstance.current = echarts.init(chartRef.current)

      const handleResize = () => {
        chartInstance.current?.resize()
      }
      window.addEventListener('resize', handleResize)

      // 点击事件
      chartInstance.current.on('click', (params: any) => {
        if (params.dataType === 'node') {
          const node = params.data as GraphNode
          setSelectedNode(node)
          onNodeClick?.(node)
          loadNodeDetails(node)
        }
      })

      return () => {
        window.removeEventListener('resize', handleResize)
        chartInstance.current?.dispose()
      }
    }
  }, [onNodeClick])

  // 加载节点详情
  const loadNodeDetails = useCallback(async (node: GraphNode) => {
    try {
      let details = null
      switch (node.category) {
        case 'author':
          details = await knowledgeGraphService.getAuthor(node.id)
          break
        case 'paper':
          details = await knowledgeGraphService.getPaper(node.id)
          break
        case 'concept':
          details = await knowledgeGraphService.getConcept(node.name)
          break
      }
      setNodeDetails(details?.data || null)
    } catch (e) {
      console.error('Failed to load node details:', e)
    }
  }, [])

  // 加载图谱数据
  const loadGraphData = useCallback(async () => {
    if (!searchQuery) return

    setLoading(true)
    setError(null)

    try {
      let data = { nodes: [], links: [] }

      switch (graphType) {
        case 'collaboration':
          // 搜索作者并获取合作网络
          const authors = await knowledgeGraphService.searchAuthors(searchQuery)
          if (authors.results?.length > 0) {
            const authorId = authors.results[0].id
            data = await knowledgeGraphService.getCollaborationNetwork(authorId)
          }
          break

        case 'citation':
          // 搜索论文并获取引用网络
          const papers = await knowledgeGraphService.searchPapers(searchQuery)
          if (papers.results?.length > 0) {
            const paperId = papers.results[0].id
            data = await knowledgeGraphService.getCitationNetwork(paperId)
          }
          break

        case 'concept':
          // 获取概念相关论文
          const conceptData = await knowledgeGraphService.getConcept(searchQuery)
          if (conceptData.data) {
            data = transformConceptToGraph(conceptData.data)
          }
          break
      }

      setGraphData(data)
      updateChart(data)
    } catch (e: any) {
      setError(e.message || 'Failed to load graph data')
    } finally {
      setLoading(false)
    }
  }, [searchQuery, graphType])

  // 转换概念数据为图格式
  const transformConceptToGraph = (concept: any) => {
    const nodes: GraphNode[] = [
      {
        id: concept.name,
        name: concept.name,
        category: 'concept',
        symbolSize: 80,
      },
      ...(concept.papers?.map((p: any) => ({
        id: p.id,
        name: p.title.slice(0, 30) + '...',
        category: 'paper' as const,
        symbolSize: 40,
        value: p.citations,
      })) || []),
    ]

    const links: GraphLink[] =
      concept.papers?.map((p: any) => ({
        source: p.id,
        target: concept.name,
        relation: 'belongs_to',
      })) || []

    return { nodes, links }
  }

  // 更新图表
  const updateChart = (data: { nodes: GraphNode[]; links: GraphLink[] }) => {
    if (!chartInstance.current) return

    const categories = [
      { name: 'Author', itemStyle: { color: '#5470c6' } },
      { name: 'Paper', itemStyle: { color: '#91cc75' } },
      { name: 'Concept', itemStyle: { color: '#fac858' } },
      { name: 'Institution', itemStyle: { color: '#ee6666' } },
    ]

    const option: echarts.EChartsOption = {
      title: {
        text: `${graphType === 'collaboration' ? 'Collaboration' : graphType === 'citation' ? 'Citation' : 'Concept'} Network`,
        left: 'center',
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            return `<strong>${params.data.name}</strong><br/>Type: ${params.data.category}`
          }
          return `${params.data.relation}`
        },
      },
      legend: {
        data: categories.map((c) => c.name),
        bottom: 10,
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: data.nodes.map((n) => ({
            ...n,
            category: categories.findIndex((c) => c.name.toLowerCase() === n.category),
            label: {
              show: n.symbolSize ? n.symbolSize > 50 : true,
            },
          })),
          links: data.links,
          categories: categories,
          roam: true,
          label: {
            position: 'right',
            formatter: '{b}',
          },
          force: {
            repulsion: 300,
            edgeLength: 100,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4,
            },
          },
        },
      ],
    }

    chartInstance.current.setOption(option, true)
  }

  // 搜索处理
  const handleSearch = () => {
    loadGraphData()
  }

  // 获取类别图标
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'author':
        return <UserOutlined />
      case 'paper':
        return <FileTextOutlined />
      case 'concept':
        return <BulbOutlined />
      case 'institution':
        return <BankOutlined />
      default:
        return <GlobalOutlined />
    }
  }

  // 获取类别颜色
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'author':
        return '#5470c6'
      case 'paper':
        return '#91cc75'
      case 'concept':
        return '#fac858'
      case 'institution':
        return '#ee6666'
      default:
        return '#999'
    }
  }

  return (
    <Card className={styles.knowledgeGraphCard}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* 标题和控制区 */}
        <Space wrap style={{ justifyContent: 'space-between', width: '100%' }}>
          <Title level={4} style={{ margin: 0 }}>
            <GlobalOutlined /> Knowledge Graph
          </Title>
          <Space>
            <Select
              value={graphType}
              onChange={setGraphType}
              style={{ width: 150 }}
            >
              <Option value="collaboration">Collaboration</Option>
              <Option value="citation">Citation</Option>
              <Option value="concept">Concept</Option>
            </Select>
            <Input.Search
              placeholder="Search author, paper, or concept..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
              style={{ width: 300 }}
              enterButton={<SearchOutlined />}
            />
            <Button icon={<ReloadOutlined />} onClick={handleSearch}>
              Refresh
            </Button>
          </Space>
        </Space>

        {/* 错误提示 */}
        {error && (
          <Alert message="Error" description={error} type="error" closable />
        )}

        {/* 主内容区 */}
        <div style={{ display: 'flex', gap: 16 }}>
          {/* 图谱 */}
          <div style={{ flex: 1 }}>
            <div
              ref={chartRef}
              style={{
                width: '100%',
                height: 500,
                border: '1px solid #e8e8e8',
                borderRadius: 8,
              }}
            />
            {loading && (
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                }}
              >
                <Spin size="large" />
              </div>
            )}
            {!graphData && !loading && (
              <Empty
                description="Search to explore the knowledge graph"
                style={{ marginTop: 100 }}
              />
            )}
          </div>

          {/* 详情面板 */}
          {selectedNode && (
            <Card
              title={
                <Space>
                  {getCategoryIcon(selectedNode.category)}
                  <span>{selectedNode.name}</span>
                  <Tag color={getCategoryColor(selectedNode.category)}>
                    {selectedNode.category}
                  </Tag>
                </Space>
              }
              style={{ width: 320 }}
              extra={
                <Button
                  type="text"
                  icon={<ShareAltOutlined />}
                  onClick={() => {
                    // Share functionality
                  }}
                />
              }
            >
              {nodeDetails ? (
                <Tabs defaultActiveKey="info" size="small">
                  <TabPane tab="Info" key="info">
                    <NodeDetailsContent
                      node={selectedNode}
                      details={nodeDetails}
                    />
                  </TabPane>
                  <TabPane tab="Related" key="related">
                    <RelatedContent node={selectedNode} details={nodeDetails} />
                  </TabPane>
                </Tabs>
              ) : (
                <Spin />
              )}
            </Card>
          )}
        </div>

        {/* 统计信息 */}
        {graphData && (
          <Space wrap>
            <Badge
              count={graphData.nodes.length}
              style={{ backgroundColor: '#1890ff' }}
            />
            <Text type="secondary">Nodes</Text>
            <Badge
              count={graphData.links.length}
              style={{ backgroundColor: '#52c41a' }}
            />
            <Text type="secondary">Relationships</Text>
          </Space>
        )}
      </Space>
    </Card>
  )
}

// 节点详情内容
const NodeDetailsContent: React.FC<{ node: GraphNode; details: any }> = ({
  node,
  details,
}) => {
  if (node.category === 'author') {
    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Text strong>{details.name}</Text>
        {details.email && <Text type="secondary">{details.email}</Text>}
        {details.h_index !== undefined && (
          <Text>H-Index: {details.h_index}</Text>
        )}
        <Text>Papers: {details.papers?.length || 0}</Text>
        <Text>Co-authors: {details.coauthors?.length || 0}</Text>
      </Space>
    )
  }

  if (node.category === 'paper') {
    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Text strong>{details.title}</Text>
        {details.year && <Text>Year: {details.year}</Text>}
        {details.venue && <Text>Venue: {details.venue}</Text>}
        {details.citations !== undefined && (
          <Text>Citations: {details.citations}</Text>
        )}
        <Text>Authors: {details.authors?.join(', ')}</Text>
        {details.abstract && (
          <Text type="secondary" ellipsis={{ rows: 3 }}>
            {details.abstract}
          </Text>
        )}
      </Space>
    )
  }

  return <Text>No details available</Text>
}

// 相关内容
const RelatedContent: React.FC<{ node: GraphNode; details: any }> = ({
  node,
  details,
}) => {
  const [recommendations, setRecommendations] = useState<any[]>([])

  useEffect(() => {
    const loadRecommendations = async () => {
      try {
        if (node.category === 'author') {
          const result = await knowledgeGraphService.recommendCollaborators(node.id)
          setRecommendations(result.collaborators || [])
        } else if (node.category === 'paper') {
          const result = await knowledgeGraphService.findSimilarPapers(node.id)
          setRecommendations(result.papers || [])
        }
      } catch (e) {
        console.error('Failed to load recommendations:', e)
      }
    }

    loadRecommendations()
  }, [node])

  return (
    <List
      size="small"
      dataSource={recommendations}
      renderItem={(item) => (
        <List.Item>
          <List.Item.Meta
            title={item.author?.name || item.paper?.title}
            description={item.reason || `Similarity: ${item.similarity}`}
          />
        </List.Item>
      )}
    />
  )
}

export default KnowledgeGraph
