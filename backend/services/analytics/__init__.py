"""
学术分析服务
影响力分析、引用统计、研究趋势
"""

from .service import AnalyticsService
from .routes import router

__all__ = ["AnalyticsService", "router"]
