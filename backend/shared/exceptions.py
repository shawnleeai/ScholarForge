"""
异常处理模块
统一的应用异常定义
"""

from enum import Enum
from typing import Any, Optional


class ErrorCode(str, Enum):
    """错误码枚举"""

    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = "1000"
    VALIDATION_ERROR = "1001"
    NOT_FOUND = "1002"
    ALREADY_EXISTS = "1003"
    PERMISSION_DENIED = "1004"
    RATE_LIMIT_EXCEEDED = "1005"

    # 认证错误 (2000-2999)
    UNAUTHORIZED = "2000"
    INVALID_CREDENTIALS = "2001"
    TOKEN_EXPIRED = "2002"
    TOKEN_INVALID = "2003"
    ACCOUNT_DISABLED = "2004"
    EMAIL_NOT_VERIFIED = "2005"

    # 用户错误 (3000-3999)
    USER_NOT_FOUND = "3000"
    USER_ALREADY_EXISTS = "3001"
    EMAIL_ALREADY_REGISTERED = "3002"
    USERNAME_ALREADY_TAKEN = "3003"
    INVALID_PASSWORD = "3004"

    # 论文错误 (4000-4999)
    PAPER_NOT_FOUND = "4000"
    PAPER_ACCESS_DENIED = "4001"
    PAPER_VERSION_CONFLICT = "4002"

    # 文献错误 (5000-5999)
    ARTICLE_NOT_FOUND = "5000"
    ARTICLE_SOURCE_UNAVAILABLE = "5001"
    ARTICLE_SEARCH_FAILED = "5002"

    # AI 服务错误 (6000-6999)
    AI_SERVICE_UNAVAILABLE = "6000"
    AI_REQUEST_FAILED = "6001"
    AI_CONTENT_FILTERED = "6002"

    # 外部服务错误 (7000-7999)
    EXTERNAL_API_ERROR = "7000"
    DATABASE_ERROR = "7001"
    CACHE_ERROR = "7002"
    STORAGE_ERROR = "7003"


class AppException(Exception):
    """应用异常基类"""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Any] = None,
        status_code: int = 400,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {
            "code": self.error_code.value,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


# 预定义异常
class UnauthorizedException(AppException):
    """未认证异常"""

    def __init__(self, message: str = "未授权访问"):
        super().__init__(
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=401,
        )


class ForbiddenException(AppException):
    """权限不足异常"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=message,
            status_code=403,
        )


class NotFoundException(AppException):
    """资源不存在异常"""

    def __init__(self, resource: str = "资源"):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=f"{resource}不存在",
            status_code=404,
        )


class ValidationException(AppException):
    """验证失败异常"""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            status_code=422,
        )


class ConflictException(AppException):
    """资源冲突异常"""

    def __init__(self, message: str):
        super().__init__(
            error_code=ErrorCode.ALREADY_EXISTS,
            message=message,
            status_code=409,
        )
