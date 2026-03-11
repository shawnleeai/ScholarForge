/**
 * 主题设置组件
 * 支持切换预设主题、暗黑/明亮模式、自定义颜色
 */

import React, { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Button,
  Radio,
  Space,
  Typography,
  Slider,
  ColorPicker,
  Divider,
  message,
  Modal,
} from 'antd'
import {
  BgColorsOutlined,
  MoonOutlined,
  SunOutlined,
  DesktopOutlined,
  CheckOutlined,
  EditOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { useThemeStore, themePresets, type ThemePreset, type ThemeConfig } from '@/stores/themeStore'
import styles from './ThemeSettings.module.css'

const { Title, Text } = Typography

// 主题预览卡片
const ThemePreviewCard: React.FC<{
  preset: ThemePreset
  config: ThemeConfig
  isActive: boolean
  isDark: boolean
  onClick: () => void
}> = ({ preset, config, isActive, isDark, onClick }) => {
  const presetNames: Record<ThemePreset, string> = {
    default: '默认',
    academic: '学术蓝',
    nature: '自然绿',
    tech: '科技紫',
    warm: '暖色调',
    cool: '冷色调',
    eyeCare: '护眼模式',
  }

  const presetDescriptions: Record<ThemePreset, string> = {
    default: '经典蓝白配色，适合日常使用',
    academic: '沉稳学术风，适合论文写作',
    nature: '清新自然绿，护眼舒适',
    tech: '深色科技风，适合夜间使用',
    warm: '温暖橙色调，减轻视觉疲劳',
    cool: '清爽蓝色调，专注高效',
    eyeCare: '护眼豆绿色，长时间阅读',
  }

  return (
    <div
      className={`${styles.previewCard} ${isActive ? styles.active : ''}`}
      onClick={onClick}
      style={{
        background: isDark ? config.bgSecondary : config.bgColor,
        borderColor: isActive ? config.primaryColor : config.borderColor,
        borderRadius: config.borderRadius,
        boxShadow: isActive
          ? `0 0 0 2px ${config.primaryColor}40`
          : `0 2px 8px ${isDark ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.08)'}`,
      }}
    >
      <div className={styles.previewHeader}>
        <div
          className={styles.colorDot}
          style={{ background: config.primaryColor }}
        />
        <Text strong style={{ color: config.textPrimary }}>
          {presetNames[preset]}
        </Text>
        {isActive && (
          <CheckOutlined style={{ color: config.successColor }} />
        )}
      </div>

      <div
        className={styles.previewContent}
        style={{
          background: config.bgSecondary,
          borderRadius: config.borderRadius,
        }}
      >
        <div
          className={styles.previewButton}
          style={{
            background: config.primaryColor,
            borderRadius: config.borderRadius,
          }}
        />
        <div className={styles.previewLines}>
          <div
            className={styles.previewLine}
            style={{ background: config.textSecondary, opacity: 0.6 }}
          />
          <div
            className={styles.previewLine}
            style={{
              background: config.textSecondary,
              opacity: 0.4,
              width: '70%',
            }}
          />
        </div>
      </div>

      <Text
        type="secondary"
        className={styles.previewDesc}
        style={{ color: config.textTertiary }}
      >
        {presetDescriptions[preset]}
      </Text>
    </div>
  )
}

// 主组件
const ThemeSettings: React.FC = () => {
  const { mode, preset, isDark, setMode, setPreset, currentTheme } = useThemeStore()
  const [customEditorVisible, setCustomEditorVisible] = useState(false)

  return (
    <div className={styles.themeSettings}>
      <Card title="外观设置" className={styles.mainCard}>
        {/* 明暗模式选择 */}
        <div className={styles.section}>
          <Title level={5}>
            <BgColorsOutlined /> 显示模式
          </Title>
          <Radio.Group
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            buttonStyle="solid"
          >
            <Radio.Button value="light">
              <SunOutlined /> 浅色
            </Radio.Button>
            <Radio.Button value="dark">
              <MoonOutlined /> 深色
            </Radio.Button>
            <Radio.Button value="system">
              <DesktopOutlined /> 跟随系统
            </Radio.Button>
          </Radio.Group>
          <Text type="secondary" className={styles.hint}>
            {mode === 'system' && '将根据系统设置自动切换'}
          </Text>
        </div>

        <Divider />

        {/* 预设主题 */}
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <Title level={5}>
              <EyeOutlined /> 主题风格
            </Title>
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => setCustomEditorVisible(true)}
            >
              自定义
            </Button>
          </div>

          <Row gutter={[16, 16]}>
            {(Object.keys(themePresets) as ThemePreset[]).map((p) => (
              <Col xs={24} sm={12} md={8} key={p}>
                <ThemePreviewCard
                  preset={p}
                  config={themePresets[p]}
                  isActive={preset === p}
                  isDark={isDark}
                  onClick={() => setPreset(p)}
                />
              </Col>
            ))}
          </Row>
        </div>

        <Divider />

        {/* 当前主题信息 */}
        <div className={styles.section}>
          <Title level={5}>当前主题</Title>
          <Space direction="vertical">
            <Text>
              主题预设: <span style={{ color: currentTheme.primaryColor }}>{preset}</span>
            </Text>
            <Text>
              显示模式: {isDark ? '深色' : '浅色'}
            </Text>
            <Text>
              圆角大小: {currentTheme.borderRadius}px
            </Text>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default ThemeSettings
