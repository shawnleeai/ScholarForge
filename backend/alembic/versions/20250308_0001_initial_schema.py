"""
Initial Schema

初始数据库模式 - 创建所有核心表

Revision ID: 0001
Revises:
Create Date: 2026-03-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级 - 创建所有表"""

    # 用户表
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=True),
        sa.Column('institution', sa.String(200), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('role', sa.String(50), default='user'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 论文表
    op.create_table(
        'papers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), default=list),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='draft'),  # draft/review/published
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('collaborators', sa.JSON(), default=list),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 文献表
    op.create_table(
        'articles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('external_id', sa.String(200), nullable=True, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('authors', sa.JSON(), default=list),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('journal', sa.String(200), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('doi', sa.String(200), nullable=True),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('source', sa.String(50), nullable=True),  # arxiv/cnki/ieee等
        sa.Column('citations_count', sa.Integer(), default=0),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 参考文献关联表
    op.create_table(
        'paper_references',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('paper_id', sa.String(36), sa.ForeignKey('papers.id'), nullable=False),
        sa.Column('article_id', sa.String(36), sa.ForeignKey('articles.id'), nullable=False),
        sa.Column('citation_style', sa.String(50), default='gb7714'),
        sa.Column('order_index', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 协作会话表
    op.create_table(
        'collaboration_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('paper_id', sa.String(36), sa.ForeignKey('papers.id'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('session_token', sa.String(255), unique=True, nullable=False),
        sa.Column('cursor_position', sa.JSON(), default=dict),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 评论表
    op.create_table(
        'comments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('paper_id', sa.String(36), sa.ForeignKey('papers.id'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('parent_id', sa.String(36), sa.ForeignKey('comments.id'), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('target_section', sa.String(200), nullable=True),
        sa.Column('position', sa.JSON(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # AI对话表
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('paper_id', sa.String(36), sa.ForeignKey('papers.id'), nullable=True),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('context', sa.JSON(), default=dict),
        sa.Column('model', sa.String(50), default='gpt-4'),
        sa.Column('is_archived', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # AI消息表
    op.create_table(
        'ai_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('ai_conversations.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),  # user/assistant/system
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 通知表
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # comment/mention/system
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),  # paper/comment等
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 创建索引
    op.create_index('idx_papers_owner', 'papers', ['owner_id'])
    op.create_index('idx_papers_status', 'papers', ['status'])
    op.create_index('idx_articles_source', 'articles', ['source'])
    op.create_index('idx_articles_year', 'articles', ['year'])
    op.create_index('idx_comments_paper', 'comments', ['paper_id'])
    op.create_index('idx_ai_messages_conv', 'ai_messages', ['conversation_id'])
    op.create_index('idx_notifications_user', 'notifications', ['user_id', 'is_read'])

    print("Initial schema created successfully!")


def downgrade() -> None:
    """降级 - 删除所有表"""

    # 删除表（按依赖顺序逆序）
    op.drop_table('notifications')
    op.drop_table('ai_messages')
    op.drop_table('ai_conversations')
    op.drop_table('comments')
    op.drop_table('collaboration_sessions')
    op.drop_table('paper_references')
    op.drop_table('articles')
    op.drop_table('papers')
    op.drop_table('users')

    print("Schema dropped successfully!")
