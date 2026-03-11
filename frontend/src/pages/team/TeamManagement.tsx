/**
 * 团队管理页面
 * 研究团队创建、成员管理、项目协作
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Table,
  Tag,
  Avatar,
  Modal,
  Form,
  Input,
  Select,
  Tabs,
  List,
  Progress,
  Statistic,
  Row,
  Col,
  Typography,
  Space,
  Dropdown,
  Menu,
  Badge,
  Empty,
  Timeline,
  Tooltip,
  message,
} from 'antd'
import {
  TeamOutlined,
  UserAddOutlined,
  SettingOutlined,
  ProjectOutlined,
  FileTextOutlined,
  MoreOutlined,
  CrownOutlined,
  UserOutlined,
  DeleteOutlined,
  EditOutlined,
  MailOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  PlusOutlined,
  RiseOutlined,
  BookOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import styles from './TeamManagement.module.css'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs
const { Option } = Select
const { TextArea } = Input

interface TeamMember {
  user_id: string
  username: string
  email: string
  avatar_url?: string
  role: 'owner' | 'admin' | 'member' | 'guest'
  join_date: string
  contributions: number
  last_active?: string
  research_interests: string[]
}

interface ResearchProject {
  id: string
  name: string
  description?: string
  status: 'active' | 'completed' | 'paused'
  start_date: string
  end_date?: string
  leader_id: string
  members: string[]
  progress: number
}

interface Team {
  id: string
  name: string
  description?: string
  institution?: string
  research_fields: string[]
  avatar_url?: string
  created_at: string
  members: TeamMember[]
  projects: ResearchProject[]
  is_public: boolean
  stats: {
    total_publications: number
    active_projects: number
    completed_projects: number
    total_contributions: number
  }
}

interface TeamActivity {
  id: string
  user_id: string
  username: string
  action: string
  target_name?: string
  created_at: string
}

const TeamManagement: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([])
  const [currentTeam, setCurrentTeam] = useState<Team | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [isCreateModalVisible, setIsCreateModalVisible] = useState(false)
  const [isInviteModalVisible, setIsInviteModalVisible] = useState(false)
  const [isProjectModalVisible, setIsProjectModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [inviteForm] = Form.useForm()
  const [projectForm] = Form.useForm()

  const roleColors = {
    owner: 'gold',
    admin: 'blue',
    member: 'green',
    guest: 'default',
  }

  const roleLabels = {
    owner: '所有者',
    admin: '管理员',
    member: '成员',
    guest: '访客',
  }

  const statusColors = {
    active: 'green',
    completed: 'blue',
    paused: 'orange',
  }

  const statusLabels = {
    active: '进行中',
    completed: '已完成',
    paused: '已暂停',
  }

  useEffect(() => {
    loadTeams()
  }, [])

  const loadTeams = async () => {
    setLoading(true)
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockTeam: Team = {
        id: 'team_001',
        name: '机器学习研究组',
        description: '专注于深度学习和自然语言处理的研究团队',
        institution: '某某大学计算机学院',
        research_fields: ['机器学习', '自然语言处理', '计算机视觉'],
        created_at: '2024-01-15',
        is_public: true,
        members: [
          {
            user_id: 'user_001',
            username: '张教授',
            email: 'zhang@example.edu',
            role: 'owner',
            join_date: '2024-01-15',
            contributions: 45,
            last_active: '2024-03-05',
            research_interests: ['深度学习', 'NLP'],
          },
          {
            user_id: 'user_002',
            username: '李博士',
            email: 'li@example.edu',
            role: 'admin',
            join_date: '2024-01-20',
            contributions: 28,
            last_active: '2024-03-04',
            research_interests: ['计算机视觉', '强化学习'],
          },
          {
            user_id: 'user_003',
            username: '王同学',
            email: 'wang@example.edu',
            role: 'member',
            join_date: '2024-02-01',
            contributions: 12,
            last_active: '2024-03-03',
            research_interests: ['机器学习', '数据挖掘'],
          },
        ],
        projects: [
          {
            id: 'proj_001',
            name: '大语言模型微调研究',
            description: '研究LLM在特定领域的微调方法',
            status: 'active',
            start_date: '2024-01-01',
            leader_id: 'user_001',
            members: ['user_001', 'user_002', 'user_003'],
            progress: 65,
          },
          {
            id: 'proj_002',
            name: '多模态学习框架',
            description: '构建统一的多模态学习架构',
            status: 'active',
            start_date: '2024-02-01',
            leader_id: 'user_002',
            members: ['user_002', 'user_003'],
            progress: 40,
          },
        ],
        stats: {
          total_publications: 12,
          active_projects: 2,
          completed_projects: 5,
          total_contributions: 156,
        },
      }

      setTeams([mockTeam])
      setCurrentTeam(mockTeam)
    } catch (error) {
      message.error('加载团队失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateTeam = async (values: any) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))
      message.success('团队创建成功')
      setIsCreateModalVisible(false)
      form.resetFields()
      loadTeams()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleInviteMember = async (values: any) => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      message.success('邀请已发送')
      setIsInviteModalVisible(false)
      inviteForm.resetFields()
    } catch (error) {
      message.error('邀请失败')
    }
  }

  const handleCreateProject = async (values: any) => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      message.success('项目创建成功')
      setIsProjectModalVisible(false)
      projectForm.resetFields()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleRemoveMember = (memberId: string) => {
    Modal.confirm({
      title: '移除成员',
      content: '确定要将该成员移出团队吗？',
      okText: '移除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => {
        message.success('成员已移除')
      },
    })
  }

  const handleUpdateRole = (memberId: string, newRole: string) => {
    message.success(`角色已更新为 ${roleLabels[newRole as keyof typeof roleLabels]}`)
  }

  const memberColumns = [
    {
      title: '成员',
      key: 'member',
      render: (record: TeamMember) => (
        <Space>
          <Avatar src={record.avatar_url} icon={<UserOutlined />} />
          <div>
            <div className={styles.memberName}>{record.username}</div>
            <div className={styles.memberEmail}>{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={roleColors[role as keyof typeof roleColors]}>
          {roleLabels[role as keyof typeof roleLabels]}
        </Tag>
      ),
    },
    {
      title: '研究兴趣',
      key: 'interests',
      render: (record: TeamMember) => (
        <Space wrap>
          {record.research_interests.map(interest => (
            <Tag key={interest} size="small">{interest}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '贡献',
      dataIndex: 'contributions',
      key: 'contributions',
      sorter: (a: TeamMember, b: TeamMember) => a.contributions - b.contributions,
    },
    {
      title: '加入时间',
      dataIndex: 'join_date',
      key: 'join_date',
    },
    {
      title: '操作',
      key: 'action',
      render: (record: TeamMember) => (
        <Dropdown
          overlay={
            <Menu>
              <Menu.Item key="role" icon={<EditOutlined />}>
                更改角色
              </Menu.Item>
              <Menu.Divider />
              <Menu.Item key="remove" icon={<DeleteOutlined />} danger>
                移除成员
              </Menu.Item>
            </Menu>
          }
          trigger={['click']}
        >
          <Button type="text" icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ]

  const renderOverview = () => (
    <div className={styles.overview}>
      <Row gutter={[24, 24]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="团队成员"
              value={currentTeam?.members.length || 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="发表论文"
              value={currentTeam?.stats.total_publications || 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="进行中的项目"
              value={currentTeam?.stats.active_projects || 0}
              prefix={<ProjectOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总贡献数"
              value={currentTeam?.stats.total_contributions || 0}
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]} className={styles.sectionRow}>
        <Col span={16}>
          <Card
            title="进行中的项目"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                size="small"
                onClick={() => setIsProjectModalVisible(true)}
              >
                新建项目
              </Button>
            }
          >
            <List
              dataSource={currentTeam?.projects.filter(p => p.status === 'active') || []}
              renderItem={project => (
                <List.Item
                  actions={[
                    <Tag color={statusColors[project.status]}>
                      {statusLabels[project.status]}
                    </Tag>,
                  ]}
                >
                  <List.Item.Meta
                    title={project.name}
                    description={
                      <div>
                        <div>{project.description}</div>
                        <Progress percent={project.progress} size="small" />
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="最近动态">
            <Timeline mode="left">
              <Timeline.Item>
                <Text strong>张教授</Text> 发布了新论文
                <div className={styles.timelineTime}>2小时前</div>
              </Timeline.Item>
              <Timeline.Item>
                <Text strong>李博士</Text> 完成了项目里程碑
                <div className={styles.timelineTime}>5小时前</div>
              </Timeline.Item>
              <Timeline.Item>
                <Text strong>王同学</Text> 加入了团队
                <div className={styles.timelineTime}>1天前</div>
              </Timeline.Item>
            </Timeline>
          </Card>
        </Col>
      </Row>
    </div>
  )

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.teamInfo}>
          <Avatar
            size={64}
            src={currentTeam?.avatar_url}
            icon={<TeamOutlined />}
            className={styles.teamAvatar}
          />
          <div className={styles.teamDetails}>
            <Title level={3} className={styles.teamName}>
              {currentTeam?.name}
              {currentTeam?.is_public && (
                <Tag color="green" style={{ marginLeft: 12 }}>公开</Tag>
              )}
            </Title>
            <Paragraph type="secondary" className={styles.teamDesc}>
              {currentTeam?.description}
            </Paragraph>
            <Space>
              <Tag icon={<BookOutlined />}>{currentTeam?.institution}</Tag>
              {currentTeam?.research_fields.map(field => (
                <Tag key={field} color="blue">{field}</Tag>
              ))}
            </Space>
          </div>
        </div>
        <Space>
          <Button icon={<MailOutlined />}>
            邀请成员
          </Button>
          <Button type="primary" icon={<SettingOutlined />}>
            团队设置
          </Button>
        </Space>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab} className={styles.tabs}>
        <TabPane tab="概览" key="overview">
          {renderOverview()}
        </TabPane>
        <TabPane tab="成员" key="members">
          <Card
            title="团队成员"
            extra={
              <Button
                type="primary"
                icon={<UserAddOutlined />}
                onClick={() => setIsInviteModalVisible(true)}
              >
                邀请成员
              </Button>
            }
          >
            <Table
              dataSource={currentTeam?.members}
              columns={memberColumns}
              rowKey="user_id"
              loading={loading}
            />
          </Card>
        </TabPane>
        <TabPane tab="项目" key="projects">
          <Card
            title="研究项目"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setIsProjectModalVisible(true)}
              >
                新建项目
              </Button>
            }
          >
            <Row gutter={[24, 24]}>
              {currentTeam?.projects.map(project => (
                <Col span={12} key={project.id}>
                  <Card
                    hoverable
                    className={styles.projectCard}
                    actions={[
                      <SettingOutlined key="setting" />,
                      <EditOutlined key="edit" />,
                      <BarChartOutlined key="stats" />,
                    ]}
                  >
                    <div className={styles.projectHeader}>
                      <Title level={5}>{project.name}</Title>
                      <Tag color={statusColors[project.status]}>
                        {statusLabels[project.status]}
                      </Tag>
                    </div>
                    <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
                      {project.description}
                    </Paragraph>
                    <div className={styles.projectMeta}>
                      <div className={styles.projectProgress}>
                        <Text type="secondary">进度</Text>
                        <Progress percent={project.progress} size="small" />
                      </div>
                      <div className={styles.projectMembers}>
                        <Avatar.Group maxCount={3}>
                          {project.members.map(memberId => {
                            const member = currentTeam.members.find(m => m.user_id === memberId)
                            return (
                              <Tooltip title={member?.username} key={memberId}>
                                <Avatar icon={<UserOutlined />} />
                              </Tooltip>
                            )
                          })}
                        </Avatar.Group>
                      </div>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </TabPane>
        <TabPane tab="统计" key="stats">
          <Card title="团队统计">
            <Empty description="统计功能开发中..." />
          </Card>
        </TabPane>
      </Tabs>

      {/* 创建团队弹窗 */}
      <Modal
        title="创建研究团队"
        open={isCreateModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setIsCreateModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateTeam}>
          <Form.Item
            name="name"
            label="团队名称"
            rules={[{ required: true, message: '请输入团队名称' }]}
          >
            <Input placeholder="输入团队名称" />
          </Form.Item>
          <Form.Item name="description" label="团队简介">
            <TextArea rows={3} placeholder="描述团队的研究方向和目标" />
          </Form.Item>
          <Form.Item name="institution" label="所属机构">
            <Input placeholder="如：某某大学计算机学院" />
          </Form.Item>
          <Form.Item name="research_fields" label="研究领域">
            <Select mode="tags" placeholder="输入研究领域">
              <Option value="机器学习">机器学习</Option>
              <Option value="自然语言处理">自然语言处理</Option>
              <Option value="计算机视觉">计算机视觉</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 邀请成员弹窗 */}
      <Modal
        title="邀请成员"
        open={isInviteModalVisible}
        onOk={() => inviteForm.submit()}
        onCancel={() => setIsInviteModalVisible(false)}
      >
        <Form form={inviteForm} layout="vertical" onFinish={handleInviteMember}>
          <Form.Item
            name="email"
            label="邮箱地址"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input placeholder="colleague@example.edu" />
          </Form.Item>
          <Form.Item name="role" label="角色" initialValue="member">
            <Select>
              <Option value="admin">管理员</Option>
              <Option value="member">成员</Option>
              <Option value="guest">访客</Option>
            </Select>
          </Form.Item>
          <Form.Item name="message" label="邀请消息">
            <TextArea rows={3} placeholder="可选：添加一条个人消息" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建项目弹窗 */}
      <Modal
        title="新建项目"
        open={isProjectModalVisible}
        onOk={() => projectForm.submit()}
        onCancel={() => setIsProjectModalVisible(false)}
      >
        <Form form={projectForm} layout="vertical" onFinish={handleCreateProject}>
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="输入项目名称" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <TextArea rows={3} placeholder="描述项目的目标和范围" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TeamManagement
