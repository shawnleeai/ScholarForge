/**
 * 参考文献管理页面
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card, Row, Col, Button, Input, Table, Tag, Space, Modal, Form,
  Select, Upload, message, Tabs, Statistic, Badge, Dropdown, Menu,
  Checkbox, Tooltip, Popconfirm, Empty, Progress, List, Typography
} from 'antd'
import type { UploadProps } from 'antd'
import {
  BookOutlined, PlusOutlined, ImportOutlined, ExportOutlined,
  FolderOutlined, TagOutlined, StarOutlined, StarFilled,
  SearchOutlined, FilterOutlined, EditOutlined, DeleteOutlined,
  FileTextOutlined, LinkOutlined, EyeOutlined, EyeInvisibleOutlined,
  CopyOutlined, DownloadOutlined, FolderAddOutlined, ReloadOutlined
} from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import {
  referenceService, type Reference, type Folder, type CitationStyle, type ReferenceStatistics
} from '@/services/referenceService'
import styles from './ReferenceManagement.module.css'

const { Title, Text, Paragraph } = Typography
const { Option } = Select
const { TabPane } = Tabs
const { Search } = Input

const CITATION_STYLES: { value: CitationStyle; label: string }[] = [
  { value: 'gb7714', label: 'GB/T 7714 (中国国标)' },
  { value: 'apa', label: 'APA (第7版)' },
  { value: 'mla', label: 'MLA (第9版)' },
  { value: 'chicago', label: 'Chicago (第17版)' },
  { value: 'ieee', label: 'IEEE' },
  { value: 'harvard', label: 'Harvard' },
  { value: 'vancouver', label: 'Vancouver' },
]

const PUBLICATION_TYPES = [
  { value: 'journal', label: '期刊论文', color: 'blue' },
  { value: 'conference', label: '会议论文', color: 'green' },
  { value: 'book', label: '图书', color: 'orange' },
  { value: 'thesis', label: '学位论文', color: 'purple' },
  { value: 'report', label: '技术报告', color: 'cyan' },
  { value: 'online', label: '网络资源', color: 'magenta' },
  { value: 'other', label: '其他', color: 'default' },
]

const ReferenceManagement: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>()

  // 状态
  const [references, setReferences] = useState<Reference[]>([])
  const [folders, setFolders] = useState<Folder[]>([])
  const [tags, setTags] = useState<string[]>([])
  const [statistics, setStatistics] = useState<ReferenceStatistics | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([])
  const [currentFolder, setCurrentFolder] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState<Record<string, any>>({})

  // 模态框状态
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [folderModalVisible, setFolderModalVisible] = useState(false)
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [citeModalVisible, setCiteModalVisible] = useState(false)
  const [citeStyle, setCiteStyle] = useState<CitationStyle>('gb7714')
  const [formattedCitations, setFormattedCitations] = useState<string[]>([])

  const [form] = Form.useForm()
  const [folderForm] = Form.useForm()

  // 获取数据
  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = {
        ...filters,
        search: searchQuery || undefined,
        folder_id: currentFolder,
        paper_id: paperId,
      }

      const [refsRes, tagsRes, statsRes] = await Promise.all([
        referenceService.getReferences(params),
        referenceService.getTags(),
        referenceService.getStatistics(paperId),
      ])

      setReferences(refsRes.data?.data?.items || [])
      setTags(tagsRes.data?.data?.tags || [])
      setStatistics(statsRes.data?.data)
    } catch (error) {
      console.error('获取数据失败', error)
    } finally {
      setLoading(false)
    }
  }, [filters, searchQuery, currentFolder, paperId])

  const fetchFolders = async () => {
    try {
      const res = await referenceService.getFolders()
      setFolders(res.data?.data?.items || [])
    } catch (error) {
      console.error('获取文件夹失败', error)
    }
  }

  useEffect(() => {
    fetchData()
    fetchFolders()
  }, [fetchData])

  // 创建参考文献
  const handleCreate = async (values: any) => {
    try {
      await referenceService.createReference({
        ...values,
        paper_id: paperId,
        folder_id: currentFolder,
      })
      message.success('添加成功')
      setCreateModalVisible(false)
      form.resetFields()
      fetchData()
    } catch (error) {
      message.error('添加失败')
    }
  }

  // 创建文件夹
  const handleCreateFolder = async (values: any) => {
    try {
      await referenceService.createFolder(values)
      message.success('文件夹创建成功')
      setFolderModalVisible(false)
      folderForm.resetFields()
      fetchFolders()
    } catch (error) {
      message.error('创建失败')
    }
  }

  // 删除参考文献
  const handleDelete = async (id: string) => {
    try {
      await referenceService.deleteReference(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  // 批量删除
  const handleBatchDelete = async () => {
    try {
      await Promise.all(selectedRowKeys.map(id => referenceService.deleteReference(id)))
      message.success(`已删除 ${selectedRowKeys.length} 篇文献`)
      setSelectedRowKeys([])
      fetchData()
    } catch (error) {
      message.error('批量删除失败')
    }
  }

  // 标记阅读状态
  const handleMarkRead = async (id: string, isRead: boolean) => {
    try {
      await referenceService.markAsRead(id, isRead)
      fetchData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  // 切换重要标记
  const handleToggleImportant = async (record: Reference) => {
    try {
      await referenceService.updateReference(record.id, {
        is_important: !record.is_important
      })
      fetchData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  // 格式化引用
  const handleFormatCitations = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择文献')
      return
    }
    try {
      const res = await referenceService.formatCitations(selectedRowKeys, citeStyle)
      const citations = res.data?.data?.citations || []
      setFormattedCitations(citations.map((c: any) => c.formatted))
      setCiteModalVisible(true)
    } catch (error) {
      message.error('格式化失败')
    }
  }

  // 导入文献
  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/v1/references/import',
    showUploadList: false,
    beforeUpload: (file) => {
      const isValidType = ['.bib', '.ris', '.txt', '.csv', '.json'].some(
        ext => file.name.toLowerCase().endsWith(ext)
      )
      if (!isValidType) {
        message.error('不支持的文件格式')
        return false
      }
      return true
    },
    customRequest: async ({ file, onSuccess, onError }) => {
      try {
        // 根据文件扩展名判断类型
        const fileName = (file as File).name.toLowerCase()
        let sourceType = 'bibtex'
        if (fileName.endsWith('.ris')) sourceType = 'ris'
        else if (fileName.endsWith('.txt')) sourceType = 'endnote'
        else if (fileName.endsWith('.csv')) sourceType = 'csv'
        else if (fileName.endsWith('.json')) sourceType = 'json'

        await referenceService.importReferences(file as File, sourceType, paperId, currentFolder || undefined)
        message.success('导入成功')
        fetchData()
        setImportModalVisible(false)
        onSuccess?.('ok')
      } catch (error) {
        message.error('导入失败')
        onError?.(error as Error)
      }
    }
  }

  // 导出文献
  const handleExport = async (format: 'bibtex' | 'ris' | 'csv' | 'json') => {
    try {
      const ids = selectedRowKeys.length > 0 ? selectedRowKeys : undefined
      const res = await referenceService.exportReferences({
        reference_ids: ids,
        folder_id: currentFolder || undefined,
        paper_id: paperId,
        format
      })
      const { file_url, file_name } = res.data?.data || {}
      if (file_url) {
        // 触发下载
        const link = document.createElement('a')
        link.href = file_url
        link.download = file_name
        link.click()
        message.success('导出成功')
      }
    } catch (error) {
      message.error('导出失败')
    }
  }

  // 批量移动
  const handleBatchMove = async (folderId: string | null) => {
    try {
      await referenceService.moveToFolder(folderId, selectedRowKeys)
      message.success('移动成功')
      setSelectedRowKeys([])
      fetchData()
    } catch (error) {
      message.error('移动失败')
    }
  }

  // 表格列定义
  const columns = [
    {
      title: '文献信息',
      key: 'info',
      width: '40%',
      render: (_: any, record: Reference) => (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Text strong style={{ fontSize: 14 }}>{record.title}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.authors?.slice(0, 3).join(', ')}
            {record.authors && record.authors.length > 3 ? ' 等' : ''}
          </Text>
          <Space size="small">
            {record.publication_year && (
              <Tag size="small">{record.publication_year}</Tag>
            )}
            {record.journal_name && (
              <Tag size="small" color="blue">{record.journal_name}</Tag>
            )}
            {record.publication_type && (
              <Tag size="small" color={PUBLICATION_TYPES.find(t => t.value === record.publication_type)?.color}>
                {PUBLICATION_TYPES.find(t => t.value === record.publication_type)?.label}
              </Tag>
            )}
          </Space>
        </Space>
      )
    },
    {
      title: '标签',
      key: 'tags',
      width: '20%',
      render: (_: any, record: Reference) => (
        <Space size="small" wrap>
          {record.tags?.map(tag => (
            <Tag key={tag} size="small">{tag}</Tag>
          ))}
        </Space>
      )
    },
    {
      title: '状态',
      key: 'status',
      width: '15%',
      render: (_: any, record: Reference) => (
        <Space>
          <Tooltip title={record.is_read ? '已读' : '未读'}>
            <Button
              type="text"
              size="small"
              icon={record.is_read ? <EyeOutlined /> : <EyeInvisibleOutlined />}
              onClick={() => handleMarkRead(record.id, !record.is_read)}
            />
          </Tooltip>
          <Tooltip title={record.is_important ? '重要' : '标记重要'}>
            <Button
              type="text"
              size="small"
              icon={record.is_important ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
              onClick={() => handleToggleImportant(record)}
            />
          </Tooltip>
          {record.doi && (
            <Tooltip title="查看DOI">
              <Button
                type="text"
                size="small"
                icon={<LinkOutlined />}
                onClick={() => window.open(`https://doi.org/${record.doi}`, '_blank')}
              />
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: '15%',
      render: (_: any, record: Reference) => (
        <Space>
          <Tooltip title="编辑">
            <Button type="text" size="small" icon={<EditOutlined />} />
          </Tooltip>
          <Popconfirm
            title="确认删除"
            onConfirm={() => handleDelete(record.id)}
          >
            <Tooltip title="删除">
              <Button type="text" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ]

  // 文件夹菜单
  const folderMenu = (
    <Menu>
      <Menu.Item key="all" onClick={() => setCurrentFolder(null)}>
        <FolderOutlined /> 全部文献
      </Menu.Item>
      <Menu.Divider />
      {folders.map(folder => (
        <Menu.Item key={folder.id} onClick={() => setCurrentFolder(folder.id)}>
          <FolderOutlined style={{ color: folder.color }} /> {folder.name}
          <span style={{ marginLeft: 8, color: '#999' }}>({folder.item_count})</span>
        </Menu.Item>
      ))}
      <Menu.Divider />
      <Menu.Item key="new" onClick={() => setFolderModalVisible(true)}>
        <FolderAddOutlined /> 新建文件夹
      </Menu.Item>
    </Menu>
  )

  // 导出菜单
  const exportMenu = (
    <Menu>
      <Menu.Item onClick={() => handleExport('bibtex')}>BibTeX (.bib)</Menu.Item>
      <Menu.Item onClick={() => handleExport('ris')}>RIS (.ris)</Menu.Item>
      <Menu.Item onClick={() => handleExport('csv')}>CSV (.csv)</Menu.Item>
      <Menu.Item onClick={() => handleExport('json')}>JSON (.json)</Menu.Item>
    </Menu>
  )

  // 移动到菜单
  const moveMenu = (
    <Menu>
      <Menu.Item onClick={() => handleBatchMove(null)}>移出文件夹</Menu.Item>
      <Menu.Divider />
      {folders.map(folder => (
        <Menu.Item key={folder.id} onClick={() => handleBatchMove(folder.id)}>
          {folder.name}
        </Menu.Item>
      ))}
    </Menu>
  )

  return (
    <div className={styles.container}>
      <Title level={2}><BookOutlined /> 参考文献管理</Title>

      {/* 统计卡片 */}
      {statistics && (
        <Row gutter={16} className={styles.stats}>
          <Col span={4}>
            <Card>
              <Statistic title="总文献数" value={statistics.total} />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic
                title="已读"
                value={statistics.read_count}
                suffix={`/${statistics.total}`}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic title="重要文献" value={statistics.important_count} />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic title="期刊论文" value={statistics.by_type?.journal || 0} />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic title="会议论文" value={statistics.by_type?.conference || 0} />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic
                title="平均评分"
                value={statistics.avg_rating || 0}
                precision={1}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 工具栏 */}
      <Card className={styles.toolbar}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space>
              <Dropdown overlay={folderMenu}>
                <Button icon={<FolderOutlined />}>
                  {currentFolder
                    ? folders.find(f => f.id === currentFolder)?.name
                    : '全部文献'
                  }
                </Button>
              </Dropdown>

              <Search
                placeholder="搜索标题、作者、DOI..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onSearch={fetchData}
                style={{ width: 300 }}
                allowClear
              />

              <Select
                placeholder="文献类型"
                allowClear
                style={{ width: 120 }}
                onChange={value => setFilters({ ...filters, publication_type: value })}
              >
                {PUBLICATION_TYPES.map(type => (
                  <Option key={type.value} value={type.value}>{type.label}</Option>
                ))}
              </Select>

              <Select
                placeholder="阅读状态"
                allowClear
                style={{ width: 100 }}
                onChange={value => setFilters({ ...filters, is_read: value })}
              >
                <Option value={true}>已读</Option>
                <Option value={false}>未读</Option>
              </Select>

              <Select
                placeholder="标签"
                allowClear
                style={{ width: 120 }}
                onChange={value => setFilters({ ...filters, tags: value ? [value] : undefined })}
              >
                {tags.map(tag => (
                  <Option key={tag} value={tag}>{tag}</Option>
                ))}
              </Select>
            </Space>
          </Col>

          <Col>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setCreateModalVisible(true)}
              >
                添加文献
              </Button>

              <Button
                icon={<ImportOutlined />}
                onClick={() => setImportModalVisible(true)}
              >
                导入
              </Button>

              <Dropdown overlay={exportMenu}>
                <Button icon={<ExportOutlined />}>导出</Button>
              </Dropdown>

              {selectedRowKeys.length > 0 && (
                <>
                  <Dropdown overlay={moveMenu}>
                    <Button>移动到</Button>
                  </Dropdown>

                  <Button onClick={handleFormatCitations}>
                    格式化引用
                  </Button>

                  <Popconfirm
                    title={`确认删除选中的 ${selectedRowKeys.length} 篇文献？`}
                    onConfirm={handleBatchDelete}
                  >
                    <Button danger>批量删除</Button>
                  </Popconfirm>
                </>
              )}

              <Button icon={<ReloadOutlined />} onClick={fetchData} />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 文献列表 */}
      <Card>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={references}
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          pagination={{
            defaultPageSize: 20,
            showSizeChanger: true,
            showTotal: total => `共 ${total} 篇文献`
          }}
        />
      </Card>

      {/* 添加文献模态框 */}
      <Modal
        title="添加参考文献"
        visible={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        width={700}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Row gutter={16}>
            <Col span={16}>
              <Form.Item name="title" label="标题" rules={[{ required: true }]}>
                <Input placeholder="输入文献标题" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="publication_type" label="类型" initialValue="journal">
                <Select>
                  {PUBLICATION_TYPES.map(type => (
                    <Option key={type.value} value={type.value}>{type.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="authors" label="作者">
            <Select
              mode="tags"
              placeholder="输入作者姓名，按回车分隔"
              tokenSeparators={[',', ';']}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="publication_year" label="发表年份">
                <Input type="number" placeholder="2023" />
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item name="journal_name" label="期刊/会议/来源">
                <Input placeholder="期刊名或会议名" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="volume" label="卷">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="issue" label="期">
                <Input />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="pages" label="页码">
                <Input placeholder="1-10" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="doi" label="DOI">
                <Input placeholder="10.xxxx/xxxxx" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="url" label="URL">
                <Input placeholder="https://..." />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="abstract" label="摘要">
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item name="tags" label="标签">
            <Select
              mode="tags"
              placeholder="添加标签"
              options={tags.map(t => ({ value: t, label: t }))}
            />
          </Form.Item>

          <Form.Item name="notes" label="笔记">
            <Input.TextArea rows={2} placeholder="个人笔记..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* 新建文件夹模态框 */}
      <Modal
        title="新建文件夹"
        visible={folderModalVisible}
        onCancel={() => setFolderModalVisible(false)}
        onOk={() => folderForm.submit()}
      >
        <Form form={folderForm} onFinish={handleCreateFolder} layout="vertical">
          <Form.Item name="name" label="文件夹名称" rules={[{ required: true }]}>
            <Input placeholder="输入文件夹名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="文件夹描述（可选）" />
          </Form.Item>
          <Form.Item name="color" label="颜色" initialValue="#1890ff">
            <Select>
              <Option value="#1890ff"><span style={{ color: '#1890ff' }}>● 蓝色</span></Option>
              <Option value="#52c41a"><span style={{ color: '#52c41a' }}>● 绿色</span></Option>
              <Option value="#faad14"><span style={{ color: '#faad14' }}>● 黄色</span></Option>
              <Option value="#f5222d"><span style={{ color: '#f5222d' }}>● 红色</span></Option>
              <Option value="#722ed1"><span style={{ color: '#722ed1' }}>● 紫色</span></Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 导入模态框 */}
      <Modal
        title="导入文献"
        visible={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={null}
      >
        <Upload.Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <ImportOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
          <p className="ant-upload-hint">
            支持 BibTeX (.bib)、RIS (.ris)、EndNote (.txt)、CSV (.csv)、JSON (.json) 格式
          </p>
        </Upload.Dragger>
      </Modal>

      {/* 格式化引用模态框 */}
      <Modal
        title="格式化引用"
        visible={citeModalVisible}
        onCancel={() => setCiteModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setCiteModalVisible(false)}>关闭</Button>,
          <Button
            key="copy"
            type="primary"
            icon={<CopyOutlined />}
            onClick={() => {
              navigator.clipboard.writeText(formattedCitations.join('\n'))
              message.success('已复制到剪贴板')
            }}
          >
            复制全部
          </Button>
        ]}
      >
        <Space style={{ marginBottom: 16 }}>
          <span>引用格式：</span>
          <Select value={citeStyle} onChange={setCiteStyle} style={{ width: 200 }}>
            {CITATION_STYLES.map(style => (
              <Option key={style.value} value={style.value}>{style.label}</Option>
            ))}
          </Select>
          <Button onClick={handleFormatCitations}>重新生成</Button>
        </Space>

        <Input.TextArea
          value={formattedCitations.join('\n\n')}
          rows={15}
          readOnly
          style={{ fontFamily: 'monospace', fontSize: 13 }}
        />
      </Modal>
    </div>
  )
}

export default ReferenceManagement
