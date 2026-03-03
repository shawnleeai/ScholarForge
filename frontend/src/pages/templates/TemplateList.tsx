/**
 * 模板管理页面
 */

import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Input,
  Select,
  Tabs,
  Typography,
  Space,
  Tag,
  Button,
  Rate,
  Empty,
  Spin,
  message,
  Breadcrumb,
  Modal,
} from 'antd'
import {
  SearchOutlined,
  DownloadOutlined,
  StarOutlined,
  FileTextOutlined,
  BookOutlined,
  TeamOutlined,
  LineChartOutlined,
  HomeOutlined,
} from '@ant-design/icons'

import { templateService, type PaperTemplate } from '@/services/templateService'
import styles from './Templates.module.css'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

const TemplateList: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [templates, setTemplates] = useState<PaperTemplate[]>([])
  const [keyword, setKeyword] = useState('')
  const [typeFilter, setTypeFilter] = useState<string>()
  const [selectedTemplate, setSelectedTemplate] = useState<PaperTemplate | null>(null)
  const [previewVisible, setPreviewVisible] = useState(false)
  const [creating, setCreating] = useState(false)

  // 加载模板
  const loadTemplates = useCallback(async () => {
    setLoading(true)
    try {
      const response = await templateService.getTemplates({
        type: typeFilter,
        keyword,
      })
      setTemplates(response.data)
    } catch (error) {
      console.error('Failed to load templates:', error)
    } finally {
      setLoading(false)
    }
  }, [typeFilter, keyword])

  useEffect(() => {
    loadTemplates()
  }, [loadTemplates])

  // 使用模板创建论文
  const handleUseTemplate = async (template: PaperTemplate) => {
    setSelectedTemplate(template)
    setPreviewVisible(true)
  }

  const handleCreatePaper = async (title: string) => {
    if (!selectedTemplate) return
    setCreating(true)
    try {
      const response = await templateService.createPaperFromTemplate(selectedTemplate.id, { title })
      message.success('论文创建成功')
      setPreviewVisible(false)
      navigate(`/papers/${response.data.paperId}`)
    } catch (error) {
      message.error('创建失败')
    } finally {
      setCreating(false)
    }
  }

  // 获取类型图标
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'thesis': return <BookOutlined />
      case 'journal': return <FileTextOutlined />
      case 'conference': return <TeamOutlined />
      case 'report': return <LineChartOutlined />
      default: return <FileTextOutlined />
    }
  }

  // 获取类型名称
  const getTypeName = (type: string) => {
    switch (type) {
      case 'thesis': return '学位论文'
      case 'journal': return '期刊论文'
      case 'conference': return '会议论文'
      case 'report': return '报告'
      default: return '其他'
    }
  }

  const tabItems = [
    {
      key: 'all',
      label: '全部模板',
    },
    {
      key: 'thesis',
      label: '学位论文',
    },
    {
      key: 'journal',
      label: '期刊论文',
    },
    {
      key: 'conference',
      label: '会议论文',
    },
  ]

  return (
    <div className={styles.templateList}>
      {/* 面包屑 */}
      <Breadcrumb
        items={[
          { href: '/dashboard', title: <><HomeOutlined /> 首页</> },
          { title: '模板中心' },
        ]}
        style={{ marginBottom: 16 }}
      />

      {/* 页面标题 */}
      <div className={styles.pageHeader}>
        <Title level={3}>模板中心</Title>
        <Text type="secondary">
          选择合适的模板快速开始您的论文写作
        </Text>
      </div>

      {/* 搜索和筛选 */}
      <Card className={styles.filterCard}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Input
              placeholder="搜索模板..."
              prefix={<SearchOutlined />}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              allowClear
              size="large"
            />
          </Col>
          <Col>
            <Select
              placeholder="模板类型"
              value={typeFilter}
              onChange={setTypeFilter}
              allowClear
              style={{ width: 150 }}
              size="large"
            >
              <Option value="thesis">学位论文</Option>
              <Option value="journal">期刊论文</Option>
              <Option value="conference">会议论文</Option>
              <Option value="report">报告</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 分类标签 */}
      <Tabs
        items={tabItems}
        onChange={(key) => setTypeFilter(key === 'all' ? undefined : key)}
        className={styles.tabs}
      />

      {/* 模板列表 */}
      {loading ? (
        <div className={styles.loading}>
          <Spin size="large" />
        </div>
      ) : templates.length === 0 ? (
        <Empty description="没有找到匹配的模板" />
      ) : (
        <Row gutter={[16, 16]}>
          {templates.map((template) => (
            <Col key={template.id} xs={24} sm={12} lg={8} xl={6}>
              <TemplateCard
                template={template}
                onUse={() => handleUseTemplate(template)}
              />
            </Col>
          ))}
        </Row>
      )}

      {/* 模板预览弹窗 */}
      <Modal
        title={`使用模板: ${selectedTemplate?.name || ''}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={600}
      >
        {selectedTemplate && (
          <TemplatePreview
            template={selectedTemplate}
            onCreate={handleCreatePaper}
            loading={creating}
          />
        )}
      </Modal>
    </div>
  )
}

// 模板卡片组件
interface TemplateCardProps {
  template: PaperTemplate
  onUse: () => void
}

const TemplateCard: React.FC<TemplateCardProps> = ({ template, onUse }) => {
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'thesis': return 'blue'
      case 'journal': return 'green'
      case 'conference': return 'orange'
      case 'report': return 'purple'
      default: return 'default'
    }
  }

  return (
    <Card
      className={styles.templateCard}
      hoverable
      cover={
        <div className={styles.cardCover}>
          <FileTextOutlined className={styles.coverIcon} />
        </div>
      }
      onClick={onUse}
    >
      <div className={styles.cardContent}>
        <div className={styles.cardHeader}>
          <Text strong ellipsis className={styles.cardTitle}>
            {template.name}
          </Text>
          <Tag color={getTypeColor(template.type)} icon={getTypeIcon(template.type)}>
            {getTypeName(template.type)}
          </Tag>
        </div>

        <Paragraph
          type="secondary"
          ellipsis={{ rows: 2 }}
          className={styles.cardDesc}
        >
          {template.description}
        </Paragraph>

        <div className={styles.cardTags}>
          {template.tags.slice(0, 3).map((tag) => (
            <Tag key={tag} className={styles.tag}>
              {tag}
            </Tag>
          ))}
        </div>

        <div className={styles.cardFooter}>
          <Space>
            <Rate disabled defaultValue={template.rating} allowHalf className={styles.rate} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {template.rating}
            </Text>
          </Space>
          <Space>
            <DownloadOutlined />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {template.downloadCount}
            </Text>
          </Space>
        </div>
      </div>
    </Card>
  )
}

// 模板预览组件
interface TemplatePreviewProps {
  template: PaperTemplate
  onCreate: (title: string) => void
  loading: boolean
}

const TemplatePreview: React.FC<TemplatePreviewProps> = ({ template, onCreate, loading }) => {
  const [title, setTitle] = useState('')

  return (
    <div className={styles.preview}>
      <div className={styles.previewInfo}>
        <Text strong>{template.name}</Text>
        <Paragraph type="secondary">{template.description}</Paragraph>
      </div>

      <div className={styles.previewSections}>
        <Text type="secondary">模板结构:</Text>
        <ul className={styles.sectionList}>
          {template.sections.map((section) => (
            <li key={section.id}>
              <Space>
                {section.required && <Tag color="red">必填</Tag>}
                <span>{section.title}</span>
              </Space>
            </li>
          ))}
        </ul>
      </div>

      <div className={styles.previewFormat}>
        <Text type="secondary">格式设置:</Text>
        <Space wrap style={{ marginTop: 8 }}>
          <Tag>字体: {template.format.fontFamily}</Tag>
          <Tag>字号: {template.format.fontSize}pt</Tag>
          <Tag>行距: {template.format.lineHeight}</Tag>
        </Space>
      </div>

      <div className={styles.previewActions}>
        <Input
          placeholder="输入论文标题"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={{ marginBottom: 12 }}
        />
        <Button
          type="primary"
          block
          onClick={() => onCreate(title || '未命名论文')}
          loading={loading}
        >
          使用此模板创建论文
        </Button>
      </div>
    </div>
  )
}

export default TemplateList
