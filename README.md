# ScholarForge（学术锻造）

> **一站式智能学术研究协作平台**
> 锻造学术精品，成就研究梦想

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

## 📖 项目简介

ScholarForge（学术锻造）是一个面向全学科研究者的一站式智能学术研究协作平台，通过AI技术赋能学术研究全流程，提供从选题开题到投稿答辩的完整解决方案。

### 核心功能

- 🎯 **智能选题助手** - 数据驱动的选题决策支持，研究趋势分析
- 📚 **多源文献检索** - CNKI、Web of Science、IEEE、arXiv 等多数据库集成
- 🤖 **AI写作助手** - 基于大语言模型的智能写作辅助
- 📊 **图表自动生成** - 出版级数据可视化
- 👥 **多人实时协作** - 类 Google Docs 的协同编辑体验
- 📝 **导师批注系统** - 结构化指导反馈
- 📰 **期刊智能匹配** - 基于论文内容推荐适合投稿的期刊
- 🕸️ **知识图谱构建** - 研究领域知识可视化
- 📑 **参考文献管理** - Zotero集成，自动格式化
- 🔍 **查重与格式检查** - 论文质量保障
- 🎤 **答辩准备助手** - PPT生成，常见问题预测

## 🏗️ 项目结构

```
ScholarForge/
├── frontend/                # React 前端应用
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   ├── services/       # API 服务
│   │   ├── stores/         # 状态管理
│   │   └── styles/         # 样式文件
│   ├── public/
│   └── package.json
├── backend/                 # Python FastAPI 后端服务
│   ├── services/           # 微服务模块
│   │   ├── user/          # 用户服务 (端口: 8001)
│   │   ├── paper/         # 论文服务 (端口: 8002)
│   │   ├── article/       # 文献服务 (端口: 8003)
│   │   ├── ai/            # AI 服务 (端口: 8004)
│   │   ├── collab/        # 协作服务 (端口: 8005)
│   │   └── recommend/     # 推荐服务 (端口: 8006)
│   ├── shared/            # 共享模块
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   └── models.py      # 数据模型
│   └── pyproject.toml
├── docs/                   # 文档
│   ├── database/          # 数据库设计
│   │   └── schema.sql
│   └── api/               # API 文档
├── deploy/                 # 部署配置
│   ├── docker/            # Docker 配置
│   └── kubernetes/        # K8s 配置
├── memory/                 # 项目记忆
├── PRD.md                  # 产品需求文档
├── 系统架构图.md            # 技术架构文档
├── 文献系统概念设计.md       # 文献推荐系统设计
├── docker-compose.yml      # Docker Compose 配置
├── .env.example            # 环境变量示例
├── .gitignore              # Git 忽略配置
└── LICENSE                 # MIT 许可证
```

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 16+
- Redis 7+
- Elasticsearch 8+
- Neo4j 5+
- MinIO

### 环境配置

```bash
# 1. 克隆项目
git clone https://github.com/your-org/scholarforge.git
cd scholarforge

# 2. 复制环境变量配置
cp .env.example .env

# 3. 编辑 .env 文件，填写必要的配置
# 注意：必须设置以下安全相关的环境变量：
# - JWT_SECRET (建议使用: openssl rand -hex 32)
# - MINIO_ACCESS_KEY
# - MINIO_SECRET_KEY
# - NEO4J_PASSWORD
```

### 使用 Docker Compose 启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

服务启动后：
- 前端访问：http://localhost:3000
- API 网关：http://localhost:8000
- Kong Admin：http://localhost:8001

### 本地开发模式

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -e ".[dev]"

# 启动各个服务
uvicorn services.user.main:app --reload --port 8001
uvicorn services.paper.main:app --reload --port 8002
# ... 其他服务
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📚 文档

- [产品需求文档 (PRD)](./PRD.md)
- [系统架构设计](./系统架构图.md)
- [文献推荐系统设计](./文献系统概念设计.md)
- [数据库模式设计](./docs/database/schema.sql)
- [API 规范](./docs/api/)
- [安全指南](./SECURITY.md)

## 🛠️ 技术栈

### 前端
- React 18 + TypeScript
- Vite (构建工具)
- Ant Design (UI 组件库)
- Zustand (状态管理)
- TanStack Query (数据获取)
- ECharts (数据可视化)
- Yjs + Hocuspocus (协同编辑)

### 后端
- Python 3.11
- FastAPI (Web 框架)
- SQLAlchemy 2.0 (ORM)
- Celery (任务队列)
- Pydantic (数据验证)

### 数据存储
- PostgreSQL (关系数据库)
- Redis (缓存 & 消息队列)
- Elasticsearch (全文搜索)
- Neo4j (知识图谱)
- MinIO (对象存储)

### AI 能力
- OpenAI GPT-4
- Anthropic Claude
- LangChain
- Sentence Transformers

### 基础设施
- Kong (API 网关)
- Docker & Docker Compose
- GitHub Actions (CI/CD)

## 📋 开发路线图

### Phase 1: 基础夯实 ✅
- [x] 产品规划与架构设计
- [x] 基础模块开发
- [x] Web 端 MVP

### Phase 2: 核心扩展 ✅
- [x] 选题助手与研究计划
- [x] 进度管理与甘特图
- [x] 期刊智能匹配
- [x] 知识图谱构建
- [x] AI 写作助手
- [x] 参考文献管理 (Zotero 集成)
- [x] 查重与格式检查
- [x] 答辩准备助手

### Phase 3: 平台化 🚧
- [ ] 开放 API
- [ ] 插件系统
- [ ] 移动端 App
- [ ] 机构版部署

## 🔐 安全说明

本项目重视数据安全和用户隐私：

- 所有敏感配置通过环境变量管理，**绝不硬编码在代码中**
- JWT 密钥、数据库密码等必须通过 `.env` 文件配置
- 请参阅 [SECURITY.md](./SECURITY.md) 了解安全配置最佳实践

**⚠️ 警告：在部署到生产环境前，请务必：**
1. 修改所有默认密码和密钥
2. 配置 HTTPS
3. 启用适当的防火墙规则
4. 定期更新依赖包

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📧 联系方式

- 项目主页：https://github.com/your-org/scholarforge
- 问题反馈：https://github.com/your-org/scholarforge/issues
- 邮箱：support@scholarforge.cn

---

**ScholarForge (学术锻造)** - 锻造学术精品，成就研究梦想
