/**
 * 顶部导航组件
 */

import React from 'react'
import { Layout, Button, Avatar, Dropdown, Badge, Tooltip } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
  RobotOutlined,
  QuestionCircleOutlined,
  LogoutOutlined,
  UserOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore, useUIStore } from '@/stores'
import styles from './Header.module.css'

const { Header: AntHeader } = Layout

const Header: React.FC = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { sidebarCollapsed, toggleSidebar, toggleAIPanel, aiPanelVisible } = useUIStore()

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/settings'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout()
        navigate('/login')
      },
    },
  ]

  return (
    <AntHeader className={styles.header}>
      <div className={styles.left}>
        <Button
          type="text"
          icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleSidebar}
          className={styles.trigger}
        />
      </div>

      <div className={styles.right}>
        <Tooltip title="AI 写作助手">
          <Button
            type={aiPanelVisible ? 'primary' : 'text'}
            icon={<RobotOutlined />}
            onClick={toggleAIPanel}
          >
            AI 助手
          </Button>
        </Tooltip>

        <Tooltip title="帮助中心">
          <Button type="text" icon={<QuestionCircleOutlined />} />
        </Tooltip>

        <Tooltip title="通知">
          <Badge count={3} size="small">
            <Button type="text" icon={<BellOutlined />} />
          </Badge>
        </Tooltip>

        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <div className={styles.user}>
            <Avatar size="small" icon={<UserOutlined />} />
            <span className={styles.userName}>{user?.fullName || user?.username}</span>
          </div>
        </Dropdown>
      </div>
    </AntHeader>
  )
}

export default Header
