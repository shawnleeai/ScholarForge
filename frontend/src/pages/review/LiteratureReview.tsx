/**
 * 文献综述生成页面
 */

import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Steps,
  Card,
  Button,
  Checkbox,
  List,
  Tag,
  Space,
  Typography,
  Radio,
  Select,
  Alert,
  Progress,
  Empty,
  message,
  Modal,
  Tooltip,
  Divider,
  Descriptions,
} from 'antd'
import {
  FileTextOutlined,
  SettingOutlined,
  EditOutlined,
  DownloadOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  BookOutlined,
  DeleteOutlined,
  EyeOutlined,
  MenuOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { articleService, literatureReviewService, type LiteratureReview } from '@/services'
import type { Article } from '@/types'
import { ReviewOutlineEditor } from '@/components/review'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps
const { Option } = Select

const LiteratureReviewPage: React.FC = () => {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [selectedArticles, setSelectedArticles] = useState<string[]>([])
  const [generating, setGenerating] = useState(false)
  const [taskId, setTaskId] = useState<string>()
  const [reviewResult, setReviewResult] = useState<LiteratureReview | null>(null)
  const [exportModalVisible, setExportModalVisible] = useState(false)

  // 配置选项
  const [focusArea, setFocusArea] = useState('general')
  const [outputLength, setOutputLength] = useState('medium')
  const [includeCitations, setIncludeCitations] = useState(true)
  const [includeReferences, setIncludeReferences] = useState(true)

  // 获取文献库数据
  const { data: libraryData, isLoading } = useQuery({
    queryKey: ['libraryForReview'],
    queryFn: () => articleService.getLibrary(),
  })

  const articles = (libraryData?.data as { items: Article[] })?.items || []

  // 轮询任务状态
  useEffect(() => {
    if (!taskId || !generating) return

    const poll = async () => {
      try {
        const result = await literatureReviewService.waitForCompletion(taskId, {
          onProgress: (task) => {
            console.log('Progress:', task.progress, task.current_step)
          },
        })
        setReviewResult(result)
        setGenerating(false)
        setCurrentStep(3)
        message.success('综述生成成功！')
      } catch (error) {
        setGenerating(false)
        message.error(error instanceof Error ? error.message : '生成失败')
      }
    }

    poll()
  }, [taskId, generating])

  const handleArticleSelect = (articleId: string, checked: boolean) => {
    if (checked) {
      if (selectedArticles.length >= 50) {
        message.warning('最多选择50篇文献')
        return
      }
      setSelectedArticles([...selectedArticles, articleId])
    } else {
      setSelectedArticles(selectedArticles.filter((id) => id !== articleId))
    }
  }

  const handleGenerate = async () => {
    if (selectedArticles.length < 2) {
      message.warning('请至少选择2篇文献')
      return
    }

    setGenerating(true)
    try {
      const { task_id } = await literatureReviewService.generate({
        article_ids: selectedArticles,
        focus_area: focusArea as any,
        output_length: outputLength as any,
        include_citations: includeCitations,
        include_references: includeReferences,
      })
      setTaskId(task_id)
      setCurrentStep(2)
    } catch (error) {
      setGenerating(false)
      message.error('生成失败：' + (error instanceof Error ? error.message : '未知错误'))
    }
  }

  const handleExport = async (format: 'markdown' | 'docx' | 'pdf') => {
    if (!taskId) return
    try {
      const { content, filename } = await literatureReviewService.exportReview(taskId, format)
      // 下载文件
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
      message.success('导出成功')
      setExportModalVisible(false)
    } catch (error) {
      message.error('导出失败')
    }
  }

  const steps = [
    { title: '选择文献', icon: <BookOutlined /> },
    { title: '配置选项', icon: <SettingOutlined /> },
    { title: '生成综述', icon: <EditOutlined /> },
    { title: '查看结果', icon: <FileTextOutlined /> },
  ]

  const renderArticleSelection = () => (
    <div>
      <Alert
        message="请选择2-50篇相关文献用于生成综述"
        description={`已选择 ${selectedArticles.length} 篇文献`}
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {isLoading ? (
        <div>加载中...</div>
      ) : articles.length === 0 ? (
        <Empty description="暂无文献，请先导入或搜索文献" />
      ) : (
        <List
          bordered
          dataSource={articles}
          style={{ maxHeight: 500, overflow: 'auto' }}
          renderItem={(article) => (
            <List.Item>
              <Checkbox
                checked={selectedArticles.includes(article.id)}
                onChange={(e) => handleArticleSelect(article.id, e.target.checked)}
              >
                <Space direction="vertical" style={{ marginLeft: 8 }}>
                  <Text strong>{article.title}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {article.authors?.map((a) => a.name).join(', ')} ·{' '}
                    {article.publicationYear}
                  </Text>
                </Space>
              </Checkbox>
            </List.Item>
          )}
        />
      )}

      <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={() => navigate('/library')}>前往文献库导入</Button>
        <Button
          type="primary"
          disabled={selectedArticles.length < 2}
          onClick={() => setCurrentStep(1)}
        >
          下一步 <ArrowRightOutlined />
        </Button>
      </div>
    </div>
  )

  const renderConfiguration = () => (
    <div>
      <Card title="综述配置" style={{ marginBottom: 16 }}>
        <Descriptions column={1} bordered>
          <Descriptions.Item label="已选文献数量">{selectedArticles.length} 篇</Descriptions.Item>
        </Descriptions>

        <Divider />

        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Text strong>综述聚焦领域</Text>
            <Radio.Group
              value={focusArea}
              onChange={(e) => setFocusArea(e.target.value)}
              style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8 }}
            >
              <Radio value="general">综合综述 - 全面概括研究领域</Radio>
              <Radio value="methodology">方法论综述 - 聚焦研究方法</Radio>
              <Radio value="findings">研究发现综述 - 总结主要发现</Radio>
              <Radio value="trends">研究趋势综述 - 分析发展趋势</Radio>
              <Radio value="gaps">研究空白综述 - 识别研究缺口</Radio>
            </Radio.Group>
          </div>

          <div>
            <Text strong>输出长度</Text>
            <Select
              value={outputLength}
              onChange={setOutputLength}
              style={{ width: 200, marginTop: 8, display: 'block' }}
            >
              <Option value="short">短篇 (~1000字)</Option>
              <Option value="medium">中篇 (~3000字)</Option>
              <Option value="long">长篇 (~5000字)</Option>
            </Select>
          </div>

          <div>
            <Text strong>其他选项</Text>
            <Space direction="vertical" style={{ marginTop: 8 }}>
              <Checkbox
                checked={includeCitations}
                onChange={(e) => setIncludeCitations(e.target.checked)}
              >
                包含引用标注
              </Checkbox>
              <Checkbox
                checked={includeReferences}
                onChange={(e) => setIncludeReferences(e.target.checked)}
              >
                包含参考文献列表
              </Checkbox>
            </Space>
          </div>
        </Space>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={() => setCurrentStep(0)}>
          <ArrowLeftOutlined /> 上一步
        </Button>
        <Button type="primary" onClick={handleGenerate} loading={generating}>
          开始生成
        </Button>
      </div>
    </div>
  )

  const renderGenerating = () => (
    <div style={{ textAlign: 'center', padding: 40 }}>
      <Progress type="circle" percent={generating ? undefined : 100} status="active" />
      <Title level={4} style={{ marginTop: 24 }}>
        {generating ? 'AI正在生成综述...' : '生成完成'}
      </Title>
      <Paragraph type="secondary">
        {generating
          ? '正在分析文献、识别主题、生成内容，请耐心等待'
          : '综述已生成完毕'}
      </Paragraph>
    </div>
  )

  const renderResult = () => {
    if (!reviewResult) return null

    // 转换sections为outline格式
    const outlineData = reviewResult.sections.map((section, idx) => ({
      id: `section_${idx}`,
      title: section.title,
      content: section.content,
      level: 1,
      wordCount: section.content?.length || 0,
      targetWordCount: Math.floor(reviewResult.word_count / reviewResult.sections.length),
      subsections: section.subsections?.map((sub, subIdx) => ({
        id: `subsection_${idx}_${subIdx}`,
        title: sub.title,
        content: sub.content,
        level: 2,
        wordCount: sub.content?.length || 0,
      })),
    }))

    return (
      <div>
        <Card
          title={
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <span>{reviewResult.title}</span>
            </Space>
          }
          extra={
            <Space>
              <Tag>{reviewResult.word_count} 字</Tag>
              <Tag>{reviewResult.metadata.article_count} 篇文献</Tag>
              <Button type="primary" icon={<DownloadOutlined />} onClick={() => setExportModalVisible(true)}>
                导出
              </Button>
            </Space>
          }
        >
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 大纲编辑器 */}
            <ReviewOutlineEditor
              outline={outlineData}
              onChange={(newOutline) => {
                // 可以在这里处理大纲变化
                console.log('Outline updated:', newOutline)
              }}
              totalWordCount={reviewResult.word_count}
              targetWordCount={reviewResult.output_length === 'short' ? 1000 : reviewResult.output_length === 'long' ? 5000 : 3000}
            />

            <Card title="摘要" size="small">
              <Paragraph>{reviewResult.abstract}</Paragraph>
            </Card>

            {reviewResult.sections.map((section, idx) => (
              <Card key={idx} title={section.title} size="small">
                <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{section.content}</Paragraph>
              </Card>
            ))}

            {reviewResult.research_gaps.length > 0 && (
              <Card title="研究空白" size="small">
                <ul>
                  {reviewResult.research_gaps.map((gap, idx) => (
                    <li key={idx}>{gap}</li>
                  ))}
                </ul>
              </Card>
            )}

            {reviewResult.future_directions.length > 0 && (
              <Card title="未来研究方向" size="small">
                <ul>
                  {reviewResult.future_directions.map((direction, idx) => (
                    <li key={idx}>{direction}</li>
                  ))}
                </ul>
              </Card>
            )}

            {reviewResult.references.length > 0 && (
              <Card title="参考文献" size="small">
                <ol>
                  {reviewResult.references.map((ref, idx) => (
                    <li key={idx} style={{ marginBottom: 8 }}>
                      {ref.authors.join(', ')}. {ref.title}. {ref.journal} {ref.year}.
                    </li>
                  ))}
                </ol>
              </Card>
            )}
          </Space>
        </Card>

        <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between' }}>
          <Button onClick={() => setCurrentStep(0)}>重新生成</Button>
          <Button type="primary" onClick={() => navigate('/papers/new')}>
            应用到论文
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>
        <FileTextOutlined /> 文献综述生成
      </Title>

      <Steps current={currentStep} style={{ marginBottom: 24 }}>
        {steps.map((step) => (
          <Step key={step.title} title={step.title} icon={step.icon} />
        ))}
      </Steps>

      <Card>
        {currentStep === 0 && renderArticleSelection()}
        {currentStep === 1 && renderConfiguration()}
        {currentStep === 2 && renderGenerating()}
        {currentStep === 3 && renderResult()}
      </Card>

      {/* 导出模态框 */}
      <Modal
        title="导出综述"
        open={exportModalVisible}
        onCancel={() => setExportModalVisible(false)}
        footer={null}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button block onClick={() => handleExport('markdown')}>
            导出为 Markdown
          </Button>
          <Button block onClick={() => handleExport('docx')} disabled>
            导出为 Word (开发中)
          </Button>
          <Button block onClick={() => handleExport('pdf')} disabled>
            导出为 PDF (开发中)
          </Button>
        </Space>
      </Modal>
    </div>
  )
}

export default LiteratureReviewPage
