/**
 * 期刊匹配页面
 */
import React, { useState } from 'react'
import { Card, Button, Input, Space, Typography, Empty, Spin, List, Tag, Row, Col, Statistic } from 'antd'
import { SearchOutlined, BookOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const JournalMatcher: React.FC = () => {
  const [paperTitle, setPaperTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any[]>([])

  const handleMatch = () => {
    setLoading(true)
    setTimeout(() => {
      setResults([
        { id: 1, name: 'Journal of Management', score: 85, if: 8.5 },
        { id: 2, name: 'Project Management Journal', score: 78, if: 4.2 },
      ])
      setLoading(false)
    }, 1000)
  }

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}><BookOutlined /> 期刊智能匹配</Title>
      <Text type="secondary">基于论文内容推荐最适合的投稿期刊</Text>
      
      <Card style={{ marginTop: 24 }}>
        <Space>
          <Input 
            placeholder="输入论文标题或摘要" 
            value={paperTitle}
            onChange={(e) => setPaperTitle(e.target.value)}
            style={{ width: 400 }}
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={handleMatch}>匹配期刊</Button>
        </Space>
      </Card>

      <Spin spinning={loading}>
        {results.length > 0 ? (
          <List
            style={{ marginTop: 24 }}
            dataSource={results}
            renderItem={(item) => (
              <List.Item>
                <Card style={{ width: '100%' }} title={item.name} extra={<Tag color="blue">匹配度: {item.score}%</Tag>}>
                  <Row gutter={16}>
                    <Col span={8}><Statistic title="影响因子" value={item.if} /></Col>
                    <Col span={8}><Statistic title="录用率" value="25%" /></Col>
                    <Col span={8}><Statistic title="审稿周期" value="3个月" /></Col>
                  </Row>
                </Card>
              </List.Item>
            )}
          />
        ) : (
          <Empty style={{ marginTop: 100 }} description="输入论文信息开始匹配" />
        )}
      </Spin>
    </div>
  )
}

export default JournalMatcher
