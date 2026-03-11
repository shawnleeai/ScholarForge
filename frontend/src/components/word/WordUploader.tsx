/**
 * Word文档上传组件
 * 支持拖拽上传、格式识别、结构解析
 */

import React, { useState, useCallback } from 'react'
import {
  Upload,
  message,
  Card,
  Typography,
  Space,
  Tag,
  Button,
  Spin,
  Alert,
  Progress,
  Steps,
  Result,
  Descriptions,
  List,
  Badge,
  Collapse
} from 'antd'
import {
  InboxOutlined,
  FileWordOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  FileTextOutlined,
  ReadOutlined,
  FormatPainterOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  ReloadOutlined,
  ImportOutlined
} from '@ant-design/icons'
import {
  wordParserService,
  type WordParseResult,
  type DocumentType
} from '@/services/word/wordParser'
import styles from './WordUploader.module.css'

const { Dragger } = Upload
const { Title, Text, Paragraph } = Typography
const { Step } = Steps
const { Panel } = Collapse

interface WordUploaderProps {
  onUploadSuccess?: (result: WordParseResult) => void
  onImportComplete?: (articleData: any) => void
}

const documentTypeLabels: Record<DocumentType, { name: string; color: string }> = {
  thesis_proposal: { name: '开题报告', color: 'blue' },
  thesis: { name: '毕业论文', color: 'purple' },
  literature_review: { name: '文献综述', color: 'cyan' },
  research_report: { name: '研究报告', color: 'green' },
  journal_paper: { name: '期刊论文', color: 'orange' },
  conference_paper: { name: '会议论文', color: 'magenta' },
  other: { name: '其他文档', color: 'default' }
}

const WordUploader: React.FC<WordUploaderProps> = ({
  onUploadSuccess,
  onImportComplete
}) => {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [parseResult, setParseResult] = useState<WordParseResult | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [importing, setImporting] = useState(false)

  const steps = [
    { title: '上传文档', icon: <FileWordOutlined /> },
    { title: '解析结构', icon: <ReadOutlined /> },
    { title: '格式校验', icon: <FormatPainterOutlined /> },
    { title: '导入完成', icon: <CheckCircleOutlined /> }
  ]

  const handleUpload = useCallback(async (file: File) => {
    // 验证文件类型
    if (!file.name.match(/\.(docx|doc)$/i)) {
      message.error('只支持Word文档(.docx, .doc)')
      return false
    }

    // 验证文件大小 (20MB)
    if (file.size > 20 * 1024 * 1024) {
      message.error('文件大小不能超过20MB')
      return false
    }

    setUploading(true)
    setProgress(0)
    setCurrentStep(0)

    // 模拟上传进度
    const uploadInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(uploadInterval)
          return 90
        }
        return prev + 10
      })
    }, 200)

    try {
      // 解析文档
      setCurrentStep(1)
      const result = await wordParserService.parseDocument(file)

      clearInterval(uploadInterval)
      setProgress(100)

      if (result.success) {
        setCurrentStep(2)
        setParseResult(result)
        message.success('文档解析成功')
        onUploadSuccess?.(result)

        // 如果验证通过，自动进入下一步
        if (result.structureValidation?.isValid) {
          setTimeout(() => setCurrentStep(3), 500)
        }
      } else {
        message.error(result.error || '解析失败')
      }
    } catch (error) {
      message.error('上传失败')
    } finally {
      setUploading(false)
    }

    return false // 阻止默认上传
  }, [onUploadSuccess])

  const handleImport = async () => {
    if (!parseResult?.document) return

    setImporting(true)
    try {
      // 模拟导入过程
      await new Promise(r => setTimeout(r, 1000))

      const articleData = wordParserService.convertToArticle(
        parseResult.document,
        'current_user_id'
      )

      message.success('文档导入成功')
      onImportComplete?.(articleData)
      setCurrentStep(3)
    } catch (error) {
      message.error('导入失败')
    } finally {
      setImporting(false)
    }
  }

  const handleReset = () => {
    setParseResult(null)
    setCurrentStep(0)
    setProgress(0)
  }

  // 渲染上传界面
  const renderUploadStep = () => (
    <Dragger
      accept=".doc,.docx"
      beforeUpload={handleUpload}
      showUploadList={false}
      disabled={uploading}
    >
      <div className={styles.uploadArea}>
        {uploading ? (
          <Space direction="vertical" size="large">
            <Progress type="circle" percent={progress} status="active" />
            <Text type="secondary">正在上传和解析文档...请稍候</Text>
          </Space>
        ) : (
          <>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽Word文档到此处上传</p>
            <p className="ant-upload-hint">
              支持 .doc 和 .docx 格式，文件大小不超过20MB
            </p>
          </>
        )}
      </div>
    </Dragger>
  )

  // 渲染解析结果
  const renderParseResult = () => {
    if (!parseResult?.document) return null

    const { document, documentType, matchedTemplate, structureValidation } = parseResult
    const typeInfo = documentType ? documentTypeLabels[documentType] : null

    return (
      <div className={styles.parseResult}>
        <Alert
          message={
            <Space>
              <FileTextOutlined />
              <span>识别为：{typeInfo?.name || '未知文档类型'}</span>
              {typeInfo && <Tag color={typeInfo.color}>{typeInfo.name}</Tag>}
            </Space>
          }
          description={matchedTemplate?.description}
          type="info"
          showIcon
          action={
            <Button size="small" icon={<ReloadOutlined />} onClick={handleReset}>
              重新上传
            </Button>
          }
        />

        <Card title="文档结构" className={styles.structureCard}>
          <Descriptions column={2}>
            <Descriptions.Item label="文档标题">{document.title}</Descriptions.Item>
            <Descriptions.Item label="总章节数">{document.headings.length}</Descriptions.Item>
            <Descriptions.Item label="一级标题">
              {document.headings.filter(h => h.level === 1).length} 个
            </Descriptions.Item>
            <Descriptions.Item label="二级标题">
              {document.headings.filter(h => h.level === 2).length} 个
            </Descriptions.Item>
          </Descriptions>

          <Divider orientation="left">章节结构</Divider>

          <List
            size="small"
            dataSource={document.headings.slice(0, 10)}
            renderItem={item => (
              <List.Item>
                <Space>
                  <Tag color={item.level === 1 ? 'blue' : item.level === 2 ? 'green' : 'default'}>
                    {item.level === 1 ? '一级' : item.level === 2 ? '二级' : '三级'}
                  </Tag>
                  <Text>{item.text}</Text>
                </Space>
              </List.Item>
            )}
          />
          {document.headings.length > 10 && (
            <Text type="secondary" className={styles.moreText}>
              还有 {document.headings.length - 10} 个章节...
            </Text>
          )}
        </Card>

        {document.abstract && (
          <Card title="摘要" className={styles.abstractCard}>
            <Paragraph ellipsis={{ rows: 3, expandable: true }}>
              {document.abstract}
            </Paragraph>          </Card>
        )}

        {structureValidation && (
          <Card
            title="格式校验结果"
            className={styles.validationCard}
          >
            {structureValidation.isValid ? (
              <Alert
                message="文档结构完整，符合模板要求"
                type="success"
                showIcon
                icon={<CheckCircleOutlined />}
              />
            ) : (
              <Alert
                message="文档存在以下问题"
                type="warning"
                showIcon
                icon={<ExclamationCircleOutlined />}
              />
            )}

            {structureValidation.missingSections.length > 0 && (
              <>
                <Divider orientation="left">缺少的章节</Divider>
                <Space wrap>
                  {structureValidation.missingSections.map(section => (
                    <Tag key={section} color="red">{section}</Tag>
                  ))}
                </Space>
              </>
            )}

            {structureValidation.formatIssues.length > 0 && (
              <>
                <Divider orientation="left">格式建议</Divider>
                <List
                  dataSource={structureValidation.formatIssues}
                  renderItem={item => (
                    <List.Item>
                      <Alert
                        message={item.message}
                        description={item.suggestion}
                        type={item.type}
                        showIcon
                        banner
                      />
                    </List.Item>
                  )}
                />
              </>
            )}

            {structureValidation.suggestions.length > 0 && (
              <>
                <Divider orientation="left">优化建议</Divider>
                <List
                  dataSource={structureValidation.suggestions}
                  renderItem={item => (
                    <List.Item>
                      <Text>• {item}</Text>
                    </List.Item>
                  )}
                />
              </>
            )}
          </Card>
        )}

        <div className={styles.importActions}>
          <Button
            type="primary"
            size="large"
            icon={<ImportOutlined />}
            onClick={handleImport}
            loading={importing}
            block
          >
            导入到论文库
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.wordUploader}>
      <Card title="Word文档导入" className={styles.mainCard}>
        <Steps
          current={currentStep}
          items={steps}
          className={styles.steps}
        />

        <div className={styles.content}>
          {!parseResult ? renderUploadStep() : renderParseResult()}
        </div>
      </Card>
    </div>
  )
}

export default WordUploader
