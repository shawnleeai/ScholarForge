/**
 * 进度管理页面
 * 甘特图、里程碑、任务管理、预警系统
 */

import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Button,
  Timeline,
  Tag,
  Space,
  Typography,
  Badge,
  Statistic,
  Tabs,
  List,
  Progress,
  Alert,
  Empty,
  Spin,
  Tooltip,
  Select,
  Form,
  Modal,
  DatePicker,
  Input,
  message,
  Popconfirm,
  Divider,
} from 'antd'
import {
  CalendarOutlined,
  FlagOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  BellOutlined,
  BarChartOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Dayjs } from 'dayjs'
import dayjs from 'dayjs'
import { progressService } from '@/services/progressService'
import type { Milestone, Task, Alert as ProgressAlert, GanttChart } from '@/types/progress'
import { paperService } from '@/services/paperService'
import styles from './ProgressManager.module.css'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { TextArea } = Input
const { RangePicker } = DatePicker

const ProgressManager: React.FC = () => {
  const [selectedPaper, setSelectedPaper] = useState<string>('')
  const [isMilestoneModalOpen, setIsMilestoneModalOpen] = useState(false)
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false)
  const [editingMilestone, setEditingMilestone] = useState<Milestone | null>(null)
  const [milestoneForm] = Form.useForm()
  const [taskForm] = Form.useForm()
  const queryClient = useQueryClient()

  // 获取论文列表
  const { data: papersData } = useQuery({
    queryKey: ['papers'],
    queryFn: () => paperService.getPapers({ page: 1, pageSize: 100 }),
  })

  const papers = papersData?.data?.data?.items || []

  // 获取里程碑
  const { data: milestonesData, isLoading: milestonesLoading } = useQuery({
    queryKey: ['milestones', selectedPaper],
    queryFn: () => progressService.getMilestones(selectedPaper),
    enabled: !!selectedPaper,
  })

  // 获取任务
  const { data: tasksData, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', selectedPaper],
    queryFn: () => progressService.getTasks(selectedPaper),
    enabled: !!selectedPaper,
  })

  // 获取甘特图
  const { data: ganttData, isLoading: ganttLoading } = useQuery({
    queryKey: ['gantt', selectedPaper],
    queryFn: () => progressService.getGanttChart(selectedPaper),
    enabled: !!selectedPaper,
  })

  // 获取预警
  const { data: alertsData, isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts', selectedPaper],
    queryFn: () => progressService.getAlerts(selectedPaper),
    enabled: !!selectedPaper,
  })

  // 获取进度报告
  const { data: reportData, isLoading: reportLoading } = useQuery({
    queryKey: ['progressReport', selectedPaper],
    queryFn: () => progressService.getProgressReport(selectedPaper),
    enabled: !!selectedPaper,
  })

  // 创建里程碑
  const createMilestoneMutation = useMutation({
    mutationFn: (data: { title: string; description: string; planned_date: string }) =>
      progressService.createMilestone(selectedPaper, data),
    onSuccess: () => {
      message.success('里程碑创建成功')
      queryClient.invalidateQueries({ queryKey: ['milestones', selectedPaper] })
      setIsMilestoneModalOpen(false)
      milestoneForm.resetFields()
    },
  })

  // 创建任务
  const createTaskMutation = useMutation({
    mutationFn: (data: any) => progressService.createTask(selectedPaper, data),
    onSuccess: () => {
      message.success('任务创建成功')
      queryClient.invalidateQueries({ queryKey: ['tasks', selectedPaper] })
      setIsTaskModalOpen(false)
      taskForm.resetFields()
    },
  })

  // 解决预警
  const resolveAlertMutation = useMutation({
    mutationFn: ({ alertId, note }: { alertId: string; note: string }) =>
      progressService.resolveAlert(alertId, note),
    onSuccess: () => {
      message.success('预警已解决')
      queryClient.invalidateQueries({ queryKey: ['alerts', selectedPaper] })
    },
  })

  const milestones = milestonesData?.data?.data || []
  const tasks = tasksData?.data?.data || []
  const gantt = ganttData?.data?.data as GanttChart | null
  const alerts = alertsData?.data?.data || []
  const report = reportData?.data?.data

  const handleCreateMilestone = (values: any) => {
    createMilestoneMutation.mutate({
      title: values.title,
      description: values.description,
      planned_date: values.planned_date.format('YYYY-MM-DD'),
    })
  }

  const handleCreateTask = (values: any) => {
    createTaskMutation.mutate({
      title: values.title,
      description: values.description,
      milestone_id: values.milestone_id,
      priority: values.priority,
      planned_start: values.date_range?.[0]?.format('YYYY-MM-DD'),
      planned_end: values.date_range?.[1]?.format('YYYY-MM-DD'),
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'in_progress': return 'processing'
      case 'delayed': return 'error'
      case 'pending': return 'default'
      default: return 'default'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成'
      case 'in_progress': return '进行中'
      case 'delayed': return '已延期'
      case 'pending': return '待开始'
      default: return status
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'red'
      case 'high': return 'orange'
      case 'medium': return 'blue'
      case 'low': return 'default'
      default: return 'default'
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <Title level={3} style={{ margin: 0 }}>
            <CalendarOutlined /> 进度管理
          </Title>
          <Text type="secondary">跟踪论文写作进度，管理里程碑和任务</Text>
        </div>
        <Select
          placeholder="选择论文"
          style={{ width: 300 }}
          value={selectedPaper || undefined}
          onChange={setSelectedPaper}
        >
          {papers.map((paper: any) => (
            <Option key={paper.id} value={paper.id}>{paper.title}</Option>
          ))}
        </Select>
      </div>

      {!selectedPaper ? (
        <Empty description="请先选择一篇论文" style={{ marginTop: 100 }} />
      ) : (
        <>
          {/* 统计卡片 */}
          {report && (
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col xs={24} sm={12} lg={4}>
                <Card>
                  <Statistic
                    title="总体进度"
                    value={report.stats.overall_progress}
                    suffix="%"
                    valueStyle={{ color: report.stats.on_track ? '#52c41a' : '#faad14' }}
                  />
                  <Progress percent={Math.round(report.stats.overall_progress)} size="small" />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={4}>
                <Card>
                  <Statistic
                    title="里程碑"
                    value={report.stats.completed_milestones}
                    suffix={`/${report.stats.total_milestones}`}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={4}>
                <Card>
                  <Statistic
                    title="已完成任务"
                    value={report.stats.completed_tasks}
                    suffix={`/${report.stats.total_tasks}`}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={4}>
                <Card>
                  <Statistic
                    title="剩余天数"
                    value={report.stats.days_remaining}
                    suffix="天"
                    valueStyle={{ color: report.stats.days_remaining < 30 ? '#ff4d4f' : '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={4}>
                <Card>
                  <Statistic
                    title="延期里程碑"
                    value={report.stats.delayed_milestones}
                    valueStyle={{ color: report.stats.delayed_milestones > 0 ? '#ff4d4f' : '#52c41a' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={4}>
                <Card>
                  <Statistic
                    title="风险预警"
                    value={alerts.filter((a: ProgressAlert) => !a.is_read).length}
                    valueStyle={{ color: alerts.filter((a: ProgressAlert) => !a.is_read).length > 0 ? '#ff4d4f' : '#52c41a' }}
                  />
                </Card>
              </Col>
            </Row>
          )}

          <Tabs
            items={[
              {
                key: 'gantt',
                label: (
                  <span>
                    <BarChartOutlined /> 甘特图
                  </span>
                ),
                children: (
                  <Spin spinning={ganttLoading}>
                    {gantt ? (
                      <Card>
                        <div className={styles.ganttContainer}>
                          {gantt.items.map((item) => (
                            <div key={item.id} className={styles.ganttRow}>
                              <div className={styles.ganttLabel}>{item.name}</div>
                              <div className={styles.ganttBarContainer}>
                                <Tooltip title={`${dayjs(item.start).format('MM-DD')} ~ ${dayjs(item.end).format('MM-DD')}`}>
                                  <div
                                    className={styles.ganttBar}
                                    style={{
                                      width: `${Math.max(item.progress, 5)}%`,
                                      backgroundColor: item.progress === 100 ? '#52c41a' : item.progress > 0 ? '#1890ff' : '#d9d9d9',
                                    }}
                                  >
                                    <span className={styles.ganttProgress}>{item.progress}%</span>
                                  </div>
                                </Tooltip>
                              </div>
                            </div>
                          ))}
                        </div>
                        <Divider />
                        <div className={styles.ganttLegend}>
                          <Space>
                            <Badge color="#52c41a" text="已完成" />
                            <Badge color="#1890ff" text="进行中" />
                            <Badge color="#d9d9d9" text="未开始" />
                          </Space>
                        </div>
                      </Card>
                    ) : (
                      <Empty description="暂无甘特图数据" />
                    )}
                  </Spin>
                ),
              },
              {
                key: 'milestones',
                label: (
                  <span>
                    <FlagOutlined /> 里程碑
                    <Badge count={milestones.length} style={{ marginLeft: 8 }} />
                  </span>
                ),
                children: (
                  <Spin spinning={milestonesLoading}>
                    <Card
                      title="里程碑列表"
                      extra={
                        <Button
                          type="primary"
                          icon={<PlusOutlined />}
                          onClick={() => setIsMilestoneModalOpen(true)}
                        >
                          新建里程碑
                        </Button>
                      }
                    >
                      <Timeline mode="left">
                        {milestones.map((milestone: Milestone) => (
                          <Timeline.Item
                            key={milestone.id}
                            label={dayjs(milestone.planned_date).format('YYYY-MM-DD')}
                            dot={
                              milestone.status === 'completed' ? (
                                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                              ) : milestone.status === 'delayed' ? (
                                <WarningOutlined style={{ color: '#ff4d4f' }} />
                              ) : (
                                <ClockCircleOutlined style={{ color: '#1890ff' }} />
                              )
                            }
                          >
                            <div className={styles.milestoneItem}>
                              <Space>
                                <Text strong>{milestone.title}</Text>
                                <Tag color={getStatusColor(milestone.status)}>
                                  {getStatusText(milestone.status)}
                                </Tag>
                              </Space>
                              {milestone.description && (
                                <Paragraph type="secondary" style={{ margin: '4px 0' }}>
                                  {milestone.description}
                                </Paragraph>
                              )}
                              <Progress
                                percent={milestone.completion_percentage}
                                size="small"
                                style={{ width: 200 }}
                              />
                            </div>
                          </Timeline.Item>
                        ))}
                      </Timeline>
                    </Card>
                  </Spin>
                ),
              },
              {
                key: 'tasks',
                label: (
                  <span>
                    <CheckCircleOutlined /> 任务
                    <Badge count={tasks.length} style={{ marginLeft: 8 }} />
                  </span>
                ),
                children: (
                  <Spin spinning={tasksLoading}>
                    <Card
                      title="任务列表"
                      extra={
                        <Button
                          type="primary"
                          icon={<PlusOutlined />}
                          onClick={() => setIsTaskModalOpen(true)}
                        >
                          新建任务
                        </Button>
                      }
                    >
                      <List
                        dataSource={tasks}
                        renderItem={(task: Task) => (
                          <List.Item
                            actions={[
                              <Button type="text" icon={<EditOutlined />} />,
                              <Button type="text" danger icon={<DeleteOutlined />} />,
                            ]}
                          >
                            <List.Item.Meta
                              title={
                                <Space>
                                  <Text strong>{task.title}</Text>
                                  <Tag color={getStatusColor(task.status)}>
                                    {getStatusText(task.status)}
                                  </Tag>
                                  <Tag color={getPriorityColor(task.priority)}>
                                    {task.priority === 'urgent' ? '紧急' : task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低'}
                                  </Tag>
                                </Space>
                              }
                              description={
                                <Space direction="vertical" size="small">
                                  {task.description && <Text type="secondary">{task.description}</Text>}
                                  <Text type="secondary">
                                    计划时间: {task.planned_start ? dayjs(task.planned_start).format('MM-DD') : '-'} ~ {task.planned_end ? dayjs(task.planned_end).format('MM-DD') : '-'}
                                  </Text>
                                </Space>
                              }
                            />
                            <Progress percent={task.progress} style={{ width: 100 }} />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Spin>
                ),
              },
              {
                key: 'alerts',
                label: (
                  <span>
                    <BellOutlined /> 预警
                    {alerts.filter((a: ProgressAlert) => !a.is_read).length > 0 && (
                      <Badge count={alerts.filter((a: ProgressAlert) => !a.is_read).length} style={{ marginLeft: 8 }} />
                    )}
                  </span>
                ),
                children: (
                  <Spin spinning={alertsLoading}>
                    <Card title="风险预警">
                      <List
                        dataSource={alerts}
                        renderItem={(alert: ProgressAlert) => (
                          <List.Item
                            actions={[
                              <Popconfirm
                                title="确认解决此预警？"
                                onConfirm={() => resolveAlertMutation.mutate({ alertId: alert.id, note: '已处理' })}
                              >
                                <Button type="primary" size="small">
                                  解决
                                </Button>
                              </Popconfirm>,
                            ]}
                          >
                            <Alert
                              message={
                                <Space>
                                  <Text strong>{alert.title}</Text>
                                  <Tag color={alert.severity === 'critical' ? 'red' : alert.severity === 'high' ? 'orange' : alert.severity === 'medium' ? 'blue' : 'default'}>
                                    {alert.severity === 'critical' ? '严重' : alert.severity === 'high' ? '高' : alert.severity === 'medium' ? '中' : '低'}
                                  </Tag>
                                </Space>
                              }
                              description={
                                <Space direction="vertical" size="small">
                                  <Text>{alert.description}</Text>
                                  {alert.suggestions.length > 0 && (
                                    <Text type="secondary">建议: {alert.suggestions.join('；')}</Text>
                                  )}
                                </Space>
                              }
                              type={alert.severity === 'critical' || alert.severity === 'high' ? 'error' : alert.severity === 'medium' ? 'warning' : 'info'}
                              showIcon
                              style={{ width: '100%' }}
                            />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Spin>
                ),
              },
              {
                key: 'report',
                label: (
                  <span>
                    <LineChartOutlined /> 进度报告
                  </span>
                ),
                children: report ? (
                  <Spin spinning={reportLoading}>
                    <Card title="进度报告">
                      <Row gutter={[16, 16]}>
                        <Col span={24}>
                          <Alert
                            message={report.stats.on_track ? '进度正常' : '需要关注'}
                            description={report.stats.on_track ? '您的论文进度正常，请继续保持！' : '您的论文进度存在风险，建议调整计划。'}
                            type={report.stats.on_track ? 'success' : 'warning'}
                            showIcon
                          />
                        </Col>
                      </Row>

                      <Divider />

                      <Title level={5}>建议</Title>
                      <List
                        dataSource={report.recommendations}
                        renderItem={(item) => (
                          <List.Item>
                            <Text>• {item}</Text>
                          </List.Item>
                        )}
                      />

                      <Divider />

                      <Title level={5}>下一步行动</Title>
                      <List
                        dataSource={report.next_actions}
                        renderItem={(item) => (
                          <List.Item>
                            <Text>• {item}</Text>
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Spin>
                ) : (
                  <Empty description="暂无报告数据" />
                ),
              },
            ]}
          />
        </>
      )}

      {/* 新建里程碑弹窗 */}
      <Modal
        title="新建里程碑"
        open={isMilestoneModalOpen}
        onCancel={() => setIsMilestoneModalOpen(false)}
        footer={null}
      >
        <Form form={milestoneForm} layout="vertical" onFinish={handleCreateMilestone}>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input placeholder="例如：完成文献综述" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="planned_date" label="计划日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={createMilestoneMutation.isPending}>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* 新建任务弹窗 */}
      <Modal
        title="新建任务"
        open={isTaskModalOpen}
        onCancel={() => setIsTaskModalOpen(false)}
        footer={null}
      >
        <Form form={taskForm} layout="vertical" onFinish={handleCreateTask}>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input placeholder="例如：检索相关文献" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="milestone_id" label="关联里程碑">
            <Select placeholder="选择里程碑" allowClear>
              {milestones.map((m: Milestone) => (
                <Option key={m.id} value={m.id}>{m.title}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="medium">
            <Select>
              <Option value="urgent">紧急</Option>
              <Option value="high">高</Option>
              <Option value="medium">中</Option>
              <Option value="low">低</Option>
            </Select>
          </Form.Item>
          <Form.Item name="date_range" label="计划时间">
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={createTaskMutation.isPending}>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ProgressManager
