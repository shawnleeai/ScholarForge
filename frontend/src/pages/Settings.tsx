/**
 * 设置页面
 */

import React from 'react'
import { Card, Form, Input, Button, Avatar, Upload, message, Divider, Switch, Select, Space } from 'antd'
import { UserOutlined } from '@ant-design/icons'

import { useAuthStore } from '@/stores'
import styles from './Settings.module.css'

const { Option } = Select

const Settings: React.FC = () => {
  const { user } = useAuthStore()
  const [form] = Form.useForm()

  const handleSave = async () => {
    message.success('设置已保存')
  }

  return (
    <div className={styles.settings}>
      <h2>设置</h2>

      <Card title="个人资料" className={styles.card}>
        <div className={styles.avatarSection}>
          <Avatar size={80} icon={<UserOutlined />} />
          <Upload showUploadList={false}>
            <Button type="link">更换头像</Button>
          </Upload>
        </div>

        <Form
          form={form}
          layout="vertical"
          initialValues={{
            fullName: user?.fullName,
            email: user?.email,
            university: user?.university,
            department: user?.department,
            major: user?.major,
          }}
        >
          <Form.Item name="fullName" label="姓名">
            <Input placeholder="请输入姓名" />
          </Form.Item>

          <Form.Item name="email" label="邮箱">
            <Input disabled />
          </Form.Item>

          <Form.Item name="university" label="学校">
            <Input placeholder="请输入学校" />
          </Form.Item>

          <Form.Item name="department" label="院系">
            <Input placeholder="请输入院系" />
          </Form.Item>

          <Form.Item name="major" label="专业">
            <Input placeholder="请输入专业" />
          </Form.Item>

          <Button type="primary" onClick={handleSave}>
            保存更改
          </Button>
        </Form>
      </Card>

      <Card title="偏好设置" className={styles.card}>
        <Form layout="vertical">
          <Form.Item label="默认引用格式">
            <Select defaultValue="gb-t-7714-2015" style={{ width: 200 }}>
              <Option value="gb-t-7714-2015">GB/T 7714-2015</Option>
              <Option value="apa-7">APA 第7版</Option>
              <Option value="ieee">IEEE</Option>
            </Select>
          </Form.Item>

          <Form.Item label="论文语言">
            <Select defaultValue="zh" style={{ width: 200 }}>
              <Option value="zh">中文</Option>
              <Option value="en">英文</Option>
            </Select>
          </Form.Item>

          <Divider />

          <Form.Item label="自动保存">
            <Space>
              <Switch defaultChecked />
              <span>每3秒自动保存</span>
            </Space>
          </Form.Item>

          <Form.Item label="AI 助手">
            <Space>
              <Switch defaultChecked />
              <span>启用 AI 写作建议</span>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card title="通知设置" className={styles.card}>
        <Form layout="vertical">
          <Form.Item label="邮件通知">
            <Space>
              <Switch defaultChecked />
              <span>接收重要更新邮件</span>
            </Space>
          </Form.Item>

          <Form.Item label="文献推荐">
            <Space>
              <Switch defaultChecked />
              <span>每日文献推荐</span>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Settings
