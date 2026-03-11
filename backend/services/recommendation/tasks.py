"""
推荐系统 Celery 任务
定时执行论文采集和推荐生成
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import List

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from .paper_fetcher import PaperFetcher, FetchConfig
from .interest_engine import HybridRecommender, InterestProfiler
from .paper_feed_models import (
    PaperSource, PaperCreate, DailyRecommendationCreate
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def fetch_daily_papers(self):
    """
    采集每日论文任务
    每6小时执行一次
    """
    logger.info("Starting daily paper fetch task")

    try:
        fetcher = PaperFetcher()

        # 配置采集参数
        configs = [
            FetchConfig(
                source=PaperSource.ARXIV,
                categories=["cs.AI", "cs.CL", "cs.LG", "cs.IR", "cs.CV"],
                keywords=["machine learning", "deep learning", "neural networks"],
                max_results=200,
                days_back=1
            ),
            FetchConfig(
                source=PaperSource.SEMANTIC_SCHOLAR,
                categories=["Computer Science", "Machine Learning"],
                keywords=["artificial intelligence", "NLP"],
                max_results=100,
                days_back=1
            ),
        ]

        total_fetched = 0
        total_new = 0

        for config in configs:
            try:
                logger.info(f"Fetching from {config.source.value}...")

                # 运行异步采集
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result, papers = loop.run_until_complete(
                    fetcher.fetch_all(config)
                )
                loop.close()

                # 保存到数据库 (这里简化处理)
                # 实际项目中应该调用数据库服务
                logger.info(
                    f"Fetched {result.fetched_count} papers from {config.source.value}, "
                    f"new: {result.new_count}"
                )

                total_fetched += result.fetched_count
                total_new += result.new_count

            except Exception as e:
                logger.error(f"Error fetching from {config.source.value}: {e}")
                continue

        logger.info(
            f"Paper fetch completed. Total: {total_fetched}, New: {total_new}"
        )

        return {
            "status": "success",
            "total_fetched": total_fetched,
            "total_new": total_new,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Task failed: {e}")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error("Max retries exceeded for fetch_daily_papers")
            raise


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_all_recommendations(self):
    """
    为所有活跃用户生成每日推荐
    每天早上9点执行
    """
    logger.info("Starting recommendation generation task")

    try:
        # 获取活跃用户列表 (简化处理)
        # 实际项目中应该从数据库查询
        active_users = get_active_users()

        today = date.today()
        recommender = HybridRecommender()

        results = {
            "total_users": len(active_users),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for user in active_users:
            try:
                # 生成该用户的推荐
                result = generate_for_user_task(
                    user_id=user["id"],
                    target_date=today
                )

                results["success"] += 1
                results["details"].append({
                    "user_id": user["id"],
                    "status": "success",
                    "recommendations_count": result.get("count", 0)
                })

            except Exception as e:
                logger.error(f"Failed to generate for user {user['id']}: {e}")
                results["failed"] += 1
                results["details"].append({
                    "user_id": user["id"],
                    "status": "failed",
                    "error": str(e)
                })

        logger.info(
            f"Recommendation generation completed. "
            f"Success: {results['success']}, Failed: {results['failed']}"
        )

        return results

    except Exception as e:
        logger.error(f"Task failed: {e}")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            raise


def get_active_users():
    """获取活跃用户列表 (模拟数据)"""
    # 实际项目中从数据库查询
    return [
        {"id": "user_001", "email": "user1@example.com"},
        {"id": "user_002", "email": "user2@example.com"},
        {"id": "user_003", "email": "user3@example.com"},
    ]


@shared_task
def generate_for_user_task(user_id: str, target_date: date):
    """为单个用户生成推荐"""
    logger.info(f"Generating recommendations for user {user_id}")

    # 这里简化处理，实际应该调用完整的推荐流程
    # 1. 获取用户兴趣
    # 2. 获取候选论文
    # 3. 运行推荐算法
    # 4. 保存推荐结果

    return {
        "user_id": user_id,
        "date": target_date.isoformat(),
        "count": 10,
        "status": "success"
    }


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_recommendation_emails(self):
    """
    发送每日推荐邮件
    每天早上9:30执行
    """
    logger.info("Starting email sending task")

    try:
        # 获取开启了邮件推送的用户
        users = get_email_enabled_users()

        results = {
            "total": len(users),
            "sent": 0,
            "failed": 0
        }

        for user in users:
            try:
                # 获取该用户的今日推荐
                recommendations = get_user_daily_recommendations(
                    user_id=user["id"],
                    rec_date=date.today()
                )

                if not recommendations:
                    continue

                # 发送邮件 (简化处理)
                # 实际项目中应该调用邮件服务
                logger.info(f"Sending email to {user['email']}")

                results["sent"] += 1

            except Exception as e:
                logger.error(f"Failed to send email to {user['email']}: {e}")
                results["failed"] += 1

        logger.info(
            f"Email sending completed. Sent: {results['sent']}, Failed: {results['failed']}"
        )

        return results

    except Exception as e:
        logger.error(f"Task failed: {e}")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            raise


def get_email_enabled_users():
    """获取开启了邮件推送的用户"""
    # 实际项目中从数据库查询
    return [
        {"id": "user_001", "email": "user1@example.com", "frequency": "daily"},
        {"id": "user_002", "email": "user2@example.com", "frequency": "daily"},
    ]


def get_user_daily_recommendations(user_id: str, rec_date: date):
    """获取用户某日的推荐"""
    # 实际项目中从数据库查询
    return []


@shared_task
def update_user_interests():
    """
    更新用户兴趣画像
    每周一凌晨2点执行
    """
    logger.info("Starting user interest update task")

    profiler = InterestProfiler()

    # 获取所有用户
    users = get_all_users()

    results = {
        "total": len(users),
        "updated": 0,
        "failed": 0
    }

    for user in users:
        try:
            # 获取用户行为数据
            reading_history = get_user_reading_history(user["id"])
            saved_papers = get_user_saved_papers(user["id"])
            search_queries = get_user_search_queries(user["id"])

            # 构建兴趣画像
            interest = profiler.build_profile(
                user_id=user["id"],
                reading_history=reading_history,
                saved_papers=saved_papers,
                search_queries=search_queries
            )

            # 保存到数据库
            save_user_interest(interest)

            results["updated"] += 1

        except Exception as e:
            logger.error(f"Failed to update interest for user {user['id']}: {e}")
            results["failed"] += 1

    logger.info(
        f"Interest update completed. Updated: {results['updated']}, Failed: {results['failed']}"
    )

    return results


def get_all_users():
    """获取所有用户"""
    return get_active_users()


def get_user_reading_history(user_id: str):
    """获取用户阅读历史"""
    return []


def get_user_saved_papers(user_id: str):
    """获取用户收藏的论文"""
    return []


def get_user_search_queries(user_id: str):
    """获取用户搜索历史"""
    return []


def save_user_interest(interest):
    """保存用户兴趣"""
    pass


@shared_task
def cleanup_old_recommendations(days_to_keep: int = 30):
    """
    清理旧的推荐数据
    每天凌晨3点执行
    """
    logger.info(f"Cleaning up recommendations older than {days_to_keep} days")

    cutoff_date = date.today() - timedelta(days=days_to_keep)

    # 实际项目中从数据库删除
    # delete_query = "DELETE FROM daily_recommendations WHERE recommend_date < :cutoff"

    logger.info(f"Cleaned up recommendations before {cutoff_date}")

    return {
        "cutoff_date": cutoff_date.isoformat(),
        "status": "success"
    }


@shared_task
def test_task():
    """测试任务"""
    logger.info("Test task executed successfully")
    return {"status": "success", "timestamp": datetime.now().isoformat()}
