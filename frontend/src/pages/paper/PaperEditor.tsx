/**
 * 论文编辑器页面
 * 集成富文本编辑器、优化的自动保存功能和实时协作
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Layout,
  Menu,
  Button,
  message,
  Dropdown,
  Space,
  Tooltip,
  Spin,
  Typography,
  Input,
  Modal,
  Drawer,
  Avatar,
  List,
  Tag,
  Switch,
  Divider,
} from 'antd'
import {
  DownloadOutlined,
  RobotOutlined,
  FileTextOutlined,
  PlusOutlined,
  SettingOutlined,
  EyeOutlined,
  HistoryOutlined,
  TeamOutlined,
  UserOutlined,
  WifiOutlined,
  DisconnectOutlined,
  ShareAltOutlined,
  CommentOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'

import { paperService } from '@/services'
import { useCollaboration } from '@/services/collaborationService'
import { usePaperStore, useUIStore, useAuthStore } from '@/stores'
import { useAutoSave } from '@/hooks'
import { RichTextEditor } from '@/components/editor'
import { AIPanel } from '@/components/ai'
import SaveIndicator from '@/components/editor/SaveIndicator'
import CollaborationStatus from '@/components/collaboration/CollaborationStatus'
import CollaborationUsers from '@/components/collaboration/CollaborationUsers'
import type { Paper, PaperSection } from '@/types'
import styles from './PaperEditor.module.css'

const { Sider, Content } = Layout
const { Title, Text } = Typography

const PaperEditor: React.FC = () => {
  const { paperId, sectionId } = useParams<{ paperId: string; sectionId?: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const {
    currentPaper,
    sections,
    activeSectionId,
    setCurrentPaper,
    setSections,
    setActiveSection,
    updateSection,
  } = usePaperStore()

  const { toggleAIPanel, aiPanelVisible } = useUIStore()
  const { user } = useAuthStore()

  const [content, setContent] = useState('')
  const [renameModalVisible, setRenameModalVisible] = useState(false)
  const [newSectionTitle, setNewSectionTitle] = useState('')
  const [collabDrawerVisible, setCollabDrawerVisible] = useState(false)
  const [collaborationEnabled, setCollaborationEnabled] = useState(true)
  const [inviteModalVisible, setInviteModalVisible] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')

  // 协作功能
  const roomId = paperId ? `paper-${paperId}` : ''
  const {
    isConnected,
    users: collabUsers,
    getDoc,
    reconnect,
  } = useCollaboration(
    roomId,
    user?.id || '',
    user?.username || user?.fullName || '匿名用户',
    { enableOffline: true }
  )

  // 协作用户信息
  const collabUserInfo = useMemo(() => {
    const colors = ['#f5222d', '#fa8c16', '#fadb14', '#52c41a', '#13c2c2', '#1890ff', '#722ed1', '#eb2f96']
    return {
      name: user?.username || user?.fullName || '匿名用户',
      color: colors[Math.floor(Math.random() * colors.length)],
    }
  }, [user])

  // 获取论文详情
  useQuery({
    queryKey: ['paper', paperId],
    queryFn: async () => {
      const response = await paperService.getPaper(paperId!)
      setCurrentPaper(response.data as Paper)
      return response.data
    },
    enabled: !!paperId,
  })

  // 获取章节列表
  useQuery({
    queryKey: ['sections', paperId],
    queryFn: async () => {
      const response = await paperService.getSections(paperId!)
      const sectionList = response.data as PaperSection[]
      setSections(sectionList || [])
      return response.data
    },
    enabled: !!paperId,
  })

  // 更新章节
  const updateMutation = useMutation({
    mutationFn: (data: { sectionId: string; content: string }) =>
      paperService.updateSection(data.sectionId, { content: data.content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sections', paperId] })
    },
  })

  // 添加章节
  const addSectionMutation = useMutation({
    mutationFn: (data: { title: string }) =>
      paperService.createSection(paperId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sections', paperId] })
      message.success('章节已添加')
    },
  })

  // 添加协作者
  const addCollaboratorMutation = useMutation({
    mutationFn: (data: { userEmail: string; role: string }) =>
      paperService.addCollaborator(paperId!, data),
    onSuccess: () => {
      message.success('邀请已发送')
      setInviteModalVisible(false)
      setInviteEmail('')
    },
    onError: () => {
      message.error('邀请失败')
    },
  })

  // 设置活动章节
  useEffect(() => {
    if (sectionId) {
      setActiveSection(sectionId)
      const section = sections.find((s) => s.id === sectionId)
      if (section) setContent(section.content || '')
    } else if (sections.length > 0) {
      setActiveSection(sections[0].id)
      setContent(sections[0].content || '')
    }
  }, [sectionId, sections, setActiveSection])

  // 自动保存逻辑
  const performSave = useCallback(async () => {
    if (!activeSectionId) return
    await updateMutation.mutateAsync({ sectionId: activeSectionId, content })
    updateSection(activeSectionId, { content })
  }, [activeSectionId, content, updateMutation, updateSection])

  const {
    status: saveStatus,
    lastSavedAt,
    hasUnsavedChanges,
    save: manualSave,
    markDirty,
    error: saveError,
  } = useAutoSave({
    onSave: performSave,
    debounceMs: 2000,
    enableLocalBackup: true,
    backupKey: `paper_${paperId}_section_${activeSectionId}_backup`,
    maxRetries: 3,
  })

  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent)
    markDirty()
  }, [markDirty])

  const handleSectionSelect = (key: string) => {
    if (hasUnsavedChanges) {
      manualSave()
    }
    navigate(`/papers/${paperId}/sections/${key}`)
  }

  const handleAddSection = () => {
    setNewSectionTitle('')
    setRenameModalVisible(true)
  }

  const handleCreateSection = () => {
    if (newSectionTitle.trim()) {
      addSectionMutation.mutate({ title: newSectionTitle.trim() })
      setRenameModalVisible(false)
    }
  }

  const handleInviteCollaborator = () => {
    if (inviteEmail.trim()) {
      addCollaboratorMutation.mutate({ userEmail: inviteEmail.trim(), role: 'editor' })
    }
  }

  // 章节菜单项
  const menuItems = sections.map((section) => ({
    key: section.id,
    icon: <FileTextOutlined />,
    label: section.title || `章节 ${section.orderIndex}`,
  }))

  // 添加"添加章节"按钮
  const extraMenuItems = [
    ...menuItems,
    { type: 'divider' as const },
    {
      key: 'add',
      icon: <PlusOutlined />,
      label: '添加章节',
      onClick: handleAddSection,
    },
  ]

  // 导出选项
  const exportItems = [
    { key: 'docx', label: 'Word 文档 (.docx)', onClick: () => handleExport('docx') },
    { key: 'pdf', label: 'PDF 文档', onClick: () => handleExport('pdf') },
    { key: 'md', label: 'Markdown', onClick: () => handleExport('md') },
  ]

  const handleExport = async (format: string) => {
    try {
      const response = await paperService.exportPaper(paperId!, format)
      const exportData = response.data as { download_url?: string; downloadUrl?: string }
      const url = exportData?.download_url || exportData?.downloadUrl
      if (url) {
        window.open(url, '_blank')
        message.success('导出成功')
      }
    } catch {
      message.error('导出失败')
    }
  }

  if (!currentPaper) {
    return (
      <div className={styles.loading}>
        <Spin size="large" />
        <Text type="secondary" style={{ marginTop: 16 }}>
          加载中...
        </Text>
      </div>
    )
  }

  const activeSection = sections.find((s) => s.id === activeSectionId)

  // 协作配置
  const collaborationConfig = collaborationEnabled && isConnected && getDoc() ? {
    doc: getDoc()!,
    user: collabUserInfo,
  } : undefined

  return (
    <Layout className={styles.editorLayout}>
      {/* 左侧章节导航 */}
      <Sider width={260} className={styles.sider} theme="light">
        <div className={styles.siderHeader}>
          <Title level={5} ellipsis className={styles.paperTitle}>
            {currentPaper.title}
          </Title>
          <Space>
            <Tooltip title="协作设置">
              <Button
                type="text"
                size="small"
                icon={<TeamOutlined />}
                onClick={() => setCollabDrawerVisible(true)}
              />
            </Tooltip>
            <Tooltip title="设置">
              <Button type="text" size="small" icon={<SettingOutlined />} />
            </Tooltip>
          </Space>
        </div>

        {/* 协作状态 */}
        {collaborationEnabled && (
          <div className={styles.collabStatus}>
            <CollaborationStatus isConnected={isConnected} userCount={collabUsers.length} />
            {collabUsers.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <CollaborationUsers users={collabUsers} maxDisplay={4} />
              </div>
            )}
          </div>
        )}

        <div className={styles.stats}>
          <Space split={<Text type="secondary">|</Text>}>
            <Text type="secondary">{content.length} 字</Text>
            <Text type="secondary">{sections.length} 节</Text>
          </Space>
        </div>

        <Menu
          mode="inline"
          selectedKeys={[activeSectionId || '']}
          items={extraMenuItems}
          onClick={({ key }) => {
            if (key !== 'add') handleSectionSelect(key)
          }}
          className={styles.menu}
        />
      </Sider>

      {/* 主编辑区 */}
      <Content className={styles.content}>
        {/* 工具栏 */}
        <div className={styles.toolbar}>
          <div className={styles.toolbarLeft}>
            <Text strong>{activeSection?.title || '选择章节'}</Text>
          </div>

          <div className={styles.toolbarCenter}>
            <SaveIndicator
              status={saveStatus}
              lastSavedAt={lastSavedAt}
              hasUnsavedChanges={hasUnsavedChanges}
              error={saveError}
              onRetry={manualSave}
            />
          </div>

          <div className={styles.toolbarRight}>
            <Space>
              {/* 协作状态指示 */}
              {collaborationEnabled && (
                <Tooltip title={isConnected ? '协作已连接' : '协作离线'}>
                  <Button
                    type="text"
                    icon={isConnected ? <WifiOutlined style={{ color: '#52c41a' }} /> : <DisconnectOutlined style={{ color: '#ff4d4f' }} />}
                    onClick={reconnect}
                  />
                </Tooltip>
              )}

              <Tooltip title="评论">
                <Button icon={<CommentOutlined />} />
              </Tooltip>

              <Tooltip title="历史版本">
                <Button icon={<HistoryOutlined />} />
              </Tooltip>

              <Tooltip title="预览">
                <Button icon={<EyeOutlined />} />
              </Tooltip>

              <Button
                type={aiPanelVisible ? 'primary' : 'default'}
                icon={<RobotOutlined />}
                onClick={toggleAIPanel}
              >
                AI 助手
              </Button>

              <Button
                type="primary"
                onClick={manualSave}
                disabled={!hasUnsavedChanges}
                loading={saveStatus === 'saving'}
              >
                保存
              </Button>

              <Dropdown menu={{ items: exportItems }}>
                <Button icon={<DownloadOutlined />}>导出</Button>
              </Dropdown>
            </Space>
          </div>
        </div>

        {/* 编辑器 */}
        <div className={styles.editorContainer}>
          <RichTextEditor
            content={content}
            onChange={handleContentChange}
            placeholder="开始写作..."
            onSave={manualSave}
            showWordCount
            collaboration={collaborationConfig}
          />
        </div>
      </Content>

      {/* AI 助手面板 */}
      {aiPanelVisible && <AIPanel />}

      {/* 添加章节弹窗 */}
      <Modal
        title="添加新章节"
        open={renameModalVisible}
        onOk={handleCreateSection}
        onCancel={() => setRenameModalVisible(false)}
        confirmLoading={addSectionMutation.isPending}
      >
        <Input
          placeholder="输入章节标题"
          value={newSectionTitle}
          onChange={(e) => setNewSectionTitle(e.target.value)}
          onPressEnter={handleCreateSection}
        />
      </Modal>

      {/* 协作设置抽屉 */}
      <Drawer
        title="协作设置"
        placement="right"
        onClose={() => setCollabDrawerVisible(false)}
        open={collabDrawerVisible}
        width={360}
      >
        <div className={styles.collabDrawer}>
          <div className={styles.collabSection}>
            <div className={styles.sectionHeader}>
              <Text strong>实时协作</Text>
              <Switch
                checked={collaborationEnabled}
                onChange={setCollaborationEnabled}
              />
            </div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              启用后可与他人实时协作编辑
            </Text>
          </div>

          <Divider />

          <div className={styles.collabSection}>
            <div className={styles.sectionHeader}>
              <Text strong>在线协作者</Text>
              <Button
                type="link"
                size="small"
                icon={<ShareAltOutlined />}
                onClick={() => setInviteModalVisible(true)}
              >
                邀请
              </Button>
            </div>

            <List
              dataSource={collabUsers}
              renderItem={(u) => (
                <List.Item key={u.clientId}>
                  <List.Item.Meta
                    avatar={<Avatar style={{ backgroundColor: u.color }}>{u.name.charAt(0)}</Avatar>}
                    title={u.name}
                    description={u.id === user?.id ? '我' : '协作者'}
                  />
                  <Tag icon={<CheckCircleOutlined />} color="success">在线</Tag>
                </List.Item>
              )}
              locale={{ emptyText: '暂无其他协作者' }}
            />
          </div>
        </div>
      </Drawer>

      {/* 邀请协作者弹窗 */}
      <Modal
        title="邀请协作者"
        open={inviteModalVisible}
        onOk={handleInviteCollaborator}
        onCancel={() => setInviteModalVisible(false)}
        confirmLoading={addCollaboratorMutation.isPending}
      >
        <Input
          placeholder="输入协作者邮箱"
          value={inviteEmail}
          onChange={(e) => setInviteEmail(e.target.value)}
          prefix={<UserOutlined />}
          type="email"
        />
      </Modal>
    </Layout>
  )
}

export default PaperEditor
