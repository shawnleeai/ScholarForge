"""
Encryption Service
数据加密服务 - 提供端到端加密、字段级加密等功能
"""

import os
import base64
import json
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from datetime import datetime


class EncryptionService:
    """加密服务"""

    def __init__(self):
        self.master_key = os.environ.get('ENCRYPTION_MASTER_KEY')
        if not self.master_key:
            raise ValueError("ENCRYPTION_MASTER_KEY environment variable is required")

        # 确保主密钥是 32 字节
        self.master_key = self.master_key.encode()[:32].ljust(32, b'0')

    def derive_key(self, salt: bytes = None, context: str = "default") -> tuple[bytes, bytes]:
        """
        从主密钥派生加密密钥

        Args:
            salt: 盐值，如果为 None 则生成新的
            context: 上下文标识，用于不同场景的密钥分离

        Returns:
            (key, salt): 派生出的密钥和盐值
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
            backend=default_backend()
        )

        key_material = f"{self.master_key.decode()}:{context}".encode()
        key = base64.urlsafe_b64encode(kdf.derive(key_material))

        return key, salt

    def encrypt(self, plaintext: str, context: str = "default") -> dict:
        """
        加密文本

        Args:
            plaintext: 要加密的明文
            context: 加密上下文

        Returns:
            加密数据包，包含密文、盐值和元数据
        """
        if not plaintext:
            return None

        key, salt = self.derive_key(context=context)
        f = Fernet(key)

        encrypted = f.encrypt(plaintext.encode('utf-8'))

        return {
            'ciphertext': base64.b64encode(encrypted).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8'),
            'context': context,
            'algorithm': 'AES-256-CBC',
            'version': 1,
            'encrypted_at': datetime.utcnow().isoformat()
        }

    def decrypt(self, encrypted_package: dict) -> Optional[str]:
        """
        解密文本

        Args:
            encrypted_package: 加密数据包

        Returns:
            解密后的明文，失败返回 None
        """
        if not encrypted_package:
            return None

        try:
            salt = base64.b64decode(encrypted_package['salt'])
            context = encrypted_package.get('context', 'default')

            key, _ = self.derive_key(salt, context)
            f = Fernet(key)

            ciphertext = base64.b64decode(encrypted_package['ciphertext'])
            decrypted = f.decrypt(ciphertext)

            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"Decryption failed: {e}")
            return None

    def encrypt_field(self, value: str, user_id: str = None) -> str:
        """
        加密单个字段（简化版，返回 JSON 字符串）

        Args:
            value: 要加密的值
            user_id: 用户ID，用于上下文分离

        Returns:
            JSON 字符串格式的加密数据
        """
        context = f"user:{user_id}" if user_id else "default"
        encrypted = self.encrypt(value, context)
        return json.dumps(encrypted) if encrypted else None

    def decrypt_field(self, encrypted_value: str) -> Optional[str]:
        """
        解密单个字段

        Args:
            encrypted_value: JSON 字符串格式的加密数据

        Returns:
            解密后的值
        """
        if not encrypted_value:
            return None

        try:
            encrypted_package = json.loads(encrypted_value)
            return self.decrypt(encrypted_package)
        except Exception as e:
            print(f"Field decryption failed: {e}")
            return None

    def rotate_key(self, encrypted_package: dict, new_context: str = None) -> dict:
        """
        密钥轮换 - 解密后使用新密钥重新加密

        Args:
            encrypted_package: 旧加密数据
            new_context: 新上下文

        Returns:
            新的加密数据包
        """
        plaintext = self.decrypt(encrypted_package)
        if plaintext is None:
            raise ValueError("Cannot rotate key: decryption failed")

        context = new_context or encrypted_package.get('context', 'default')
        return self.encrypt(plaintext, context)


class PaperEncryptionService:
    """论文专用加密服务"""

    def __init__(self):
        self.encryption = EncryptionService()

    def encrypt_paper_content(self, content: str, paper_id: str, author_id: str) -> dict:
        """
        加密论文内容

        Args:
            content: 论文正文
            paper_id: 论文ID
            author_id: 作者ID

        Returns:
            加密数据包
        """
        context = f"paper:{paper_id}:author:{author_id}"
        return self.encryption.encrypt(content, context)

    def decrypt_paper_content(self, encrypted_package: dict, paper_id: str, author_id: str) -> Optional[str]:
        """
        解密论文内容

        Args:
            encrypted_package: 加密数据包
            paper_id: 论文ID（验证用）
            author_id: 作者ID（验证用）

        Returns:
            解密后的内容
        """
        # 验证上下文
        expected_context = f"paper:{paper_id}:author:{author_id}"
        actual_context = encrypted_package.get('context', '')

        if not actual_context.startswith(f"paper:{paper_id}"):
            raise ValueError("Context mismatch: paper_id does not match")

        return self.encryption.decrypt(encrypted_package)

    def encrypt_abstract(self, abstract: str, paper_id: str) -> str:
        """加密摘要（字段级）"""
        return self.encryption.encrypt_field(abstract, paper_id)

    def decrypt_abstract(self, encrypted_abstract: str) -> Optional[str]:
        """解密摘要"""
        return self.encryption.decrypt_field(encrypted_abstract)


class FieldEncryption:
    """SQLAlchemy 字段加密助手"""

    def __init__(self, encryption_service: EncryptionService):
        self.encryption = encryption_service

    def encrypt_column(self, value: str) -> str:
        """加密列值"""
        if value is None:
            return None
        return self.encryption.encrypt_field(value)

    def decrypt_column(self, value: str) -> str:
        """解密列值"""
        if value is None:
            return None
        return self.encryption.decrypt_field(value)


# 单例实例
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """获取加密服务单例"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def get_paper_encryption_service() -> PaperEncryptionService:
    """获取论文加密服务单例"""
    return PaperEncryptionService()
