/**
 * 协作工作空间组件
 * 整合实时编辑、评论、版本历史等协作功能
 */

import React, { useState } from 'react'
import {
  Card,
  Tabs,
  Button,
  Space,
  Avatar,
  Badge,
  Tooltip,
  Typography,
  List,
  Tag,
  Divider,
  Empty,
  message
} from 'antd'
import {
  EditOutlined,
  CommentOutlined,
  HistoryOutlined,
  TeamOutlined,
  ShareAltOutlined,
  EyeOutlined,
  SaveOutlined,
  CloudSyncOutlined
} from '@ant-design/icons'
import CollaborativeEditor from './CollaborativeEditor'
import CommentSidebar from './CommentSidebar'
import VersionHistoryPanel from './VersionHistoryPanel'
import CollaborationStatus from './CollaborationStatus'
import styles from './Collaboration.module.css'

const { Title, Text } = Typography
const { TabPane } = Tabs

interface ActiveUser {
  id: string
  name: string
  avatar?: string
  color: string
  cursor?: { x: number; y: number }
  isEditing?: boolean
}

interface CollaborativeWorkspaceProps {
  documentId: string
  documentTitle: string
  currentUser: {
    id: string
    name: string
    avatar?: string
  }
  initialContent?: string
}

const CollaborativeWorkspace: React.FC<CollaborativeWorkspaceProps> = ({
  documentId,
  documentTitle,
  currentUser,
  initialContent = ''
}) => {
  const [activeTab, setActiveTab] = useState('edit')
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([
    { id: 'user_1', name: '张教授', color: '#1890ff', isEditing: true },
    { id: 'user_2', name: '李博士', color: '#52c41a' },
    { id: currentUser.id, name: currentUser.name, color: '#faad14', isEditing: true }
  ])
  const [isSaving, setIsSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState<Date>(new Date())
  const [commentCount, setCommentCount] = useState(3)

  // 模拟保存
  const handleSave = async () => {
    setIsSaving(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      setLastSaved(new Date())
      message.success('文档已保存')
    } catch (error) {
      message.error('保存失败')
    } finally {
      setIsSaving(false)
    }
  }

  // 分享文档
  const handleShare = () => {
    Modal.info({
      title: '分享文档',
      content: (
        <div>
          <p>文档链接已复制到剪贴板</p>
          <Input
            value={`${window.location.origin}/collaborate/${documentId}`}
            readOnly
            addonAfter={<Button type="primary">复制</Button>}
          />
        </div>
      )
    })
  }

  // 渲染活跃用户头像
  const renderActiveUsers = () => (
    <Avatar.Group maxCount={4} size="small">
      {activeUsers.map(user => (
        <Tooltip key={user.id} title={user.name}>
          <Avatar
            style={{
              backgroundColor: user.color,
              border: user.isEditing ? `2px solid ${user.color}` : '2px solid transparent'
            }}
          >
            {user.name.charAt(0)}
          </Avatar>
        </Tooltip>
      ))}
    </Avatar.Group>
  )

  return (
    <div className={styles.workspace}>
      {/* 顶部工具栏 */}
      <Card className={styles.workspaceHeader} size="small">
        <div className={styles.headerContent}>
          <div className={styles.documentInfo}>
            <Title level={4} className={styles.documentTitle}>
              {documentTitle}
            </Title>
            <Space split={<Divider type="vertical" />}>
              <Text type="secondary" className={styles.saveStatus}>
                <CloudSyncOutlined spin={isSaving} />
                {isSaving ? '保存中...' : `上次保存: ${lastSaved.toLocaleTimeString()}`}
              </Text>
              <Badge status="success" text={`${activeUsers.length} 人在线`} />
            </Space>
          </div>

          <Space>
            {renderActiveUsers()}
            <Button icon={<ShareAltOutlined />} onClick={handleShare}>
              分享
            </Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              loading={isSaving}
              onClick={handleSave}
            >
              保存
            </Button>
          </Space>
        </div>
      </Card>

      {/* 主工作区 */}
      <div className={styles.workspaceBody}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          className={styles.workspaceTabs}
          type="card"
        >
          <TabPane
            tab={
              <span>
                <EditOutlined /> 编辑
              </span>
            }
            key="edit"
          >
            <div className={styles.editorContainer}>
              <CollaborativeEditor
                documentId={documentId}
                currentUser={currentUser}
                initialContent={initialContent}
                onSave={handleSave}
              />
            </div>
          </TabPane>

          <TabPane
            tab={
              <span>
                <CommentOutlined />
                评论
                {commentCount > 0 && (
                  <Badge count={commentCount} offset={[8, -2]} size="small" />
                )}
              </span>
            }
            key="comments"
          >
            <div className={styles.commentsContainer}>
              <CommentSidebar
                documentId={documentId}
                currentUser={currentUser}
                onCommentCountChange={setCommentCount}
              />
            </div>
          </TabPane>

          <TabPane
            tab={
              <span>
                <HistoryOutlined /> 历史版本
              </span>
            }
            key="history"
          >
            <div className={styles.historyContainer}>
              <VersionHistoryPanel
                documentId={documentId}
                onRestore={(version) => {
                  message.success(`已恢复到版本: ${version}`)
                }}
              />
            </div>
          </TabPane>

          <TabPane
            tab={
              <span>
                <TeamOutlined /> 协作成员
              </span>
            }
            key="members"
          >
            <Card title="在线成员">
              <List
                dataSource={activeUsers}
                renderItem={user => (
                  <List.Item
                    actions={[
                      user.isEditing ? (
                        <Tag color="processing">编辑中</Tag>
                      ) : (
                        <Tag>查看中</Tag>
                      )
                    ]}
                  >
                    <List.Item.Meta
                      avatar={
                        <Avatar style={{ backgroundColor: user.color }}>
                          {user.name.charAt(0)}
                        </Avatar>
                      }
                      title={user.name}
                      description={user.id === currentUser.id ? '我' : '团队成员'}
                    />
                  </List.Item>
                )}
              />
            </Card>
          </TabPane>
        </Tabs>
      </div>

      {/* 协作状态指示器 */}
      <CollaborationStatus
        connected={true}
        collaborators={activeUsers.length}
      />
    </div>
  )
}

// 简单的 Modal 和 Input 组件导入
import { Modal, Input } from 'antd'

export default CollaborativeWorkspace
