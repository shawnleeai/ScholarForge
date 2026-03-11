/**
 * 证据矩阵组件
 * 展示多文献对比矩阵，支持排序和筛选
 */

import React, { useState, useMemo } from 'react'
import {
  Table,
  Card,
  Typography,
  Tag,
  Space,
  Tooltip,
  Badge,
  Empty,
  Spin,
  Alert,
  Statistic,
  Row,
  Col,
  Button,
  Dropdown,
  Menu,
  Input,
} from 'antd'
import {
  BookOutlined,
  FilterOutlined,
  DownloadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
  QuestionCircleOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import styles from './EvidenceMatrix.module.css'

const { Title, Text, Paragraph } = Typography

interface MatrixCell {
  value: any
  display_value: string
  metadata?: {
    evidence_type?: string
  }
}

interface MatrixRow {
  article_id: string
  article_title: string
  authors: string[]
  year: number
  journal: string
  cells: Record<string, MatrixCell>
}

interface MatrixColumn {
  id: string
  name: string
  description: string
  type: string
  options?: string[]
}

interface EvidenceMatrixData {
  id: string
  title: string
  description?: string
  columns: MatrixColumn[]
  rows: MatrixRow[]
}

interface EvidenceMatrixProps {
  matrix?: EvidenceMatrixData
  summary?: {
    total_studies: number
    effect_directions: Record<string, number>
    study_designs: Record<string, number>
    evidence_qualities: Record<string, number>
    average_sample_size: number
    sample_size_range: { min: number; max: number }
  }
  loading?: boolean
  onExport?: () => void
}

const EvidenceMatrix: React.FC<EvidenceMatrixProps> = ({
  matrix,
  summary,
  loading = false,
  onExport,
}) => {
  const [searchText, setSearchText] = useState('')
  const [filteredInfo, setFilteredInfo] = useState<Record<string, any>>({})
  const [sortedInfo, setSortedInfo] = useState<any>({})

  // 渲染单元格
  const renderCell = (columnId: string, cell: MatrixCell) => {
    if (!cell) return '-'

    const value = cell.display_value || cell.value

    // 根据列类型渲染不同样式
    switch (columnId) {
      case 'evidence_quality':
        const qualityColors: Record<string, string> = {
          '高': 'green',
          '中': 'blue',
          '低': 'orange',
          '很低': 'red',
        }
        return (
          <Tag color={qualityColors[value] || 'default'}>
            {value}
          </Tag>
        )

      case 'effect_direction':
        const directionIcons: Record<string, React.ReactNode> = {
          '正面': <CheckCircleOutlined style={{ color: '#52c41a' }} />,
          '负面': <CloseCircleOutlined style={{ color: '#f5222d' }} />,
          '无效果': <MinusCircleOutlined style={{ color: '#8c8c8c' }} />,
          '混合': <QuestionCircleOutlined style={{ color: '#faad14' }} />,
        }
        return (
          <Space>
            {directionIcons[value]}
            <span>{value}</span>
          </Space>
        )

      case 'study_design':
        return <Tag color="blue">{value}</Tag>

      case 'sample_size':
        return value && value !== '-' ? (
          <Text strong>{Number(value).toLocaleString()}</Text>
        ) : (
          '-'
        )

      default:
        return (
          <Tooltip title={value}>
            <Text ellipsis style={{ maxWidth: 200 }}>
              {value}
            </Text>
          </Tooltip>
        )
    }
  }

  // 构建表格列
  const columns = useMemo(() => {
    if (!matrix?.columns) return []

    const baseColumns = [
      {
        title: '文献',
        key: 'article',
        fixed: 'left' as const,
        width: 250,
        render: (_: any, record: MatrixRow) => (
          <div className={styles.articleCell}>
            <Text strong className={styles.articleTitle}>
              {record.article_title}
            </Text>
            <div className={styles.articleMeta}>
              <Text type="secondary" className={styles.authors}>
                {record.authors?.join(', ') || 'Unknown'}
              </Text>
              <Space size="small">
                <Tag size="small">{record.year}</Tag>
                <Text type="secondary" className={styles.journal}>
                  {record.journal}
                </Text>
              </Space>
            </div>
          </div>
        ),
      },
    ]

    const dataColumns = matrix.columns.map((col) => ({
      title: (
        <Tooltip title={col.description}>
          <span>{col.name}</span>
        </Tooltip>
      ),
      dataIndex: ['cells', col.id],
      key: col.id,
      width: col.id === 'main_finding' ? 300 : 120,
      render: (cell: MatrixCell) => renderCell(col.id, cell),
      filters: col.options?.map((opt) => ({ text: opt, value: opt })),
      filteredValue: filteredInfo[col.id] || null,
      onFilter: (value: any, record: MatrixRow) => {
        const cell = record.cells[col.id]
        return cell?.value === value || cell?.display_value === value
      },
      sorter: (a: MatrixRow, b: MatrixRow) => {
        const aVal = a.cells[col.id]?.display_value || ''
        const bVal = b.cells[col.id]?.display_value || ''
        return String(aVal).localeCompare(String(bVal))
      },
      sortOrder: sortedInfo.columnKey === col.id ? sortedInfo.order : null,
    }))

    return [...baseColumns, ...dataColumns]
  }, [matrix?.columns, filteredInfo, sortedInfo])

  // 过滤数据
  const filteredRows = useMemo(() => {
    if (!matrix?.rows) return []
    if (!searchText) return matrix.rows

    return matrix.rows.filter(
      (row) =>
        row.article_title.toLowerCase().includes(searchText.toLowerCase()) ||
        row.authors?.some((a) =>
          a.toLowerCase().includes(searchText.toLowerCase())
        )
    )
  }, [matrix?.rows, searchText])

  // 处理表格变化
  const handleTableChange = (
    pagination: any,
    filters: any,
    sorter: any
  ) => {
    setFilteredInfo(filters)
    setSortedInfo(sorter)
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <Spin size="large" tip="正在生成证据矩阵..." />
      </div>
    )
  }

  if (!matrix) {
    return (
      <Empty description="暂无证据矩阵数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
    )
  }

  return (
    <div className={styles.evidenceMatrix}>
      {/* 标题区域 */}
      <div className={styles.header}>
        <div className={styles.titleSection}>
          <Title level={4} className={styles.title}>
            <BookOutlined /> {matrix.title}
          </Title>
          {matrix.description && (
            <Paragraph type="secondary" className={styles.description}>
              {matrix.description}
            </Paragraph>
          )}
        </div>
        <div className={styles.actions}>
          <Input.Search
            placeholder="搜索文献..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Button icon={<DownloadOutlined />} onClick={onExport}>
            导出
          </Button>
        </div>
      </div>

      {/* 统计摘要 */}
      {summary && (
        <Card className={styles.summaryCard} size="small">
          <Row gutter={16}>
            <Col span={4}>
              <Statistic
                title="研究数量"
                value={summary.total_studies}
                prefix={<FileTextOutlined />}
              />
            </Col>
            <Col span={5}>
              <div className={styles.statSection}>
                <Text type="secondary">效应方向</Text>
                <div className={styles.tagGroup}>
                  {Object.entries(summary.effect_directions).map(
                    ([direction, count]) =>
                      count > 0 && (
                        <Tag key={direction} color="blue">
                          {direction}: {count}
                        </Tag>
                      )
                  )}
                </div>
              </div>
            </Col>
            <Col span={5}>
              <div className={styles.statSection}>
                <Text type="secondary">证据质量</Text>
                <div className={styles.tagGroup}>
                  {Object.entries(summary.evidence_qualities).map(
                    ([quality, count]) =>
                      count > 0 && (
                        <Tag
                          key={quality}
                          color={
                            quality === '高'
                              ? 'green'
                              : quality === '中'
                              ? 'blue'
                              : quality === '低'
                              ? 'orange'
                              : 'red'
                          }
                        >
                          {quality}: {count}
                        </Tag>
                      )
                  )}
                </div>
              </div>
            </Col>
            <Col span={5}>
              <div className={styles.statSection}>
                <Text type="secondary">研究设计</Text>
                <div className={styles.tagGroup}>
                  {Object.entries(summary.study_designs)
                    .slice(0, 3)
                    .map(([design, count]) => (
                      <Tag key={design}>{design}</Tag>
                    ))}
                </div>
              </div>
            </Col>
            <Col span={5}>
              <Statistic
                title="平均样本量"
                value={summary.average_sample_size}
                suffix={`(${summary.sample_size_range.min}-${summary.sample_size_range.max})`}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 矩阵表格 */}
      <Card className={styles.matrixCard}>
        <Table
          dataSource={filteredRows}
          columns={columns}
          rowKey="article_id"
          scroll={{ x: 'max-content' }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 篇文献`,
          }}
          onChange={handleTableChange}
          bordered
          size="small"
        />
      </Card>

      {/* 使用说明 */}
      <Alert
        message="使用提示"
        description="点击表头可排序，点击筛选图标可按条件过滤，悬停在单元格上可查看完整内容。"
        type="info"
        showIcon
        className={styles.tips}
      />
    </div>
  )
}

export default EvidenceMatrix
