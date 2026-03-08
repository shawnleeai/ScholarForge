/**
 * 加载动画组件
 */

import React from 'react'
import { Spin } from 'antd'

interface LoadingSpinnerProps {
  tip?: string
  size?: 'small' | 'default' | 'large'
  fullscreen?: boolean
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  tip = '加载中...',
  size = 'large',
  fullscreen = false
}) => {
  if (fullscreen) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999
      }}>
        <Spin size={size} tip={tip} />
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '40px 0'
    }}>
      <Spin size={size} tip={tip} />
    </div>
  )
}

export default LoadingSpinner
