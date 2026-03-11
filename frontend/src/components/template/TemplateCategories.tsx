/**
 * 模板分类导航组件
 * 提供多维度模板筛选导航
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Menu,
  Tag,
  Space,
  Typography,
  Badge,
  Collapse,
  Checkbox,
  Radio,
  Divider,
  Button,
  Tooltip,
} from 'antd'
import {
  FileTextOutlined,
  BookOutlined,
  GlobalOutlined,
  BankOutlined,
  ExperimentOutlined,
  TeamOutlined,
  StarOutlined,
  FireOutlined,
  ClockCircleOutlined,
  FilterOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import styles from './TemplateCategories.module.css'

const { Title, Text } = Typography
const { SubMenu } = Menu
const { Panel } = Collapse

interface FilterOptions {
  types: { value: string; label: string }[]
  institutions: string[]
  disciplines: string[]
  languages: string[]
  difficulties: string[]
  tags: string[]
}

interface FilterState {
  type?: string
  institution?: string
  discipline?: string
  language?: string
  difficulty?: string
  tags: string[]
  sortBy: string
}

interface TemplateCategoriesProps {
  filterOptions: FilterOptions
  currentFilter: FilterState
  onFilterChange: (filter: Partial<FilterState>) => void
  onReset: () => void
  resultCount?: number
}

const TemplateCategories: React.FC<TemplateCategoriesProps> = ({
  filterOptions,
  currentFilter,
  onFilterChange,
  onReset,
  resultCount = 0,
}) => {
  const [expandedKeys, setExpandedKeys] = useState<string[]>(['type', 'institution'])
  const [selectedMenuKey, setSelectedMenuKey] = useState<string>('all')

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'thesis':
        return <BookOutlined />
      case 'journal':
        return <FileTextOutlined />
      case 'conference':
        return <TeamOutlined />
      case 'report':
        return <ExperimentOutlined />
      default:
        return <FileTextOutlined />
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'green'
      case 'intermediate':
        return 'blue'
      case 'advanced':
        return 'red'
      default:
        return 'default'
    }
  }

  const getDifficultyLabel = (difficulty: string) => {
    const labels: Record<string, string> = {
      beginner: '入门级',
      intermediate: '中级',
      advanced: '高级',
    }
    return labels[difficulty] || difficulty
  }

  const handleMenuClick = (key: string) => {
    setSelectedMenuKey(key)

    // 解析菜单key
    if (key === 'all') {
      onFilterChange({ type: undefined, institution: undefined })
    } else if (key.startsWith('type:')) {
      const type = key.replace('type:', '')
      onFilterChange({ type })
    } else if (key.startsWith('inst:')) {
      const institution = key.replace('inst:', '')
      onFilterChange({ institution })
    } else if (key === 'favorites') {
      // 处理收藏
    } else if (key === 'recent') {
      // 处理最近使用
    } else if (key === 'popular') {
      onFilterChange({ sortBy: 'downloads' })
    }
  }

  const hasActiveFilters = () => {
    return (
      currentFilter.type ||
      currentFilter.institution ||
      currentFilter.discipline ||
      currentFilter.language ||
      currentFilter.difficulty ||
      currentFilter.tags.length > 0
    )
  }

  return (
    <div className={styles.categoriesContainer}>
      {/* 快捷导航菜单 */}
      <Card size="small" className={styles.quickNav}>
        <Menu
          mode="inline"
          selectedKeys={[selectedMenuKey]}
          onClick={({ key }) => handleMenuClick(key)}
          className={styles.menu}
        >
          <Menu.Item key="all" icon={<FileTextOutlined />}>
            <Space>
              <span>全部模板</span>
              <Badge count={resultCount} overflowCount={999} style={{ backgroundColor: '#1890ff' }} />
            </Space>
          </Menu.Item>

          <Menu.Item key="popular" icon={<FireOutlined />}>
            热门模板
          </Menu.Item>

          <Menu.Item key="favorites" icon={<StarOutlined />}>
            我的收藏
          </Menu.Item>

          <Menu.Item key="recent" icon={<ClockCircleOutlined />}>
            最近使用
          </Menu.Item>

          <Divider style={{ margin: '8px 0' }} />

          <SubMenu key="types" icon={<BookOutlined />} title="按类型">
            {filterOptions.types.map((type) => (
              <Menu.Item key={`type:${type.value}`}>
                <Space>
                  {getTypeIcon(type.value)}
                  <span>{type.label}</span>
                </Space>
              </Menu.Item>
            ))}
          </SubMenu>

          <SubMenu key="institutions" icon={<BankOutlined />} title="按机构">
            {filterOptions.institutions.slice(0, 10).map((inst) => (
              <Menu.Item key={`inst:${inst}`}>
                <span>{inst}</span>
              </Menu.Item>
            ))}
          </SubMenu>
        </Menu>
      </Card>

      {/* 高级筛选 */}
      <Card
        size="small"
        title={
          <Space>
            <FilterOutlined />
            <span>高级筛选</span>
            {hasActiveFilters() && (
              <Badge
                count={
                  (currentFilter.type ? 1 : 0) +
                  (currentFilter.institution ? 1 : 0) +
                  (currentFilter.discipline ? 1 : 0) +
                  (currentFilter.language ? 1 : 0) +
                  (currentFilter.difficulty ? 1 : 0) +
                  currentFilter.tags.length
                }
                style={{ backgroundColor: '#52c41a' }}
              />
            )}
          </Space>
        }
        extra={
          hasActiveFilters() && (
            <Button type="link" size="small" icon={<ReloadOutlined />} onClick={onReset}>
              重置
            </Button>
          )
        }
        className={styles.filterCard}
      >
        <Collapse
          activeKey={expandedKeys}
          onChange={setExpandedKeys}
          ghost
          className={styles.filterCollapse}
        >
          {/* 类型筛选 */}
          <Panel header="模板类型" key="type">
            <Radio.Group
              value={currentFilter.type}
              onChange={(e) => onFilterChange({ type: e.target.value })}
              className={styles.filterGroup}
            >
              <Space direction="vertical">
                <Radio value={undefined}>全部类型</Radio>
                {filterOptions.types.map((type) => (
                  <Radio key={type.value} value={type.value}>
                    <Space>
                      {getTypeIcon(type.value)}
                      {type.label}
                    </Space>
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          </Panel>

          {/* 机构筛选 */}
          {filterOptions.institutions.length > 0 && (
            <Panel header="所属机构" key="institution">
              <Radio.Group
                value={currentFilter.institution}
                onChange={(e) => onFilterChange({ institution: e.target.value })}
                className={styles.filterGroup}
              >
                <Space direction="vertical">
                  <Radio value={undefined}>全部机构</Radio>
                  {filterOptions.institutions.slice(0, 15).map((inst) => (
                    <Radio key={inst} value={inst}>
                      {inst}
                    </Radio>
                  ))}
                </Space>
              </Radio.Group>
            </Panel>
          )}

          {/* 学科筛选 */}
          {filterOptions.disciplines.length > 0 && (
            <Panel header="学科领域" key="discipline">
              <Radio.Group
                value={currentFilter.discipline}
                onChange={(e) => onFilterChange({ discipline: e.target.value })}
                className={styles.filterGroup}
              >
                <Space direction="vertical">
                  <Radio value={undefined}>全部学科</Radio>
                  {filterOptions.disciplines.map((disc) => (
                    <Radio key={disc} value={disc}>
                      {disc}
                    </Radio>
                  ))}
                </Space>
              </Radio.Group>
            </Panel>
          )}

          {/* 语言筛选 */}
          <Panel header="语言" key="language">
            <Radio.Group
              value={currentFilter.language}
              onChange={(e) => onFilterChange({ language: e.target.value })}
              className={styles.filterGroup}
            >
              <Space direction="vertical">
                <Radio value={undefined}>全部语言</Radio>
                <Radio value="zh">
                  <Space>
                    <span>🇨🇳</span>
                    <span>中文</span>
                  </Space>
                </Radio>
                <Radio value="en">
                  <Space>
                    <span>🇺🇸</span>
                    <span>英文</span>
                  </Space>
                </Radio>
              </Space>
            </Radio.Group>
          </Panel>

          {/* 难度筛选 */}
          <Panel header="难度等级" key="difficulty">
            <Radio.Group
              value={currentFilter.difficulty}
              onChange={(e) => onFilterChange({ difficulty: e.target.value })}
              className={styles.filterGroup}
            >
              <Space direction="vertical">
                <Radio value={undefined}>全部难度</Radio>
                {['beginner', 'intermediate', 'advanced'].map((diff) => (
                  <Radio key={diff} value={diff}>
                    <Tag color={getDifficultyColor(diff)}>
                      {getDifficultyLabel(diff)}
                    </Tag>
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          </Panel>

          {/* 标签筛选 */}
          {filterOptions.tags.length > 0 && (
            <Panel header="标签" key="tags">
              <div className={styles.tagsFilter}>
                {filterOptions.tags.slice(0, 20).map((tag) => (
                  <Tag.CheckableTag
                    key={tag}
                    checked={currentFilter.tags.includes(tag)}
                    onChange={(checked) => {
                      const newTags = checked
                        ? [...currentFilter.tags, tag]
                        : currentFilter.tags.filter((t) => t !== tag)
                      onFilterChange({ tags: newTags })
                    }}
                  >
                    {tag}
                  </Tag.CheckableTag>
                ))}
              </div>
            </Panel>
          )}
        </Collapse>
      </Card>

      {/* 排序选项 */}
      <Card size="small" title="排序方式" className={styles.sortCard}>
        <Radio.Group
          value={currentFilter.sortBy}
          onChange={(e) => onFilterChange({ sortBy: e.target.value })}
          buttonStyle="solid"
          className={styles.sortGroup}
        >
          <Radio.Button value="relevance">相关度</Radio.Button>
          <Radio.Button value="rating">评分</Radio.Button>
          <Radio.Button value="downloads">下载量</Radio.Button>
          <Radio.Button value="created">最新</Radio.Button>
          <Radio.Button value="updated">最近更新</Radio.Button>
        </Radio.Group>
      </Card>

      {/* 已选筛选条件 */}
      {hasActiveFilters() && (
        <Card size="small" className={styles.activeFilters}>
          <Text type="secondary">已选条件：</Text>
          <Space wrap style={{ marginTop: 8 }}>
            {currentFilter.type && (
              <Tag
                closable
                onClose={() => onFilterChange({ type: undefined })}
              >
                类型: {filterOptions.types.find((t) => t.value === currentFilter.type)?.label}
              </Tag>
            )}
            {currentFilter.institution && (
              <Tag
                closable
                onClose={() => onFilterChange({ institution: undefined })}
              >
                机构: {currentFilter.institution}
              </Tag>
            )}
            {currentFilter.discipline && (
              <Tag
                closable
                onClose={() => onFilterChange({ discipline: undefined })}
              >
                学科: {currentFilter.discipline}
              </Tag>
            )}
            {currentFilter.language && (
              <Tag
                closable
                onClose={() => onFilterChange({ language: undefined })}
              >
                语言: {currentFilter.language === 'zh' ? '中文' : '英文'}
              </Tag>
            )}
            {currentFilter.difficulty && (
              <Tag
                closable
                onClose={() => onFilterChange({ difficulty: undefined })}
              >
                难度: {getDifficultyLabel(currentFilter.difficulty)}
              </Tag>
            )}
            {currentFilter.tags.map((tag) => (
              <Tag
                key={tag}
                closable
                onClose={() =>
                  onFilterChange({
                    tags: currentFilter.tags.filter((t) => t !== tag),
                  })
                }
              >
                {tag}
              </Tag>
            ))}
          </Space>
        </Card>
      )}
    </div>
  )
}

export default TemplateCategories
