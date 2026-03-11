/**
 * 模板预览组件
 * 展示模板详情、章节结构和AI指导
 */

import React, { useState } from 'react'
import {
  Modal,
  Card,
  Tag,
  Button,
  Descriptions,
  List,
  Typography,
  Space,
  Tabs,
  Badge,
  Statistic,
  Row,
  Col,
  Tooltip,
  Collapse,
  Divider,
  Alert,
} from 'antd'
import {
  FileTextOutlined,
  DownloadOutlined,
  StarOutlined,
  StarFilled,
  EyeOutlined,
  CheckCircleOutlined,
  RobotOutlined,
  BookOutlined,
  TagOutlined,
  InfoCircleOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import styles from './TemplatePreview.module.css'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs
const { Panel } = Collapse

interface TemplateSection {
  id: string
  title: string
  order_index: number
  required: boolean
  placeholder?: string
  description?: string
  word_count_hint?: number
  ai_guidance?: string
  example_content?: string
  fields?: any[]
}

interface TemplateFormat {
  font_family: string
  font_size: number
  line_height: number
  margins: {
    top: number
    bottom: number
    left: number
    right: number
  }
  heading_styles: Record<string, any>
  page_size: string
  column_count: number
}

interface TemplateStats {
  download_count: number
  usage_count: number
  rating: number
  rating_count: number
  view_count: number
  favorite_count: number
}

interface PaperTemplate {
  id: string
  name: string
  description: string
  type: string
  institution?: string
  author?: string
  thumbnail?: string
  preview_images: string[]
  sections: TemplateSection[]
  format: TemplateFormat
  tags: string[]
  language: string
  discipline?: string
  difficulty: string
  stats: TemplateStats
  keywords: string[]
  created_at: string
  updated_at: string
  version: string
}

interface TemplatePreviewProps {
  template: PaperTemplate | null
  visible: boolean
  onClose: () => void
  onUse: (template: PaperTemplate) => void
  onFavorite?: (templateId: string, isFavorite: boolean) => void
  isFavorite?: boolean
}

const TemplatePreview: React.FC<TemplatePreviewProps> = ({
  template,
  visible,
  onClose,
  onUse,
  onFavorite,
  isFavorite = false,
}) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [favorite, setFavorite] = useState(isFavorite)

  if (!template) return null

  const handleFavorite = () => {
    const newState = !favorite
    setFavorite(newState)
    onFavorite?.(template.id, newState)
  }

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      thesis: '学位论文',
      journal: '期刊论文',
      conference: '会议论文',
      report: '研究报告',
      proposal: '开题报告',
      review: '综述文章',
      book: '书籍章节',
    }
    return labels[type] || type
  }

  const getDifficultyLabel = (difficulty: string) => {
    const labels: Record<string, { text: string; color: string }> = {
      beginner: { text: '入门级', color: 'green' },
      intermediate: { text: '中级', color: 'blue' },
      advanced: { text: '高级', color: 'red' },
    }
    return labels[difficulty] || { text: difficulty, color: 'default' }
  }

  const getRequiredSections = () =>
    template.sections.filter((s) => s.required)

  const getOptionalSections = () =>
    template.sections.filter((s) => !s.required)

  const getTotalWordHint = () => {
    return template.sections.reduce(
      (sum, s) => sum + (s.word_count_hint || 0),
      0
    )
  }

  const getAISupportedSections = () => {
    return template.sections.filter((s) => s.ai_guidance)
  }

  return (
    <Modal
      title={null}
      open={visible}
      onCancel={onClose}
      width={900}
      footer={
        <Space>
          <Button onClick={onClose}>关闭</Button>
          <Button
            icon={favorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
            onClick={handleFavorite}
          >
            {favorite ? '已收藏' : '收藏'}
          </Button>
          <Button type="primary" icon={<DownloadOutlined />} onClick={() => onUse(template)}>
            使用模板
          </Button>
        </Space>
      }
      className={styles.previewModal}
    >
      {/* 头部信息 */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Space wrap>
              <Tag color="blue">{getTypeLabel(template.type)}</Tag>
              {template.institution && <Tag color="purple">{template.institution}</Tag>}
              <Tag color={getDifficultyLabel(template.difficulty).color}>
                {getDifficultyLabel(template.difficulty).text}
              </Tag>
              {template.language === 'en' ? (
                <Tag>英文</Tag>
              ) : (
                <Tag>中文</Tag>
              )}
            </Space>
            <Title level={4} className={styles.title}>
              {template.name}
            </Title>
            <Paragraph type="secondary" className={styles.description}>
              {template.description}
            </Paragraph>
            <Space wrap>
              {template.tags.map((tag) => (
                <Tag key={tag} icon={<TagOutlined />} size="small">
                  {tag}
                </Tag>
              ))}
            </Space>
          </Space>
        </div>
        <div className={styles.headerStats}>
          <Row gutter={16}>
            <Col span={12}>
              <Statistic
                title="评分"
                value={template.stats.rating}
                precision={1}
                prefix={<StarFilled style={{ color: '#faad14' }} />}
                suffix={`/${template.stats.rating_count}人`}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="下载"
                value={template.stats.download_count}
                prefix={<DownloadOutlined />}
              />
            </Col>
          </Row>
        </div>
      </div>

      <Divider />

      {/* 标签页内容 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="概览" key="overview">
          <Row gutter={24}>
            <Col span={16}>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                {/* 章节结构 */}
                <Card title="章节结构" size="small">
                  <Alert
                    message={`共 ${template.sections.length} 个章节，其中 ${getRequiredSections().length} 个为必需章节`}
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  <List
                    size="small"
                    dataSource={getRequiredSections()}
                    renderItem={(section, index) => (
                      <List.Item>
                        <Space>
                          <Badge count={index + 1} style={{ backgroundColor: '#1890ff' }} />
                          <Text strong>{section.title}</Text>
                          {section.word_count_hint && (
                            <Tag size="small" color="blue">
                              约{section.word_count_hint}字
                            </Tag>
                          )}
                          {section.ai_guidance && (
                            <Tooltip title="支持AI辅助写作">
                              <RobotOutlined style={{ color: '#52c41a' }} />
                            </Tooltip>
                          )}
                        </Space>
                      </List.Item>
                    )}
                  />
                  {getOptionalSections().length > 0 && (
                    <>
                      <Divider style={{ margin: '12px 0' }} />
                      <Text type="secondary">可选章节：</Text>
                      <Space wrap style={{ marginTop: 8 }}>
                        {getOptionalSections().map((section) => (
                          <Tag key={section.id}>{section.title}</Tag>
                        ))}
                      </Space>
                    </>
                  )}
                </Card>

                {/* AI支持 */}
                {getAISupportedSections().length > 0 && (
                  <Card
                    title={
                      <Space>
                        <RobotOutlined style={{ color: '#52c41a' }} />
                        <span>AI写作支持</span>
                      </Space>
                    }
                    size="small"
                  >
                    <Alert
                      message="本模板支持AI辅助写作"
                      description={`${getAISupportedSections().length} 个章节提供AI写作指导和示例内容`}
                      type="success"
                      showIcon
                      style={{ marginBottom: 12 }}
                    />
                    <Space wrap>
                      {getAISupportedSections().map((section) => (
                        <Tag key={section.id} color="green">
                          {section.title}
                        </Tag>
                      ))}
                    </Space>
                  </Card>
                )}
              </Space>
            </Col>
            <Col span={8}>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {/* 基本信息 */}
                <Card title="基本信息" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="版本">{template.version}</Descriptions.Item>
                    <Descriptions.Item label="作者">{template.author || '未知'}</Descriptions.Item>
                    <Descriptions.Item label="学科">{template.discipline || '通用'}</Descriptions.Item>
                    <Descriptions.Item label="预计字数">
                      {getTotalWordHint() > 0 ? `${getTotalWordHint()} 字` : '未指定'}
                    </Descriptions.Item>
                    <Descriptions.Item label="更新时间">
                      {new Date(template.updated_at).toLocaleDateString()}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>

                {/* 格式设置 */}
                <Card title="格式设置" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="字体">{template.format.font_family}</Descriptions.Item>
                    <Descriptions.Item label="字号">{template.format.font_size}pt</Descriptions.Item>
                    <Descriptions.Item label="行距">{template.format.line_height}</Descriptions.Item>
                    <Descriptions.Item label="页边距">
                      上{template.format.margins.top}cm / 下{template.format.margins.bottom}cm / 左
                      {template.format.margins.left}cm / 右{template.format.margins.right}cm
                    </Descriptions.Item>
                    <Descriptions.Item label="页面">{template.format.page_size}</Descriptions.Item>
                  </Descriptions>
                </Card>
              </Space>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="章节详情" key="sections">
          <Collapse accordion>
            {template.sections.map((section) => (
              <Panel
                header={
                  <Space>
                    <Text strong>{section.title}</Text>
                    {section.required ? (
                      <Tag color="red" size="small">
                        必需
                      </Tag>
                    ) : (
                      <Tag size="small">可选</Tag>
                    )}
                    {section.word_count_hint && (
                      <Tag color="blue" size="small">
                        {section.word_count_hint}字
                      </Tag>
                    )}
                    {section.ai_guidance && (
                      <Tooltip title="支持AI辅助">
                        <RobotOutlined style={{ color: '#52c41a' }} />
                      </Tooltip>
                    )}
                  </Space>
                }
                key={section.id}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  {section.description && (
                    <div>
                      <Text type="secondary">描述：</Text>
                      <Text>{section.description}</Text>
                    </div>
                  )}

                  {section.placeholder && (
                    <div>
                      <Text type="secondary">占位符：</Text>
                      <Text type="secondary" italic>
                        {section.placeholder}
                      </Text>
                    </div>
                  )}

                  {section.ai_guidance && (
                    <Alert
                      message="AI写作指导"
                      description={section.ai_guidance}
                      type="info"
                      showIcon
                      icon={<BulbOutlined />}
                    />
                  )}

                  {section.example_content && (
                    <div className={styles.exampleContent}>
                      <Text type="secondary">示例内容：</Text>
                      <div className={styles.exampleBox}>
                        <Text>{section.example_content}</Text>
                      </div>
                    </div>
                  )}
                </Space>
              </Panel>
            ))}
          </Collapse>
        </TabPane>

        <TabPane tab="使用统计" key="stats">
          <Row gutter={24}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="总下载量"
                  value={template.stats.download_count}
                  prefix={<DownloadOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="实际使用"
                  value={template.stats.usage_count}
                  prefix={<CheckCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="浏览次数"
                  value={template.stats.view_count}
                  prefix={<EyeOutlined />}
                />
              </Card>
            </Col>
          </Row>
          <Card style={{ marginTop: 16 }} title="评分详情">
            <Row align="middle">
              <Col span={8} style={{ textAlign: 'center' }}>
                <div className={styles.ratingBig}>{template.stats.rating}</div>
                <Rate
                  disabled
                  defaultValue={Math.round(template.stats.rating)}
                  style={{ fontSize: 24 }}
                />
                <div className={styles.ratingCount}>
                  共 {template.stats.rating_count} 人评分
                </div>
              </Col>
              <Col span={16}>{/* 评分分布可以在这里添加 */}</Col>
            </Row>
          </Card>
        </TabPane>
      </Tabs>
    </Modal>
  )
}

// 简化版Rate组件用于显示
const Rate: React.FC<any> = ({ value, disabled, style }) => {
  return (
    <span style={style}>
      {[1, 2, 3, 4, 5].map((star) => (
        <StarFilled
          key={star}
          style={{
            color: star <= value ? '#faad14' : '#d9d9d9',
            marginRight: 4,
          }}
        />
      ))}
    </span>
  )
}

export default TemplatePreview
