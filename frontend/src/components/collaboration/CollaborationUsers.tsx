/**
 * 协作用户列表组件
 */

import React from 'react'
import { Avatar, Tooltip, Space } from 'antd'
import { UserOutlined } from '@ant-design/icons'
import type { CollaborationUser } from '@/services/collaborationService'
import styles from './Collaboration.module.css'

interface CollaborationUsersProps {
  users: CollaborationUser[]
  maxDisplay?: number
}

const CollaborationUsers: React.FC<CollaborationUsersProps> = ({
  users,
  maxDisplay = 5,
}) => {
  const displayUsers = users.slice(0, maxDisplay)
  const remainingCount = users.length - maxDisplay

  return (
    <div className={styles.userList}>
      <Space size={-8}>
        {displayUsers.map((user) => (
          <Tooltip key={user.id} title={user.name}>
            <Avatar
              size="small"
              style={{ backgroundColor: user.color }}
              icon={<UserOutlined />}
              className={styles.userAvatar}
            >
              {user.name.charAt(0).toUpperCase()}
            </Avatar>
          </Tooltip>
        ))}
        {remainingCount > 0 && (
          <Avatar size="small" className={styles.moreAvatar}>
            +{remainingCount}
          </Avatar>
        )}
      </Space>
    </div>
  )
}

export default CollaborationUsers
