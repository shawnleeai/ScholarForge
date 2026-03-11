"""
AI Tools Marketplace Models
AI科研工具商店模型 - 工具发布、购买、评价
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ToolType(str, Enum):
    """工具类型"""
    PLUGIN = "plugin"              # 插件
    SCRIPT = "script"              # 脚本
    TEMPLATE = "template"          # 模板
    WORKFLOW = "workflow"          # 工作流
    DATASET = "dataset"            # 数据集
    MODEL = "model"                # 模型
    EXTENSION = "extension"        # 扩展


class PricingType(str, Enum):
    """定价类型"""
    FREE = "free"                  # 免费
    PAID = "paid"                  # 付费
    SUBSCRIPTION = "subscription"  # 订阅
    FREEMIUM = "freemium"          # 免费增值


class ToolStatus(str, Enum):
    """工具状态"""
    DRAFT = "draft"
    PENDING = "pending"            # 审核中
    PUBLISHED = "published"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


@dataclass
class Tool:
    """AI科研工具"""
    id: str
    name: str
    description: str
    tool_type: ToolType
    developer_id: str
    status: ToolStatus = ToolStatus.DRAFT

    # 内容
    icon_url: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    demo_video_url: Optional[str] = None
    documentation_url: Optional[str] = None
    readme: str = ""

    # 分类
    categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    compatible_platforms: List[str] = field(default_factory=list)

    # 定价
    pricing_type: PricingType = PricingType.FREE
    price: float = 0.0
    currency: str = "CNY"
    subscription_period: Optional[str] = None  # monthly/yearly
    trial_days: int = 0

    # 版本
    version: str = "1.0.0"
    changelog: str = ""
    download_url: Optional[str] = None
    file_size: Optional[int] = None

    # 统计
    download_count: int = 0
    rating_sum: float = 0.0
    rating_count: int = 0
    review_count: int = 0

    # 时间
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    @property
    def rating(self) -> float:
        """平均评分"""
        if self.rating_count == 0:
            return 0.0
        return self.rating_sum / self.rating_count


@dataclass
class ToolReview:
    """工具评价"""
    id: str
    tool_id: str
    user_id: str
    rating: int  # 1-5
    title: str
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_recommended: bool = False
    helpful_count: int = 0


@dataclass
class ToolPurchase:
    """工具购买记录"""
    id: str
    tool_id: str
    user_id: str
    amount: float
    currency: str
    status: str = "completed"  # completed/refunded
    purchased_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # 订阅过期时间
    license_key: Optional[str] = None


@dataclass
class DeveloperProfile:
    """开发者主页"""
    user_id: str
    display_name: str
    bio: str = ""
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    verified: bool = False

    # 统计
    total_tools: int = 0
    total_downloads: int = 0
    total_revenue: float = 0.0
    average_rating: float = 0.0

    # 社交
    followers: List[str] = field(default_factory=list)
