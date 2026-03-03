/**
 * 文献搜索页面
 */

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Input, Button, List, Checkbox, Empty, message, Avatar } from 'antd'
import { SearchOutlined, FileTextOutlined, PlusOutlined } from '@ant-design/icons'

import { articleService } from '@/services'
import type { Article, PaginatedResponse } from '@/types'
import styles from './Library.module.css'

const { Search } = Input

const SearchPage: React.FC = () => {
  const [searchText, setSearchText] = useState('')
  const [hasSearched, setHasSearched] = useState(false)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['search', searchText],
    queryFn: () => articleService.search({ q: searchText }),
    enabled: false,
  })

  const articles = (data?.data as PaginatedResponse<Article>)?.items || []
  const total = (data?.data as PaginatedResponse<Article>)?.total || 0

  const handleSearch = (value: string) => {
    if (!value.trim()) return
    setSearchText(value)
    setHasSearched(true)
    refetch()
  }

  const handleAddToLibrary = async (articleId: string) => {
    try {
      await articleService.addToLibrary({ articleId })
      message.success('已添加到文献库')
    } catch {
      message.error('添加失败')
    }
  }

  return (
    <div className={styles.searchPage}>
      <Card className={styles.searchCard}>
        <div className={styles.searchHeader}>
          <h2>多源文献检索</h2>
        </div>

        <Search
          placeholder="输入关键词搜索文献..."
          allowClear
          enterButton={<><SearchOutlined /> 搜索</>}
          size="large"
          onSearch={handleSearch}
          loading={isLoading}
        />

        <div className={styles.filters}>
          <Checkbox.Group defaultValue={['cnki', 'wos', 'ieee']}>
            <Checkbox value="cnki">CNKI</Checkbox>
            <Checkbox value="wos">Web of Science</Checkbox>
            <Checkbox value="ieee">IEEE</Checkbox>
          </Checkbox.Group>
        </div>
      </Card>

      {hasSearched && (
        <Card className={styles.resultsCard}>
          <div className={styles.resultsHeader}>
            找到 <strong>{total}</strong> 条结果
          </div>

          {articles.length === 0 ? (
            <Empty description="未找到相关文献" />
          ) : (
            <List
              itemLayout="vertical"
              dataSource={articles}
              renderItem={(article: Article) => (
                <List.Item
                  key={article.id}
                  className={styles.listItem}
                  actions={[
                    <Button
                      key="add"
                      type="primary"
                      ghost
                      size="small"
                      icon={<PlusOutlined />}
                      onClick={() => handleAddToLibrary(article.id)}
                    >
                      加入文献库
                    </Button>,
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
                    title={<a href={article.sourceUrl} target="_blank" rel="noopener noreferrer">{article.title}</a>}
                    description={
                      <div className={styles.articleMeta}>
                        <div>{article.authors?.map((a) => a.name).join(', ')}</div>
                        <div className={styles.source}>
                          {article.sourceName} · {article.publicationYear} · 引用 {article.citationCount}
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Card>
      )}
    </div>
  )
}

export default SearchPage
