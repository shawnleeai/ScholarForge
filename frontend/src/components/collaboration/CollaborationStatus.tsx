/**
 * 协作状态组件
 */

import React from 'react'
import styles from './Collaboration.module.css'

interface CollaborationStatusProps {
  isConnected: boolean
  userCount: number
}

const CollaborationStatus: React.FC<CollaborationStatusProps> = ({
  isConnected,
  userCount,
}) => {
  return (
    <div
      className={`${styles.collaborationStatus} ${
        isConnected ? styles.connected : styles.disconnected
      }`}
    >
      <span className={styles.statusDot} />
      <span>
        {isConnected
          ? `已连接 · ${userCount} 人在线`
          : '离线模式'}
      </span>
    </div>
  )
}

export default CollaborationStatus
