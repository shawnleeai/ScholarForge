/**
 * PDF解析结果展示组件
 */

import React, { useState } from 'react'
import {
  Card,
  Tabs,
  Typography,
  Tag,
  Space,
  List,
  Collapse,
  Skeleton,
  Empty,
  Button,
  Tooltip,
  Descriptions,
  Divider,
  Alert
} from 'antd'
import {
  FileTextOutlined,
  BookOutlined,
  TeamOutlined,
  TagsOutlined,
  GlobalOutlined,
  FilePdfOutlined,
  DownloadOutlined,
  LinkOutlined,
  CopyOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import type { PDFParseResult as IPDFParseResult, Reference, Section } from '@/services/pdfService'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse
const { TabPane } = Tabs

interface PDFParseResultProps {
  result: IPDFParseResult | null
  loading?: boolean
}

export const PDFParseResultView: React.FC<PDFParseResultProps> = ({
  result,
  loading = false
}) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [copied, setCopied] = useState(false)

  if (loading) {
    return (
      <Card>
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    )
  }

  if (!result) {
    return (
      <Card>
        <Empty
          description="暂无解析结果"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    )
  }

  const { metadata, ai_summary, ai_key_points, ai_methodology, references, sections } = result

  const handleCopyReferences = () => {
    const refText = references.map((ref, idx) => {
      const authors = ref.authors.slice(0, 3).join(', ')
      const etAl = ref.authors.length > 3 ? ' et al.' : ''
      return `[${idx + 1}] ${authors}${etAl}. ${ref.title || 'Unknown'}. ${ref.journal || ''} ${ref.year || ''}.`
    }).join('\n')

    navigator.clipboard.writeText(refText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const renderOverview = () => (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* AI摘要 */}
      {ai_summary && (
        <Card
          title={<><FileTextOutlined /> AI智能摘要</>}
          bordered={false}
          style={{ background: '#f6ffed' }}
        >
          <Paragraph>{ai_summary}</Paragraph>
        </Card>
      )}

      {/* 关键要点 */}
      {ai_key_points && ai_key_points.length > 0 && (
        <Card title={<><CheckCircleOutlined /> 核心观点</>} bordered={false}>
          <List
            size="small"
            dataSource={ai_key_points}
            renderItem={(point, idx) => (
              <List.Item>
                <Text><strong>{idx + 1}.</strong> {point}</Text>
              </List.Item>
            )}
          />
        </Card>
      )}

      {/* 研究方法 */}
      {ai_methodology && (
        <Card title={<><GlobalOutlined /> 研究方法</>} bordered={false}>
          <Descriptions size="small" column={1}>
            {ai_methodology.research_type && (
              <Descriptions.Item label="研究类型">
                {ai_methodology.research_type}
              </Descriptions.Item>
            )}
            {ai_methodology.data_collection && (
              <Descriptions.Item label="数据收集">
                {ai_methodology.data_collection}
              </Descriptions.Item>
            )}
            {ai_methodology.analysis_method && (
              <Descriptions.Item label="分析方法">
                {ai_methodology.analysis_method}
              </Descriptions.Item>
            )}
          </Descriptions>
        </Card>
      )}
    </Space>
  )

  const renderMetadata = () => (
    <Descriptions bordered column={{ xs: 1, sm: 2 }}>
      <Descriptions.Item label="标题" span={2}>
        {metadata.title || '未识别'}
      </Descriptions.Item>

      <Descriptions.Item label="作者" span={2}>
        {metadata.authors?.length > 0 ? (
          <Space wrap>
            {metadata.authors.map((author, idx) => (
              <Tag key={idx} icon={<TeamOutlined />}>{author}</Tag>
            ))}
          </Space>
        ) : '未识别'}
      </Descriptions.Item>

      {metadata.abstract && (
        <Descriptions.Item label="摘要" span={2}>
          <Paragraph style={{ maxHeight: 200, overflow: 'auto' }}>
            {metadata.abstract}
          </Paragraph>
        </Descriptions.Item>
      )}

      {metadata.keywords?.length > 0 && (
        <Descriptions.Item label="关键词" span={2}>
          <Space wrap>
            {metadata.keywords.map((kw, idx) => (
              <Tag key={idx} color="blue">{kw}</Tag>
            ))}
          </Space>
        </Descriptions.Item>
      )}

      {metadata.doi && (
        <Descriptions.Item label="DOI">
          <a href={`https://doi.org/${metadata.doi}`} target="_blank" rel="noopener noreferrer">
            {metadata.doi} <LinkOutlined />
          </a>
        </Descriptions.Item>
      )}

      {metadata.publication_year && (
        <Descriptions.Item label="发表年份">
          {metadata.publication_year}
        </Descriptions.Item>
      )}

      {metadata.journal && (
        <Descriptions.Item label="期刊">
          {metadata.journal}
        </Descriptions.Item>
      )}

      <Descriptions.Item label="语言">
        {metadata.language === 'zh' ? '中文' : '英文'}
      </Descriptions.Item>

      <Descriptions.Item label="页数">
        {result.page_count || '未知'}
      </Descriptions.Item>
    </Descriptions>
  )

  const renderReferences = () => (
    <Space direction="vertical" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text strong>共识别 {references.length} 条参考文献</Text>
        <Button
          icon={copied ? <CheckCircleOutlined /> : <CopyOutlined />}
          onClick={handleCopyReferences}
          size="small"
        >
          {copied ? '已复制' : '复制全部'}
        </Button>
      </div>

      <List
        bordered
        dataSource={references}
        style={{ maxHeight: 600, overflow: 'auto' }}
        renderItem={(ref, idx) => (
          <List.Item>
            <List.Item.Meta
              title={
                <Space>
                  <Text type="secondary">[{idx + 1}]</Text>
                  <Text>{ref.title || 'Unknown Title'}</Text>
                  {ref.year && <Tag color="green">{ref.year}</Tag>}
                </Space>
              }
              description={
                <Space direction="vertical" size={0}>
                  <Text type="secondary">
                    {ref.authors.slice(0, 5).join(', ')}
                    {ref.authors.length > 5 ? ' et al.' : ''}
                  </Text>
                  {ref.journal && ref.journal !== 'Unknown' && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      <BookOutlined /> {ref.journal}
                      {ref.doi && (
                        <a
                          href={`https://doi.org/${ref.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ marginLeft: 8 }}
                        >
                          DOI <LinkOutlined />
                        </a>
                      )}
                    </Text>
                  )}
                </Space>
              }
            />
          </List.Item>
        )}
      />
    </Space>
  )

  const renderSections = () => (
    <Collapse defaultActiveKey={['0']}>
      {sections.map((section, idx) => (
        <Panel
          header={
            <Space>
              <Text strong>{section.title}</Text>
              {section.page_start && (
                <Tag size="small">第{section.page_start}页</Tag>
              )}
            </Space>
          }
          key={idx}
        >
          <Text type="secondary">章节内容可在全文中查看</Text>
        </Panel>
      ))}
    </Collapse>
  )

  return (
    <Card
      title={
        <Space>
          <FilePdfOutlined />
          <span>解析结果</span>
          <Tag color="success">{metadata.language === 'zh' ? '中文' : '英文'}</Tag>
        </Space>
      }
      extra={
        <Text type="secondary" style={{ fontSize: 12 }}>
          任务ID: {result.task_id.slice(0, 8)}...
        </Text>
      }
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="概览" key="overview">
          {renderOverview()}
        </TabPane>

        <TabPane
          tab={<span><BookOutlined /> 元数据</span>}
          key="metadata"
        >
          {renderMetadata()}
        </TabPane>

        <TabPane
          tab={<span><TagsOutlined /> 参考文献 ({references.length})</span>}
          key="references"
        >
          {renderReferences()}
        </TabPane>

        <TabPane
          tab={<span><FileTextOutlined /> 章节结构</span>}
          key="sections"
        >
          {renderSections()}
        </TabPane>
      </Tabs>
    </Card>
  )
}

export default PDFParseResultView
