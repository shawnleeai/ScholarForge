/**
 * 查重报告组件
 * 展示查重结果，包括相似度统计、匹配来源、重复片段高亮
 */

import React, { useState, useMemo } from 'react'
import {
  Card,
  Progress,
  Tag,
  List,
  Typography,
  Space,
  Divider,
  Button,
  Tooltip,
  Badge,
  Tabs,
  Statistic,
  Row,
  Col,
  Alert,
  Empty,
  Collapse,
} from 'antd'
import {
  FileTextOutlined,
  LinkOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import type { TabsProps } from 'antd'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

export interface PlagiarismMatch {
  id: string
  text: string
  startIndex: number
  endIndex: number
  similarity: number
  sourceId: string
  sourceTitle: string
  sourceUrl?: string
}

export interface PlagiarismSource {
  id: string
  title: string
  type: 'internet' | 'publication' | 'student_paper' | 'local'
  url?: string
  similarity: number
  matchCount: number
}

export interface PlagiarismReportData {
  success: boolean
  overallSimilarity: number
  internetSimilarity: number
  publicationsSimilarity: number
  studentPapersSimilarity: number
  matches: PlagiarismMatch[]
  sources: PlagiarismSource[]
  processingTime: number
  errorMessage?: string
  recommendation?: string
}

interface PlagiarismReportProps {
  data: PlagiarismReportData
  originalText: string
  onDownload?: () => void
  onShare?: () => void
}

export const PlagiarismReport: React.FC<PlagiarismReportProps> = ({
  data,
  originalText,
  onDownload,
  onShare,
}) => {
  const [selectedMatch, setSelectedMatch] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  // 计算相似度等级
  const similarityLevel = useMemo(() => {
    const sim = data.overallSimilarity
    if (sim < 15) return { level: 'low', color: '#52c41a', text: '低' }
    if (sim < 30) return { level: 'medium', color: '#faad14', text: '中' }
    if (sim < 50) return { level: 'high', color: '#fa8c16', text: '较高' }
    return { level: 'danger', color: '#f5222d', text: '高' }
  }, [data.overallSimilarity])

  // 获取推荐建议
  const recommendation = useMemo(() => {
    if (data.recommendation) return data.recommendation

    const sim = data.overallSimilarity
    if (sim < 15) return '相似度很低，论文原创性良好'
    if (sim < 30) return '相似度较低，基本符合要求，建议检查标红部分'
    if (sim < 50) return '相似度中等，需要修改部分重复内容'
    if (sim < 70) return '相似度较高，建议大幅修改重复段落'
    return '相似度过高，存在严重抄袭风险，必须全面修改'
  }, [data.recommendation, data.overallSimilarity])

  // 高亮显示重复文本
  const renderHighlightedText = () => {
    if (!data.matches.length) {
      return <Paragraph>{originalText}</Paragraph>
    }

    // 按位置排序匹配项
    const sortedMatches = [...data.matches].sort(
      (a, b) => a.startIndex - b.startIndex
    )

    const elements: React.ReactNode[] = []
    let lastIndex = 0

    sortedMatches.forEach((match, index) => {
      // 添加匹配前的文本
      if (match.startIndex > lastIndex) {
        elements.push(
          <span key={`text-${index}`}>
            {originalText.slice(lastIndex, match.startIndex)}
          </span>
        )
      }

      // 添加高亮的匹配文本
      const isSelected = selectedMatch === match.id
      elements.push(
        <Tooltip
          key={`match-${index}`}
          title={
            <div>
              <div>相似度: {(match.similarity * 100).toFixed(1)}%</div>
              <div>来源: {match.sourceTitle}</div>
            </div>
          }
        >
          <span
            style={{
              backgroundColor: isSelected
                ? '#ff4d4f'
                : `rgba(255, 77, 79, ${match.similarity * 0.3 + 0.2})`,
              cursor: 'pointer',
              padding: '2px 4px',
              borderRadius: 4,
              transition: 'all 0.2s',
            }}
            onClick={() => setSelectedMatch(match.id)}
          >
            {originalText.slice(match.startIndex, match.endIndex)}
          </span>
        </Tooltip>
      )

      lastIndex = match.endIndex
    })

    // 添加剩余的文本
    if (lastIndex < originalText.length) {
      elements.push(
        <span key="text-end">{originalText.slice(lastIndex)}</span>
      )
    }

    return (
      <div
        style={{
          maxHeight: 400,
          overflow: 'auto',
          padding: 16,
          background: '#fafafa',
          borderRadius: 8,
          lineHeight: 1.8,
        }}
      >
        {elements}
      </div>
    )
  }

  // 渲染来源列表
  const renderSourcesList = () => {
    return (
      <List
        dataSource={data.sources}
        renderItem={(source) => (
          <List.Item
            actions={[
              source.url && (
                <Button
                  type="link"
                  icon={<LinkOutlined />}
                  href={source.url}
                  target="_blank"
                >
                  查看
                </Button>
              ),
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <Text strong>{source.title}</Text>
                  <Tag
                    color={
                      source.type === 'internet'
                        ? 'blue'
                        : source.type === 'publication'
                        ? 'green'
                        : 'orange'
                    }
                  >
                    {source.type === 'internet'
                      ? '网络'
                      : source.type === 'publication'
                      ? '出版物'
                      : '学生论文'}
                  </Tag>
                </Space>
              }
              description={
                <Space direction="vertical" size={4}>
                  <Text type="secondary">
                    相似度: {(source.similarity * 100).toFixed(1)}% | 匹配片段:{' '}
                    {source.matchCount} 处
                  </Text>
                </Space>
              }
            />
          </List.Item>
        )}
      />
    )
  }

  // 渲染匹配详情
  const renderMatchesDetail = () => {
    return (
      <Collapse>
        {data.matches.map((match) => (
          <Panel
            header={
              <Space>
                <Text strong>片段 {match.id}</Text>
                <Tag color={match.similarity > 0.7 ? 'red' : 'orange'}>
                  {(match.similarity * 100).toFixed(1)}%
                </Tag>
                <Text type="secondary" ellipsis style={{ maxWidth: 300 }}>
                  {match.sourceTitle}
                </Text>
              </Space>
            }
            key={match.id}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text type="secondary">重复内容:</Text>
                <Paragraph
                  style={{
                    background: '#fff2f0',
                    padding: 12,
                    borderRadius: 4,
                    marginTop: 8,
                  }}
                >
                  {match.text}
                </Paragraph>
              </div>
              <div>
                <Text type="secondary">来源:</Text>
                <Paragraph>
                  {match.sourceTitle}
                  {match.sourceUrl && (
                    <a
                      href={match.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ marginLeft: 8 }}
                    >
                      <LinkOutlined /> 查看原文
                    </a>
                  )}
                </Paragraph>
              </div>
            </Space>
          </Panel>
        ))}
      </Collapse>
    )
  }

  // Tab配置
  const tabItems: TabsProps['items'] = [
    {
      key: 'overview',
      label: '概览',
      children: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 总体相似度 */}
          <Card>
            <Row gutter={24} align="middle">
              <Col span={8}>
                <Progress
                  type="circle"
                  percent={data.overallSimilarity}
                  strokeColor={similarityLevel.color}
                  format={(percent) => (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                        {percent?.toFixed(1)}%
                      </div>
                      <div style={{ fontSize: 12 }}>总体相似度</div>
                    </div>
                  )}
                />
              </Col>
              <Col span={16}>
                <Space direction="vertical" size="middle">
                  <Alert
                    message={recommendation}
                    type={
                      similarityLevel.level === 'low'
                        ? 'success'
                        : similarityLevel.level === 'medium'
                        ? 'warning'
                        : 'error'
                    }
                    showIcon
                    icon={
                      similarityLevel.level === 'low' ? (
                        <CheckCircleOutlined />
                      ) : similarityLevel.level === 'medium' ? (
                        <WarningOutlined />
                      ) : (
                        <ExclamationCircleOutlined />
                      )
                    }
                  />
                  <Space size="large">
                    <Statistic
                      title="网络资源"
                      value={data.internetSimilarity}
                      suffix="%"
                      valueStyle={{ color: '#1890ff' }}
                    />
                    <Statistic
                      title="出版物"
                      value={data.publicationsSimilarity}
                      suffix="%"
                      valueStyle={{ color: '#52c41a' }}
                    />
                    <Statistic
                      title="学生论文"
                      value={data.studentPapersSimilarity}
                      suffix="%"
                      valueStyle={{ color: '#faad14' }}
                    />
                  </Space>
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 统计信息 */}
          <Row gutter={16}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="匹配来源"
                  value={data.sources.length}
                  prefix={<FileTextOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="重复片段"
                  value={data.matches.length}
                  prefix={<WarningOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="处理时间"
                  value={data.processingTime.toFixed(2)}
                  suffix="秒"
                  prefix={<InfoCircleOutlined />}
                />
              </Card>
            </Col>
          </Row>
        </Space>
      ),
    },
    {
      key: 'text',
      label: '原文对照',
      children: (
        <Card title="重复内容高亮显示" extra={<Text type="secondary">点击高亮部分查看详情</Text>}>
          {renderHighlightedText()}
          <Divider />
          <Space>
            <Text type="secondary">图例:</Text>
            <span style={{ padding: '2px 8px', background: 'rgba(255, 77, 79, 0.3)', borderRadius: 4 }}>
              重复片段
            </span>
            <span style={{ padding: '2px 8px', background: '#ff4d4f', borderRadius: 4 }}>
              选中片段
            </span>
          </Space>
        </Card>
      ),
    },
    {
      key: 'sources',
      label: '匹配来源',
      children: (
        <Card title="相似来源列表">
          {data.sources.length > 0 ? (
            renderSourcesList()
          ) : (
            <Empty description="未发现相似来源" />
          )}
        </Card>
      ),
    },
    {
      key: 'details',
      label: '详细匹配',
      children: (
        <Card title="重复片段详情">
          {data.matches.length > 0 ? (
            renderMatchesDetail()
          ) : (
            <Empty description="未发现重复片段" />
          )}
        </Card>
      ),
    },
  ]

  if (!data.success) {
    return (
      <Alert
        message="查重失败"
        description={data.errorMessage || '未知错误'}
        type="error"
        showIcon
      />
    )
  }

  return (
    <Card
      title={
        <Space>
          <Title level={4} style={{ margin: 0 }}>
            查重报告
          </Title>
          <Badge
            count={similarityLevel.text}
            style={{
              backgroundColor: similarityLevel.color,
              fontSize: 12,
              padding: '0 8px',
            }}
          />
        </Space>
      }
      extra={
        <Space>
          {onDownload && (
            <Button icon={<DownloadOutlined />} onClick={onDownload}>
              下载报告
            </Button>
          )}
          {onShare && (
            <Button icon={<ShareAltOutlined />} onClick={onShare}>
              分享
            </Button>
          )}
        </Space>
      }
    >
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />
    </Card>
  )
}

export default PlagiarismReport
