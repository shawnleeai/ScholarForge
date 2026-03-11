/**
 * 演示状态管理组件
 * 提供演示模式的全局状态管理
 */

import React, { createContext, useContext, useState, useCallback } from 'react'
import { message } from 'antd'
import { demoSteps, samplePapers, demoQA } from './demoData'

interface DemoContextType {
  isDemoMode: boolean
  currentStep: number
  totalSteps: number
  demoData: {
    papers: typeof samplePapers
    qa: typeof demoQA
  }
  startDemo: () => void
  endDemo: () => void
  nextStep: () => void
  prevStep: () => void
  goToStep: (step: number) => void
  resetDemo: () => void
}

const DemoContext = createContext<DemoContextType | undefined>(undefined)

interface DemoProviderProps {
  children: React.ReactNode
}

export const DemoProvider: React.FC<DemoProviderProps> = ({ children }) => {
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  // 开始演示
  const startDemo = useCallback(() => {
    setIsDemoMode(true)
    setCurrentStep(0)
    message.success('演示模式已启动，跟随引导了解产品功能')

    // 记录演示开始事件
    if (typeof window !== 'undefined' && (window as any).gtag) {
      ;(window as any).gtag('event', 'demo_start', {
        event_category: 'demo',
        event_label: 'guided_tour'
      })
    }
  }, [])

  // 结束演示
  const endDemo = useCallback(() => {
    setIsDemoMode(false)
    setCurrentStep(0)

    // 清理高亮
    document.querySelectorAll('.tour-highlight').forEach(el => {
      el.classList.remove('tour-highlight')
    })
  }, [])

  // 下一步
  const nextStep = useCallback(() => {
    if (currentStep < demoSteps.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      // 演示完成
      message.success('恭喜！您已完成产品导览')

      // 记录演示完成事件
      if (typeof window !== 'undefined' && (window as any).gtag) {
        ;(window as any).gtag('event', 'demo_complete', {
          event_category: 'demo',
          event_label: 'guided_tour',
          value: demoSteps.length
        })
      }

      endDemo()
    }
  }, [currentStep, endDemo])

  // 上一步
  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1)
    }
  }, [currentStep])

  // 跳转到指定步骤
  const goToStep = useCallback((step: number) => {
    if (step >= 0 && step < demoSteps.length) {
      setCurrentStep(step)
    }
  }, [])

  // 重置演示
  const resetDemo = useCallback(() => {
    setCurrentStep(0)
    message.info('演示已重置')
  }, [])

  const value: DemoContextType = {
    isDemoMode,
    currentStep,
    totalSteps: demoSteps.length,
    demoData: {
      papers: samplePapers,
      qa: demoQA
    },
    startDemo,
    endDemo,
    nextStep,
    prevStep,
    goToStep,
    resetDemo
  }

  return (
    <DemoContext.Provider value={value}>
      {children}
    </DemoContext.Provider>
  )
}

// Hook for using demo context
export const useDemo = (): DemoContextType => {
  const context = useContext(DemoContext)
  if (context === undefined) {
    throw new Error('useDemo must be used within a DemoProvider')
  }
  return context
}

// 演示数据Hook
export const useDemoData = () => {
  const { demoData } = useDemo()
  return demoData
}

// 演示步骤Hook
export const useDemoStep = () => {
  const { currentStep, totalSteps, nextStep, prevStep, goToStep } = useDemo()
  return {
    currentStep,
    totalSteps,
    nextStep,
    prevStep,
    goToStep,
    currentStepData: demoSteps[currentStep]
  }
}

export default DemoProvider
