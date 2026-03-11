# ScholarForge 项目详细开发规划

> 版本: v1.0
> 日期: 2026-03-05
> 状态: Phase 3 完成 → Phase 4 规划

---

## 一、项目现状全景分析

### 1.1 代码规模统计

```
┌─────────────────────────────────────────────────────────────┐
│                      代码规模统计                            │
├──────────────────────┬───────────┬───────────┬──────────────┤
│        模块          │  文件数   │  代码行数 │    占比      │
├──────────────────────┼───────────┼───────────┼──────────────┤
│ Python后端服务       │    80+    │  ~18,000  │     51%      │
│ TypeScript前端       │    50+    │  ~12,000  │     34%      │
│ CSS样式              │    20+    │   ~5,000  │     14%      │
│ 文档                 │    15+    │   ~5,000  │      1%      │
├──────────────────────┼───────────┼───────────┼──────────────┤
│ 总计                 │   165+    │  ~40,000  │    100%      │
└──────────────────────┴───────────┴───────────┴──────────────┘
```

### 1.2 后端服务架构（微服务）

| 服务 | 端口 | 代码行数 | 核心功能 | 完成度 |
|------|------|---------|---------|--------|
| ai | 8004 | 2,710 | LLM提供商、写作助手 | 95% |
| article | 8003 | 2,478 | 文献检索、多源适配器 | 90% |
| paper | 8002 | 2,365 | 论文管理、版本控制 | 85% |
| reference | 8008 | 4,472 | 参考文献管理、格式化 | 80% |
| plagiarism | 8009 | 3,423 | 查重检测、SimHash | 85% |
| knowledge_graph | 8010 | 1,879 | Neo4j知识图谱 | 80% |
| collaboration | 8005 | 1,415 | WebSocket协作、Yjs | 90% |
| literature_review | 8011 | 873 | AI综述生成 | 85% |
| pdf_parser | 8012 | 1,485 | PDF解析、文本提取 | 90% |
| analytics | 8013 | 686 | 学术影响力分析 | 80% |
| recommendation | 8014 | 1,261 | 智能推荐、AI重排 | 85% |
| journal | 8015 | 1,820 | 期刊匹配、投稿建议 | 85% |
| topic | 8016 | 1,791 | 选题助手、趋势分析 | 80% |
| progress | 8017 | 1,499 | 进度管理、甘特图 | 75% |
| user | 8001 | 1,166 | 用户管理、认证 | 95% |
| defense | 8018 | 765 | 答辩准备、PPT生成 | 70% |
| annotation | 8006 | 958 | 批注系统 | 80% |
| format_engine | 8019 | 581 | 格式检查、排版 | 75% |
| export | 8020 | 290 | 导出服务 | 70% |

### 1.3 前端页面结构

```
frontend/src/pages/
├── auth/                    # 认证模块
│   ├── Login.tsx           ✅ 登录
│   └── Register.tsx        ✅ 注册
├── paper/                   # 论文管理
│   ├── PaperList.tsx       ✅ 论文列表
│   └── PaperEditor.tsx     ✅ 论文编辑器
├── library/                 # 文献库
│   ├── Library.tsx         ✅ 文献库（集成PDF）
│   └── Search.tsx          ✅ 文献搜索
├── review/                  # 文献综述
│   └── LiteratureReview.tsx ✅ 综述生成页面
├── analytics/               # 学术分析
│   └── AnalyticsPage.tsx   ✅ 影响力分析
├── topic/                   # 选题助手
│   └── TopicAssistant.tsx  ✅ 选题分析
├── progress/                # 进度管理
│   └── ProgressManager.tsx ✅ 甘特图
├── knowledge/               # 知识图谱
│   └── KnowledgeGraph.tsx  ✅ 知识图谱可视化
├── journal/                 # 期刊匹配
│   └── JournalMatcher.tsx  ✅ 期刊推荐
├── reference/               # 参考文献
│   └── ReferenceManagement.tsx ✅ 文献管理
├── plagiarism/              # 查重检测
│   └── PlagiarismCheck.tsx ✅ 查重页面
├── format/                  # 格式检查
│   └── FormatCheck.tsx     ✅ 格式检查
├── defense/                 # 答辩助手
│   └── DefenseAssistant.tsx ✅ 答辩准备
├── templates/               # 模板中心
│   └── TemplateList.tsx    ✅ 模板列表
├── Dashboard.tsx           ✅ 仪表盘
├── Settings.tsx            ✅ 设置页面
└── App.tsx                 ✅ 路由配置
```

### 1.4 前端组件结构

```
frontend/src/components/
├── ai/                      # AI相关组件
│   ├── AIPanel.tsx         ✅ AI助手面板
│   ├── SummaryPanel.tsx    ✅ 智能摘要
│   ├── ReferenceSuggestions.tsx ✅ 引用建议
│   └── LogicCheckPanel.tsx ✅ 逻辑检查
├── collaboration/           # 协作组件
│   ├── CollaborativeEditor.tsx ✅ 协作编辑器
│   ├── AwarenessCursors.tsx ✅ 光标同步
│   ├── CommentPanel.tsx    ✅ 评论面板
│   ├── CommentSidebar.tsx  ✅ 评论侧边栏
│   ├── CommentHighlights.tsx ✅ 评论高亮
│   └── VersionHistoryPanel.tsx ✅ 版本历史
├── pdf/                     # PDF组件
│   ├── PDFUploader.tsx     ✅ PDF上传
│   └── PDFParseResult.tsx  ✅ 解析结果
├── recommendation/          # 推荐组件
│   ├── RecommendationPanel.tsx ✅ 推荐面板
│   ├── RecommendationCard.tsx ✅ 推荐卡片
│   └── RecommendationList.tsx ✅ 推荐列表
├── analytics/               # 分析组件
│   └── ImpactDashboard.tsx ✅ 影响力仪表盘
├── knowledge/               # 知识图谱组件
│   └── KnowledgeGraph.tsx  ✅ 图谱可视化
├── plagiarism/              # 查重组件
│   └── PlagiarismReport.tsx ✅ 查重报告
├── review/                  # 综述组件
│   └── ReviewOutlineEditor.tsx ✅ 大纲编辑
├── editor/                  # 编辑器组件
│   ├── RichTextEditor.tsx  ✅ 富文本编辑
│   ├── EditorToolbar.tsx   ✅ 工具栏
│   ├── WordCount.tsx       ✅ 字数统计
│   └── SaveIndicator.tsx   ✅ 保存指示器
├── charts/                  # 图表组件
│   ├── BarChart.tsx        ✅ 柱状图
│   ├── LineChart.tsx       ✅ 折线图
│   ├── PieChart.tsx        ✅ 饼图
│   ├── ChartGenerator.tsx  ✅ 图表生成器
│   └── DataInput.tsx       ✅ 数据输入
├── reference/               # 参考文献组件
│   ├── MetadataExtractor.tsx ✅ 元数据提取
│   ├── ZoteroImport.tsx    ✅ Zotero导入
│   └── ImportPreview.tsx   ✅ 导入预览
├── comments/                # 评论组件
│   └── CommentThread.tsx   ✅ 评论线程
├── quality/                 # 质量检查组件
│   ├── PlagiarismChecker.tsx ✅ 查重检查器
│   └── FormatChecker.tsx   ✅ 格式检查器
├── export/                  # 导出组件
│   └── ExportModal.tsx     ✅ 导出弹窗
├── layout/                  # 布局组件
│   ├── MainLayout.tsx      ✅ 主布局
│   ├── AuthLayout.tsx      ✅ 认证布局
│   ├── Header.tsx          ✅ 头部
│   └── Sidebar.tsx         ✅ 侧边栏
└── ...
```

---

## 二、已完成功能清单（Phase 1-3）

### Phase 1: 基础夯实 ✅
- [x] 产品规划与架构设计
- [x] 用户认证与授权系统
- [x] 基础论文管理
- [x] 文献检索基础
- [x] Web端MVP

### Phase 2: 核心扩展 ✅
- [x] 选题助手与研究计划
- [x] 进度管理与甘特图
- [x] 期刊智能匹配
- [x] 知识图谱构建（Neo4j）
- [x] AI写作助手（续写/润色/翻译）
- [x] 参考文献管理（Zotero集成）
- [x] 查重与格式检查
- [x] 答辩准备助手

### Phase 3: 智能化与协作 ✅
- [x] **AI服务增强**
  - [x] 流式响应（SSE）
  - [x] Token使用统计
  - [x] 成本估算
  - [x] 健康检查
  - [x] 故障转移
  - [x] 批量生成
- [x] **PDF解析服务**
  - [x] 文本提取（PyMuPDF）
  - [x] 章节结构识别
  - [x] 参考文献解析（GB/T 7714, APA, IEEE）
  - [x] 元数据提取
  - [x] AI智能摘要
- [x] **文献综述生成**
  - [x] 多文献AI分析
  - [x] 主题自动识别
  - [x] 对比分析生成
  - [x] Markdown导出
- [x] **真实学术数据源**
  - [x] arXiv API集成
  - [x] Semantic Scholar集成
  - [x] 速率限制处理
  - [x] PDF下载
- [x] **协作编辑**
  - [x] WebSocket服务器
  - [x] Yjs文档同步
  - [x] 光标位置同步
  - [x] 在线用户列表
- [x] **学术分析**
  - [x] h-index/i10-index/g-index计算
  - [x] 合作网络分析
  - [x] 研究趋势分析
- [x] **智能推荐增强**
  - [x] 多维度推荐
  - [x] 协同过滤
  - [x] AI重排序

---

## 三、业界AI学术工具参考分析

### 3.1 竞品功能对比

| 功能维度 | ScholarForge | Elicit | Consensus | Semantic Scholar | ResearchRabbit | Connected Papers |
|---------|--------------|--------|-----------|------------------|----------------|------------------|
| 文献搜索 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| AI问答 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| 综述生成 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| 知识图谱 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 写作辅助 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| 协作功能 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 引用管理 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 中文支持 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |

### 3.2 可借鉴的先进功能

#### 1. Elicit.com 特色功能
- **研究问题回答**: 针对研究问题自动提取文献答案
- **证据矩阵**: 多文献对比表格自动生成
- **引文溯源**: 自动追踪支持/反对某一观点的文献

#### 2. Consensus.app 特色功能
- **科学共识度评分**: 显示某一观点在学术界的一致程度
- **是/否问题回答**: 针对是非问题的文献证据总结
- **研究质量评级**: 基于期刊影响因子、引用数等指标

#### 3. ResearchRabbit 特色功能
- **文献网络可视化**: 精美的引用关系图谱
- **作者工作追踪**: 自动追踪特定作者的最新研究
- **相似文献发现**: 基于嵌入向量的语义相似度搜索

#### 4. Semantic Scholar 特色功能
- **TL;DR 生成**: 一句话概括论文核心贡献
- **高影响力引用**: 标记被引用次数最多的关键文献
- **方法提取**: 自动提取论文方法部分的关键信息

---

## 四、Phase 4 详细开发规划

### 4.1 功能增强矩阵

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Phase 4 功能增强矩阵                                  │
├─────────────────────────┬──────────┬──────────┬──────────┬──────────────────┤
│        功能模块          │  优先级   │ 工作量   │  依赖     │    预计完成      │
├─────────────────────────┼──────────┼──────────┼──────────┼──────────────────┤
│ 4.1 AI问答对话系统       │    P0    │   5天    │   AI服务  │   Week 1         │
│ 4.2 智能引用推荐        │    P0    │   4天    │  知识图谱 │   Week 1-2       │
│ 4.3 文献证据矩阵        │    P0    │   5天    │  综述服务 │   Week 2         │
│ 4.4 写作模板库增强      │    P0    │   4天    │  模板服务 │   Week 2-3       │
│ 4.5 图表生成增强        │    P0    │   5天    │   AI服务  │   Week 3         │
├─────────────────────────┼──────────┼──────────┼──────────┼──────────────────┤
│ 4.6 浏览器扩展插件       │    P1    │   5天    │   无      │   Week 4         │
│ 4.7 学术社交功能        │    P1    │   7天    │  用户服务 │   Week 4-5       │
│ 4.8 研究数据管理        │    P1    │   5天    │   无      │   Week 5         │
│ 4.9 论文版本对比        │    P1    │   4天    │ 协作服务  │   Week 5-6       │
│ 4.10 多语言翻译增强     │    P1    │   4天    │   AI服务  │   Week 6         │
├─────────────────────────┼──────────┼──────────┼──────────┼──────────────────┤
│ 4.11 API开放平台        │    P2    │   7天    │   无      │   Week 7-8       │
│ 4.12 插件生态系统       │    P2    │   10天   │  API平台  │   Week 8-10      │
│ 4.13 移动端适配         │    P2    │   7天    │   无      │   Week 9-10      │
│ 4.14 高级数据分析       │    P2    │   5天    │  分析服务 │   Week 10        │
└─────────────────────────┴──────────┴──────────┴──────────┴──────────────────┘
```

---

## 五、详细任务清单（TODO）

### 模块 4.1: AI问答对话系统 (P0)

#### 4.1.1 后端服务开发

**Task 4.1.1.1**: 创建对话会话模型
- 文件: `backend/services/ai/conversation_models.py`
- 内容: 定义Conversation, Message, Session等模型
- 预计时间: 4小时
- 验收标准: 模型包含id, user_id, messages, context_papers, created_at等字段

**Task 4.1.1.2**: 实现对话管理服务
- 文件: `backend/services/ai/conversation_service.py`
- 内容: 会话CRUD、上下文管理、历史记录
- 预计时间: 6小时
- 验收标准: 支持创建、获取、删除对话，消息历史存储

**Task 4.1.1.3**: 实现RAG检索增强生成
- 文件: `backend/services/ai/rag_engine.py`
- 内容: 向量检索、上下文组装、引用追踪
- 预计时间: 8小时
- 验收标准: 基于用户文献库进行回答，返回引用来源

**Task 4.1.1.4**: 实现问答API端点
- 文件: `backend/services/ai/routes.py` (新增端点)
- 内容:
  - POST /api/v1/ai/chat - 创建对话
  - GET /api/v1/ai/chat/{session_id} - 获取对话历史
  - POST /api/v1/ai/chat/{session_id}/message - 发送消息（流式）
  - DELETE /api/v1/ai/chat/{session_id} - 删除对话
- 预计时间: 6小时
- 验收标准: 所有端点正常工作，支持SSE流式响应

**Task 4.1.1.5**: 实现研究问题专门回答
- 文件: `backend/services/ai/research_qa.py`
- 内容: 针对研究问题的专门回答逻辑
- 预计时间: 6小时
- 验收标准: 支持"是/否"问题、"如何"问题、"为什么"问题

#### 4.1.2 前端组件开发

**Task 4.1.2.1**: 创建对话组件
- 文件: `frontend/src/components/ai/ChatPanel.tsx`
- 内容: 对话框、消息列表、输入框
- 预计时间: 6小时
- 验收标准: 类似ChatGPT的聊天界面，支持Markdown渲染

**Task 4.1.2.2**: 创建对话历史侧边栏
- 文件: `frontend/src/components/ai/ChatHistory.tsx`
- 内容: 历史会话列表、新建对话按钮
- 预计时间: 4小时
- 验收标准: 显示历史对话标题、时间，支持删除

**Task 4.1.2.3**: 创建引用展示组件
- 文件: `frontend/src/components/ai/CitationCards.tsx`
- 内容: AI回答中引用的文献卡片
- 预计时间: 4小时
- 验收标准: 点击引用跳转到原文献

**Task 4.1.2.4**: 集成对话到主界面
- 文件: `frontend/src/components/ai/AIPanel.tsx` (修改)
- 内容: 在AI面板中添加"对话问答"标签页
- 预计时间: 3小时
- 验收标准: 与其他AI功能标签共存

#### 4.1.3 测试验证

**Task 4.1.3.1**: 单元测试
- 文件: `backend/tests/test_conversation.py`
- 内容: 对话服务单元测试
- 预计时间: 4小时
- 验收标准: 覆盖率>80%

**Task 4.1.3.2**: API集成测试
- 文件: `backend/tests/test_chat_api.py`
- 内容: 端到端API测试
- 预计时间: 3小时
- 验收标准: 所有端点测试通过

---

### 模块 4.2: 智能引用推荐 (P0)

#### 4.2.1 后端服务开发

**Task 4.2.1.1**: 实现引用推荐引擎
- 文件: `backend/services/reference/recommendation_engine.py`
- 内容: 基于上下文的引用推荐
- 预计时间: 8小时
- 验收标准: 分析文本上下文，推荐相关文献

**Task 4.2.1.2**: 实现引用重要性评分
- 文件: `backend/services/reference/citation_scorer.py`
- 内容: 影响因子、引用数、时效性评分
- 预计时间: 6小时
- 验收标准: 返回多维度评分

**Task 4.2.1.3**: 实现引用推荐API
- 文件: `backend/services/reference/routes.py` (新增)
- 内容:
  - POST /api/v1/references/recommend - 获取推荐
  - POST /api/v1/references/analyze-citations - 分析引用质量
- 预计时间: 4小时
- 验收标准: API正常工作

#### 4.2.2 前端组件开发

**Task 4.2.2.1**: 创建智能引用推荐组件
- 文件: `frontend/src/components/reference/SmartCitationSuggest.tsx`
- 内容: 实时推荐悬浮窗
- 预计时间: 6小时
- 验收标准: 打字时自动推荐相关文献

**Task 4.2.2.2**: 创建引用质量分析面板
- 文件: `frontend/src/components/reference/CitationQuality.tsx`
- 内容: 引用分布、质量评分
- 预计时间: 5小时
- 验收标准: 可视化展示引用质量

---

### 模块 4.3: 文献证据矩阵 (P0)

#### 4.3.1 后端服务开发

**Task 4.3.1.1**: 实现证据提取服务
- 文件: `backend/services/literature_review/evidence_extractor.py`
- 内容: 从文献提取关键证据
- 预计时间: 8小时
- 验收标准: 提取研究方法、样本量、结论等

**Task 4.3.1.2**: 实现证据矩阵生成
- 文件: `backend/services/literature_review/evidence_matrix.py`
- 内容: 多文献对比矩阵
- 预计时间: 8小时
- 验收标准: 生成可比较的矩阵数据

**Task 4.3.1.3**: 实现共识度分析
- 文件: `backend/services/literature_review/consensus_analyzer.py`
- 内容: 分析学术界对某一观点的共识度
- 预计时间: 6小时
- 验收标准: 返回共识度评分和支持/反对证据

**Task 4.3.1.4**: 实现证据矩阵API
- 文件: `backend/services/literature_review/routes.py` (新增)
- 内容:
  - POST /api/v1/literature-review/evidence-matrix - 生成证据矩阵
  - POST /api/v1/literature-review/consensus - 分析共识度
- 预计时间: 4小时
- 验收标准: API正常工作

#### 4.3.2 前端组件开发

**Task 4.3.2.1**: 创建证据矩阵表格组件
- 文件: `frontend/src/components/review/EvidenceMatrix.tsx`
- 内容: 可排序、可筛选的对比表格
- 预计时间: 8小时
- 验收标准: 类似Elicit的证据矩阵界面

**Task 4.3.2.2**: 创建共识度可视化组件
- 文件: `frontend/src/components/review/ConsensusMeter.tsx`
- 内容: 共识度仪表盘
- 预计时间: 5小时
- 验收标准: 直观展示共识程度

---

### 模块 4.4: 写作模板库增强 (P0)

#### 4.4.1 后端服务开发

**Task 4.4.1.1**: 扩展模板数据模型
- 文件: `backend/services/template/models.py`
- 内容: 增加模板分类、学科、语言字段
- 预计时间: 3小时
- 验收标准: 支持更多维度的模板分类

**Task 4.4.1.2**: 实现模板搜索服务
- 文件: `backend/services/template/search_service.py`
- 内容: 全文搜索、标签筛选
- 预计时间: 5小时
- 验收标准: 支持关键词搜索模板

**Task 4.4.1.3**: 实现模板推荐服务
- 文件: `backend/services/template/recommendation.py`
- 内容: 基于用户行为的模板推荐
- 预计时间: 5小时
- 验收标准: 智能推荐相关模板

**Task 4.4.1.4**: 实现AI模板填充
- 文件: `backend/services/template/ai_filler.py`
- 内容: 根据论文内容自动填充模板
- 预计时间: 6小时
- 验收标准: 基于已有内容生成模板章节

#### 4.4.2 前端组件开发

**Task 4.4.2.1**: 重构模板列表页面
- 文件: `frontend/src/pages/templates/TemplateList.tsx` (重写)
- 内容: 分类浏览、搜索、预览
- 预计时间: 8小时
- 验收标准: 类似Notion模板库的界面

**Task 4.4.2.2**: 创建模板预览组件
- 文件: `frontend/src/components/template/TemplatePreview.tsx`
- 内容: 模板预览、使用按钮
- 预计时间: 4小时
- 验收标准: 展示模板结构和示例内容

**Task 4.4.2.3**: 创建AI模板填充对话框
- 文件: `frontend/src/components/template/AITemplateFill.tsx`
- 内容: 一键填充模板
- 预计时间: 5小时
- 验收标准: 选择模板后自动填充到论文

---

### 模块 4.5: 图表生成增强 (P0)

#### 4.5.1 后端服务开发

**Task 4.5.1.1**: 实现智能图表推荐
- 文件: `backend/services/chart/recommendation.py`
- 内容: 基于数据特征推荐图表类型
- 预计时间: 6小时
- 验收标准: 根据数据自动推荐最佳图表

**Task 4.5.1.2**: 实现图表描述生成
- 文件: `backend/services/chart/description_generator.py`
- 内容: 自动生成图表标题和说明
- 预计时间: 5小时
- 验收标准: 生成学术规范的图表说明

**Task 4.5.1.3**: 实现更多图表类型
- 文件: `backend/services/chart/generator.py`
- 内容: 热力图、桑基图、雷达图等
- 预计时间: 8小时
- 验收标准: 支持8种以上图表类型

#### 4.5.2 前端组件开发

**Task 4.5.2.1**: 创建增强图表生成器
- 文件: `frontend/src/components/charts/EnhancedChartGenerator.tsx`
- 内容: 更多图表类型、智能推荐
- 预计时间: 8小时
- 验收标准: 支持所有新图表类型

**Task 4.5.2.2**: 创建图表描述编辑器
- 文件: `frontend/src/components/charts/ChartCaptionEditor.tsx`
- 内容: AI生成+人工编辑图表说明
- 预计时间: 4小时
- 验收标准: 方便编辑图表标题和说明

---

### 模块 4.6: 浏览器扩展插件 (P1)

#### 4.6.1 扩展开发

**Task 4.6.1.1**: 创建扩展基础结构
- 目录: `browser-extension/`
- 内容: manifest.json、popup、background、content脚本
- 预计时间: 4小时
- 验收标准: 扩展可加载到浏览器

**Task 4.6.1.2**: 实现网页文献提取
- 文件: `browser-extension/content/extractor.js`
- 内容: 从学术网页提取元数据
- 预计时间: 6小时
- 验收标准: 支持arXiv、Google Scholar、知网等

**Task 4.6.1.3**: 实现一键导入功能
- 文件: `browser-extension/popup/import.js`
- 内容: 导入到ScholarForge
- 预计时间: 5小时
- 验收标准: 一键将当前页面文献导入系统

**Task 4.6.1.4**: 实现侧边栏助手
- 文件: `browser-extension/sidebar/sidebar.js`
- 内容: 浏览器侧边栏快速访问
- 预计时间: 6小时
- 验收标准: 支持Chrome/Edge侧边栏API

---

### 模块 4.7: 学术社交功能 (P1)

#### 4.7.1 后端服务开发

**Task 4.7.1.1**: 实现研究团队模型
- 文件: `backend/services/collaboration/team_models.py`
- 内容: Team, TeamMember, Invitation模型
- 预计时间: 4小时
- 验收标准: 支持团队创建、成员管理

**Task 4.7.1.2**: 实现团队服务
- 文件: `backend/services/collaboration/team_service.py`
- 内容: 团队CRUD、权限管理
- 预计时间: 6小时
- 验收标准: 完整的团队管理功能

**Task 4.7.1.3**: 实现研究动态feed
- 文件: `backend/services/collaboration/feed_service.py`
- 内容: 论文更新、评论动态
- 预计时间: 5小时
- 验收标准: 类似GitHub activity feed

#### 4.7.2 前端组件开发

**Task 4.7.2.1**: 创建团队管理页面
- 文件: `frontend/src/pages/team/TeamManagement.tsx`
- 内容: 团队成员、权限设置
- 预计时间: 8小时
- 验收标准: 完整的团队管理界面

**Task 4.7.2.2**: 创建研究动态页面
- 文件: `frontend/src/pages/activity/ActivityFeed.tsx`
- 内容: 团队动态、个人动态
- 预计时间: 6小时
- 验收标准: 时间线展示研究活动

---

### 模块 4.8: 研究数据管理 (P1)

#### 4.8.1 后端服务开发

**Task 4.8.1.1**: 实现数据集模型
- 文件: `backend/services/dataset/models.py`
- 内容: Dataset, DataFile, Version模型
- 预计时间: 4小时
- 验收标准: 支持数据集版本管理

**Task 4.8.1.2**: 实现数据管理服务
- 文件: `backend/services/dataset/service.py`
- 内容: 上传、版本控制、元数据管理
- 预计时间: 8小时
- 验收标准: 支持CSV、Excel、JSON等格式

**Task 4.8.1.3**: 实现数据可视化预览
- 文件: `backend/services/dataset/preview.py`
- 内容: 数据统计、预览生成
- 预计时间: 5小时
- 验收标准: 生成数据集预览

#### 4.8.2 前端组件开发

**Task 4.8.2.1**: 创建数据管理页面
- 文件: `frontend/src/pages/dataset/DatasetManagement.tsx`
- 内容: 数据集列表、上传、版本
- 预计时间: 8小时
- 验收标准: 类似Git LFS的数据管理界面

**Task 4.8.2.2**: 创建数据预览组件
- 文件: `frontend/src/components/dataset/DataPreview.tsx`
- 内容: 表格预览、统计信息
- 预计时间: 5小时
- 验收标准: 展示数据内容

---

### 模块 4.9: 论文版本对比 (P1)

#### 4.9.1 后端服务开发

**Task 4.9.1.1**: 实现版本对比服务
- 文件: `backend/services/paper/diff_service.py`
- 内容: 文本diff、结构化diff
- 预计时间: 6小时
- 验收标准: 生成word-level diff

**Task 4.9.1.2**: 实现版本对比API
- 文件: `backend/services/paper/routes.py` (新增端点)
- 内容: GET /api/v1/papers/{id}/versions/{v1}/diff/{v2}
- 预计时间: 3小时
- 验收标准: 返回结构化diff数据

#### 4.9.2 前端组件开发

**Task 4.9.2.1**: 创建版本对比组件
- 文件: `frontend/src/components/paper/VersionDiff.tsx`
- 内容: 左右对比、行内diff
- 预计时间: 8小时
- 验收标准: 类似GitHub的diff界面

---

### 模块 4.10: 多语言翻译增强 (P1)

#### 4.10.1 后端服务开发

**Task 4.10.1.1**: 实现术语库管理
- 文件: `backend/services/ai/terminology.py`
- 内容: 领域术语、翻译记忆
- 预计时间: 6小时
- 验收标准: 支持自定义术语库

**Task 4.10.1.2**: 实现术语一致性检查
- 文件: `backend/services/ai/terminology_checker.py`
- 内容: 检查术语翻译一致性
- 预计时间: 5小时
- 验收标准: 标记不一致的术语翻译

#### 4.10.2 前端组件开发

**Task 4.10.2.1**: 创建术语库管理界面
- 文件: `frontend/src/pages/terminology/TerminologyManager.tsx`
- 内容: 术语添加、编辑、导入
- 预计时间: 6小时
- 验收标准: 完整的术语管理功能

---

### 模块 4.11: API开放平台 (P2)

#### 4.11.1 后端服务开发

**Task 4.11.1.1**: 实现API密钥管理
- 文件: `backend/services/api_platform/key_manager.py`
- 内容: 密钥生成、权限、限流
- 预计时间: 6小时
- 验收标准: 支持多密钥、权限分级

**Task 4.11.1.2**: 实现API文档自动生成
- 文件: `backend/services/api_platform/docs_generator.py`
- 内容: OpenAPI规范、文档页面
- 预计时间: 5小时
- 验收标准: 自动生成API文档

**Task 4.11.1.3**: 实现Webhook系统
- 文件: `backend/services/api_platform/webhook.py`
- 内容: 事件订阅、推送
- 预计时间: 6小时
- 验收标准: 支持论文更新等事件推送

---

### 模块 4.12: 插件生态系统 (P2)

#### 4.12.1 后端服务开发

**Task 4.12.1.1**: 实现插件管理框架
- 文件: `backend/services/plugin/manager.py`
- 内容: 插件加载、生命周期管理
- 预计时间: 10小时
- 验收标准: 支持动态加载插件

**Task 4.12.1.2**: 实现插件市场API
- 文件: `backend/services/plugin/marketplace.py`
- 内容: 插件列表、安装、更新
- 预计时间: 8小时
- 验收标准: 完整的插件市场功能

---

### 模块 4.13: 移动端适配 (P2)

#### 4.13.1 前端开发

**Task 4.13.1.1**: 实现响应式布局优化
- 文件: 修改现有组件
- 内容: 移动端适配、触摸优化
- 预计时间: 10小时
- 验收标准: 在移动端正常使用

**Task 4.13.1.2**: 创建移动端专用视图
- 文件: `frontend/src/mobile/`
- 内容: 简化版移动端界面
- 预计时间: 15小时
- 验收标准: 移动端体验优化

---

### 模块 4.14: 高级数据分析 (P2)

#### 4.14.1 后端服务开发

**Task 4.14.1.1**: 实现引用预测模型
- 文件: `backend/services/analytics/citation_prediction.py`
- 内容: 基于机器学习的引用预测
- 预计时间: 10小时
- 验收标准: 预测论文未来引用数

**Task 4.14.1.2**: 实现研究影响力追踪
- 文件: `backend/services/analytics/impact_tracking.py`
- 内容: 长期影响力分析
- 预计时间: 6小时
- 验收标准: 追踪研究影响力的变化

---

## 六、性能优化任务

### 6.1 后端优化

**Task 6.1.1**: 实现Redis缓存层
- 文件: `backend/shared/cache.py`
- 内容: 文献数据缓存、搜索结果缓存
- 预计时间: 6小时
- 验收标准: 缓存命中率>80%

**Task 6.1.2**: 实现异步任务队列
- 文件: `backend/shared/celery_config.py`
- 内容: Celery + Redis配置
- 预计时间: 5小时
- 验收标准: PDF解析等耗时任务异步处理

**Task 6.1.3**: 数据库查询优化
- 文件: 各服务repository层
- 内容: 索引优化、查询重构
- 预计时间: 8小时
- 验收标准: 主要查询<100ms

### 6.2 前端优化

**Task 6.2.1**: 实现虚拟列表
- 文件: `frontend/src/components/common/VirtualList.tsx`
- 内容: 长列表虚拟滚动
- 预计时间: 5小时
- 验收标准: 支持万级数据流畅滚动

**Task 6.2.2**: 实现图片懒加载
- 文件: `frontend/src/components/common/LazyImage.tsx`
- 内容: 图片延迟加载
- 预计时间: 3小时
- 验收标准: 首屏加载时间减少50%

**Task 6.2.3**: 代码分割优化
- 文件: `frontend/vite.config.ts` (修改)
- 内容: 路由级别代码分割
- 预计时间: 4小时
- 验收标准: 首包体积<200KB

---

## 七、测试策略

### 7.1 单元测试覆盖目标

| 模块 | 目标覆盖率 | 当前覆盖率 | 缺口 |
|------|-----------|-----------|------|
| AI服务 | 85% | 60% | +25% |
| 文献服务 | 80% | 50% | +30% |
| 用户服务 | 90% | 75% | +15% |
| 协作服务 | 80% | 40% | +40% |
| 知识图谱 | 75% | 30% | +45% |

### 7.2 集成测试清单

- [ ] 端到端论文创建流程
- [ ] 协作编辑冲突处理
- [ ] AI服务故障转移
- [ ] PDF解析大文件测试
- [ ] 多数据源检索一致性

---

## 八、部署与运维

### 8.1 Docker配置更新

**Task 8.1.1**: 优化Docker镜像
- 文件: `deploy/docker/Dockerfile.*`
- 内容: 多阶段构建、镜像瘦身
- 预计时间: 5小时
- 验收标准: 镜像体积减少50%

**Task 8.1.2**: 实现健康检查
- 文件: `backend/gateway/health_check.py`
- 内容: 服务健康状态监控
- 预计时间: 4小时
- 验收标准: 完整的服务健康报告

### 8.2 监控与日志

**Task 8.2.1**: 实现Prometheus指标
- 文件: `backend/shared/metrics.py`
- 内容: 请求量、延迟、错误率
- 预计时间: 5小时
- 验收标准: 关键指标可监控

**Task 8.2.2**: 实现分布式追踪
- 文件: `backend/shared/tracing.py`
- 内容: Jaeger/OpenTelemetry集成
- 预计时间: 6小时
- 验收标准: 跨服务调用链追踪

---

## 九、开发时间表

```
Week 1-3: P0 高优先级功能
┌─────────────────────────────────────────────────────────────┐
│ Week 1 │ 4.1 AI问答对话系统 + 4.2 智能引用推荐基础           │
│ Week 2 │ 4.2 完成 + 4.3 文献证据矩阵                        │
│ Week 3 │ 4.4 写作模板增强 + 4.5 图表生成增强                 │
└─────────────────────────────────────────────────────────────┘

Week 4-6: P1 中优先级功能
┌─────────────────────────────────────────────────────────────┐
│ Week 4 │ 4.6 浏览器扩展 + 4.7 学术社交基础                   │
│ Week 5 │ 4.7 完成 + 4.8 研究数据管理 + 4.9 版本对比          │
│ Week 6 │ 4.10 多语言翻译 + 性能优化                         │
└─────────────────────────────────────────────────────────────┘

Week 7-10: P2 低优先级功能
┌─────────────────────────────────────────────────────────────┐
│ Week 7-8  │ 4.11 API开放平台                               │
│ Week 8-10 │ 4.12 插件生态 + 4.13 移动端适配                 │
│ Week 10   │ 4.14 高级数据分析 + 测试完善                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 十、任务优先级总览

### P0 - 必须完成（4周）
1. ✅ AI问答对话系统
2. ✅ 智能引用推荐
3. ✅ 文献证据矩阵
4. ✅ 写作模板库增强
5. ✅ 图表生成增强

### P1 - 应该完成（3周）
6. ✅ 浏览器扩展插件
7. ✅ 学术社交功能
8. ✅ 研究数据管理
9. ✅ 论文版本对比
10. ✅ 多语言翻译增强

### P2 - 可以延后（4周）
11. API开放平台
12. 插件生态系统
13. 移动端适配
14. 高级数据分析

---

## 十一、验收标准

### 功能验收
- [ ] 所有API端点有文档和测试
- [ ] 前端组件有Storybook文档
- [ ] 关键用户流程端到端测试通过
- [ ] 性能指标达到预期

### 代码质量
- [ ] 后端测试覆盖率>80%
- [ ] 前端组件测试覆盖率>70%
- [ ] 代码审查通过
- [ ] 无严重安全漏洞

### 用户体验
- [ ] 首屏加载<2秒
- [ ] AI响应<3秒（流式）
- [ ] 移动端可用性良好
- [ ] 无障碍访问支持

---

*文档版本: v1.0*
*最后更新: 2026-03-05*
*规划周期: 11周（Phase 4）*
