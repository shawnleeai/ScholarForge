"""
文献综述生成服务
基于多篇文献自动生成学术综述
"""

from .service import LiteratureReviewService
from .routes import router

__all__ = ["LiteratureReviewService", "router"]
