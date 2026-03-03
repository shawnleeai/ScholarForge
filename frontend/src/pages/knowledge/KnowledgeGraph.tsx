/**
 * 知识图谱可视化页面
 */
import React, { useState, useEffect } from 'react'
import {
  Card, Button, Input, Space, Typography, Empty, Spin, Row, Col, Statistic,
  List, Tag, Form, Modal, message, Tabs
} from 'antd'
import {
  SearchOutlined, ShareAltOutlined, PlusOutlined, BranchesOutlined,
  NodeIndexOutlined, HistoryOutlined
} from '@ant-design/icons'
import { knowledgeService, type KnowledgeGraph, type GraphNode } from '@/services/knowledgeService'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs
const { TextArea } = Input

const KnowledgeGraphPage: React.FC = () => {
  const [graphs, setGraphs] = useState<KnowledgeGraph[]>([])
  const [currentGraph, setCurrentGraph] = useState<KnowledgeGraph | null>(null)
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [form] = Form.useForm()

  // 获取我的图谱
  const fetchGraphs = async () => {
    try {
      const res = await knowledgeService.getMyGraphs()
      setGraphs(res.data?.data || [])
    } catch (error) {
      console.error('获取图谱失败', error)
    }
  }

  // 创建图谱
  const handleCreate = async (values: any) => {
    try {
      await knowledgeService.buildGraph({
        keywords: values.keywords.split(',').map((k: string) => k.trim()),
        text: values.text,
        depth: values.depth || 2,
        max_nodes: 100,
      })
      message.success('知识图谱构建成功')
      setCreateModalVisible(false)
      form.resetFields()
      fetchGraphs()
    } catch (error) {
      message.error('构建知识图谱失败')
    }
  }

  // 查看图谱详情
  const handleViewGraph = async (graphId: string) => {
    setLoading(true)
    try {
      const res = await knowledgeService.getGraph(graphId)
      setCurrentGraph(res.data?.data)
    } catch (error) {
      message.error('获取图谱详情失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchGraphs()
  }, [])

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}><ShareAltOutlined /> 知识图谱</Title>
      <Text type="secondary">可视化研究领域知识关系，发现研究脉络</Text>

      <Row gutter={24} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card
            title="我的图谱"
            extra={
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                onClick={() => setCreateModalVisible(true)}
              >
                新建
              </Button>
            }
          >
            <List
              dataSource={graphs}
              renderItem={(graph) => (
                <List.Item
                  actions={[
                    <Button
                      type="link"
                      size="small"
                      onClick={() => handleViewGraph(graph.id)}
                    >
                      查看
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    title={graph.name}
                    description={`${graph.stats.node_count}节点 · ${graph.stats.edge_count}关系`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col span={18}>
          {currentGraph ? (
            <Card
              title={currentGraph.name}
              extra={
                <Space>
                  <span>{currentGraph.stats.node_count} 节点</span>
                  <span>{currentGraph.stats.edge_count} 关系</span>
                </Space>
              }
            >
              {loading ? (
                <Spin size="large" />
              ) : (
                <>
                  <Row gutter={16} style={{ marginBottom: 24 }}>
                    <Col span={8}>
                      <Statistic
                        title="概念节点"
                        value={currentGraph.nodes.filter(n => n.type === 'concept').length}
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="方法节点"
                        value={currentGraph.nodes.filter(n => n.type === 'method').length}
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="论文节点"
                        value={currentGraph.nodes.filter(n => n.type === 'paper').length}
                      />
                    </Col>
                  </Row>

                  <div style={{ marginBottom: 24 }}>
                    <h4>核心概念</h4>
                    <Space wrap>
                      {currentGraph.nodes
                        .filter(n => n.importance > 0.7)
                        .slice(0, 20)
                        .map(node => (
                          <Tag key={node.id} color="blue" size="large">
                            {node.label}
                          </Tag>
                        ))}
                    </Space>
                  </div>

                  <div>
                    <h4>主要关系</h4>
                    <List
                      size="small"
                      dataSource={currentGraph.edges.slice(0, 10)}
                      renderItem={(edge) => {
                        const source = currentGraph.nodes.find(n => n.id === edge.source)
                        const target = currentGraph.nodes.find(n => n.id === edge.target)
                        return (
                          <List.Item>
                            {source?.label} <span style={{ color: '#1890ff' }}>{edge.type}</span> {target?.label}
                          </List.Item>
                        )
                      }}
                    />
                  </div>
                </>
              )}
            </Card>
          ) : (
            <Card style={{ height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Empty description="选择一个图谱查看详情或创建新图谱" />
            </Card>
          )}
        </Col>
      </Row>

      {/* 创建图谱弹窗 */}
      <Modal
        title="构建知识图谱"
        visible={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item name="keywords" label="关键词" rules={[{ required: true }]}>
            <Input placeholder="输入关键词，用逗号分隔（如：人工智能, 项目管理）" />
          </Form.Item>
          <Form.Item name="text" label="参考文本">
            <TextArea rows={4} placeholder="输入相关文本内容（可选）" />
          </Form.Item>
          <Form.Item name="depth" label="构建深度" initialValue={2}>
            <Input type="number" min={1} max={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default KnowledgeGraphPage
