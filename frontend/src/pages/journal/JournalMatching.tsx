/**
 * 期刊匹配页面
 */

import React, { useState, useEffect } from 'react'
import {
  Card, Row, Col, Button, Input, List, Tag, Progress, Modal, Table, Badge, Tabs,
  Select, Space, Typography, Empty, message, Form, Tooltip, Statistic, Divider
} from 'antd'
import {
  BookOutlined, SearchOutlined, StarOutlined, ArrowRightOutlined,
  BarChartOutlined, HistoryOutlined, FileTextOutlined, TrophyOutlined,
  CheckCircleOutlined, GlobalOutlined, PercentageOutlined
} from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import { journalService, type Journal, type MatchResult, type SubmissionRecord } from '@/services/journalService'
import styles from './JournalMatching.module.css'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { TabPane } = Tabs
const { Search } = Input

const JournalMatching: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>()
  const [journals, setJournals] = useState<Journal[]>([])
  const [matchResults, setMatchResults] = useState<MatchResult[]>([])
  const [submissions, setSubmissions] = useState<SubmissionRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [matching, setMatching] = useState(false)
  const [selectedJournal, setSelectedJournal] = useState<Journal | null>(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [submitModalVisible, setSubmitModalVisible] = useState(false)
  const [searchParams, setSearchParams] = useState({ field: '', keywords: '' })

  // 获取期刊列表
  const fetchJournals = async (params?: any) => {
    setLoading(true)
    try {
      const res = await journalService.getJournals(params)
      setJournals(res.data?.data?.items || [])
    } catch (error) {
      message.error('获取期刊列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取投稿记录
  const fetchSubmissions = async () => {
    try {
      const res = await journalService.getSubmissions()
      setSubmissions(res.data?.data?.items || [])
    } catch (error) {
      console.error('获取投稿记录失败', error)
    }
  }

  // 执行期刊匹配
  const handleMatch = async () => {
    if (!searchParams.field) {
      message.warning('请输入研究领域')
      return
    }
    setMatching(true)
    try {
      const res = await journalService.matchJournals({
        paper_id: paperId || 'temp',
        title: searchParams.field,
        keywords: searchParams.keywords.split(',').map(k => k.trim()).filter(Boolean),
        field: searchParams.field,
      })
      setMatchResults(res.data?.data?.results || [])
      message.success('期刊匹配完成')
    } catch (error) {
      message.error('期刊匹配失败')
    } finally {
      setMatching(false)
    }
  }

  // 创建投稿记录
  const handleSubmit = async (values: any) => {
    if (!selectedJournal || !paperId) return
    try {
      await journalService.createSubmission({
        paper_id: paperId,
        journal_id: selectedJournal.id,
        manuscript_id: values.manuscript_id,
        notes: values.notes,
      })
      message.success('投稿记录已创建')
      setSubmitModalVisible(false)
      fetchSubmissions()
    } catch (error) {
      message.error('创建投稿记录失败')
    }
  }

  // 查看期刊详情
  const handleViewDetail = async (journalId: string) => {
    try {
      const res = await journalService.getJournal(journalId)
      setSelectedJournal(res.data?.data)
      setDetailVisible(true)
    } catch (error) {
      message.error('获取期刊详情失败')
    }
  }

  useEffect(() => {
    fetchJournals()
    fetchSubmissions()
  }, [])

  const columns = [
    { title: '期刊名称', dataIndex: 'name', key: 'name', render: (text: string) => <strong>{text}</strong> },
    { title: '学科领域', dataIndex: 'subject_areas', key: 'subject_areas',
      render: (areas: string[]) => <Space>{areas?.map(a => <Tag key={a}>{a}</Tag>)}</Space> },
    { title: '影响因子', dataIndex: 'impact_factor', key: 'impact_factor',
      render: (if_: number) => if_ ? if_.toFixed(2) : '-' },
    { title: '录用率', dataIndex: 'acceptance_rate', key: 'acceptance_rate',
      render: (rate: number) => rate ? `${(rate * 100).toFixed(0)}%` : '-' },
    { title: '操作', key: 'action',
      render: (_: any, record: Journal) => (
        <Button type="link" onClick={() => handleViewDetail(record.id)}>详情</Button>
      )
    },
  ]

  return (
    <div className={styles.container}>
      <Title level={2}><BookOutlined /> 期刊智能匹配</Title>

      <Card className={styles.searchCard}>
        <Row gutter={16}>
          <Col span={10}>
            <Input
              placeholder="研究领域（如：工程管理）"
              value={searchParams.field}
              onChange={e => setSearchParams({ ...searchParams, field: e.target.value })}
              size="large"
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col span={10}>
            <Input
              placeholder="关键词（用逗号分隔）"
              value={searchParams.keywords}
              onChange={e => setSearchParams({ ...searchParams, keywords: e.target.value })}
              size="large"
            />
          </Col>
          <Col span={4}>
            <Button
              type="primary"
              size="large"
              block
              onClick={handleMatch}
              loading={matching}
              icon={<SearchOutlined />}
            >
              智能匹配
            </Button>
          </Col>
        </Row>
      </Card>

      <Tabs defaultActiveKey="matches">
        <TabPane tab={<span><TrophyOutlined /> 匹配结果</span>} key="matches">
          {matchResults.length === 0 ? (
            <Empty description="请输入研究领域并点击智能匹配" />
          ) : (
            <List
              grid={{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2 }}
              dataSource={matchResults}
              renderItem={(result: MatchResult) => (
                <List.Item>
                  <Card
                    className={styles.matchCard}
                    title={
                      <div className={styles.cardTitle}>
                        {result.journal.name}
                        <Tag color={result.match_score >= 80 ? 'green' : result.match_score >= 60 ? 'blue' : 'orange'}>
                          匹配度: {result.match_score}%
                        </Tag>
                      </div>
                    }
                    actions={[
                      <Button type="link" onClick={() => { setSelectedJournal(result.journal); setSubmitModalVisible(true) }}>
                        记录投稿
                      </Button>,
                      <Button type="link" onClick={() => handleViewDetail(result.journal.id)}>
                        查看详情
                      </Button>,
                    ]}
                  >
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        {result.journal.subject_areas?.map((a: string) => <Tag key={a} size="small">{a}</Tag>)}
                      </div>
                      <div className={styles.stats}>
                        <span>影响因子: {result.journal.impact_factor || '-'}</span>
                        <span>录用率: {result.journal.acceptance_rate ? `${(result.journal.acceptance_rate * 100).toFixed(0)}%` : '-'}</span>
                      </div>
                      <div className={styles.reasons}>
                        {result.match_reasons.map((r, i) => <div key={i}><CheckCircleOutlined /> {r}</div>)}
                      </div>
                    </Space>
                  </Card>
                </List.Item>
              )}
            />
          )}
        </TabPane>

        <TabPane tab={<span><BookOutlined /> 期刊库</span>} key="journals">
          <Table dataSource={journals} columns={columns} rowKey="id" loading={loading} />
        </TabPane>

        <TabPane tab={<span><HistoryOutlined /> 投稿记录</span>} key="submissions">
          <Table
            dataSource={submissions}
            columns={[
              { title: '期刊', dataIndex: 'journal_name', key: 'journal' },
              { title: '稿件号', dataIndex: 'manuscript_id', key: 'manuscript_id' },
              { title: '状态', dataIndex: 'status', key: 'status',
                render: (s: string) => <Badge status={s === 'accepted' ? 'success' : s === 'rejected' ? 'error' : 'processing'} text={s} />
              },
              { title: '投稿日期', dataIndex: 'submitted_at', key: 'submitted_at' },
            ]}
            rowKey="id"
          />
        </TabPane>
      </Tabs>

      {/* 期刊详情弹窗 */}
      <Modal
        title={selectedJournal?.name}
        visible={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>关闭</Button>,
          <Button key="submit" type="primary" onClick={() => { setDetailVisible(false); setSubmitModalVisible(true) }}>
            记录投稿
          </Button>,
        ]}
      >
        {selectedJournal && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <p><strong>学科领域:</strong> {selectedJournal.subject_areas?.join(', ')}</p>
            <p><strong>影响因子:</strong> {selectedJournal.impact_factor || '-'}</p>
            <p><strong>录用率:</strong> {selectedJournal.acceptance_rate ? `${(selectedJournal.acceptance_rate * 100).toFixed(0)}%` : '-'}</p>
            <p><strong>审稿周期:</strong> {selectedJournal.review_cycle_days ? `${selectedJournal.review_cycle_days}天` : '-'}</p>
            {selectedJournal.submission_url && (
              <p><strong>投稿链接:</strong> <a href={selectedJournal.submission_url} target="_blank" rel="noreferrer">{selectedJournal.submission_url}</a></p>
            )}
          </Space>
        )}
      </Modal>

      {/* 投稿记录弹窗 */}
      <Modal
        title="记录投稿"
        visible={submitModalVisible}
        onCancel={() => setSubmitModalVisible(false)}
        onOk={() => { /* submit form */ }}
        footer={null}
      >
        <Form onFinish={handleSubmit} layout="vertical">
          <Form.Item label="期刊">
            <Input value={selectedJournal?.name} disabled />
          </Form.Item>
          <Form.Item name="manuscript_id" label="稿件号">
            <Input placeholder="期刊分配的稿件号" />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>保存</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default JournalMatching
