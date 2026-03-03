/**
 * 保存状态指示器组件
 */

import React from 'react'
import { Typography, Space, Tooltip, Button } from 'antd'
import {
  CheckCircleOutlined,
  SyncOutlined,
  ExclamationCircleOutlined,
  SaveOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

import type { SaveStatus } from '@/hooks/useAutoSave'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text } = Typography

interface SaveIndicatorProps {
  status: SaveStatus
  lastSavedAt: Date | null
  hasUnsavedChanges: boolean
  error?: Error | null
  onRetry?: () => void
}

const SaveIndicator: React.FC<SaveIndicatorProps> = ({
  status,
  lastSavedAt,
  hasUnsavedChanges,
  error,
  onRetry,
}) => {
  const getStatusDisplay = () => {
    switch (status) {
      case 'saving':
        return {
          icon: <SyncOutlined spin />,
          text: '保存中...',
          color: '#1890ff',
        }
      case 'saved':
        return {
          icon: <CheckCircleOutlined />,
          text: '已保存',
          color: '#52c41a',
        }
      case 'error':
        return {
          icon: <ExclamationCircleOutlined />,
          text: '保存失败',
          color: '#ff4d4f',
        }
      default:
        if (hasUnsavedChanges) {
          return {
            icon: <ClockCircleOutlined />,
            text: '有未保存的更改',
            color: '#faad14',
          }
        }
        return {
          icon: <SaveOutlined />,
          text: '已保存',
          color: '#52c41a',
        }
    }
  }

  const { icon, text, color } = getStatusDisplay()

  const formatLastSaved = () => {
    if (!lastSavedAt) return null
    return dayjs(lastSavedAt).fromNow()
  }

  return (
    <Space size="small">
      <Tooltip title={error?.message || (lastSavedAt ? `上次保存: ${formatLastSaved()}` : text)}>
        <Text style={{ color, fontSize: 12 }}>
          <Space size={4}>
            {icon}
            {text}
          </Space>
        </Text>
      </Tooltip>

      {status === 'error' && onRetry && (
        <Button size="small" type="link" onClick={onRetry}>
          重试
        </Button>
      )}
    </Space>
  )
}

export default SaveIndicator
