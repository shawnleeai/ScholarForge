"""
文献数据模型
SQLAlchemy ORM 模型定义（SQLite兼容）
"""

import uuid
import json
from datetime import datetime, date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    Numeric,
    Boolean,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


class Article(Base):
    """文献模型"""

    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    doi: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[Optional[str]] = mapped_column(Text)  # JSON字符串存储
    abstract: Mapped[Optional[str]] = mapped_column(Text)

    # 来源信息
    source_type: Mapped[Optional[str]] = mapped_column(String(20))  # journal, conference, book, thesis
    source_name: Mapped[Optional[str]] = mapped_column(String(500))  # 期刊名或会议名
    source_db: Mapped[Optional[str]] = mapped_column(String(20), index=True)  # cnki, wos, ieee, arxiv

    # 出版信息
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    publication_date: Mapped[Optional[date]] = mapped_column(Date)
    volume: Mapped[Optional[str]] = mapped_column(String(50))
    issue: Mapped[Optional[str]] = mapped_column(String(50))
    pages: Mapped[Optional[str]] = mapped_column(String(50))
    issn: Mapped[Optional[str]] = mapped_column(String(20))
    isbn: Mapped[Optional[str]] = mapped_column(String(20))

    # 关键词（JSON字符串存储）
    keywords: Mapped[Optional[str]] = mapped_column(Text)

    # 指标
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    impact_factor: Mapped[Optional[float]] = mapped_column(Numeric(5, 3))

    # 链接
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))

    # 原始数据（JSON字符串存储）
    raw_data: Mapped[Optional[str]] = mapped_column(Text)

    # 时间戳
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    @property
    def authors_list(self) -> List[dict]:
        """获取作者列表"""
        if self.authors:
            try:
                return json.loads(self.authors)
            except:
                return []
        return []

    @property
    def keywords_list(self) -> List[str]:
        """获取关键词列表"""
        if self.keywords:
            try:
                return json.loads(self.keywords)
            except:
                return []
        return []


# 为了兼容性保留别名
ArticleCollection = Article


class UserLibrary(Base):
    """用户文献库"""

    __tablename__ = "user_libraries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    article_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 用户标注
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # 用户笔记
    notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[str]] = mapped_column(Text)  # JSON字符串存储

    # 分类
    folder_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("library_folders.id", ondelete="SET NULL"),
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # 关系
    article: Mapped["Article"] = relationship("Article")


class LibraryFolder(Base):
    """文献文件夹"""

    __tablename__ = "library_folders"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("library_folders.id", ondelete="CASCADE"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(10))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
