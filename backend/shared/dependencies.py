"""
依赖注入模块
FastAPI 通用依赖
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .exceptions import UnauthorizedException
from .security import verify_token

# Bearer Token 安全方案
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """获取当前用户ID（从JWT Token）"""
    if credentials is None:
        raise UnauthorizedException("未提供认证令牌")

    token = credentials.credentials
    user_id = verify_token(token, token_type="access")

    if user_id is None:
        raise UnauthorizedException("无效或过期的令牌")

    return user_id


async def get_current_user_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """获取当前用户ID（可选）"""
    if credentials is None:
        return None

    token = credentials.credentials
    return verify_token(token, token_type="access")


class PaginationParams:
    """分页参数"""

    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100,
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
        self.offset = (self.page - 1) * self.page_size
        self.limit = self.page_size


def get_pagination_params(
    page: int = 1,
    page_size: int = 20,
) -> PaginationParams:
    """获取分页参数依赖"""
    return PaginationParams(page=page, page_size=page_size)
