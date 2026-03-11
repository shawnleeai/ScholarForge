/**
 * 引用统计图表组件
 * 可视化展示引用分布、趋势和统计信息
 */

import React, { useMemo } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Space,
  Tag,
  Empty,
  Tabs,
  List,
  Tooltip,
} from 'antd'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts'
import {
  BookOutlined,
  CalendarOutlined,
  TeamOutlined,
  FileTextOutlined,
  LinkOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  RadarChartOutlined,
} from '@ant-design/icons'
import styles from './CitationStats.module.css'

const { TabPane } = Tabs

interface CitationData {
  id: string
  title: string
  authors: string[]
  year: number
  journal?: string
  field?: string
  cited_count: number
  type: 'journal' | 'conference' | 'book' | 'thesis' | 'other'
}

interface CitationStatsProps {
  citations: CitationData[]
}

const COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272']

const CitationStats: React.FC<CitationStatsProps> = ({ citations }) => {
  // 按年份统计
  const yearStats = useMemo(() => {
    const stats: Record<number, number> = {}
    citations.forEach(c => {
      stats[c.year] = (stats[c.year] || 0) + 1
    })
    return Object.entries(stats)
      .map(([year, count]) => ({ year: parseInt(year), count }))
      .sort((a, b) => a.year - b.year)
  }, [citations])

  // 按类型统计
  const typeStats = useMemo(() => {
    const stats: Record<string, number> = {}
    citations.forEach(c => {
      stats[c.type] = (stats[c.type] || 0) + 1
    })
    return Object.entries(stats).map(([type, count]) => ({
      type: getTypeLabel(type),
      count,
      value: count,
      name: getTypeLabel(type),
    }))
  }, [citations])

  // 按领域统计
  const fieldStats = useMemo(() => {
    const stats: Record<string, number> = {}
    citations.forEach(c => {
      if (c.field) {
        stats[c.field] = (stats[c.field] || 0) + 1
      }
    })
    return Object.entries(stats)
      .map(([field, count]) => ({ field, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
  }, [citations])

  // 被引次数统计
  const citationImpactStats = useMemo(() => {
    const ranges = [
      { label: '高被引 (>100)', min: 100, count: 0 },
      { label: '较高被引 (50-100)', min: 50, max: 100, count: 0 },
      { label: '一般被引 (10-50)', min: 10, max: 50, count: 0 },
      { label: '低被引 (<10)', max: 10, count: 0 },
    ]

    citations.forEach(c => {
      const range = ranges.find(
        r =>
          (r.min === undefined || c.cited_count >= r.min) &&
          (r.max === undefined || c.cited_count < r.max)
      )
      if (range) range.count++
    })

    return ranges
  }, [citations])

  // 作者统计
  const authorStats = useMemo(() => {
    const stats: Record<string, number> = {}
    citations.forEach(c => {
      c.authors.forEach(author => {
        stats[author] = (stats[author] || 0) + 1
      })
    })
    return Object.entries(stats)
      .map(([author, count]) => ({ author, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
  }, [citations])

  // 雷达图数据
  const radarData = useMemo(() => {
    const currentYear = new Date().getFullYear()
    const avgYear =
      citations.reduce((sum, c) => sum + c.year, 0) / citations.length || currentYear

    return [
      { subject: '时效性', A: Math.max(0, 100 - (currentYear - avgYear) * 5), fullMark: 100 },
      { subject: '多样性', A: Math.min(100, typeStats.length * 20), fullMark: 100 },
      { subject: '影响力', A: Math.min(100, citations.filter(c => c.cited_count > 50).length * 10), fullMark: 100 },
      { subject: '覆盖度', A: Math.min(100, fieldStats.length * 15), fullMark: 100 },
      { subject: '权威性', A: Math.min(100, citations.filter(c => c.journal).length * 2), fullMark: 100 },
    ]
  }, [citations, typeStats.length, fieldStats.length])

  function getTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      journal: '期刊论文',
      conference: '会议论文',
      book: '书籍',
      thesis: '学位论文',
      other: '其他',
    }
    return labels[type] || type
  }

  if (citations.length === 0) {
    return (
      <Card title="引用统计" className={styles.statsPanel}>
        <Empty description="暂无引用数据" />
      </Card>
    )
  }

  return (
    <Card title="引用统计" className={styles.statsPanel}>
      {/* 概览统计 */}
      <Row gutter={[16, 16]} className={styles.overviewStats}>
        <Col span={6}>
          <Card>
            <Statistic
              title="引用总数"
              value={citations.length}
              prefix={<BookOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="时间跨度"
              value={`${Math.min(...citations.map(c => c.year))}-${Math.max(...citations.map(c => c.year))}`}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="涉及作者"
              value={new Set(citations.flatMap(c => c.authors)).size}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均被引"
              value={Math.round(citations.reduce((sum, c) => sum + c.cited_count, 0) / citations.length)}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="year">
        <TabPane
          tab={
            <span>
              <LineChartOutlined />
              时间分布
            </span>
          }
          key="year"
        >
          <div className={styles.chartContainer}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={yearStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="count"
                  name="引用数量"
                  stroke="#5470c6"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </TabPane>

        <TabPane
          tab={
            <span>
              <PieChartOutlined />
              类型分布
            </span>
          }
          key="type"
        >
          <Row gutter={24}>
            <Col span={12}>
              <div className={styles.chartContainer}>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={typeStats}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      fill="#8884d8"
                      paddingAngle={5}
                      dataKey="value"
                      label
                    >
                      {typeStats.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </Col>
            <Col span={12}>
              <List
                dataSource={typeStats}
                renderItem={item => (
                  <List.Item>
                    <Space>
                      <Tag color={COLORS[typeStats.indexOf(item) % COLORS.length]}>
                        {item.type}
                      </Tag>
                      <span>{item.count} 篇</span>
                      <span>({((item.count / citations.length) * 100).toFixed(1)}%)</span>
                    </Space>
                  </List.Item>
                )}
              />
            </Col>
          </Row>
        </TabPane>

        <TabPane
          tab={
            <span>
              <BarChartOutlined />
              领域分布
            </span>
          }
          key="field"
        >
          <div className={styles.chartContainer}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={fieldStats} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="field" type="category" width={100} />
                <RechartsTooltip />
                <Bar dataKey="count" name="引用数量" fill="#5470c6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </TabPane>

        <TabPane
          tab={
            <span>
              <BarChartOutlined />
              影响力分析
            </span>
          }
          key="impact"
        >
          <Row gutter={24}>
            <Col span={12}>
              <div className={styles.chartContainer}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={citationImpactStats}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="label" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="count" name="文献数量" fill="#91cc75" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Col>
            <Col span={12}>
              <List
                header="高被引文献"
                dataSource={citations
                  .filter(c => c.cited_count > 50)
                  .sort((a, b) => b.cited_count - a.cited_count)
                  .slice(0, 5)}
                renderItem={item => (
                  <List.Item>
                    <List.Item.Meta
                      title={item.title}
                      description={
                        <Space>
                          <Tag color="gold">{item.cited_count} 被引</Tag>
                          <span>{item.year}</span>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Col>
          </Row>
        </TabPane>

        <TabPane
          tab={
            <span>
              <RadarChartOutlined />
              综合评估
            </span>
          }
          key="radar"
        >
          <Row gutter={24}>
            <Col span={12}>
              <div className={styles.chartContainer}>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} />
                    <Radar
                      name="引用质量"
                      dataKey="A"
                      stroke="#5470c6"
                      fill="#5470c6"
                      fillOpacity={0.6}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </Col>
            <Col span={12}>
              <List
                header="核心作者"
                dataSource={authorStats.slice(0, 5)}
                renderItem={item => (
                  <List.Item>
                    <List.Item.Meta
                      title={item.author}
                      description={`${item.count} 篇引用`}
                    />
                  </List.Item>
                )}
              />
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </Card>
  )
}

export default CitationStats
