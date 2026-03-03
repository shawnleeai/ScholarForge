# ScholarForge API 规范

## API 设计原则

1. **RESTful 风格**：遵循 REST 架构风格，资源命名清晰
2. **版本控制**：通过 URL 路径 `/api/v1/` 进行版本管理
3. **统一响应**：标准化响应格式，包含状态码、数据和错误信息
4. **认证授权**：JWT Token 认证，RBAC 权限控制

## 基础信息

- **Base URL**: `https://api.scholarforge.cn/api/v1`
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`

## 统一响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "Success",
  "data": { ... },
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "Validation Error",
  "errors": [
    {"field": "email", "message": "Invalid email format"}
  ],
  "timestamp": "2026-02-28T12:00:00Z"
}
```

## 认证接口

### 用户注册
```
POST /auth/register
```

**请求体**:
```json
{
  "email": "user@example.com",
  "username": "researcher",
  "password": "SecurePass123!",
  "full_name": "张三",
  "university": "浙江大学",
  "major": "工程管理"
}
```

### 用户登录
```
POST /auth/login
```

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 86400
  }
}
```

### 刷新Token
```
POST /auth/refresh
```

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

## 用户接口

### 获取当前用户信息
```
GET /users/me
Authorization: Bearer {token}
```

### 更新用户信息
```
PUT /users/me
Authorization: Bearer {token}
```

### 获取用户画像
```
GET /users/me/profile
Authorization: Bearer {token}
```

## 论文接口

### 创建论文
```
POST /papers
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "title": "AI协同项目管理研究",
  "paper_type": "thesis",
  "template_id": "uuid-of-template",
  "team_id": "uuid-of-team"
}
```

### 获取论文列表
```
GET /papers?page=1&limit=20&status=draft
Authorization: Bearer {token}
```

### 获取论文详情
```
GET /papers/{paper_id}
Authorization: Bearer {token}
```

### 更新论文章节
```
PUT /papers/{paper_id}/sections/{section_id}
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "title": "第一章 绪论",
  "content": "## 1.1 研究背景\n...",
  "order_index": 1
}
```

### 添加协作者
```
POST /papers/{paper_id}/collaborators
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "user_email": "collaborator@example.com",
  "role": "editor",
  "can_edit": true,
  "can_comment": true
}
```

## 文献接口

### 搜索文献
```
GET /articles/search?query=AI+project+management&sources=cnki,wos&year_from=2020
Authorization: Bearer {token}
```

### 获取文献详情
```
GET /articles/{article_id}
Authorization: Bearer {token}
```

### 添加到个人文献库
```
POST /users/me/library
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "article_id": "uuid-of-article",
  "folder_id": "uuid-of-folder",
  "tags": ["重要", "方法论"],
  "notes": "核心参考文献"
}
```

### 获取文献推荐
```
GET /recommendations/daily?limit=5
Authorization: Bearer {token}
```

## AI 接口

### 写作助手 - 续写
```
POST /ai/writing/continue
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "paper_id": "uuid-of-paper",
  "section_id": "uuid-of-section",
  "context": "前文内容...",
  "max_tokens": 500
}
```

### 写作助手 - 润色
```
POST /ai/writing/polish
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "text": "这段文字需要润色...",
  "style": "academic",
  "language": "zh"
}
```

### 图表生成
```
POST /ai/charts/generate
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "data": [...],
  "chart_type": "bar",
  "title": "实验结果对比",
  "options": {}
}
```

## 协作接口

### WebSocket 连接
```
WS /collab/{paper_id}?token={jwt_token}
```

### 获取批注列表
```
GET /papers/{paper_id}/annotations
Authorization: Bearer {token}
```

### 创建批注
```
POST /papers/{paper_id}/annotations
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "section_id": "uuid-of-section",
  "annotation_type": "comment",
  "content": "这段论述需要补充参考文献",
  "position": {
    "start_offset": 100,
    "end_offset": 150
  }
}
```

### 解决批注
```
PUT /papers/{paper_id}/annotations/{annotation_id}/resolve
Authorization: Bearer {token}
```

## 知识图谱接口

### 获取概念网络
```
GET /knowledge-graph/concepts/{concept_id}/network?depth=2
Authorization: Bearer {token}
```

### 搜索概念
```
GET /knowledge-graph/concepts/search?query=项目管理
Authorization: Bearer {token}
```

### 获取研究脉络
```
GET /knowledge-graph/research-lines?concept=AI
Authorization: Bearer {token}
```

## 期刊接口

### 搜索期刊
```
GET /journals/search?subject=engineering&impact_factor_min=2.0
Authorization: Bearer {token}
```

### 期刊匹配推荐
```
POST /journals/match
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "paper_id": "uuid-of-paper",
  "preferences": {
    "open_access": false,
    "max_review_days": 90
  }
}
```

## 错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 无内容（删除成功）|
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 验证失败 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 速率限制

| 接口类型 | 限制 |
|----------|------|
| 普通接口 | 100次/分钟 |
| AI接口 | 50次/分钟 |
| 搜索接口 | 60次/分钟 |

## Webhook

### 支持的事件
- `paper.created` - 论文创建
- `paper.updated` - 论文更新
- `annotation.created` - 批注创建
- `recommendation.ready` - 推荐生成完成
- `submission.status_changed` - 投稿状态变更
