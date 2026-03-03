/**
 * 导入预览组件
 * 预览导入文件内容，显示重复项和无效项
 */

import React, { useState } from 'react'
import {
  Modal, Table, Tag, Alert, Space, Typography, Button, Progress,
  Tabs, List, Card, Tooltip
} from 'antd'
import {
  CheckCircleOutlined, WarningOutlined, CloseCircleOutlined,
  FileTextOutlined, CopyOutlined
} from '@ant-design/icons'

const { Text, Paragraph } = Typography
const { TabPane } = Tabs

interface ImportPreviewProps {
  visible: boolean
  previewData: {
    total: number
    valid: number
    duplicates: number
    invalid: number
    sample: any[]
    duplicates_detail: any[]
  } | null
  onCancel: () => void
  onConfirm: () => void
  onSkipDuplicates?: () => void
}

const ImportPreview: React.FC<ImportPreviewProps> = ({
  visible,
  previewData,
  onCancel,
  onConfirm,
  onSkipDuplicates
}) => {
  const [activeTab, setActiveTab] = useState('valid')

  if (!previewData) return null

  const { total, valid, duplicates, invalid, sample, duplicates_detail } = previewData

  const validItems = sample.slice(0, valid)
  const duplicateItems = duplicates_detail

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string) => (
        <Text ellipsis style={{ maxWidth: 300 }} title={text}>
          {text}
        </Text>
      )
    },
    {
      title: '作者',
      dataIndex: 'authors',
      key: 'authors',
      render: (authors: string[]) => (
        <Text type="secondary" ellipsis style={{ maxWidth: 150 }}>
          {authors?.slice(0, 2).join(', ')}
          {authors?.length > 2 ? ' 等' : ''}
        </Text>
      )
    },
    {
      title: '年份',
      dataIndex: 'publication_year',
      key: 'year',
      width: 80
    },
    {
      title: '期刊/来源',
      dataIndex: 'journal_name',
      key: 'journal',
      render: (text: string) => (
        <Text ellipsis style={{ maxWidth: 150 }} title={text}>
          {text}
        </Text>
      )
    },
    {
      title: '类型',
      dataIndex: 'publication_type',
      key: 'type',
      width: 100,
      render: (type: string) => {
        const typeColors: Record<string, string> = {
          journal: 'blue',
          conference: 'green',
          book: 'orange',
          thesis: 'purple',
          report: 'cyan',
          online: 'magenta'
        }
        return (
          <Tag color={typeColors[type] || 'default'}>
            {type === 'journal' ? '期刊' :
             type === 'conference' ? '会议' :
             type === 'book' ? '图书' :
             type === 'thesis' ? '学位论文' :
             type === 'report' ? '报告' :
             type === 'online' ? '网络' : type}
          </Tag>
        )
      }
    }
  ]

  return (
    <Modal
      title="导入预览"
      visible={visible}
      onCancel={onCancel}
      width={900}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        duplicates > 0 && onSkipDuplicates && (
          <Button key="skip" onClick={onSkipDuplicates}>
            跳过重复项导入
          </Button>
        ),
        <Button key="import" type="primary" onClick={onConfirm}>
          确认导入
        </Button>
      ]}
    >
      {/* 统计概览 */}
      <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
        <Alert
          message={
            <Space>
              <FileTextOutlined />
              <span>共解析到 <strong>{total}</strong> 篇文献</span>
            </Space>
          }
          type="info"
          showIcon={false}
        />

        <Progress
          percent={Math.round((valid / total) * 100)}
          status={invalid > 0 ? 'exception' : 'success'}
          format={() => (
            <Space>
              <Tag icon={<CheckCircleOutlined />} color="success">
                有效 {valid}
              </Tag>
              {duplicates > 0 && (
                <Tag icon={<CopyOutlined />} color="warning">
                  重复 {duplicates}
                </Tag>
              )}
              {invalid > 0 && (
                <Tag icon={<CloseCircleOutlined />} color="error">
                  无效 {invalid}
                </Tag>
              )}
            </Space>
          )}
        />
      </Space>

      {/* 详细信息标签页 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={<span><CheckCircleOutlined /> 有效文献 ({valid})</span>}
          key="valid"
        >
          <Table
            dataSource={validItems}
            columns={columns}
            rowKey={(record, index) => index?.toString() || ''}
            pagination={{ pageSize: 5, size: 'small' }}
            size="small"
          />
          {valid > 5 && (
            <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 8 }}>
              还有 {valid - 5} 篇文献...
            </Text>
          )}
        </TabPane>

        {duplicates > 0 && (
          <TabPane
            tab={<span><CopyOutlined /> 重复项 ({duplicates})</span>}
            key="duplicates"
          >
            <List
              dataSource={duplicateItems}
              renderItem={(item: any) => (
                <List.Item>
                  <Card size="small" style={{ width: '100%' }}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Text strong>{item.reference?.title}</Text>
                      <Space>
                        <Tag color="warning">重复</Tag>
                        <Text type="secondary">
                          与现有文献 "{item.duplicate_of?.title}" 重复
                        </Text>
                      </Space>
                    </Space>
                  </Card>
                </List.Item>
              )}
            />
          </TabPane>
        )}

        {invalid > 0 && (
          <TabPane
            tab={<span><WarningOutlined /> 无效项 ({invalid})</span>}
            key="invalid"
          >
            <Alert
              message="以下文献缺少必要信息（标题），无法导入"
              type="warning"
              showIcon
            />
          </TabPane>
        )}
      </Tabs>
    </Modal>
  )
}

export default ImportPreview
