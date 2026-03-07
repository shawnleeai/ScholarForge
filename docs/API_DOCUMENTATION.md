# ScholarForge API 文档

## 概述

ScholarForge API 采用 RESTful 设计，基于 FastAPI 构建。

**基础 URL**: `http://localhost:8000/api/v1`

**文档地址**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 认证

所有 API 请求（除登录注册外）需要在 Header 中包含 JWT Token：

```
Authorization: Bearer <access_token>
```

## 核心端点

### 认证

#### POST /auth/register
用户注册

**请求体**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePass123!",
  "full_name": "Full Name"
}
```

**响应**:
```json
{
  "code": 201,
  "message": "注册成功",
  "data": {
    "user": { ... },
    "token": {
      "access_token": "...",
      "refresh_token": "...",
      "token_type": "Bearer",
      "expires_in": 604800
    }
  }
}
```

#### POST /auth/login
用户登录

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

### 论文

#### GET /papers
获取论文列表

**查询参数**:
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20)
- `status`: 状态过滤 (draft/review/published)

#### POST /papers
创建论文

**请求体**:
```json
{
  "title": "论文标题",
  "abstract": "摘要",
  "content": "内容",
  "keywords": ["关键词1", "关键词2"]
}
```

#### GET /papers/{paper_id}
获取论文详情

#### PUT /papers/{paper_id}
更新论文

#### DELETE /papers/{paper_id}
删除论文

### 文献

#### GET /articles/search
搜索文献

**查询参数**:
- `q`: 搜索关键词
- `source`: 来源 (arxiv/cnki/ieee/semantic_scholar)
- `year_from`: 起始年份
- `year_to`: 结束年份
- `limit`: 返回数量

### AI

#### POST /ai/writing
AI写作助手

**请求体**:
```json
{
  "task": "continue",
  "content": "当前内容",
  "context": "上下文"
}
```

#### POST /ai/chat
AI对话

**请求体**:
```json
{
  "message": "用户消息",
  "conversation_id": "会话ID"
}
```

## 错误码

| 码 | 含义 |
|-----|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 500 | 服务器内部错误 |

## 限流

API 限流策略：
- 认证用户：1000 请求/小时
- 未认证用户：100 请求/小时
