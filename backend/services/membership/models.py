"""
Membership Models
会员体系模型 - 支持Trial/Standard/Pro/Ultra等级
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


class MembershipTier(str, Enum):
    """会员等级"""
    TRIAL = "trial"           # 试用版
    STANDARD = "standard"     # 标准版
    PRO = "pro"               # 专业版
    ULTRA = "ultra"           # 旗舰版


class BillingCycle(str, Enum):
    """计费周期"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class MembershipBenefits:
    """会员权益"""
    # Token配额
    monthly_tokens: int = 100000
    max_context_window: int = 32000

    # 模型访问权限
    available_models: List[str] = field(default_factory=lambda: ["gpt-3.5-turbo"])
    priority_access: bool = False

    # 功能权限
    can_use_vision: bool = False
    can_use_voice: bool = False
    can_use_video: bool = False
    can_export: bool = False
    can_collaborate: bool = False
    can_use_advanced_analysis: bool = False

    # 存储限制
    storage_gb: int = 1
    max_projects: int = 3
    max_papers: int = 10

    # 支持服务
    support_level: str = "community"  # community/standard/priority/dedicated


@dataclass
class MembershipPlan:
    """会员套餐"""
    tier: MembershipTier
    name: str
    description: str
    price_cny_monthly: float
    price_cny_quarterly: float
    price_cny_yearly: float
    benefits: MembershipBenefits
    is_popular: bool = False


@dataclass
class UserMembership:
    """用户会员状态"""
    user_id: str
    tier: MembershipTier
    status: str = "active"  # active/suspended/cancelled/expired

    # 时间信息
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    next_billing_date: Optional[datetime] = None

    # 使用统计
    tokens_used_this_period: int = 0
    tokens_remaining: int = 0

    # 支付信息
    payment_method: Optional[str] = None
    auto_renew: bool = True

    # 额外购买
    extra_tokens_purchased: int = 0
    extra_tokens_remaining: int = 0

    def is_active(self) -> bool:
        """检查会员是否有效"""
        if self.status != "active":
            return False
        if self.end_date and datetime.utcnow() > self.end_date:
            return False
        return True

    def get_total_available_tokens(self) -> int:
        """获取总可用token数"""
        return self.tokens_remaining + self.extra_tokens_remaining


@dataclass
class PaymentRecord:
    """支付记录"""
    id: str
    user_id: str
    amount_cny: float
    payment_type: str  # subscription/extra_tokens/addon
    description: str
    status: str  # pending/success/failed/refunded
    created_at: datetime = field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenPackage:
    """Token加油包"""
    id: str
    name: str
    token_amount: int
    price_cny: float
    bonus_tokens: int = 0
    validity_days: int = 90
    description: str = ""


# 预定义会员套餐
MEMBERSHIP_PLANS = {
    MembershipTier.TRIAL: MembershipPlan(
        tier=MembershipTier.TRIAL,
        name="免费试用",
        description="适合初次体验的用户",
        price_cny_monthly=0,
        price_cny_quarterly=0,
        price_cny_yearly=0,
        benefits=MembershipBenefits(
            monthly_tokens=100000,
            max_context_window=32000,
            available_models=["step-1-32k", "gpt-3.5-turbo", "deepseek-chat"],
            priority_access=False,
            can_use_vision=False,
            can_use_voice=False,
            can_use_video=False,
            can_export=True,
            can_collaborate=False,
            can_use_advanced_analysis=False,
            storage_gb=1,
            max_projects=2,
            max_papers=5,
            support_level="community"
        )
    ),

    MembershipTier.STANDARD: MembershipPlan(
        tier=MembershipTier.STANDARD,
        name="标准版",
        description="适合个人研究人员",
        price_cny_monthly=68,
        price_cny_quarterly=188,
        price_cny_yearly=588,
        benefits=MembershipBenefits(
            monthly_tokens=1000000,
            max_context_window=131072,
            available_models=["step-1-128k", "gpt-4o", "moonshot-v1-128k", "deepseek-chat"],
            priority_access=True,
            can_use_vision=True,
            can_use_voice=True,
            can_use_video=False,
            can_export=True,
            can_collaborate=True,
            can_use_advanced_analysis=False,
            storage_gb=10,
            max_projects=10,
            max_papers=100,
            support_level="standard"
        )
    ),

    MembershipTier.PRO: MembershipPlan(
        tier=MembershipTier.PRO,
        name="专业版",
        description="适合科研团队和高级用户",
        price_cny_monthly=168,
        price_cny_quarterly=468,
        price_cny_yearly=1588,
        is_popular=True,
        benefits=MembershipBenefits(
            monthly_tokens=5000000,
            max_context_window=262144,
            available_models=["step-1-256k", "gpt-4-turbo", "gpt-4o", "step-1o"],
            priority_access=True,
            can_use_vision=True,
            can_use_voice=True,
            can_use_video=True,
            can_export=True,
            can_collaborate=True,
            can_use_advanced_analysis=True,
            storage_gb=100,
            max_projects=50,
            max_papers=500,
            support_level="priority"
        )
    ),

    MembershipTier.ULTRA: MembershipPlan(
        tier=MembershipTier.ULTRA,
        name="旗舰版",
        description="适合大型研究团队和企业",
        price_cny_monthly=488,
        price_cny_quarterly=1288,
        price_cny_yearly=4688,
        benefits=MembershipBenefits(
            monthly_tokens=20000000,
            max_context_window=262144,
            available_models=["step-1-256k", "gpt-4-turbo", "gpt-4o", "step-1o", "step-video"],
            priority_access=True,
            can_use_vision=True,
            can_use_voice=True,
            can_use_video=True,
            can_export=True,
            can_collaborate=True,
            can_use_advanced_analysis=True,
            storage_gb=1000,
            max_projects=999999,
            max_papers=999999,
            support_level="dedicated"
        )
    )
}


# 预定义Token加油包
TOKEN_PACKAGES = [
    TokenPackage(
        id="token_500k",
        name="基础包",
        token_amount=500000,
        price_cny=39,
        bonus_tokens=50000,
        description="50万Tokens + 5万赠送"
    ),
    TokenPackage(
        id="token_2m",
        name="标准包",
        token_amount=2000000,
        price_cny=128,
        bonus_tokens=300000,
        description="200万Tokens + 30万赠送"
    ),
    TokenPackage(
        id="token_5m",
        name="超值包",
        token_amount=5000000,
        price_cny=288,
        bonus_tokens=1000000,
        description="500万Tokens + 100万赠送"
    ),
    TokenPackage(
        id="token_20m",
        name="团队包",
        token_amount=20000000,
        price_cny=888,
        bonus_tokens=5000000,
        description="2000万Tokens + 500万赠送"
    )
]
