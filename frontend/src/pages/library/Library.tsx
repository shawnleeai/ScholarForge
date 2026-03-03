/**
 * 文献库页面
 */

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Row, Col, Card, List, Tag, Space, Input, Tree, Button, Empty, Avatar, Tooltip, Dropdown } from 'antd'
import {
  FolderOutlined,
  FileTextOutlined,
  StarOutlined,
  StarFilled,
  MoreOutlined,
  PlusOutlined,
} from '@ant-design/icons'

import { articleService } from '@/services'
import type { LibraryItem, LibraryFolder, PaginatedResponse } from '@/types'
import styles from './Library.module.css'

const { Search } = Input

const Library: React.FC = () => {
  const [selectedFolderId, setSelectedFolderId] = useState<string>()
  const [searchText, setSearchText] = useState('')

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
  ]

  const getSourceTag = (source: string) => {
    const config: Record<string, { color: string; label: string }> = {
      wos: { color: 'blue', label: 'WoS' },
      cnki: { color: 'red', label: 'CNKI' },
      ieee: { color: 'green', label: 'IEEE' },
    }
    return config[source] || { color: 'default', label: source }
  }

  return (
    <div className={styles.library}>
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
              <Button icon={<StarOutlined />}>收藏</Button>
            </div>

            {isLoading ? (
              <div className={styles.loading}>加载中...</div>
            ) : filteredItems.length === 0 ? (
              <Empty description="暂无文献" />
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
                          <Dropdown menu={{ items: getDropdownItems(item) }} trigger={['click']}>
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
    </div>
  )
}

export default Library
