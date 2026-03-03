"""
ScholarForge Shared Module
共享模块 - 包含配置、数据库连接、通用工具
"""

from .config import settings
from .database import get_db, Base, engine, async_session_factory
from .exceptions import (
    AppException,
    ErrorCode,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
    ConflictException,
)
from .responses import success_response, error_response, paginated_response
from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
)
from .dependencies import (
    get_current_user_id,
    get_current_user_id_optional,
    PaginationParams,
    get_pagination_params,
)

__all__ = [
    # Config
    "settings",
    # Database
    "get_db",
    "Base",
    "engine",
    "async_session_factory",
    # Exceptions
    "AppException",
    "ErrorCode",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "ValidationException",
    "ConflictException",
    # Responses
    "success_response",
    "error_response",
    "paginated_response",
    # Security
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_token",
    # Dependencies
    "get_current_user_id",
    "get_current_user_id_optional",
    "PaginationParams",
    "get_pagination_params",
]
