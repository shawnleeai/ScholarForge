"""
统一数据模型入口
整合所有服务的模型定义
"""

# 基础模型
from .base import Base, BaseModel, TimestampMixin, SoftDeleteMixin

# 用户与认证模型
class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"

    from sqlalchemy import String, Boolean, Text, Integer
    from sqlalchemy.orm import Mapped, mapped_column

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    institution: Mapped[Optional[str]] = mapped_column(String(200))
    department: Mapped[Optional[str]] = mapped_column(String(200))
    position: Mapped[Optional[str]] = mapped_column(String(100))
    bio: Mapped[Optional[str]] = mapped_column(Text)

    # 状态字段
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 统计字段
    paper_count: Mapped[int] = mapped_column(Integer, default=0)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)


class UserPreference(BaseModel):
    """用户偏好设置"""
    __tablename__ = "user_preferences"

    from sqlalchemy import String, JSON, ForeignKey
    from sqlalchemy.orm import Mapped, mapped_column

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 界面偏好
    language: Mapped[str] = mapped_column(String(10), default="zh-CN")
    theme: Mapped[str] = mapped_column(String(20), default="light")

    # 通知偏好
    email_notifications: Mapped[bool] = mapped_column(default=True)
    daily_digest: Mapped[bool] = mapped_column(default=False)

    # AI偏好
    default_ai_model: Mapped[str] = mapped_column(String(50), default="stepfun")
    custom_prompts: Mapped[Optional[dict]] = mapped_column(JSON)

    # 研究领域
    research_fields: Mapped[list] = mapped_column(JSON, default=list)
    keywords: Mapped[list] = mapped_column(JSON, default=list)


# 文献管理模型
class Article(BaseModel):
    """文献模型"""
    __tablename__ = "articles"

    from sqlalchemy import String, Text, Date, Integer, ForeignKey, JSON
    from sqlalchemy.orm import Mapped, mapped_column
    from datetime import date

    # 基础信息
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    authors: Mapped[list] = mapped_column(JSON, default=list)  # [{"name": "", "affiliation": ""}]

    # 出版信息
    journal: Mapped[Optional[str]] = mapped_column(String(500))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    volume: Mapped[Optional[str]] = mapped_column(String(50))
    issue: Mapped[Optional[str]] = mapped_column(String(50))
    pages: Mapped[Optional[str]] = mapped_column(String(50))
    doi: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    pmid: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    arxiv_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # 元数据
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    urls: Mapped[list] = mapped_column(JSON, default=list)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text)
    pdf_path: Mapped[Optional[str]] = mapped_column(Text)  # 本地存储路径

    # 分类
    categories: Mapped[list] = mapped_column(JSON, default=list)
    primary_category: Mapped[Optional[str]] = mapped_column(String(100))

    # 统计
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    # 所有者
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 原始数据
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)


class Collection(BaseModel):
    """文献集合/文件夹"""
    __tablename__ = "collections"

    from sqlalchemy import String, Text, ForeignKey
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # HEX颜色
    icon: Mapped[Optional[str]] = mapped_column(String(50))

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("collections.id", ondelete="SET NULL"))


class ArticleCollection(Base):
    """文献与集合关联表"""
    __tablename__ = "article_collections"

    from sqlalchemy import String, ForeignKey, UniqueConstraint
    from sqlalchemy.orm import Mapped, mapped_column

    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    collection_id: Mapped[str] = mapped_column(ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)


class Annotation(BaseModel):
    """文献批注/高亮"""
    __tablename__ = "annotations"

    from sqlalchemy import String, Text, ForeignKey, JSON, Float
    from sqlalchemy.orm import Mapped, mapped_column

    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 批注内容
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="highlight")  # highlight, note, underline

    # PDF位置信息
    page: Mapped[int] = mapped_column(default=1)
    position: Mapped[Optional[dict]] = mapped_column(JSON)  # {x, y, width, height}
    quad_points: Mapped[Optional[list]] = mapped_column(JSON)  # PDF四边形坐标

    # 关联文本
    selected_text: Mapped[Optional[str]] = mapped_column(Text)

    # 颜色
    color: Mapped[str] = mapped_column(String(7), default="#FFD700")


# AI对话模型
class Conversation(BaseModel):
    """AI对话会话"""
    __tablename__ = "conversations"

    from sqlalchemy import String, Text, ForeignKey, JSON, Enum as SQLEnum
    from sqlalchemy.orm import Mapped, mapped_column

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), default="新对话")
    type: Mapped[str] = mapped_column(String(50), default="general")  # general, research, paper_review

    # 上下文配置
    context_article_ids: Mapped[list] = mapped_column(JSON, default=list)
    context_paper_id: Mapped[Optional[str]] = mapped_column(String(36))

    # 模型设置
    model: Mapped[str] = mapped_column(String(50), default="stepfun")
    temperature: Mapped[float] = mapped_column(default=0.7)

    # 系统提示词
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)

    # 会话状态
    is_pinned: Mapped[bool] = mapped_column(default=False)
    is_archived: Mapped[bool] = mapped_column(default=False)


class Message(BaseModel):
    """对话消息"""
    __tablename__ = "messages"

    from sqlalchemy import String, Text, ForeignKey, JSON, Integer
    from sqlalchemy.orm import Mapped, mapped_column

    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), default="text")  # text, markdown, json

    #  token统计
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # 引用文献
    citations: Mapped[list] = mapped_column(JSON, default=list)  # [{article_id, title, snippet}]

    # 元数据
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)

    # 顺序
    sequence: Mapped[int] = mapped_column(Integer, default=0)


# 协作模型
class Team(BaseModel):
    """研究团队"""
    __tablename__ = "teams"

    from sqlalchemy import String, Text, ForeignKey
    from sqlalchemy.orm import Mapped, mapped_column

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)

    # 所有者
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class TeamMember(Base):
    """团队成员关联"""
    __tablename__ = "team_members"

    from sqlalchemy import String, ForeignKey, Enum as SQLEnum
    from sqlalchemy.orm import Mapped, mapped_column

    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    role: Mapped[str] = mapped_column(String(20), default="member")  # owner, admin, member, guest
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Comment(BaseModel):
    """评论"""
    __tablename__ = "comments"

    from sqlalchemy import String, Text, ForeignKey
    from sqlalchemy.orm import Mapped, mapped_column

    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # article, paper, discussion
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"))

    content: Mapped[str] = mapped_column(Text, nullable=False)


# 论文写作模型
class Paper(BaseModel):
    """论文文档"""
    __tablename__ = "papers"

    from sqlalchemy import String, Text, ForeignKey, JSON, Enum as SQLEnum
    from sqlalchemy.orm import Mapped, mapped_column

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[Optional[str]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"))

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    keywords: Mapped[list] = mapped_column(JSON, default=list)

    # 内容 (BlockNote JSON格式)
    content: Mapped[Optional[dict]] = mapped_column(JSON)

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, reviewing, submitted, published

    # 目标期刊
    target_journal: Mapped[Optional[str]] = mapped_column(String(500))


class PaperVersion(BaseModel):
    """论文版本历史"""
    __tablename__ = "paper_versions"

    from sqlalchemy import String, Text, ForeignKey, JSON, Integer
    from sqlalchemy.orm import Mapped, mapped_column

    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)

    version: Mapped[str] = mapped_column(String(20), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    content: Mapped[dict] = mapped_column(JSON, nullable=False)

    comment: Mapped[Optional[str]] = mapped_column(Text)
    change_summary: Mapped[Optional[str]] = mapped_column(Text)


# 术语库模型
class TerminologyEntry(BaseModel):
    """术语条目"""
    __tablename__ = "terminology_entries"

    from sqlalchemy import String, Text, Boolean, Integer
    from sqlalchemy.orm import Mapped, mapped_column

    source_term: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    target_term: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    source_lang: Mapped[str] = mapped_column(String(10), default="en")
    target_lang: Mapped[str] = mapped_column(String(10), default="zh")

    domain: Mapped[str] = mapped_column(String(100), default="general")
    definition: Mapped[Optional[str]] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text)

    examples: Mapped[list] = mapped_column(JSON, default=list)

    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)

    usage_count: Mapped[int] = mapped_column(Integer, default=0)


# 推荐系统模型
class DailyRecommendation(BaseModel):
    """每日论文推荐记录"""
    __tablename__ = "daily_recommendations"

    from sqlalchemy import String, ForeignKey, JSON, Float, Boolean
    from sqlalchemy.orm import Mapped, mapped_column

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    article_id: Mapped[str] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)

    # 推荐理由
    reason: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float, default=0.0)

    # 用户反馈
    is_clicked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)

    # 推荐日期
    recommend_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)


# 导入必要的类型用于类型提示
from datetime import datetime, date
from typing import Optional
from sqlalchemy import DateTime, func

__all__ = [
    # 基础
    "Base", "BaseModel", "TimestampMixin", "SoftDeleteMixin",
    # 用户
    "User", "UserPreference",
    # 文献
    "Article", "Collection", "ArticleCollection", "Annotation",
    # AI对话
    "Conversation", "Message",
    # 协作
    "Team", "TeamMember", "Comment",
    # 论文写作
    "Paper", "PaperVersion",
    # 术语
    "TerminologyEntry",
    # 推荐
    "DailyRecommendation",
]
