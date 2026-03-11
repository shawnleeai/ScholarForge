/**
 * 兴趣偏好设置页面
 * 用户可以设置感兴趣的研究领域、关键词、作者等
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Input,
  Select,
  Switch,
  Button,
  Space,
  Tag,
  Typography,
  Divider,
  Alert,
  message,
  Tabs,
  List,
  Checkbox,
  Row,
  Col,
  Slider,
  Empty
} from 'antd'
import {
  TagOutlined,
  UserOutlined,
  BookOutlined,
  BellOutlined,
  SaveOutlined,
  ReloadOutlined,
  PlusOutlined,
  CloseCircleOutlined,
  GlobalOutlined,
  FilterOutlined
} from '@ant-design/icons'
import styles from './InterestSettings.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Option } = Select
const { TabPane } = Tabs

interface InterestSettings {
  keywords: string[]
  categories: string[]
  authors: string[]
  excludedKeywords: string[]
  minYear: number
  preferredSources: string[]
  emailFrequency: 'daily' | 'weekly' | 'never'
  keywordsPerPaper: number
  enableAIRecommendations: boolean
}

const InterestSettingsPage: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [settings, setSettings] = useState<InterestSettings>({
    keywords: ['machine learning', 'natural language processing', 'deep learning'],
    categories: ['cs.AI', 'cs.CL', 'cs.LG'],
    authors: [],
    excludedKeywords: [],
    minYear: 2020,
    preferredSources: ['arxiv', 'semantic_scholar'],
    emailFrequency: 'daily',
    keywordsPerPaper: 10,
    enableAIRecommendations: true
  })

  // 加载设置
  useEffect(() => {
    const loadSettings = async () => {
      setLoading(true)
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))
      form.setFieldsValue(settings)
      setLoading(false)
    }
    loadSettings()
  }, [])

  // 保存设置
  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setSaving(true)

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800))

      setSettings(values)
      message.success('兴趣设置已保存')
    } catch (error) {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  // 重置设置
  const handleReset = () => {
    form.resetFields()
    message.info('已重置为上次保存的设置')
  }

  // 清空所有设置
  const handleClear = () => {
    form.setFieldsValue({
      keywords: [],
      categories: [],
      authors: [],
      excludedKeywords: []
    })
  }

  // 论文类别选项
  const categoryOptions = [
    { label: 'Artificial Intelligence (cs.AI)', value: 'cs.AI' },
    { label: 'Computation and Language (cs.CL)', value: 'cs.CL' },
    { label: 'Computer Vision (cs.CV)', value: 'cs.CV' },
    { label: 'Machine Learning (cs.LG)', value: 'cs.LG' },
    { label: 'Information Retrieval (cs.IR)', value: 'cs.IR' },
    { label: 'Databases (cs.DB)', value: 'cs.DB' },
    { label: 'Software Engineering (cs.SE)', value: 'cs.SE' },
    { label: 'Human-Computer Interaction (cs.HC)', value: 'cs.HC' },
    { label: 'Networking (cs.NI)', value: 'cs.NI' },
    { label: 'Operating Systems (cs.OS)', value: 'cs.OS' },
    { label: 'Programming Languages (cs.PL)', value: 'cs.PL' },
    { label: 'Robotics (cs.RO)', value: 'cs.RO' },
    { label: 'Cryptography (cs.CR)', value: 'cs.CR' },
    { label: 'Graphics (cs.GR)', value: 'cs.GR' },
    { label: 'Statistical Learning (stat.ML)', value: 'stat.ML' },
    { label: 'Quantitative Biology (q-bio)', value: 'q-bio' },
    { label: 'Physics (physics)', value: 'physics' },
    { label: 'Mathematics (math)', value: 'math' },
  ]

  // 数据源选项
  const sourceOptions = [
    { label: 'arXiv', value: 'arxiv', description: '预印本论文，覆盖CS、物理、数学等' },
    { label: 'Semantic Scholar', value: 'semantic_scholar', description: '学术搜索引擎，覆盖多领域' },
    { label: 'PubMed', value: 'pubmed', description: '生物医学文献数据库' },
    { label: 'IEEE Xplore', value: 'ieee', description: '工程技术领域' },
    { label: 'CNKI', value: 'cnki', description: '中国知网，中文学术文献' },
  ]

  // 标签输入处理
  const tagRender = (props: any) => {
    const { label, value, closable, onClose } = props
    return (
      <Tag
        closable={closable}
        onClose={onClose}
        style={{ marginRight: 3 }}
        color="blue"
      >
        {label}
      </Tag>
    )
  }

  return (
    <div className={styles.container}>
      <Title level={3}>
        <TagOutlined /> 兴趣偏好设置
      </Title>

      <Paragraph type="secondary">
        设置您的研究兴趣，我们将根据这些偏好为您推荐最相关的论文。
        推荐系统会结合您的阅读历史、收藏行为和显式设置来优化推荐结果。
      </Paragraph>

      <Form
        form={form}
        layout="vertical"
        initialValues={settings}
        className={styles.form}
      >
        <Tabs defaultActiveKey="keywords" className={styles.tabs}>
          {/* 关键词设置 */}
          <TabPane
            tab={<span><TagOutlined /> 关注关键词</span>}
            key="keywords"
          >
            <Card loading={loading}>
              <Alert
                message="关键词提示"
                description="输入您感兴趣的研究方向关键词，如：machine learning, natural language processing, computer vision 等。系统会根据这些关键词匹配相关论文。"
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Form.Item
                name="keywords"
                label="关注的关键词"
                rules={[{ required: true, message: '请至少输入一个关键词' }]}
              >
                <Select
                  mode="tags"
                  placeholder="输入关键词，按回车添加"
                  tagRender={tagRender}
                  style={{ width: '100%' }}
                  tokenSeparators={[',']}
                />
              </Form.Item>

              <Form.Item
                name="excludedKeywords"
                label="排除的关键词"
              >
                <Select
                  mode="tags"
                  placeholder="输入不想看到的主题关键词"
                  tagRender={(props) => (
                    <Tag
                      closable={props.closable}
                      onClose={props.onClose}
                      color="red"
                    >
                      {props.label}
                    </Tag>
                  )}
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item
                name="keywordsPerPaper"
                label="每篇论文提取关键词数量"
              >
                <Slider
                  min={5}
                  max={50}
                  marks={{
                    5: '5',
                    25: '25',
                    50: '50'
                  }}
                />
              </Form.Item>
            </Card>
          </TabPane>

          {/* 研究领域 */}
          <TabPane
            tab={<span><BookOutlined /> 研究领域</span>}
            key="categories"
          >
            <Card loading={loading}>
              <Alert
                message="领域选择提示"
                description="选择您感兴趣的研究领域，多选会扩大推荐范围但可能降低精准度。"
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Form.Item
                name="categories"
                label="关注的研究领域"
              >
                <Select
                  mode="multiple"
                  placeholder="选择研究领域"
                  style={{ width: '100%' }}
                  options={categoryOptions}
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                />
              </Form.Item>

              <Divider />

              <Form.Item
                name="minYear"
                label="最早发表年份"
              >
                <Slider
                  min={2010}
                  max={2024}
                  marks={{
                    2010: '2010',
                    2015: '2015',
                    2020: '2020',
                    2024: '2024'
                  }}
                />
              </Form.Item>

              <Text type="secondary">
                设置后，系统将只推荐 {form.getFieldValue('minYear') || 2020} 年及以后发表的论文
              </Text>
            </Card>
          </TabPane>

          {/* 关注作者 */}
          <TabPane
            tab={<span><UserOutlined /> 关注作者</span>}
            key="authors"
          >
            <Card loading={loading}>
              <Alert
                message="作者关注提示"
                description="添加您关注的学者姓名，当这些作者有新论文发表时，系统会优先推荐给您。"
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Form.Item
                name="authors"
                label="关注的作者"
              >
                <Select
                  mode="tags"
                  placeholder="输入作者姓名，如：Yoshua Bengio, Yann LeCun"
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Divider />

              <Title level={5}>推荐关注的作者</Title>
              <List
                size="small"
                bordered
                dataSource={[
                  { name: 'Geoffrey Hinton', field: 'Deep Learning', cited: 1500000 },
                  { name: 'Yoshua Bengio', field: 'Deep Learning', cited: 1200000 },
                  { name: 'Yann LeCun', field: 'Computer Vision', cited: 900000 },
                  { name: 'Andrew Ng', field: 'Machine Learning', cited: 800000 },
                ]}
                renderItem={item => (
                  <List.Item
                    actions={[
                      <Button
                        type="link"
                        size="small"
                        icon={<PlusOutlined />}
                        onClick={() => {
                          const current = form.getFieldValue('authors') || []
                          if (!current.includes(item.name)) {
                            form.setFieldsValue({
                              authors: [...current, item.name]
                            })
                          }
                        }}
                      >
                        添加
                      </Button>
                    ]}
                  >
                    <List.Item.Meta
                      title={item.name}
                      description={`${item.field} · ${item.cited.toLocaleString()} citations`}
                    />
                  </List.Item>
                )}
              />
            </Card>
          </TabPane>

          {/* 数据源 */}
          <TabPane
            tab={<span><GlobalOutlined /> 数据源</span>}
            key="sources"
          >
            <Card loading={loading}>
              <Alert
                message="数据源选择"
                description="选择您希望获取论文的数据源，推荐同时选择多个源以获得更全面的覆盖。"
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Form.Item
                name="preferredSources"
                label="偏好的数据源"
                rules={[{ required: true, message: '请至少选择一个数据源' }]}
              >
                <Checkbox.Group className={styles.sourceGroup}>
                  <Row gutter={[16, 16]}>
                    {sourceOptions.map(source => (
                      <Col span={12} key={source.value}>
                        <Card size="small" className={styles.sourceCard}>
                          <Checkbox value={source.value}>
                            <Text strong>{source.label}</Text>
                          </Checkbox>
                          <Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0, fontSize: 12 }}>
                            {source.description}
                          </Paragraph>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Checkbox.Group>
              </Form.Item>
            </Card>
          </TabPane>

          {/* 通知设置 */}
          <TabPane
            tab={<span><BellOutlined /> 通知设置</span>}
            key="notifications"
          >
            <Card loading={loading}>
              <Form.Item
                name="emailFrequency"
                label="邮件推送频率"
              >
                <Select style={{ width: 200 }}>
                  <Option value="daily">每日推送</Option>
                  <Option value="weekly">每周推送</Option>
                  <Option value="never">不推送</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="enableAIRecommendations"
                valuePropName="checked"
              >
                <Switch
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                />
                <Text style={{ marginLeft: 8 }}>
                  启用AI智能推荐（根据阅读行为自动学习偏好）
                </Text>
              </Form.Item>

              <Divider />

              <Alert
                message="隐私说明"
                description="AI推荐功能会分析您的阅读历史、点击行为和收藏记录来优化推荐。所有数据仅用于改进推荐质量，不会与第三方共享。"
                type="warning"
                showIcon
              />
            </Card>
          </TabPane>
        </Tabs>

        {/* 操作按钮 */}
        <div className={styles.actions}>
          <Space size="large">
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              loading={saving}
              size="large"
            >
              保存设置
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
              size="large"
            >
              重置
            </Button>
            <Button
              danger
              onClick={handleClear}
              size="large"
            >
              清空所有
            </Button>
          </Space>
        </div>
      </Form>

      {/* 效果预览 */}
      <Card
        title={<><FilterOutlined /> 设置效果预览</>}
        className={styles.preview}
        style={{ marginTop: 32 }}
      >
        <Row gutter={24}>
          <Col span={8}>
            <Statistic
              title="关注的领域"
              value={(form.getFieldValue('categories') || []).length}
              suffix="个"
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="关注的关键词"
              value={(form.getFieldValue('keywords') || []).length}
              suffix="个"
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="关注的作者"
              value={(form.getFieldValue('authors') || []).length}
              suffix="人"
            />
          </Col>
        </Row>
        <Divider />
        <Paragraph>
          根据当前设置，预计每日可推荐 <Text strong>15-30</Text> 篇相关论文
        </Paragraph>
      </Card>
    </div>
  )
}

export default InterestSettingsPage
