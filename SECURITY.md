# 安全指南

本文档介绍 ScholarForge 的安全配置和最佳实践。

## 🔐 环境变量配置

ScholarForge 使用环境变量管理所有敏感配置。**切勿将敏感信息硬编码在代码中或提交到 Git 仓库。**

### 必需的安全环境变量

以下环境变量必须在 `.env` 文件中设置，且不能保留默认值：

```bash
# JWT 配置（必填）
# 使用强随机字符串，建议 32 位以上
# 生成命令: openssl rand -hex 32
JWT_SECRET=your-secure-random-jwt-secret-key

# MinIO 对象存储（必填）
MINIO_ACCESS_KEY=your-secure-access-key
MINIO_SECRET_KEY=your-secure-secret-key

# Neo4j 图数据库（必填）
NEO4J_PASSWORD=your-secure-neo4j-password
```

### 可选的外部 API 配置

以下 API 密钥为可选配置，用于增强平台功能：

```bash
# AI 服务
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 学术数据库
CNKI_API_KEY=...
WOS_API_KEY=...
IEEE_API_KEY=...
```

## 🛡️ 安全配置检查清单

在部署到生产环境前，请确认以下事项：

### 1. 环境变量检查
- [ ] 已创建 `.env` 文件（基于 `.env.example`）
- [ ] `JWT_SECRET` 已设置为强随机字符串
- [ ] `MINIO_ACCESS_KEY` 和 `MINIO_SECRET_KEY` 已修改
- [ ] `NEO4J_PASSWORD` 已修改
- [ ] 所有外部 API 密钥已配置（如需要）
- [ ] `.env` 文件已添加到 `.gitignore`

### 2. 网络安全
- [ ] 已配置 HTTPS（使用有效的 SSL 证书）
- [ ] Kong 网关已配置速率限制
- [ ] CORS 配置已限制为允许的域名
- [ ] 防火墙已配置，仅开放必要端口

### 3. 数据库安全
- [ ] PostgreSQL 已禁用默认用户
- [ ] Redis 已启用密码认证
- [ ] Elasticsearch 已配置安全设置
- [ ] Neo4j 已修改默认密码

### 4. 文件存储安全
- [ ] MinIO 已修改默认凭证
- [ ] 存储桶访问策略已正确配置
- [ ] 文件上传已限制类型和大小

## 🚨 安全事件响应

如果发现安全漏洞或数据泄露：

1. **立即更换密钥**：重置 JWT_SECRET 和所有相关密码
2. **检查日志**：审查访问日志，识别异常行为
3. **通知用户**：如涉及用户数据，及时通知受影响用户
4. **报告问题**：通过 GitHub Issues 报告安全问题

## 📝 安全更新

定期执行以下操作保持系统安全：

```bash
# 更新 Python 依赖
pip list --outdated
pip install --upgrade <package>

# 更新 Node.js 依赖
npm outdated
npm update

# 更新 Docker 镜像
docker-compose pull
docker-compose up -d
```

## 🔍 代码安全扫描

建议在 CI/CD 流程中集成安全扫描：

```bash
# Python 依赖漏洞扫描
pip install safety
safety check

# 密钥泄露检测
pip install detect-secrets
detect-secrets scan
```

## 📞 安全联系

如有安全相关问题，请通过以下方式联系：

- GitHub Issues: https://github.com/your-org/scholarforge/issues
- 邮箱: security@scholarforge.cn

**请勿在公开的 Issue 中披露敏感信息。**
