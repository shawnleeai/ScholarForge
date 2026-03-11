"""
Prompt管理模块
"""

from .academic_prompts import AcademicPrompts, PromptTemplate, PromptType
from .prompt_manager import PromptManager

__all__ = [
    'AcademicPrompts',
    'PromptTemplate',
    'PromptType',
    'PromptManager',
]