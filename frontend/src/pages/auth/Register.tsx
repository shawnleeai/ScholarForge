/**
 * 注册页面
 */

import React, { useState } from 'react'
import { Form, Input, Button, message, Divider } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'

import { authService } from '@/services'
import { useAuthStore } from '@/stores'
import styles from './Auth.module.css'

const Register: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      const response = await authService.register(values)
      const { user, token } = response.data!

      login(user, token.accessToken, token.refreshToken)
      message.success('注册成功')
      navigate('/dashboard')
    } catch (error: any) {
      message.error(error.message || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.authForm}>
      <div className={styles.header}>
        <h2>创建账户</h2>
        <p>开始您的学术研究之旅</p>
      </div>

      <Form
        form={form}
        name="register"
        onFinish={handleSubmit}
        layout="vertical"
        requiredMark={false}
      >
        <Form.Item
          name="email"
          rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' },
          ]}
        >
          <Input
            prefix={<MailOutlined />}
            placeholder="邮箱地址"
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="username"
          rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, message: '用户名至少3个字符' },
          ]}
        >
          <Input
            prefix={<UserOutlined />}
            placeholder="用户名"
            size="large"
          />
        </Form.Item>

        <Form.Item name="fullName">
          <Input placeholder="真实姓名（选填）" size="large" />
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

        <Form.Item
          name="confirmPassword"
          dependencies={['password']}
          rules={[
            { required: true, message: '请确认密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve()
                }
                return Promise.reject(new Error('两次输入的密码不一致'))
              },
            }),
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="确认密码"
            size="large"
          />
        </Form.Item>

        <Form.Item name="university">
          <Input placeholder="学校（选填）" size="large" />
        </Form.Item>

        <Form.Item name="major">
          <Input placeholder="专业（选填）" size="large" />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            size="large"
            block
            loading={loading}
          >
            注册
          </Button>
        </Form.Item>
      </Form>

      <Divider plain>或</Divider>

      <div className={styles.footer}>
        <p>
          已有账户？{' '}
          <Link to="/login" className={styles.link}>
            立即登录
          </Link>
        </p>
      </div>
    </div>
  )
}

export default Register
