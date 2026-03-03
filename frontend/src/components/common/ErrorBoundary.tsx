/**
 * 全局错误边界组件
 * 捕获子组件树中的 JavaScript 错误，防止整个应用崩溃
 */

import { Component, ErrorInfo, ReactNode } from 'react'
import { Result, Button, Typography, Space } from 'antd'
import { BugOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons'

const { Paragraph, Text } = Typography

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo })
    this.props.onError?.(error, errorInfo)

    // 在开发环境下输出详细错误信息
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error)
      console.error('Component stack:', errorInfo.componentStack)
    }
  }

  handleReload = (): void => {
    window.location.reload()
  }

  handleGoHome = (): void => {
    window.location.href = '/'
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state
    const { children, fallback } = this.props

    if (hasError) {
      if (fallback) {
        return fallback
      }

      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          background: '#f5f5f5',
          padding: '24px'
        }}>
          <Result
            status="error"
            icon={<BugOutlined style={{ color: '#ff4d4f' }} />}
            title="页面出错了"
            subTitle="抱歉，页面遇到了一些问题。请尝试刷新页面或返回首页。"
            extra={[
              <Button
                key="reload"
                type="primary"
                icon={<ReloadOutlined />}
                onClick={this.handleReload}
              >
                刷新页面
              </Button>,
              <Button
                key="home"
                icon={<HomeOutlined />}
                onClick={this.handleGoHome}
              >
                返回首页
              </Button>,
            ]}
          >
            {import.meta.env.DEV && error && (
              <div style={{ textAlign: 'left', maxWidth: '600px', margin: '0 auto' }}>
                <Paragraph>
                  <Text strong style={{ color: '#ff4d4f' }}>
                    错误信息：
                  </Text>
                </Paragraph>
                <Paragraph>
                  <Text code style={{ color: '#ff4d4f' }}>
                    {error.toString()}
                  </Text>
                </Paragraph>
                {errorInfo?.componentStack && (
                  <>
                    <Paragraph>
                      <Text strong>组件堆栈：</Text>
                    </Paragraph>
                    <pre style={{
                      fontSize: '12px',
                      overflow: 'auto',
                      maxHeight: '200px',
                      background: '#f6f6f6',
                      padding: '12px',
                      borderRadius: '4px',
                      border: '1px solid #e8e8e8'
                    }}>
                      {errorInfo.componentStack}
                    </pre>
                  </>
                )}
                <Space style={{ marginTop: '16px' }}>
                  <Button size="small" onClick={this.handleReset}>
                    尝试恢复
                  </Button>
                </Space>
              </div>
            )}
          </Result>
        </div>
      )
    }

    return children
  }
}

export default ErrorBoundary
