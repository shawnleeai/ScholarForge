/**
 * 认证页面布局
 */

import React from 'react'
import { Outlet } from 'react-router-dom'
import styles from './AuthLayout.module.css'

const AuthLayout: React.FC = () => {
  return (
    <div className={styles.container}>
      <div className={styles.left}>
        <div className={styles.brand}>
          <div className={styles.logo}>
            <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1 className={styles.title}>ScholarForge</h1>
          <p className={styles.subtitle}>学术锻造 - 一站式智能学术研究协作平台</p>
        </div>

        <div className={styles.features}>
          <div className={styles.featureItem}>
            <span className={styles.featureIcon}>📝</span>
            <div>
              <h3>智能写作</h3>
              <p>AI 驱动的学术写作助手</p>
            </div>
          </div>
          <div className={styles.featureItem}>
            <span className={styles.featureIcon}>📚</span>
            <div>
              <h3>文献管理</h3>
              <p>多源文献检索与推荐</p>
            </div>
          </div>
          <div className={styles.featureItem}>
            <span className={styles.featureIcon}>👥</span>
            <div>
              <h3>团队协作</h3>
              <p>实时协作与导师批注</p>
            </div>
          </div>
          <div className={styles.featureItem}>
            <span className={styles.featureIcon}>🔍</span>
            <div>
              <h3>期刊匹配</h3>
              <p>智能推荐适合的投稿期刊</p>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.right}>
        <Outlet />
      </div>
    </div>
  )
}

export default AuthLayout
