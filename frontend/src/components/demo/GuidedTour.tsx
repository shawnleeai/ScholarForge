/**
 * 引导式交互演示组件
 * 步骤引导、高亮提示
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Button, Card, Space, Typography, Steps, Tooltip } from 'antd'
import {
  ArrowRightOutlined,
  ArrowLeftOutlined,
  CloseOutlined,
  PlayCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { demoSteps, DemoStep } from './demoData'
import styles from './GuidedTour.module.css'

const { Title, Text } = Typography

interface GuidedTourProps {
  isOpen: boolean
  onClose: () => void
  onComplete?: () => void
}

const GuidedTour: React.FC<GuidedTourProps> = ({
  isOpen,
  onClose,
  onComplete
}) => {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null)
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })

  const step = demoSteps[currentStep]

  // 查找目标元素
  useEffect(() => {
    if (!isOpen || !step) return

    const findTarget = () => {
      const element = document.querySelector(step.target) as HTMLElement
      if (element) {
        setTargetElement(element)
        highlightElement(element)
        calculatePosition(element, step.placement || 'bottom')
      }
    }

    // 延迟以确保DOM已渲染
    const timer = setTimeout(findTarget, 100)
    return () => clearTimeout(timer)
  }, [isOpen, currentStep, step])

  // 高亮元素
  const highlightElement = (element: HTMLElement) => {
    // 移除之前的高亮
    document.querySelectorAll('.tour-highlight').forEach(el => {
      el.classList.remove('tour-highlight')
    })

    // 添加高亮
    element.classList.add('tour-highlight')
  }

  // 计算提示框位置
  const calculatePosition = (
    element: HTMLElement,
    placement: string
  ) => {
    const rect = element.getBoundingClientRect()
    const tooltipWidth = 320
    const tooltipHeight = 200
    const offset = 16

    let x = 0
    let y = 0

    switch (placement) {
      case 'top':
        x = rect.left + rect.width / 2 - tooltipWidth / 2
        y = rect.top - tooltipHeight - offset
        break
      case 'bottom':
        x = rect.left + rect.width / 2 - tooltipWidth / 2
        y = rect.bottom + offset
        break
      case 'left':
        x = rect.left - tooltipWidth - offset
        y = rect.top + rect.height / 2 - tooltipHeight / 2
        break
      case 'right':
        x = rect.right + offset
        y = rect.top + rect.height / 2 - tooltipHeight / 2
        break
      default:
        x = rect.left + rect.width / 2 - tooltipWidth / 2
        y = rect.bottom + offset
    }

    // 边界检查
    x = Math.max(16, Math.min(x, window.innerWidth - tooltipWidth - 16))
    y = Math.max(16, Math.min(y, window.innerHeight - tooltipHeight - 16))

    setTooltipPosition({ x, y })
  }

  // 下一步
  const handleNext = useCallback(() => {
    // 执行步骤动作
    if (step.action) {
      step.action()
    }

    if (currentStep < demoSteps.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      handleComplete()
    }
  }, [currentStep, step])

  // 上一步
  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1)
    }
  }

  // 完成
  const handleComplete = () => {
    // 清理高亮
    document.querySelectorAll('.tour-highlight').forEach(el => {
      el.classList.remove('tour-highlight')
    })
    onComplete?.()
    onClose()
  }

  // 跳过
  const handleSkip = () => {
    document.querySelectorAll('.tour-highlight').forEach(el => {
      el.classList.remove('tour-highlight')
    })
    onClose()
  }

  // 重新开始
  const handleRestart = () => {
    setCurrentStep(0)
  }

  if (!isOpen || !step) return null

  return (
    <>
      {/* 遮罩层 */}
      <div className={styles.overlay} onClick={handleSkip} />

      {/* 高亮区域 */}
      {targetElement && (
        <div
          className={styles.highlight}
          style={{
            top: targetElement.getBoundingClientRect().top - 4,
            left: targetElement.getBoundingClientRect().left - 4,
            width: targetElement.getBoundingClientRect().width + 8,
            height: targetElement.getBoundingClientRect().height + 8
          }}
        />
      )}

      {/* 提示框 */}
      <Card
        className={styles.tooltip}
        style={{
          left: tooltipPosition.x,
          top: tooltipPosition.y
        }}
        title={
          <div className={styles.header}>
            <Title level={5} style={{ margin: 0 }}>
              {step.title}
            </Title>
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={handleSkip}
            />
          </div>
        }
        actions={[
          <Space key="actions" className={styles.actions}>
            <Text type="secondary">
              {currentStep + 1} / {demoSteps.length}
            </Text>
            <Button
              disabled={currentStep === 0}
              onClick={handlePrev}
              icon={<ArrowLeftOutlined />}
            >
              上一步
            </Button>
            <Button
              type="primary"
              onClick={handleNext}
              icon={currentStep === demoSteps.length - 1 ? undefined : <ArrowRightOutlined />}
            >
              {currentStep === demoSteps.length - 1 ? '完成' : '下一步'}
            </Button>
          </Space>
        ]}
      >
        <Text>{step.content}</Text>

        {/* 步骤指示器 */}
        <Steps
          current={currentStep}
          size="small"
          className={styles.steps}
          items={demoSteps.map((s, i) => ({
            title: '',
            status: i === currentStep ? 'process' : i < currentStep ? 'finish' : 'wait'
          }))}
        />
      </Card>
    </>
  )
}

// 演示启动按钮
export const DemoLauncher: React.FC = () => {
  const [isTourOpen, setIsTourOpen] = useState(false)

  return (
    <>
      <Tooltip title="开始产品导览">
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={() => setIsTourOpen(true)}
        >
          开始使用
        </Button>
      </Tooltip>

      <GuidedTour
        isOpen={isTourOpen}
        onClose={() => setIsTourOpen(false)}
        onComplete={() => {
          console.log('Tour completed')
        }}
      />
    </>
  )
}

// 演示模式指示器
export const DemoBadge: React.FC<{ onRestart: () => void }> = ({ onRestart }) => {
  return (
    <div className={styles.demoBadge}>
      <Space>
        <Text style={{ color: '#fff' }}>演示模式</Text>
        <Button
          type="primary"
          size="small"
          ghost
          icon={<ReloadOutlined />}
          onClick={onRestart}
        >
          重新播放
        </Button>
      </Space>
    </div>
  )
}

export default GuidedTour
