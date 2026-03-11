# ScholarForge 详细开发规划

> 项目当前阶段：Phase 2 - 核心功能扩展
> 最后更新：2026-03-03

---

## 一、项目现状分析

### 1.1 已完成功能清单

| 模块 | 完成度 | 状态 |
|------|--------|------|
| 基础设施 | 100% | ✅ 完成 |
| 用户认证服务 | 100% | ✅ 完成 |
| 论文管理服务 | 95% | ✅ 完成（除实时协作后端） |
| 文献检索服务 | 95% | ✅ 完成（除实际API对接） |
| 智能推荐服务 | 100% | ✅ 完成 |
| AI写作助手 | 85% | ✅ 完成 |
| 前端界面 | 95% | ✅ 完成 |
| 错误处理与用户体验 | 100% | ✅ 完成 |

### 1.2 Phase 2 已完成功能

| 服务 | 完成度 | 状态 | 说明 |
|------|--------|------|------|
| topic（选题助手） | 100% | ✅ 完成 | 含AI选题建议、可行性分析 |
| progress（进度管理） | 100% | ✅ 完成 | 含甘特图、任务管理 |
| journal（期刊匹配） | 100% | ✅ 完成 | 含智能匹配算法 |
| knowledge（知识图谱） | 100% | ✅ 完成 | 含Neo4j图数据库支持 |
| reference（参考文献） | 100% | ✅ 完成 | 含多格式导入、引文生成 |
| plagiarism（查重检测） | 100% | ✅ 完成 | 含多引擎支持 |
| format（格式排版） | 100% | ✅ 完成 | 含模板系统 |
| defense（答辩准备） | 100% | ✅ 完成 | 含PPT生成、模拟答辩 |

### 1.3 待开始/剩余任务

| 模块 | 优先级 | 复杂度 | 说明 |
|------|--------|--------|------|
| 系统集成优化 | P0 | 中 | API网关、缓存、性能优化 |
| 端到端测试 | P0 | 中 | 完整功能测试 |
| 文献深度分析 | P1 | 高 | AI文献综述生成 |
| 学术规范检查 | P2 | 中 | 语法、格式规范 |
| 同行评审模拟 | P2 | 高 | AI模拟审稿 |
| 审稿意见分析 | P2 | 高 | 审稿意见智能解析 |

---

## 二、开发阶段规划

### Phase 2.1：研究准备阶段（第1-2周）

**目标**：完成选题助手、进度管理、期刊匹配、知识图谱的后端API实现和前端集成

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|----------|------|
| 2.1.1 选题助手服务完善 | P0 | 2天 | 无 |
| 2.1.2 进度管理服务完善 | P0 | 2天 | 无 |
| 2.1.3 期刊匹配服务完善 | P0 | 2天 | 无 |
| 2.1.4 知识图谱服务完善 | P1 | 3天 | 无 |
| 2.1.5 前端页面开发（Topic/Progress/Journal/Knowledge） | P0 | 4天 | 以上任务 |

**交付物**：
- 完整的选题助手功能（选题建议、可行性分析、开题报告生成、趋势分析）
- 进度管理系统（里程碑、任务、甘特图、预警）
- 期刊智能匹配（期刊数据库、匹配算法、投稿管理）
- 知识图谱构建与可视化

### Phase 2.2：文献深度增强（第3-4周）

**目标**：实现文献深度分析、参考文献管理

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|----------|------|
| 2.2.1 文献深度分析API | P1 | 3天 | 无 |
| 2.2.2 参考文献管理服务 | P0 | 3天 | 无 |
| 2.2.3 Zotero/EndNote导入功能 | P1 | 2天 | 2.2.2 |
| 2.2.4 文献引用格式转换 | P1 | 2天 | 2.2.2 |
| 2.2.5 前端文献分析页面 | P1 | 2天 | 以上任务 |

**交付物**：
- AI文献摘要与关键观点提取
- 参考文献自动管理
- 多格式引用导入导出

### Phase 2.3：质量保障与排版（第5-6周）

**目标**：实现查重对接、一键排版、学术规范检查

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|----------|------|
| 2.3.1 查重检测服务对接 | P1 | 2天 | 无 |
| 2.3.2 一键排版引擎 | P0 | 4天 | 无 |
| 2.3.3 学术规范检查 | P1 | 2天 | 无 |
| 2.3.4 前端质量保障页面 | P1 | 2天 | 以上任务 |

**交付物**：
- 第三方查重API对接
- Word/PDF一键排版
- 学术规范自动检查

### Phase 2.4：投稿与答辩（第7-8周）

**目标**：完成投稿管理和答辩准备功能

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|----------|------|
| 2.4.1 期刊匹配算法优化 | P1 | 2天 | 无 |
| 2.4.2 投稿材料准备 | P1 | 2天 | 无 |
| 2.4.3 答辩准备助手 | P1 | 3天 | 无 |
| 2.4.4 前端页面完善 | P1 | 2天 | 以上任务 |

**交付物**：
- 投稿材料自动生成
- 答辩PPT模板与生成
- 常见问题库与回答建议

### Phase 2.5：系统集成与优化（第9-10周）

**目标**：数据库持久化、性能优化、系统集成测试

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|----------|------|
| 2.5.1 所有服务数据库持久化 | P0 | 5天 | Phase 2.1-2.4 |
| 2.5.2 缓存层实现（Redis） | P1 | 2天 | 2.5.1 |
| 2.5.3 性能优化 | P1 | 2天 | 2.5.1 |
| 2.5.4 集成测试 | P0 | 3天 | 2.5.1 |

---

## 三、详细设计文档

### 3.1 选题助手服务（Topic Service）

**功能模块**：
1. 选题建议生成
2. 可行性分析
3. 开题报告生成
4. 趋势分析
5. 研究计划生成

**数据库表**：
```sql
-- 选题记录表
CREATE TABLE topic_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    field VARCHAR(100),
    keywords TEXT[],
    feasibility_score INTEGER,
    feasibility_level VARCHAR(20),
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 开题报告表
CREATE TABLE proposal_outlines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    topic_id UUID REFERENCES topic_suggestions(id),
    title VARCHAR(500),
    background TEXT,
    objectives TEXT,
    methods JSONB,
    timeline JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**API端点**：
- `POST /api/v1/topics/suggest` - 获取选题建议
- `POST /api/v1/topics/analyze/{topic_id}` - 深度可行性分析
- `POST /api/v1/topics/proposal/generate` - 生成开题报告
- `GET /api/v1/topics/trends` - 研究趋势分析
- `POST /api/v1/topics/plan/generate` - 生成研究计划

### 3.2 进度管理服务（Progress Service）

**功能模块**：
1. 里程碑管理
2. 任务管理
3. 甘特图生成
4. 预警系统
5. 进度报告

**数据库表**：
```sql
-- 里程碑表
CREATE TABLE milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    planned_date DATE,
    actual_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    completion_percentage INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 任务表
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id),
    milestone_id UUID REFERENCES milestones(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    progress INTEGER DEFAULT 0,
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,
    assignee_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 预警记录表
CREATE TABLE progress_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id),
    alert_type VARCHAR(50),
    severity VARCHAR(20),
    title VARCHAR(200),
    description TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 期刊匹配服务（Journal Service）

**功能模块**：
1. 期刊数据库管理
2. 智能匹配算法
3. 投稿记录管理
4. 期刊对比分析

**数据库表**：
```sql
-- 期刊数据表（已有基础，需完善）
-- 投稿记录表（已有基础，需完善）
-- 匹配历史表
CREATE TABLE journal_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    paper_id UUID REFERENCES papers(id),
    journal_id UUID REFERENCES journals(id),
    match_score DECIMAL(5,2),
    match_reasons JSONB,
    estimated_acceptance_rate DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4 知识图谱服务（Knowledge Service）

**功能模块**：
1. 图谱构建
2. 概念抽取
3. 路径查询
4. 研究脉络

**数据库设计（Neo4j）**：
```cypher
// 节点类型
(:Concept {name, type, importance})
(:Paper {title, year, citations})
(:Author {name, affiliation})
(:Method {name, category})

// 关系类型
(:Concept)-[:RELATED_TO {weight}]->(:Concept)
(:Paper)-[:CITES]->(:Paper)
(:Paper)-[:USES]->(:Method)
(:Author)-[:AUTHORED]->(:Paper)
```

### 3.5 参考文献管理服务（Reference Service）

**功能模块**：
1. 参考文献CRUD
2. 格式转换（GB/T 7714, APA, IEEE, MLA）
3. Zotero/EndNote导入
4. 引用完整性检查

**数据库表**：
```sql
-- 参考文献表（已有基础，需扩展）
-- 引用格式模板表
CREATE TABLE citation_styles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    style_code VARCHAR(50) UNIQUE NOT NULL, -- gb-t-7714-2015, apa-7th, etc.
    config JSONB NOT NULL, -- 格式配置
    is_builtin BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id)
);
```

### 3.6 排版引擎服务（Formatting Service）

**功能模块**：
1. 模板解析
2. 样式应用
3. 格式检查
4. 文档生成

**数据库表**：
```sql
-- 排版模板表（扩展已有模板表）
-- 格式规则表
CREATE TABLE format_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES paper_templates(id),
    rule_type VARCHAR(50), -- paragraph, heading, citation, etc.
    selector VARCHAR(200), -- CSS-like selector
    properties JSONB, -- 样式属性
    order_index INTEGER
);
```

---

## 四、技术实现要点

### 4.1 AI服务集成

所有AI功能统一通过 `ai` 服务调用LLM：

```python
# ai服务提供的统一接口
- POST /api/v1/ai/complete - 文本续写
- POST /api/v1/ai/polish - 文本润色
- POST /api/v1/ai/translate - 翻译
- POST /api/v1/ai/summarize - 摘要生成
- POST /api/v1/ai/extract - 关键信息提取
- POST /api/v1/ai/analyze-logic - 逻辑检查
- POST /api/v1/ai/recommend-references - 引用建议
```

### 4.2 缓存策略

| 数据类型 | 缓存策略 | TTL |
|----------|----------|-----|
| 用户会话 | Redis | 24h |
| 文献搜索结果 | Redis | 1h |
| 推荐列表 | Redis | 30min |
| 期刊数据 | Redis + 本地 | 24h |
| AI生成内容 | Redis | 1h |
| 知识图谱 | Redis | 2h |

### 4.3 数据库访问模式

所有服务使用统一的数据库访问模式：

```python
# Repository Pattern
class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[Model]:
        ...

    async def create(self, data: dict) -> Model:
        ...

    async def update(self, id: UUID, data: dict) -> Model:
        ...

    async def delete(self, id: UUID) -> bool:
        ...
```

---

## 五、前端开发规划

### 5.1 新增页面

| 页面 | 路径 | 功能描述 |
|------|------|----------|
| 选题助手 | `/topic` | 选题建议、可行性分析、开题报告 |
| 进度管理 | `/progress/:paperId` | 甘特图、里程碑、任务管理 |
| 期刊匹配 | `/journal-match` | 期刊推荐、投稿管理 |
| 知识图谱 | `/knowledge` | 图谱可视化、概念关系 |
| 参考文献 | `/references` | 文献管理、格式转换 |
| 质量检查 | `/quality` | 查重、格式检查、规范检查 |
| 答辩助手 | `/defense` | PPT生成、常见问题 |

### 5.2 组件开发

| 组件 | 用途 | 位置 |
|------|------|------|
| GanttChart | 甘特图展示 | components/charts/GanttChart.tsx |
| KnowledgeGraph | 知识图谱可视化 | components/knowledge/KnowledgeGraph.tsx |
| TopicCard | 选题建议卡片 | components/topic/TopicCard.tsx |
| JournalMatcher | 期刊匹配表单 | components/journal/JournalMatcher.tsx |
| ReferenceManager | 参考文献管理 | components/references/ReferenceManager.tsx |
| FormatChecker | 格式检查器 | components/quality/FormatChecker.tsx |

---

## 六、测试计划

### 6.1 单元测试

每个服务需要覆盖：
- API端点测试
- Repository层测试
- Service层测试
- 工具函数测试

### 6.2 集成测试

- 服务间调用测试
- 数据库操作测试
- 缓存操作测试
- AI服务调用测试

### 6.3 端到端测试

- 用户流程测试
- 论文写作全流程
- 协作编辑测试

---

## 七、风险与应对

| 风险 | 影响 | 概率 | 应对策略 |
|------|------|------|----------|
| AI服务成本过高 | 高 | 中 | 实现智能缓存，批量处理 |
| 数据库性能瓶颈 | 中 | 中 | 读写分离，分库分表 |
| 第三方API限制 | 高 | 高 | 多源备份，降级方案 |
| 开发进度延期 | 高 | 中 | 功能优先级调整，MVP优先 |

---

## 八、里程碑与验收标准

### Milestone 1: Phase 2.1 完成（第2周末）
- [ ] 选题助手功能完整可用
- [ ] 进度管理功能完整可用
- [ ] 期刊匹配功能完整可用
- [ ] 知识图谱基础功能可用

### Milestone 2: Phase 2.2-2.3 完成（第6周末）
- [ ] 文献深度分析功能
- [ ] 参考文献管理完整功能
- [ ] 一键排版引擎
- [ ] 查重检测对接

### Milestone 3: Phase 2.4-2.5 完成（第10周末）
- [ ] 答辩准备助手
- [ ] 所有功能数据库持久化
- [ ] 系统集成测试通过
- [ ] 性能优化完成

---

**文档版本**: v1.0
**制定日期**: 2026-03-03
**执行周期**: 10周
