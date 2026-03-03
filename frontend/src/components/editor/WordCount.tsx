/**
 * 字数统计组件
 */

import React from 'react'
import { Typography, Space, Tooltip } from 'antd'
import { Editor } from '@tiptap/react'

const { Text } = Typography

interface WordCountProps {
  editor: Editor
}

const WordCount: React.FC<WordCountProps> = ({ editor }) => {
  const characterCount = editor.storage.characterCount?.characters?.() ?? editor.getText().length
  const wordCount = editor.getText().trim().split(/\s+/).filter(word => word.length > 0).length

  // 中文字符统计（不含空格和标点）
  const chineseChars = editor.getText().match(/[\u4e00-\u9fa5]/g)?.length ?? 0

  // 总字数（中文按字符计，英文按单词计）
  const totalCount = chineseChars + wordCount

  return (
    <div className="word-count-bar">
      <Space split={<Text type="secondary">|</Text>} size="small">
        <Tooltip title="总字数（中文字符 + 英文单词）">
          <Text type="secondary">
            字数：{totalCount}
          </Text>
        </Tooltip>
        <Tooltip title="包含所有字符">
          <Text type="secondary">
            字符：{characterCount}
          </Text>
        </Tooltip>
        <Tooltip title="中文字符数">
          <Text type="secondary">
            中文：{chineseChars}
          </Text>
        </Tooltip>
      </Space>
    </div>
  )
}

export default WordCount
