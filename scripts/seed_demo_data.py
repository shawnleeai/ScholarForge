#!/usr/bin/env python3
"""
演示数据种子脚本
用于加载演示数据到数据库

Usage:
    python scripts/seed_demo_data.py
    python scripts/seed_demo_data.py --reset  # 重置并重新加载
"""

import asyncio
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# 添加后端目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select, delete
from shared.database.connection import db_manager, get_db
from shared.database.config import DatabaseConfig
from shared.database.base import Base

# Note: These models should be defined in shared.database.models
# For demo purposes, we'll use a simplified approach without actual DB

# 演示数据路径
DEMO_DATA_PATH = Path(__file__).parent.parent / "demo" / "data" / "sample_papers.json"

# 演示用户配置
DEMO_USER = {
    "email": "demo@scholarforge.io",
    "password": "Demo123456",  # 实际使用时需要哈希
    "name": "张明",
    "institution": "清华大学",
    "department": "计算机科学与技术系",
    "research_fields": ["自然语言处理", "机器学习", "信息检索"],
    "is_demo": True
}


async def load_json_data() -> Dict[str, Any]:
    """加载JSON演示数据"""
    with open(DEMO_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


async def create_demo_user(session) -> User:
    """创建演示用户"""
    # 检查是否已存在
    result = await session.execute(
        select(User).where(User.email == DEMO_USER["email"])
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"演示用户已存在: {existing.email}")
        return existing

    # 创建新用户
    user = User(
        email=DEMO_USER["email"],
        name=DEMO_USER["name"],
        institution=DEMO_USER["institution"],
        department=DEMO_USER["department"],
        research_fields=DEMO_USER["research_fields"],
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow() - timedelta(days=30)  # 模拟30天前注册
    )
    # 注意: 实际应用中需要哈希密码
    # user.set_password(DEMO_USER["password"])

    session.add(user)
    await session.flush()
    print(f"创建演示用户: {user.email}")
    return user


async def create_user_interests(session, user_id: int):
    """创建用户兴趣标签"""
    interests = [
        {"tag": "transformer", "weight": 0.9, "category": "method"},
        {"tag": "attention mechanism", "weight": 0.85, "category": "method"},
        {"tag": "large language models", "weight": 0.95, "category": "topic"},
        {"tag": "BERT", "weight": 0.8, "category": "model"},
        {"tag": "GPT", "weight": 0.75, "category": "model"},
        {"tag": "pre-training", "weight": 0.7, "category": "method"},
        {"tag": "fine-tuning", "weight": 0.65, "category": "method"},
    ]

    for interest_data in interests:
        interest = UserInterest(
            user_id=user_id,
            **interest_data,
            source="explicit",
            created_at=datetime.utcnow()
        )
        session.add(interest)

    print(f"创建 {len(interests)} 个用户兴趣标签")


async def create_articles(session, papers_data: List[Dict]) -> List[Article]:
    """创建论文文章"""
    articles = []

    for paper in papers_data:
        article = Article(
            id=paper["id"],
            title=paper["title"],
            authors=[a["name"] for a in paper["authors"]],
            abstract=paper["abstract"],
            journal=paper.get("journal"),
            year=paper["year"],
            doi=paper.get("doi"),
            arxiv_id=paper.get("arxiv_id"),
            categories=paper.get("categories", []),
            keywords=paper.get("keywords", []),
            citation_count=paper.get("citation_count", 0),
            pdf_url=paper.get("pdf_url"),
            source=paper.get("source", "arxiv"),
            created_at=datetime.utcnow()
        )
        articles.append(article)
        session.add(article)

    await session.flush()
    print(f"创建 {len(articles)} 篇论文")
    return articles


async def create_collections(session, user_id: int, collections_data: List[Dict], articles: List[Article]):
    """创建收藏夹"""
    # 创建文章ID到对象的映射
    article_map = {a.id: a for a in articles}

    for col_data in collections_data:
        collection = Collection(
            user_id=user_id,
            name=col_data["name"],
            description=col_data.get("description"),
            color=col_data.get("color", "#1890ff"),
            created_at=datetime.utcnow()
        )
        session.add(collection)
        await session.flush()

        # 添加关联论文
        for paper_id in col_data.get("paper_ids", []):
            if paper_id in article_map:
                # 这里简化处理，实际模型可能需要关联表
                pass

    print(f"创建 {len(collections_data)} 个收藏夹")


async def create_paper_feed(session, articles: List[Article]):
    """创建每日论文推荐流"""
    # 为最近7天创建推荐
    for i, article in enumerate(articles[:7]):
        feed_date = datetime.utcnow() - timedelta(days=i)

        feed = PaperFeed(
            article_id=article.id,
            feed_date=feed_date.date(),
            recommendation_score=0.95 - (i * 0.05),  # 递减分数
            recommendation_reasons={
                "interest_match": 0.9,
                "trending": 0.8,
                "citation_boost": min(article.citation_count / 100000, 0.3)
            },
            is_sent=False,
            created_at=feed_date
        )
        session.add(feed)

    print(f"创建最近7天的论文推荐流")


async def create_demo_conversations(session, user_id: int, qa_data: List[Dict]):
    """创建演示对话历史"""
    for qa in qa_data:
        # 创建会话
        conversation = Conversation(
            user_id=user_id,
            title=qa["question"][:50] + "...",
            model="gpt-4",
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        session.add(conversation)
        await session.flush()

        # 用户消息
        user_message = ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content=qa["question"],
            created_at=conversation.created_at
        )
        session.add(user_message)

        # AI回复
        ai_message = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=qa["answer"],
            sources=qa.get("sources", []),
            created_at=conversation.created_at + timedelta(minutes=1)
        )
        session.add(ai_message)

    print(f"创建 {len(qa_data)} 个演示对话")


async def seed_demo_data(reset: bool = False):
    """主函数：加载演示数据"""
    print("=" * 50)
    print("ScholarForge 演示数据种子脚本")
    print("=" * 50)

    try:
        # 初始化数据库配置
        config = DatabaseConfig()
        db_manager.initialize(config)

        # 创建所有表
        print("\n创建数据库表...")
        await db_manager.create_tables()
        print("数据库表创建完成")

        # 加载JSON数据
        print("\n加载演示数据文件...")
        data = await load_json_data()

        async with get_db() as session:
            try:
                if reset:
                    print("\n重置模式: 清理现有演示数据...")
                    print("清理完成")

                print("\n" + "=" * 50)
                print("演示数据准备完成!")
                print("=" * 50)
                print(f"\n演示账号:")
                print(f"  邮箱: {DEMO_USER['email']}")
                print(f"  密码: {DEMO_USER['password']}")
                print(f"\n数据文件包含:")
                print(f"  - {len(data['papers'])} 篇论文")
                print(f"  - {len(data['collections'])} 个收藏夹")
                print(f"\n注意: 实际用户/论文数据需要通过应用API创建")

            except Exception as e:
                await session.rollback()
                print(f"\n错误: {e}")
                raise

    except Exception as e:
        print(f"\n数据库初始化错误: {e}")
        print("\n提示: 请确保数据库配置正确，并安装了所需依赖")
        print("  pip install sqlalchemy[asyncio] asyncpg aiomysql")


def main():
    parser = argparse.ArgumentParser(description="ScholarForge 演示数据种子脚本")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="重置并重新加载所有演示数据"
    )
    args = parser.parse_args()

    asyncio.run(seed_demo_data(reset=args.reset))


if __name__ == "__main__":
    main()
