/**
 * 智能文献推荐与Word自动排版组件
 * 根据写作上下文实时推荐文献，支持一键引用到Word
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  List,
  Tag,
  Badge,
  Tooltip,
  Empty,
  Spin,
  Select,
  Radio,
  Divider,
  Alert,
  Input,
  message,
  Popover,
  Avatar,
  Row,
  Col
} from 'antd'
import {
  FileWordOutlined,
  BookOutlined,
  LinkOutlined,
  CopyOutlined,
  ReloadOutlined,
  SettingOutlined,
  ExportOutlined,
  CheckCircleOutlined,
  ReadOutlined,
  ImportOutlined,
  FormatPainterOutlined,
  FileTextOutlined,
  PlusOutlined,
  EyeOutlined
} from '@ant-design/icons'
import {
  literatureRecommendationService,
  FORMAT_TEMPLATES,
  type SmartRecommendation,
  type FormatTemplate,
  type WritingContext
} from '@/services/literatureRecommendationService'
import styles from './SmartLiteratureRecommendation.module.css'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

interface SmartLiteratureRecommendationProps {
  paperId?: string
  currentSection?: string
  recentText?: string
}

const SmartLiteratureRecommendation: React.FC<SmartLiteratureRecommendationProps> = ({
  paperId = 'default_paper',
  currentSection = 'literature',
  recentText = ''
}) => {
  const [recommendations, setRecommendations] = useState<SmartRecommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<FormatTemplate>(FORMAT_TEMPLATES[0])
  const [citationStyle, setCitationStyle] = useState<'apa' | 'mla' | 'chicago' | 'gb7714'>('gb7714')
  const [contextInput, setContextInput] = useState(recentText)
  const [usedReferences, setUsedReferences] = useState<Set<string>>(new Set())
  const [showPreview, setShowPreview] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)

  // 分析上下文并获取推荐
  const analyzeAndRecommend = useCallback(async () => {
    if (!contextInput.trim()) {
      message.warning('请先输入写作内容')
      return
    }

    setLoading(true)
    try {
      // 分析上下文
      const context = literatureRecommendationService.analyzeContext(
        paperId,
        contextInput,
        currentSection
      )

      // 获取推荐
      const recs = await literatureRecommendationService.getSmartRecommendations(
        context,
        citationStyle,
        5
      )

      setRecommendations(recs)
      message.success(`为您推荐 ${recs.length} 篇相关文献`)
    } catch (error) {
      message.error('获取推荐失败')
    } finally {
      setLoading(false)
    }
  }, [contextInput, currentSection, paperId, citationStyle])

  // 插入Word
  const insertToWord = async (rec: SmartRecommendation) => {
    try {
      await literatureRecommendationService.insertToWord(rec)
      setUsedReferences(prev => new Set([...prev, rec.id]))
      message.success('已插入Word文档')
    } catch (error) {
      message.error('插入失败')
    }
  }

  // 复制引用
  const copyCitation = (rec: SmartRecommendation) => {
    navigator.clipboard.writeText(rec.inTextCitation)
    message.success('引用已复制')
  }

  // 复制参考文献
  const copyBibliography = (rec: SmartRecommendation) => {
    navigator.clipboard.writeText(rec.formattedBibliography)
    message.success('参考文献已复制')
  }

  // 导出全部参考文献
  const exportAllBibliography = () => {
    const bibliography = literatureRecommendationService.exportBibliography(recommendations)
    navigator.clipboard.writeText(bibliography)
    message.success('参考文献列表已复制到剪贴板')
  }

  // 应用格式模板
  const applyTemplate = () => {
    const instructions = literatureRecommendationService.generateWordFormattingInstructions(selectedTemplate)
    navigator.clipboard.writeText(instructions)
    message.success('格式设置说明已复制，请在Word中按说明设置')
  }

  // 生成推荐位置标签
  const getLocationLabel = (location?: string) => {
    const labels: Record<string, string> = {
      introduction: '引言',
      literature: '文献综述',
      methodology: '研究方法',
      discussion: '讨论',
      conclusion: '结论'
    }
    return labels[location || ''] || '文献综述'
  }

  return (
    <Card
      className={styles.smartRecommendation}
      title={
        <Space>
          <ReadOutlined />
          <span>智能文献推荐</span>
          {recommendations.length > 0 && (
            <Badge count={recommendations.length} style={{ backgroundColor: '#52c41a' }} />
          )}
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="导出参考文献列表">
            <Button
              icon={<ExportOutlined />}
              onClick={exportAllBibliography}
              disabled={recommendations.length === 0}
              size="small"
            >
              导出
            </Button>
          </Tooltip>
          <Tooltip title="应用格式模板">
            <Button
              icon={<FormatPainterOutlined />}
              onClick={applyTemplate}
              size="small"
            >
              格式
            </Button>
          </Tooltip>
        </Space>
      }
    >
      {/* 上下文输入区 */}
      <div className={styles.contextSection}>
        <Alert
          message="输入您的写作内容，AI将分析上下文并推荐相关文献"
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
        />

        <TextArea
          value={contextInput}
          onChange={e => setContextInput(e.target.value)}
          placeholder="粘贴您正在写作的内容，AI会分析主题、关键词，并推荐相关文献..."
          rows={4}
          className={styles.contextInput}
        />

        <div className={styles.contextControls}>
          <Space>
            <Text type="secondary">当前段落：</Text>
            <Select
              value={currentSection}
              size="small"
              style={{ width: 120 }}
              options={[
                { value: 'introduction', label: '引言' },
                { value: 'literature', label: '文献综述' },
                { value: 'methodology', label: '研究方法' },
                { value: 'discussion', label: '讨论' },
                { value: 'conclusion', label: '结论' }
              ]}
            />
          </Space>

          <Button
            type="primary"
            icon={<BookOutlined />}
            onClick={analyzeAndRecommend}
            loading={loading}
          >
            智能推荐
          </Button>
        </div>
      </div>

      <Divider />

      {/* 格式设置 */}
      <div className={styles.formatSection}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12}>
            <div>
              <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                引用格式
              </Text>
              <Radio.Group
                value={citationStyle}
                onChange={e => setCitationStyle(e.target.value)}
                buttonStyle="solid"
                size="small"
              >
                <Radio.Button value="gb7714">GB7714</Radio.Button>
                <Radio.Button value="apa">APA</Radio.Button>
                <Radio.Button value="mla">MLA</Radio.Button>
                <Radio.Button value="chicago">Chicago</Radio.Button>
              </Radio.Group>
            </div>
          </Col>

          <Col xs={24} sm={12}>
            <div>
              <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                排版模板
              </Text>
              <Select
                value={selectedTemplate.id}
                onChange={value => {
                  const template = FORMAT_TEMPLATES.find(t => t.id === value)
                  if (template) setSelectedTemplate(template)
                }}
                style={{ width: '100%' }}
                size="small"
                options={FORMAT_TEMPLATES.map(t => ({
                  value: t.id,
                  label: t.name
                }))}
              />
            </div>
          </Col>
        </Row>
      </div>

      <Divider />

      {/* 推荐列表 */}
      <div className={styles.recommendationList}>
        {loading ? (
          <div className={styles.loadingState}>
            <Spin size="large" />
            <Text type="secondary" style={{ marginTop: 16 }}>
              AI正在分析您的写作内容...
            </Text>
          </div>
        ) : recommendations.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="输入内容后点击智能推荐，获取相关文献"
          />
        ) : (
          <List
            dataSource={recommendations}
            renderItem={rec => (
              <List.Item
                className={styles.recommendationItem}
                actions={[
                  <Tooltip title="复制引用">
                    <Button
                      icon={<CopyOutlined />}
                      onClick={() => copyCitation(rec)}
                      size="small"
                    >
                      引用
                    </Button>
                  </Tooltip>,
                  <Tooltip title="插入Word">
                    <Button
                      type="primary"
                      icon={<FileWordOutlined />}
                      onClick={() => insertToWord(rec)}
                      disabled={usedReferences.has(rec.id)}
                      size="small"
                    >
                      {usedReferences.has(rec.id) ? '已插入' : '插入'}
                    </Button>
                  </Tooltip>
                ]}
              >
                <div className={styles.recommendationContent}>
                  <div className={styles.recommendationHeader}>
                    <Space>
                      <Avatar style={{ backgroundColor: '#1890ff' }}>
                        {rec.article.authors[0]?.charAt(0) || '?'}
                      </Avatar>
                      <div>
                        <Text strong className={styles.articleTitle}>
                          {rec.article.title}
                        </Text>
                        <div>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {rec.article.authors.join(', ')} · {rec.article.source} · {rec.article.publicationYear}
                          </Text>
                        </div>
                      </div>
                    </Space>
                  </div>

                  <Paragraph ellipsis={{ rows: 2 }} className={styles.abstract}>
                    {rec.article.abstract}
                  </Paragraph>

                  <div className={styles.recommendationMeta}>
                    <Space wrap size="small">
                      <Tag color="blue" icon={<CheckCircleOutlined />}>
                        相关度 {rec.relevanceScore}%
                      </Tag>
                      <Tag color="green">
                        推荐用于：{getLocationLabel(rec.suggestedLocation)}
                      </Tag>
                      {rec.article.citationCount && (
                        <Tag>被引 {rec.article.citationCount} 次</Tag>
                      )}
                    </Space>
                  </div>

                  {/* 引用预览 */}
                  <div className={styles.citationPreview}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      文内引用：{rec.inTextCitation}
                    </Text>
                  </div>

                  {/* 引用建议 */}
                  {rec.quoteSuggestion && (
                    <Popover
                      content={
                        <div style={{ maxWidth: 400 }}>
                          <Text style={{ fontSize: 12 }}>引用建议：</Text>
                          <Paragraph style={{ marginTop: 8, marginBottom: 0, fontSize: 12 }}>
                            {rec.quoteSuggestion}
                          </Paragraph>
                          <Button
                            type="link"
                            size="small"
                            icon={<CopyOutlined />}
                            onClick={() => {
                              navigator.clipboard.writeText(rec.quoteSuggestion || '')
                              message.success('已复制')
                            }}
                            style={{ padding: 0, marginTop: 8 }}
                          >
                            复制引用语
                          </Button>
                        </div>
                      }
                      title="引用建议"
                      trigger="click"
                    >
                      <Button type="link" size="small" icon={<EyeOutlined />} style={{ padding: 0 }}>
                        查看引用建议
                      </Button>
                    </Popover>
                  )}

                  {/* 参考文献格式预览 */}
                  {showPreview === rec.id && (
                    <div className={styles.bibliographyPreview}>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        参考文献格式：
                      </Text>
                      <Paragraph copyable style={{ fontSize: 11, marginBottom: 0 }}>
                        {rec.formattedBibliography}
                      </Paragraph>
                    </div>
                  )}

                  <Button
                    type="link"
                    size="small"
                    onClick={() => setShowPreview(showPreview === rec.id ? null : rec.id)}
                    style={{ padding: 0 }}
                  >
                    {showPreview === rec.id ? '隐藏' : '显示'}参考文献格式
                  </Button>
                </div>
              </List.Item>
            )}
          />
        )}
      </div>

      {/* 模板详情 */}
      {selectedTemplate && (
        <div className={styles.templateInfo}>
          <Divider orientation="left">
            <Text type="secondary" style={{ fontSize: 12 }}>
              当前格式模板：{selectedTemplate.name}
            </Text>
          </Divider>
          <Alert
            message={selectedTemplate.description}
            description={
              <Space direction="vertical" size="small" style={{ marginTop: 8 }}>
                <Text style={{ fontSize: 12 }}>
                  字体：{selectedTemplate.fontSettings.mainFont} {selectedTemplate.fontSettings.fontSize}pt
                </Text>
                <Text style={{ fontSize: 12 }}>
                  行距：{selectedTemplate.fontSettings.lineSpacing}倍
                </Text>
                <Text style={{ fontSize: 12 }}>
                  引用格式：{selectedTemplate.citationStyle.toUpperCase()}
                </Text>
              </Space>
            }
            type="info"
            showIcon
          />
        </div>
      )}
    </Card>
  )
}

export default SmartLiteratureRecommendation
