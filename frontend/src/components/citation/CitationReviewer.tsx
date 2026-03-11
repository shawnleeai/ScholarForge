/**
 * AI智能引用审查与自动排版组件
 * 引用格式检查、自动排版、引用完整性验证
 */

import React, { useState } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Select,
  List,
  Tag,
  Alert,
  Progress,
  Collapse,
  Badge,
  Tooltip,
  Input,
  Statistic,
  Row,
  Col,
  Divider,
  message,
  Empty
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  FormatPainterOutlined,
  FileTextOutlined,
  ExportOutlined,
  EditOutlined,
  ReloadOutlined,
  CheckOutlined,
  BookOutlined,
  LinkOutlined,
  CalendarOutlined,
  UserOutlined
} from '@ant-design/icons'
import {
  citationReviewService,
  type Citation,
  type CitationStyle,
  type CitationReview,
  type CitationError
} from '@/services/citationReviewService'
import styles from './CitationReviewer.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Panel } = Collapse
const { Option } = Select

const STYLE_OPTIONS: { value: CitationStyle; label: string }[] = [
  { value: 'gb7714', label: 'GB7714 (国标)' },
  { value: 'apa', label: 'APA' },
  { value: 'mla', label: 'MLA' },
  { value: 'chicago', label: 'Chicago' },
  { value: 'ieee', label: 'IEEE' }
]

const CitationReviewer: React.FC = () => {
  const [citationsText, setCitationsText] = useState('')
  const [selectedStyle, setSelectedStyle] = useState<CitationStyle>('gb7714')
  const [citations, setCitations] = useState<Citation[]>([])
  const [review, setReview] = useState<CitationReview | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeKey, setActiveKey] = useState<string[]>(['input'])

  // 解析引用
  const handleReview = () => {
    if (!citationsText.trim()) {
      message.warning('请输入参考文献内容')
      return
    }

    setLoading(true)

    // 按行分割引用
    const lines = citationsText.split('\n').filter(line => line.trim())

    // 解析每条引用
    const parsedCitations = lines.map((line, index) =>
      citationReviewService.parseCitation(line, index + 1)
    )

    // 审查引用
    const reviewResult = citationReviewService.reviewCitations(parsedCitations, selectedStyle)

    setCitations(parsedCitations)
    setReview(reviewResult)
    setLoading(false)
    setActiveKey(['results'])

    message.success('引用审查完成')
  }

  // 格式化单条引用
  const handleFormat = (citation: Citation, index: number) => {
    const formatted = citationReviewService.formatCitation(citation, selectedStyle, index + 1)
    const updated = citations.map(c =>
      c.id === citation.id ? { ...c, formattedText: formatted } : c
    )
    setCitations(updated)
    message.success('已格式化')
  }

  // 自动修复
  const handleAutoFix = (citation: Citation) => {
    const fixed = citationReviewService.autoFixCitation(citation, selectedStyle)
    const updated = citations.map(c =>
      c.id === citation.id ? fixed : c
    )
    setCitations(updated)

    // 重新审查
    const reviewResult = citationReviewService.reviewCitations(updated, selectedStyle)
    setReview(reviewResult)

    message.success('已尝试自动修复')
  }

  // 导出格式化后的引用
  const handleExport = () => {
    const formatted = citationReviewService.exportFormattedCitations(citations, selectedStyle)
    navigator.clipboard.writeText(formatted)
    message.success('格式化后的引用已复制到剪贴板')
  }

  // 获取错误图标
  const getErrorIcon = (severity: CitationError['severity']) => {
    switch (severity) {
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />
      default:
        return <CheckCircleOutlined style={{ color: '#1890ff' }} />
    }
  }

  // 渲染审查结果
  const renderReviewResults = () => {
    if (!review) return null

    return (
      <div className={styles.reviewResults}>
        {/* 总体统计 */}
        <Card className={styles.statsCard}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="总引用数"
                value={review.totalCitations}
                prefix={<BookOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="格式正确"
                value={review.validCitations}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="存在问题"
                value={review.invalidCitations}
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<CloseCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="完整性"
                value={review.completeness}
                suffix="%"
                prefix={<CheckOutlined />}
              />
            </Col>
          </Row>

          <Divider />

          <div className={styles.progressSection}>
            <Text type="secondary">格式一致性</Text>
            <Progress
              percent={review.styleConsistency}
              status={review.styleConsistency > 80 ? 'success' : review.styleConsistency > 60 ? 'normal' : 'exception'}
            />
          </div>
        </Card>

        {/* 改进建议 */}
        {review.suggestions.length > 0 && (
          <Alert
            message="改进建议"
            description={
              <ul>
                {review.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            }
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}

        {/* 引用列表 */}
        <List
          className={styles.citationsList}
          header={
            <div className={styles.listHeader}>
              <Space>
                <Text strong>引用详情</Text>
                <Tag color="blue">{STYLE_OPTIONS.find(s => s.value === selectedStyle)?.label}</Tag>
              </Space>
              <Button icon={<ExportOutlined />} onClick={handleExport} size="small">
                导出
              </Button>
            </div>
          }
          dataSource={citations}
          renderItem={(citation, index) => (
            <List.Item
              className={styles.citationItem}
              actions={[
                <Tooltip title="格式化">
                  <Button
                    icon={<FormatPainterOutlined />}
                    onClick={() => handleFormat(citation, index)}
                    size="small"
                  />
                </Tooltip>,
                <Tooltip title="自动修复">
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={() => handleAutoFix(citation)}
                    size="small"
                  />
                </Tooltip>
              ]}
            >
              <div className={styles.citationContent}>
                <div className={styles.citationHeader}>
                  <Badge
                    count={index + 1}
                    style={{
                      backgroundColor: citation.isValid ? '#52c41a' : '#ff4d4f'
                    }}
                  />
                  <Tag color={citation.isValid ? 'success' : 'error'}>
                    {citation.isValid ? '格式正确' : '需要修改'}
                  </Tag>
                  <Tag>{citation.type}</Tag>
                </div>

                <Paragraph className={styles.rawText}>{citation.rawText}</Paragraph>

                {citation.formattedText && (
                  <div className={styles.formattedText}>
                    <Text type="secondary" style={{ fontSize: 12 }}>格式化后：</Text>
                    <Paragraph copyable>{citation.formattedText}</Paragraph>
                  </div>
                )}

                {/* 错误列表 */}
                {citation.errors.length > 0 && (
                  <Collapse ghost size="small">
                    <Panel
                      header={`发现问题 (${citation.errors.length})`}
                      key="errors"
                    >
                      <List
                        dataSource={citation.errors}
                        renderItem={error => (
                          <List.Item>
                            <Space>
                              {getErrorIcon(error.severity)}
                              <div>
                                <Text>{error.message}</Text>
                                <br />
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  建议：{error.suggestion}
                                </Text>
                              </div>
                            </Space>
                          </List.Item>
                        )}
                      />
                    </Panel>
                  </Collapse>
                )}
              </div>
            </List.Item>
          )}
        />
      </div>
    )
  }

  return (
    <Card
      className={styles.citationReviewer}
      title={
        <Space>
          <FormatPainterOutlined />
          <span>AI智能引用审查</span>
        </Space>
      }
    >
      <Collapse activeKey={activeKey} onChange={setActiveKey}>
        <Panel header="输入参考文献" key="input">
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Alert
              message="粘贴您的参考文献列表，AI将自动检查格式并提供修改建议"
              type="info"
              showIcon
            />

            <div>
              <Text type="secondary">选择引用格式</Text>
              <Select
                value={selectedStyle}
                onChange={setSelectedStyle}
                style={{ width: 200, marginLeft: 8 }}
              >
                {STYLE_OPTIONS.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </div>

            <TextArea
              value={citationsText}
              onChange={e => setCitationsText(e.target.value)}
              placeholder={`示例格式：&#xd;&#xd;[1] 张三, 李四. 人工智能研究[J]. 计算机学报, 2023, 45(3): 120-135.&#xd;[2] Wang W, Chen L. Deep Learning Methods[M]. Springer, 2022.&#xd;`}
              rows={10}
            />

            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={handleReview}
              loading={loading}
              block
            >
              开始审查
            </Button>
          </Space>
        </Panel>

        <Panel header="审查结果" key="results">
          {review ? renderReviewResults() : (
            <Empty description="请先输入参考文献并点击审查" />
          )}
        </Panel>

        <Panel header="格式说明" key="help">
          <Collapse ghost>
            <Panel header="GB7714 格式" key="gb7714">
              <ul>
                <li>期刊：[序号] 作者. 标题[J]. 刊名, 年, 卷(期): 起止页码.</li>
                <li>专著：[序号] 作者. 书名[M]. 出版地: 出版者, 年.</li>
                <li>论文集：[序号] 作者. 标题[C]//编者. 论文集名. 出版地: 出版者, 年: 起止页码.</li>
                <li>学位论文：[序号] 作者. 标题[D]. 保存地: 保存单位, 年.</li>
              </ul>
            </Panel>
            <Panel header="APA 格式" key="apa">
              <ul>
                <li>Author, A. A. (Year). Title of article. <i>Title of Journal</i>, <i>volume</i>(issue), pages.</li>
                <li>Author, A. A. (Year). <i>Title of work</i>. Publisher.</li>
              </ul>
            </Panel>
            <Panel header="MLA 格式" key="mla">
              <ul>
                <li>Author. &quot;Title of Article.&quot; <i>Title of Journal</i>, vol. #, no. #, Year, pp. ##-##.</li>
              </ul>
            </Panel>
          </Collapse>
        </Panel>
      </Collapse>
    </Card>
  )
}

export default CitationReviewer
