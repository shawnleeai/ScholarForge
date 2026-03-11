"""
写作模板服务
提供论文模板管理、搜索、推荐和AI填充功能
"""

from .models import PaperTemplate, TemplateSection, TemplateFormat
from .search_service import TemplateSearchService
from .recommendation import TemplateRecommendation
from .ai_filler import TemplateAIFiller

__all__ = [
    "PaperTemplate",
    "TemplateSection",
    "TemplateFormat",
    "TemplateSearchService",
    "TemplateRecommendation",
    "TemplateAIFiller",
]