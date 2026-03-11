/**
 * 版本对比组件
 * 论文版本差异可视化
 */

import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Select,
  Space,
  Typography,
  Badge,
  Tabs,
  List,
  Tag,
  Divider,
  Statistic,
  Row,
  Col,
  Tooltip,
  message,
} from 'antd'
import {
  DiffOutlined,
  SwapOutlined,
  DownloadOutlined,
  EyeOutlined,
  FileTextOutlined,
  PlusOutlined,
  MinusOutlined,
  EditOutlined,
} from '@ant-design/icons'
import styles from './VersionDiff.module.css'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs

interface Version {
  id: string
  version: string
  timestamp: string
  author: string
  comment?: string
}

interface DiffBlock {
  operation: 'equal' | 'insert' | 'delete' | 'replace'
  old_start: number
  old_end: number
  new_start: number
  new_end: number
  old_text: string
  new_text: string
}

interface VersionDiffProps {
  paperId: string
}

const VersionDiff: React.FC<VersionDiffProps> = ({ paperId }) => {
  const [oldVersion, setOldVersion] = useState<string>('')
  const [newVersion, setNewVersion] = useState<string>('')
  const [versions, setVersions] = useState<Version[]>([])
  const [diffResult, setDiffResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState<'side' | 'unified'>('side')

  useEffect(() => {
    loadVersions()
  }, [paperId])

  const loadVersions = async () => {
    // 模拟API调用
    const mockVersions: Version[] = [
      { id: 'v1', version: '1.0.0', timestamp: '2024-01-15 10:00', author: '张三', comment: '初始版本' },
      { id: 'v2', version: '1.1.0', timestamp: '2024-02-01 14:30', author: '张三', comment: '修订引言部分' },
      { id: 'v3', version: '1.2.0', timestamp: '2024-02-20 09:00', author: '李四', comment: '添加实验结果' },
      { id: 'v4', version: '2.0.0', timestamp: '2024-03-05 16:00', author: '张三', comment: '重大更新：重写方法论' },
    ]
    setVersions(mockVersions)
    if (mockVersions.length >= 2) {
      setOldVersion(mockVersions[mockVersions.length - 2].id)
      setNewVersion(mockVersions[mockVersions.length - 1].id)
    }
  }

  const handleCompare = async () => {
    if (!oldVersion || !newVersion) {
      message.warning('请选择两个版本进行对比')
      return
    }
    if (oldVersion === newVersion) {
      message.warning('请选择不同的版本进行对比')
      return
    }

    setLoading(true)
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 800))

      const mockDiff = {
        similarity: 0.75,
        stats: {
          insertions: 45,
          deletions: 30,
          modifications: 20,
          unchanged: 150,
        },
        changes: [
          {
            operation: 'equal',
            old_start: 1,
            old_end: 10,
            new_start: 1,
            new_end: 10,
            old_text: '未变更的内容...',
            new_text: '未变更的内容...',
          },
          {
            operation: 'delete',
            old_start: 11,
            old_end: 15,
            new_start: 11,
            new_end: 11,
            old_text: '被删除的旧内容',
            new_text: '',
          },
          {
            operation: 'insert',
            old_start: 16,
            old_end: 16,
            new_start: 12,
            new_end: 18,
            old_text: '',
            new_text: '新添加的内容段落',
          },
        ],
      }
      setDiffResult(mockDiff)
    } catch (error) {
      message.error('对比失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSwap = () => {
    const temp = oldVersion
    setOldVersion(newVersion)
    setNewVersion(temp)
  }

  const renderDiffContent = () => {
    if (!diffResult) return null

    return (
      <div className={styles.diffContainer}>
        {viewMode === 'side' ? (
          <div className={styles.sideBySide}>
            <div className={styles.diffColumn}>
              <div className={styles.columnHeader}>旧版本</div>
              {diffResult.changes.map((change: DiffBlock, idx: number) => (
                <div
                  key={idx}
                  className={`${styles.diffBlock} ${styles[change.operation]}`}
                >
                  {change.old_text}
                </div>
              ))}
            </div>
            <div className={styles.diffColumn}>
              <div className={styles.columnHeader}>新版本</div>
              {diffResult.changes.map((change: DiffBlock, idx: number) => (
                <div
                  key={idx}
                  className={`${styles.diffBlock} ${styles[change.operation]}`}
                >
                  {change.new_text}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className={styles.unified}>
            {diffResult.changes.map((change: DiffBlock, idx: number) => (
              <div
                key={idx}
                className={`${styles.diffBlock} ${styles[change.operation]}`}
              >
                {change.operation === 'delete' && <MinusOutlined />}
                {change.operation === 'insert' && <PlusOutlined />}
                {change.operation === 'replace' && <EditOutlined />}
                <span>{change.new_text || change.old_text}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <Card className={styles.diffCard}>
      <div className={styles.header}>
        <Title level={4}>
          <DiffOutlined /> 版本对比
        </Title>
      </div>

      <div className={styles.selector}>
        <Space>
          <Select
            value={oldVersion}
            onChange={setOldVersion}
            placeholder="选择旧版本"
            style={{ width: 200 }}
          >
            {versions.map(v => (
              <Option key={v.id} value={v.id}>{v.version} - {v.comment}</Option>
            ))}
          </Select>

          <Button icon={<SwapOutlined />} onClick={handleSwap} />

          <Select
            value={newVersion}
            onChange={setNewVersion}
            placeholder="选择新版本"
            style={{ width: 200 }}
          >
            {versions.map(v => (
              <Option key={v.id} value={v.id}>{v.version} - {v.comment}</Option>
            ))}
          </Select>

          <Button type="primary" onClick={handleCompare} loading={loading}>
            对比
          </Button>
        </Space>
      </div>

      {diffResult && (
        <>
          <div className={styles.stats}>
            <Row gutter={24}>
              <Col span={6}>
                <Statistic
                  title="相似度"
                  value={diffResult.similarity * 100}
                  suffix="%"
                  precision={1}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="新增"
                  value={diffResult.stats.insertions}
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<PlusOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="删除"
                  value={diffResult.stats.deletions}
                  valueStyle={{ color: '#ff4d4f' }}
                  prefix={<MinusOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="修改"
                  value={diffResult.stats.modifications}
                  valueStyle={{ color: '#faad14' }}
                  prefix={<EditOutlined />}
                />
              </Col>
            </Row>
          </div>

          <Tabs activeKey={viewMode} onChange={(k) => setViewMode(k as any)}>
            <TabPane tab="并排对比" key="side" />
            <TabPane tab="统一视图" key="unified" />
          </Tabs>

          {renderDiffContent()}
        </>
      )}
    </Card>
  )
}

export default VersionDiff
