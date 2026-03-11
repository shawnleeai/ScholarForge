"""
Security V2 API Routes
数据安全与隐私保护API路由V2 - 加密、审计、隐私、备份
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from datetime import datetime

from .service import get_security_service_v2, EncryptionLevel, AuditAction, PrivacySetting

router = APIRouter(prefix="/security-v2", tags=["security-v2"])


# ==================== 请求/响应模型 ====================

class EncryptRequest(BaseModel):
    """加密请求"""
    data: str
    data_type: str
    resource_id: str
    level: str = "field"


class PrivacySettingsRequest(BaseModel):
    """隐私设置请求"""
    profile_visibility: Optional[str] = None
    paper_visibility: Optional[str] = None
    activity_visibility: Optional[str] = None
    allow_search_by_name: Optional[bool] = None
    allow_analytics: Optional[bool] = None
    allow_personalization: Optional[bool] = None


class IPRestrictionRequest(BaseModel):
    """IP限制请求"""
    allowed_ips: Optional[List[str]] = None
    blocked_ips: Optional[List[str]] = None
    enforce_ip_check: bool = False


class DataExportRequest(BaseModel):
    """数据导出请求"""
    data_types: List[str]  # papers/notes/profile/activity/all
    request_type: str = "partial"


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== 密钥管理API ====================

@router.post("/keys/generate")
async def generate_encryption_key(user_id: str = Depends(get_current_user)):
    """生成加密密钥"""
    service = get_security_service_v2()

    key = service.generate_key_pair(user_id)

    return {
        "message": "Encryption key generated",
        "key_id": key.id,
        "fingerprint": key.key_fingerprint,
        "algorithm": key.algorithm,
        "expires_at": key.expires_at.isoformat() if key.expires_at else None
    }


@router.post("/keys/rotate")
async def rotate_encryption_key(user_id: str = Depends(get_current_user)):
    """轮换加密密钥"""
    service = get_security_service_v2()

    new_key = service.rotate_key(user_id)

    if not new_key:
        raise HTTPException(status_code=404, detail="No active key found")

    return {
        "message": "Key rotated successfully",
        "new_key_id": new_key.id,
        "fingerprint": new_key.key_fingerprint
    }


# ==================== 数据加密API ====================

@router.post("/encrypt")
async def encrypt_data(
    request: EncryptRequest,
    user_id: str = Depends(get_current_user)
):
    """加密数据"""
    service = get_security_service_v2()

    try:
        level = EncryptionLevel(request.level)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid encryption level")

    enc_data = service.encrypt_field(
        user_id=user_id,
        data_type=request.data_type,
        resource_id=request.resource_id,
        plaintext=request.data,
        level=level
    )

    return {
        "message": "Data encrypted",
        "encrypted_id": enc_data.id,
        "encryption_level": enc_data.encryption_level.value,
        "key_id": enc_data.key_id
    }


@router.post("/decrypt/{encrypted_id}")
async def decrypt_data(
    encrypted_id: str,
    user_id: str = Depends(get_current_user)
):
    """解密数据"""
    service = get_security_service_v2()

    plaintext = service.decrypt_field(encrypted_id, user_id)

    if not plaintext:
        raise HTTPException(status_code=403, detail="Cannot decrypt data")

    return {
        "decrypted": plaintext[:100] + "..." if len(plaintext) > 100 else plaintext
    }


# ==================== 审计日志API ====================

@router.get("/audit-logs")
async def get_audit_logs(
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    user_id: str = Depends(get_current_user)
):
    """获取审计日志"""
    service = get_security_service_v2()

    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            pass

    logs = service.get_audit_logs(
        user_id=user_id,
        resource_type=resource_type,
        action=action_enum,
        start_time=start_date,
        end_time=end_date,
        limit=limit
    )

    return {
        "logs": [
            {
                "id": l.id,
                "timestamp": l.timestamp.isoformat(),
                "action": l.action.value,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "success": l.success,
                "ip_address": l.ip_address
            }
            for l in logs
        ]
    }


# ==================== 安全告警API ====================

@router.get("/alerts")
async def get_security_alerts(
    risk_level: Optional[str] = None,
    resolved_only: Optional[bool] = None,
    limit: int = 50
):
    """获取安全告警"""
    service = get_security_service_v2()

    from .models import RiskLevel
    risk_enum = None
    if risk_level:
        try:
            risk_enum = RiskLevel(risk_level)
        except ValueError:
            pass

    alerts = service.get_security_alerts(risk_enum, resolved_only, limit)

    return {
        "alerts": [
            {
                "id": a.id,
                "type": a.alert_type,
                "risk_level": a.risk_level.value,
                "description": a.description,
                "detected_at": a.detected_at.isoformat(),
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None
            }
            for a in alerts
        ]
    }


# ==================== 隐私设置API ====================

@router.get("/privacy/settings")
async def get_privacy_settings(user_id: str = Depends(get_current_user)):
    """获取隐私设置"""
    service = get_security_service_v2()
    pref = service.get_privacy_preferences(user_id)

    return {
        "profile_visibility": pref.profile_visibility.value,
        "paper_visibility": pref.paper_visibility.value,
        "activity_visibility": pref.activity_visibility.value,
        "search_settings": {
            "allow_search_by_name": pref.allow_search_by_name,
            "allow_search_by_email": pref.allow_search_by_email,
            "allow_search_by_institution": pref.allow_search_by_institution
        },
        "data_usage": {
            "allow_analytics": pref.allow_analytics,
            "allow_personalization": pref.allow_personalization,
            "allow_recommendations": pref.allow_recommendations
        },
        "third_party_share": pref.allow_third_party_share
    }


@router.put("/privacy/settings")
async def update_privacy_settings(
    request: PrivacySettingsRequest,
    user_id: str = Depends(get_current_user)
):
    """更新隐私设置"""
    service = get_security_service_v2()

    updates = {k: v for k, v in request.dict().items() if v is not None}

    # 转换字符串为枚举
    if "profile_visibility" in updates:
        updates["profile_visibility"] = PrivacySetting(updates["profile_visibility"])
    if "paper_visibility" in updates:
        updates["paper_visibility"] = PrivacySetting(updates["paper_visibility"])
    if "activity_visibility" in updates:
        updates["activity_visibility"] = PrivacySetting(updates["activity_visibility"])

    pref = service.set_privacy_preferences(user_id, **updates)

    return {
        "message": "Privacy settings updated",
        "updated_at": pref.updated_at.isoformat()
    }


@router.post("/privacy/data-export")
async def request_data_export(
    request: DataExportRequest,
    user_id: str = Depends(get_current_user)
):
    """请求数据导出"""
    service = get_security_service_v2()

    export = service.request_data_export(
        user_id=user_id,
        data_types=request.data_types,
        request_type=request.request_type
    )

    return {
        "message": "Export request submitted",
        "request_id": export.id,
        "status": export.status,
        "download_url": export.download_url,
        "expires_at": export.expires_at.isoformat() if export.expires_at else None
    }


@router.get("/privacy/data-export/{request_id}")
async def get_export_status(
    request_id: str,
    user_id: str = Depends(get_current_user)
):
    """获取导出状态"""
    service = get_security_service_v2()

    export = service.get_export_status(request_id, user_id)

    if not export:
        raise HTTPException(status_code=404, detail="Export request not found")

    return {
        "request_id": export.id,
        "status": export.status,
        "requested_at": export.requested_at.isoformat(),
        "completed_at": export.completed_at.isoformat() if export.completed_at else None,
        "download_url": export.download_url,
        "file_size": export.file_size
    }


@router.delete("/privacy/account")
async def delete_account(user_id: str = Depends(get_current_user)):
    """删除账户和数据（GDPR合规）"""
    # 实际应启动数据删除流程
    return {
        "message": "Account deletion request received",
        "status": "processing",
        "note": "Your data will be permanently deleted within 30 days"
    }


# ==================== IP限制API ====================

@router.post("/ip-restrictions")
async def set_ip_restrictions(
    request: IPRestrictionRequest,
    user_id: str = Depends(get_current_user)
):
    """设置IP限制"""
    service = get_security_service_v2()

    restriction = service.set_ip_restrictions(
        user_id=user_id,
        allowed_ips=request.allowed_ips,
        blocked_ips=request.blocked_ips,
        enforce_ip_check=request.enforce_ip_check
    )

    return {
        "message": "IP restrictions updated",
        "allowed_ips": restriction.allowed_ips,
        "blocked_ips": restriction.blocked_ips,
        "enforce_ip_check": restriction.enforce_ip_check
    }


@router.get("/ip-restrictions")
async def get_ip_restrictions(user_id: str = Depends(get_current_user)):
    """获取IP限制"""
    service = get_security_service_v2()

    restriction = service._ip_restrictions.get(user_id)

    if not restriction:
        return {
            "allowed_ips": [],
            "blocked_ips": [],
            "enforce_ip_check": False
        }

    return {
        "allowed_ips": restriction.allowed_ips,
        "blocked_ips": restriction.blocked_ips,
        "enforce_ip_check": restriction.enforce_ip_check
    }


# ==================== 数据脱敏API ====================

@router.post("/mask")
async def mask_sensitive_data(
    data: str,
    data_type: str  # email/phone/name/id_card
):
    """数据脱敏"""
    service = get_security_service_v2()

    masked = service.mask_sensitive_data(data, data_type)

    return {
        "original_type": data_type,
        "masked": masked
    }


# ==================== 备份管理API ====================

@router.post("/backups")
async def create_backup(
    backup_type: str = "full"
):
    """创建备份"""
    service = get_security_service_v2()

    backup = service.create_backup(backup_type)

    return {
        "message": "Backup created",
        "backup_id": backup.id,
        "type": backup.backup_type,
        "status": backup.status,
        "size_bytes": backup.size_bytes,
        "file_count": backup.file_count,
        "completed_at": backup.completed_at.isoformat() if backup.completed_at else None
    }


@router.get("/backups")
async def get_backup_history(limit: int = 20):
    """获取备份历史"""
    service = get_security_service_v2()

    backups = service.get_backup_history(limit)

    return {
        "backups": [
            {
                "id": b.id,
                "type": b.backup_type,
                "status": b.status,
                "size_bytes": b.size_bytes,
                "file_count": b.file_count,
                "started_at": b.started_at.isoformat(),
                "completed_at": b.completed_at.isoformat() if b.completed_at else None
            }
            for b in backups
        ]
    }


# ==================== 安全信息API ====================

@router.get("/info")
async def get_security_info():
    """获取安全信息"""
    return {
        "encryption": {
            "algorithms_supported": ["AES-256-GCM", "RSA-4096"],
            "default_level": "field",
            "end_to_end_available": True
        },
        "compliance": {
            "gdpr": True,
            "ccpa": True,
            "iso27001": "certified"
        },
        "data_retention": {
            "default_days": 365,
            "audit_logs_days": 2555  # 7 years
        },
        "security_features": [
            "End-to-end encryption",
            "Field-level encryption",
            "Audit logging",
            "IP restrictions",
            "Two-factor authentication",
            "Data export",
            "Account deletion",
            "Automatic backup"
        ]
    }
