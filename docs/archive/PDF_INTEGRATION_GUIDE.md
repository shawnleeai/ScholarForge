# PDF解析功能集成指南

> 文档日期：2026-03-04
> 版本：v1.0

---

## 一、功能概述

ScholarForge现已集成完整的PDF文献解析功能，支持：

- **PDF上传**: 拖拽上传，最大50MB
- **文本提取**: 自动提取全文、章节结构
- **元数据识别**: 标题、作者、摘要、关键词、DOI等
- **参考文献提取**: 自动识别参考文献列表
- **AI智能分析**: 自动摘要、核心观点、研究方法识别

---

## 二、前端组件

### 2.1 组件列表

| 组件 | 路径 | 说明 |
|------|------|------|
| PDFUploader | `components/pdf/PDFUploader.tsx` | PDF上传组件 |
| PDFParseResultView | `components/pdf/PDFParseResult.tsx` | 解析结果展示 |

### 2.2 使用示例

```tsx
import { PDFUploader, PDFParseResultView } from '@/components/pdf'
import type { PDFParseResult } from '@/services/pdfService'

// 在文献库页面使用
const LibraryPage = () => {
  const [parseResult, setParseResult] = useState<PDFParseResult | null>(null)

  return (
    <div>
      <PDFUploader
        onUploadSuccess={(taskId) => console.log('上传成功:', taskId)}
        onParseComplete={(result) => setParseResult(result)}
      />

      {parseResult && (
        <PDFParseResultView result={parseResult} />
      )}
    </div>
  )
}
```

---

## 三、后端服务

### 3.1 服务集成

PDF解析服务已集成到 **Article服务** (端口8002) 中：

```
Article Service (端口8002)
├── /api/v1/articles/*    文献检索API
├── /api/v1/library/*     文献库API
└── /api/v1/pdf/*         PDF解析API (新增)
```

### 3.2 API端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/pdf/upload` | 上传并解析PDF |
| GET | `/api/v1/pdf/status/{task_id}` | 查询解析状态 |
| GET | `/api/v1/pdf/result/{task_id}` | 获取解析结果 |
| GET | `/api/v1/pdf/result/{task_id}/text` | 获取全文 |
| GET | `/api/v1/pdf/result/{task_id}/references` | 获取参考文献 |
| DELETE | `/api/v1/pdf/tasks/{task_id}` | 删除解析任务 |

### 3.3 上传参数

```typescript
interface PDFParseRequest {
  enable_ai?: boolean        // 启用AI分析 (默认true)
  extract_references?: boolean  // 提取参考文献 (默认true)
  extract_figures?: boolean     // 提取图表 (默认false)
}
```

---

## 四、网关配置

已更新 `gateway/main.py` 添加PDF路由映射：

```python
SERVICES = {
    # ... 其他服务
    "/api/v1/pdf": "http://localhost:8002",  # PDF解析服务
}
```

---

## 五、启动服务

### 5.1 启动Article服务（包含PDF解析）

```bash
cd backend
python run.py article
```

### 5.2 启动网关

```bash
cd backend
python run.py gateway
```

### 5.3 启动前端

```bash
cd frontend
npm run dev
```

---

## 六、功能测试

### 6.1 测试步骤

1. 访问 http://localhost:5173/library
2. 点击"导入PDF"按钮
3. 拖拽或选择PDF文件上传
4. 等待解析完成（约30秒-2分钟）
5. 查看解析结果（元数据、AI分析、参考文献）

### 6.2 预期结果

上传PDF后将展示：
- **概览**: AI智能摘要、核心观点、研究方法
- **元数据**: 标题、作者、摘要、关键词、DOI
- **参考文献**: 提取的参考文献列表
- **章节结构**: 文档大纲

---

## 七、技术依赖

### 7.1 后端依赖

```bash
pip install PyMuPDF pdfplumber
```

### 7.2 前端依赖

已包含在项目中：
- Ant Design Upload组件
- PDF解析服务API

---

## 八、故障排除

### 8.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| PDF上传失败 | 文件过大 | 确保文件小于50MB |
| 解析超时 | 文档过长 | 减少文档页数或关闭AI分析 |
| 元数据识别不准 | PDF格式问题 | 使用标准学术论文PDF |
| 服务不可用 | 服务未启动 | 启动article服务 |

### 8.2 日志查看

```bash
# 查看article服务日志
python run.py article

# 查看网关日志
python run.py gateway
```

---

## 九、文件结构

```
backend/
├── services/
│   ├── article/
│   │   ├── main.py          # 已集成PDF路由
│   │   └── ...
│   └── pdf_parser/
│       ├── __init__.py
│       ├── parser.py        # PDF解析核心
│       ├── routes.py        # API路由
│       ├── schemas.py       # 数据模型
│       └── extractors/      # 提取器模块
├── gateway/
│   └── main.py              # 已添加PDF路由映射
└── uploads/pdf/             # 上传文件存储

frontend/
└── src/
    ├── components/pdf/
    │   ├── index.ts         # 组件导出
    │   ├── PDFUploader.tsx  # 上传组件
    │   └── PDFParseResult.tsx  # 结果展示
    ├── services/
    │   └── pdfService.ts    # PDF服务API
    └── pages/library/
        └── Library.tsx      # 已集成PDF功能
```

---

## 十、后续优化建议

1. **批量上传**: 支持同时上传多个PDF
2. **解析队列**: 实现队列管理，避免并发过高
3. **缓存机制**: 相同PDF直接返回缓存结果
4. **OCR支持**: 添加扫描版PDF的OCR识别
5. **图表提取**: 完善图表和公式提取功能

---

**最后更新**: 2026-03-04
**文档状态**: 已完成
