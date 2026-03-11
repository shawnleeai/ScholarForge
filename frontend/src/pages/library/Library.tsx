/**
 * 文献库页面 - 集成PDF上传功能
 */

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Row, Col, Card, List, Tag, Space, Input, Tree, Button, Empty, Avatar, Tooltip, Dropdown, Modal, Tabs, Drawer } from 'antd'
import {
  FolderOutlined,
  FileTextOutlined,
  StarOutlined,
  StarFilled,
  MoreOutlined,
  PlusOutlined,
  UploadOutlined,
  SearchOutlined,
  ReadOutlined,
  RobotOutlined,
} from '@ant-design/icons'

import { articleService } from '@/services'
import { PDFUploader, PDFParseResultView, PDFAnalysisPanel } from '@/components/pdf'
import type { LibraryItem, LibraryFolder, PaginatedResponse, Article } from '@/types'
import type { PDFParseResult } from '@/services/pdfService'
import styles from './Library.module.css'

const { Search } = Input
const { TabPane } = Tabs

const Library: React.FC = () => {
  const [selectedFolderId, setSelectedFolderId] = useState<string>()
  const [searchText, setSearchText] = useState('')
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [parseResult, setParseResult] = useState<PDFParseResult | null>(null)
  const [activeTab, setActiveTab] = useState('library')
  const [analysisDrawerVisible, setAnalysisDrawerVisible] = useState(false)
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)

  const { data: libraryData, isLoading } = useQuery({
    queryKey: ['library', selectedFolderId],
    queryFn: () => articleService.getLibrary(),
  })

  const { data: foldersData } = useQuery({
    queryKey: ['folders'],
    queryFn: () => articleService.getFolders(),
  })

  const libraryItems = (libraryData?.data as PaginatedResponse<LibraryItem>)?.items || []
  const folders = (foldersData?.data as LibraryFolder[]) || []

  const filteredItems = libraryItems.filter(
    (item: LibraryItem) => item.article.title.toLowerCase().includes(searchText.toLowerCase())
  )

  const treeData = [
    { key: 'all', title: '全部文献', icon: <FolderOutlined /> },
    ...folders.map((folder: LibraryFolder) => ({
      key: folder.id,
      title: `${folder.name} (${folder.articleCount})`,
      icon: <FolderOutlined style={{ color: folder.color }} />,
    })),
  ]

  const getDropdownItems = (item: LibraryItem) => [
    { key: 'favorite', icon: item.isFavorite ? <StarFilled /> : <StarOutlined />, label: item.isFavorite ? '取消收藏' : '收藏' },
    { key: 'analyze', icon: <RobotOutlined />, label: 'AI 智能分析' },
  ]

  const handleMenuClick = (key: string, item: LibraryItem) => {
    if (key === 'analyze') {
      setSelectedArticle(item.article)
      setAnalysisDrawerVisible(true)
    } else if (key === 'favorite') {
      // TODO: 实现收藏切换
      console.log('切换收藏状态:', item.id)
    }
  }

  const getSourceTag = (source: string) => {
    const config: Record<string, { color: string; label: string }> = {
      wos: { color: 'blue', label: 'WoS' },
      cnki: { color: 'red', label: 'CNKI' },
      ieee: { color: 'green', label: 'IEEE' },
      arxiv: { color: 'purple', label: 'arXiv' },
      pdf: { color: 'orange', label: 'PDF' },
    }
    return config[source] || { color: 'default', label: source }
  }

  const handleUploadSuccess = (taskId: string) => {
    console.log('上传成功，任务ID:', taskId)
  }

  const handleParseComplete = (result: PDFParseResult) => {
    setParseResult(result)
    setUploadModalVisible(false)
  }

  return (
    <div className={styles.library}>
      <Tabs activeKey={activeTab} onChange={setActiveTab} style={{ marginBottom: 16 }}>
        <TabPane tab="文献库" key="library" />
        {parseResult && (
          <TabPane tab="PDF解析结果" key="parseResult" closable onClose={() => setParseResult(null)} />
        )}
      </Tabs>

      {activeTab === 'library' && (
        <Row gutter={24}>
          <Col xs={24} sm={6} lg={5}>
            <Card className={styles.folderCard}>
              <div className={styles.folderHeader}>
                <h3>我的文献库</h3>
                <Tooltip title="新建文件夹">
                  <Button type="text" size="small" icon={<PlusOutlined />} />
                </Tooltip>
              </div>
              <Tree
                showIcon
                defaultExpandedKeys={['all']}
                selectedKeys={[selectedFolderId || 'all']}
                treeData={treeData}
                onSelect={(keys) => {
                  const key = keys[0] as string
                  setSelectedFolderId(key === 'all' ? undefined : key)
                }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={18} lg={19}>
            <Card className={styles.listCard}>
              <div className={styles.searchBar}>
                <Search
                  placeholder="搜索文献..."
                  allowClear
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  style={{ maxWidth: 400 }}
                />
                <Space>
                  <Button icon={<SearchOutlined />}>高级搜索</Button>
                  <Button
                    type="primary"
                    icon={<UploadOutlined />}
                    onClick={() => setUploadModalVisible(true)}
                  >
                    导入PDF
                  </Button>
                </Space>
              </div>

              {isLoading ? (
                <div className={styles.loading}>加载中...</div>
              ) : filteredItems.length === 0 ? (
                <Empty
                  description="暂无文献"
                  extra={
                    <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadModalVisible(true)}>
                      上传PDF解析
                    </Button>
                  }
                />
              ) : (
                <List
                  itemLayout="vertical"
                  dataSource={filteredItems}
                  renderItem={(item: LibraryItem) => {
                    const sourceTag = getSourceTag(item.article.sourceDb || '')
                    return (
                      <List.Item
                        key={item.id}
                        className={styles.listItem}
                        actions={[
                          <Space key="actions">
                            <Tooltip title={item.isFavorite ? '取消收藏' : '收藏'}>
                              <Button
                                type="text"
                                icon={item.isFavorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
                              />
                            </Tooltip>
                            <Dropdown
                              menu={{
                                items: getDropdownItems(item),
                                onClick: ({ key }) => handleMenuClick(key, item)
                              }}
                              trigger={['click']}
                            >
                              <Button type="text" icon={<MoreOutlined />} />
                            </Dropdown>
                          </Space>,
                        ]}
                      >
                        <List.Item.Meta
                          avatar={
                            <Avatar
                              shape="square"
                              size={48}
                              style={{ backgroundColor: '#f0f5ff' }}
                              icon={<FileTextOutlined style={{ color: '#1890ff' }} />}
                            />
                          }
                          title={
                            <Space>
                              <span className={styles.articleTitle}>{item.article.title}</span>
                              <Tag color={sourceTag.color}>{sourceTag.label}</Tag>
                            </Space>
                          }
                          description={
                            <div className={styles.articleMeta}>
                              <div>{item.article.authors?.map((a) => a.name).join(', ')}</div>
                              <div className={styles.source}>
                                {item.article.sourceName} · {item.article.publicationYear}
                              </div>
                            </div>
                          }
                        />
                      </List.Item>
                    )
                  }}
                />
              )}
            </Card>
          </Col>
        </Row>
      )}

      {activeTab === 'parseResult' && parseResult && (
        <PDFParseResultView result={parseResult} />
      )}

      {/* PDF上传弹窗 */}
      <Modal
        title="导入PDF文献"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={700}
        destroyOnClose
      >
        <PDFUploader
          onUploadSuccess={handleUploadSuccess}
          onParseComplete={handleParseComplete}
        />
      </Modal>

      {/* PDF AI 分析抽屉 */}
      <Drawer
        title={
          <Space>
            <RobotOutlined />
            <span>文献智能分析</span>
          </Space>
        }
        placement="right"
        width={600}
        open={analysisDrawerVisible}
        onClose={() => setAnalysisDrawerVisible(false)}
        destroyOnClose
      >
        {selectedArticle && (
          <PDFAnalysisPanel
            article={selectedArticle}
            userTopic="AI在学术写作中的应用"
            visible={analysisDrawerVisible}
            onClose={() => setAnalysisDrawerVisible(false)}
          />
        )}
      </Drawer>
    </div>
  )
}

export default Library
