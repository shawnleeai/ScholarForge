# GitHub 上传指南

本文档指导如何将 ScholarForge 项目安全地上传到 GitHub。

## ⚠️ 重要安全提醒

**上传前必须确认以下事项：**

1. ✅ 已检查所有代码中没有硬编码的 API 密钥、密码或敏感信息
2. ✅ `.env` 文件已添加到 `.gitignore` 且不会被提交
3. ✅ `.env.example` 已更新，包含所有必要的环境变量（但无真实值）

## 📋 文件清单检查

### 必需文件（已准备）
- [x] `README.md` - 项目介绍
- [x] `LICENSE` - MIT 许可证
- [x] `.gitignore` - Git 忽略规则
- [x] `.env.example` - 环境变量示例
- [x] `SECURITY.md` - 安全指南
- [x] `CONTRIBUTING.md` - 贡献指南
- [x] `.github/workflows/ci.yml` - CI/CD 配置

### 敏感文件检查状态
- [x] `backend/shared/config.py` - 已修复，无硬编码密钥
- [x] `backend/services/knowledge/neo4j_client.py` - 已修复，移除默认密码
- [x] `.env` - 存在但已被 .gitignore 排除

## 🚀 上传步骤

### 1. 初始化 Git 仓库（如尚未初始化）

```bash
cd /d/Github/coding/PaperAssistant

# 初始化仓库
git init

# 配置用户信息（如尚未配置）
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 2. 验证 .gitignore 生效

```bash
# 检查 .env 是否被忽略
git check-ignore -v .env

# 应该输出类似：.gitignore:5:.env	.env
# 表示 .env 被第 5 行的规则忽略
```

### 3. 添加文件到暂存区

```bash
# 添加所有文件（.gitignore 中排除的不会被添加）
git add .

# 验证没有添加敏感文件
git status

# 确保没有看到 .env 文件在待提交列表中
```

### 4. 提交代码

```bash
# 首次提交
git commit -m "Initial commit: ScholarForge v0.1.0

Phase 2 功能开发完成：
- 选题助手与研究计划
- 进度管理与甘特图
- 期刊智能匹配
- 知识图谱构建
- AI 写作助手
- 参考文献管理
- 查重与格式检查
- 答辩准备助手

包含完整的微服务架构、前端界面和文档。"
```

### 5. 推送到 GitHub

```bash
# 添加远程仓库（替换 your-username 为你的 GitHub 用户名）
git remote add origin https://github.com/your-username/scholarforge.git

# 推送到 main 分支
git push -u origin main
```

## 🔒 安全验证清单

上传后，在 GitHub 仓库页面验证：

- [ ] 仓库中不存在 `.env` 文件
- [ ] 所有密码字段都是占位符（如 `your-jwt-secret`）
- [ ] 没有真实的 API 密钥
- [ ] `SECURITY.md` 和 `CONTRIBUTING.md` 已上传

## 🐛 如意外泄露敏感信息

如果误将敏感信息提交到 GitHub：

1. **立即撤销密钥**：
   - 更换 JWT_SECRET
   - 更换 MinIO 密钥
   - 更换 Neo4j 密码
   - 撤销所有 API 密钥

2. **清理 Git 历史**：
   ```bash
   # 安装 git-filter-repo
   pip install git-filter-repo

   # 移除敏感文件
   git filter-repo --path .env --invert-paths

   # 强制推送
   git push origin main --force
   ```

3. **在 GitHub 上**：
   - 联系 GitHub 支持清除缓存
   - 检查 Security 标签页的告警

## 📚 上传后配置

### 启用分支保护
在 GitHub 仓库设置中：
1. Settings → Branches
2. 添加规则：要求 Pull Request 审查
3. 启用状态检查（CI 通过后才能合并）

### 配置 Secrets
在 GitHub 仓库中设置环境变量：
Settings → Secrets and variables → Actions

添加以下 secrets（用于 CI/CD）：
- `JWT_SECRET`
- `NEO4J_PASSWORD`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`

### 启用安全功能
1. Settings → Security → Code security
2. 启用 Dependabot 警报
3. 启用 Secret scanning

## ✅ 最终确认

执行以下命令确认一切就绪：

```bash
# 检查仓库大小
du -sh .git

# 检查文件数量
git ls-files | wc -l

# 检查最近的提交
git log --oneline -5

# 确认远程仓库
git remote -v
```

---

**项目现已准备好上传到 GitHub！**

如有任何问题，请参考 SECURITY.md 或联系项目维护者。
