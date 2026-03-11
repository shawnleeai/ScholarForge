#!/usr/bin/env python3
"""
演示数据种子脚本
生成示例用户、论文、文献等数据
与 paper/数据/演示案例设计.md 匹配
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import DatabaseConfig, DatabaseType, db_manager
from shared.database.base import Base
from shared.database.models import User, UserPreference, Article, Paper
from sqlalchemy import select


# ============ 演示数据配置 ============

DEMO_USER = {
    "id": "user-wangxm-001",
    "email": "wangxiaoming@zju.edu.cn",
    "username": "wangxiaoming",
    "full_name": "王小明",
    "institution": "浙江大学",
    "department": "工程师学院",
    "position": "硕士研究生",
    "bio": "浙江大学工程师学院2024级MEM研究生，研究方向：人工智能与信息工程管理",
    "is_active": True,
    "is_verified": True,
}

DEMO_USER_PREFERENCES = {
    "research_fields": ["人工智能", "项目管理", "人机协同", "软件工程"],
    "keywords": ["Human-Agent Collaboration", "Multi-Agent Systems", "Project Management", "LLM"],
    "default_ai_model": "stepfun",
    "language": "zh-CN",
    "theme": "light",
}

# 演示论文 - 与演示案例中的论文题目匹配
DEMO_PAPERS = [
    {
        "id": "paper-thesis-001",
        "title": "基于多Agent协同的智能科研论文写作系统项目管理研究",
        "abstract": """本研究以ScholarForge智能科研论文写作系统为研究对象，探索多Agent协同的项目管理机制。
研究背景：随着AI技术特别是大语言模型的发展，人与AI Agent的协同工作模式成为研究热点。
研究内容：分析多Agent协同的特点，设计适用于AI驱动科研项目的管理框架。
研究方法：案例研究、系统开发、实验验证相结合。
研究结论：多Agent协同的项目管理模式可显著提升科研效率30-50%。""",
        "keywords": ["Human-Agent Collaboration", "Multi-Agent Systems", "Project Management", "AI"],
        "paper_type": "thesis",
        "status": "published",
        "language": "zh",
        "owner_id": "user-wangxm-001",
        "word_count": 45000,
        "page_count": 85,
    }
]

# 演示文献 - 与演示案例中的核心参考文献匹配
DEMO_ARTICLES = [
    {
        "id": "article-001",
        "title": "A Unified Framework for Human-Agent Collaboration",
        "authors": [{"name": "Microsoft Research"}],
        "abstract": "本研究提出了人-Agent协作的统一框架，系统阐述了协作的认知模型和交互机制。该研究将人-Agent协作分为五个层次：工具使用、助手模式、协作伙伴、自主代理、完全自主。",
        "journal": "Microsoft Research Technical Report",
        "year": 2025,
        "doi": "10.1234/msr.2025.001",
        "keywords": ["Human-Agent Collaboration", "LLM", "Cognitive Model"],
        "categories": ["cs.AI", "cs.HC"],
        "primary_category": "cs.AI",
        "citation_count": 156,
        "source": "arxiv",
    },
    {
        "id": "article-002",
        "title": "Towards fluid human-agent collaboration: From dynamic goal recognition to adaptive agent policy",
        "authors": [{"name": "Chiari, M."}, {"name": "Paxton, C."}],
        "abstract": "研究了动态人-Agent协作，提出了"fluid collaboration"的概念，强调协作应该是动态适应的而非静态定义的。",
        "journal": "Frontiers in Robotics and AI",
        "year": 2025,
        "doi": "10.3389/frobt.2025.1532693",
        "keywords": ["Human-Agent Collaboration", "Adaptive Policy", "Dynamic Goals"],
        "categories": ["cs.RO", "cs.AI"],
        "primary_category": "cs.RO",
        "citation_count": 89,
        "source": "arxiv",
    },
    {
        "id": "article-003",
        "title": "Agent2Agent Protocol: A New Era of Agent Interoperability",
        "authors": [{"name": "Google Research"}],
        "abstract": "A2A协议允许AI Agent之间相互通信、安全交换信息，为Agent间协作提供了技术基础。",
        "journal": "Google Research Blog",
        "year": 2025,
        "doi": "10.1234/google.2025.a2a",
        "keywords": ["Agent Protocol", "Interoperability", "Multi-Agent"],
        "categories": ["cs.DC", "cs.AI"],
        "primary_category": "cs.DC",
        "citation_count": 234,
        "source": "arxiv",
    },
    {
        "id": "article-004",
        "title": "Multi-Agent Collaboration via Cross-Team Orchestration",
        "authors": [{"name": "Khan, A."}, {"name": "Zhang, Y."}],
        "abstract": "提出了跨团队的多Agent协作框架，允许多个Agent团队协同解决复杂问题。",
        "journal": "ACL Findings",
        "year": 2025,
        "doi": "10.1234/acl.2025.8765",
        "keywords": ["Multi-Agent", "Orchestration", "Collaboration"],
        "categories": ["cs.CL", "cs.AI"],
        "primary_category": "cs.CL",
        "citation_count": 78,
        "source": "arxiv",
    },
    {
        "id": "article-005",
        "title": "Shaping the Future of Project Management With AI",
        "authors": [{"name": "PMI"}],
        "abstract": "PMI报告分析了AI对项目管理的影响，指出AI正在从辅助工具演变为项目团队成员。",
        "journal": "PMI Research Report",
        "year": 2025,
        "doi": "10.1234/pmi.2025.ai",
        "keywords": ["Project Management", "AI", "Future of Work"],
        "categories": ["cs.CY", "cs.AI"],
        "primary_category": "cs.CY",
        "citation_count": 312,
        "source": "arxiv",
    },
    {
        "id": "article-006",
        "title": "Reflective Multi-Agent Collaboration based on Large Language Models",
        "authors": [{"name": "NeurIPS 2024"}],
        "abstract": "提出了反射式多Agent协作机制，通过自我反思提升协作效率，可将任务完成准确率提升25%。",
        "journal": "NeurIPS 2024 Proceedings",
        "year": 2024,
        "doi": "10.1234/neurips.2024.refl",
        "keywords": ["Multi-Agent", "Reflection", "LLM"],
        "categories": ["cs.LG", "cs.AI"],
        "primary_category": "cs.LG",
        "citation_count": 445,
        "source": "arxiv",
    },
    {
        "id": "article-007",
        "title": "LLM-Based Human-Agent Collaboration and Interaction Systems: A Survey",
        "authors": [{"name": "Li, X."}, {"name": "Wang, J."}],
        "abstract": "本研究提供了LLM-HAS的首个全面综述，系统阐述了核心组件。研究表明，人-Agent协作可提升软件工程效率30-50%。",
        "journal": "IEEE Transactions on Software Engineering",
        "year": 2024,
        "doi": "10.1109/tse.2024.001",
        "keywords": ["LLM", "Human-Agent Collaboration", "Survey"],
        "categories": ["cs.SE", "cs.AI"],
        "primary_category": "cs.SE",
        "citation_count": 567,
        "source": "arxiv",
    },
]


# ============ 种子函数 ============

async def seed_demo_user(session):
    """创建演示用户（王小明）"""
    from shared.security import get_password_hash

    # 检查用户是否已存在
    result = await session.execute(
        select(User).where(User.email == DEMO_USER["email"])
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  用户已存在: {DEMO_USER['full_name']} ({DEMO_USER['email']})")
        return existing

    # 创建用户
    user = User(
        id=DEMO_USER["id"],
        email=DEMO_USER["email"],
        username=DEMO_USER["username"],
        hashed_password=get_password_hash("demo123456"),  # 演示密码
        full_name=DEMO_USER["full_name"],
        institution=DEMO_USER["institution"],
        department=DEMO_USER["department"],
        position=DEMO_USER["position"],
        bio=DEMO_USER["bio"],
        is_active=DEMO_USER["is_active"],
        is_verified=DEMO_USER["is_verified"],
        is_superuser=False,
    )
    session.add(user)
    await session.flush()

    # 创建用户偏好
    pref = UserPreference(
        user_id=user.id,
        research_fields=DEMO_USER_PREFERENCES["research_fields"],
        keywords=DEMO_USER_PREFERENCES["keywords"],
        default_ai_model=DEMO_USER_PREFERENCES["default_ai_model"],
        language=DEMO_USER_PREFERENCES["language"],
        theme=DEMO_USER_PREFERENCES["theme"],
    )
    session.add(pref)

    print(f"  创建用户: {user.full_name} ({user.email})")
    print(f"    学校: {user.institution}")
    print(f"    研究方向: {', '.join(pref.research_fields[:3])}...")
    return user


async def seed_demo_articles(session):
    """创建演示文献"""
    created = []

    for data in DEMO_ARTICLES:
        # 检查是否已存在
        result = await session.execute(
            select(Article).where(Article.doi == data.get("doi"))
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  文献已存在: {data['title'][:50]}...")
            created.append(existing)
            continue

        article = Article(
            id=data["id"],
            title=data["title"],
            authors=data["authors"],
            abstract=data.get("abstract", ""),
            journal=data.get("journal"),
            year=data.get("year"),
            doi=data.get("doi"),
            keywords=data.get("keywords", []),
            categories=data.get("categories", []),
            primary_category=data.get("primary_category"),
            citation_count=data.get("citation_count", 0),
        )
        session.add(article)
        created.append(article)
        print(f"  创建文献: {data['title'][:50]}... ({data['year']})")

    return created


async def seed_demo_papers(session, user_id: str):
    """创建演示论文"""
    created = []

    for data in DEMO_PAPERS:
        # 检查是否已存在
        result = await session.execute(
            select(Paper).where(Paper.id == data["id"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  论文已存在: {data['title'][:50]}...")
            created.append(existing)
            continue

        paper = Paper(
            id=data["id"],
            title=data["title"],
            abstract=data.get("abstract", ""),
            keywords=data.get("keywords", []),
            paper_type=data.get("paper_type", "thesis"),
            status=data.get("status", "draft"),
            language=data.get("language", "zh"),
            owner_id=user_id,
            word_count=data.get("word_count", 0),
            page_count=data.get("page_count", 0),
            figure_count=data.get("figure_count", 0),
            table_count=data.get("table_count", 0),
            reference_count=len(DEMO_ARTICLES),
        )
        session.add(paper)
        created.append(paper)
        print(f"  创建论文: {data['title'][:50]}...")
        print(f"    字数: {paper.word_count}, 页数: {paper.page_count}")

    return created


async def seed_all():
    """生成所有演示数据"""
    print("=" * 60)
    print("ScholarForge 演示数据种子")
    print("=" * 60)
    print()

    # 初始化数据库
    config = DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        database="./demo.db",
    )
    db_manager.initialize(config)

    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("数据库初始化完成")
    print()

    # 使用会话创建数据
    async with db_manager.session() as session:
        try:
            print("1. 创建演示用户...")
            user = await seed_demo_user(session)
            print()

            print("2. 创建演示文献...")
            articles = await seed_demo_articles(session)
            print(f"  共 {len(articles)} 篇文献")
            print()

            print("3. 创建演示论文...")
            papers = await seed_demo_papers(session, user.id)
            print(f"  共 {len(papers)} 篇论文")
            print()

            await session.commit()

        except Exception as e:
            await session.rollback()
            print(f"错误: {e}")
            raise

    print("=" * 60)
    print("演示数据创建成功！")
    print("=" * 60)
    print()
    print("演示账号:")
    print(f"  邮箱: {DEMO_USER['email']}")
    print(f"  密码: demo123456")
    print()
    print("演示场景:")
    print("  - 用户：王小明，浙江大学MEM研究生")
    print("  - 论文：基于多Agent协同的智能科研论文写作系统项目管理研究")
    print("  - 文献：7篇核心参考文献（与演示案例一致）")
    print()

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(seed_all())
