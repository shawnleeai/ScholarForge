/**
 * TipTap 评论扩展
 * 支持高亮选中文本并添加评论
 */

import { Mark, mergeAttributes } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

export interface CommentOptions {
  HTMLAttributes: Record<string, string>
  onCommentAdd?: (data: { from: number; to: number; text: string }) => void
  onCommentClick?: (commentId: string) => void
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    comment: {
      /**
       * 添加评论标记
       */
      setComment: (commentId: string) => ReturnType
      /**
       * 移除评论标记
       */
      unsetComment: (commentId: string) => ReturnType
      /**
       * 切换评论标记
       */
      toggleComment: (commentId: string) => ReturnType
    }
  }
}

// 评论标记扩展
export const CommentMark = Mark.create<CommentOptions>({
  name: 'comment',

  addOptions() {
    return {
      HTMLAttributes: {},
      onCommentAdd: undefined,
      onCommentClick: undefined,
    }
  },

  addAttributes() {
    return {
      commentId: {
        default: null,
        parseHTML: (element: HTMLElement) => element.getAttribute('data-comment-id'),
        renderHTML: (attributes: Record<string, unknown>) => {
          if (!attributes.commentId) {
            return {}
          }
          return {
            'data-comment-id': attributes.commentId,
          }
        },
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-comment-id]',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: 'comment-highlight',
      }),
      0,
    ]
  },

  addCommands() {
    return {
      setComment:
        (commentId: string) =>
        ({ commands }) => {
          return commands.setMark(this.name, { commentId })
        },
      unsetComment:
        (_commentId: string) =>
        ({ commands }) => {
          return commands.unsetMark(this.name)
        },
      toggleComment:
        (commentId: string) =>
        ({ commands }) => {
          return commands.toggleMark(this.name, { commentId })
        },
    }
  },

  addProseMirrorPlugins() {
    const extensionThis = this

    return [
      // 装饰器插件，用于高亮评论区域
      new Plugin({
        key: new PluginKey('commentDecoration'),
        props: {
          decorations(state) {
            const decorations: Decoration[] = []
            const { doc } = state

            doc.descendants((node, pos) => {
              if (node.marks) {
                node.marks.forEach((mark) => {
                  if (mark.type.name === 'comment') {
                    const commentId = mark.attrs.commentId as string
                    decorations.push(
                      Decoration.inline(pos, pos + node.nodeSize, {
                        class: 'comment-highlight',
                        'data-comment-id': commentId,
                      })
                    )
                  }
                })
              }
            })

            return DecorationSet.create(doc, decorations)
          },
          // 点击评论时的处理
          handleClick(_view, _pos, event) {
            const target = event.target as HTMLElement
            const commentElement = target.closest('.comment-highlight')

            if (commentElement) {
              const commentId = commentElement.getAttribute('data-comment-id')
              if (commentId && extensionThis.options.onCommentClick) {
                extensionThis.options.onCommentClick(commentId)
                return true
              }
            }
            return false
          },
        },
      }),
    ]
  },
})

// CSS 样式（需要在编辑器 CSS 中添加）
export const commentStyles = `
.comment-highlight {
  background-color: #fff3cd;
  border-bottom: 2px solid #ffc107;
  cursor: pointer;
  transition: background-color 0.2s;
}

.comment-highlight:hover {
  background-color: #ffe69c;
}

.comment-highlight.resolved {
  background-color: #d4edda;
  border-bottom-color: #28a745;
}
`

export default CommentMark
