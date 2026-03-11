/**
 * 学术影响力仪表盘
 * 可视化展示学术影响力指标
 */

import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Timeline,
  Tag,
  Space,
  Typography,
  Tabs,
  List,
  Avatar,
} from 'antd'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'
import {
  RiseOutlined,
  TeamOutlined,
  FileTextOutlined,
  GlobalOutlined,
  StarOutlined,
  BookOutlined,
  TrophyOutlined,
  LinkOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography
const { TabPane } = Tabs

// 模拟数据
const mockCitationData = [
  { year: 2019, citations: 45, publications: 3 },
  { year: 2020, citations: 89, publications: 5 },
  { year: 2021, citations: 156, publications: 4 },
  { year: 2022, citations: 234, publications: 6 },
  { year: 2023, citations: 312, publications: 5 },
  { year: 2024, citations: 178, publications: 3 },
]

const mockFieldDistribution = [
  { name: '人工智能', value: 35, color: '#0088FE' },
  { name: '机器学习', value: 28, color: '#00C49F' },
  { name: '数据挖掘', value: 20, color: '#FFBB28' },
  { name: '自然语言处理', value: 17, color: '#FF8042' },
]

const mockCollaborators = [
  { name: '张三', count: 12, avatar: 'Z' },
  { name: '李四', count: 8, avatar: 'L' },
  { name: '王五', count: 6, avatar: 'W' },
  { name: '赵六', count: 5, avatar: 'Z' },
]

const mockRadarData = [
  { subject: '引用影响力', A: 120, fullMark: 150 },
  { subject: '发表活跃度', A: 98, fullMark: 150 },
  { subject: '合作网络', A: 86, fullMark: 150 },
  { subject: 'H-index', A: 99, fullMark: 150 },
  { subject: '领域影响力', A: 85, fullMark: 150 },
  { subject: '创新性', A: 65, fullMark: 150 },
]

interface ImpactDashboardProps {
  authorId?: string
}

export const ImpactDashboard: React.FC<ImpactDashboardProps> = ({ authorId }) => {
  const [activeTab, setActiveTab] = useState('overview')

  const renderOverview = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="总引用次数"
            value={1014}
            prefix={<RiseOutlined />}
            valueStyle={{ color: '#3f8600' }}
          />
          <Progress percent={75} size="small" showInfo={false} />
          <Text type="secondary" style={{ fontSize: 12 }}>超过同领域75%的研究者</Text>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="H-index"
            value={18}
            prefix={<TrophyOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
          <Progress percent={60} size="small" showInfo={false} />
          <Text type="secondary" style={{ fontSize: 12 }}>超过同领域60%的研究者</Text>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="发表论文"
            value={26}
            prefix={<FileTextOutlined />}
            valueStyle={{ color: '#722ed1' }}
          />
          <Progress percent={80} size="small" showInfo={false} />
          <Text type="secondary" style={{ fontSize: 12 }}>第一作者15篇</Text>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="合作学者"
            value={42}
            prefix={<TeamOutlined />}
            valueStyle={{ color: '#fa8c16' }}
          />
          <Progress percent={70} size="small" showInfo={false} />
          <Text type="secondary" style={{ fontSize: 12 }}>覆盖12个国家/地区</Text>
        </Card>
      </Col>

      <Col xs={24} lg={16}>
        <Card title="引用趋势" extra={<Tag color="blue">年均169次</Tag>}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={mockCitationData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="citations"
                stroke="#1890ff"
                strokeWidth={2}
                name="引用次数"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="publications"
                stroke="#52c41a"
                strokeWidth={2}
                name="发表论文"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={8}>
        <Card title="研究领域分布">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={mockFieldDistribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {mockFieldDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
            {mockFieldDistribution.map((item) => (
              <Tag key={item.name} color={item.color}>
                {item.name} {item.value}%
              </Tag>
            ))}
          </div>
        </Card>
      </Col>
    </Row>
  )

  const renderCollaboration = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}>
        <Card title="主要合作者">
          <List
            dataSource={mockCollaborators}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  avatar={<Avatar>{item.avatar}</Avatar>}
                  title={item.name}
                  description={`合作 ${item.count} 篇论文`}
                />
                <Tag color="blue">{item.count} 篇</Tag>
              </List.Item>
            )}
          />
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="综合能力雷达图">
          <ResponsiveContainer width="100%" height={350}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={mockRadarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis angle={30} domain={[0, 150]} />
              <Radar
                name="学术能力"
                dataKey="A"
                stroke="#1890ff"
                fill="#1890ff"
                fillOpacity={0.6}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </Card>
      </Col>
    </Row>
  )

  const renderPublications = () => (
    <Card title="发表论文统计">
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={mockCitationData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="publications" fill="#1890ff" name="发表论文数" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )

  return (
    <div>
      <Title level={2}>
        <TrophyOutlined /> 学术影响力分析
      </Title>

      <Card>
        <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 16 }}>
          <Avatar size={64} icon={<TeamOutlined />} />
          <div>
            <Title level={4} style={{ margin: 0 }}>研究者姓名</Title>
            <Text type="secondary">某某大学 · 计算机学院 · 教授</Text>
          </div>
          <div style={{ marginLeft: 'auto' }}>
            <Tag color="gold" icon={<StarOutlined />}>全球前10%</Tag>
          </div>
        </div>

        <Tabs activeKey={activeTab} onChange={setActiveTab} type="card">
          <TabPane tab={<span><RiseOutlined /> 概览</span>} key="overview">
            {renderOverview()}
          </TabPane>
          <TabPane tab={<span><TeamOutlined /> 合作网络</span>} key="collaboration">
            {renderCollaboration()}
          </TabPane>
          <TabPane tab={<span><FileTextOutlined /> 发表论文</span>} key="publications">
            {renderPublications()}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default ImpactDashboard
