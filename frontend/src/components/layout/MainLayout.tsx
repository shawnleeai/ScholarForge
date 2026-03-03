/**
 * 主布局组件
 */

import React from 'react'
import { Outlet } from 'react-router-dom'
import { Layout } from 'antd'
import Sidebar from './Sidebar'
import Header from './Header'
import AIPanel from '@/components/ai/AIPanel'
import { useUIStore } from '@/stores'
import styles from './MainLayout.module.css'

const { Content } = Layout

const MainLayout: React.FC = () => {
  const { sidebarCollapsed, aiPanelVisible } = useUIStore()

  return (
    <Layout className={styles.layout}>
      {/* 侧边栏 */}
      <Sidebar collapsed={sidebarCollapsed} />

      {/* 主内容区 */}
      <Layout
        className={styles.mainLayout}
        style={{
          marginLeft: sidebarCollapsed ? 80 : 240,
          marginRight: aiPanelVisible ? 400 : 0,
          transition: 'margin 0.2s ease',
        }}
      >
        {/* 顶部导航 */}
        <Header />

        {/* 内容区域 */}
        <Content className={styles.content}>
          <Outlet />
        </Content>
      </Layout>

      {/* AI 助手面板 */}
      {aiPanelVisible && <AIPanel />}
    </Layout>
  )
}

export default MainLayout
