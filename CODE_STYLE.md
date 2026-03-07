# ScholarForge 代码风格指南

## Python 后端

### 工具
- **Linter**: Ruff
- **Formatter**: Ruff (format)
- **Type Checker**: MyPy

### 配置
配置在 `backend/pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
```

### 代码规范

#### 导入顺序
```python
# 1. 标准库
import os
import sys
from datetime import datetime
from typing import Optional

# 2. 第三方库
from fastapi import FastAPI
from sqlalchemy import Column

# 3. 本地模块
from shared.database import Base
from .models import User
```

#### 函数命名
```python
# 好的命名
def get_user_by_id(user_id: str) -> Optional[User]:
def create_paper(paper_data: PaperCreate) -> Paper:
async def search_articles(query: str) -> List[Article]:

# 避免的命名
def getUser(userId):  # 不使用驼峰
def foo(x):  # 太简短，不描述性
def do_something():  # 太模糊
```

#### 类型注解
```python
from typing import Optional, List, Dict, Any

# 参数和返回值都要有类型注解
def process_data(
    data: Dict[str, Any],
    options: Optional[Dict] = None
) -> List[str]:
    ...
```

## TypeScript 前端

### 工具
- **Linter**: ESLint
- **Formatter**: Prettier

### 配置
- ESLint: `frontend/.eslintrc.cjs`
- Prettier: `frontend/.prettierrc`

### 代码规范

#### 组件命名
```tsx
// 使用 PascalCase
const UserProfile: React.FC<UserProfileProps> = ({ user }) => {
  // ...
}

// 自定义 Hook 使用 camelCase 并以 use 开头
const useUserData = (userId: string) => {
  // ...
}
```

#### Props 接口
```tsx
interface ButtonProps {
  label: string
  onClick: () => void
  disabled?: boolean  // 可选属性
  variant?: 'primary' | 'secondary'  // 字面量类型
}

const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  disabled = false,
  variant = 'primary'
}) => {
  // ...
}
```

#### 导入顺序
```tsx
// 1. React 和第三方库
import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

// 2. 本地组件
import { Button } from '@/components/common/Button'

// 3. 服务和工具
import { userService } from '@/services/userService'
import { formatDate } from '@/utils/date'

// 4. 类型
import type { User } from '@/types/user'
```

## Git 提交规范

### 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式（不影响代码运行）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建过程或辅助工具的变动

### 示例
```
feat(auth): add JWT authentication

- Implement login/logout endpoints
- Add token refresh mechanism
- Add password hashing with bcrypt

Closes #123
```

## Pre-commit 钩子

### 安装
```bash
# 后端
cd backend
pip install pre-commit
pre-commit install

# 前端
cd frontend
npm install
```

### 手动运行
```bash
# 运行所有钩子
pre-commit run --all-files

# 运行特定钩子
pre-commit run ruff
```

## CI/CD 检查

### 自动检查
- 每次 PR 会自动运行 lint 检查
- 代码必须符合规范才能合并

### 本地检查
```bash
# 后端
cd backend
ruff check .
ruff format --check .
mypy .

# 前端
cd frontend
npm run lint
npx prettier --check "src/**/*.{ts,tsx}"
```
