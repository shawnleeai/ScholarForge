"""
论文数据模型
SQLAlchemy ORM 模型定义（SQLite兼容）
"""

import uuid
import json
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base

if TYPE_CHECKING:
    from services.user.models import User


class Paper(Base):
    """论文模型"""

    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    keywords: Mapped[Optional[str]] = mapped_column(Text)  # JSON字符串存储

    # 所有者与团队
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("teams.id", ondelete="SET NULL"),
    )

    # 论文元数据
    paper_type: Mapped[str] = mapped_column(String(50), default="thesis")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    language: Mapped[str] = mapped_column(String(10), default="zh")

    # 模板与格式
    template_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("paper_templates.id", ondelete="SET NULL"),
    )
    citation_style: Mapped[str] = mapped_column(String(50), default="gb-t-7714-2015")

    # 统计信息
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    figure_count: Mapped[int] = mapped_column(Integer, default=0)
    table_count: Mapped[int] = mapped_column(Integer, default=0)
    reference_count: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # 关系
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    sections: Mapped[List["PaperSection"]] = relationship(
        "PaperSection",
        back_populates="paper",
        cascade="all, delete-orphan",
        order_by="PaperSection.order_index",
    )
    collaborators: Mapped[List["PaperCollaborator"]] = relationship(
        "PaperCollaborator",
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    versions: Mapped[List["PaperVersion"]] = relationship(
        "PaperVersion",
        back_populates="paper",
        cascade="all, delete-orphan",
    )

    @property
    def keywords_list(self) -> List[str]:
        """获取关键词列表"""
        if self.keywords:
            try:
                return json.loads(self.keywords)
            except:
                return []
        return []


class PaperSection(Base):
    """论文章节模型"""

    __tablename__ = "paper_sections"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    paper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("paper_sections.id", ondelete="CASCADE"),
    )

    title: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[Optional[str]] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 章节元数据
    section_type: Mapped[Optional[str]] = mapped_column(String(50))
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # 关系
    paper: Mapped["Paper"] = relationship("Paper", back_populates="sections")
    children: Mapped[List["PaperSection"]] = relationship(
        "PaperSection",
        backref="parent",
        remote_side=[id],
        cascade="all, delete-orphan",
        single_parent=True,
    )


class PaperCollaborator(Base):
    """论文协作者模型"""

    __tablename__ = "paper_collaborators"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    paper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")

    # 权限设置
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    can_comment: Mapped[bool] = mapped_column(Boolean, default=True)
    can_share: Mapped[bool] = mapped_column(Boolean, default=False)

    invited_by: Mapped[Optional[str]] = mapped_column(String(36))
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # 关系
    paper: Mapped["Paper"] = relationship("Paper", back_populates="collaborators")


class PaperVersion(Base):
    """论文版本历史"""

    __tablename__ = "paper_versions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    paper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    content_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)

    created_by: Mapped[Optional[str]] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    change_summary: Mapped[Optional[str]] = mapped_column(Text)

    # 关系
    paper: Mapped["Paper"] = relationship("Paper", back_populates="versions")


class PaperTemplate(Base):
    """论文模板"""

    __tablename__ = "paper_templates"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # 模板来源
    source_type: Mapped[str] = mapped_column(String(20), default="system")
    source_id: Mapped[Optional[str]] = mapped_column(String(100))

    # 模板配置
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    preview_url: Mapped[Optional[str]] = mapped_column(String(500))

    # 可见性
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(36))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Comment(Base):
    """评论模型"""

    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    paper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("paper_sections.id", ondelete="CASCADE"),
    )
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("comments.id", ondelete="CASCADE"),
    )

    # 用户信息
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 评论内容
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 位置信息（用于定位到文档中的具体位置）
    position: Mapped[dict] = mapped_column(JSON, default=dict)  # {from, to, sectionId, selectedText}

    # 状态
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(36))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # 关系
    replies: Mapped[List["CommentReply"]] = relationship(
        "CommentReply",
        back_populates="comment",
        cascade="all, delete-orphan",
    )


class CommentReply(Base):
    """评论回复模型"""

    __tablename__ = "comment_replies"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    comment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # 关系
    comment: Mapped["Comment"] = relationship("Comment", back_populates="replies")


class Annotation(Base):
    """批注模型"""

    __tablename__ = "annotations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    paper_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("paper_sections.id", ondelete="CASCADE"),
    )

    # 创建者
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 批注类型
    annotation_type: Mapped[str] = mapped_column(String(20), default="comment")  # comment, highlight, question, suggestion

    # 批注内容
    content: Mapped[str] = mapped_column(Text)

    # 位置信息
    position: Mapped[dict] = mapped_column(JSON, default=dict)  # {from, to, sectionId, selectedText}

    # 样式（用于高亮等）
    style: Mapped[dict] = mapped_column(JSON, default=dict)  # {color, bgColor}

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, resolved, dismissed

    # 优先级
    priority: Mapped[str] = mapped_column(String(10), default="normal")  # low, normal, high

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
