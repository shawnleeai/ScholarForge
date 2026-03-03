/**
 * 进度管理页面
 */

import React, { useState, useEffect } from 'react'
import {
  Card, Row, Col, Button, Timeline, Progress, Tag, Table, Modal, Form,
  Input, DatePicker, Select, Badge, message, Empty, Tabs, Statistic, Alert, Space
} from 'antd'
import {
  CalendarOutlined, PlusOutlined, CheckCircleOutlined, WarningOutlined,
  ClockCircleOutlined, FlagOutlined, BarChartOutlined, BellOutlined
} from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import { progressService, type Milestone, type Task, type Alert as AlertType } from '@/services/progressService'
import styles from './ProgressManagement.module.css'

const { Option } = Select
const { TabPane } = Tabs
const { TextArea } = Input
const { RangePicker } = DatePicker

const ProgressManagement: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>()
  const [milestones, setMilestones] = useState<Milestone[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [alerts, setAlerts] = useState<AlertType[]>([])
  const [loading, setLoading] = useState(false)
  const [milestoneModalVisible, setMilestoneModalVisible] = useState(false)
  const [taskModalVisible, setTaskModalVisible] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [report, setReport] = useState<any>(null)

  const [milestoneForm] = Form.useForm()
  const [taskForm] = Form.useForm()

  // 获取数据
  const fetchData = async () => {
    if (!paperId) return
    setLoading(true)
    try {
      const [milestonesRes, tasksRes, alertsRes, reportRes] = await Promise.all([
        progressService.getMilestones(paperId),
        progressService.getTasks(paperId),
        progressService.getAlerts(paperId),
        progressService.getProgressReport(paperId),
      ])
      setMilestones(milestonesRes.data?.data || [])
      setTasks(tasksRes.data?.data || [])
      setAlerts(alertsRes.data?.data || [])
      setReport(reportRes.data?.data)
    } catch (error) {
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  // 创建里程碑
  const handleCreateMilestone = async (values: any) => {
    if (!paperId) return
    try {
      await progressService.createMilestone(paperId, {
        title: values.title,
        description: values.description,
        planned_date: values.planned_date.format('YYYY-MM-DD'),
      })
      message.success('里程碑创建成功')
      setMilestoneModalVisible(false)
      milestoneForm.resetFields()
      fetchData()
    } catch (error) {
      message.error('创建失败')
    }
  }

  // 创建任务
  const handleCreateTask = async (values: any) => {
    if (!paperId) return
    try {
      await progressService.createTask(paperId, {
        title: values.title,
        description: values.description,
        milestone_id: values.milestone_id,
        priority: values.priority,
        planned_start: values.planned_dates[0].format('YYYY-MM-DD'),
        planned_end: values.planned_dates[1].format('YYYY-MM-DD'),
      })
      message.success('任务创建成功')
      setTaskModalVisible(false)
      taskForm.resetFields()
      fetchData()
    } catch (error) {
      message.error('创建失败')
    }
  }

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'in_progress': return 'processing'
      case 'delayed': return 'error'
      case 'at_risk': return 'warning'
      default: return 'default'
    }
  }

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '待开始'
      case 'in_progress': return '进行中'
      case 'completed': return '已完成'
      case 'delayed': return '已延期'
      case 'at_risk': return '有风险'
      default: return status
    }
  }

  useEffect(() => {
    fetchData()
  }, [paperId])

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (status: string) => <Badge status={getStatusColor(status)} text={getStatusText(status)} />
    },
    { title: '进度', dataIndex: 'completion_percentage', key: 'progress',
      render: (pct: number) => <Progress percent={pct} size="small" />
    },
    { title: '计划日期', dataIndex: 'planned_date', key: 'planned_date' },
  ]

  return (
    <div className={styles.container}>
      <h2><CalendarOutlined /> 进度管理</h2>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab={<span><BarChartOutlined /> 概览</span>} key="overview">
          {report && (
            <Row gutter={16} className={styles.stats}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="总体进度"
                    value={report.stats.overall_progress}
                    suffix="%"
                    valueStyle={{ color: report.stats.on_track ? '#3f8600' : '#cf1322' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic title="里程碑" value={report.stats.completed_milestones}
                    suffix={`/${report.stats.total_milestones}`} />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic title="任务" value={report.stats.completed_tasks}
                    suffix={`/${report.stats.total_tasks}`} />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic title="剩余天数" value={report.stats.days_remaining} />
                </Card>
              </Col>
            </Row>
          )}

          {alerts.length > 0 && (
            <Alert
              message="预警提醒"
              description={alerts.map(a => a.title).join('、')}
              type="warning"
              showIcon
              icon={<BellOutlined />}
              className={styles.alert}
            />
          )}
        </TabPane>

        <TabPane tab={<span><FlagOutlined /> 里程碑</span>} key="milestones">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setMilestoneModalVisible(true)}
            className={styles.addButton}
          >
            添加里程碑
          </Button>
          <Table dataSource={milestones} columns={columns} rowKey="id" loading={loading} />
        </TabPane>

        <TabPane tab={<span><CheckCircleOutlined /> 任务</span>} key="tasks">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setTaskModalVisible(true)}
            className={styles.addButton}
          >
            添加任务
          </Button>
          <Table
            dataSource={tasks}
            columns={[
              ...columns,
              { title: '优先级', dataIndex: 'priority', key: 'priority',
                render: (p: string) => <Tag color={p === 'high' ? 'red' : p === 'medium' ? 'orange' : 'green'}>{p}</Tag>
              },
            ]}
            rowKey="id"
            loading={loading}
          />
        </TabPane>
      </Tabs>

      {/* 里程碑弹窗 */}
      <Modal
        title="添加里程碑"
        visible={milestoneModalVisible}
        onCancel={() => setMilestoneModalVisible(false)}
        onOk={() => milestoneForm.submit()}
      >
        <Form form={milestoneForm} onFinish={handleCreateMilestone} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="planned_date" label="计划日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 任务弹窗 */}
      <Modal
        title="添加任务"
        visible={taskModalVisible}
        onCancel={() => setTaskModalVisible(false)}
        onOk={() => taskForm.submit()}
      >
        <Form form={taskForm} onFinish={handleCreateTask} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item name="milestone_id" label="关联里程碑">
            <Select allowClear>
              {milestones.map(m => <Option key={m.id} value={m.id}>{m.title}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="medium">
            <Select>
              <Option value="high">高</Option>
              <Option value="medium">中</Option>
              <Option value="low">低</Option>
            </Select>
          </Form.Item>
          <Form.Item name="planned_dates" label="计划时间" rules={[{ required: true }]}>
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ProgressManagement
