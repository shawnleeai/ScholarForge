/**
 * 格式检测与排版页面
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card, Row, Col, Button, Select, Tabs, List, Tag, Space, Typography,
  Alert, Empty, Progress, Steps, Divider, Tooltip, Badge, message, Modal,
  Descriptions, Switch, InputNumber, Form, Collapse, Table, Skeleton
} from 'antd'
import type { TabsProps } from 'antd'
import {
  FileTextOutlined, CheckCircleOutlined, WarningOutlined,
  FormatPainterOutlined, EyeOutlined, SettingOutlined,
  DownloadOutlined, ReloadOutlined, FileProtectOutlined,
  AlignLeftOutlined, FontSizeOutlined, ColumnWidthOutlined,
  ArrowRightOutlined, InfoCircleOutlined, PlayCircleOutlined
} from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import { formatService } from '@/services/formatService'
import type { FormatTemplate, FormatIssue, FormatCheckResult } from '@/types/format'
import styles from './FormatCheck.module.css'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

const SEVERITY_CONFIG: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
  error: { color: 'red', icon: <WarningOutlined />, text: '错误' },
  warning: { color: 'orange', icon: <InfoCircleOutlined />, text: '警告' },
  info: { color: 'blue', icon: <InfoCircleOutlined />, text: '提示' },
}

const ISSUE_TYPE_NAMES: Record<string, string> = {
  title_length: '标题长度',
  abstract_length: '摘要长度',
  keywords_count: '关键词数量',
  no_sections: '章节结构',
  references_count: '参考文献数量',
  font_size: '字体大小',
  line_spacing: '行距',
  margin: '页边距',
  paragraph_indent: '段落缩进',
  heading_format: '标题格式',
  page_number: '页码',
  header_footer: '页眉页脚',
}

const FormatCheckPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>()

  const [activeTab, setActiveTab] = useState('check')
  const [templates, setTemplates] = useState<FormatTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [checkResult, setCheckResult] = useState<FormatCheckResult | null>(null)
  const [checking, setChecking] = useState(false)
  const [formatting, setFormatting] = useState(false)
  const [previewVisible, setPreviewVisible] = useState(false)
  const [formatProgress, setFormatProgress] = useState(0)

  // 加载模板列表
  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      const res = await formatService.getTemplates()
      setTemplates(res.data || [])
      if (res.data?.length > 0) {
        setSelectedTemplate(res.data[0].id)
      }
    } catch (error) {
      console.error('获取模板失败', error)
    }
  }

  // 执行格式检查
  const handleCheck = async () => {
    if (!paperId) {
      message.warning('请先选择论文')
      return
    }

    setChecking(true)
    try {
      const res = await formatService.checkFormat(paperId, selectedTemplate)
      setCheckResult(res.data)
      message.success('格式检查完成')
    } catch (error) {
      message.error('格式检查失败')
    } finally {
      setChecking(false)
    }
  }

  // 执行自动排版
  const handleFormat = async () => {
    if (!paperId) {
      message.warning('请先选择论文')
      return
    }

    Modal.confirm({
      title: '确认自动排版',
      content: '自动排版将修改论文格式，建议先备份当前版本。是否继续？',
      onOk: async () => {
        setFormatting(true)
        setFormatProgress(0)

        // 模拟进度
        const progressTimer = setInterval(() => {
          setFormatProgress(p => Math.min(p + 10, 90))
        }, 300)

        try {
          await formatService.autoFormat(paperId, selectedTemplate)
          clearInterval(progressTimer)
          setFormatProgress(100)
          message.success('自动排版完成')
          // 重新检查
          handleCheck()
        } catch (error) {
          clearInterval(progressTimer)
          message.error('自动排版失败')
        } finally {
          setFormatting(false)
        }
      }
    })
  }

  // 统计问题数量
  const getIssueStats = () => {
    if (!checkResult?.issues) return { error: 0, warning: 0, info: 0 }
    return {
      error: checkResult.issues.filter(i => i.severity === 'error').length,
      warning: checkResult.issues.filter(i => i.severity === 'warning').length,
      info: checkResult.issues.filter(i => i.severity === 'info').length,
    }
  }

  const issueStats = getIssueStats()

  // 问题列表列定义
  const issueColumns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string) => ISSUE_TYPE_NAMES[type] || type
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => {
        const config = SEVERITY_CONFIG[severity]
        return (
          <Tag icon={config.icon} color={config.color}>
            {config.text}
          </Tag>
        )
      }
    },
    {
      title: '问题描述',
      dataIndex: 'message',
      key: 'message',
      render: (text: string, record: FormatIssue) => (
        <Space direction="vertical" size={0}>
          <Text>{text}</Text>
          {record.position && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              位置: {record.position}
            </Text>
          )}
        </Space>
      )
    },
    {
      title: '建议',
      dataIndex: 'suggestion',
      key: 'suggestion',
      width: 200,
      render: (text: string) => text || '-'
    }
  ]

  // 检查步骤
  const checkSteps = [
    { title: '页面设置', icon: <ColumnWidthOutlined /> },
    { title: '字体格式', icon: <FontSizeOutlined /> },
    { title: '段落样式', icon: <AlignLeftOutlined /> },
    { title: '标题层级', icon: <FileTextOutlined /> },
    { title: '参考文献', icon: <FileProtectOutlined /> },
  ]

  const tabItems: TabsProps['items'] = [
    {
      key: 'check',
      label: '格式检查',
      children: (
        <div>
          {/* 模板选择和操作区 */}
          <Card className={styles.actionCard}>
            <Row gutter={16} align="middle">
              <Col flex="auto">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>选择检测模板</Text>
                  <Select
                    style={{ width: 300 }}
                    placeholder="选择格式模板"
                    value={selectedTemplate}
                    onChange={setSelectedTemplate}
                    options={templates.map(t => ({
                      value: t.id,
                      label: t.name,
                      description: t.description
                    }))}
                    optionRender={(option) => (
                      <div>
                        <div>{option.label}</div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {option.data.description}
                        </Text>
                      </div>
                    )}
                  />
                </Space>
              </Col>
              <Col>
                <Space>
                  <Button
                    icon={<EyeOutlined />}
                    onClick={() => setPreviewVisible(true)}
                    disabled={!checkResult}
                  >
                    预览结果
                  </Button>
                  <Button
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    loading={checking}
                    onClick={handleCheck}
                  >
                    开始检查
                  </Button>
                </Space>
              </Col>
            </Row>
          </Card>

          {/* 检查进度 */}
          {checking && (
            <Card className={styles.progressCard}>
              <Steps
                size="small"
                current={2}
                items={checkSteps.map(s => ({ title: s.title, icon: s.icon }))}
              />
              <Progress
                percent={60}
                status="active"
                strokeColor={{ from: '#108ee9', to: '#87d068' }}
                style={{ marginTop: 16 }}
              />
            </Card>
          )}

          {/* 检查结果 */}
          {checkResult ? (
            <>
              {/* 统计卡片 */}
              <Row gutter={16} className={styles.statsRow}>
                <Col span={8}>
                  <Card>
                    <div className={styles.statItem}>
                      <Text type="danger" strong style={{ fontSize: 24 }}>
                        {issueStats.error}
                      </Text>
                      <div><Tag color="red">错误</Tag></div>
                    </div>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card>
                    <div className={styles.statItem}>
                      <Text style={{ color: '#faad14', fontSize: 24, fontWeight: 'bold' }}>
                        {issueStats.warning}
                      </Text>
                      <div><Tag color="orange">警告</Tag></div>
                    </div>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card>
                    <div className={styles.statItem}>
                      <Text type="primary" strong style={{ fontSize: 24 }}>
                        {issueStats.info}
                      </Text>
                      <div><Tag color="blue">提示</Tag></div>
                    </div>
                  </Card>
                </Col>
              </Row>

              {/* 格式评分 */}
              <Card className={styles.scoreCard}>
                <Row gutter={24} align="middle">
                  <Col span={6}>
                    <div className={styles.scoreCircle}>
                      <Progress
                        type="circle"
                        percent={checkResult.score || 0}
                        strokeColor={
                          (checkResult.score || 0) >= 90 ? '#52c41a' :
                          (checkResult.score || 0) >= 70 ? '#faad14' : '#ff4d4f'
                        }
                        size={100}
                        format={(p) => (
                          <div>
                            <div style={{ fontSize: 28, fontWeight: 'bold' }}>{p}</div>
                            <div style={{ fontSize: 12 }}>格式得分</div>
                          </div>
                        )}
                      />
                    </div>
                  </Col>
                  <Col span={18}>
                    <Descriptions column={2} size="small">
                      <Descriptions.Item label="检测模板">
                        {checkResult.templateName || '默认模板'}
                      </Descriptions.Item>
                      <Descriptions.Item label="检测时间">
                        {new Date(checkResult.checkedAt).toLocaleString()}
                      </Descriptions.Item>
                      <Descriptions.Item label="论文标题">
                        {checkResult.paperTitle || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="问题总数">
                        {checkResult.issues?.length || 0} 个
                      </Descriptions.Item>
                    </Descriptions>
                  </Col>
                </Row>
              </Card>

              {/* 问题列表 */}
              <Card
                title="格式问题详情"
                className={styles.issuesCard}
                extra={
                  <Button
                    type="primary"
                    icon={<FormatPainterOutlined />}
                    loading={formatting}
                    onClick={handleFormat}
                    disabled={issueStats.error === 0 && issueStats.warning === 0}
                  >
                    一键修复
                  </Button>
                }
              >
                {formatting ? (
                  <div style={{ padding: 40, textAlign: 'center' }}>
                    <Progress
                      type="circle"
                      percent={formatProgress}
                      status={formatProgress === 100 ? 'success' : 'active'}
                    />
                    <p style={{ marginTop: 16 }}>正在自动排版...</p>
                  </div>
                ) : (
                  <Table
                    columns={issueColumns}
                    dataSource={checkResult.issues || []}
                    rowKey={(record, index) => `${record.type}-${index}`}
                    pagination={{ pageSize: 10 }}
                    size="small"
                    expandable={{
                      expandedRowRender: (record: FormatIssue) => (
                        <div style={{ padding: '8px 16px', background: '#fafafa' }}>
                          <Text strong>修复建议：</Text>
                          <Paragraph style={{ marginTop: 8 }}>
                            {record.suggestion || '根据模板规范进行调整'}
                          </Paragraph>
                          {record.example && (
                            <>
                              <Text strong>示例：</Text>
                              <pre className={styles.codeExample}>{record.example}</pre>
                            </>
                          )}
                        </div>
                      ),
                    }}
                  />
                )}
              </Card>
            </>
          ) : (
            <Card className={styles.emptyCard}>
              <Empty
                image={<FileTextOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />}
                description={
                  <div>
                    <p>暂无格式检查结果</p>
                    <Text type="secondary">选择模板后点击"开始检查"按钮</Text>
                  </div>
                }
              />
            </Card>
          )}
        </div>
      )
    },
    {
      key: 'templates',
      label: '模板管理',
      children: (
        <Card>
          <List
            grid={{ gutter: 16, column: 2 }}
            dataSource={templates}
            renderItem={(template) => (
              <List.Item>
                <Card
                  hoverable
                  className={selectedTemplate === template.id ? styles.selectedTemplate : ''}
                  onClick={() => setSelectedTemplate(template.id)}
                  title={template.name}
                  extra={template.isDefault && <Tag color="blue">默认</Tag>}
                >
                  <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
                    {template.description}
                  </Paragraph>
                  <Divider style={{ margin: '12px 0' }} />
                  <Space direction="vertical" size={0} style={{ width: '100%' }}>
                    <Text style={{ fontSize: 12 }}>
                      <FontSizeOutlined /> 正文字体: {template.config?.fontFamily} {template.config?.fontSize}pt
                    </Text>
                    <Text style={{ fontSize: 12 }}>
                      <AlignLeftOutlined /> 行距: {template.config?.lineSpacing}倍
                    </Text>
                    <Text style={{ fontSize: 12 }}>
                      <ColumnWidthOutlined /> 页边距: {template.config?.marginTop}mm
                    </Text>
                  </Space>
                  {selectedTemplate === template.id && (
                    <div className={styles.selectedBadge}>
                      <CheckCircleOutlined style={{ color: '#52c41a' }} />
                    </div>
                  )}
                </Card>
              </List.Item>
            )}
          />
        </Card>
      )
    },
    {
      key: 'settings',
      label: '自定义设置',
      children: (
        <Card title="格式自定义设置">
          <Form layout="vertical">
            <Row gutter={24}>
              <Col span={12}>
                <Form.Item label="正文字体">
                  <Select defaultValue="SimSun">
                    <Select.Option value="SimSun">宋体</Select.Option>
                    <Select.Option value="SimHei">黑体</Select.Option>
                    <Select.Option value="KaiTi">楷体</Select.Option>
                    <Select.Option value="FangSong">仿宋</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="正文字号">
                  <Select defaultValue={12}>
                    <Select.Option value={10.5}>五号 (10.5pt)</Select.Option>
                    <Select.Option value={12}>小四 (12pt)</Select.Option>
                    <Select.Option value={14}>四号 (14pt)</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={24}>
              <Col span={12}>
                <Form.Item label="行距">
                  <Select defaultValue={1.5}>
                    <Select.Option value={1.0}>单倍</Select.Option>
                    <Select.Option value={1.5}>1.5倍</Select.Option>
                    <Select.Option value={2.0}>双倍</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="首行缩进">
                  <InputNumber
                    defaultValue={24}
                    min={0}
                    max={48}
                    addonAfter="pt"
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={24}>
              <Col span={12}>
                <Form.Item label="上边距">
                  <InputNumber defaultValue={25.4} min={0} addonAfter="mm" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="下边距">
                  <InputNumber defaultValue={25.4} min={0} addonAfter="mm" />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={24}>
              <Col span={12}>
                <Form.Item label="左边距">
                  <InputNumber defaultValue={31.7} min={0} addonAfter="mm" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="右边距">
                  <InputNumber defaultValue={31.7} min={0} addonAfter="mm" />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item>
              <Space>
                <Button type="primary" icon={<CheckCircleOutlined />}>
                  保存设置
                </Button>
                <Button icon={<ReloadOutlined />}>
                  重置默认
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      )
    }
  ]

  return (
    <div className={styles.container}>
      <Title level={2}>
        <FormatPainterOutlined /> 格式检测与排版
      </Title>

      <Row gutter={24}>
        <Col span={24}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            type="card"
          />
        </Col>
      </Row>

      {/* 预览弹窗 */}
      <Modal
        title="格式预览"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
          >
            下载排版后文档
          </Button>
        ]}
      >
        {checkResult?.previewUrl ? (
          <iframe
            src={checkResult.previewUrl}
            style={{ width: '100%', height: 600, border: 'none' }}
          />
        ) : (
          <Empty description="暂无预览" />
        )}
      </Modal>
    </div>
  )
}

export default FormatCheckPage
