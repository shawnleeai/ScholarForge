/**
 * 论文列表页面
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Card,
  List,
  Button,
  Tag,
  Space,
  Input,
  Select,
  Modal,
  Form,
  message,
  Empty,
  Dropdown,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  ExportOutlined,
} from '@ant-design/icons'

import { paperService } from '@/services'
import type { Paper, PaginatedResponse } from '@/types'
import styles from './Paper.module.css'

const { Search } = Input

const PaperList: React.FC = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>()
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [form] = Form.useForm()

  const { data } = useQuery({
    queryKey: ['papers', statusFilter],
    queryFn: () => paperService.getPapers({ page: 1, pageSize: 20, status: statusFilter }),
  })

  const createMutation = useMutation({
    mutationFn: (values: Partial<Paper>) => paperService.createPaper(values),
    onSuccess: (response) => {
      message.success('论文创建成功')
      setCreateModalVisible(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['papers'] })
      const paperData = response.data as Paper
      navigate(`/papers/${paperData.id}`)
    },
    onError: () => {
      message.error('创建失败')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (paperId: string) => paperService.deletePaper(paperId),
    onSuccess: () => {
      message.success('论文已删除')
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })

  const papers = (data?.data as PaginatedResponse<Paper>)?.items || []
  const filteredPapers = papers.filter(
    (paper: Paper) => paper.title.toLowerCase().includes(searchText.toLowerCase())
  )

  const statusConfig: Record<string, { color: string; label: string }> = {
    draft: { color: 'default', label: '草稿' },
    in_progress: { color: 'processing', label: '写作中' },
    review: { color: 'warning', label: '审核中' },
    submitted: { color: 'blue', label: '已提交' },
    published: { color: 'green', label: '已发表' },
  }

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      createMutation.mutate(values)
    } catch {
      // 验证错误
    }
  }

  const handleDelete = (paper: Paper) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除论文《${paper.title}》吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(paper.id),
    })
  }

  const getDropdownItems = (paper: Paper) => [
    { key: 'edit', icon: <EditOutlined />, label: '编辑', onClick: () => navigate(`/papers/${paper.id}`) },
    { key: 'export', icon: <ExportOutlined />, label: '导出' },
    { type: 'divider' as const },
    { key: 'delete', icon: <DeleteOutlined />, label: '删除', danger: true, onClick: () => handleDelete(paper) },
  ]

  return (
    <div className={styles.paperList}>
      <div className={styles.header}>
        <div className={styles.titleSection}>
          <h2>我的论文</h2>
          <span className={styles.count}>{filteredPapers.length} 篇</span>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
          新建论文
        </Button>
      </div>

      <Card className={styles.filterCard}>
        <Space>
          <Search
            placeholder="搜索论文..."
            allowClear
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 150 }}
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { value: 'draft', label: '草稿' },
              { value: 'in_progress', label: '写作中' },
              { value: 'submitted', label: '已提交' },
              { value: 'published', label: '已发表' },
            ]}
          />
        </Space>
      </Card>

      <Card className={styles.listCard}>
        {filteredPapers.length === 0 ? (
          <Empty description="暂无论文">
            <Button type="primary" onClick={() => setCreateModalVisible(true)}>
              创建第一篇论文
            </Button>
          </Empty>
        ) : (
          <List
            itemLayout="horizontal"
            dataSource={filteredPapers}
            renderItem={(paper: Paper) => (
              <List.Item
                key={paper.id}
                className={styles.listItem}
                onClick={() => navigate(`/papers/${paper.id}`)}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <span className={styles.paperTitle}>{paper.title}</span>
                      <Tag color={statusConfig[paper.status]?.color}>
                        {statusConfig[paper.status]?.label}
                      </Tag>
                    </Space>
                  }
                  description={
                    <span>{paper.wordCount?.toLocaleString()} 字 · 更新于 {new Date(paper.updatedAt).toLocaleDateString()}</span>
                  }
                />
                <Dropdown menu={{ items: getDropdownItems(paper) }} trigger={['click']}>
                  <Button type="text" icon={<MoreOutlined />} />
                </Dropdown>
              </List.Item>
            )}
          />
        )}
      </Card>

      <Modal
        title="新建论文"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => setCreateModalVisible(false)}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="论文标题" rules={[{ required: true, message: '请输入论文标题' }]}>
            <Input placeholder="例如：AI协同项目管理研究" />
          </Form.Item>
          <Form.Item name="abstract" label="摘要">
            <Input.TextArea rows={3} placeholder="简要描述..." />
          </Form.Item>
          <Form.Item name="paperType" label="论文类型" initialValue="thesis">
            <Select options={[
              { value: 'thesis', label: '学位论文' },
              { value: 'journal', label: '期刊论文' },
              { value: 'conference', label: '会议论文' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default PaperList
