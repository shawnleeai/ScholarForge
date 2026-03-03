/**
 * 查重检测页面
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card, Row, Col, Button, Upload, Progress, Statistic, Table, Tag, Space,
  Modal, List, Typography, Alert, Empty, Timeline, Tooltip, Badge, message
} from 'antd'
import type { UploadProps } from 'antd'
import {
  SafetyOutlined, UploadOutlined, FileTextOutlined, HistoryOutlined,
  CheckCircleOutlined, WarningOutlined, CloseCircleOutlined, EyeOutlined,
  DownloadOutlined, DeleteOutlined, FileSearchOutlined, BarChartOutlined
} from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import {
  plagiarismService, type PlagiarismCheck, type CheckStatus, type SeverityLevel
} from '@/services/plagiarismService'
import styles from './PlagiarismCheck.module.css'

const { Title, Text, Paragraph } = Typography

const STATUS_CONFIG: Record<CheckStatus, { color: string; text: string; icon: React.ReactNode }> = {
  pending: { color: 'default', text: '等待中', icon: <ClockIcon /> },
  processing: { color: 'processing', text: '检测中', icon: <LoadingIcon /> },
  completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
  failed: { color: 'error', text: '失败', icon: <CloseCircleOutlined /> },
  cancelled: { color: 'default', text: '已取消', icon: <CloseCircleOutlined /> },
}

const SEVERITY_CONFIG: Record<SeverityLevel, { color: string; text: string }> = {
  low: { color: 'green', text: '低' },
  medium: { color: 'blue', text: '中' },
  high: { color: 'orange', text: '高' },
  critical: { color: 'red', text: '严重' },
}

// 简化的图标组件
function ClockIcon() {
  return <span>⏱️</span>
}
function LoadingIcon() {
  return <span>⏳</span>
}

const PlagiarismCheckPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>()

  const [checks, setChecks] = useState<PlagiarismCheck[]>([])
  const [currentCheck, setCurrentCheck] = useState<PlagiarismCheck | null>(null)
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [selectedCheckId, setSelectedCheckId] = useState<string | null>(null)

  // 获取查重列表
  const fetchChecks = useCallback(async () => {
    setLoading(true)
    try {
      const res = await plagiarismService.getChecks({
        paper_id: paperId,
        page: 1,
        page_size: 50
      })
      setChecks(res.data?.data?.items || [])
    } catch (error) {
      console.error('获取查重列表失败', error)
    } finally {
      setLoading(false)
    }
  }, [paperId])

  useEffect(() => {
    fetchChecks()
  }, [fetchChecks])

  // 获取报告详情
  const fetchReport = async (checkId: string) => {
    try {
      const res = await plagiarismService.getCheckReport(checkId)
      setReport(res.data?.data)
      setSelectedCheckId(checkId)
    } catch (error) {
      message.error('获取报告失败')
    }
  }

  // 上传文件查重
  const uploadProps: UploadProps = {
    name: 'file',
    showUploadList: false,
    beforeUpload: (file) => {
      const isValid = file.type === 'text/plain' ||
                      file.name.endsWith('.docx') ||
                      file.name.endsWith('.doc') ||
                      file.name.endsWith('.pdf')
      if (!isValid) {
        message.error('请上传 .txt, .docx, .doc 或 .pdf 文件')
        return false
      }
      return true
    },
    customRequest: async ({ file, onSuccess, onError }) => {
      setUploading(true)
      try {
        const res = await plagiarismService.uploadAndCheck(
          file as File,
          'mock', // 使用模拟引擎进行演示
          paperId
        )
        const check = res.data?.data
        setCurrentCheck(check)
        message.success('查重任务已提交')
        fetchChecks()
        onSuccess?.('ok')
      } catch (error) {
        message.error('提交失败')
        onError?.(error as Error)
      } finally {
        setUploading(false)
      }
    }
  }

  // 提交新的查重
  const handleSubmitCheck = async () => {
    try {
      const res = await plagiarismService.submitCheck({
        paper_id: paperId,
        engine: 'mock'
      })
      const check = res.data?.data
      setCurrentCheck(check)
      message.success('查重任务已提交')
      fetchChecks()
    } catch (error) {
      message.error('提交失败')
    }
  }

  // 删除查重记录
  const handleDelete = async (id: string) => {
    try {
      await plagiarismService.deleteCheck(id)
      message.success('已删除')
      fetchChecks()
      if (selectedCheckId === id) {
        setSelectedCheckId(null)
        setReport(null)
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  // 表格列
  const columns = [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'name',
      render: (text: string, record: PlagiarismCheck) => (
        <Space>
          <Text strong={selectedCheckId === record.id}>
            {text || `查重任务 ${record.id.slice(0, 8)}`}
          </Text>
          {record.engine === 'turnitin' && <Tag color="blue">Turnitin</Tag>}
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: CheckStatus) => {
        const config = STATUS_CONFIG[status]
        return (
          <Tag icon={config.icon} color={config.color}>
            {config.text}
          </Tag>
        )
      }
    },
    {
      title: '总体相似度',
      dataIndex: 'overall_similarity',
      key: 'similarity',
      width: 120,
      render: (val: number, record: PlagiarismCheck) => {
        if (record.status !== 'completed') return '-'
        const color = (val || 0) > 30 ? 'red' : (val || 0) > 15 ? 'orange' : 'green'
        return <Text style={{ color, fontWeight: 'bold' }}>{(val || 0).toFixed(1)}%</Text>
      }
    },
    {
      title: '提交时间',
      dataIndex: 'submitted_at',
      key: 'submitted',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: PlagiarismCheck) => (
        <Space>
          {record.status === 'completed' && (
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => fetchReport(record.id)}
            >
              查看
            </Button>
          )}
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      )
    }
  ]

  return (
    <div className={styles.container}>
      <Title level={2}><SafetyOutlined /> 查重检测</Title>

      <Row gutter={24}>
        <Col span={16}>
          {/* 上传区域 */}
          <Card className={styles.uploadCard}>
            <Row gutter={16} align="middle">
              <Col flex="auto">
                <div>
                  <Text strong style={{ fontSize: 16 }}>提交论文进行查重检测</Text>
                  <br />
                  <Text type="secondary">
                    支持 .txt, .docx, .doc, .pdf 格式，系统将自动检测相似度
                  </Text>
                </div>
              </Col>
              <Col>
                <Space>
                  <Upload {...uploadProps}>
                    <Button
                      type="primary"
                      icon={<UploadOutlined />}
                      loading={uploading}
                      size="large"
                    >
                      上传文件查重
                    </Button>
                  </Upload>
                  {paperId && (
                    <Button
                      icon={<FileTextOutlined />}
                      onClick={handleSubmitCheck}
                      size="large"
                    >
                      直接查重
                    </Button>
                  )}
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 查重列表 */}
          <Card title="检测历史" className={styles.historyCard}>
            <Table
              rowKey="id"
              columns={columns}
              dataSource={checks}
              loading={loading}
              pagination={{ pageSize: 10 }}
              size="small"
              locale={{
                emptyText: <Empty description="暂无查重记录" />
              }}
            />
          </Card>
        </Col>

        <Col span={8}>
          {/* 报告展示 */}
          {report ? (
            <Card title="检测报告" className={styles.reportCard}>
              {/* 相似度统计 */}
              <div className={styles.similarityStats}>
                <div className={styles.overallScore}>
                  <Progress
                    type="circle"
                    percent={Math.round(report.overall_similarity * 100)}
                    strokeColor={
                      report.overall_similarity > 0.3 ? '#ff4d4f' :
                      report.overall_similarity > 0.15 ? '#faad14' : '#52c41a'
                    }
                    size={120}
                    format={(p) => (
                      <div>
                        <div style={{ fontSize: 24, fontWeight: 'bold' }}>{p}%</div>
                        <div style={{ fontSize: 12 }}>总体相似度</div>
                      </div>
                    )}
                  />
                </div>

                <Row gutter={[8, 8]} className={styles.detailStats}>
                  <Col span={12}>
                    <Card size="small">
                      <Statistic
                        title="互联网资源"
                        value={(report.internet_similarity || 0).toFixed(1)}
                        suffix="%"
                        valueStyle={{ fontSize: 16 }}
                      />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card size="small">
                      <Statistic
                        title="出版物"
                        value={(report.publications_similarity || 0).toFixed(1)}
                        suffix="%"
                        valueStyle={{ fontSize: 16 }}
                      />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card size="small">
                      <Statistic
                        title="学生论文"
                        value={(report.student_papers_similarity || 0).toFixed(1)}
                        suffix="%"
                        valueStyle={{ fontSize: 16 }}
                      />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card size="small">
                      <Statistic
                        title="严重程度"
                        value={SEVERITY_CONFIG[report.severity]?.text || '未知'}
                        valueStyle={{
                          fontSize: 16,
                          color: SEVERITY_CONFIG[report.severity]?.color
                        }}
                      />
                    </Card>
                  </Col>
                </Row>
              </div>

              {/* 相似片段 */}
              {report.section_reports?.[0]?.similar_segments?.length > 0 && (
                <>
                  <Divider>相似片段</Divider>
                  <List
                    dataSource={report.section_reports[0].similar_segments.slice(0, 5)}
                    renderItem={(segment: any) => (
                      <List.Item>
                        <Card size="small" style={{ width: '100%' }}>
                          <Space direction="vertical" style={{ width: '100%' }}>
                            <Text type="secondary" ellipsis>{segment.source_text}</Text>
                            <Space>
                              <Tag color="red">相似度: {(segment.similarity * 100).toFixed(0)}%</Tag>
                              {segment.source_title && (
                                <Tag>{segment.source_title}</Tag>
                              )}
                            </Space>
                          </Space>
                        </Card>
                      </List.Item>
                    )}
                  />
                </>
              )}

              {/* 下载报告 */}
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  href={report.report_url}
                  disabled={!report.report_url}
                >
                  下载完整报告
                </Button>
              </div>
            </Card>
          ) : (
            <Card className={styles.emptyReport}>
              <Empty
                image={<FileSearchOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />}
                description="选择左侧查重任务查看详细报告"
              />
            </Card>
          )}
        </Col>
      </Row>
    </div>
  )
}

// 分隔符组件
const Divider: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <div style={{
    margin: '16px 0',
    borderBottom: '1px solid #f0f0f0',
    textAlign: 'center',
    lineHeight: '0'
  }}>
    <span style={{
      background: '#fff',
      padding: '0 16px',
      color: '#999',
      fontSize: 12
    }}>
      {children}
    </span>
  </div>
)

export default PlagiarismCheckPage
