#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ScholarForge 服务测试脚本
验证各服务能否正常启动和响应
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """测试模块导入"""
    print("=" * 50)
    print("Testing module imports...")
    print("=" * 50)

    errors = []

    # 测试共享模块
    try:
        from shared.config import settings
        print("[OK] shared.config")
    except Exception as e:
        errors.append(f"[FAIL] shared.config: {e}")
        print(f"[FAIL] shared.config: {e}")

    try:
        from shared.database import Base, get_db, init_db
        print("[OK] shared.database")
    except Exception as e:
        errors.append(f"[FAIL] shared.database: {e}")
        print(f"[FAIL] shared.database: {e}")

    try:
        from shared.security import get_password_hash, verify_password
        print("[OK] shared.security")
    except Exception as e:
        errors.append(f"[FAIL] shared.security: {e}")
        print(f"[FAIL] shared.security: {e}")

    try:
        from shared.exceptions import AppException, NotFoundException
        print("[OK] shared.exceptions")
    except Exception as e:
        errors.append(f"[FAIL] shared.exceptions: {e}")
        print(f"[FAIL] shared.exceptions: {e}")

    # 测试用户服务
    try:
        from services.user.models import User, Team, TeamMember
        print("[OK] services.user.models")
    except Exception as e:
        errors.append(f"[FAIL] services.user.models: {e}")
        print(f"[FAIL] services.user.models: {e}")

    try:
        from services.user.routes import router
        print("[OK] services.user.routes")
    except Exception as e:
        errors.append(f"[FAIL] services.user.routes: {e}")
        print(f"[FAIL] services.user.routes: {e}")

    try:
        from services.user.main import app as user_app
        print("[OK] services.user.main")
    except Exception as e:
        errors.append(f"[FAIL] services.user.main: {e}")
        print(f"[FAIL] services.user.main: {e}")

    # 测试文献服务
    try:
        from services.article.models import Article
        print("[OK] services.article.models")
    except Exception as e:
        errors.append(f"[FAIL] services.article.models: {e}")
        print(f"[FAIL] services.article.models: {e}")

    try:
        from services.article.main import app as article_app
        print("[OK] services.article.main")
    except Exception as e:
        errors.append(f"[FAIL] services.article.main: {e}")
        print(f"[FAIL] services.article.main: {e}")

    # 测试论文服务
    try:
        from services.paper.models import Paper, PaperSection
        print("[OK] services.paper.models")
    except Exception as e:
        errors.append(f"[FAIL] services.paper.models: {e}")
        print(f"[FAIL] services.paper.models: {e}")

    try:
        from services.paper.main import app as paper_app
        print("[OK] services.paper.main")
    except Exception as e:
        errors.append(f"[FAIL] services.paper.main: {e}")
        print(f"[FAIL] services.paper.main: {e}")

    # 测试AI服务
    try:
        from services.ai.llm_provider import LLMService
        print("[OK] services.ai.llm_provider")
    except Exception as e:
        errors.append(f"[FAIL] services.ai.llm_provider: {e}")
        print(f"[FAIL] services.ai.llm_provider: {e}")

    try:
        from services.ai.writing_assistant import WritingAssistant
        print("[OK] services.ai.writing_assistant")
    except Exception as e:
        errors.append(f"[FAIL] services.ai.writing_assistant: {e}")
        print(f"[FAIL] services.ai.writing_assistant: {e}")

    try:
        from services.ai.main import app as ai_app
        print("[OK] services.ai.main")
    except Exception as e:
        errors.append(f"[FAIL] services.ai.main: {e}")
        print(f"[FAIL] services.ai.main: {e}")

    # 测试推荐服务
    try:
        from services.recommendation.algorithm import RecommendationAlgorithm
        print("[OK] services.recommendation.algorithm")
    except Exception as e:
        errors.append(f"[FAIL] services.recommendation.algorithm: {e}")
        print(f"[FAIL] services.recommendation.algorithm: {e}")

    try:
        from services.recommendation.main import app as rec_app
        print("[OK] services.recommendation.main")
    except Exception as e:
        errors.append(f"[FAIL] services.recommendation.main: {e}")
        print(f"[FAIL] services.recommendation.main: {e}")

    # 测试协作服务
    try:
        from services.collaboration.main import app as collab_app
        print("[OK] services.collaboration.main")
    except Exception as e:
        errors.append(f"[FAIL] services.collaboration.main: {e}")
        print(f"[FAIL] services.collaboration.main: {e}")

    print()
    if errors:
        print(f"Found {len(errors)} errors:")
        for err in errors:
            print(f"  {err}")
        return False
    else:
        print("All module imports successful!")
        return True


async def test_database():
    """测试数据库连接"""
    print("\n" + "=" * 50)
    print("Testing database connection...")
    print("=" * 50)

    try:
        from shared.database import init_db, close_db, engine
        from sqlalchemy import text

        # 初始化数据库
        await init_db()
        print("[OK] Database initialized")

        # 测试连接
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("[OK] Database connection test passed")

        await close_db()
        print("[OK] Database closed")
        return True

    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        return False


def test_password_hash():
    """测试密码哈希"""
    print("\n" + "=" * 50)
    print("Testing password hashing...")
    print("=" * 50)

    try:
        from shared.security import get_password_hash, verify_password

        password = "test123456"
        hashed = get_password_hash(password)
        print(f"[OK] Password hash generated: {hashed[:30]}...")

        verified = verify_password(password, hashed)
        print(f"[OK] Password verification: {verified}")

        wrong_verified = verify_password("wrong_password", hashed)
        print(f"[OK] Wrong password verification: {wrong_verified} (should be False)")

        return verified and not wrong_verified

    except Exception as e:
        print(f"[FAIL] Password test failed: {e}")
        return False


def test_jwt_token():
    """测试JWT令牌"""
    print("\n" + "=" * 50)
    print("Testing JWT tokens...")
    print("=" * 50)

    try:
        from shared.security import create_access_token, create_refresh_token, verify_token

        # 创建访问令牌
        access_token = create_access_token(subject="test-user-123")
        print(f"[OK] Access token created: {access_token[:50]}...")

        # 验证令牌
        user_id = verify_token(access_token, token_type="access")
        print(f"[OK] Access token verified: user_id={user_id}")

        # 创建刷新令牌
        refresh_token = create_refresh_token(subject="test-user-123")
        print(f"[OK] Refresh token created")

        # 验证刷新令牌
        user_id_from_refresh = verify_token(refresh_token, token_type="refresh")
        print(f"[OK] Refresh token verified: user_id={user_id_from_refresh}")

        return user_id == "test-user-123"

    except Exception as e:
        print(f"[FAIL] JWT test failed: {e}")
        return False


def test_recommendation_algorithm():
    """测试推荐算法"""
    print("\n" + "=" * 50)
    print("Testing recommendation algorithm...")
    print("=" * 50)

    try:
        from services.recommendation.algorithm import RecommendationAlgorithm
        from datetime import datetime

        algo = RecommendationAlgorithm()

        # 测试相关度计算
        relevance = algo.calculate_relevance_score(
            user_interests={"AI": 0.8, "PM": 0.6},
            article_keywords=["AI", "ML", "DL"],
        )
        print(f"[OK] Relevance score: {relevance:.2f}")

        # 测试时效性计算
        timeliness = algo.calculate_timeliness_score(
            publication_date=datetime(2024, 1, 1)
        )
        print(f"[OK] Timeliness score: {timeliness:.2f}")

        # 测试权威性计算
        authority = algo.calculate_authority_score(
            citation_count=100,
            impact_factor=3.5,
        )
        print(f"[OK] Authority score: {authority:.2f}")

        # 测试总分计算
        total, scores = algo.calculate_total_score(
            relevance=relevance,
            timeliness=timeliness,
            authority=authority,
        )
        print(f"[OK] Total score: {total:.2f}")
        print(f"  Dimension scores: {scores}")

        # 测试推荐解释
        explanation = algo.generate_explanation(scores, "Test Paper")
        print(f"[OK] Explanation: {explanation}")

        return True

    except Exception as e:
        print(f"[FAIL] Recommendation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  ScholarForge Backend Service Tests")
    print("=" * 60)

    results = {
        "Module Imports": test_imports(),
        "Password Hashing": test_password_hash(),
        "JWT Tokens": test_jwt_token(),
        "Recommendation Algorithm": test_recommendation_algorithm(),
    }

    # 数据库测试（异步）
    print("\nTesting database...")
    try:
        results["Database Connection"] = asyncio.run(test_database())
    except Exception as e:
        print(f"Database test skipped: {e}")
        results["Database Connection"] = None

    # 打印结果摘要
    print("\n" + "=" * 60)
    print("  Test Results Summary")
    print("=" * 60)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results.items():
        if result is True:
            print(f"  [PASS] {name}")
            passed += 1
        elif result is False:
            print(f"  [FAIL] {name}")
            failed += 1
        else:
            print(f"  [SKIP] {name}")
            skipped += 1

    print()
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
