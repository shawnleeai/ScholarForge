/**
 * 导出弹窗组件
 * 支持多种格式导出，显示导出进度
 */

import React, { useState } from 'react'
import {
  Modal,
  Form,
  Input,
  Radio,
  Checkbox,
  Button,
  Space,
  Progress,
  Typography,
  Divider,
  Alert,
} from 'antd'
import {
  FileWordOutlined,
  FilePdfOutlined,
  FileMarkdownOutlined,
  FileTextOutlined,
  DownloadOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'

import { paperService } from '@/services'
import styles from './Export.module.css'

const { Text } = Typography

interface ExportModalProps {
  visible: boolean
  paperId: string
  paperTitle?: string
  onClose: () => void
}

type ExportStatus = 'idle' | 'exporting' | 'success' | 'error'

const ExportModal: React.FC<ExportModalProps> = ({
  visible,
  paperId,
  paperTitle,
  onClose,
}) => {
  const [form] = Form.useForm()
  const [status, setStatus] = useState<ExportStatus>('idle')
  const [progress, setProgress] = useState(0)
  const [downloadUrl, setDownloadUrl] = useState<string>()
  const [error, setError] = useState<string>()

  const formatOptions = [
    {
      value: 'docx',
      label: 'Word 文档',
      icon: <FileWordOutlined style={{ color: '#2b579a' }} />,
      description: 'Microsoft Word 格式，适合继续编辑',
    },
    {
      value: 'pdf',
      label: 'PDF 文档',
      icon: <FilePdfOutlined style={{ color: '#d93025' }} />,
      description: '便携式文档格式，适合分享和打印',
    },
    {
      value: 'md',
      label: 'Markdown',
      icon: <FileMarkdownOutlined style={{ color: '#083fa1' }} />,
      description: '纯文本格式，适合版本控制和在线发布',
    },
    {
      value: 'tex',
      label: 'LaTeX',
      icon: <FileTextOutlined style={{ color: '#008080' }} />,
      description: '学术排版格式，适合期刊投稿',
    },
  ]

  const handleExport = async () => {
    try {
      const values = await form.validateFields()
      setStatus('exporting')
      setProgress(0)
      setError(undefined)

      // 模拟导出进度
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return prev
          }
          return prev + 10
        })
      }, 200)

      const response = await paperService.exportPaper(paperId, values.format)

      clearInterval(progressInterval)
      setProgress(100)

      // 使用 download_url 或 downloadUrl (兼容两种格式)
      const url = (response.data as { download_url?: string; downloadUrl?: string })?.download_url
        || (response.data as { download_url?: string; downloadUrl?: string })?.downloadUrl

      if (url) {
        setDownloadUrl(url)
        setStatus('success')
      }
    } catch (err: unknown) {
      setStatus('error')
      setError((err as Error).message || '导出失败，请重试')
    }
  }

  const handleDownload = () => {
    if (downloadUrl) {
      window.open(downloadUrl, '_blank')
    }
  }

  const handleClose = () => {
    setStatus('idle')
    setProgress(0)
    setDownloadUrl(undefined)
    setError(undefined)
    onClose()
  }

  const renderContent = () => {
    if (status === 'exporting') {
      return (
        <div className={styles.statusContent}>
          <LoadingOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <Text>正在导出文档...</Text>
          <Progress percent={progress} status="active" />
        </div>
      )
    }

    if (status === 'success') {
      return (
        <div className={styles.statusContent}>
          <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }} />
          <Text>导出成功！</Text>
          <Space>
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload}>
              下载文件
            </Button>
            <Button onClick={handleClose}>关闭</Button>
          </Space>
        </div>
      )
    }

    if (status === 'error') {
      return (
        <div className={styles.statusContent}>
          <Alert
            message="导出失败"
            description={error}
            type="error"
            showIcon
          />
          <Button onClick={() => setStatus('idle')}>重试</Button>
        </div>
      )
    }

    return (
      <Form
        form={form}
        layout="vertical"
        initialValues={{ format: 'docx', includeComments: false }}
      >
        <Form.Item label="导出格式" name="format" required>
          <Radio.Group className={styles.formatGroup}>
            {formatOptions.map((opt) => (
              <Radio.Button key={opt.value} value={opt.value} className={styles.formatOption}>
                <div className={styles.formatContent}>
                  <span className={styles.formatIcon}>{opt.icon}</span>
                  <span className={styles.formatLabel}>{opt.label}</span>
                </div>
              </Radio.Button>
            ))}
          </Radio.Group>
        </Form.Item>

        <Divider />

        <Form.Item label="导出选项">
          <Space direction="vertical">
            <Checkbox>包含批注和评论</Checkbox>
            <Checkbox>包含页眉页脚</Checkbox>
            <Checkbox>嵌入字体</Checkbox>
          </Space>
        </Form.Item>

        <Form.Item label="文件名" name="filename">
          <Input placeholder={paperTitle || '论文'} suffix=".docx" />
        </Form.Item>
      </Form>
    )
  }

  return (
    <Modal
      title={
        <Space>
          <DownloadOutlined />
          <span>导出论文</span>
        </Space>
      }
      open={visible}
      onCancel={handleClose}
      footer={
        status === 'idle' ? (
          <Space>
            <Button onClick={handleClose}>取消</Button>
            <Button type="primary" onClick={handleExport}>
              开始导出
            </Button>
          </Space>
        ) : null
      }
      width={520}
    >
      {renderContent()}
    </Modal>
  )
}

export default ExportModal
