/**
 * 数据输入组件
 */

import React, { useState } from 'react'
import { Tabs, Input, Button, message, Table } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'

const { TextArea } = Input

interface DataInputProps {
  onChange: (data: unknown[]) => void
}

const DataInput: React.FC<DataInputProps> = ({ onChange }) => {
  const [textInput, setTextInput] = useState('')
  const [tableData, setTableData] = useState<{ x: string; y: number; name?: string }[]>([
    { x: 'A', y: 10 },
    { x: 'B', y: 25 },
    { x: 'C', y: 18 },
    { x: 'D', y: 32 },
  ])

  const parseTextData = () => {
    try {
      const lines = textInput.trim().split('\n')
      const data = lines.map((line) => {
        const parts = line.split(/[,\t]/)
        return {
          x: parts[0]?.trim() || '',
          y: parseFloat(parts[1]) || 0,
          name: parts[2]?.trim(),
        }
      }).filter((d) => d.x)

      setTableData(data)
      onChange(data)
      message.success(`已解析 ${data.length} 条数据`)
    } catch {
      message.error('数据格式错误')
    }
  }

  const handleTableChange = (index: number, field: string, value: string | number) => {
    const newData = [...tableData]
    newData[index] = { ...newData[index], [field]: value }
    setTableData(newData)
    onChange(newData)
  }

  const addRow = () => {
    const newData = [...tableData, { x: '', y: 0 }]
    setTableData(newData)
    onChange(newData)
  }

  const deleteRow = (index: number) => {
    const newData = tableData.filter((_, i) => i !== index)
    setTableData(newData)
    onChange(newData)
  }

  const columns = [
    {
      title: 'X 值',
      dataIndex: 'x',
      render: (value: string, _record: unknown, index: number) => (
        <Input
          value={value}
          onChange={(e) => handleTableChange(index, 'x', e.target.value)}
          size="small"
        />
      ),
    },
    {
      title: 'Y 值',
      dataIndex: 'y',
      render: (value: number, _record: unknown, index: number) => (
        <Input
          type="number"
          value={value}
          onChange={(e) => handleTableChange(index, 'y', parseFloat(e.target.value) || 0)}
          size="small"
        />
      ),
    },
    {
      title: '名称',
      dataIndex: 'name',
      render: (value: string, _record: unknown, index: number) => (
        <Input
          value={value}
          onChange={(e) => handleTableChange(index, 'name', e.target.value)}
          size="small"
          placeholder="可选"
        />
      ),
    },
    {
      title: '',
      render: (_value: unknown, _record: unknown, index: number) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => deleteRow(index)}
          size="small"
        />
      ),
    },
  ]

  const tabItems = [
    {
      key: 'table',
      label: '表格输入',
      children: (
        <div>
          <Table
            dataSource={tableData}
            columns={columns}
            pagination={false}
            size="small"
            rowKey={(_record, index) => index?.toString() || '0'}
          />
          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={addRow}
            block
            style={{ marginTop: 8 }}
          >
            添加行
          </Button>
        </div>
      ),
    },
    {
      key: 'text',
      label: '文本输入',
      children: (
        <div>
          <TextArea
            rows={6}
            placeholder="输入数据，每行一条，格式：X值,Y值,名称&#10;例如：&#10;2020,150,销售额&#10;2021,280,销售额&#10;2022,350,销售额"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
          />
          <Button type="primary" onClick={parseTextData} style={{ marginTop: 8 }}>
            解析数据
          </Button>
        </div>
      ),
    },
  ]

  return (
    <Tabs defaultActiveKey="table" items={tabItems} size="small" />
  )
}

export default DataInput
