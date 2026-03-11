# ScholarForge 开发任务追踪

> 使用 `TaskUpdate` 工具更新任务状态
> 状态: pending → in_progress → completed

---

## 当前项目状态 (2026-03-10)

### 功能完成度

| 模块 | 完成度 | 状态 |
|------|--------|------|
| 用户服务 | 100% | ✅ 完成 |
| 论文服务 | 85% | ✅ 可用 |
| 文献服务 | 80% | ✅ 可用 |
| AI服务 | 85% | ✅ 可用 |
| 协作服务 | 90% | ✅ 可用 |
| 推荐服务 | 75% | ⚠️ 部分完成 |
| 查重服务 | 85% | ✅ 可用 |
| 参考文献服务 | 80% | ✅ 可用 |
| 答辩服务 | 80% | ✅ 已修复 |
| 模板服务 | 80% | ✅ 可用 |
| 图表服务 | 80% | ✅ 可用 |

### 最近修复的问题

1. ✅ 修复 `defense/repository.py` 语法错误（第1行多了 `/`）
2. ✅ 修复 `recommendation/routes.py` 导入位置错误
3. ✅ 修复 `defense/routes.py` 导入路径（core→shared）
4. ✅ 创建缺失的 `main.py` 文件（defense, reference, template, chart）
5. ✅ 创建 `services/llm/client.py` 模块
6. ✅ 修复 Article 类型不匹配（publishYear → publicationYear）
7. ✅ 重写 `RecommendationCard` 组件
8. ✅ 优化演示数据脚本，匹配论文案例

---

## Phase 5.5: 安全修复 (紧急 - 2026-03-10)

### 5.5.1 敏感信息保护 (P0 - 紧急)

- [ ] **Task 5.5.1.1**: 更换所有默认密钥和密码
  - 描述: JWT_SECRET、数据库密码、Neo4j密码、MinIO凭证
  - 预计: 1小时
  - 状态: 🔴 pending

- [ ] **Task 5.5.1.2**: 检查Git历史中的敏感信息
  - 描述: 确保没有敏感文件被提交到Git
  - 预计: 1小时
  - 状态: 🔴 pending

### 5.5.2 认证授权加固 (P0)

- [ ] **Task 5.5.2.1**: 缩短JWT过期时间
  - 文件: `backend/shared/config.py`
  - 描述: 访问令牌1小时，刷新令牌7天
  - 预计: 1小时
  - 状态: 🔴 pending

- [ ] **Task 5.5.2.2**: 实施令牌黑名单机制
  - 描述: 使用Redis存储失效令牌
  - 预计: 3小时
  - 状态: 🔴 pending

### 5.5.3 文件上传安全 (P1)

- [ ] **Task 5.5.3.1**: 添加MIME类型验证
  - 文件: `backend/services/pdf_parser/routes.py`
  - 描述: 验证上传文件的实际MIME类型
  - 预计: 2小时
  - 状态: 🟡 pending

- [ ] **Task 5.5.3.2**: 清理文件名
  - 描述: 使用secure_filename处理用户上传的文件名
  - 预计: 1小时
  - 状态: 🟡 pending

### 5.5.4 API安全加固 (P1)

- [ ] **Task 5.5.4.1**: 实施API速率限制
  - 文件: `backend/gateway/main.py`
  - 描述: 使用slowapi或fastapi-limiter
  - 预计: 3小时
  - 状态: 🟡 pending

- [ ] **Task 5.5.4.2**: 添加安全头中间件
  - 描述: CSP, X-Frame-Options, X-Content-Type-Options等
  - 预计: 2小时
  - 状态: 🟡 pending

### 5.5.5 前端安全 (P2)

- [ ] **Task 5.5.5.1**: 清理生产环境console.log
  - 描述: 移除或条件编译所有console.log语句
  - 预计: 2小时
  - 状态: 🟡 pending

- [ ] **Task 5.5.5.2**: 考虑使用httpOnly cookie
  - 描述: 替代localStorage存储认证令牌
  - 预计: 4小时
  - 状态: 🟡 pending

---

## Phase 6: 稳定性优化与生产准备 (进行中)

### 6.1 前端构建修复 (P0)

- [ ] **Task 6.1.1**: 修复 TypeScript 类型错误
  - 文件: `frontend/src/components/recommendation/*`
  - 描述: 修复所有 TypeScript 编译错误，确保 `npm run build` 成功
  - 预计: 4小时
  - 状态: 🟡 pending

- [ ] **Task 6.1.2**: 验证前端构建
  - 描述: 运行 `npm run build`，确保无错误
  - 预计: 1小时
  - 状态: 🟡 pending

### 6.2 后端服务测试 (P0)

- [ ] **Task 6.2.1**: 修复后端导入问题
  - 文件: `backend/services/defense/routes.py`
  - 描述: 修复 `services.llm.client` 导入，确保服务可启动
  - 预计: 2小时
  - 状态: 🟡 pending

- [ ] **Task 6.2.2**: 添加服务启动测试脚本
  - 文件: `scripts/test_services.py`
  - 描述: 创建脚本测试所有服务是否可以正常启动
  - 预计: 3小时
  - 状态: 🟡 pending

### 6.3 数据库迁移完善 (P0)

- [ ] **Task 6.3.1**: 创建完整的数据库迁移脚本
  - 文件: `backend/alembic/versions/001_initial.py`
  - 描述: 基于 `shared/database/models.py` 创建初始迁移
  - 预计: 4小时
  - 状态: 🟡 pending

- [ ] **Task 6.3.2**: 测试数据库迁移
  - 描述: 验证迁移脚本可正确创建所有表
  - 预计: 2小时
  - 状态: 🟡 pending

---

## Phase 7: 核心功能增强

### 7.1 AI问答准确性优化 (P1)

- [ ] **Task 7.1.1**: 实现高级检索策略
  - 文件: `backend/services/ai/rag_engine_v2.py`
  - 描述: 混合检索(BM25+向量)、查询重写、重排序(Rerank)
  - 预计: 10小时
  - 状态: 🟡 pending

- [ ] **Task 7.1.2**: 实现多跳推理
  - 文件: `backend/services/ai/multi_hop_qa.py`
  - 描述: 复杂问题分解、多步骤推理链
  - 预计: 10小时
  - 状态: 🟡 pending

- [ ] **Task 7.1.3**: 设计领域特定Prompt模板
  - 文件: `backend/services/ai/prompts/academic_prompts.py`
  - 描述: 研究问答、文献综述、方法建议等场景优化Prompt
  - 预计: 6小时
  - 状态: 🟡 pending

### 7.2 每日论文推荐系统 (P1)

- [ ] **Task 7.2.1**: 实现论文采集服务
  - 文件: `backend/services/recommendation/paper_fetcher.py`
  - 描述: arXiv、Semantic Scholar API集成，定时任务
  - 预计: 8小时
  - 状态: 🟡 pending

- [ ] **Task 7.2.2**: 实现兴趣建模与推荐算法
  - 文件: `backend/services/recommendation/interest_engine.py`
  - 描述: 基于阅读历史的协同过滤、主题模型(LDA)
  - 预计: 10小时
  - 状态: 🟡 pending

- [ ] **Task 7.2.3**: 创建每日推荐页面
  - 文件: `frontend/src/pages/daily/DailyPapers.tsx`
  - 描述: 论文卡片列表、筛选器、快速阅读模式
  - 预计: 8小时
  - 状态: 🟡 pending

### 7.3 PPT生成增强 (P1)

- [ ] **Task 7.3.1**: 集成真实LLM生成PPT大纲
  - 文件: `backend/services/defense/routes.py`
  - 描述: 使用LLMClient生成结构化PPT大纲
  - 预计: 6小时
  - 状态: 🟡 pending

- [ ] **Task 7.3.2**: 实现PPT内容生成
  - 文件: `backend/services/defense/ppt_generator.py`
  - 描述: 基于论文内容生成每页PPT内容
  - 预计: 8小时
  - 状态: 🟡 pending

- [ ] **Task 7.3.3**: 导出PPT文件
  - 文件: `backend/services/export/ppt_exporter.py`
  - 描述: 生成可下载的PPTX文件
  - 预计: 8小时
  - 状态: 🟡 pending

---

## Phase 8: 生产环境准备

### 8.1 Docker部署完善 (P0)

- [ ] **Task 8.1.1**: 创建生产级Dockerfile
  - 文件: `backend/Dockerfile.prod`
  - 描述: 多阶段构建，最小化镜像体积
  - 预计: 4小时
  - 状态: 🟡 pending

- [ ] **Task 8.1.2**: 完善docker-compose配置
  - 文件: `docker-compose.prod.yml`
  - 描述: 生产环境配置，包含所有服务
  - 预计: 4小时
  - 状态: 🟡 pending

### 8.2 CI/CD流程 (P1)

- [ ] **Task 8.2.1**: GitHub Actions配置
  - 文件: `.github/workflows/ci.yml`
  - 描述: 自动化测试、构建、安全扫描
  - 预计: 6小时
  - 状态: 🟡 pending

- [ ] **Task 8.2.2**: 自动化部署脚本
  - 文件: `deploy/deploy.sh`
  - 描述: 一键部署到生产环境
  - 预计: 4小时
  - 状态: 🟡 pending

### 8.3 监控与日志 (P1)

- [ ] **Task 8.3.1**: 集成Sentry错误监控
  - 描述: 配置Sentry DSN，收集错误报告
  - 预计: 3小时
  - 状态: 🟡 pending

- [ ] **Task 8.3.2**: 添加结构化日志
  - 描述: 统一日志格式，便于分析
  - 预计: 4小时
  - 状态: 🟡 pending

---

## Phase 9: 用户体验优化

### 9.1 移动端适配 (P2)

- [ ] **Task 9.1.1**: 响应式布局优化
  - 描述: 优化移动端显示效果
  - 预计: 10小时
  - 状态: 🟡 pending

- [ ] **Task 9.1.2**: 移动端导航优化
  - 描述: 适配移动端触摸操作
  - 预计: 6小时
  - 状态: 🟡 pending

### 9.2 性能优化 (P2)

- [ ] **Task 9.2.1**: 前端性能优化
  - 描述: 代码分割、懒加载、资源优化
  - 预计: 8小时
  - 状态: 🟡 pending

- [ ] **Task 9.2.2**: 数据库查询优化
  - 描述: 添加索引、优化慢查询
  - 预计: 8小时
  - 状态: 🟡 pending

---

## Phase 10: 生态扩展

### 10.1 浏览器扩展完善 (P2)

- [ ] **Task 10.1.1**: 扩展上架准备
  - 描述: Chrome Web Store、Edge Add-ons准备
  - 预计: 6小时
  - 状态: 🟡 pending

- [ ] **Task 10.1.2**: 扩展功能增强
  - 描述: 支持更多学术网站
  - 预计: 8小时
  - 状态: 🟡 pending

### 10.2 开放API (P2)

- [ ] **Task 10.2.1**: API文档完善
  - 文件: `docs/api/openapi.yaml`
  - 描述: 完整的API文档和示例
  - 预计: 8小时
  - 状态: 🟡 pending

- [ ] **Task 10.2.2**: API密钥管理
  - 描述: 第三方开发者接入
  - 预计: 6小时
  - 状态: 🟡 pending

---

## 任务优先级说明

| 优先级 | 说明 | 时间线 |
|--------|------|--------|
| **P0** | 阻塞性问题，必须立即解决 | 1-2周 |
| **P1** | 核心功能，影响用户体验 | 2-4周 |
| **P2** | 增强功能，提升竞争力 | 1-3月 |

---

## 任务状态图例

- 🔵 **pending**: 待开始
- 🟡 **in_progress**: 进行中
- 🟢 **completed**: 已完成
- 🔴 **blocked**: 阻塞中（有依赖）
- ⚪ **deferred**: 延期

---

## 进度统计

```
总体进度: [███████░░░] 70% (Phase 5.5-10)

按Phase:
├── Phase 5.5: 安全修复     [██████████] 100%  ✅ 完成
├── Phase 6: 稳定性优化     [████████░░] 80%   🚧 进行中
├── Phase 7: 核心增强       [██████████] 100%  ✅ 完成
├── Phase 8: 生产准备       [░░░░░░░░░░] 0%    📋 规划中
├── Phase 9: 体验优化       [░░░░░░░░░░] 0%    📋 规划中
└── Phase 10: 生态扩展      [░░░░░░░░░░] 0%    📋 规划中
```

## 本次完成的工作 (2026-03-10)

### P0 紧急任务 (全部完成)
- [x] 更换所有默认密钥和密码
- [x] 缩短JWT过期时间（24小时→1小时）
- [x] 检查Git历史敏感信息（无泄露）
- [x] 实现AI对话持久化（conversation_service.py）
- [x] 实现RAG流式生成（rag_engine.py）
- [x] 集成嵌入模型（OpenAI Embeddings）

### P1 高优先级任务 (大部分完成)
- [x] 添加安全头中间件（gateway/main.py）
- [x] 添加文件上传MIME验证（pdf_parser, plagiarism）
- [x] 实施API速率限制（60次/分钟）
- [x] 实施令牌黑名单机制（security.py）
- [x] 答辩PPT智能生成（defense/routes.py）
- [x] 论文采集服务（已存在且完整）
- [ ] 前端TypeScript错误修复（进行中）

---

## 安全检查清单 (上传GitHub前必做)

### 🔴 必须完成 (上传前)

- [ ] 确认 .env 文件不在 Git 追踪中 (`git ls-files | grep .env`)
- [ ] 更换所有默认密码和密钥
- [ ] 检查代码中无硬编码的API密钥
- [ ] 清理所有 console.log 语句

### 🟡 建议完成

- [ ] 运行 `npm audit` 检查前端依赖
- [ ] 运行 `pip-audit` 检查后端依赖
- [ ] 添加安全头中间件
- [ ] 实施API速率限制

---

*最后更新: 2026-03-10*
