/**
 * 版本历史面板
 * 显示文档版本历史，支持对比和回滚
 */

import React, { useState, useCallback, useEffect } from 'react'
import * as Y from 'yjs'
import {
  Modal,
  List,
  Button,
  Space,
  Tag,
  Popconfirm,
  message,
  Empty,
  Tooltip,
  Timeline,
  Typography,
  Badge,
} from 'antd'
import {
  HistoryOutlined,
  RollbackOutlined,
  EyeOutlined,
  DownloadOutlined,
  DeleteOutlined,
  FileTextOutlined,
  EditOutlined,
  PlusOutlined,
  MinusOutlined,
} from '@ant-design/icons'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'

import {
  VersionManager,
  VersionInfo,
  UserInfo,
  formatVersionTime,
  formatRelativeTime,
} from '../../services/collaboration'
import styles from './Collaboration.module.css'

const { Text, Title } = Typography

interface VersionHistoryPanelProps {
  versionManager: VersionManager
  ydoc: Y.Doc
  currentUser: UserInfo
  onClose: () => void
  visible: boolean
}

export const VersionHistoryPanel: React.FC<VersionHistoryPanelProps> = ({
  versionManager,
  ydoc,
  currentUser,
  onClose,
  visible,
}) => {
  const [versions, setVersions] = useState<VersionInfo[]>([])
  const [selectedVersion, setSelectedVersion] = useState<VersionInfo | null>(null)
  const [compareMode, setCompareMode] = useState(false)
  const [oldVersionId, setOldVersionId] = useState<string | null>(null)
  const [newVersionId, setNewVersionId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // 加载版本列表
  useEffect(() => {
    if (visible) {
      loadVersions()
    }
  }, [visible])

  const loadVersions = () => {
    const allVersions = versionManager.getVersions()
    setVersions(allVersions)
  }

  // 创建预览编辑器
  const previewEditor = useEditor({
    extensions: [StarterKit],
    editable: false,
    content: '',
  })

  // 查看版本
  const handleViewVersion = useCallback(
    (version: VersionInfo) => {
      setSelectedVersion(version)
      setCompareMode(false)

      // 创建临时文档预览
      const tempDoc = new Y.Doc()
      Y.applyUpdate(tempDoc, version.snapshot)
      const text = tempDoc.getText('content').toString()

      previewEditor?.commands.setContent(text)
    },
    [previewEditor]
  )

  // 比较版本
  const handleCompare = useCallback(() => {
    if (!oldVersionId || !newVersionId) {
      message.warning('请选择两个版本进行比较')
      return
    }

    const result = versionManager.compareVersions(oldVersionId, newVersionId)
    if (result) {
      setCompareMode(true)
      // 显示差异视图
      message.info(`发现 ${result.changes.length} 处变更`)
    }
  }, [oldVersionId, newVersionId, versionManager])

  // 回滚到版本
  const handleRestore = useCallback(
    async (version: VersionInfo) => {
      setLoading(true)
      try {
        const success = await versionManager.restoreVersion(version.id)
        if (success) {
          message.success(`已回滚到 ${formatVersionTime(version.timestamp)}`)
          loadVersions()
        } else {
          message.error('回滚失败')
        }
      } finally {
        setLoading(false)
      }
    },
    [versionManager]
  )

  // 导出版本
  const handleExport = useCallback(() => {
    const json = versionManager.exportVersions()
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `versions-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
    message.success('版本历史已导出')
  }, [versionManager])

  // 清理旧版本
  const handleCleanup = useCallback(() => {
    const removed = versionManager.cleanupOldVersions(50)
    message.success(`已清理 ${removed} 个旧版本`)
    loadVersions()
  }, [versionManager])

  // 创建新版本
  const handleCreateVersion = useCallback(() => {
    const version = versionManager.createVersion(
      currentUser.name,
      currentUser.id,
      '手动保存'
    )
    message.success('新版本已创建')
    loadVersions()
    setSelectedVersion(version)
  }, [versionManager, currentUser])

  // 渲染版本差异标签
  const renderDiffTag = (diff?: { added: number; removed: number; modified: number }) => {
    if (!diff) return null

    return (
      <Space size={4}>
        {diff.added > 0 && (
          <Tag color="green" icon={<PlusOutlined />}>
            +{diff.added}
          </Tag>
        )}
        {diff.removed > 0 && (
          <Tag color="red" icon={<MinusOutlined />}>
            -{diff.removed}
          </Tag>
        )}
        {diff.modified > 0 && (
          <Tag color="blue" icon={<EditOutlined />}>
            ~{diff.modified}
          </Tag>
        )}
      </Space>
    )
  }

  return (
    <Modal
      title={
        <Space>
          <HistoryOutlined />
          版本历史
          <Badge count={versions.length} showZero color="#108ee9" />
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={900}
      footer={
        <Space>
          <Button onClick={handleExport} icon={<DownloadOutlined />}>
            导出
          </Button>
          <Button onClick={handleCleanup} icon={<DeleteOutlined />}>
            清理旧版本
          </Button>
          <Button type="primary" onClick={handleCreateVersion} icon={<PlusOutlined />}>
            创建版本
          </Button>
        </Space>
      }
    >
      <div className={styles.versionPanel}>
        {/* 版本列表 */}
        <div className={styles.versionList}>
          {versions.length === 0 ? (
            <Empty description="暂无版本历史" />
          ) : (
            <Timeline mode="left">
              {versions.map((version, index) => (
                <Timeline.Item key={version.id}>
                  <div
                    className={`${styles.versionItem} ${
                      selectedVersion?.id === version.id ? styles.selected : ''
                    }`}
                    onClick={() => handleViewVersion(version)}
                  >
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      <Space>
                        <Text strong>版本 {index + 1}</Text>
                        {index === versions.length - 1 && (
                          <Tag color="green">最新</Tag>
                        )}
                      </Space>
                      <Text type="secondary">{formatVersionTime(version.timestamp)}</Text>
                      <Text type="secondary">
                        <FileTextOutlined /> {version.author}
                      </Text>
                      {version.message && (
                        <Text type="secondary" ellipsis>
                          {version.message}
                        </Text>
                      )}
                      {renderDiffTag(version.diff)}
                      <Space>
                        <Tooltip title="查看">
                          <Button
                            size="small"
                            icon={<EyeOutlined />}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleViewVersion(version)
                            }}
                          />
                        </Tooltip>
                        <Tooltip title="回滚">
                          <Popconfirm
                            title="确定要回滚到这个版本吗？"
                            description="当前内容将被保存为版本，然后回滚到选中版本。"
                            onConfirm={() => handleRestore(version)}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button
                              size="small"
                              icon={<RollbackOutlined />}
                              danger
                              onClick={(e) => e.stopPropagation()}
                            />
                          </Popconfirm>
                        </Tooltip>
                      </Space>
                    </Space>
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          )}
        </div>

        {/* 预览区域 */}
        <div className={styles.versionPreview}>
          {selectedVersion ? (
            <>
              <Title level={5}>
                {compareMode ? '版本对比' : `版本预览 - ${formatVersionTime(selectedVersion.timestamp)}`}
              </Title>
              <div className={styles.previewContent}>
                <EditorContent editor={previewEditor} />
              </div>
            </>
          ) : (
            <Empty description="选择一个版本查看内容" />
          )}
        </div>
      </div>
    </Modal>
  )
}

export default VersionHistoryPanel
