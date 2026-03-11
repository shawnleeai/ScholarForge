/**
 * 数据管理页面
 * 数据集上传、版本管理、预览分析
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Table,
  Tag,
  Upload,
  Modal,
  Form,
  Input,
  Select,
  Tabs,
  Statistic,
  Row,
  Col,
  Space,
  Typography,
  Dropdown,
  Menu,
  Badge,
  Empty,
  message,
  Progress,
} from 'antd'
import {
  DatabaseOutlined,
  UploadOutlined,
  EyeOutlined,
  HistoryOutlined,
  ShareAltOutlined,
  DeleteOutlined,
  EditOutlined,
  MoreOutlined,
  FileExcelOutlined,
  FileTextOutlined,
  PictureOutlined,
  SoundOutlined,
  VideoCameraOutlined,
  FolderOutlined,
  PlusOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import styles from './DatasetManagement.module.css'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs
const { Option } = Select
const { TextArea } = Input
const { Dragger } = Upload

interface Dataset {
  id: string
  name: string
  description?: string
  data_type: string
  status: 'draft' | 'processing' | 'ready' | 'archived' | 'error'
  owner_id: string
  research_field?: string
  tags: string[]
  access_level: 'private' | 'team' | 'organization' | 'public'
  versions: DatasetVersion[]
  current_version_id?: string
  columns: DatasetColumn[]
  created_at: string
  updated_at: string
  stats: {
    total_versions: number
    total_downloads: number
    last_accessed?: string
  }
}

interface DatasetVersion {
  id: string
  version_number: string
  description?: string
  file_size: number
  row_count?: number
  created_at: string
  created_by: string
  is_latest: boolean
}

interface DatasetColumn {
  name: string
  data_type: string
  description?: string
  nullable: boolean
}

const DatasetManagement: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(false)
  const [isUploadModalVisible, setIsUploadModalVisible] = useState(false)
  const [isDetailModalVisible, setIsDetailModalVisible] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null)
  const [uploadForm] = Form.useForm()

  const typeIcons: Record<string, React.ReactNode> = {
    tabular: <FileExcelOutlined />,
    image: <PictureOutlined />,
    text: <FileTextOutlined />,
    audio: <SoundOutlined />,
    video: <VideoCameraOutlined />,
    mixed: <FolderOutlined />,
  }

  const typeColors: Record<string, string> = {
    tabular: 'green',
    image: 'blue',
    text: 'cyan',
    audio: 'purple',
    video: 'magenta',
    mixed: 'orange',
  }

  const statusColors: Record<string, string> = {
    draft: 'default',
    processing: 'processing',
    ready: 'success',
    archived: 'warning',
    error: 'error',
  }

  const accessLabels: Record<string, string> = {
    private: '私有',
    team: '团队',
    organization: '组织',
    public: '公开',
  }

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockData: Dataset[] = [
        {
          id: 'ds_001',
          name: '房价预测数据集',
          description: '包含房屋特征和价格信息的回归分析数据集',
          data_type: 'tabular',
          status: 'ready',
          owner_id: 'user_001',
          research_field: '机器学习',
          tags: ['回归', '房价', '房地产'],
          access_level: 'team',
          columns: [
            { name: 'area', data_type: 'float', nullable: false },
            { name: 'bedrooms', data_type: 'int', nullable: false },
            { name: 'price', data_type: 'float', nullable: false },
          ],
          versions: [
            {
              id: 'ver_001',
              version_number: '1.0.0',
              description: '初始版本',
              file_size: 1024 * 1024 * 2,
              row_count: 1000,
              created_at: '2024-02-01',
              created_by: 'user_001',
              is_latest: true,
            },
          ],
          current_version_id: 'ver_001',
          created_at: '2024-02-01',
          updated_at: '2024-02-15',
          stats: {
            total_versions: 1,
            total_downloads: 45,
          },
        },
        {
          id: 'ds_002',
          name: '医学影像数据集',
          description: '肺部CT扫描图像数据集，用于疾病检测',
          data_type: 'image',
          status: 'ready',
          owner_id: 'user_001',
          research_field: '计算机视觉',
          tags: ['医学影像', 'CT', '疾病检测'],
          access_level: 'private',
          columns: [],
          versions: [
            {
              id: 'ver_002',
              version_number: '1.0.0',
              description: '原始数据集',
              file_size: 1024 * 1024 * 500,
              row_count: 5000,
              created_at: '2024-01-15',
              created_by: 'user_001',
              is_latest: true,
            },
          ],
          current_version_id: 'ver_002',
          created_at: '2024-01-15',
          updated_at: '2024-01-20',
          stats: {
            total_versions: 1,
            total_downloads: 12,
          },
        },
      ]

      setDatasets(mockData)
    } catch (error) {
      message.error('加载数据集失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (values: any) => {
    try {
      message.success('数据集创建成功')
      setIsUploadModalVisible(false)
      uploadForm.resetFields()
      loadDatasets()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleDelete = (datasetId: string) => {
    Modal.confirm({
      title: '删除数据集',
      content: '确定要删除此数据集吗？此操作不可恢复。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => {
        message.success('数据集已删除')
      },
    })
  }

  const handleViewDetail = (dataset: Dataset) => {
    setSelectedDataset(dataset)
    setIsDetailModalVisible(true)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
  }

  const columns = [
    {
      title: '数据集',
      key: 'name',
      render: (record: Dataset) => (
        <Space>
          <div className={styles.typeIcon} style={{ color: `var(--ant-${typeColors[record.data_type]}-color)` }}>
            {typeIcons[record.data_type]}
          </div>
          <div>
            <div className={styles.datasetName}>{record.name}</div>
            <div className={styles.datasetDesc}>{record.description}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'data_type',
      key: 'data_type',
      width: 100,
      render: (type: string) => (
        <Tag color={typeColors[type]}>{type}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Badge status={statusColors[status] as any} text={status} />
      ),
    },
    {
      title: '版本',
      key: 'versions',
      width: 80,
      render: (record: Dataset) => (
        <span>{record.versions.length}</span>
      ),
    },
    {
      title: '访问级别',
      dataIndex: 'access_level',
      key: 'access_level',
      width: 100,
      render: (level: string) => accessLabels[level],
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 120,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (record: Dataset) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          />
          <Dropdown
            overlay={
              <Menu>
                <Menu.Item key="preview" icon={<EyeOutlined />}>
                  预览数据
                </Menu.Item>
                <Menu.Item key="version" icon={<HistoryOutlined />}>
                  版本管理
                </Menu.Item>
                <Menu.Item key="share" icon={<ShareAltOutlined />}>
                  分享
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item key="edit" icon={<EditOutlined />}>
                  编辑
                </Menu.Item>
                <Menu.Item key="delete" icon={<DeleteOutlined />} danger>
                  删除
                </Menu.Item>
              </Menu>
            }
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Title level={3}>
          <DatabaseOutlined /> 数据管理
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsUploadModalVisible(true)}
        >
          新建数据集
        </Button>
      </div>

      <Card className={styles.statsCard}>
        <Row gutter={24}>
          <Col span={6}>
            <Statistic title="数据集总数" value={datasets.length} />
          </Col>
          <Col span={6}>
            <Statistic title="总存储大小" value="2.5 GB" />
          </Col>
          <Col span={6}>
            <Statistic title="总下载次数" value={57} />
          </Col>
          <Col span={6}>
            <Statistic title="本月新增" value={3} />
          </Col>
        </Row>
      </Card>

      <Card className={styles.tableCard}>
        <div className={styles.tableHeader}>
          <Input
            placeholder="搜索数据集"
            prefix={<SearchOutlined />}
            style={{ width: 300 }}
          />
          <Select defaultValue="all" style={{ width: 120 }}>
            <Option value="all">全部类型</Option>
            <Option value="tabular">表格</Option>
            <Option value="image">图像</Option>
            <Option value="text">文本</Option>
          </Select>
        </div>

        <Table
          dataSource={datasets}
          columns={columns}
          rowKey="id"
          loading={loading}
        />
      </Card>

      {/* 上传弹窗 */}
      <Modal
        title="新建数据集"
        open={isUploadModalVisible}
        onOk={() => uploadForm.submit()}
        onCancel={() => setIsUploadModalVisible(false)}
        width={700}
      >
        <Form form={uploadForm} layout="vertical" onFinish={handleUpload}>
          <Form.Item
            name="name"
            label="数据集名称"
            rules={[{ required: true, message: '请输入数据集名称' }]}
          >
            <Input placeholder="输入数据集名称" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="描述数据集的内容和用途" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="data_type"
                label="数据类型"
                rules={[{ required: true }]}
              >
                <Select placeholder="选择数据类型">
                  <Option value="tabular">表格数据</Option>
                  <Option value="image">图像数据</Option>
                  <Option value="text">文本数据</Option>
                  <Option value="audio">音频数据</Option>
                  <Option value="video">视频数据</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="access_level" label="访问级别" initialValue="private">
                <Select>
                  <Option value="private">私有</Option>
                  <Option value="team">团队</Option>
                  <Option value="organization">组织</Option>
                  <Option value="public">公开</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="research_field" label="研究领域">
            <Select placeholder="选择研究领域" allowClear>
              <Option value="机器学习">机器学习</Option>
              <Option value="计算机视觉">计算机视觉</Option>
              <Option value="自然语言处理">自然语言处理</Option>
            </Select>
          </Form.Item>

          <Form.Item label="上传文件">
            <Dragger>
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持 CSV, Excel, JSON, ZIP 等格式
              </p>
            </Dragger>
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title="数据集详情"
        open={isDetailModalVisible}
        onCancel={() => setIsDetailModalVisible(false)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setIsDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button key="preview" type="primary" icon={<EyeOutlined />}>
            预览数据
          </Button>,
        ]}
      >
        {selectedDataset && (
          <Tabs defaultActiveKey="overview">
            <TabPane tab="概览" key="overview">
              <div className={styles.detailSection}>
                <Title level={5}>{selectedDataset.name}</Title>
                <Paragraph>{selectedDataset.description}</Paragraph>
                <Space wrap>
                  <Tag color={typeColors[selectedDataset.data_type]}>
                    {selectedDataset.data_type}
                  </Tag>
                  <Tag>{accessLabels[selectedDataset.access_level]}</Tag>
                  {selectedDataset.tags.map(tag => (
                    <Tag key={tag}>{tag}</Tag>
                  ))}
                </Space>
              </div>

              <Row gutter={24} className={styles.detailStats}>
                <Col span={8}>
                  <Statistic
                    title="总行数"
                    value={selectedDataset.versions[0]?.row_count || 0}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="文件大小"
                    value={formatFileSize(selectedDataset.versions[0]?.file_size || 0)}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="下载次数"
                    value={selectedDataset.stats.total_downloads}
                  />
                </Col>
              </Row>
            </TabPane>

            <TabPane tab="版本" key="versions">
              <Table
                dataSource={selectedDataset.versions}
                rowKey="id"
                pagination={false}
                columns={[
                  { title: '版本', dataIndex: 'version_number', key: 'version' },
                  { title: '描述', dataIndex: 'description', key: 'description' },
                  { title: '大小', dataIndex: 'file_size', key: 'size', render: formatFileSize },
                  { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
                ]}
              />
            </TabPane>

            <TabPane tab="数据结构" key="schema">
              {selectedDataset.columns.length > 0 ? (
                <Table
                  dataSource={selectedDataset.columns}
                  rowKey="name"
                  pagination={false}
                  columns={[
                    { title: '列名', dataIndex: 'name', key: 'name' },
                    { title: '类型', dataIndex: 'data_type', key: 'type' },
                    { title: '可空', dataIndex: 'nullable', key: 'nullable', render: v => v ? '是' : '否' },
                  ]}
                />
              ) : (
                <Empty description="该数据集没有列信息" />
              )}
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  )
}

export default DatasetManagement
