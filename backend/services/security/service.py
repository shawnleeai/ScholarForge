"""
Security Service V2
数据安全服务V2 - 加密、审计、隐私保护、备份
"""

import uuid
import hashlib
import hmac
import base64
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from secrets import token_urlsafe

from .models import (
    EncryptionKey, EncryptedData, EncryptionLevel, KeyStatus,
    AuditLog, AuditAction, SecurityAlert, RiskLevel,
    PrivacyPreference, PrivacySetting, DataExportRequest,
    IPRestriction, BackupRecord
)


class SecurityServiceV2:
    """安全服务V2"""

    def __init__(self):
        self._keys: Dict[str, EncryptionKey] = {}
        self._encrypted_data: Dict[str, EncryptedData] = {}
        self._audit_logs: List[AuditLog] = []
        self._alerts: List[SecurityAlert] = []
        self._privacy_prefs: Dict[str, PrivacyPreference] = {}
        self._export_requests: Dict[str, DataExportRequest] = {}
        self._ip_restrictions: Dict[str, IPRestriction] = {}
        self._backups: Dict[str, BackupRecord] = {}

        # 模拟主密钥
        self._master_key = token_urlsafe(32)

    # ==================== 密钥管理 ====================

    def generate_key_pair(self, user_id: str, key_type: str = "user") -> EncryptionKey:
        """为用户生成密钥对"""
        key_id = str(uuid.uuid4())

        # 模拟生成密钥对
        public_key = f"pk_{token_urlsafe(32)}"
        private_key = f"sk_{token_urlsafe(32)}"

        # 使用主密钥加密私钥
        encrypted_private = self._encrypt_with_master_key(private_key)

        key = EncryptionKey(
            id=key_id,
            key_type=key_type,
            owner_id=user_id,
            public_key=public_key,
            encrypted_private_key=encrypted_private,
            key_fingerprint=hashlib.sha256(public_key.encode()).hexdigest()[:16],
            expires_at=datetime.utcnow() + timedelta(days=365)
        )

        self._keys[key_id] = key
        return key

    def get_user_key(self, user_id: str) -> Optional[EncryptionKey]:
        """获取用户的加密密钥"""
        for key in self._keys.values():
            if key.owner_id == user_id and key.status == KeyStatus.ACTIVE:
                return key
        return None

    def rotate_key(self, user_id: str) -> Optional[EncryptionKey]:
        """轮换密钥"""
        # 找到当前密钥并标记为过期
        current_key = self.get_user_key(user_id)
        if current_key:
            current_key.status = KeyStatus.EXPIRED

        # 生成新密钥
        new_key = self.generate_key_pair(user_id)
        new_key.last_rotated_at = datetime.utcnow()

        return new_key

    def _encrypt_with_master_key(self, data: str) -> str:
        """使用主密钥加密数据"""
        # 模拟加密
        return f"enc_{base64.b64encode(data.encode()).decode()}"

    def _decrypt_with_master_key(self, encrypted: str) -> str:
        """使用主密钥解密数据"""
        # 模拟解密
        if encrypted.startswith("enc_"):
            return base64.b64decode(encrypted[4:]).decode()
        return encrypted

    # ==================== 数据加密 ====================

    def encrypt_field(
        self,
        user_id: str,
        data_type: str,
        resource_id: str,
        plaintext: str,
        level: EncryptionLevel = EncryptionLevel.FIELD
    ) -> EncryptedData:
        """加密字段"""
        # 获取或生成用户密钥
        key = self.get_user_key(user_id)
        if not key:
            key = self.generate_key_pair(user_id)

        # 生成数据加密密钥(DEK)
        dek = token_urlsafe(32)

        # 使用DEK加密数据
        iv = token_urlsafe(16)
        encrypted_content = self._encrypt_with_dek(plaintext, dek, iv)

        # 使用用户公钥加密DEK
        encrypted_dek = self._encrypt_dek(dek, key.public_key)

        enc_data = EncryptedData(
            id=str(uuid.uuid4()),
            data_type=data_type,
            resource_id=resource_id,
            encryption_level=level,
            encrypted_content=encrypted_content,
            iv=iv,
            key_id=key.id,
            encrypted_data_key=encrypted_dek
        )

        self._encrypted_data[enc_data.id] = enc_data
        return enc_data

    def decrypt_field(self, encrypted_data_id: str, user_id: str) -> Optional[str]:
        """解密字段"""
        enc_data = self._encrypted_data.get(encrypted_data_id)
        if not enc_data:
            return None

        key = self._keys.get(enc_data.key_id)
        if not key or key.owner_id != user_id:
            return None

        # 解密DEK
        dek = self._decrypt_dek(enc_data.encrypted_data_key, key.encrypted_private_key)

        # 解密数据
        plaintext = self._decrypt_with_dek(
            enc_data.encrypted_content,
            dek,
            enc_data.iv
        )

        return plaintext

    def _encrypt_with_dek(self, plaintext: str, dek: str, iv: str) -> str:
        """使用DEK加密"""
        # 模拟加密
        combined = f"{plaintext}:{dek}:{iv}"
        return base64.b64encode(combined.encode()).decode()

    def _decrypt_with_dek(self, ciphertext: str, dek: str, iv: str) -> str:
        """使用DEK解密"""
        # 模拟解密
        try:
            decoded = base64.b64decode(ciphertext).decode()
            parts = decoded.rsplit(":", 2)
            return parts[0] if parts else ""
        except:
            return ""

    def _encrypt_dek(self, dek: str, public_key: str) -> str:
        """使用公钥加密DEK"""
        return f"encrypted_{dek}"

    def _decrypt_dek(self, encrypted_dek: str, private_key: str) -> str:
        """使用私钥解密DEK"""
        return encrypted_dek.replace("encrypted_", "")

    # ==================== 审计日志 ====================

    def log_audit(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """记录审计日志"""
        log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values or {},
            new_values=new_values or {},
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )

        self._audit_logs.append(log)

        # 检查异常
        self._detect_anomalies(log)

        return log

    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """查询审计日志"""
        logs = self._audit_logs

        if user_id:
            logs = [l for l in logs if l.user_id == user_id]

        if resource_type:
            logs = [l for l in logs if l.resource_type == resource_type]

        if action:
            logs = [l for l in logs if l.action == action]

        if start_time:
            logs = [l for l in logs if l.timestamp >= start_time]

        if end_time:
            logs = [l for l in logs if l.timestamp <= end_time]

        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs[:limit]

    def _detect_anomalies(self, log: AuditLog):
        """检测异常行为"""
        # 检测频繁失败登录
        if log.action == AuditAction.LOGIN and not log.success:
            recent_failures = [
                l for l in self._audit_logs[-20:]
                if l.user_id == log.user_id
                and l.action == AuditAction.LOGIN
                and not l.success
                and (log.timestamp - l.timestamp) < timedelta(minutes=10)
            ]

            if len(recent_failures) >= 5:
                self._create_alert(
                    "login_anomaly",
                    RiskLevel.HIGH,
                    f"用户 {log.user_id} 在短时间内多次登录失败",
                    affected_user_id=log.user_id,
                    evidence={"failure_count": len(recent_failures)}
                )

        # 检测异常数据访问
        if log.action == AuditAction.READ and log.resource_type == "paper":
            # 检测大量下载
            recent_reads = [
                l for l in self._audit_logs[-100:]
                if l.user_id == log.user_id
                and l.action == AuditAction.READ
                and l.timestamp > log.timestamp - timedelta(hours=1)
            ]

            if len(recent_reads) > 50:
                self._create_alert(
                    "data_exfiltration",
                    RiskLevel.MEDIUM,
                    f"用户 {log.user_id} 短时间内访问大量数据",
                    affected_user_id=log.user_id,
                    evidence={"access_count": len(recent_reads)}
                )

    def _create_alert(
        self,
        alert_type: str,
        risk_level: RiskLevel,
        description: str,
        affected_user_id: Optional[str] = None,
        affected_resource_id: Optional[str] = None,
        evidence: Optional[Dict] = None
    ) -> SecurityAlert:
        """创建安全告警"""
        alert = SecurityAlert(
            id=str(uuid.uuid4()),
            alert_type=alert_type,
            risk_level=risk_level,
            description=description,
            affected_user_id=affected_user_id,
            affected_resource_id=affected_resource_id,
            evidence=evidence or {}
        )

        self._alerts.append(alert)
        return alert

    def get_security_alerts(
        self,
        risk_level: Optional[RiskLevel] = None,
        resolved_only: Optional[bool] = None,
        limit: int = 50
    ) -> List[SecurityAlert]:
        """获取安全告警"""
        alerts = self._alerts

        if risk_level:
            alerts = [a for a in alerts if a.risk_level == risk_level]

        if resolved_only is not None:
            alerts = [a for a in alerts if (a.resolved_at is not None) == resolved_only]

        alerts.sort(key=lambda x: x.detected_at, reverse=True)
        return alerts[:limit]

    # ==================== 隐私保护 ====================

    def set_privacy_preferences(
        self,
        user_id: str,
        **preferences
    ) -> PrivacyPreference:
        """设置隐私偏好"""
        pref = self._privacy_prefs.get(user_id)
        if not pref:
            pref = PrivacyPreference(user_id=user_id)

        for key, value in preferences.items():
            if hasattr(pref, key):
                setattr(pref, key, value)

        pref.updated_at = datetime.utcnow()
        self._privacy_prefs[user_id] = pref

        return pref

    def get_privacy_preferences(self, user_id: str) -> PrivacyPreference:
        """获取隐私偏好"""
        return self._privacy_prefs.get(user_id, PrivacyPreference(user_id=user_id))

    def check_visibility(
        self,
        resource_owner_id: str,
        viewer_id: str,
        resource_type: str
    ) -> bool:
        """检查资源可见性"""
        pref = self.get_privacy_preferences(resource_owner_id)

        setting = getattr(pref, f"{resource_type}_visibility", PrivacySetting.TEAM_ONLY)

        if setting == PrivacySetting.PUBLIC:
            return True

        if setting == PrivacySetting.PRIVATE:
            return resource_owner_id == viewer_id

        if setting == PrivacySetting.TEAM_ONLY:
            # 简化处理：同一团队可访问
            return True

        return False

    def mask_sensitive_data(
        self,
        data: str,
        data_type: str
    ) -> str:
        """脱敏敏感数据"""
        if data_type == "email":
            # 邮箱脱敏: xxx***@xxx.com
            if "@" in data:
                local, domain = data.split("@")
                if len(local) > 2:
                    return f"{local[:2]}***@{domain}"

        elif data_type == "phone":
            # 手机脱敏: 138****8888
            if len(data) == 11:
                return f"{data[:3]}****{data[-4:]}"

        elif data_type == "name":
            # 姓名脱敏: 张**
            if len(data) > 1:
                return f"{data[0]}**"

        elif data_type == "id_card":
            # 身份证号脱敏
            if len(data) == 18:
                return f"{data[:6]}********{data[-4:]}"

        return data

    # ==================== 数据导出 ====================

    def request_data_export(
        self,
        user_id: str,
        data_types: List[str],
        request_type: str = "full"
    ) -> DataExportRequest:
        """请求数据导出"""
        request = DataExportRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            request_type=request_type,
            data_types=data_types,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        self._export_requests[request.id] = request

        # 模拟处理导出
        # 实际应异步处理
        request.status = "completed"
        request.completed_at = datetime.utcnow()
        request.download_url = f"https://api.example.com/exports/{request.id}.zip"
        request.file_size = 1024 * 1024  # 1MB

        return request

    def get_export_status(self, request_id: str, user_id: str) -> Optional[DataExportRequest]:
        """获取导出状态"""
        request = self._export_requests.get(request_id)
        if not request or request.user_id != user_id:
            return None
        return request

    # ==================== IP限制 ====================

    def set_ip_restrictions(
        self,
        user_id: str,
        allowed_ips: Optional[List[str]] = None,
        blocked_ips: Optional[List[str]] = None,
        enforce_ip_check: bool = False
    ) -> IPRestriction:
        """设置IP限制"""
        restriction = self._ip_restrictions.get(user_id)
        if not restriction:
            restriction = IPRestriction(id=str(uuid.uuid4()), user_id=user_id)

        if allowed_ips is not None:
            restriction.allowed_ips = allowed_ips

        if blocked_ips is not None:
            restriction.blocked_ips = blocked_ips

        restriction.enforce_ip_check = enforce_ip_check

        self._ip_restrictions[user_id] = restriction
        return restriction

    def check_ip_access(self, user_id: str, ip_address: str) -> bool:
        """检查IP访问权限"""
        restriction = self._ip_restrictions.get(user_id)
        if not restriction or not restriction.enforce_ip_check:
            return True

        # 检查黑名单
        if ip_address in restriction.blocked_ips:
            return False

        # 检查白名单
        if restriction.allowed_ips:
            return ip_address in restriction.allowed_ips

        return True

    # ==================== 备份管理 ====================

    def create_backup(
        self,
        backup_type: str = "full"
    ) -> BackupRecord:
        """创建备份"""
        backup = BackupRecord(
            id=str(uuid.uuid4()),
            backup_type=backup_type,
            retention_until=datetime.utcnow() + timedelta(days=90)
        )

        self._backups[backup.id] = backup

        # 模拟备份过程
        backup.status = "completed"
        backup.completed_at = datetime.utcnow()
        backup.size_bytes = 1024 * 1024 * 100  # 100MB
        backup.file_count = 1000

        return backup

    def get_backup_history(self, limit: int = 20) -> List[BackupRecord]:
        """获取备份历史"""
        backups = sorted(
            self._backups.values(),
            key=lambda x: x.started_at,
            reverse=True
        )
        return backups[:limit]


# 单例
_security_service_v2 = None


def get_security_service_v2() -> SecurityServiceV2:
    """获取安全服务V2单例"""
    global _security_service_v2
    if _security_service_v2 is None:
        _security_service_v2 = SecurityServiceV2()
    return _security_service_v2
