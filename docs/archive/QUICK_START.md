# ScholarForge 快速启动指南

> 本指南帮助您快速启动并运行 ScholarForge 的开发环境

---

## 一、环境准备

### 1.1 安装依赖

```bash
# Python 3.10+
pip install -r backend/requirements.txt

# Node.js 18+
cd frontend
npm install
```

### 1.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加您的API Key
nano .env
```

**必需的配置项**：

```env
# AI服务（至少配置一个）
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# 数据库（开发环境可以使用SQLite）
DATABASE_URL=sqlite+aiosqlite:///./scholarforge.db

# JWT密钥（用于用户认证）
JWT_SECRET=your-secret-key-at-least-32-characters
```

---

## 二、启动服务

### 2.1 启动后端服务

```bash
cd backend

# 方式1：使用统一入口（推荐）
python run.py

# 方式2：直接启动API网关
python -m uvicorn gateway.main:app --reload --port 8000
```

后端服务默认在 `http://localhost:8000` 运行

### 2.2 启动前端服务

```bash
cd frontend
npm run dev
```

前端服务默认在 `http://localhost:3000` 运行

### 2.3 验证服务状态

```bash
# 检查AI服务健康状态
curl http://localhost:8000/api/v1/ai/health

# 检查PDF解析服务
curl http://localhost:8000/api/v1/pdf/status/test

# 测试arXiv搜索
curl "http://localhost:8000/api/v1/articles/search?query=machine+learning&source=arxiv"
```

---

## 三、新功能使用指南

### 3.1 PDF文献解析

**前端界面**：
1. 登录系统
2. 进入"文献库"页面
3. 点击"导入PDF"按钮
4. 拖拽或选择PDF文件上传
5. 等待AI解析完成
6. 查看解析结果（摘要、参考文献、章节结构）

**API调用**：

```bash
# 上传并解析PDF
curl -X POST \
  -F "file=@your-paper.pdf" \
  -F "enable_ai=true" \
  -F "extract_references=true" \
  http://localhost:8000/api/v1/pdf/upload

# 查询解析状态
curl http://localhost:8000/api/v1/pdf/status/{task_id}

# 获取解析结果
curl http://localhost:8000/api/v1/pdf/result/{task_id}
```

### 3.2 arXiv文献搜索

**前端界面**：
1. 进入"文献搜索"页面
2. 选择"arXiv"数据源
3. 输入关键词搜索
4. 点击结果查看详情
5. 直接下载PDF

**API调用**：

```bash
# 搜索arXiv
curl "http://localhost:8000/api/v1/articles/search?query=deep+learning&source=arxiv&page=1"

# 获取最新论文
curl "http://localhost:8000/api/v1/articles/arxiv/recent?category=cs.AI&max_results=10"
```

### 3.3 文献综述生成

**前端界面**：
1. 进入"文献综述"页面（需要创建）
2. 从文献库选择2-50篇文献
3. 选择综述聚焦领域和长度
4. 点击"生成综述"
5. 等待AI生成完成
6. 导出为Markdown/Word/PDF

**API调用**：

```bash
# 生成综述
curl -X POST http://localhost:8000/api/v1/literature-review/generate \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": ["id1", "id2", "id3"],
    "focus_area": "general",
    "output_length": "medium"
  }'

# 导出为Markdown
curl "http://localhost:8000/api/v1/literature-review/tasks/{task_id}/export?format=markdown"
```

### 3.4 AI写作助手

**功能**：
- 智能续写：按 `Ctrl+Space` 或点击"AI续写"
- 文本润色：选中文本点击"润色"
- 学术翻译：支持中英互译
- 流式响应：实时显示生成进度

**API调用**：

```bash
# 流式生成（SSE）
curl -X POST http://localhost:8000/api/v1/ai/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "写一篇关于深度学习的介绍", "max_tokens": 500}'

# 批量生成
curl -X POST http://localhost:8000/api/v1/ai/batch \
  -H "Content-Type: application/json" \
  -d '{
    "prompts": ["总结机器学习", "总结深度学习"],
    "max_tokens": 300
  }'

# 查看AI使用统计
curl http://localhost:8000/api/v1/ai/usage
```

---

## 四、开发配置

### 4.1 前端开发模式切换

```bash
# 使用真实后端（推荐）
# .env.development
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 使用Mock数据（离线开发）
VITE_USE_MOCK=true
```

### 4.2 后端调试模式

```bash
# 开启调试日志
export DEBUG=true

# 详细SQL日志
export SQL_ECHO=true
```

### 4.3 数据库迁移

```bash
cd backend

# 生成迁移脚本
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

---

## 五、常见问题

### 5.1 AI服务返回模拟响应

**问题**：AI功能返回"[模拟响应]"而不是真实AI生成内容

**解决方案**：
1. 检查 `.env` 文件是否配置了 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`
2. 检查API Key是否有效
3. 访问 `/api/v1/ai/health` 查看服务状态

### 5.2 PDF解析超时

**问题**：大文件解析超时

**解决方案**：
1. 检查文件大小是否超过50MB限制
2. 调整超时设置：`.env` 中设置 `AI_PARSER_TIMEOUT=300`
3. 对于超大文件，可以分段处理

### 5.3 arXiv搜索无结果

**问题**：arXiv搜索返回空结果

**解决方案**：
1. arXiv API有速率限制（3秒/请求），请稍等重试
2. 检查网络连接
3. 查看后端日志确认请求是否发送成功

### 5.4 前端无法连接后端

**问题**：前端报错"无法连接到服务器"

**解决方案**：
1. 确认后端服务已启动：`curl http://localhost:8000/health`
2. 检查Vite代理配置：`vite.config.ts`
3. 检查环境变量：`.env.development`

---

## 六、目录结构

```
ScholarForge/
├── backend/                    # 后端服务
│   ├── services/              # 微服务
│   │   ├── ai/                # AI服务（增强版）
│   │   ├── pdf_parser/        # PDF解析服务（新）
│   │   ├── literature_review/ # 文献综述服务（新）
│   │   └── article/           # 文献服务
│   │       └── adapters/      # 数据源适配器
│   │           └── arxiv.py   # arXiv真实API（已更新）
│   └── gateway/               # API网关
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/
│   │   │   └── pdf/           # PDF组件（新）
│   │   ├── pages/
│   │   │   └── library/       # 文献库（已更新）
│   │   └── services/
│   │       └── pdfService.ts  # PDF服务API（新）
│   └── vite.config.ts         # Vite配置（已更新）
└── QUICK_START.md             # 本文件
```

---

## 七、下一步开发计划

### 7.1 待完成

- [ ] 文献综述前端页面
- [ ] 协作编辑实时同步
- [ ] Semantic Scholar API对接
- [ ] 移动端适配

### 7.2 优化建议

- [ ] 添加Redis缓存
- [ ] 实现异步任务队列（Celery）
- [ ] 添加更完善的错误监控
- [ ] 性能优化（数据库查询、前端加载）

---

**更新日期**: 2026-03-04
**版本**: v0.2.0-Phase3
