"""
推荐服务数据模型
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from shared.database import Base


class UserPreference(Base):
    """用户偏好模型"""

    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)

    # 研究兴趣（关键词向量）
    research_interests = Column(Text)  # JSON 格式的关键词权重
    preferred_sources = Column(Text)  # 偏好的数据源
    preferred_languages = Column(Text)  # 偏好的语言

    # 协同过滤特征
    embedding_vector = Column(Text)  # 用户嵌入向量

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ArticleFeature(Base):
    """文献特征模型"""

    __tablename__ = "article_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)

    # 内容特征
    keywords = Column(Text)  # 关键词列表
    abstract_embedding = Column(Text)  # 摘要嵌入向量
    category = Column(String(100))  # 学科分类

    # 统计特征
    citation_count = Column(Integer, default=0)
    recency_score = Column(Float, default=0.0)  # 时效性分数
    authority_score = Column(Float, default=0.0)  # 权威性分数

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Recommendation(Base):
    """推荐记录模型"""

    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # 推荐分数
    score = Column(Float, nullable=False)
    relevance_score = Column(Float, default=0.0)
    timeliness_score = Column(Float, default=0.0)
    authority_score = Column(Float, default=0.0)

    # 推荐类型
    recommendation_type = Column(String(50))  # daily, similar, trending

    # 用户反馈
    is_clicked = Column(Boolean, default=False)
    is_saved = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class UserBehavior(Base):
    """用户行为模型"""

    __tablename__ = "user_behaviors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    behavior_type = Column(String(50))  # view, save, cite, download
    duration = Column(Integer, default=0)  # 浏览时长（秒）

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
