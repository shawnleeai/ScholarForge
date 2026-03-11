/**
 * 写作码力值热力图组件
 * GitHub风格的贡献热力图
 */

import React, { useState, useEffect, useMemo } from 'react'
import {
  Card,
  Tooltip,
  Typography,
  Space,
  Select,
  Row,
  Col,
  Statistic,
  Badge,
  Divider,
  Progress
} from 'antd'
import {
  FireOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  TrophyOutlined,
  CalendarOutlined,
  RiseOutlined
} from '@ant-design/icons'
import { writingStatsService, type WritingStats } from '@/services/writingStatsService'
import styles from './WritingHeatmap.module.css'

const { Title, Text } = Typography
const { Option } = Select

// 颜色等级
const LEVEL_COLORS = {
  0: '#ebedf0', // 无数据
  1: '#9be9a8', // 少量
  2: '#40c463', // 中等
  3: '#30a14e', // 较多
  4: '#216e39'  // 大量
}

// 月份标签
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// 星期标签
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

interface WritingHeatmapProps {
  className?: string
}

const WritingHeatmap: React.FC<WritingHeatmapProps> = ({ className }) => {
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [stats, setStats] = useState<WritingStats | null>(null)
  const [heatmapData, setHeatmapData] = useState<Array<{ date: string; count: number; level: number }>>([])

  // 生成年份选项
  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear()
    return [currentYear, currentYear - 1, currentYear - 2]
  }, [])

  // 加载数据
  useEffect(() => {
    const loadData = () => {
      const currentStats = writingStatsService.getStats()
      const heatmap = writingStatsService.getHeatmapData(selectedYear)
      setStats(currentStats)
      setHeatmapData(heatmap)
    }

    loadData()
    // 每分钟刷新一次
    const interval = setInterval(loadData, 60000)
    return () => clearInterval(interval)
  }, [selectedYear])

  // 组织热力图数据
  const organizedData = useMemo(() => {
    const weeks: Array<Array<{ date: string; count: number; level: number } | null>> = []
    let currentWeek: Array<{ date: string; count: number; level: number } | null> = []

    // 填充年初空白
    const firstDay = new Date(selectedYear, 0, 1).getDay()
    for (let i = 0; i < firstDay; i++) {
      currentWeek.push(null)
    }

    heatmapData.forEach(day => {
      currentWeek.push(day)
      if (currentWeek.length === 7) {
        weeks.push(currentWeek)
        currentWeek = []
      }
    })

    // 填充年末空白
    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) {
        currentWeek.push(null)
      }
      weeks.push(currentWeek)
    }

    return weeks
  }, [heatmapData, selectedYear])

  // 获取月份标签位置
  const monthLabels = useMemo(() => {
    const labels: Array<{ month: string; weekIndex: number }> = []
    let currentMonth = -1

    organizedData.forEach((week, weekIndex) => {
      const firstDay = week.find(day => day !== null)
      if (firstDay) {
        const month = new Date(firstDay.date).getMonth()
        if (month !== currentMonth) {
          labels.push({ month: MONTHS[month], weekIndex })
          currentMonth = month
        }
      }
    })

    return labels
  }, [organizedData])

  // 格式化日期
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long'
    })
  }

  // 获取提示文本
  const getTooltipText = (day: { date: string; count: number; level: number }) => {
    if (day.count === 0) {
      return `${formatDate(day.date)}: 无写作记录`
    }
    return `${formatDate(day.date)}: ${day.count} 字`
  }

  if (!stats) {
    return <Card loading className={className} />
  }

  return (
    <Card
      title={
        <Space>
          <FireOutlined style={{ color: '#ff4d4f' }} />
          <span>论文写作码力值</span>
        </Space>
      }
      extra={
        <Select
          value={selectedYear}
          onChange={setSelectedYear}
          style={{ width: 100 }}
          size="small"
        >
          {yearOptions.map(year => (
            <Option key={year} value={year}>{year}年</Option>
          ))}
        </Select>
      }
      className={`${styles.heatmapCard} ${className || ''}`}
    >
      {/* 统计概览 */}
      <Row gutter={[16, 16]} className={styles.statsRow}>
        <Col xs={12} sm={6}>
          <Statistic
            title="总字数"
            value={stats.totalWordCount}
            suffix="字"
            prefix={<FileTextOutlined />}
          />
        </Col>
        <Col xs={12} sm={6}>
          <Statistic
            title="总时长"
            value={Math.floor(stats.totalWritingTime / 60)}
            suffix="小时"
            prefix={<ClockCircleOutlined />}
          />
        </Col>
        <Col xs={12} sm={6}>
          <Statistic
            title="连续写作"
            value={stats.currentStreak}
            suffix="天"
            prefix={<FireOutlined style={{ color: '#ff4d4f' }} />}
          />
        </Col>
        <Col xs={12} sm={6}>
          <Statistic
            title="活跃天数"
            value={stats.totalDays}
            suffix="天"
            prefix={<CalendarOutlined />}
          />
        </Col>
      </Row>

      <Divider />

      {/* 连续写作进度 */}
      <div className={styles.streakProgress}>
        <div className={styles.streakHeader}>
          <Text strong>连续写作挑战</Text>
          <Text type="secondary">
            最长连续 {stats.longestStreak} 天
          </Text>
        </div>
        <Progress
          percent={Math.min((stats.currentStreak / 30) * 100, 100)}
          format={() => `${stats.currentStreak}/30 天`}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068'
          }}
        />
      </div>

      <Divider />

      {/* 热力图 */}
      <div className={styles.heatmapContainer}>
        <div className={styles.monthLabels}>
          {monthLabels.map((label, index) => (
            <span
              key={index}
              className={styles.monthLabel}
              style={{ left: `${(label.weekIndex / organizedData.length) * 100}%` }}
            >
              {label.month}
            </span>
          ))}
        </div>

        <div className={styles.heatmapWrapper}>
          {/* 星期标签 */}
          <div className={styles.weekdayLabels}>
            {WEEKDAYS.filter((_, i) => i % 2 === 1).map((day, index) => (
              <span key={index} className={styles.weekdayLabel}>
                {day}
              </span>
            ))}
          </div>

          {/* 热力图格子 */}
          <div className={styles.heatmapGrid}>
            {organizedData.map((week, weekIndex) => (
              <div key={weekIndex} className={styles.weekColumn}>
                {week.map((day, dayIndex) => (
                  day ? (
                    <Tooltip
                      key={dayIndex}
                      title={getTooltipText(day)}
                      placement="top"
                    >
                      <div
                        className={styles.heatmapCell}
                        style={{
                          backgroundColor: LEVEL_COLORS[day.level as keyof typeof LEVEL_COLORS],
                          transform: day.level > 0 ? 'scale(1)' : 'scale(0.9)'
                        }}
                      />
                    </Tooltip>
                  ) : (
                    <div key={dayIndex} className={styles.heatmapCell} style={{ opacity: 0 }} />
                  )
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* 图例 */}
        <div className={styles.legend}>
          <Text type="secondary">少</Text>
          {[0, 1, 2, 3, 4].map(level => (
            <div
              key={level}
              className={styles.legendCell}
              style={{ backgroundColor: LEVEL_COLORS[level as keyof typeof LEVEL_COLORS] }}
            />
          ))}
          <Text type="secondary">多</Text>
        </div>
      </div>

      <Divider />

      {/* 生产力洞察 */}
      <div className={styles.insights}>
        <Title level={5}>
          <RiseOutlined /> 生产力洞察
        </Title>
        <Row gutter={[16, 8]}>
          <Col span={12}>
            <Text type="secondary">日均写作:</Text>
            <Text strong style={{ marginLeft: 8 }}>
              {stats.averageDailyWords} 字
            </Text>
          </Col>
          <Col span={12}>
            <Text type="secondary">日均时长:</Text>
            <Text strong style={{ marginLeft: 8 }}>
              {Math.round(stats.averageDailyTime)} 分钟
            </Text>
          </Col>
          <Col span={12}>
            <Text type="secondary">最高效时段:</Text>
            <Text strong style={{ marginLeft: 8 }}>
              {stats.mostProductiveHour}:00
            </Text>
          </Col>
          <Col span={12}>
            <Text type="secondary">最高产日期:</Text>
            <Text strong style={{ marginLeft: 8 }}>
              {stats.mostProductiveDay
                ? new Date(stats.mostProductiveDay.date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
                : '暂无'}
            </Text>
          </Col>
        </Row>
      </div>
    </Card>
  )
}

export default WritingHeatmap
