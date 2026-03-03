/**
 * 侧边栏组件
 */

import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  FileTextOutlined,
  BookOutlined,
  SearchOutlined,
  SettingOutlined,
  TeamOutlined,
  BulbOutlined,
  CalendarOutlined,
  ShareAltOutlined,
  BookFilled,
  SafetyOutlined,
  FormatPainterOutlined,
  LinkOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import styles from './Sidebar.module.css'

const { Sider } = Layout

interface SidebarProps {
  collapsed: boolean
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed }) => {
  const navigate = useNavigate()
  const location = useLocation()

  // 获取当前选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname
    if (path === '/dashboard' || path === '/') return '/dashboard'
    if (path.startsWith('/papers')) return '/papers'
    if (path.startsWith('/library/search')) return '/library/search'
    if (path.startsWith('/library')) return '/library'
    if (path.startsWith('/references')) return '/references'
    if (path.startsWith('/plagiarism')) return '/plagiarism'
    if (path.startsWith('/format')) return '/format'
    if (path.startsWith('/defense')) return '/defense'
    if (path.startsWith('/settings')) return '/settings'
    return '/dashboard'
  }

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/papers',
      icon: <FileTextOutlined />,
      label: '我的论文',
    },
    {
      key: '/library',
      icon: <BookOutlined />,
      label: '文献库',
    },
    {
      key: '/library/search',
      icon: <SearchOutlined />,
      label: '文献搜索',
    },
    {
      key: '/topic',
      icon: <BulbOutlined />,
      label: '选题助手',
    },
    {
      key: '/progress',
      icon: <CalendarOutlined />,
      label: '进度管理',
    },
    {
      key: '/knowledge',
      icon: <ShareAltOutlined />,
      label: '知识图谱',
    },
    {
      key: '/journal',
      icon: <BookFilled />,
      label: '期刊匹配',
    },
    {
      key: '/references',
      icon: <LinkOutlined />,
      label: '参考文献',
    },
    {
      key: '/plagiarism',
      icon: <SafetyOutlined />,
      label: '查重检测',
    },
    {
      key: '/format',
      icon: <FormatPainterOutlined />,
      label: '格式排版',
    },
    {
      key: '/defense',
      icon: <TrophyOutlined />,
      label: '答辩准备',
    },
    {
      key: '/teams',
      icon: <TeamOutlined />,
      label: '团队管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ]

  return (
    <Sider
      className={styles.sider}
      collapsed={collapsed}
      width={240}
      collapsedWidth={80}
      theme="light"
    >
      {/* Logo */}
      <div className={styles.logo}>
        <div className={styles.logoIcon}>
          <svg viewBox="0 0 24 24" width="32" height="32" fill="#1890ff">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
        {!collapsed && (
          <div className={styles.logoText}>
            <span className={styles.logoTitle}>ScholarForge</span>
            <span className={styles.logoSubtitle}>学术锻造</span>
          </div>
        )}
      </div>

      {/* 导航菜单 */}
      <Menu
        mode="inline"
        selectedKeys={[getSelectedKey()]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
        className={styles.menu}
      />
    </Sider>
  )
}

export default Sidebar
