/**
 * PDF文献分析面板
 * 提供翻译、总结、关联性分析等功能
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Space,
  Typography,
  Spin,
  Alert,
  Tag,
  Divider,
  Progress,
  Collapse,
  message,
  Tooltip,
  Tabs,
  Empty
} from 'antd'
import {
  TranslationOutlined,
  FileTextOutlined,
  BulbOutlined,
  LinkOutlined,
  ReadOutlined,
  GlobalOutlined,
  CheckCircleOutlined,
  StarOutlined,
  BookOutlined
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { pdfAnalysisService, type PDFAnalysisResult, type TranslationResult } from '@/services/pdfAnalysisService'
import type { Article } from '@/types'
import styles from './PDFAnalysisPanel.module.css'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse
const { TabPane } = Tabs

interface PDFAnalysisPanelProps {
  article: Article
  userTopic?: string
  selectedText?: string
  pdfContent?: string
  visible: boolean
  onClose: () => void
}

const PDFAnalysisPanel: React.FC<PDFAnalysisPanelProps> = ({
  article,
  userTopic,
  selectedText,
  pdfContent,
  visible,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState('summary')
  const [analysis, setAnalysis] = useState<PDFAnalysisResult | null>(null)
  const [translation, setTranslation] = useState<TranslationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [translating, setTranslating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [translatedSegments, setTranslatedSegments] = useState<Record<string, string>>({})

  // 分析文献
  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await pdfAnalysisService.analyzeArticle(article, userTopic, pdfContent)
      setAnalysis(result)
      message.success('文献分析完成')
    } catch (err: any) {
      setError(err.message || '分析失败')
      message.error('文献分析失败')
    } finally {
      setLoading(false)
    }
  }

  // 翻译选中内容
  const handleTranslateSelection = async () => {
    if (!selectedText) {
      message.warning('请先选中文本')
      return
    }
    setTranslating(true)
    try {
      const result = await pdfAnalysisService.translateContent(selectedText, 'zh')
      setTranslatedSegments(prev => ({
        ...prev,
        [selectedText]: result.translatedText
      }))
      message.success('翻译完成')
    } catch (err: any) {
      message.error('翻译失败')
    } finally {
      setTranslating(false)
    }
  }

  // 翻译整个文档摘要
  const handleTranslateAbstract = async () => {
    if (!article.abstract) {
      message.warning('该文献没有摘要')
      return
    }
    setActiveTab('translate')
    setTranslating(true)
    try {
      const result = await pdfAnalysisService.translateContent(article.abstract, 'zh')
      setTranslation(result)
    } catch (err: any) {
      message.error('翻译失败')
    } finally {
      setTranslating(false)
    }
  }

  // 自动分析（首次打开）
  useEffect(() => {
    if (visible && !analysis && !loading) {
      handleAnalyze()
    }
  }, [visible])

  // 渲染关联度评分
  const renderRelevanceScore = (score: number) => {
    let color = 'red'
    let label = '低'
    if (score >= 0.8) {
      color = 'green'
      label = '高'
    } else if (score >= 0.6) {
      color = 'blue'
      label = '中'
    }

    return (
      <div className={styles.relevanceScore}>
        <Progress
          type="circle"
          percent={Math.round(score * 100)}
          size={80}
          strokeColor={color}
          format={() => <Text strong>{label}</Text>}
        />
        <Text type="secondary" className={styles.scoreLabel}>关联度</Text>
      </div>
    )
  }

  if (!visible) return null

  return (
    <div className={styles.analysisPanel}>
      <Card
        title={
          <Space>
            <ReadOutlined />
            <span>文献智能分析</span>
          </Space>
        }
        extra={
          <Space>
            {selectedText && (
              <Button
                size="small"
                icon={<TranslationOutlined />}
                onClick={handleTranslateSelection}
                loading={translating}
              >
                翻译选中
              </Button>
            )}
            <Button size="small" onClick={onClose}>关闭</Button>
          </Space>
        }
        className={styles.card}
      >
        {error && (
          <Alert
            message="分析失败"
            description={error}
            type="error"
            showIcon
            action={
              <Button size="small" onClick={handleAnalyze}>重试</Button>
            }
            style={{ marginBottom: 16 }}
          />
        )}

        {loading ? (
          <div className={styles.loadingContainer}>
            <Spin size="large" />
            <Text type="secondary" style={{ marginTop: 16 }}>正在分析文献，请稍候...</Text>
          </div>
        ) : analysis ? (
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            className={styles.tabs}
          >
            <TabPane
              tab={
                <span>
                  <FileTextOutlined /> 摘要总结
                </span>
              }
              key="summary"
            >
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div className={styles.summarySection}>
                  <Title level={5}>📝 一句话总结</Title>
                  <Paragraph>{analysis.summary}</Paragraph>
                  <Button
                    size="small"
                    icon={<TranslationOutlined />}
                    onClick={handleTranslateAbstract}
                  >
                    翻译摘要
                  </Button>
                </div>

                <Divider />

                <div>
                  <Title level={5}>🎯 核心创新点</Title>
                  <ul className={styles.keyPointsList}>
                    {analysis.keyPoints.map((point, index) => (
                      <li key={index}>
                        <CheckCircleOutlined className={styles.checkIcon} />
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>

                <Divider />

                <div>
                  <Title level={5}>🔬 研究方法</Title>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {analysis.methodology}
                  </ReactMarkdown>
                </div>
              </Space>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <LinkOutlined /> 关联性分析
                </span>
              }
              key="relevance"
            >
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div className={styles.relevanceHeader}>
                  {renderRelevanceScore(analysis.relevance.score)}
                  <div className={styles.relevanceInfo}>
                    <Title level={5}>{userTopic ? `与"${userTopic}"的关联性` : '研究关联性'}</Title>
                    <Paragraph>{analysis.relevance.topicMatch}</Paragraph>
                  </div>
                </div>

                <Divider />

                <Collapse ghost>
                  <Panel header="💡 方法论启示" key="1">
                    <Paragraph>{analysis.relevance.methodologyInsight}</Paragraph>
                  </Panel>
                  <Panel header="📚 引用价值" key="2">
                    <Paragraph>{analysis.relevance.referenceValue}</Paragraph>
                  </Panel>
                  <Panel header="🔍 研究缺口与启发" key="3">
                    <Paragraph>{analysis.relevance.researchGap}</Paragraph>
                  </Panel>
                </Collapse>

                <Divider />

                <div className={styles.readingGuide}>
                  <Title level={5}>📖 阅读建议</Title>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {pdfAnalysisService.generateReadingGuide(analysis)}
                  </ReactMarkdown>
                </div>
              </Space>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <TranslationOutlined /> 翻译
                  {translatedSegments[selectedText || ''] && <Tag color="success">新</Tag>}
                </span>
              }
              key="translate"
            >
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                {selectedText ? (
                  <>
                    <div className={styles.originalText}>
                      <Title level={5}>📝 原文</Title>
                      <Paragraph className={styles.textBlock}>{selectedText}</Paragraph>
                    </div>

                    {translatedSegments[selectedText] ? (
                      <div className={styles.translatedText}>
                        <Title level={5}>🌐 译文</Title>
                        <Paragraph className={styles.textBlock}>
                          {translatedSegments[selectedText]}
                        </Paragraph>
                      </div>
                    ) : (
                      <Button
                        type="primary"
                        icon={<TranslationOutlined />}
                        onClick={handleTranslateSelection}
                        loading={translating}
                        block
                      >
                        翻译选中内容
                      </Button>
                    )}
                  </>
                ) : translation ? (
                  <div className={styles.translatedText}>
                    <Title level={5}>🌐 译文</Title>
                    <Paragraph className={styles.textBlock}>{translation.translatedText}</Paragraph>
                    <Text type="secondary" size="small">
                      检测语言: {translation.detectedLanguage} | 置信度: {translation.confidence}
                    </Text>
                  </div>
                ) : (
                  <Empty
                    description="选择PDF中的文本进行翻译"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  >
                    <Text type="secondary">在PDF阅读器中选中任意文本，点击"翻译选中"按钮</Text>
                  </Empty>
                )}
              </Space>
            </TabPane>
          </Tabs>
        ) : null}
      </Card>

      {/* 选中文本快速操作浮层 */}
      {selectedText && !visible && (
        <div className={styles.floatActions}>
          <Tooltip title="翻译">
            <Button
              type="primary"
              shape="circle"
              icon={<TranslationOutlined />}
              onClick={handleTranslateSelection}
              loading={translating}
            />
          </Tooltip>
        </div>
      )}
    </div>
  )
}

export default PDFAnalysisPanel
