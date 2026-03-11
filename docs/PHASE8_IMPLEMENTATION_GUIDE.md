# Phase 8 实施指南：系统完善

## 概述
Phase 8 聚焦于系统级功能的完善，包括权限管理、消息通知、数据安全和性能优化。这是产品从 MVP 走向生产环境的关键阶段。

## 1. 用户权限系统 (RBAC)

### 1.1 数据模型设计

```python
# models/role.py
from sqlalchemy import Column, String, Integer, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# 角色-权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id')),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'))
)

# 用户-角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id')),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'))
)

class Role(Base):
    __tablename__ = 'roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    is_system = Column(Boolean, default=False)  # 系统内置角色不可删除

    permissions = relationship("Permission", secondary=role_permissions)

    # 预定义角色
    ROLES = {
        'super_admin': '超级管理员',
        'institution_admin': '机构管理员',
        'advisor': '导师',
        'student': '学生',
        'reviewer': '审稿人',
        'guest': '访客'
    }

class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource = Column(String(50), nullable=False)  # paper, team, dataset
    action = Column(String(50), nullable=False)    # create, read, update, delete, share
    description = Column(String(255))

    # 权限组合示例
    PERMISSIONS = {
        'paper:create': '创建论文',
        'paper:read': '查看论文',
        'paper:update': '编辑论文',
        'paper:delete': '删除论文',
        'paper:share': '分享论文',
        'team:manage': '管理团队',
        'ai:use': '使用AI功能',
        'export:pdf': '导出PDF',
    }
```

### 1.2 权限检查装饰器

```python
# services/permission/decorators.py
from functools import wraps
from fastapi import HTTPException, Depends
from starlette.status import HTTP_403_FORBIDDEN

def require_permission(resource: str, action: str):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            permission_code = f"{resource}:{action}"

            # 检查用户是否有权限
            has_perm = await permission_service.check_permission(
                user_id=current_user.id,
                permission_code=permission_code,
                resource_id=kwargs.get('resource_id')  # 用于资源级权限
            )

            if not has_perm:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission_code}"
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用示例
@app.post("/papers")
@require_permission("paper", "create")
async def create_paper(
    paper_data: PaperCreate,
    current_user: User = Depends(get_current_user)
):
    return await paper_service.create(paper_data, current_user.id)
```

### 1.3 资源级权限实现

```python
# services/permission/resource_permission.py
class ResourcePermissionService:
    """资源级权限服务"""

    async def check_paper_permission(
        self,
        user_id: UUID,
        paper_id: UUID,
        action: str
    ) -> bool:
        """检查论文权限"""

        # 1. 获取用户角色
        user_roles = await self.get_user_roles(user_id)

        # 2. 超级管理员直接通过
        if 'super_admin' in user_roles:
            return True

        # 3. 获取论文信息
        paper = await paper_service.get(paper_id)

        # 4. 论文所有者
        if paper.author_id == user_id:
            return True

        # 5. 协作者权限
        if action == 'read':
            collaborator = await collaboration_service.get_collaborator(
                paper_id, user_id
            )
            if collaborator:
                return True

        # 6. 导师权限
        if action in ['read', 'comment']:
            is_advisor = await team_service.is_user_advisor(
                user_id, paper.author_id
            )
            if is_advisor:
                return True

        return False
```

## 2. 消息通知系统

### 2.1 通知类型定义

```python
# models/notification.py
from enum import Enum

class NotificationType(str, Enum):
    # 论文相关
    PAPER_COMMENT = "paper_comment"           # 新批注
    PAPER_MENTION = "paper_mention"           # 被@提及
    PAPER_SHARED = "paper_shared"             # 论文被分享
    PAPER_APPROVED = "paper_approved"         # 论文通过审核

    # 协作相关
    COLLAB_INVITE = "collab_invite"           # 协作邀请
    COLLAB_JOINED = "collab_joined"           # 有人加入协作
    VERSION_UPDATED = "version_updated"       # 版本更新

    # AI 相关
    AI_SUGGESTION = "ai_suggestion"           # AI 建议
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"  # AI 分析完成

    # 系统相关
    SYSTEM_MAINTENANCE = "system_maintenance" # 系统维护
    SECURITY_ALERT = "security_alert"         # 安全提醒

class NotificationChannel(str, Enum):
    IN_APP = "in_app"      # 站内信
    EMAIL = "email"        # 邮件
    SMS = "sms"            # 短信
    WEB_PUSH = "web_push"  # 浏览器推送
```

### 2.2 通知服务实现

```python
# services/notification/notification_service.py
class NotificationService:
    def __init__(self):
        self.email_service = EmailService()
        self.push_service = WebPushService()
        self.ws_manager = WebSocketManager()

    async def send_notification(
        self,
        user_id: UUID,
        type: NotificationType,
        title: str,
        content: str,
        data: dict = None,
        channels: list[NotificationChannel] = None
    ):
        """发送多渠道通知"""

        # 1. 获取用户通知偏好
        preferences = await self.get_user_preferences(user_id)

        # 2. 保存通知记录
        notification = await self.create_notification(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            data=data
        )

        # 3. 站内信 (WebSocket)
        if NotificationChannel.IN_APP in channels:
            await self.ws_manager.send_to_user(user_id, {
                'type': 'notification',
                'data': {
                    'id': str(notification.id),
                    'type': type.value,
                    'title': title,
                    'content': content,
                    'created_at': notification.created_at.isoformat()
                }
            })

        # 4. 邮件通知
        if NotificationChannel.EMAIL in channels and preferences.email_enabled:
            await self.email_service.send_async(
                to=await self.get_user_email(user_id),
                subject=title,
                template='notification',
                context={'title': title, 'content': content, 'data': data}
            )

        # 5. 浏览器推送
        if NotificationChannel.WEB_PUSH in channels and preferences.push_enabled:
            await self.push_service.send(
                user_id=user_id,
                title=title,
                body=content[:100],
                icon='/logo.png',
                data=data
            )
```

### 2.3 WebSocket 实时推送

```python
# services/notification/websocket_manager.py
from fastapi import WebSocket
from typing import Dict, Set
import json

class WebSocketManager:
    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """建立 WebSocket 连接"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

        # 发送未读消息计数
        unread_count = await notification_service.get_unread_count(user_id)
        await websocket.send_json({
            'type': 'init',
            'unread_count': unread_count
        })

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

    async def send_to_user(self, user_id: str, message: dict):
        """向指定用户发送消息"""
        if user_id not in self.active_connections:
            return

        disconnected = set()
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)

        # 清理断开的连接
        for ws in disconnected:
            self.active_connections[user_id].discard(ws)
```

## 3. 数据安全与加密

### 3.1 论文内容加密

```python
# services/security/encryption_service.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionService:
    def __init__(self):
        self.master_key = os.environ.get('ENCRYPTION_MASTER_KEY')

    def derive_key(self, user_id: str, salt: bytes = None) -> tuple[bytes, bytes]:
        """从用户密码派生加密密钥"""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(
            f"{self.master_key}:{user_id}".encode()
        ))
        return key, salt

    def encrypt_content(self, content: str, user_id: str) -> dict:
        """加密论文内容"""
        key, salt = self.derive_key(user_id)
        f = Fernet(key)

        encrypted = f.encrypt(content.encode('utf-8'))

        return {
            'encrypted_content': base64.b64encode(encrypted).decode(),
            'salt': base64.b64encode(salt).decode(),
            'algorithm': 'AES-256-GCM',
            'version': 1
        }

    def decrypt_content(self, encrypted_data: dict, user_id: str) -> str:
        """解密论文内容"""
        salt = base64.b64decode(encrypted_data['salt'])
        key, _ = self.derive_key(user_id, salt)
        f = Fernet(key)

        encrypted = base64.b64decode(encrypted_data['encrypted_content'])
        decrypted = f.decrypt(encrypted)

        return decrypted.decode('utf-8')
```

### 3.2 审计日志中间件

```python
# middleware/audit_middleware.py
from fastapi import Request
import time
import json

class AuditMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        # 获取请求信息
        user_id = getattr(request.state, 'user_id', None)
        method = request.method
        path = request.url.path
        ip = request.client.host
        user_agent = request.headers.get('user-agent')

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        duration = time.time() - start_time

        # 记录审计日志
        audit_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': str(user_id) if user_id else None,
            'method': method,
            'path': path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'ip': ip,
            'user_agent': user_agent,
            'request_id': request.headers.get('x-request-id')
        }

        # 异步写入日志 (Kafka -> ClickHouse)
        await audit_service.log_async(audit_log)

        return response
```

### 3.3 自动备份策略

```python
# services/backup/backup_service.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class BackupService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.storage = S3Storage()  # 或 MinIO

    async def setup_scheduled_backups(self):
        """设置定时备份"""

        # 每日增量备份
        self.scheduler.add_job(
            self.incremental_backup,
            'cron',
            hour=2,  # 凌晨 2 点
            minute=0,
            id='daily_incremental'
        )

        # 每周全量备份
        self.scheduler.add_job(
            self.full_backup,
            'cron',
            day_of_week='sun',
            hour=3,
            minute=0,
            id='weekly_full'
        )

        self.scheduler.start()

    async def incremental_backup(self):
        """增量备份 - 只备份变化的数据"""
        last_backup = await self.get_last_backup_time()

        # 备份数据库变更
        changed_papers = await db.query(
            "SELECT * FROM papers WHERE updated_at > :last_backup",
            {"last_backup": last_backup}
        )

        for paper in changed_papers:
            backup_data = {
                'type': 'paper',
                'id': str(paper.id),
                'data': paper.to_dict(),
                'version': paper.version,
                'backed_up_at': datetime.utcnow().isoformat()
            }
            await self.storage.upload(
                f"backups/incremental/{datetime.now().strftime('%Y%m%d')}/{paper.id}.json",
                json.dumps(backup_data)
            )

    async def full_backup(self):
        """全量备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 数据库全量导出
        dump_file = await self.dump_database()
        await self.storage.upload(
            f"backups/full/{timestamp}/database.sql.gz",
            dump_file
        )

        # 文件存储备份
        await self.storage.sync_folder(
            source='/data/uploads',
            dest=f"backups/full/{timestamp}/uploads/"
        )
```

## 4. 性能优化实施

### 4.1 Redis 缓存集成

```python
# services/cache/redis_client.py
import redis.asyncio as redis
from functools import wraps
import pickle
import hashlib

class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=int(os.environ.get('REDIS_DB', 0)),
            decode_responses=True
        )

    async def get(self, key: str):
        """获取缓存"""
        data = await self.redis.get(key)
        if data:
            return pickle.loads(data)
        return None

    async def set(self, key: str, value, expire: int = 3600):
        """设置缓存"""
        data = pickle.dumps(value)
        await self.redis.setex(key, expire, data)

    async def delete(self, key: str):
        """删除缓存"""
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str):
        """按模式删除缓存"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

def cached(expire: int = 3600, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(
                str(args) + str(kwargs)
            ).hexdigest()}"

            # 尝试从缓存获取
            cache = RedisCache()
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 写入缓存
            await cache.set(cache_key, result, expire)

            return result
        return wrapper
    return decorator

# 使用示例
class PaperService:
    @cached(expire=600, key_prefix="paper")
    async def get_paper(self, paper_id: UUID):
        return await self.db.get(paper_id)

    @cached(expire=300, key_prefix="paper_list")
    async def get_user_papers(self, user_id: UUID, page: int = 1):
        return await self.db.query(user_id=user_id, page=page)
```

### 4.2 数据库查询优化

```python
# utils/db_optimization.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

logger = logging.getLogger(__name__)

# 慢查询监控
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - context._query_start_time

    if total_time > 1.0:  # 超过 1 秒的查询记录为慢查询
        logger.warning(f"Slow query ({total_time:.2f}s): {statement[:200]}")

        # 发送到监控系统
        metrics.timing('db.query_slow', total_time * 1000)

# 查询优化器
class QueryOptimizer:
    @staticmethod
    def optimize_paper_query(query, user_id: UUID, filters: dict):
        """优化论文查询"""

        # 1. 选择性加载字段
        query = query.options(
            defer('content'),  # 延迟加载大字段
            defer('full_text')
        )

        # 2. 预加载关联数据
        query = query.options(
            joinedload('author'),
            joinedload('collaborators'),
            selectinload('comments')
        )

        # 3. 添加索引过滤
        query = query.filter(Paper.author_id == user_id)

        # 4. 添加分页
        if 'page' in filters:
            page = filters['page']
            per_page = filters.get('per_page', 20)
            query = query.offset((page - 1) * per_page).limit(per_page)

        return query
```

### 4.3 前端性能优化

```typescript
// utils/performanceMonitor.ts
export class PerformanceMonitor {
  static init() {
    // 监控 LCP (Largest Contentful Paint)
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        console.log('LCP:', entry.startTime);
        this.report('LCP', entry.startTime);
      }
    }).observe({ entryTypes: ['largest-contentful-paint'] });

    // 监控 FID (First Input Delay)
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        console.log('FID:', entry.processingStart - entry.startTime);
        this.report('FID', entry.processingStart - entry.startTime);
      }
    }).observe({ entryTypes: ['first-input'] });
  }

  static report(metric: string, value: number) {
    // 发送到监控系统
    fetch('/api/metrics', {
      method: 'POST',
      body: JSON.stringify({ metric, value, url: window.location.href })
    });
  }
}

// 虚拟列表组件 (长列表优化)
// components/common/VirtualList.tsx
import { useVirtualizer } from '@tanstack/react-virtual';

export function VirtualList({ items, renderItem, itemHeight = 50 }) {
  const parentRef = React.useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
  });

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {renderItem(items[virtualItem.index])}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## 5. 监控与告警

### 5.1 应用监控

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info

# 定义指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

ai_requests = Counter(
    'ai_requests_total',
    'Total AI service requests',
    ['model', 'status']
)

# 中间件集成
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # 记录指标
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()

    http_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

### 5.2 健康检查

```python
# monitoring/health.py
from fastapi import APIRouter
import asyncio

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """健康检查端点"""
    checks = {
        'database': await check_database(),
        'redis': await check_redis(),
        'ai_service': await check_ai_service(),
        'storage': await check_storage()
    }

    all_healthy = all(c['status'] == 'healthy' for c in checks.values())

    return {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }

async def check_database():
    try:
        await db.execute("SELECT 1")
        return {'status': 'healthy', 'latency_ms': 10}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

async def check_redis():
    try:
        await redis.ping()
        return {'status': 'healthy', 'latency_ms': 5}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}
```

## 6. 测试策略

### 6.1 单元测试

```python
# tests/services/test_permission_service.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def permission_service():
    return PermissionService()

@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="test@example.com")

class TestPermissionService:
    async def test_check_permission_with_role(self, permission_service, mock_user):
        # 准备
        await permission_service.assign_role(mock_user.id, 'advisor')

        # 执行
        result = await permission_service.check_permission(
            mock_user.id, 'paper:read'
        )

        # 验证
        assert result is True

    async def test_check_permission_denied(self, permission_service, mock_user):
        # 执行
        result = await permission_service.check_permission(
            mock_user.id, 'paper:delete', resource_id=uuid4()
        )

        # 验证
        assert result is False

    async def test_paper_owner_has_all_permissions(self, permission_service, mock_user):
        # 准备
        paper = Paper(id=uuid4(), author_id=mock_user.id)

        # 执行
        result = await permission_service.check_paper_permission(
            mock_user.id, paper.id, 'delete'
        )

        # 验证
        assert result is True
```

### 6.2 集成测试

```python
# tests/integration/test_notification_flow.py
@pytest.mark.asyncio
async def test_paper_comment_notification_flow(client, db):
    """测试评论通知完整流程"""

    # 1. 创建论文和协作者
    author = await create_user(db, email="author@test.com")
    collaborator = await create_user(db, email="collaborator@test.com")
    paper = await create_paper(db, author_id=author.id)
    await add_collaborator(db, paper.id, collaborator.id)

    # 2. 协作者添加评论
    async with client.websocket_connect(f"/ws/{collaborator.id}") as ws:
        response = await client.post(
            f"/papers/{paper.id}/comments",
            json={"content": "Great work!"},
            headers=auth_headers(collaborator)
        )
        assert response.status_code == 201

        # 3. 作者收到实时通知
        message = await ws.receive_json()
        assert message['type'] == 'notification'
        assert message['data']['title'] == 'New comment on your paper'

    # 4. 验证数据库通知记录
    notifications = await db.query(Notification).filter(
        Notification.user_id == author.id
    ).all()
    assert len(notifications) == 1
    assert notifications[0].type == NotificationType.PAPER_COMMENT
```

### 6.3 性能测试

```python
# tests/performance/test_load.py
import locust

class ScholarForgeUser(locust.HttpUser):
    wait_time = locust.between(1, 5)

    def on_start(self):
        """登录获取 token"""
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json()['access_token']

    @locust.task(3)
    def get_paper_list(self):
        """获取论文列表"""
        self.client.get(
            "/papers",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @locust.task(2)
    def get_paper_detail(self):
        """获取论文详情"""
        self.client.get(
            "/papers/test-paper-id",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @locust.task(1)
    def ai_suggestion(self):
        """AI 建议功能"""
        self.client.post(
            "/ai/suggest",
            json={"content": "Introduction to machine learning"},
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

## 7. 部署清单

### 7.1 环境变量配置

```bash
# .env.production
# 数据库
DATABASE_URL=postgresql://user:pass@db:5432/scholarforge
DATABASE_POOL_SIZE=20

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# 安全
ENCRYPTION_MASTER_KEY=xxx
JWT_SECRET_KEY=xxx
JWT_ALGORITHM=HS256

# AI 服务
OPENAI_API_KEY=sk-xxx
STEPFUN_API_KEY=xxx
AI_DEFAULT_MODEL=gpt-4

# 存储
S3_ENDPOINT=https://oss.example.com
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx
S3_BUCKET=scholarforge

# 邮件
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=xxx

# 监控
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
PROMETHEUS_PORT=9090
```

### 7.2 Docker Compose 生产配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: scholarforge/app:latest
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    env_file:
      - .env.production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    image: scholarforge/app:latest
    command: celery -A tasks worker --loglevel=info
    env_file:
      - .env.production
    deploy:
      replicas: 2

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 2G

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=scholarforge
      - POSTGRES_USER=scholarforge
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  postgres_data:
  redis_data:
```

---

## 附录：检查清单

### 部署前检查
- [ ] 所有环境变量已配置
- [ ] 数据库迁移已执行
- [ ] Redis 连接正常
- [ ] 对象存储配置正确
- [ ] SSL 证书已安装
- [ ] 日志收集已配置
- [ ] 监控告警已启用
- [ ] 备份策略已验证

### 发布后监控
- [ ] 错误率 < 0.1%
- [ ] API 响应时间 P95 < 500ms
- [ ] 数据库连接池使用率 < 80%
- [ ] Redis 内存使用率 < 70%
- [ ] 磁盘空间 > 20%

---

**文档版本**: v1.0
**最后更新**: 2026-03-06
