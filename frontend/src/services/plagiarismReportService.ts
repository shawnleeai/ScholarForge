/**
 * 查重报告服务
 * 生成和导出查重报告
 */

import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import { PlagiarismReportData } from '../components/plagiarism/PlagiarismReport'

export interface ReportExportOptions {
  format: 'pdf' | 'html' | 'json'
  includeHighlight: boolean
  includeSources: boolean
  includeDetails: boolean
}

/**
 * 生成报告HTML内容
 */
function generateReportHTML(
  data: PlagiarismReportData,
  originalText: string,
  options: ReportExportOptions
): string {
  const { format, includeHighlight, includeSources, includeDetails } = options

  const reportDate = new Date().toLocaleString('zh-CN')
  const similarityColor =
    data.overallSimilarity < 15
      ? '#52c41a'
      : data.overallSimilarity < 30
      ? '#faad14'
      : data.overallSimilarity < 50
      ? '#fa8c16'
      : '#f5222d'

  let html = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>查重报告 - ScholarForge</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 20px;
    }
    .header {
      text-align: center;
      border-bottom: 3px solid #1890ff;
      padding-bottom: 20px;
      margin-bottom: 30px;
    }
    .header h1 {
      color: #1890ff;
      margin: 0 0 10px 0;
    }
    .header .date {
      color: #999;
      font-size: 14px;
    }
    .score-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      border-radius: 12px;
      text-align: center;
      margin-bottom: 30px;
    }
    .score-card .score {
      font-size: 72px;
      font-weight: bold;
      margin: 0;
    }
    .score-card .label {
      font-size: 18px;
      opacity: 0.9;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin-bottom: 30px;
    }
    .stat-item {
      background: #f5f5f5;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-item .value {
      font-size: 32px;
      font-weight: bold;
      color: #1890ff;
    }
    .stat-item .label {
      color: #666;
      font-size: 14px;
    }
    .section {
      margin-bottom: 30px;
    }
    .section h2 {
      color: #1890ff;
      border-left: 4px solid #1890ff;
      padding-left: 12px;
      margin-bottom: 20px;
    }
    .source-item {
      background: #fafafa;
      border: 1px solid #e8e8e8;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
    }
    .source-item .title {
      font-weight: bold;
      margin-bottom: 8px;
    }
    .source-item .meta {
      color: #666;
      font-size: 14px;
    }
    .match-item {
      background: #fff2f0;
      border: 1px solid #ffccc7;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
    }
    .match-item .similarity {
      color: #f5222d;
      font-weight: bold;
    }
    .text-highlight {
      background: #f6ffed;
      padding: 20px;
      border-radius: 8px;
      line-height: 2;
    }
    .highlight {
      background: #ffccc7;
      padding: 2px 4px;
      border-radius: 4px;
    }
    .recommendation {
      background: ${similarityColor}15;
      border: 2px solid ${similarityColor};
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 30px;
    }
    .recommendation h3 {
      color: ${similarityColor};
      margin-top: 0;
    }
    .footer {
      text-align: center;
      color: #999;
      font-size: 12px;
      margin-top: 50px;
      padding-top: 20px;
      border-top: 1px solid #e8e8e8;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📄 ScholarForge 查重报告</h1>
    <div class="date">生成时间: ${reportDate}</div>
  </div>

  <div class="score-card">
    <div class="score">${data.overallSimilarity.toFixed(1)}%</div>
    <div class="label">总体相似度</div>
  </div>

  <div class="recommendation">
    <h3>💡 检测建议</h3>
    <p>${data.recommendation || '请根据相似度结果进行相应修改'}</p>
  </div>

  <div class="stats">
    <div class="stat-item">
      <div class="value">${data.internetSimilarity.toFixed(1)}%</div>
      <div class="label">网络资源</div>
    </div>
    <div class="stat-item">
      <div class="value">${data.publicationsSimilarity.toFixed(1)}%</div>
      <div class="label">出版物</div>
    </div>
    <div class="stat-item">
      <div class="value">${data.studentPapersSimilarity.toFixed(1)}%</div>
      <div class="label">学生论文</div>
    </div>
  </div>
`

  // 来源列表
  if (includeSources && data.sources.length > 0) {
    html += `
  <div class="section">
    <h2>📚 相似来源 (${data.sources.length})</h2>
    ${data.sources
      .map(
        (source) => `
    <div class="source-item">
      <div class="title">${source.title}</div>
      <div class="meta">
        类型: ${source.type === 'internet' ? '网络' : source.type === 'publication' ? '出版物' : '学生论文'} |
        相似度: ${(source.similarity * 100).toFixed(1)}% |
        匹配: ${source.matchCount} 处
        ${source.url ? `| <a href="${source.url}" target="_blank">查看原文</a>` : ''}
      </div>
    </div>
    `
      )
      .join('')}
  </div>
`
  }

  // 详细匹配
  if (includeDetails && data.matches.length > 0) {
    html += `
  <div class="section">
    <h2>🔍 重复片段详情 (${data.matches.length})</h2>
    ${data.matches
      .map(
        (match) => `
    <div class="match-item">
      <div class="similarity">相似度: ${(match.similarity * 100).toFixed(1)}%</div>
      <div>来源: ${match.sourceTitle}</div>
      <div style="margin-top: 8px; padding: 8px; background: white; border-radius: 4px;">
        ${match.text}
      </div>
    </div>
    `
      )
      .join('')}
  </div>
`
  }

  // 原文高亮
  if (includeHighlight) {
    // 简单的文本高亮处理
    let highlightedText = originalText
    const sortedMatches = [...data.matches].sort((a, b) => b.startIndex - a.startIndex)

    for (const match of sortedMatches) {
      const before = highlightedText.slice(0, match.startIndex)
      const matched = highlightedText.slice(match.startIndex, match.endIndex)
      const after = highlightedText.slice(match.endIndex)

      highlightedText = `${before}<span class="highlight" title="相似度: ${(match.similarity * 100).toFixed(1)}%">${matched}</span>${after}`
    }

    html += `
  <div class="section">
    <h2>📝 原文对照</h2>
    <div class="text-highlight">
      ${highlightedText.replace(/\n/g, '<br>')}
    </div>
  </div>
`
  }

  html += `
  <div class="footer">
    <p>本报告由 ScholarForge 学术锻造平台生成</p>
    <p>© 2026 ScholarForge. All rights reserved.</p>
  </div>
</body>
</html>
`

  return html
}

/**
 * 导出为PDF
 */
export async function exportToPDF(
  elementId: string,
  filename: string = '查重报告.pdf'
): Promise<void> {
  const element = document.getElementById(elementId)
  if (!element) {
    throw new Error('Element not found')
  }

  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    logging: false,
  })

  const imgData = canvas.toDataURL('image/png')
  const pdf = new jsPDF('p', 'mm', 'a4')

  const pdfWidth = pdf.internal.pageSize.getWidth()
  const pdfHeight = pdf.internal.pageSize.getHeight()
  const imgWidth = canvas.width
  const imgHeight = canvas.height
  const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight)

  const imgX = (pdfWidth - imgWidth * ratio) / 2
  let imgY = 0

  let heightLeft = imgHeight * ratio
  let position = 0

  // 添加第一页
  pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio)
  heightLeft -= pdfHeight

  // 如果内容超出，添加更多页面
  while (heightLeft > 0) {
    position = heightLeft - imgHeight * ratio
    pdf.addPage()
    pdf.addImage(imgData, 'PNG', imgX, position, imgWidth * ratio, imgHeight * ratio)
    heightLeft -= pdfHeight
  }

  pdf.save(filename)
}

/**
 * 导出为HTML文件
 */
export function exportToHTML(
  data: PlagiarismReportData,
  originalText: string,
  options: ReportExportOptions,
  filename: string = '查重报告.html'
): void {
  const html = generateReportHTML(data, originalText, options)

  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

/**
 * 导出为JSON
 */
export function exportToJSON(
  data: PlagiarismReportData,
  originalText: string,
  filename: string = '查重报告.json'
): void {
  const exportData = {
    report: data,
    originalText,
    exportTime: new Date().toISOString(),
  }

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

/**
 * 主导出函数
 */
export async function exportReport(
  data: PlagiarismReportData,
  originalText: string,
  options: ReportExportOptions,
  elementId?: string
): Promise<void> {
  const timestamp = new Date().toISOString().slice(0, 10)
  const filename = `查重报告_${timestamp}`

  switch (options.format) {
    case 'pdf':
      if (!elementId) {
        throw new Error('PDF export requires elementId')
      }
      await exportToPDF(elementId, `${filename}.pdf`)
      break

    case 'html':
      exportToHTML(data, originalText, options, `${filename}.html`)
      break

    case 'json':
      exportToJSON(data, originalText, `${filename}.json`)
      break

    default:
      throw new Error(`Unsupported format: ${options.format}`)
  }
}

export default {
  exportReport,
  exportToPDF,
  exportToHTML,
  exportToJSON,
}
