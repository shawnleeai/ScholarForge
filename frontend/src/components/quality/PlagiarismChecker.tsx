/**
 * 查重检测组件
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Button,
  Progress,
  Typography,
  Space,
  Tag,
  List,
  Collapse,
  Alert,
  Spin,
  Statistic,
  Row,
  Col,
  Divider,
  Modal,
  Checkbox,
  message,
  Empty,
} from 'antd'
import {
  SearchOutlined,
  DownloadOutlined,
  HistoryOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons'

import { plagiarismService } from '@/services/plagiarismService'
import type { PlagiarismReport, PlagiarismMatch } from '@/types/plagiarism'
import styles from './Quality.module.css'

const { Text, Title, Paragraph } = Typography
const { Panel } = Collapse

interface PlagiarismCheckerProps {
  paperId: string
  paperTitle?: string
}

const PlagiarismChecker: React.FC<PlagiarismCheckerProps> = ({
  paperId,
  paperTitle,
}) => {
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(false)
  const [report, setReport] = useState<PlagiarismReport | null>(null)
  const [optionsVisible, setOptionsVisible] = useState(false)
  const [checkOptions, setCheckOptions] = useState({
    checkWeb: true,
    checkDatabase: true,
    checkPapers: true,
    excludeQuotes: true,
    excludeReferences: true,
  })

  // 加载最新报告
  const loadReport = useCallback(async () => {
    setLoading(true)
    try {
      const response = await plagiarismService.getReport(paperId)
      setReport(response.data)
    } catch (error) {
      console.error('Failed to load report:', error)
    } finally {
      setLoading(false)
    }
  }, [paperId])

  useEffect(() => {
    loadReport()
  }, [loadReport])

  // 发起检测
  const handleStartCheck = async () => {
    setChecking(true)
    setOptionsVisible(false)
    try {
      await plagiarismService.startCheck({
        paperId,
        options: checkOptions,
      })

      message.success('查重检测已开始')

      // 模拟进度更新
      setTimeout(() => {
        loadReport()
        setChecking(false)
      }, 2000)
    } catch (error) {
      message.error('发起检测失败')
      setChecking(false)
    }
  }

  // 下载报告
  const handleDownload = async () => {
    if (!report) return
    try {
      const response = await plagiarismService.downloadReport(paperId, report.id)
      window.open(response.data.downloadUrl, '_blank')
    } catch (error) {
      message.error('下载失败')
    }
  }

  // 获取相似度颜色
  const getSimilarityColor = (similarity: number) => {
    if (similarity < 15) return '#52c41a'
    if (similarity < 30) return '#faad14'
    return '#ff4d4f'
  }

  // 获取相似度状态
  const getSimilarityStatus = (similarity: number) => {
    if (similarity < 15) return { text: '通过', icon: <CheckCircleOutlined />, color: 'success' }
    if (similarity < 30) return { text: '需修改', icon: <ExclamationCircleOutlined />, color: 'warning' }
    return { text: '高风险', icon: <ExclamationCircleOutlined />, color: 'error' }
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <Spin size="large" />
      </div>
    )
  }

  const status = report ? getSimilarityStatus(report.overallSimilarity) : null

  return (
    <div className={styles.plagiarismChecker}>
      {/* 标题区域 */}
      <Card className={styles.headerCard}>
        <div className={styles.headerContent}>
          <div>
            <Title level={4}>
              <SearchOutlined style={{ marginRight: 8 }} />
              查重检测
            </Title>
            <Text type="secondary">{paperTitle || '论文查重检测'}</Text>
          </div>
          <Space>
            <Button
              icon={<HistoryOutlined />}
            >
              历史记录
            </Button>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={() => setOptionsVisible(true)}
              loading={checking}
            >
              开始检测
            </Button>
          </Space>
        </div>
      </Card>

      {checking && (
        <Card className={styles.checkingCard}>
          <div className={styles.checkingContent}>
            <Spin size="large" />
            <Title level={5}>正在检测中...</Title>
            <Text type="secondary">预计需要 2-5 分钟</Text>
            <Progress percent={50} status="active" />
          </div>
        </Card>
      )}

      {report && !checking && (
        <>
          {/* 结果概览 */}
          <Card className={styles.resultCard}>
            <Row gutter={24}>
              <Col span={8}>
                <div className={styles.scoreCircle}>
                  <Progress
                    type="circle"
                    percent={100 - report.overallSimilarity}
                    format={() => (
                      <div className={styles.scoreText}>
                        <span
                          className={styles.scoreValue}
                          style={{ color: getSimilarityColor(report.overallSimilarity) }}
                        >
                          {report.overallSimilarity.toFixed(1)}%
                        </span>
                        <span className={styles.scoreLabel}>相似度</span>
                      </div>
                    )}
                    strokeColor={getSimilarityColor(report.overallSimilarity)}
                    trailColor="#f0f0f0"
                  />
                </div>
              </Col>
              <Col span={16}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {status && (
                    <Alert
                      message={status.text}
                      description={
                        report.overallSimilarity < 15
                          ? '论文原创度较高，符合学术规范要求'
                          : report.overallSimilarity < 30
                            ? '存在部分相似内容，建议进行修改'
                            : '相似度较高，请认真检查并修改'
                      }
                      type={status.color as 'success' | 'warning' | 'error'}
                      icon={status.icon}
                      showIcon
                    />
                  )}
                  <Row gutter={16}>
                    <Col span={8}>
                      <Statistic
                        title="检测字数"
                        value={report.wordCount}
                        suffix="字"
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="检测章节"
                        value={report.sections.length}
                        suffix="个"
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="检测时间"
                        value={new Date(report.checkedAt).toLocaleString('zh-CN', {
                          month: 'numeric',
                          day: 'numeric',
                          hour: 'numeric',
                          minute: 'numeric',
                        })}
                      />
                    </Col>
                  </Row>
                </Space>
              </Col>
            </Row>
            <Divider />
            <div className={styles.actions}>
              <Button icon={<DownloadOutlined />} onClick={handleDownload}>
                下载报告
              </Button>
            </div>
          </Card>

          {/* 章节详情 */}
          <Card title="章节详情" className={styles.detailCard}>
            <Collapse accordion>
              {report.sections.map((section) => (
                <Panel
                  key={section.sectionId}
                  header={
                    <Space>
                      <FileTextOutlined />
                      <span>{section.sectionTitle}</span>
                      <Tag color={getSimilarityColor(section.similarity)}>
                        {section.similarity.toFixed(1)}%
                      </Tag>
                    </Space>
                  }
                >
                  {section.matches.length === 0 ? (
                    <Empty description="无匹配内容" />
                  ) : (
                    <List
                      dataSource={section.matches}
                      renderItem={(match) => (
                        <MatchItem key={match.id} match={match} />
                      )}
                    />
                  )}
                </Panel>
              ))}
            </Collapse>
          </Card>

          {/* 修改建议 */}
          {report.suggestions.length > 0 && (
            <Card title="修改建议" className={styles.suggestionCard}>
              <List
                dataSource={report.suggestions}
                renderItem={(item, index) => (
                  <List.Item key={index}>
                    <Text>
                      <Tag color="blue">{index + 1}</Tag>
                      {item}
                    </Text>
                  </List.Item>
                )}
              />
            </Card>
          )}
        </>
      )}

      {/* 检测选项弹窗 */}
      <Modal
        title="查重检测选项"
        open={optionsVisible}
        onOk={handleStartCheck}
        onCancel={() => setOptionsVisible(false)}
        okText="开始检测"
      >
        <div className={styles.optionsForm}>
          <Text strong>检测范围</Text>
          <div className={styles.optionGroup}>
            <Checkbox
              checked={checkOptions.checkWeb}
              onChange={(e) => setCheckOptions({ ...checkOptions, checkWeb: e.target.checked })}
            >
              互联网资源
            </Checkbox>
            <Checkbox
              checked={checkOptions.checkDatabase}
              onChange={(e) => setCheckOptions({ ...checkOptions, checkDatabase: e.target.checked })}
            >
              学术数据库
            </Checkbox>
            <Checkbox
              checked={checkOptions.checkPapers}
              onChange={(e) => setCheckOptions({ ...checkOptions, checkPapers: e.target.checked })}
            >
              其他论文
            </Checkbox>
          </div>
          <Divider />
          <Text strong>排除选项</Text>
          <div className={styles.optionGroup}>
            <Checkbox
              checked={checkOptions.excludeQuotes}
              onChange={(e) => setCheckOptions({ ...checkOptions, excludeQuotes: e.target.checked })}
            >
              排除引用内容
            </Checkbox>
            <Checkbox
              checked={checkOptions.excludeReferences}
              onChange={(e) => setCheckOptions({ ...checkOptions, excludeReferences: e.target.checked })}
            >
              排除参考文献
            </Checkbox>
          </div>
        </div>
      </Modal>
    </div>
  )
}

// 匹配项组件
const MatchItem: React.FC<{ match: PlagiarismMatch }> = ({ match }) => {
  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'web': return '🌐'
      case 'paper': return '📄'
      case 'database': return '📚'
      default: return '📝'
    }
  }

  return (
    <List.Item className={styles.matchItem}>
      <div className={styles.matchContent}>
        <div className={styles.matchHeader}>
          <Space>
            <span>{getSourceIcon(match.source.type)}</span>
            <Text strong>{match.source.title}</Text>
            {match.source.author && (
              <Text type="secondary">- {match.source.author}</Text>
            )}
          </Space>
          <Tag color={match.similarity > 90 ? 'red' : match.similarity > 70 ? 'orange' : 'blue'}>
            相似度 {match.similarity}%
          </Tag>
        </div>
        <Paragraph
          type="secondary"
          ellipsis={{ rows: 2 }}
          className={styles.matchText}
        >
          "{match.text}"
        </Paragraph>
        {match.source.url && (
          <a href={match.source.url} target="_blank" rel="noopener noreferrer">
            查看来源
          </a>
        )}
      </div>
    </List.Item>
  )
}

export default PlagiarismChecker
