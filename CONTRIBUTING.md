# 贡献指南

感谢您对 ScholarForge 项目的关注！我们欢迎各种形式的贡献。

## 🤝 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议：

1. 先搜索 [Issues](https://github.com/your-org/scholarforge/issues) 确认问题是否已被报告
2. 如果没有，创建新 Issue 并提供以下信息：
   - 问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（操作系统、浏览器版本等）
   - 相关截图或日志

### 提交代码

1. **Fork 仓库**
   ```bash
   git clone https://github.com/your-username/scholarforge.git
   cd scholarforge
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/issue-description
   ```

3. **开发规范**

   - **Python 后端**
     - 遵循 PEP 8 规范
     - 使用类型注解
     - 添加 docstring
     - 编写单元测试

   - **TypeScript 前端**
     - 使用 ESLint 和 Prettier
     - 编写类型定义
     - 组件使用函数式编程

4. **提交更改**
   ```bash
   git add .
   git commit -m "type: description"
   ```

   Commit 消息格式：
   - `feat:` 新功能
   - `fix:` 修复 bug
   - `docs:` 文档更新
   - `style:` 代码格式调整
   - `refactor:` 重构
   - `test:` 测试相关
   - `chore:` 构建/工具相关

5. **推送到 Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 填写 PR 描述模板
   - 关联相关 Issue
   - 确保 CI 检查通过

## 📋 开发流程

### 本地开发设置

```bash
# 1. 克隆并进入项目
git clone https://github.com/your-org/scholarforge.git
cd scholarforge

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写配置

# 3. 启动依赖服务
docker-compose up -d postgres redis elasticsearch neo4j minio

# 4. 启动后端（终端 1）
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
uvicorn services.user.main:app --reload --port 8001

# 5. 启动前端（终端 2）
cd frontend
npm install
npm run dev
```

### 代码审查

所有 PR 都需要：
- 至少 1 个维护者的审查批准
- CI 检查通过
- 无冲突
- 符合代码规范

## 📝 文档

- 更新功能时同步更新相关文档
- API 变更需要更新 API 文档
- 复杂功能添加使用说明

## 🎯 优先事项

我们特别需要帮助的领域：
- 测试覆盖率提升
- 性能优化
- 文档完善
- 多语言支持
- 移动端适配

## 💬 沟通交流

- GitHub Issues: 问题报告和功能讨论
- GitHub Discussions: 一般性讨论
- 邮箱: dev@scholarforge.cn

## ⚖️ 行为准则

- 尊重所有参与者
- 接受建设性批评
- 关注社区最佳利益
- 禁止任何形式的骚扰

## 📄 许可

提交 PR 即表示您同意您的贡献将采用 MIT 许可证。

---

如有疑问，欢迎随时联系维护团队！
