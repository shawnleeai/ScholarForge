/**
 * PDF上传组件
 * 支持拖拽上传、进度显示
 */

import React, { useState, useCallback } from 'react'
import { Upload, message, Progress, Card, Typography, Space, Tag } from 'antd'
import { InboxOutlined, FilePdfOutlined, CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons'
import { pdfService, type PDFParseTask } from '@/services'

const { Dragger } = Upload
const { Text, Title } = Typography

interface PDFUploaderProps {
  onUploadSuccess?: (taskId: string) => void
  onParseComplete?: (result: PDFParseTask) => void
}

export const PDFUploader: React.FC<PDFUploaderProps> = ({
  onUploadSuccess,
  onParseComplete,
}) => {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'parsing' | 'completed' | 'error'>('idle')
  const [taskInfo, setTaskInfo] = useState<PDFParseTask | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  const handleUpload = useCallback(async (file: File) => {
    // 验证文件类型
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      message.error('只支持PDF文件')
      return false
    }

    // 验证文件大小 (50MB)
    if (file.size > 50 * 1024 * 1024) {
      message.error('文件大小不能超过50MB')
      return false
    }

    setUploading(true)
    setStatus('uploading')
    setProgress(0)
    setErrorMsg('')

    // 模拟进度
    const progressInterval = setInterval(() => {
      setProgress(prev => Math.min(prev + 10, 90))
    }, 300)

    try {
      // 上传文件
      const task = await pdfService.upload(file, {
        enable_ai: true,
        extract_references: true,
        extract_figures: false,
      })

      clearInterval(progressInterval)
      setProgress(100)
      setTaskInfo(task)
      setStatus('parsing')

      message.success('上传成功，正在解析...')
      onUploadSuccess?.(task.task_id)

      // 等待解析完成
      const result = await pdfService.waitForCompletion(
        task.task_id,
        {
          interval: 2000,
          onProgress: (status) => {
            if (status === 'processing') {
              message.loading({ content: 'AI正在分析文献...', key: 'parsing', duration: 0 })
            }
          }
        }
      )

      message.destroy('parsing')
      setStatus('completed')
      message.success('解析完成！')
      onParseComplete?.(result as unknown as PDFParseTask)

    } catch (error) {
      clearInterval(progressInterval)
      setStatus('error')
      setErrorMsg(error instanceof Error ? error.message : '上传失败')
      message.error(error instanceof Error ? error.message : '上传失败')
    } finally {
      setUploading(false)
    }

    return false
  }, [onUploadSuccess, onParseComplete])

  const getStatusIcon = () => {
    switch (status) {
      case 'uploading':
        return <LoadingOutlined style={{ fontSize: 48, color: '#1890ff' }} />
      case 'parsing':
        return <LoadingOutlined style={{ fontSize: 48, color: '#52c41a' }} />
      case 'completed':
        return <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
      case 'error':
        return <FilePdfOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
      default:
        return <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'uploading':
        return '正在上传...'
      case 'parsing':
        return 'AI正在解析文献...'
      case 'completed':
        return '解析完成！'
      case 'error':
        return errorMsg || '上传失败'
      default:
        return '点击或拖拽PDF文件到此处'
    }
  }

  return (
    <Card>
      <Dragger
        beforeUpload={handleUpload}
        accept=".pdf"
        disabled={uploading}
        showUploadList={false}
        multiple={false}
      >
        <Space direction="vertical" size="large" style={{ width: '100%', padding: '20px 0' }}>
          {getStatusIcon()}

          <Title level={5} style={{ margin: 0 }}>
            {getStatusText()}
          </Title>

          {status === 'idle' && (
            <>
              <Text type="secondary">
                支持学术论文PDF，自动提取文本、参考文献和关键信息
              </Text>
              <Space>
                <Tag color="blue">AI智能摘要</Tag>
                <Tag color="green">参考文献提取</Tag>
                <Tag color="orange">章节识别</Tag>
              </Space>
            </>
          )}

          {(status === 'uploading' || status === 'parsing') && (
            <div style={{ width: '60%', margin: '0 auto' }}>
              <Progress
                percent={progress}
                status={status === 'error' ? 'exception' : 'active'}
                strokeWidth={8}
              />
              {taskInfo && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  文件: {taskInfo.file_name} ({(taskInfo.file_size / 1024 / 1024).toFixed(2)} MB)
                </Text>
              )}
            </div>
          )}

          {status === 'completed' && taskInfo && (
            <Space direction="vertical">
              <Text type="success">文件解析成功！</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {taskInfo.file_name}
              </Text>
            </Space>
          )}
        </Space>
      </Dragger>

      <div style={{ marginTop: 16 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          <strong>提示：</strong>支持中英文PDF文献，最大50MB。解析过程可能需要30秒-2分钟，取决于文档长度。
        </Text>
      </div>
    </Card>
  )
}

export default PDFUploader
