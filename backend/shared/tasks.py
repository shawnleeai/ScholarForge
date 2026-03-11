"""
Celery 任务配置
定时任务：论文采集、推荐生成
"""

import os
from celery import Celery
from celery.schedules import crontab

# 创建Celery应用
app = Celery('scholarforge')

# 配置
app.conf.update(
    # 使用Redis作为Broker和Backend
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),

    # 序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # 时区
    timezone='Asia/Shanghai',
    enable_utc=True,

    # 任务跟踪
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时

    # 结果过期时间
    result_expires=3600 * 24,  # 1天

    #  worker配置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 自动发现任务
app.autodiscover_tasks([
    'services.recommendation.tasks',
    'services.article.tasks',
    'services.ai.tasks',
])


# 定时任务配置
app.conf.beat_schedule = {
    # 每日论文采集 (每6小时)
    'fetch-papers-every-6-hours': {
        'task': 'services.recommendation.tasks.fetch_daily_papers',
        'schedule': 60 * 60 * 6,  # 6小时
        'args': (),
    },

    # 生成每日推荐 (每天早上9点)
    'generate-daily-recommendations': {
        'task': 'services.recommendation.tasks.generate_all_recommendations',
        'schedule': crontab(hour=9, minute=0),
        'args': (),
    },

    # 发送每日推荐邮件 (每天早上9:30)
    'send-daily-recommendation-emails': {
        'task': 'services.recommendation.tasks.send_recommendation_emails',
        'schedule': crontab(hour=9, minute=30),
        'args': (),
    },

    # 更新用户兴趣画像 (每周一凌晨2点)
    'update-user-interests': {
        'task': 'services.recommendation.tasks.update_user_interests',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),
        'args': (),
    },

    # 清理旧推荐数据 (每天凌晨3点)
    'cleanup-old-recommendations': {
        'task': 'services.recommendation.tasks.cleanup_old_recommendations',
        'schedule': crontab(hour=3, minute=0),
        'args': (30,),  # 保留30天
    },

    # 全文索引更新 (每2小时)
    'update-search-index': {
        'task': 'services.article.tasks.update_search_index',
        'schedule': 60 * 60 * 2,
        'args': (),
    },
}
