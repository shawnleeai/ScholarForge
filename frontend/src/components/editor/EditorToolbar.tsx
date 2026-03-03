/**
 * 编辑器工具栏组件
 * 支持学术写作所需的所有格式化功能
 */

import React, { useState } from 'react'
import { Editor } from '@tiptap/react'
import { Button, Tooltip, Dropdown, Modal, Input } from 'antd'
import {
  BoldOutlined,
  ItalicOutlined,
  StrikethroughOutlined,
  OrderedListOutlined,
  UnorderedListOutlined,
  AlignLeftOutlined,
  AlignCenterOutlined,
  AlignRightOutlined,
  LinkOutlined,
  PictureOutlined,
  CodeOutlined,
  UndoOutlined,
  RedoOutlined,
  FontSizeOutlined,
  UnderlineOutlined,
  HighlightOutlined,
  TableOutlined,
  DeleteOutlined,
  PlusOutlined,
  MinusOutlined,
  BarChartOutlined,
  FontColorsOutlined,
} from '@ant-design/icons'

interface EditorToolbarProps {
  editor: Editor
  onInsertImage: (url: string) => void
  onInsertChart?: (config: unknown) => void
}

const EditorToolbar: React.FC<EditorToolbarProps> = ({
  editor,
  onInsertImage,
  onInsertChart,
}) => {
  const [linkModalVisible, setLinkModalVisible] = useState(false)
  const [imageModalVisible, setImageModalVisible] = useState(false)
  const [chartModalVisible, setChartModalVisible] = useState(false)
  const [linkUrl, setLinkUrl] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [highlightColor, setHighlightColor] = useState<string>('#fef3cd')

  const setLink = () => {
    if (linkUrl) {
      editor.chain().focus().setLink({ href: linkUrl }).run()
    }
    setLinkModalVisible(false)
    setLinkUrl('')
  }

  const handleInsertImage = () => {
    if (imageUrl) {
      onInsertImage(imageUrl)
      setImageModalVisible(false)
      setImageUrl('')
    }
  }

  const headingItems = [
    { key: '1', label: '标题 1', onClick: () => editor.chain().focus().toggleHeading({ level: 1 }).run() },
    { key: '2', label: '标题 2', onClick: () => editor.chain().focus().toggleHeading({ level: 2 }).run() },
    { key: '3', label: '标题 3', onClick: () => editor.chain().focus().toggleHeading({ level: 3 }).run() },
    { key: 'p', label: '正文', onClick: () => editor.chain().focus().setParagraph().run() },
  ]

  const tableItems = [
    { key: 'insert', label: '插入表格', icon: <PlusOutlined />, onClick: () => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run() },
    { key: 'addRow', label: '添加行', icon: <PlusOutlined />, onClick: () => editor.chain().focus().addRowAfter().run() },
    { key: 'addCol', label: '添加列', icon: <PlusOutlined />, onClick: () => editor.chain().focus().addColumnAfter().run() },
    { key: 'deleteRow', label: '删除行', icon: <MinusOutlined />, onClick: () => editor.chain().focus().deleteRow().run() },
    { key: 'deleteCol', label: '删除列', icon: <MinusOutlined />, onClick: () => editor.chain().focus().deleteColumn().run() },
    { key: 'deleteTable', label: '删除表格', icon: <DeleteOutlined />, onClick: () => editor.chain().focus().deleteTable().run() },
  ]

  const highlightColors = [
    { label: '黄色', color: '#fef3cd' },
    { label: '绿色', color: '#d4edda' },
    { label: '蓝色', color: '#cce5ff' },
    { label: '红色', color: '#f8d7da' },
    { label: '紫色', color: '#e2d9f3' },
    { label: '清除', color: 'transparent' },
  ]

  const handleHighlightChange = (color: string) => {
    setHighlightColor(color)
    if (color === 'transparent') {
      editor.chain().focus().unsetHighlight().run()
    } else {
      editor.chain().focus().toggleHighlight({ color }).run()
    }
  }

  const ToolbarButton = ({ icon, title, onClick, active }: {
    icon: React.ReactNode
    title: string
    onClick: () => void
    active?: boolean
  }) => (
    <Tooltip title={title}>
      <Button
        type={active ? 'primary' : 'text'}
        icon={icon}
        onClick={onClick}
        size="small"
      />
    </Tooltip>
  )

  return (
    <div className="editor-toolbar">
      <div className="toolbar-group">
        <ToolbarButton
          icon={<UndoOutlined />}
          title="撤销 (Ctrl+Z)"
          onClick={() => editor.chain().focus().undo().run()}
        />
        <ToolbarButton
          icon={<RedoOutlined />}
          title="重做 (Ctrl+Y)"
          onClick={() => editor.chain().focus().redo().run()}
        />
      </div>

      <div className="toolbar-divider" />

      <div className="toolbar-group">
        <Dropdown menu={{ items: headingItems }} trigger={['click']}>
          <Button size="small" icon={<FontSizeOutlined />}>标题</Button>
        </Dropdown>
      </div>

      <div className="toolbar-divider" />

      <div className="toolbar-group">
        <ToolbarButton
          icon={<BoldOutlined />}
          title="加粗 (Ctrl+B)"
          onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive('bold')}
        />
        <ToolbarButton
          icon={<ItalicOutlined />}
          title="斜体 (Ctrl+I)"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive('italic')}
        />
        <ToolbarButton
          icon={<UnderlineOutlined />}
          title="下划线 (Ctrl+U)"
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          active={editor.isActive('underline')}
        />
        <ToolbarButton
          icon={<StrikethroughOutlined />}
          title="删除线"
          onClick={() => editor.chain().focus().toggleStrike().run()}
          active={editor.isActive('strike')}
        />
      </div>

      <div className="toolbar-divider" />

      <div className="toolbar-group">
        <Dropdown menu={{ items: highlightColors.map(c => ({
          key: c.color,
          label: c.label,
          onClick: () => handleHighlightChange(c.color),
        })) }} trigger={['click']}>
          <ToolbarButton
            icon={<HighlightOutlined style={{ color: highlightColor !== 'transparent' ? highlightColor : undefined }} />}
            title="高亮"
            onClick={() => {}}
            active={editor.isActive('highlight')}
          />
        </Dropdown>
        <ToolbarButton
          icon={<FontColorsOutlined style={{ fontSize: 12, fontWeight: 'bold' }}>x₂</FontColorsOutlined>}
          title="下标"
          onClick={() => editor.chain().focus().toggleSubscript().run()}
          active={editor.isActive('subscript')}
        />
        <ToolbarButton
          icon={<FontColorsOutlined style={{ fontSize: 12, fontWeight: 'bold' }}>x²</FontColorsOutlined>}
          title="上标"
          onClick={() => editor.chain().focus().toggleSuperscript().run()}
          active={editor.isActive('superscript')}
        />
      </div>

      <div className="toolbar-divider" />

      <div className="toolbar-group">
        <ToolbarButton
          icon={<OrderedListOutlined />}
          title="有序列表"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          active={editor.isActive('orderedList')}
        />
        <ToolbarButton
          icon={<UnorderedListOutlined />}
          title="无序列表"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive('bulletList')}
        />
      </div>

      <div className="toolbar-divider" />

      <div className="toolbar-group">
        <ToolbarButton
          icon={<AlignLeftOutlined />}
          title="左对齐"
          onClick={() => editor.chain().focus().setTextAlign('left').run()}
          active={editor.isActive({ textAlign: 'left' })}
        />
        <ToolbarButton
          icon={<AlignCenterOutlined />}
          title="居中"
          onClick={() => editor.chain().focus().setTextAlign('center').run()}
          active={editor.isActive({ textAlign: 'center' })}
        />
        <ToolbarButton
          icon={<AlignRightOutlined />}
          title="右对齐"
          onClick={() => editor.chain().focus().setTextAlign('right').run()}
          active={editor.isActive({ textAlign: 'right' })}
        />
      </div>

      <div className="toolbar-divider" />

      <div className="toolbar-group">
        <Dropdown menu={{ items: tableItems }} trigger={['click']}>
          <ToolbarButton
            icon={<TableOutlined />}
            title="表格"
            onClick={() => {}}
            active={editor.isActive('table')}
          />
        </Dropdown>
        <ToolbarButton
          icon={<LinkOutlined />}
          title="链接"
          onClick={() => setLinkModalVisible(true)}
          active={editor.isActive('link')}
        />
        <ToolbarButton
          icon={<PictureOutlined />}
          title="图片"
          onClick={() => setImageModalVisible(true)}
        />
        {onInsertChart && (
          <ToolbarButton
            icon={<BarChartOutlined />}
            title="图表"
            onClick={() => setChartModalVisible(true)}
          />
        )}
        <ToolbarButton
          icon={<CodeOutlined />}
          title="代码块"
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          active={editor.isActive('codeBlock')}
        />
      </div>

      <Modal title="插入链接" open={linkModalVisible} onOk={setLink} onCancel={() => setLinkModalVisible(false)}>
        <Input placeholder="链接地址" value={linkUrl} onChange={(e) => setLinkUrl(e.target.value)} prefix={<LinkOutlined />} />
      </Modal>

      <Modal title="插入图片" open={imageModalVisible} onOk={handleInsertImage} onCancel={() => setImageModalVisible(false)}>
        <Input placeholder="图片地址" value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} prefix={<PictureOutlined />} />
      </Modal>

      <Modal
        title="插入图表"
        open={chartModalVisible}
        onOk={() => {
          if (onInsertChart) {
            onInsertChart({ type: 'bar', title: '新图表' })
          }
          setChartModalVisible(false)
        }}
        onCancel={() => setChartModalVisible(false)}
      >
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <BarChartOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <p>点击确定将打开图表编辑器</p>
        </div>
      </Modal>
    </div>
  )
}

export default EditorToolbar
