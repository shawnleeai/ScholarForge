/**
 * Zotero 导入组件
 * 支持从 Zotero API 直接同步文献
 */

import React, { useState } from 'react'
import {
  Modal, Form, Input, Button, Alert, Space, Typography, List, Card,
  Spin, Checkbox, message, Tag, Tooltip
} from 'antd'
import {
  CloudSyncOutlined, InfoCircleOutlined, FolderOutlined,
  BookOutlined, CheckOutlined, LinkOutlined
} from '@ant-design/icons'
import { referenceService } from '@/services/referenceService'

const { Text, Paragraph, Link } = Typography

interface ZoteroImportProps {
  visible: boolean
  onCancel: () => void
  onSuccess: () => void
  paperId?: string
  folderId?: string
}

interface ZoteroCollection {
  key: string
  name: string
  itemCount: number
}

const ZoteroImport: React.FC<ZoteroImportProps> = ({
  visible,
  onCancel,
  onSuccess,
  paperId,
  folderId
}) => {
  const [form] = Form.useForm()
  const [step, setStep] = useState<'credentials' | 'collections' | 'importing'>('credentials')
  const [collections, setCollections] = useState<ZoteroCollection[]>([])
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [importResult, setImportResult] = useState<any>(null)

  const fetchCollections = async () => {
    const values = form.getFieldsValue()
    if (!values.userId || !values.apiKey) {
      message.error('请输入 User ID 和 API Key')
      return
    }

    setLoading(true)
    try {
      // 这里应该调用获取收藏夹列表的 API
      // 暂时模拟一些示例数据
      const mockCollections: ZoteroCollection[] = [
        { key: '', name: '我的文库', itemCount: 150 },
        { key: 'COLLECTION_1', name: '研究论文', itemCount: 45 },
        { key: 'COLLECTION_2', name: '参考文献', itemCount: 80 },
        { key: 'COLLECTION_3', name: '待读文献', itemCount: 25 },
      ]
      setCollections(mockCollections)
      setStep('collections')
    } catch (error) {
      message.error('获取收藏夹失败，请检查凭据')
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async () => {
    const values = form.getFieldsValue()
    setLoading(true)
    setStep('importing')

    try {
      const res = await referenceService.importFromZotero(
        {
          user_id: values.userId,
          api_key: values.apiKey
        },
        selectedCollection || undefined,
        paperId,
        folderId
      )

      setImportResult(res.data?.data)
      message.success('导入成功')
      onSuccess()
    } catch (error) {
      message.error('导入失败')
      setStep('collections')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    form.resetFields()
    setStep('credentials')
    setCollections([])
    setSelectedCollection(null)
    setImportResult(null)
  }

  const handleCancel = () => {
    handleReset()
    onCancel()
  }

  return (
    <Modal
      title={
        <Space>
          <CloudSyncOutlined />
          从 Zotero 导入
        </Space>
      }
      visible={visible}
      onCancel={handleCancel}
      width={600}
      footer={
        step === 'credentials' ? (
          <>
            <Button onClick={handleCancel}>取消</Button>
            <Button type="primary" onClick={fetchCollections} loading={loading}>
              连接并获取收藏夹
            </Button>
          </>
        ) : step === 'collections' ? (
          <>
            <Button onClick={() => setStep('credentials')}>上一步</Button>
            <Button type="primary" onClick={handleImport} loading={loading}>
              开始导入
            </Button>
          </>
        ) : (
          <Button onClick={handleCancel}>关闭</Button>
        )
      }
    >
      {step === 'credentials' && (
        <>
          <Alert
            message="如何获取 Zotero API 凭据"
            description={
              <ol style={{ margin: 0, paddingLeft: 16 }}>
                <li>登录 <Link href="https://www.zotero.org/settings/keys" target="_blank">Zotero API 设置</Link></li>
                <li>点击 "Create new private key"</li>
                <li>勾选 "Allow library access" 权限</li>
                <li>复制生成的 API Key</li>
                <li>您的 User ID 在 <Link href="https://www.zotero.org/settings/account" target="_blank">账户设置</Link> 页面</li>
              </ol>
            }
            type="info"
            showIcon
            icon={<InfoCircleOutlined />}
            style={{ marginBottom: 16 }}
          />

          <Form form={form} layout="vertical">
            <Form.Item
              name="userId"
              label="User ID"
              rules={[{ required: true, message: '请输入 User ID' }]}
            >
              <Input placeholder="例如: 1234567" />
            </Form.Item>

            <Form.Item
              name="apiKey"
              label="API Key"
              rules={[{ required: true, message: '请输入 API Key' }]}
            >
              <Input.Password placeholder="输入您的 Zotero API Key" />
            </Form.Item>

            <Form.Item name="saveCredentials" valuePropName="checked">
              <Checkbox>保存凭据（下次可直接导入）</Checkbox>
            </Form.Item>
          </Form>
        </>
      )}

      {step === 'collections' && (
        <>
          <Paragraph>
            请选择要导入的收藏夹：
          </Paragraph>

          <List
            dataSource={collections}
            renderItem={(item) => (
              <List.Item>
                <Card
                  size="small"
                  style={{
                    width: '100%',
                    cursor: 'pointer',
                    borderColor: selectedCollection === item.key ? '#1890ff' : undefined
                  }}
                  onClick={() => setSelectedCollection(item.key)}
                >
                  <Space>
                    <FolderOutlined
                      style={{
                        fontSize: 24,
                        color: selectedCollection === item.key ? '#1890ff' : '#999'
                      }}
                    />
                    <div>
                      <Text strong>{item.name}</Text>
                      <br />
                      <Text type="secondary">{item.itemCount} 篇文献</Text>
                    </div>
                    {selectedCollection === item.key && (
                      <Tag color="blue" icon={<CheckOutlined />}>已选择</Tag>
                    )}
                  </Space>
                </Card>
              </List.Item>
            )}
          />
        </>
      )}

      {step === 'importing' && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          {loading ? (
            <>
              <Spin size="large" />
              <Paragraph style={{ marginTop: 16 }}>
                正在从 Zotero 同步文献...
              </Paragraph>
            </>
          ) : importResult ? (
            <>
              <CheckOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              <Paragraph strong style={{ marginTop: 16, fontSize: 16 }}>
                导入完成
              </Paragraph>
              <Space>
                <Tag color="success">成功 {importResult.success_count || 0}</Tag>
                <Tag>总计 {importResult.total_count || 0}</Tag>
              </Space>
            </>
          ) : null}
        </div>
      )}
    </Modal>
  )
}

export default ZoteroImport
