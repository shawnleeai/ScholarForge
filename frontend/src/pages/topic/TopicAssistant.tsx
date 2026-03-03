/**
 * 选题助手页面
 * 提供智能选题建议、可行性分析、趋势分析等功能
 */

import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Form,
  Input,
  Select,
  Button,
  Tag,
  Progress,
  Timeline,
  Space,
  Typography,
  Divider,
  Badge,
  Statistic,
  Tabs,
  List,
  Tooltip,
  Empty,
  Spin,
  message,
} from 'antd'
import {
  BulbOutlined,
  BarChartOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  StarOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery } from '@tanstack/react-query'
import { topicService, type TopicIdea, type ResearchPlan, type TrendAnalysis } from '@/services/topicService'
import styles from './TopicAssistant.module.css'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

const TopicAssistant: React.FC = () => {
  const [form] = Form.useForm()
  const [selectedTopic, setSelectedTopic] = useState<TopicIdea | null>(null)
  const [activeTab, setActiveTab] = useState('suggestions')

  // 获取选题建议
  const suggestMutation = useMutation({
    mutationFn: topicService.suggestTopics,
    onSuccess: () => {
      message.success('选题建议生成成功')
    },
    onError: () => {
      message.error('生成选题建议失败')
    },
  })

  // 生成研究计划
  const planMutation = useMutation({
    mutationFn: topicService.generateResearchPlan,
  })

  // 趋势分析
  const trendsQuery = useQuery({
    queryKey: ['trends'],
    queryFn: () => topicService.analyzeTrends({
      field: form.getFieldValue('field') || '工程管理',
      keywords: form.getFieldValue('keywords')?.join(','),
      years: 5,
    }),
    enabled: false,
  })

  const handleGenerateSuggestions = (values: any) => {
    suggestMutation.mutate({
      field: values.field,
      keywords: values.keywords.split(',').map((k: string) => k.trim()),
      interests: values.interests?.split(',').map((k: string) => k.trim()),
      degree_level: values.degree_level,
    })
  }

  const handleSelectTopic = (topic: TopicIdea) => {
    setSelectedTopic(topic)
    planMutation.mutate({
      topic: topic.title,
      duration_months: topic.estimated_duration_months,
    })
  }

  const handleSaveTopic = (topicId: string) => {
    topicService.saveTopic(topicId).then(() => {
      message.success('选题已收藏')
    })
  }

  const suggestions = (suggestMutation.data?.data?.data?.suggestions || []) as TopicIdea[]
  const researchPlan = (planMutation.data?.data?.data || null) as ResearchPlan | null
  const trends = (trendsQuery.data?.data?.data || null) as TrendAnalysis | null

  const getFeasibilityColor = (level: string) => {
    switch (level) {
      case 'high': return 'success'
      case 'medium': return 'warning'
      case 'low': return 'error'
      case 'risky': return 'default'
      default: return 'default'
    }
  }

  const getFeasibilityText = (level: string) => {
    switch (level) {
      case 'high': return '可行性高'
      case 'medium': return '可行性中'
      case 'low': return '可行性低'
      case 'risky': return '有风险'
      default: return '未知'
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <Title level={3} style={{ margin: 0 }}>
            <BulbOutlined /> 智能选题助手
          </Title>
          <Text type="secondary">基于AI分析为您提供个性化的选题建议</Text>
        </div>
      </div>

      <Row gutter={[16, 16]}>
        {/* 左侧输入区域 */}
        <Col xs={24} lg={8}>
          <Card title="研究背景设置" className={styles.inputCard}>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleGenerateSuggestions}
              initialValues={{
                field: '工程管理',
                degree_level: 'master',
              }}
            >
              <Form.Item
                name="field"
                label="研究领域"
                rules={[{ required: true, message: '请选择研究领域' }]}
              >
                <Select placeholder="选择研究领域">
                  <Option value="工程管理">工程管理</Option>
                  <Option value="计算机科学">计算机科学</Option>
                  <Option value="工商管理">工商管理</Option>
                  <Option value="教育学">教育学</Option>
                  <Option value="经济学">经济学</Option>
                  <Option value="医学">医学</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="keywords"
                label="关键词（用逗号分隔）"
                rules={[{ required: true, message: '请至少输入一个关键词' }]}
              >
                <Input placeholder="例如：人工智能, 项目管理, 协同" />
              </Form.Item>

              <Form.Item
                name="interests"
                label="研究兴趣（可选）"
              >
                <Input placeholder="例如：数字化转型, 敏捷方法" />
              </Form.Item>

              <Form.Item
                name="degree_level"
                label="学位级别"
              >
                <Select>
                  <Option value="bachelor">本科</Option>
                  <Option value="master">硕士</Option>
                  <Option value="doctor">博士</Option>
                </Select>
              </Form.Item>

              <Button
                type="primary"
                htmlType="submit"
                block
                size="large"
                loading={suggestMutation.isPending}
                icon={<BulbOutlined />}
              >
                生成选题建议
              </Button>
            </Form>

            <Divider />

            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                block
                icon={<BarChartOutlined />}
                onClick={() => trendsQuery.refetch()}
                loading={trendsQuery.isFetching}
              >
                分析研究趋势
              </Button>
            </Space>
          </Card>

          {/* 可行性评估说明 */}
          <Card style={{ marginTop: 16 }}>
            <Title level={5}>可行性评估标准</Title>
            <Space direction="vertical" size="small">
              <Badge status="success" text="高可行性：资源充足，研究基础好" />
              <Badge status="warning" text="中等可行性：需要一定资源投入" />
              <Badge status="error" text="低可行性：资源需求高，风险较大" />
              <Badge status="default" text="有风险：存在明显障碍，需谨慎" />
            </Space>
          </Card>
        </Col>

        {/* 右侧结果区域 */}
        <Col xs={24} lg={16}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'suggestions',
                label: (
                  <span>
                    <BulbOutlined /> 选题建议
                    {suggestions.length > 0 && (
                      <Badge count={suggestions.length} style={{ marginLeft: 8 }} />
                    )}
                  </span>
                ),
                children: (
                  <Spin spinning={suggestMutation.isPending}>
                    {suggestions.length > 0 ? (
                      <Row gutter={[16, 16]}>
                        {suggestions.map((topic) => (
                          <Col xs={24} key={topic.id}>
                            <Card
                              className={styles.topicCard}
                              hoverable
                              onClick={() => handleSelectTopic(topic)}
                              title={
                                <Space>
                                  <Text strong>{topic.title}</Text>
                                  <Tag color={getFeasibilityColor(topic.feasibility_level)}>
                                    {getFeasibilityText(topic.feasibility_level)}
                                  </Tag>
                                </Space>
                              }
                              extra={
                                <Button
                                  type="text"
                                  icon={<StarOutlined />}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleSaveTopic(topic.id)
                                  }}
                                >
                                  收藏
                                </Button>
                              }
                            >
                              <Paragraph>{topic.description}</Paragraph>
                              
                              <Space wrap>
                                {topic.keywords.map((kw) => (
                                  <Tag key={kw}>{kw}</Tag>
                                ))}
                              </Space>

                              <Divider style={{ margin: '12px 0' }} />

                              <Row gutter={16}>
                                <Col span={8}>
                                  <Statistic
                                    title="可行性评分"
                                    value={topic.feasibility_score}
                                    suffix="/100"
                                    valueStyle={{ color: topic.feasibility_score >= 70 ? '#52c41a' : '#faad14' }}
                                  />
                                </Col>
                                <Col span={8}>
                                  <Statistic
                                    title="预计周期"
                                    value={topic.estimated_duration_months}
                                    suffix="个月"
                                  />
                                </Col>
                                <Col span={8}>
                                  <Statistic
                                    title="风险因素"
                                    value={topic.risks.length}
                                    valueStyle={{ color: topic.risks.length > 2 ? '#ff4d4f' : '#faad14' }}
                                  />
                                </Col>
                              </Row>

                              {topic.research_gaps.length > 0 && (
                                <>
                                  <Divider style={{ margin: '12px 0' }} />
                                  <Text type="secondary">研究缺口：</Text>
                                  <ul className={styles.gapList}>
                                    {topic.research_gaps.map((gap, idx) => (
                                      <li key={idx}>
                                        <Tooltip title={gap.description}>
                                          <Text>{gap.description}</Text>
                                        </Tooltip>
                                        <Tag size="small" style={{ marginLeft: 8 }}>
                                          重要性: {gap.significance}
                                        </Tag>
                                      </li>
                                    ))}
                                  </ul>
                                </>
                              )}
                            </Card>
                          </Col>
                        ))}
                      </Row>
                    ) : (
                      <Empty
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        description="暂无选题建议，请设置研究背景后点击生成"
                      />
                    )}
                  </Spin>
                ),
              },
              {
                key: 'plan',
                label: (
                  <span>
                    <CalendarOutlined /> 研究计划
                    {researchPlan && <Badge status="processing" style={{ marginLeft: 8 }} />}
                  </span>
                ),
                children: selectedTopic ? (
                  <Spin spinning={planMutation.isPending}>
                    {researchPlan ? (
                      <Card>
                        <Title level={4}>{researchPlan.topic}</Title>
                        
                        <Row gutter={16} style={{ marginBottom: 24 }}>
                          <Col span={8}>
                            <Statistic
                              title="总周期"
                              value={researchPlan.total_weeks}
                              suffix="周"
                            />
                          </Col>
                          <Col span={8}>
                            <Statistic
                              title="阶段数"
                              value={researchPlan.phases.length}
                              suffix="个"
                            />
                          </Col>
                          <Col span={8}>
                            <Statistic
                              title="任务数"
                              value={researchPlan.tasks.length}
                              suffix="个"
                            />
                          </Col>
                        </Row>

                        <Divider />

                        <Title level={5}>甘特图预览</Title>
                        <div className={styles.ganttPreview}>
                          {researchPlan.gantt_chart.tasks.map((task) => (
                            <div key={task.id} className={styles.ganttBar}>
                              <Text className={styles.ganttLabel}>{task.name}</Text>
                              <Progress
                                percent={task.progress}
                                strokeColor={task.progress === 0 ? '#d9d9d9' : '#1890ff'}
                                showInfo={false}
                                style={{ width: 200 }}
                              />
                            </div>
                          ))}
                        </div>

                        <Divider />

                        <Title level={5}>关键里程碑</Title>
                        <Timeline mode="left">
                          {researchPlan.milestones.map((milestone, idx) => (
                            <Timeline.Item
                              key={idx}
                              label={`第${milestone.week}周`}
                              dot={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                            >
                              {milestone.name}
                            </Timeline.Item>
                          ))}
                        </Timeline>
                      </Card>
                    ) : (
                      <Empty description="请先从选题建议中选择一个选题" />
                    )}
                  </Spin>
                ) : (
                  <Empty description="请先从选题建议中选择一个选题查看研究计划" />
                ),
              },
              {
                key: 'trends',
                label: (
                  <span>
                    <BarChartOutlined /> 趋势分析
                  </span>
                ),
                children: (
                  <Spin spinning={trendsQuery.isFetching}>
                    {trends ? (
                      <div>
                        <Row gutter={[16, 16]}>
                          <Col xs={24} md={8}>
                            <Card title="热门话题">
                              <Space direction="vertical" style={{ width: '100%' }}>
                                {trends.hot_topics.map((topic) => (
                                  <Tag key={topic} color="red" style={{ margin: 4 }}>
                                    <BarChartOutlined /> {topic}
                                  </Tag>
                                ))}
                              </Space>
                            </Card>
                          </Col>
                          <Col xs={24} md={8}>
                            <Card title="新兴话题">
                              <Space direction="vertical" style={{ width: '100%' }}>
                                {trends.emerging_topics.map((topic) => (
                                  <Tag key={topic} color="green" style={{ margin: 4 }}>
                                    <LineChartOutlined /> {topic}
                                  </Tag>
                                ))}
                              </Space>
                            </Card>
                          </Col>
                          <Col xs={24} md={8}>
                            <Card title="衰退话题">
                              <Space direction="vertical" style={{ width: '100%' }}>
                                {trends.declining_topics.map((topic) => (
                                  <Tag key={topic} style={{ margin: 4 }}>
                                    {topic}
                                  </Tag>
                                ))}
                              </Space>
                            </Card>
                          </Col>
                        </Row>

                        <Card title="关键词趋势" style={{ marginTop: 16 }}>
                          <List
                            dataSource={trends.trends}
                            renderItem={(item) => (
                              <List.Item>
                                <List.Item.Meta
                                  title={
                                    <Space>
                                      <Text strong>{item.keyword}</Text>
                                      <Tag color={item.predicted_trend === 'rising' ? 'green' : item.predicted_trend === 'declining' ? 'red' : 'default'}>
                                        {item.predicted_trend === 'rising' ? '上升' : item.predicted_trend === 'declining' ? '下降' : '稳定'}
                                      </Tag>
                                    </Space>
                                  }
                                  description={
                                    <Space direction="vertical" size="small">
                                      <Text>热度: {Math.round(item.current_hotness * 100)}%</Text>
                                      <Text type="secondary">
                                        相关词: {item.related_keywords.join(', ')}
                                      </Text>
                                    </Space>
                                  }
                                />
                              </List.Item>
                            )}
                          />
                        </Card>
                      </div>
                    ) : (
                      <Empty description='点击左侧"分析研究趋势"按钮查看趋势分析' />
                    )}
                  </Spin>
                ),
              },
            ]}
          />
        </Col>
      </Row>
    </div>
  )
}

export default TopicAssistant
