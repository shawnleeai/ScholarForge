/**
 * 元数据提取工具组件
 * 支持通过 DOI、PMID 或标题自动提取文献信息
 */

import React, { useState } from 'react'
import { Modal, Form, Input, Button, Radio, Space, message, Card, Spin, Typography, Tag } from 'antd'
import { SearchOutlined, LinkOutlined, FileTextOutlined, ReloadOutlined, CheckOutlined } from '@ant-design/icons'
import { referenceService } from '@/services/referenceService'

const { Text, Paragraph } = Typography

interface MetadataExtractorProps {
  visible: boolean
  onCancel: () => void
  onImport: (reference: any) => void
}

const MetadataExtractor: React.FC<MetadataExtractorProps> = ({
  visible,
  onCancel,
  onImport
}) => {
  const [form] = Form.useForm()
  const [extractType, setExtractType] = useState<'doi' | 'pmid' | 'text'>('doi')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [imported, setImported] = useState(false)

  const handleExtract = async () => {
    const values = form.getFieldsValue()

    if (extractType === 'doi' && !values.identifier) {
      message.warning('请输入 DOI')
      return
    }
    if (extractType === 'pmid' && !values.identifier) {
      message.warning('请输入 PMID')
      return
    }
    if (extractType === 'text' && !values.text) {
      message.warning('请输入标题或引用文本')
      return
    }

    setLoading(true)
    setResult(null)
    setImported(false)

    try {
      const res = await referenceService.extractMetadata(
        extractType !== 'text' ? values.identifier : undefined,
        extractType !== 'text' ? extractType : undefined,
        extractType === 'text' ? values.text : undefined
      )

      if (res.data?.data?.success) {
        setResult(res.data.data)
        message.success('提取成功')
      } else {
        message.warning(res.data?.data?.message || '未能提取到完整信息')
      }
    } catch (error) {
      message.error('提取失败')
    } finally {
      setLoading(false)
    }
  }

  const handleImport = () => {
    if (result?.reference) {
      onImport(result.reference)
      setImported(true)
      message.success('已添加到表单')
    }
  }

  const handleReset = () => {
    form.resetFields()
    setResult(null)
    setImported(false)
  }

  return (
    <Modal
      title="自动提取文献信息"
      visible={visible}
      onCancel={onCancel}
      width={700}
      footer={[
        <Button key="reset" onClick={handleReset} icon={<ReloadOutlined />}>
          重置
        </Button>,
        <Button key="cancel" onClick={onCancel}>
          关闭
        </Button>,
        result && !imported && (
          <Button
            key="import"
            type="primary"
            icon={<CheckOutlined />}
            onClick={handleImport}
          >
            使用此信息
          </Button>
        )
      ]}
    >
      <Form form={form} layout="vertical">
        <Form.Item label="提取方式">
          <Radio.Group
            value={extractType}
            onChange={(e) => {
              setExtractType(e.target.value)
              setResult(null)
              form.resetFields(['identifier', 'text'])
            }}
          >
            <Radio.Button value="doi">
              <LinkOutlined /> DOI
            </Radio.Button>
            <Radio.Button value="pmid">
              <FileTextOutlined /> PMID
            </Radio.Button>
            <Radio.Button value="text">
              <SearchOutlined /> 标题/文本
            </Radio.Button>
          </Radio.Group>
        </Form.Item>

        {extractType !== 'text' ? (
          <Form.Item
            name="identifier"
            label={extractType === 'doi' ? 'DOI' : 'PMID'}
            rules={[{ required: true }]}
          >
            <Input.Search
              placeholder={
                extractType === 'doi'
                  ? '例如: 10.1038/s41586-021-03819-2'
                  : '例如: 34526774'
              }
              enterButton={<><SearchOutlined /> 提取</>}
              onSearch={handleExtract}
              loading={loading}
            />
          </Form.Item>
        ) : (
          <Form.Item
            name="text"
            label="标题或引用文本"
            rules={[{ required: true }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="输入文献标题、引用文本或相关信息..."
            />
          </Form.Item>
        )}

        {extractType === 'text' && (
          <Form.Item>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={handleExtract}
              loading={loading}
            >
              提取信息
            </Button>
          </Form.Item>
        )}
      </Form>

      {loading && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <Paragraph style={{ marginTop: 16 }}>
            正在从数据库提取文献信息...
          </Paragraph>
        </div>
      )}

      {result && result.success && result.reference && (
        <Card
          title="提取结果"
          size="small"
          style={{ marginTop: 16 }}
          extra={
            result.confidence && (
              <Tag color={result.confidence > 0.8 ? 'green' : 'orange'}>
                置信度: {(result.confidence * 100).toFixed(0)}%
              </Tag>
            )
          }
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text type="secondary">标题:</Text>
              <br />
              <Text strong>{result.reference.title}</Text>
            </div>

            {result.reference.authors?.length > 0 && (
              <div>
                <Text type="secondary">作者:</Text>
                <br />
                <Text>{result.reference.authors.join(', ')}</Text>
              </div>
            )}

            <Space split={<span style={{ color: '#ddd' }}>|</span>}>
              {result.reference.publication_year && (
                <span><Text type="secondary">年份:</Text> {result.reference.publication_year}</span>
              )}
              {result.reference.journal_name && (
                <span><Text type="secondary">期刊:</Text> {result.reference.journal_name}</span>
              )}
              {result.reference.volume && (
                <span><Text type="secondary">卷:</Text> {result.reference.volume}</span>
              )}
              {result.reference.issue && (
                <span><Text type="secondary">期:</Text> {result.reference.issue}</span>
              )}
              {result.reference.pages && (
                <span><Text type="secondary">页码:</Text> {result.reference.pages}</span>
              )}
            </Space>

            {result.reference.doi && (
              <div>
                <Text type="secondary">DOI:</Text>{' '}
                <a href={`https://doi.org/${result.reference.doi}`} target="_blank" rel="noreferrer">
                  {result.reference.doi}
                </a>
              </div>
            )}

            {result.reference.abstract && (
              <div>
                <Text type="secondary">摘要:</Text>
                <Paragraph ellipsis={{ rows: 3, expandable: true }}>
                  {result.reference.abstract}
                </Paragraph>
              </div>
            )}
          </Space>
        </Card>
      )}
    </Modal>
  )
}

export default MetadataExtractor
