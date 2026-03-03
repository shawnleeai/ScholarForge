/**
 * 富文本编辑器组件
 * 基于 TipTap 实现，支持学术写作功能和实时协作
 */

import React, { useCallback, useEffect, useMemo } from 'react'
import { useEditor, EditorContent, type AnyExtension } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import TextAlign from '@tiptap/extension-text-align'
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import { Table, TableRow, TableCell, TableHeader } from '@tiptap/extension-table'
import Underline from '@tiptap/extension-underline'
import Highlight from '@tiptap/extension-highlight'
import Subscript from '@tiptap/extension-subscript'
import Superscript from '@tiptap/extension-superscript'
import Typography from '@tiptap/extension-typography'
import Collaboration from '@tiptap/extension-collaboration'
import CollaborationCursor from '@tiptap/extension-collaboration-cursor'
import * as Y from 'yjs'

import { common, createLowlight } from 'lowlight'
const lowlight = createLowlight(common)

import EditorToolbar from './EditorToolbar'
import WordCount from './WordCount'
import './Editor.css'

interface CollaborationConfig {
  doc: Y.Doc
  user: { name: string; color: string }
}

interface RichTextEditorProps {
  content: string
  onChange: (content: string) => void
  placeholder?: string
  editable?: boolean
  onSave?: () => void
  showWordCount?: boolean
  /** 协作配置，提供后启用协作模式 */
  collaboration?: CollaborationConfig
  /** 图表插入回调 */
  onInsertChart?: (config: unknown) => void
}

const RichTextEditor: React.FC<RichTextEditorProps> = ({
  content,
  onChange,
  placeholder = '开始写作...',
  editable = true,
  onSave,
  showWordCount = true,
  collaboration,
  onInsertChart,
}) => {
  // 构建扩展列表
  const extensions = useMemo(() => {
    const baseExtensions: AnyExtension[] = [
      StarterKit.configure({
        codeBlock: false,
      }),
      Placeholder.configure({
        placeholder,
      }),
      Image.configure({
        inline: true,
        allowBase64: true,
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'reference-link',
        },
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      CodeBlockLowlight.configure({
        lowlight,
      }),
      Table.configure({
        resizable: true,
        HTMLAttributes: {
          class: 'editor-table',
        },
      }),
      TableRow,
      TableCell,
      TableHeader,
      Underline,
      Highlight.configure({
        multicolor: true,
      }),
      Subscript,
      Superscript,
      Typography,
    ]

    // 添加协作扩展
    if (collaboration) {
      baseExtensions.push(
        Collaboration.configure({
          document: collaboration.doc,
        }),
        CollaborationCursor.configure({
          provider: collaboration.doc,
          user: collaboration.user,
          render: (user: { name: string; color: string }) => {
            const cursor = document.createElement('span')
            cursor.classList.add('collaboration-cursor__caret')
            cursor.setAttribute('style', `border-color: ${user.color}`)
            cursor.insertBefore(document.createTextNode('\u200B'), null)

            const label = document.createElement('span')
            label.classList.add('collaboration-cursor__label')
            label.setAttribute('style', `background-color: ${user.color}`)
            label.insertBefore(document.createTextNode(user.name), null)
            cursor.insertBefore(label, null)

            return cursor
          },
        })
      )
    }

    return baseExtensions
  }, [placeholder, collaboration])

  const editor = useEditor({
    extensions,
    content: collaboration ? undefined : content, // 协作模式下内容由 Yjs 管理
    editable,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
    editorProps: {
      attributes: {
        class: 'prose prose-lg max-w-none focus:outline-none min-h-[500px] p-4',
      },
      handleKeyDown: (_view, event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
          event.preventDefault()
          onSave?.()
          return true
        }
        return false
      },
    },
  })

  // 非协作模式下同步内容
  useEffect(() => {
    if (editor && !collaboration && content !== editor.getHTML()) {
      editor.commands.setContent(content)
    }
  }, [content, editor, collaboration])

  const insertImage = useCallback((url: string) => {
    editor?.chain().focus().setImage({ src: url }).run()
  }, [editor])

  const insertChart = useCallback((config: unknown) => {
    if (onInsertChart) {
      onInsertChart(config)
    }
    // 将图表配置作为 HTML 插入
    const chartHtml = `<div class="chart-placeholder" data-chart="${encodeURIComponent(JSON.stringify(config))}">
      <p>[图表: ${(config as { title?: string })?.title || '未命名图表'}]</p>
    </div>`
    editor?.chain().focus().insertContent(chartHtml).run()
  }, [editor, onInsertChart])

  if (!editor) {
    return <div className="editor-loading">加载编辑器...</div>
  }

  return (
    <div className="rich-text-editor">
      <EditorToolbar
        editor={editor}
        onInsertImage={insertImage}
        onInsertChart={onInsertChart ? insertChart : undefined}
      />
      <EditorContent editor={editor} className="editor-content" />
      {showWordCount && <WordCount editor={editor} />}
    </div>
  )
}

export default RichTextEditor
