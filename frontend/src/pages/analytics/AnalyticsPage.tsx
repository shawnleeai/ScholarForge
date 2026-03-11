/**
 * 学术影响力分析页面
 */

import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Typography } from 'antd'
import { ArrowLeftOutlined, TrophyOutlined } from '@ant-design/icons'
import { ImpactDashboard } from '@/components/analytics'

const { Title } = Typography

const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div style={{ padding: 24 }}>
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/dashboard')}>
            返回
          </Button>
          <Title level={3} style={{ margin: 0 }}>
            <TrophyOutlined /> 学术影响力分析
          </Title>
        </div>
      </Card>

      <ImpactDashboard authorId="current-user" />
    </div>
  )
}

export default AnalyticsPage
