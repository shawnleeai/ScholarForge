/**
 * 登录页面
 */

import React, { useState } from 'react'
import { Form, Input, Button, Checkbox, message, Divider } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { Link, useNavigate, useLocation } from 'react-router-dom'

import { authService } from '@/services'
import { useAuthStore } from '@/stores'
import styles from './Auth.module.css'

const Login: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuthStore()
  const [loading, setLoading] = useState(false)

  const from = (location.state as any)?.from?.pathname || '/dashboard'

  const handleSubmit = async (values: { email: string; password: string; remember: boolean }) => {
    setLoading(true)
    try {
      const response = await authService.login(values)
      const { user, token } = response.data!

      login(user, token.accessToken, token.refreshToken)
      message.success('登录成功')
      navigate(from, { replace: true })
    } catch (error: any) {
      message.error(error.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.authForm}>
      <div className={styles.header}>
        <h2>欢迎回来</h2>
        <p>登录您的 ScholarForge 账户</p>
      </div>

      <Form
        name="login"
        onFinish={handleSubmit}
        layout="vertical"
        requiredMark={false}
        initialValues={{ remember: true }}
      >
        <Form.Item
          name="email"
          rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' },
          ]}
        >
          <Input
            prefix={<UserOutlined />}
            placeholder="邮箱地址"
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="password"
          rules={[
            { required: true, message: '请输入密码' },
            { min: 8, message: '密码至少8个字符' },
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="密码"
            size="large"
          />
        </Form.Item>

        <Form.Item>
          <div className={styles.formOptions}>
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox>记住我</Checkbox>
            </Form.Item>
            <Link to="/forgot-password" className={styles.forgotLink}>
              忘记密码？
            </Link>
          </div>
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            block
            loading={loading}
          >
            登录
          </Button>
        </Form.Item>
      </Form>

      <Divider plain>或</Divider>

      <div className={styles.footer}>
        <p>
          还没有账户？{' '}
          <Link to="/register" className={styles.link}>
            立即注册
          </Link>
        </p>
      </div>
    </div>
  )
}

export default Login
