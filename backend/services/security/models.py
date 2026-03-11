"""
Security V2 Models
数据安全与隐私保护模型V2 - 端到端加密、审计日志、隐私保护
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class EncryptionLevel(str, Enum):
    """加密级别"""
    NONE = "none"
    TRANSPORT = "transport"      # 传输加密 (TLS)
    FIELD = "field"              # 字段级加密
    END_TO_END = "end_to_end"    # 端到端加密


class KeyStatus(str, Enum):
    """密钥状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class AuditAction(str, Enum):
    """审计动作"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    SHARE = "share"
    PERMISSION_CHANGE = "permission_change"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PrivacySetting(str, Enum):
    """隐私设置"""
    PUBLIC = "public"            # 公开
    TEAM_ONLY = "team_only"      # 团队内
    PRIVATE = "private"          # 私密
    ANONYMOUS = "anonymous"      # 匿名


@dataclass
class EncryptionKey:
    """加密密钥"""
    id: str
    key_type: str              # master/data/field/session
    owner_id: str
    public_key: Optional[str] = None
    encrypted_private_key: Optional[str] = None
    key_fingerprint: Optional[str] = None

    algorithm: str = "AES-256-GCM"
    key_size: int = 256

    status: KeyStatus = KeyStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_rotated_at: Optional[datetime] = None


@dataclass
class EncryptedData:
    """加密数据"""
    id: str
    data_type: str             # paper/note/file等
    resource_id: str

    encryption_level: EncryptionLevel
    encrypted_content: str
    iv: Optional[str] = None   # 初始化向量
    auth_tag: Optional[str] = None  # 认证标签

    key_id: str = ""           # 使用的密钥ID
    encrypted_data_key: Optional[str] = None  # 加密的DEK

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditLog:
    """审计日志"""
    id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # 用户
    user_id: str = ""
    user_email: Optional[str] = None
    session_id: Optional[str] = None

    # 动作
    action: AuditAction = AuditAction.READ
    resource_type: str = ""    # paper/note/user等
    resource_id: str = ""

    # 详情
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 上下文
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None

    # 结果
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class SecurityAlert:
    """安全告警"""
    id: str
    alert_type: str            # login_anomaly/data_exfiltration/unauthorized_access
    risk_level: RiskLevel

    description: str
    affected_user_id: Optional[str] = None
    affected_resource_id: Optional[str] = None

    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    evidence: Dict[str, Any] = field(default_factory=dict)
    is_false_positive: bool = False


@dataclass
class PrivacyPreference:
    """用户隐私偏好"""
    user_id: str

    # 数据可见性
    profile_visibility: PrivacySetting = PrivacySetting.TEAM_ONLY
    paper_visibility: PrivacySetting = PrivacySetting.TEAM_ONLY
    activity_visibility: PrivacySetting = PrivacySetting.TEAM_ONLY

    # 搜索可见性
    allow_search_by_name: bool = True
    allow_search_by_email: bool = False
    allow_search_by_institution: bool = True

    # 数据使用
    allow_analytics: bool = True
    allow_personalization: bool = True
    allow_recommendations: bool = True

    # 第三方共享
    allow_third_party_share: bool = False

    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DataRetentionPolicy:
    """数据保留策略"""
    resource_type: str

    retention_days: int = 365      # 保留天数
    archive_after_days: int = 180  # 归档天数

    auto_delete: bool = False
    require_confirmation: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DataExportRequest:
    """数据导出请求"""
    id: str
    user_id: str

    request_type: str          # full/partial
    data_types: List[str] = field(default_factory=list)

    status: str = "pending"    # pending/processing/completed/failed
    requested_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None

    file_size: Optional[int] = None
    checksum: Optional[str] = None


@dataclass
class IPRestriction:
    """IP访问限制"""
    id: str
    user_id: str

    allowed_ips: List[str] = field(default_factory=list)
    blocked_ips: List[str] = field(default_factory=list)

    enforce_ip_check: bool = False
    allow_unknown_ips: bool = True

    geo_restrictions: List[str] = field(default_factory=list)  # 国家代码

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BackupRecord:
    """备份记录"""
    id: str
    backup_type: str           # full/incremental/differential

    status: str = "pending"    # pending/running/completed/failed
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    size_bytes: int = 0
    file_count: int = 0
    storage_location: str = ""

    checksum: Optional[str] = None
    is_encrypted: bool = True

    retention_until: Optional[datetime] = None
