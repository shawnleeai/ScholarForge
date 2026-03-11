# ScholarForge 全面审核与发展规划报告

## 第一部分：现有功能审核

### 1.1 后端服务架构 (26+ 微服务)

#### 核心服务清单

| 服务类别 | 服务名称 | 状态 | 核心功能 |
|---------|---------|------|---------|
| **网关** | Gateway | ✅ | 统一入口、路由分发、负载均衡 |
| **用户** | User | ✅ | 认证、用户管理、团队管理 |
| **AI核心** | AI | ✅ | 多LLM提供商、RAG、对话、写作助手 |
| **文献** | Article | ✅ | 多源检索(arXiv/CNKI/IEEE/WOS)、PDF下载 |
| **推荐** | Recommendation | ✅ | 内容推荐、协同过滤、热门推荐 |
| **协作** | Collaboration | ✅ | 实时协作、光标同步、评论系统 |
| **知识图谱** | Knowledge Graph | ✅ | Neo4j图数据库、作者网络、引用网络 |
| **查重** | Plagiarism | ✅ | SimHash、Turnitin、网络搜索 |
| **文献综述** | Literature Review | ✅ | 证据矩阵、共识分析 |
| **论文** | Paper | ✅ | 论文编辑、版本管理 |
| **批注** | Annotation | ✅ | PDF批注、高亮 |
| **期刊** | Journal | ✅ | 期刊匹配、投稿建议 |
| **进度** | Progress | ✅ | 研究进度跟踪 |
| **导出** | Export | ✅ | 多格式导出 |
| **格式引擎** | Format Engine | ✅ | 论文格式化 |
| **图表** | Chart | ✅ | 图表生成 |
| **通知** | Notification | ✅ | WebSocket实时推送 |
| **权限** | Permission | ✅ | RBAC权限系统 |
| **安全** | Security | ✅ | AES-256加密 |
| **缓存** | Cache | ✅ | Redis缓存 |
| **数据分析** | Analytics | ✅ | 使用统计 |
| **PDF解析** | PDF Parser | ✅ | PDF内容提取 |
| **数据集** | Dataset | ✅ | 数据集管理 |
| **答辩** | Defense | ✅ | 答辩管理 |
| **模板** | Template | ✅ | 论文模板 |
| **选题** | Topic | ✅ | 智能选题 |
| **参考文献** | Reference | ✅ | 引用管理 |

#### AI服务详细分析

**支持的LLM提供商 (7个)**:
1. OpenAI (GPT-4, GPT-3.5)
2. Anthropic (Claude系列)
3. DeepSeek
4. Moonshot (月之暗面)
5. StepFun (阶跃星辰) ⭐ **已配置**
6. ChatGLM
7. Azure OpenAI

**AI功能模块**:
- `writing_assistant.py` - 写作助手（续写、润色、翻译、总结）
- `research_qa.py` - 研究问答
- `multi_hop_qa.py` - 多跳问答
- `conversation_service.py` - 对话管理
- `rag_engine.py` - RAG检索增强
- `terminology.py` - 术语库
- `reasoning/` - 推理链、事实检查
- `retrieval/` - 混合搜索、查询重写、重排序
- `prompts/` - 提示词管理

### 1.2 前端功能架构 (40+ 页面, 100+ 组件)

#### 页面路由清单

| 页面 | 功能 | 状态 |
|-----|------|------|
| Dashboard | 仪表盘首页 | ✅ |
| Paper Editor | 论文编辑器（TipTap+Yjs协作） | ✅ |
| Paper List | 论文列表 | ✅ |
| Library | 文献库管理 | ✅ |
| Search | 文献搜索（多源聚合） | ✅ |
| AI Assistant | AI写作助手面板 | ✅ |
| AI Voice Dialogue | AI语音对话 | ✅ |
| Knowledge Graph | 知识图谱可视化 | ✅ |
| Literature Review | 文献综述生成 | ✅ |
| Literature Deep Analysis | 文献深度分析 | ✅ |
| Plagiarism Check | 查重检测 | ✅ |
| Format Check | 格式检查 | ✅ |
| Defense Assistant | 答辩准备 | ✅ |
| Defense Simulation V2 | 模拟答辩 | ✅ |
| Journal Matcher | 期刊匹配 | ✅ |
| Reference Management | 参考文献管理 | ✅ |
| Topic Assistant | 智能选题 | ✅ |
| Progress Manager | 进度管理 | ✅ |
| Template Center | 模板中心 | ✅ |
| Daily Papers | 每日论文推荐 | ✅ |
| Recommendation Panel | 智能推荐 | ✅ |
| Writing Stats | 写作热力图 | ✅ |
| Analytics | 学术影响力分析 | ✅ |
| Export | 多格式导出 | ✅ |
| Settings | 系统设置 | ✅ |
| Notification Center | 通知中心 | ✅ |
| Permission Management | 权限管理 | ✅ |

#### 核心组件库

| 组件类别 | 组件数量 | 代表组件 |
|---------|---------|---------|
| AI组件 | 8 | AIPanel, AIVoiceDialogue, AIWritingAssistantV2 |
| 协作组件 | 9 | AwarenessCursors, CollaborativeEditor, CommentPanel |
| 图表组件 | 8 | ChartGenerator, EnhancedChartGenerator, WritingHeatmap |
| 分析组件 | 6 | ImpactDashboard, EvidenceMatrix, ConsensusMeter |
| 可视化组件 | 4 | KnowledgeGraph, PlagiarismReport, CitationStats |

### 1.3 数据模型

#### 核心实体

```
User (用户)
├── UserPreference (偏好设置)
├── TeamMembership (团队关系)
└── Article (文献收藏)

Paper (论文)
├── PaperVersion (版本历史)
├── Section (章节)
└── Reference (参考文献)

Conversation (AI对话)
└── Message (消息)

Team (团队)
└── TeamMember (成员)

Article (文献)
├── Collection (集合)
└── Annotation (批注)
```

---

## 第二部分：科研写作痛点与竞品分析

### 2.1 科研写作核心痛点

#### 痛点1：文献阅读与管理效率低下
- **问题**：每天面对海量文献，难以快速筛选、阅读和整理
- **现有解决方案**：文献库管理、PDF批注、多源检索
- **改进空间**：AI辅助阅读、自动摘要、文献关系图谱

#### 痛点2：论文结构与逻辑梳理困难
- **问题**：不知道该如何组织论文结构，逻辑链条不清晰
- **现有解决方案**：模板中心、大纲编辑
- **改进空间**：AI逻辑检查、自动大纲生成、结构推荐

#### 痛点3：学术写作语言表达问题
- **问题**：非母语写作者语言表达不准确、学术化程度不够
- **现有解决方案**：AI润色、翻译、术语库
- **改进空间**：实时语法检查、风格一致性检查、学科术语推荐

#### 痛点4：引用管理与格式规范
- **问题**：引用格式容易出错，参考文献管理混乱
- **现有解决方案**：智能引用、格式检查
- **改进空间**：自动引用推荐、引用质量评估、一键格式化

#### 痛点5：研究创新点挖掘困难
- **问题**：难以发现研究空白，创新点表述不清晰
- **现有解决方案**：选题助手、文献综述
- **改进空间**：研究趋势分析、创新点推荐、研究空白识别

#### 痛点6：协作与审阅效率低
- **问题**：导师反馈周期长，多人协作混乱
- **现有解决方案**：实时协作、评论系统、版本管理
- **改进空间**：AI预审阅、语音批注、智能修改建议

#### 痛点7：投稿与审稿准备不足
- **问题**：不了解期刊偏好，答辩准备不充分
- **现有解决方案**：期刊匹配、模拟答辩
- **改进空间**：期刊影响力预测、审稿人视角分析

### 2.2 竞品功能分析

#### A. ResearchRabbit (文献发现)
**核心优势**：
- 可视化文献网络图（引用关系、相似论文）
- "剥洋葱"式文献探索（从一篇文献向外扩展）
- 作者关系网络
- 研究收藏与分享

**可借鉴**：
- 更直观的文献关系可视化
- 文献探索的交互体验
- 作者合作网络分析

#### B. Elicit (AI研究助手)
**核心优势**：
- 自然语言搜索论文（无需关键词）
- 自动提取关键信息（方法、结果、样本量）
- 问答式文献综述
- 证据矩阵自动生成

**可借鉴**：
- 对话式文献探索
- 结构化信息提取
- 研究问题的自动拆解

#### C. Consensus (科学共识引擎)
**核心优势**：
- 直接回答Yes/No研究问题
- 共识度评分（支持度/反对度）
- 证据质量评估
- 一键引用

**可借鉴**：
- 共识度可视化
- 证据质量指标
- 直接回答模式

#### D. Semantic Scholar (学术搜索引擎)
**核心优势**：
- 强大的语义搜索
- TL;DR自动摘要
- 引用意图分类（背景、方法、结果）
- 作者影响力指标

**可借鉴**：
- 语义搜索能力
- 引用意图分析
- 影响力可视化

#### E. Connected Papers (文献网络)
**核心优势**：
- 图形化文献网络
- 相似论文发现
- 先前工作/衍生工作区分
- 直观的颜色编码

**可借鉴**：
- 网络图可视化效果
- 文献聚类展示
- 时间轴展示

#### F. Overleaf (LaTeX协作)
**核心优势**：
- 实时协作编辑
- 版本历史
- LaTeX编译
- 模板丰富

**可借鉴**：
- 协作编辑体验
- 版本对比
- 编译错误提示

#### G. Google Scholar (学术搜索)
**核心优势**：
- 海量文献索引
- 引用跟踪
- 学者档案
- 推荐算法

**可借鉴**：
- 引用跟踪功能
- 学者画像
- 推荐算法

### 2.3 竞品对比矩阵

| 功能维度 | ScholarForge | ResearchRabbit | Elicit | Consensus | Semantic Scholar |
|---------|-------------|----------------|--------|-----------|------------------|
| 文献搜索 | ✅✅ | ✅✅ | ✅✅✅ | ✅ | ✅✅✅ |
| 关系可视化 | ✅ | ✅✅✅ | ❌ | ❌ | ✅ |
| AI写作助手 | ✅✅✅ | ❌ | ❌ | ❌ | ❌ |
| 协作编辑 | ✅✅✅ | ❌ | ❌ | ❌ | ❌ |
| 问答交互 | ✅✅ | ❌ | ✅✅✅ | ✅✅✅ | ❌ |
| 证据矩阵 | ✅✅ | ❌ | ✅✅ | ✅✅✅ | ❌ |
| 模拟答辩 | ✅✅✅ | ❌ | ❌ | ❌ | ❌ |
| 期刊匹配 | ✅✅ | ❌ | ❌ | ❌ | ❌ |
| 知识图谱 | ✅✅ | ✅✅ | ❌ | ❌ | ❌ |
| 语音交互 | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 第三部分：AI原生解决方案设计

### 3.1 阶跃星辰(StepFun)模型选型

#### 阶跃模型能力矩阵

| 模型 | 输入 | 输出 | 特点 | 适用场景 |
|-----|------|------|------|---------|
| **step-1-32k** | 文本32K | 文本 | 通用能力强 | 常规写作、问答 |
| **step-1-128k** | 文本128K | 文本 | 长文本处理 | 长论文分析、综述 |
| **step-1-256k** | 文本256K | 文本 | 超长上下文 | 全书分析、大量文献 |
| **step-1o** | 文本+图像 | 文本 | 多模态理解 | 图表分析、图文混合 |
| **step-1v** | 文本+图像 | 文本+图像 | 视觉生成 | 图表生成、示意图 |
| **step-tts** | 文本 | 语音 | 语音合成 | 语音播报、朗读 |
| **step-asr** | 语音 | 文本 | 语音识别 | 语音输入、会议转录 |
| **step-video** | 文本/图像 | 视频 | 视频生成 | 研究演示、教学视频 |

#### 功能-模型匹配方案

```yaml
# 科研写作场景模型匹配

文本生成类:
  - 论文续写: step-1-128k (长上下文保持连贯性)
  - 段落润色: step-1-32k (快速响应)
  - 摘要生成: step-1-32k
  - 综述生成: step-1-256k (处理大量文献)
  - 逻辑检查: step-1-128k (理解全文逻辑)

多模态类:
  - 图表分析: step-1o (理解图表内容)
  - 图表生成: step-1v (生成可视化图表)
  - 公式识别: step-1o (OCR+理解)
  - 示意图生成: step-1v

语音交互类:
  - 语音输入: step-asr (实时转录)
  - 语音播报: step-tts (自然朗读)
  - 语音对话: step-asr + step-1-32k + step-tts
  - 会议记录: step-asr (多说话人识别)

视频生成类:
  - 研究演示视频: step-video (论文介绍视频)
  - 教学视频: step-video (方法讲解)
  - 答辩预演: step-video (模拟答辩场景)

复杂推理类:
  - 文献综述: step-1-256k + RAG
  - 创新点挖掘: step-1-128k (深度分析)
  - 审稿意见分析: step-1-128k
  - 多跳问答: step-1-128k
```

### 3.2 AI原生功能设计

#### 功能1：智能文献阅读助手 (Literature Copilot)

**痛点**：读文献效率低，抓不住重点

**AI解决方案**：
```
┌─────────────────────────────────────────────────────────────┐
│                    文献阅读工作流                            │
├─────────────────────────────────────────────────────────────┤
│  1. PDF上传 → step-1o (图文理解) → 结构化提取               │
│     - 研究问题、方法、结果、结论                             │
│     - 图表内容自动描述                                      │
│     - 关键数据提取                                          │
│                                                            │
│  2. 对话式探索 → step-1-128k                                │
│     - "这篇论文的核心创新是什么？"                           │
│     - "实验设计有什么缺陷？"                                │
│     - "与我的工作有什么关系？"                              │
│                                                            │
│  3. 语音交互 → step-asr + step-tts                          │
│     - 语音提问，语音回答                                    │
│     - 边读边问，解放双手                                    │
│                                                            │
│  4. 知识图谱构建 → Neo4j + step-1-32k                       │
│     - 自动提取实体和关系                                    │
│     - 与已有文献建立关联                                    │
└─────────────────────────────────────────────────────────────┘
```

**界面设计**：
- 左侧：PDF阅读器
- 右侧：AI助手面板（对话+语音按钮）
- 底部：文献关系图谱

#### 功能2：语音驱动的写作助手 (Voice-First Writing)

**痛点**：打字慢，思路容易中断

**AI解决方案**：
```
┌─────────────────────────────────────────────────────────────┐
│                    语音写作工作流                            │
├─────────────────────────────────────────────────────────────┤
│  输入层: step-asr (语音识别)                                │
│    - 支持中英文混合                                         │
│    - 学术术语识别优化                                       │
│    - 实时转录，低延迟                                       │
│                                                            │
│  处理层: step-1-128k (意图理解+结构化)                       │
│    - 口语化 → 学术化转换                                   │
│    - 自动分段、分节                                         │
│    - 逻辑结构优化                                           │
│                                                            │
│  输出层:                                                    │
│    - 文本插入编辑器                                         │
│    - step-tts 朗读确认                                      │
│    - 多版本对比                                             │
└─────────────────────────────────────────────────────────────┘
```

**交互模式**：
- 按住说话（类似微信语音）
- 语音指令："插入引用Smith2023"、"生成方法章节"、"润色这段话"

#### 功能3：视频摘要与演示生成 (Video Abstract Generator)

**痛点**：论文传播难，会议presentation准备耗时

**AI解决方案**：
```
┌─────────────────────────────────────────────────────────────┐
│                    视频生成工作流                            │
├─────────────────────────────────────────────────────────────┤
│  1. 论文解析 → step-1-128k                                  │
│     - 提取关键信息                                          │
│     - 生成视频脚本                                          │
│     - 确定视觉元素                                          │
│                                                            │
│  2. 视觉生成 → step-1v + step-video                         │
│     - 生成关键图表动画                                      │
│     - 制作演示幻灯片                                        │
│     - 生成讲解视频                                          │
│                                                            │
│  3. 语音合成 → step-tts                                     │
│     - 自然语音旁白                                          │
│     - 多语言支持                                            │
│                                                            │
│  输出: 2-3分钟论文介绍视频                                  │
└─────────────────────────────────────────────────────────────┘
```

**应用场景**：
- 论文视频摘要 (Video Abstract)
- 学术会议报告预演
- 研究方法演示视频

#### 功能4：多模态知识图谱 (Multimodal Knowledge Graph)

**痛点**：文献之间的关系难以直观理解

**AI解决方案**：
```
┌─────────────────────────────────────────────────────────────┐
│                    多模态知识图谱构建                        │
├─────────────────────────────────────────────────────────────┤
│  实体抽取: step-1o (文本+图像)                              │
│    - 作者、机构、关键词                                     │
│    - 研究方法、数据集                                       │
│    - 图表中的关键发现                                       │
│                                                            │
│  关系抽取: step-1-128k                                     │
│    - 引用关系（支持/反对/扩展）                             │
│    - 合作关系                                               │
│    - 方法继承关系                                           │
│                                                            │
│  可视化: ECharts + D3.js                                    │
│    - 3D力导向图                                             │
│    - 时间轴演化                                             │
│    - 聚类分析                                               │
│    - 路径发现                                               │
└─────────────────────────────────────────────────────────────┘
```

**特色功能**：
- 上传图片搜索相关文献（以图搜文）
- 研究趋势时间演化动画
- 作者迁徙路径可视化

#### 功能5：AI虚拟导师 (AI Virtual Advisor)

**痛点**：导师指导时间有限，反馈周期长

**AI解决方案**：
```
┌─────────────────────────────────────────────────────────────┐
│                    虚拟导师系统                              │
├─────────────────────────────────────────────────────────────┤
│  知识库构建:                                                │
│    - 上传导师历史论文、评语                                 │
│    - 领域知识库                                             │
│    - 研究方法学知识                                         │
│                                                            │
│  交互方式:                                                  │
│    - 文字对话 → step-1-128k                                │
│    - 语音对话 → step-asr + step-1-32k + step-tts           │
│    - 视频对话 → step-video (生成导师形象)                   │
│                                                            │
│  核心能力:                                                  │
│    - 论文初稿审阅                                           │
│    - 修改建议生成                                           │
│    - 研究方法指导                                           │
│    - 创新点评估                                             │
│    - 模拟答辩                                               │
└─────────────────────────────────────────────────────────────┘
```

**个性化配置**：
- 选择导师风格（严厉型/温和型/细节控）
- 设置关注重点（创新性/方法/写作）
- 语音克隆（可选）

#### 功能6：研究趋势预测与空白识别 (Trend Forecasting)

**痛点**：难以把握研究方向，不知道做什么创新

**AI解决方案**：
```
┌─────────────────────────────────────────────────────────────┐
│                    研究趋势分析系统                          │
├─────────────────────────────────────────────────────────────┤
│  数据处理:                                                  │
│    - 大规模文献分析 → step-1-256k                           │
│    - 引用网络分析                                           │
│    - 关键词演化追踪                                         │
│                                                            │
│  分析维度:                                                  │
│    - 热点趋势识别                                           │
│    - 研究空白发现                                           │
│    - 方法学演进路径                                         │
│    - 跨学科融合机会                                         │
│                                                            │
│  输出:                                                      │
│    - 趋势预测报告                                           │
│    - 研究机会推荐                                           │
│    - 风险预警（过度竞争领域）                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 第四部分：界面与数据可视化优化

### 4.1 界面显示效果优化

#### 4.1.1 设计系统升级

**当前问题**：
- 界面风格不够统一
- 动画效果较少
- 暗色主题支持不完善

**优化方案**：

```css
/* 新设计系统变量 */
:root {
  /* 品牌渐变 */
  --brand-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  --warning-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);

  /* 玻璃态效果 */
  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-border: rgba(255, 255, 255, 0.3);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);

  /* 动画曲线 */
  --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
  --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);

  /* 新拟态阴影 */
  --neumorphism-light: 8px 8px 16px #d1d9e6, -8px -8px 16px #ffffff;
  --neumorphism-dark: 8px 8px 16px #151515, -8px -8px 16px #1f1f1f;
}
```

#### 4.1.2 动画效果增强

| 场景 | 动画效果 | 实现方式 |
|-----|---------|---------|
| 页面切换 | 平滑淡入+轻微上滑 | Framer Motion |
| 数据加载 | 骨架屏脉冲动画 | CSS Animation |
| 卡片悬停 | 上浮+阴影增强 | CSS Transition |
| 通知提醒 | 滑入+弹性效果 | Framer Motion |
| 图表数据 | 渐进式绘制 | ECharts Animation |
| 协作光标 | 平滑跟随 | CSS Transform |
| AI生成 | 打字机效果 | React State |

#### 4.1.3 卡片式UI设计

```typescript
// 统一卡片组件
interface CardProps {
  variant: 'default' | 'glass' | 'neumorphism' | 'gradient';
  hoverable?: boolean;
  animated?: boolean;
  children: React.ReactNode;
}

// 使用示例
<Card variant="glass" hoverable animated>
  <CardHeader>
    <IconWrapper gradient><FileTextOutlined /></IconWrapper>
    <CardTitle>论文标题</CardTitle>
  </CardHeader>
  <CardContent>{content}</CardContent>
  <CardFooter actions={actions} />
</Card>
```

#### 4.1.4 沉浸式阅读模式

```
┌─────────────────────────────────────────────────────────────┐
│  [退出沉浸]                                    [设置] [主题] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    论文标题                                 │
│                    ========                                 │
│                                                             │
│  摘要                                                       │
│  ─────────────────────────────────────────────────────     │
│  这是一段摘要内容，使用易读的字体和行高...                   │
│                                                             │
│  1. 引言                                                    │
│  ─────────────────────────────────────────────────────     │
│  近年来，随着人工智能技术的发展...                          │
│                                                             │
│                          ┌──────────────────────┐          │
│                          │  AI助手              │          │
│                          │  ┌────────────────┐  │          │
│                          │  │ 这段话可以     │  │          │
│                          │  │ 进一步展开...  │  │          │
│                          │  └────────────────┘  │          │
│                          │  [语音输入] [发送]   │          │
│                          └──────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 数据可视化优化

#### 4.2.1 学术影响力仪表盘

```typescript
// 影响力指标可视化
interface ImpactMetrics {
  citationCount: number;      // 引用次数
  hIndex: number;             // H指数
  i10Index: number;           // i10指数
  citationVelocity: number;   // 引用速度
  fieldCitationRatio: number; // 领域引用比

  // 可视化组件
  citationTrend: LineChartData;      // 引用趋势图
  fieldDistribution: PieChartData;   // 领域分布
  coauthorNetwork: GraphData;        // 合作者网络
  paperTimeline: TimelineData;       // 论文时间轴
}
```

**可视化效果**：
- 引用趋势：动态折线图，显示逐年引用变化
- 影响力雷达图：多维度展示学术影响力
- 合作网络：力导向图，显示合作关系强度

#### 4.2.2 文献关系网络图

```typescript
// 使用 ECharts Graph + Force Layout
interface LiteratureNetwork {
  nodes: {
    id: string;
    name: string;
    category: 'core' | 'citation' | 'reference' | 'similar';
    value: number;  // 引用次数
    symbolSize: number;
  }[];
  edges: {
    source: string;
    target: string;
    value: number;  // 关系强度
    relation: 'cite' | 'similar' | 'coauthor';
  }[];
}
```

**交互功能**：
- 鼠标悬停显示详情
- 点击聚焦相关文献
- 拖拽调整布局
- 缩放和平移
- 聚类着色

#### 4.2.3 写作热力图 (GitHub风格)

```typescript
// 写作活动热力图
interface WritingActivity {
  date: string;      // 日期
  wordCount: number; // 字数
  duration: number;  // 时长
  sections: string[];// 编辑的章节
}

// 可视化参数
const heatmapConfig = {
  colors: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'],
  cellSize: 12,
  cellGap: 2,
  weeks: 52,
};
```

**展示维度**：
- 写作频率热力图
- 章节完成进度条
- 字数统计仪表盘
- 活跃时段分析

#### 4.2.4 证据矩阵可视化

```typescript
interface EvidenceMatrix {
  papers: PaperSummary[];
  criteria: {
    name: string;
    type: 'outcome' | 'method' | 'population' | 'effect';
    values: string[];
  }[];
  consensus: {
    supports: number;
    opposes: number;
    neutral: number;
    score: number;  // -1 to 1
  };
}
```

**可视化组件**：
- 矩阵热力图：论文×特征的交叉分析
- 共识度仪表盘：支持/反对/中性比例
- 效应量森林图：研究结果的元分析

#### 4.2.5 研究趋势时间轴

```typescript
interface TrendTimeline {
  events: {
    date: string;
    type: 'paper' | 'citation' | 'method' | 'trend';
    title: string;
    impact: number;
    relatedPapers: string[];
  }[];
  trends: {
    keyword: string;
    timeline: { date: string; count: number }[];
  }[];
}
```

**可视化效果**：
- 垂直时间轴布局
- 热度曲线叠加
- 关键事件标注
- 趋势预测虚线

---

## 第五部分：后续开发路线图

### 5.1 优先级矩阵

| 功能 | 用户价值 | 技术难度 | 实施成本 | 优先级 |
|-----|---------|---------|---------|--------|
| 语音驱动写作 | 高 | 中 | 低 | P0 |
| 智能文献阅读 | 高 | 中 | 中 | P0 |
| 多模态知识图谱 | 高 | 高 | 高 | P1 |
| AI虚拟导师 | 高 | 高 | 中 | P1 |
| 视频摘要生成 | 中 | 高 | 高 | P2 |
| 研究趋势预测 | 中 | 高 | 中 | P2 |
| 界面动画优化 | 中 | 低 | 低 | P1 |
| 可视化增强 | 中 | 中 | 中 | P1 |

### 5.2 阶段规划

#### Phase 9: AI原生体验强化 (Q2 2024)

**目标**：打造AI原生写作体验

**核心功能**：
1. **语音驱动写作** (step-asr + step-1-128k + step-tts)
   - 语音输入实时转录
   - 口语化转学术化
   - 语音指令控制
   - 预计工期：2周

2. **智能文献阅读** (step-1o + step-1-128k)
   - 多模态文献解析
   - 对话式问答
   - 关键信息提取
   - 预计工期：3周

3. **界面动画升级**
   - 全局动画系统
   - 卡片交互优化
   - 加载状态美化
   - 预计工期：1周

#### Phase 10: 多模态能力扩展 (Q3 2024)

**目标**：支持多模态内容理解与生成

**核心功能**：
1. **多模态知识图谱** (step-1o + Neo4j)
   - 图表内容理解
   - 图像检索文献
   - 3D可视化展示
   - 预计工期：4周

2. **图表智能生成** (step-1v)
   - 数据到图表生成
   - 图表美化建议
   - 图表描述生成
   - 预计工期：2周

3. **AI虚拟导师V2** (step-video可选)
   - 个性化导师配置
   - 视频对话模式
   - 深度论文审阅
   - 预计工期：3周

#### Phase 11: 视频与预测能力 (Q4 2024)

**目标**：支持视频内容生成和研究洞察

**核心功能**：
1. **视频摘要生成** (step-video + step-tts)
   - 论文介绍视频
   - 方法演示视频
   - 会议报告预演
   - 预计工期：4周

2. **研究趋势预测** (step-1-256k)
   - 趋势分析算法
   - 研究空白识别
   - 风险预警系统
   - 预计工期：3周

3. **数据可视化增强**
   - 影响力仪表盘
   - 证据矩阵可视化
   - 写作热力图增强
   - 预计工期：2周

### 5.3 技术实施计划

#### 模型接入

```python
# StepFun 多模型统一接口
class StepFunMultiModal:
    """
    阶跃多模型统一调用接口
    """

    async def generate_text(
        self,
        prompt: str,
        model: str = "step-1-128k",
        temperature: float = 0.7
    ) -> str:
        """文本生成"""
        pass

    async def recognize_speech(
        self,
        audio: bytes,
        language: str = "zh"
    ) -> str:
        """语音识别 (step-asr)"""
        pass

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "default"
    ) -> bytes:
        """语音合成 (step-tts)"""
        pass

    async def analyze_image(
        self,
        image: bytes,
        prompt: str
    ) -> dict:
        """图像分析 (step-1o)"""
        pass

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024"
    ) -> bytes:
        """图像生成 (step-1v)"""
        pass

    async def generate_video(
        self,
        prompt: str,
        duration: int = 5
    ) -> bytes:
        """视频生成 (step-video)"""
        pass
```

#### 前端架构调整

```typescript
// 新增模块
src/
├── components/
│   ├── voice/           # 语音交互组件
│   │   ├── VoiceInput.tsx
│   │   ├── VoicePlayer.tsx
│   │   └── VoiceCommandPanel.tsx
│   │
│   ├── video/           # 视频生成组件
│   │   ├── VideoGenerator.tsx
│   │   ├── VideoPlayer.tsx
│   │   └── VideoTemplateSelector.tsx
│   │
│   └── visualization/   # 数据可视化
│       ├── CitationNetwork.tsx
│       ├── ImpactDashboard.tsx
│       ├── WritingHeatmap.tsx
│       └── EvidenceMatrixViz.tsx
│
├── hooks/
│   ├── useSpeechRecognition.ts   # 语音识别Hook
│   ├── useSpeechSynthesis.ts     # 语音合成Hook
│   └── useVideoGeneration.ts     # 视频生成Hook
│
└── services/
    └── stepfunService.ts         # 阶跃服务客户端
```

### 5.4 资源配置

#### 模型成本估算（月度）

| 模型 | 预计调用量 | 单价 | 月成本 |
|-----|-----------|------|-------|
| step-1-32k | 100K | ¥0.015/1K tokens | ¥1,500 |
| step-1-128k | 50K | ¥0.06/1K tokens | ¥3,000 |
| step-1-256k | 10K | ¥0.12/1K tokens | ¥1,200 |
| step-asr | 5K小时 | ¥0.5/小时 | ¥2,500 |
| step-tts | 2K小时 | ¥0.8/小时 | ¥1,600 |
| step-1o | 20K | ¥0.08/次 | ¥1,600 |
| step-1v | 5K | ¥0.1/次 | ¥500 |
| step-video | 500 | ¥2/次 | ¥1,000 |
| **总计** | - | - | **¥12,900/月** |

#### 开发团队配置

| 角色 | 人数 | 职责 |
|-----|------|------|
| AI工程师 | 2 | 模型集成、Prompt工程 |
| 前端工程师 | 2 | UI实现、可视化 |
| 后端工程师 | 1 | API开发、数据处理 |
| 设计师 | 1 | UI/UX设计、动效设计 |
| **总计** | **6人** | - |

#### 时间线

```
Phase 9  (6周)
├── Week 1-2: 语音驱动写作
├── Week 3-5: 智能文献阅读
└── Week 6: 界面优化

Phase 10 (9周)
├── Week 1-4: 多模态知识图谱
├── Week 5-6: 图表智能生成
└── Week 7-9: AI虚拟导师V2

Phase 11 (9周)
├── Week 1-4: 视频摘要生成
├── Week 5-7: 研究趋势预测
└── Week 8-9: 可视化增强

总计: 24周 (约6个月)
```

---

## 附录：StepFun API 配置示例

```python
# backend/services/ai/stepfun_config.py

STEPFUN_MODELS = {
    # 文本模型
    "step-1-32k": {
        "max_tokens": 32000,
        "temperature_range": [0, 2],
        "use_case": ["常规写作", "快速问答"],
        "cost_per_1k": 0.015
    },
    "step-1-128k": {
        "max_tokens": 128000,
        "temperature_range": [0, 2],
        "use_case": ["长论文分析", "综述生成"],
        "cost_per_1k": 0.06
    },
    "step-1-256k": {
        "max_tokens": 256000,
        "temperature_range": [0, 2],
        "use_case": ["全书分析", "大规模文献"],
        "cost_per_1k": 0.12
    },

    # 多模态模型
    "step-1o": {
        "supports_vision": True,
        "max_tokens": 32000,
        "use_case": ["图表分析", "图文理解"],
        "cost_per_call": 0.08
    },
    "step-1v": {
        "supports_generation": True,
        "output_type": ["image"],
        "use_case": ["图表生成", "示意图"],
        "cost_per_call": 0.10
    },

    # 语音模型
    "step-asr": {
        "type": "speech-to-text",
        "languages": ["zh", "en"],
        "use_case": ["语音输入", "会议转录"],
        "cost_per_hour": 0.5
    },
    "step-tts": {
        "type": "text-to-speech",
        "voices": ["xiaosi", "xiaoyan"],
        "use_case": ["语音播报", "朗读"],
        "cost_per_hour": 0.8
    },

    # 视频模型
    "step-video": {
        "max_duration": 60,
        "resolution": "720p",
        "use_case": ["演示视频", "教学视频"],
        "cost_per_call": 2.0
    }
}

# 场景-模型映射
SCENARIO_MODEL_MAP = {
    "writing_continuation": "step-1-128k",
    "quick_polish": "step-1-32k",
    "literature_review": "step-1-256k",
    "chart_analysis": "step-1o",
    "chart_generation": "step-1v",
    "voice_input": "step-asr",
    "voice_output": "step-tts",
    "video_abstract": "step-video",
    "logic_check": "step-1-128k",
    "multi_hop_qa": "step-1-128k"
}
```

---

**报告生成时间**: 2026-03-06
**版本**: v1.0
**状态**: 审核完成，规划已制定
