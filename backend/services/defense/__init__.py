"""
答辩准备服务
"""

from .routes import router
from .repository import (
    DefenseChecklistRepository,
    DefensePPTRepository,
    DefenseQARepository,
    DefenseMockRepository,
)

__all__ = [
    "router",
    "DefenseChecklistRepository",
    "DefensePPTRepository",
    "DefenseQARepository",
    "DefenseMockRepository",
]