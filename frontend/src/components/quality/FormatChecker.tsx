/**
 * 格式检查组件
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
  Select,
  Spin,
  Statistic,
  Row,
  Col,
  Divider,
  Empty,
  message,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  SyncOutlined,
} from '@ant-design/icons'

import { formatService } from '@/services/formatService'
import type { FormatCheckResult } from '@/types/format'
import styles from './Quality.module.css'

const { Text, Title, Paragraph } = Typography

interface FormatCheckerProps {
  paperId: string
  paperTitle?: string
}

const FormatChecker: React.FC<FormatCheckerProps> = ({
  paperId,
  paperTitle,
}) => {
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(false)
  const [result, setResult] = useState<FormatCheckResult | null>(null)
  const [templates, setTemplates] = useState<{ id: string; name: string }[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>()

  // 加载模板
  const loadTemplates = useCallback(async () => {
    try {
      const response = await formatService.getTemplates()
      setTemplates(response.data.map(t => ({ id: t.id, name: t.name })))
      if (response.data.length > 0) {
        setSelectedTemplate(response.data[0].id)
      }
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }, [])

  // 加载检查结果
  const loadResult = useCallback(async () => {
    setLoading(true)
    try {
      const response = await formatService.getCheckResult(paperId)
      setResult(response.data)
    } catch (error) {
      console.error('Failed to load result:', error)
    } finally {
      setLoading(false)
    }
  }, [paperId])

  useEffect(() => {
    loadTemplates()
    loadResult()
  }, [loadTemplates, loadResult])

  // 发起检查
  const handleStartCheck = async () => {
    setChecking(true)
    try {
      await formatService.startCheck({
        paperId,
        templateId: selectedTemplate,
      })
      message.success('格式检查已开始')

      // 模拟检查完成
      setTimeout(() => {
        loadResult()
        setChecking(false)
      }, 1500)
    } catch (error) {
      message.error('检查失败')
      setChecking(false)
    }
  }

  // 获取问题图标和颜色
  const getIssueStyle = (severity: string) => {
    switch (severity) {
      case 'error':
        return { icon: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />, color: 'error' }
      case 'warning':
        return { icon: <WarningOutlined style={{ color: '#faad14' }} />, color: 'warning' }
      case 'info':
        return { icon: <InfoCircleOutlined style={{ color: '#1890ff' }} />, color: 'processing' }
      default:
        return { icon: <InfoCircleOutlined />, color: 'default' }
    }
  }

  // 获取分数颜色
  const getScoreColor = (score: number) => {
    if (score >= 90) return '#52c41a'
    if (score >= 70) return '#faad14'
    return '#ff4d4f'
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className={styles.formatChecker}>
      {/* 标题区域 */}
      <Card className={styles.headerCard}>
        <div className={styles.headerContent}>
          <div>
            <Title level={4}>
              <SettingOutlined style={{ marginRight: 8 }} />
              格式检查
            </Title>
            <Text type="secondary">{paperTitle || '论文格式检查'}</Text>
          </div>
          <Space>
            <Select
              style={{ width: 200 }}
              placeholder="选择格式模板"
              value={selectedTemplate}
              onChange={setSelectedTemplate}
              options={templates.map(t => ({
                value: t.id,
                label: t.name,
              }))}
            />
            <Button
              type="primary"
              icon={<SyncOutlined />}
              onClick={handleStartCheck}
              loading={checking}
            >
              开始检查
            </Button>
          </Space>
        </div>
      </Card>

      {checking && (
        <Card className={styles.checkingCard}>
          <div className={styles.checkingContent}>
            <Spin size="large" />
            <Title level={5}>正在检查格式...</Title>
            <Progress percent={50} status="active" />
          </div>
        </Card>
      )}

      {result && !checking && (
        <>
          {/* 结果概览 */}
          <Card className={styles.resultCard}>
            <Row gutter={24}>
              <Col span={6}>
                <div className={styles.scoreDisplay}>
                  <Progress
                    type="circle"
                    percent={result.score}
                    strokeColor={getScoreColor(result.score)}
                    format={(percent) => (
                      <span style={{ fontSize: 24, fontWeight: 'bold', color: getScoreColor(result.score) }}>
                        {percent}
                      </span>
                    )}
                  />
                  <Text type="secondary">格式评分</Text>
                </div>
              </Col>
              <Col span={18}>
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="错误"
                      value={result.summary.errorCount}
                      valueStyle={{ color: '#ff4d4f' }}
                      prefix={<CloseCircleOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="警告"
                      value={result.summary.warningCount}
                      valueStyle={{ color: '#faad14' }}
                      prefix={<WarningOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="提示"
                      value={result.summary.infoCount}
                      valueStyle={{ color: '#1890ff' }}
                      prefix={<InfoCircleOutlined />}
                    />
                  </Col>
                </Row>
                <Divider />
                <Space>
                  <Text type="secondary">检查时间: {new Date(result.checkedAt).toLocaleString('zh-CN')}</Text>
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 问题列表 */}
          <Card title="检查结果" className={styles.issuesCard}>
            {result.issues.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="格式检查全部通过"
              />
            ) : (
              <List
                dataSource={result.issues}
                renderItem={(issue) => {
                  const style = getIssueStyle(issue.severity)
                  return (
                    <List.Item className={styles.issueItem}>
                      <div className={styles.issueContent}>
                        <div className={styles.issueHeader}>
                          <Space>
                            {style.icon}
                            <Text strong>{issue.ruleName}</Text>
                            <Tag color={style.color}>
                              {issue.severity === 'error' ? '错误' : issue.severity === 'warning' ? '警告' : '提示'}
                            </Tag>
                          </Space>
                        </div>
                        <Paragraph className={styles.issueMessage}>
                          {issue.message}
                        </Paragraph>
                        {issue.suggestion && (
                          <div className={styles.issueSuggestion}>
                            <Text type="secondary">
                              <InfoCircleOutlined style={{ marginRight: 4 }} />
                              建议: {issue.suggestion}
                            </Text>
                          </div>
                        )}
                      </div>
                    </List.Item>
                  )
                }}
              />
            )}
          </Card>

          {/* 通过的规则 */}
          {result.passedRules.length > 0 && (
            <Card title="通过的检查项" className={styles.passedCard}>
              <Space wrap>
                {result.passedRules.map((ruleId) => (
                  <Tag key={ruleId} icon={<CheckCircleOutlined />} color="success">
                    {ruleId}
                  </Tag>
                ))}
              </Space>
            </Card>
          )}
        </>
      )}
    </div>
  )
}

export default FormatChecker
