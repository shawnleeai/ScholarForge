"""
统一响应格式模块
"""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel


class ResponseModel(BaseModel):
    """统一响应模型"""

    code: int = 200
    message: str = "Success"
    data: Optional[Any] = None
    timestamp: str = datetime.now(timezone.utc).isoformat()


class PaginatedData(BaseModel):
    """分页数据模型"""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


def success_response(
    data: Any = None,
    message: str = "Success",
    code: int = 200,
) -> dict:
    """成功响应"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def error_response(
    message: str,
    code: int = 400,
    errors: Optional[list] = None,
) -> dict:
    """错误响应"""
    response = {
        "code": code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if errors:
        response["errors"] = errors
    return response


def paginated_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
    message: str = "Success",
) -> dict:
    """分页响应"""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
        message=message,
    )
