/**
 * AI模板填充对话框
 * 使用AI智能生成模板各章节内容
 */

import React, { useState, useEffect } from 'react'
import {
  Modal,
  Form,
  Input,
  Select,
  Steps,
  Button,
  Card,
  List,
  Typography,
  Space,
  Tag,
  Progress,
  Alert,
  Collapse,
  Tooltip,
  Badge,
  Spin,
  Empty,
  Result,
  Tabs,
} from 'antd'
import {
  RobotOutlined,
  EditOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  BulbOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  DownloadOutlined,
  ReloadOutlined,
  ArrowRightOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons'
import styles from './AITemplateFill.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Option } = Select
const { Step } = Steps
const { Panel } = Collapse
const { TabPane } = Tabs

interface TemplateSection {
  id: string
  title: string
  required: boolean
  word_count_hint?: number
  ai_guidance?: string
}

interface PaperTemplate {
  id: string
  name: string
  type: string
  sections: TemplateSection[]
  language: string
}

interface SectionFillResult {
  section_id: string
  section_title: string
  content: string
  word_count: number
  confidence: number
  suggestions: string[]
  references: string[]
}

interface AITemplateFillProps {
  template: PaperTemplate | null
  visible: boolean
  onClose: () => void
  onComplete: (results: SectionFillResult[]) => void
}

const AITemplateFill: React.FC<AITemplateFillProps> = ({
  template,
  visible,
  onClose,
  onComplete,
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [form] = Form.useForm()
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [fillResults, setFillResults] = useState<SectionFillResult[]>([])
  const [currentGeneratingSection, setCurrentGeneratingSection] = useState<string>('')
  const [selectedSections, setSelectedSections] = useState<string[]>([])

  useEffect(() => {
    if (visible && template) {
      // 默认选中所有支持AI的必需章节
      const aiSupported = template.sections
        .filter((s) => s.required && s.ai_guidance)
        .map((s) => s.id)
      setSelectedSections(aiSupported)
      setCurrentStep(0)
      setFillResults([])
      setGenerationProgress(0)
      form.resetFields()
    }
  }, [visible, template])

  if (!template) return null

  const steps = [
    {
      title: '基本信息',
      icon: <EditOutlined />,
      description: '填写论文信息',
    },
    {
      title: '选择章节',
      icon: <FileTextOutlined />,
      description: '选择要生成的章节',
    },
    {
      title: 'AI生成',
      icon: <RobotOutlined />,
      description: '智能生成内容',
    },
    {
      title: '完成',
      icon: <CheckCircleOutlined />,
      description: '查看结果',
    },
  ]

  const handleNext = async () => {
    if (currentStep === 0) {
      const values = await form.validateFields()
      if (values) {
        setCurrentStep(1)
      }
    } else if (currentStep === 1) {
      if (selectedSections.length === 0) {
        return
      }
      setCurrentStep(2)
      await startGeneration()
    } else if (currentStep === 3) {
      onComplete(fillResults)
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const startGeneration = async () => {
    setIsGenerating(true)
    setGenerationProgress(0)

    const sectionsToGenerate = template.sections.filter((s) =>
      selectedSections.includes(s.id)
    )

    const results: SectionFillResult[] = []

    // 模拟逐个生成章节
    for (let i = 0; i < sectionsToGenerate.length; i++) {
      const section = sectionsToGenerate[i]
      setCurrentGeneratingSection(section.title)

      // 模拟生成延迟
      await new Promise((resolve) => setTimeout(resolve, 2000))

      const result = await generateSectionContent(section)
      results.push(result)
      setFillResults([...results])

      const progress = ((i + 1) / sectionsToGenerate.length) * 100
      setGenerationProgress(progress)
    }

    setIsGenerating(false)
    setCurrentStep(3)
  }

  const generateSectionContent = async (
    section: TemplateSection
  ): Promise<SectionFillResult> => {
    const values = form.getFieldsValue()

    // 这里应该调用API
    // 模拟返回结果
    const mockContent = generateMockContent(section, values)

    return {
      section_id: section.id,
      section_title: section.title,
      content: mockContent,
      word_count: mockContent.length,
      confidence: 0.75 + Math.random() * 0.2,
      suggestions: [
        `建议检查${section.title}的逻辑连贯性`,
        '可添加更多参考文献支撑',
        '注意与前后章节的衔接',
      ],
      references: ['Smith, 2023', 'Zhang et al., 2024'],
    }
  }

  const generateMockContent = (section: TemplateSection, values: any) => {
    return `【AI生成的${section.title}示例内容】

论文标题：${values.paper_title || '未命名论文'}

本章节由AI根据您提供的信息智能生成。在实际部署环境中，这里将包含由大语言模型生成的完整学术内容，包括：

1. 与论文主题相关的详细论述
2. 符合学术规范的表达方式
3. 适当的文献引用标注
4. 逻辑清晰的段落结构

【AI写作指导】
${section.ai_guidance || '暂无特定指导'}

【建议字数】
${section.word_count_hint || '未指定'}字

---
注意：以上内容仅为演示。在实际使用时，系统将调用AI服务生成真正的学术内容。`
  }

  const getStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Form
            form={form}
            layout="vertical"
            className={styles.form}
            initialValues={{
              language: template.language,
              tone: 'academic',
            }}
          >
            <Form.Item
              name="paper_title"
              label="论文标题"
              rules={[{ required: true, message: '请输入论文标题' }]}
            >
              <Input placeholder="请输入论文标题" />
            </Form.Item>

            <Form.Item name="paper_abstract" label="论文摘要（可选）">
              <TextArea
                rows={4}
                placeholder="如果已有摘要，可在此处填写，AI将参考此内容进行生成"
              />
            </Form.Item>

            <Form.Item name="paper_keywords" label="关键词">
              <Select
                mode="tags"
                placeholder="输入关键词后按回车"
                tokenSeparators={[',']}
              />
            </Form.Item>

            <Form.Item name="research_area" label="研究领域">
              <Input placeholder="例如：计算机视觉、自然语言处理等" />
            </Form.Item>

            <Form.Item name="target_audience" label="目标读者">
              <Input placeholder="例如：期刊审稿人、会议评委等" />
            </Form.Item>

            <Form.Item name="tone" label="写作风格">
              <Select>
                <Option value="academic">学术正式</Option>
                <Option value="formal">正式</Option>
                <Option value="neutral">中性</Option>
              </Select>
            </Form.Item>

            <Form.Item name="additional_context" label="补充信息（可选）">
              <TextArea
                rows={3}
                placeholder="任何有助于AI理解您需求的补充信息"
              />
            </Form.Item>
          </Form>
        )

      case 1:
        return (
          <div className={styles.sectionSelection}>
            <Alert
              message="选择要AI生成的章节"
              description="系统将为您选中的章节生成初始内容。建议先生成主要章节，再根据需要补充其他章节。"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Card title="必需章节" size="small">
              <List
                dataSource={template.sections.filter((s) => s.required)}
                renderItem={(section) => (
                  <List.Item
                    actions={[
                      section.ai_guidance ? (
                        <Tooltip title="支持AI生成">
                          <RobotOutlined style={{ color: '#52c41a' }} />
                        </Tooltip>
                      ) : (
                        <Tooltip title="暂不支持AI生成">
                          <InfoCircleOutlined style={{ color: '#999' }} />
                        </Tooltip>
                      ),
                    ]}
                  >
                    <Checkbox
                      checked={selectedSections.includes(section.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedSections([...selectedSections, section.id])
                        } else {
                          setSelectedSections(
                            selectedSections.filter((id) => id !== section.id)
                          )
                        }
                      }}
                      disabled={!section.ai_guidance}
                    >
                      <Space>
                        <Text strong={section.required}>{section.title}</Text>
                        {section.word_count_hint && (
                          <Tag size="small" color="blue">
                            {section.word_count_hint}字
                          </Tag>
                        )}
                        {section.required && (
                          <Tag size="small" color="red">
                            必需
                          </Tag>
                        )}
                      </Space>
                    </Checkbox>
                  </List.Item>
                )}
              />
            </Card>

            {template.sections.filter((s) => !s.required).length > 0 && (
              <Card title="可选章节" size="small" style={{ marginTop: 16 }}>
                <List
                  dataSource={template.sections.filter((s) => !s.required)}
                  renderItem={(section) => (
                    <List.Item
                      actions={[
                        section.ai_guidance ? (
                          <RobotOutlined style={{ color: '#52c41a' }} />
                        ) : (
                          <InfoCircleOutlined style={{ color: '#999' }} />
                        ),
                      ]}
                    >
                      <Checkbox
                        checked={selectedSections.includes(section.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedSections([...selectedSections, section.id])
                          } else {
                            setSelectedSections(
                              selectedSections.filter((id) => id !== section.id)
                            )
                          }
                        }}
                        disabled={!section.ai_guidance}
                      >
                        <Space>
                          <Text>{section.title}</Text>
                          {section.word_count_hint && (
                            <Tag size="small" color="blue">
                              {section.word_count_hint}字
                            </Tag>
                          )}
                        </Space>
                      </Checkbox>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            <Alert
              message={`已选择 ${selectedSections.length} 个章节`}
              type={selectedSections.length > 0 ? 'success' : 'warning'}
              showIcon
              style={{ marginTop: 16 }}
            />
          </div>
        )

      case 2:
        return (
          <div className={styles.generationStep}>
            <div className={styles.generationStatus}>
              {isGenerating ? (
                <>
                  <Spin
                    indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />}
                  />
                  <Title level={4} style={{ marginTop: 24 }}>
                    正在生成 {currentGeneratingSection}
                  </Title>
                  <Progress
                    percent={Math.round(generationProgress)}
                    status="active"
                    style={{ width: 300, marginTop: 16 }}
                  />
                  <Text type="secondary" style={{ marginTop: 16 }}>
                    AI正在根据您的论文信息生成内容，请稍候...
                  </Text>
                </>
              ) : (
                <Empty description="点击开始生成" />
              )}
            </div>

            {fillResults.length > 0 && (
              <div className={styles.previewResults}>
                <Title level={5}>已生成章节</Title>
                <List
                  dataSource={fillResults}
                  renderItem={(result) => (
                    <List.Item
                      actions={[
                        <Tag color={result.confidence > 0.8 ? 'green' : 'orange'}>
                          置信度: {Math.round(result.confidence * 100)}%
                        </Tag>,
                      ]}
                    >
                      <List.Item.Meta
                        title={result.section_title}
                        description={`${result.word_count} 字`}
                      />
                    </List.Item>
                  )}
                />
              </div>
            )}
          </div>
        )

      case 3:
        return (
          <div className={styles.resultStep}>
            <Result
              status="success"
              title="生成完成！"
              subTitle={`成功生成 ${fillResults.length} 个章节，总计 ${fillResults.reduce(
                (sum, r) => sum + r.word_count,
                0
              )} 字`}
            />

            <Tabs defaultActiveKey="content">
              <TabPane tab="生成内容" key="content">
                <Collapse accordion>
                  {fillResults.map((result) => (
                    <Panel
                      header={
                        <Space>
                          <Text strong>{result.section_title}</Text>
                          <Tag>{result.word_count}字</Tag>
                          <Tag color={result.confidence > 0.8 ? 'green' : 'orange'}>
                            置信度 {Math.round(result.confidence * 100)}%
                          </Tag>
                        </Space>
                      }
                      key={result.section_id}
                    >
                      <div className={styles.sectionContent}>
                        <pre>{result.content}</pre>
                      </div>

                      {result.suggestions.length > 0 && (
                        <Alert
                          message="改进建议"
                          description={
                            <ul>
                              {result.suggestions.map((s, i) => (
                                <li key={i}>{s}</li>
                              ))}
                            </ul>
                          }
                          type="warning"
                          showIcon
                          icon={<BulbOutlined />}
                          style={{ marginTop: 16 }}
                        />
                      )}

                      {result.references.length > 0 && (
                        <div className={styles.references}>
                          <Text type="secondary">参考文献：</Text>
                          <Space wrap>
                            {result.references.map((ref, i) => (
                              <Tag key={i}>{ref}</Tag>
                            ))}
                          </Space>
                        </div>
                      )}
                    </Panel>
                  ))}
                </Collapse>
              </TabPane>

              <TabPane tab="改进建议" key="suggestions">
                <List
                  dataSource={fillResults.filter((r) => r.suggestions.length > 0)}
                  renderItem={(result) => (
                    <Card size="small" title={result.section_title} style={{ marginBottom: 16 }}>
                      <ul>
                        {result.suggestions.map((suggestion, i) => (
                          <li key={i}>
                            <Text>{suggestion}</Text>
                          </li>
                        ))}
                      </ul>
                    </Card>
                  )}
                />
              </TabPane>
            </Tabs>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <Modal
      title={
        <Space>
          <RobotOutlined style={{ color: '#1890ff' }} />
          <span>AI 智能填充 - {template.name}</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={
        <div className={styles.footer}>
          <Button onClick={onClose}>取消</Button>
          {currentStep > 0 && currentStep < 3 && (
            <Button onClick={handlePrev} icon={<ArrowLeftOutlined />}>
              上一步
            </Button>
          )}
          {currentStep < 3 && (
            <Button
              type="primary"
              onClick={handleNext}
              disabled={currentStep === 1 && selectedSections.length === 0}
              icon={<ArrowRightOutlined />}
            >
              {currentStep === 2 ? '开始生成' : '下一步'}
            </Button>
          )}
          {currentStep === 3 && (
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => setCurrentStep(0)}>
                重新生成
              </Button>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() => onComplete(fillResults)}
              >
                应用内容
              </Button>
            </Space>
          )}
        </div>
      }
      className={styles.aiFillModal}
    >
      <Steps current={currentStep} size="small" style={{ marginBottom: 24 }}>
        {steps.map((step) => (
          <Step
            key={step.title}
            title={step.title}
            description={step.description}
            icon={step.icon}
          />
        ))}
      </Steps>

      <div className={styles.stepContent}>{getStepContent()}</div>
    </Modal>
  )
}

// 简化版Checkbox组件
const Checkbox: React.FC<any> = ({ children, checked, onChange, disabled }) => {
  return (
    <label
      style={{
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        disabled={disabled}
      />
      {children}
    </label>
  )
}

export default AITemplateFill
