/**
 * 文献综述大纲编辑器
 * 支持拖拽排序、添加/删除/编辑章节
 */

import React, { useState, useCallback } from 'react'
import {
  Card,
  List,
  Input,
  Button,
  Space,
  Typography,
  Tooltip,
  Popconfirm,
  Badge,
  Progress,
  Divider,
  Modal,
  Form,
} from 'antd'
import {
  DragOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  FileTextOutlined,
  SubnodeOutlined,
  MenuOutlined,
} from '@ant-design/icons'
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

const { Text, Title } = Typography

interface OutlineSection {
  id: string
  title: string
  description?: string
  wordCount?: number
  targetWordCount?: number
  subsections?: OutlineSection[]
  level: number
}

interface ReviewOutlineEditorProps {
  outline: OutlineSection[]
  onChange: (outline: OutlineSection[]) => void
  totalWordCount?: number
  targetWordCount?: number
}

// 可排序的章节项
const SortableSection: React.FC<{
  section: OutlineSection
  index: number
  onEdit: (section: OutlineSection) => void
  onDelete: (id: string) => void
  onAddSubsection: (parentId: string) => void
}> = ({ section, index, onEdit, onDelete, onAddSubsection }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id: section.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="outline-section-item"
    >
      <div
        className={`section-content level-${section.level}`}
        style={{
          padding: '12px 16px',
          background: '#f6ffed',
          borderRadius: 8,
          marginBottom: 8,
          borderLeft: `4px solid ${section.level === 1 ? '#52c41a' : '#95de64'}`,
          marginLeft: section.level * 24,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div {...attributes} {...listeners} style={{ cursor: 'grab' }}>
            <DragOutlined style={{ color: '#999' }} />
          </div>

          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Text strong style={{ fontSize: section.level === 1 ? 16 : 14 }}>
                {section.title}
              </Text>
              {section.wordCount !== undefined && (
                <Badge
                  count={`${section.wordCount}字`}
                  style={{ backgroundColor: section.wordCount > (section.targetWordCount || 0) ? '#ff4d4f' : '#52c41a' }}
                />
              )}
            </div>
            {section.description && (
              <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
                {section.description}
              </Text>
            )}
          </div>

          <Space>
            <Tooltip title="编辑">
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={() => onEdit(section)}
              />
            </Tooltip>
            <Tooltip title="添加子章节">
              <Button
                type="text"
                size="small"
                icon={<SubnodeOutlined />}
                onClick={() => onAddSubsection(section.id)}
              />
            </Tooltip>
            <Popconfirm
              title="确定删除此章节？"
              onConfirm={() => onDelete(section.id)}
            >
              <Button
                type="text"
                danger
                size="small"
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Space>
        </div>

        {section.targetWordCount && (
          <div style={{ marginTop: 8 }}>
            <Progress
              percent={Math.round(((section.wordCount || 0) / section.targetWordCount) * 100)}
              size="small"
              status={section.wordCount && section.wordCount > section.targetWordCount ? 'exception' : 'success'}
            />
          </div>
        )}
      </div>

      {/* 子章节 */}
      {section.subsections && section.subsections.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {section.subsections.map((sub, subIndex) => (
            <SortableSection
              key={sub.id}
              section={sub}
              index={subIndex}
              onEdit={onEdit}
              onDelete={onDelete}
              onAddSubsection={onAddSubsection}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export const ReviewOutlineEditor: React.FC<ReviewOutlineEditorProps> = ({
  outline,
  onChange,
  totalWordCount = 0,
  targetWordCount = 3000,
}) => {
  const [editingSection, setEditingSection] = useState<OutlineSection | null>(null)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [form] = Form.useForm()

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // 拖拽结束处理
  const handleDragEnd = useCallback((event: any) => {
    const { active, over } = event

    if (active.id !== over?.id) {
      const oldIndex = outline.findIndex((item) => item.id === active.id)
      const newIndex = outline.findIndex((item) => item.id === over.id)
      onChange(arrayMove(outline, oldIndex, newIndex))
    }
  }, [outline, onChange])

  // 编辑章节
  const handleEdit = (section: OutlineSection) => {
    setEditingSection(section)
    form.setFieldsValue({
      title: section.title,
      description: section.description,
      targetWordCount: section.targetWordCount,
    })
    setEditModalVisible(true)
  }

  // 保存编辑
  const handleSaveEdit = (values: any) => {
    if (!editingSection) return

    const updateSection = (sections: OutlineSection[]): OutlineSection[] => {
      return sections.map((section) => {
        if (section.id === editingSection.id) {
          return { ...section, ...values }
        }
        if (section.subsections) {
          return { ...section, subsections: updateSection(section.subsections) }
        }
        return section
      })
    }

    onChange(updateSection(outline))
    setEditModalVisible(false)
    setEditingSection(null)
  }

  // 删除章节
  const handleDelete = (id: string) => {
    const deleteSection = (sections: OutlineSection[]): OutlineSection[] => {
      return sections
        .filter((section) => section.id !== id)
        .map((section) => ({
          ...section,
          subsections: section.subsections ? deleteSection(section.subsections) : undefined,
        }))
    }

    onChange(deleteSection(outline))
  }

  // 添加章节
  const handleAddSection = () => {
    const newSection: OutlineSection = {
      id: `section_${Date.now()}`,
      title: '新章节',
      level: 1,
      targetWordCount: 500,
    }
    onChange([...outline, newSection])
  }

  // 添加子章节
  const handleAddSubsection = (parentId: string) => {
    const addSub = (sections: OutlineSection[]): OutlineSection[] => {
      return sections.map((section) => {
        if (section.id === parentId) {
          const newSub: OutlineSection = {
            id: `subsection_${Date.now()}`,
            title: '新子章节',
            level: section.level + 1,
            targetWordCount: 200,
          }
          return {
            ...section,
            subsections: [...(section.subsections || []), newSub],
          }
        }
        if (section.subsections) {
          return { ...section, subsections: addSub(section.subsections) }
        }
        return section
      })
    }

    onChange(addSub(outline))
  }

  // 扁平化章节列表（用于拖拽排序）
  const flattenSections = (sections: OutlineSection[]): OutlineSection[] => {
    const result: OutlineSection[] = []
    sections.forEach((section) => {
      result.push(section)
      if (section.subsections) {
        result.push(...flattenSections(section.subsections))
      }
    })
    return result
  }

  const flatSections = flattenSections(outline)

  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <MenuOutlined />
            <span>综述大纲</span>
          </Space>
          <Space>
            <Badge
              count={`${totalWordCount} / ${targetWordCount} 字`}
              style={{ backgroundColor: totalWordCount > targetWordCount ? '#ff4d4f' : '#52c41a' }}
            />
            <Button
              type="primary"
              size="small"
              icon={<PlusOutlined />}
              onClick={handleAddSection}
            >
              添加章节
            </Button>
          </Space>
        </div>
      }
    >
      <Progress
        percent={Math.round((totalWordCount / targetWordCount) * 100)}
        status={totalWordCount > targetWordCount ? 'exception' : 'success'}
        strokeWidth={8}
        style={{ marginBottom: 16 }}
      />

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={flatSections.map((s) => s.id)}
          strategy={verticalListSortingStrategy}
        >
          {outline.map((section, index) => (
            <SortableSection
              key={section.id}
              section={section}
              index={index}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onAddSubsection={handleAddSubsection}
            />
          ))}
        </SortableContext>
      </DndContext>

      {outline.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
          <FileTextOutlined style={{ fontSize: 48, marginBottom: 16 }} />
          <p>暂无章节，点击"添加章节"开始编辑</p>
        </div>
      )}

      {/* 编辑模态框 */}
      <Modal
        title="编辑章节"
        open={editModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setEditModalVisible(false)}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveEdit}
        >
          <Form.Item
            name="title"
            label="章节标题"
            rules={[{ required: true, message: '请输入章节标题' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="description"
            label="章节描述"
          >
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item
            name="targetWordCount"
            label="目标字数"
          >
            <Input type="number" />
          </Form.Item>
        </Form>
      </Modal>

      <style>{`
        .outline-section-item {
          position: relative;
        }
        .outline-section-item:hover .section-content {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
      `}</style>
    </Card>
  )
}

export default ReviewOutlineEditor
