/**
 * 模板列表页面（增强版）
 * 支持搜索、筛选、推荐和AI填充
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Input,
  Button,
  List,
  Typography,
  Space,
  Tag,
  Empty,
  Spin,
  Pagination,
  Row,
  Col,
  Tooltip,
  Badge,
  message,
  BackTop,
} from 'antd'
import {
  SearchOutlined,
  StarOutlined,
  StarFilled,
  DownloadOutlined,
  EyeOutlined,
  RobotOutlined,
  AppstoreOutlined,
  BarsOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import TemplatePreview from '../../components/template/TemplatePreview'
import AITemplateFill from '../../components/template/AITemplateFill'
import TemplateCategories from '../../components/template/TemplateCategories'
import { templateService } from '../../services/templateService'
import styles from './TemplateList.module.css'

const { Title, Text, Paragraph } = Typography
const { Search } = Input

interface FilterState {
  type?: string
  institution?: string
  discipline?: string
  language?: string
  difficulty?: string
  tags: string[]
  sortBy: string
}

const TemplateList: React.FC = () => {
  const navigate = useNavigate()
  const [templates, setTemplates] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filter, setFilter] = useState<FilterState>({
    tags: [],
    sortBy: 'relevance',
  })
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 12,
    total: 0,
  })
  const [filterOptions, setFilterOptions] = useState({
    types: [],
    institutions: [],
    disciplines: [],
    languages: [],
    difficulties: [],
    tags: [],
  })

  // 模态框状态
  const [previewVisible, setPreviewVisible] = useState(false)
  const [aiFillVisible, setAiFillVisible] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null)
  const [favorites, setFavorites] = useState<string[]>([])

  // 视图模式
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  // 获取模板列表
  const fetchTemplates = useCallback(async () => {
    setLoading(true)
    try {
      const response = await templateService.getTemplates({
        keyword: searchQuery,
        type: filter.type,
        institution: filter.institution,
        page: pagination.current,
        pageSize: pagination.pageSize,
        sortBy: filter.sortBy,
      })
      setTemplates(response.data || [])
      setPagination((prev) => ({
        ...prev,
        total: response.total || 0,
      }))
    } catch (error) {
      message.error('获取模板列表失败')
    } finally {
      setLoading(false)
    }
  }, [searchQuery, filter, pagination.current, pagination.pageSize])

  // 获取筛选选项
  const fetchFilterOptions = useCallback(async () => {
    try {
      const response = await templateService.getFilterOptions()
      setFilterOptions(response.data || {
        types: [],
        institutions: [],
        disciplines: [],
        languages: [],
        difficulties: [],
        tags: [],
      })
    } catch (error) {
      console.error('获取筛选选项失败', error)
    }
  }, [])

  // 获取收藏列表
  const fetchFavorites = useCallback(async () => {
    try {
      const response = await templateService.getFavorites()
      setFavorites((response.data || []).map((t: any) => t.id))
    } catch (error) {
      console.error('获取收藏列表失败', error)
    }
  }, [])

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  useEffect(() => {
    fetchFilterOptions()
    fetchFavorites()
  }, [fetchFilterOptions, fetchFavorites])

  const handleSearch = (value: string) => {
    setSearchQuery(value)
    setPagination((prev) => ({ ...prev, current: 1 }))
  }

  const handleFilterChange = (newFilter: Partial<FilterState>) => {
    setFilter((prev) => ({ ...prev, ...newFilter }))
    setPagination((prev) => ({ ...prev, current: 1 }))
  }

  const handleResetFilter = () => {
    setFilter({ tags: [], sortBy: 'relevance' })
    setSearchQuery('')
    setPagination((prev) => ({ ...prev, current: 1 }))
  }

  const handlePageChange = (page: number, pageSize?: number) => {
    setPagination((prev) => ({
      ...prev,
      current: page,
      pageSize: pageSize || prev.pageSize,
    }))
  }

  const openPreview = (template: any) => {
    setSelectedTemplate(template)
    setPreviewVisible(true)
  }

  const closePreview = () => {
    setPreviewVisible(false)
    setSelectedTemplate(null)
  }

  const openAiFill = (template: any) => {
    setSelectedTemplate(template)
    setAiFillVisible(true)
  }

  const closeAiFill = () => {
    setAiFillVisible(false)
  }

  const handleUseTemplate = async (template: any) => {
    try {
      await templateService.useTemplate(template.id, {
        title: `使用${template.name}创建的论文`,
      })
      message.success('已开始使用模板创建论文')
      navigate(`/papers/new?template=${template.id}`)
    } catch (error) {
      message.error('使用模板失败')
    }
  }

  const handleFavorite = async (templateId: string, isFavorite: boolean) => {
    try {
      if (isFavorite) {
        await templateService.addFavorite(templateId)
        setFavorites((prev) => [...prev, templateId])
        message.success('已添加到收藏')
      } else {
        await templateService.removeFavorite(templateId)
        setFavorites((prev) => prev.filter((id) => id !== templateId))
        message.success('已取消收藏')
      }
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleAiFillComplete = (results: any[]) => {
    message.success(`成功生成 ${results.length} 个章节内容`)
    setAiFillVisible(false)
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

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      thesis: 'blue',
      journal: 'green',
      conference: 'purple',
      report: 'orange',
      proposal: 'cyan',
      review: 'magenta',
      book: 'gold',
    }
    return colors[type] || 'default'
  }

  // 网格视图卡片
  const renderGridCard = (template: any) => (
    <Card
      hoverable
      className={styles.templateCard}
      cover={
        <div className={styles.cardCover}>
          <div className={styles.coverPlaceholder}>
            <Text type="secondary">{template.name.slice(0, 2)}</Text>
          </div>
          <div className={styles.cardActions}>
            <Tooltip title="预览">
              <Button
                type="primary"
                shape="circle"
                icon={<EyeOutlined />}
                onClick={(e) => {
                  e.stopPropagation()
                  openPreview(template)
                }}
              />
            </Tooltip>
            {template.sections?.some((s: any) => s.ai_guidance) && (
              <Tooltip title="AI填充">
                <Button
                  type="primary"
                  shape="circle"
                  icon={<RobotOutlined />}
                  onClick={(e) => {
                    e.stopPropagation()
                    openAiFill(template)
                  }}
                />
              </Tooltip>
            )}
          </div>
          <div className={styles.cardBadge}>
            {favorites.includes(template.id) && (
              <StarFilled style={{ color: '#faad14', fontSize: 20 }} />
            )}
          </div>
        </div>
      }
      onClick={() => openPreview(template)}
    >
      <div className={styles.cardContent}>
        <Space wrap size="small">
          <Tag color={getTypeColor(template.type)}>{getTypeLabel(template.type)}</Tag>
          {template.institution && <Tag>{template.institution}</Tag>}
        </Space>
        <Title level={5} className={styles.cardTitle} ellipsis={{ rows: 1 }}>
          {template.name}
        </Title>
        <Paragraph type="secondary" className={styles.cardDesc} ellipsis={{ rows: 2 }}>
          {template.description}
        </Paragraph>
        <div className={styles.cardMeta}>
          <Space wrap size="small">
            <Tag icon={<StarOutlined />} color="gold">
              {template.stats?.rating || 0}
            </Tag>
            <Tag icon={<DownloadOutlined />}>
              {template.stats?.download_count || 0}
            </Tag>
          </Space>
        </div>
      </div>
    </Card>
  )

  // 列表视图行
  const renderListItem = (template: any) => (
    <List.Item
      className={styles.listItem}
      actions={[
        <Button
          type="text"
          icon={favorites.includes(template.id) ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
          onClick={() => handleFavorite(template.id, !favorites.includes(template.id))}
        >
          收藏
        </Button>,
        <Button type="primary" icon={<DownloadOutlined />} onClick={() => handleUseTemplate(template)}>
          使用
        </Button>,
      ]}
    >
      <List.Item.Meta
        title={
          <Space>
            <a onClick={() => openPreview(template)}>{template.name}</a>
            <Tag color={getTypeColor(template.type)}>{getTypeLabel(template.type)}</Tag>
            {template.sections?.some((s: any) => s.ai_guidance) && (
              <Tooltip title="支持AI辅助写作">
                <RobotOutlined style={{ color: '#52c41a' }} />
              </Tooltip>
            )}
          </Space>
        }
        description={
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text type="secondary" ellipsis>
              {template.description}
            </Text>
            <Space wrap>
              {template.institution && <Tag size="small">{template.institution}</Tag>}
              {template.tags?.slice(0, 3).map((tag: string) => (
                <Tag key={tag} size="small">
                  {tag}
                </Tag>
              ))}
            </Space>
          </Space>
        }
      />
      <div className={styles.listStats}>
        <Space>
          <Badge count={template.stats?.rating?.toFixed(1)} style={{ backgroundColor: '#faad14' }} />
          <Text type="secondary">{template.stats?.download_count} 次下载</Text>
        </Space>
      </div>
    </List.Item>
  )

  return (
    <div className={styles.container}>
      {/* 页面头部 */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <Title level={2}>论文模板库</Title>
          <Paragraph type="secondary">
            选择适合您的论文模板，支持AI智能填充，快速开始学术写作
          </Paragraph>
        </div>
        <div className={styles.headerStats}>
          <Space size="large">
            <div className={styles.statItem}>
              <Text strong className={styles.statNumber}>
                {pagination.total}
              </Text>
              <Text type="secondary">模板总数</Text>
            </div>
            <div className={styles.statItem}>
              <Text strong className={styles.statNumber}>
                {favorites.length}
              </Text>
              <Text type="secondary">我的收藏</Text>
            </div>
          </Space>
        </div>
      </div>

      {/* 搜索栏 */}
      <div className={styles.searchBar}>
        <Search
          placeholder="搜索模板名称、机构、标签..."
          allowClear
          enterButton={<Button type="primary" icon={<SearchOutlined />}>搜索</Button>}
          size="large"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onSearch={handleSearch}
          className={styles.searchInput}
        />
      </div>

      {/* 主内容区 */}
      <Row gutter={24} className={styles.mainContent}>
        {/* 左侧筛选 */}
        <Col span={6}>
          <TemplateCategories
            filterOptions={filterOptions}
            currentFilter={filter}
            onFilterChange={handleFilterChange}
            onReset={handleResetFilter}
            resultCount={pagination.total}
          />
        </Col>

        {/* 右侧列表 */}
        <Col span={18}>
          <Card
            className={styles.listCard}
            title={
              <div className={styles.listHeader}>
                <Space>
                  <Text strong>模板列表</Text>
                  <Text type="secondary">共 {pagination.total} 个</Text>
                </Space>
                <Space>
                  <Button.Group>
                    <Button
                      type={viewMode === 'grid' ? 'primary' : 'default'}
                      icon={<AppstoreOutlined />}
                      onClick={() => setViewMode('grid')}
                    >
                      网格
                    </Button>
                    <Button
                      type={viewMode === 'list' ? 'primary' : 'default'}
                      icon={<BarsOutlined />}
                      onClick={() => setViewMode('list')}
                    >
                      列表
                    </Button>
                  </Button.Group>
                </Space>
              </div>
            }
          >
            <Spin spinning={loading}>
              {templates.length > 0 ? (
                <>
                  {viewMode === 'grid' ? (
                    <Row gutter={[16, 16]}>
                      {templates.map((template) => (
                        <Col key={template.id} span={8}>
                          {renderGridCard(template)}
                        </Col>
                      ))}
                    </Row>
                  ) : (
                    <List
                      dataSource={templates}
                      renderItem={renderListItem}
                      split
                    />
                  )}

                  {/* 分页 */}
                  <div className={styles.pagination}>
                    <Pagination
                      current={pagination.current}
                      pageSize={pagination.pageSize}
                      total={pagination.total}
                      onChange={handlePageChange}
                      showSizeChanger
                      showQuickJumper
                      showTotal={(total) => `共 ${total} 个模板`}
                    />
                  </div>
                </>
              ) : (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="暂无符合条件的模板"
                >
                  <Button type="primary" onClick={handleResetFilter}>
                    重置筛选条件
                  </Button>
                </Empty>
              )}
            </Spin>
          </Card>
        </Col>
      </Row>

      {/* 模板预览弹窗 */}
      <TemplatePreview
        template={selectedTemplate}
        visible={previewVisible}
        onClose={closePreview}
        onUse={handleUseTemplate}
        onFavorite={handleFavorite}
        isFavorite={selectedTemplate ? favorites.includes(selectedTemplate.id) : false}
      />

      {/* AI填充弹窗 */}
      <AITemplateFill
        template={selectedTemplate}
        visible={aiFillVisible}
        onClose={closeAiFill}
        onComplete={handleAiFillComplete}
      />

      <BackTop />
    </div>
  )
}

export default TemplateList
