"""
数据库基础模型
SQLAlchemy 2.0 声明式基类
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    """
    SQLAlchemy 2.0 声明式基类
    所有模型都继承此类
    """

    # 自动生成表名: 类名小写转下划线
    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = cls.__name__
        # 驼峰命名转下划线命名
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)

    # 通用字段
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self, exclude: Optional[set] = None, include: Optional[set] = None) -> Dict[str, Any]:
        """转换为字典"""
        exclude = exclude or set()
        data = {}

        for column in self.__table__.columns:
            if column.name in exclude:
                continue
            if include and column.name not in include:
                continue

            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            data[column.name] = value

        return data

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """时间戳混入类"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """软删除混入类"""

    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """恢复"""
        self.is_deleted = False
        self.deleted_at = None


class BaseModel(Base, SoftDeleteMixin):
    """
    完整基础模型
    包含ID、时间戳、软删除
    """

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    @classmethod
    def generate_id(cls) -> str:
        """生成UUID"""
        return str(uuid.uuid4())


# 枚举类型辅助函数
def create_enum_column(enum_class, **kwargs):
    """创建枚举类型列"""
    return mapped_column(
        String(50),
        **kwargs
    )
