"""
Membership Service
会员服务 - 管理用户订阅、配额、支付
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from .models import (
    MembershipTier, BillingCycle, UserMembership, MembershipPlan,
    PaymentRecord, TokenPackage, MEMBERSHIP_PLANS, TOKEN_PACKAGES
)


class MembershipService:
    """会员服务"""

    def __init__(self):
        # 内存存储（实际应使用数据库）
        self._memberships: Dict[str, UserMembership] = {}
        self._payments: List[PaymentRecord] = []

    def create_trial_membership(self, user_id: str) -> UserMembership:
        """创建试用会员"""
        plan = MEMBERSHIP_PLANS[MembershipTier.TRIAL]

        membership = UserMembership(
            user_id=user_id,
            tier=MembershipTier.TRIAL,
            status="active",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=14),  # 14天试用
            billing_cycle=BillingCycle.MONTHLY,
            tokens_remaining=plan.benefits.monthly_tokens
        )

        self._memberships[user_id] = membership
        return membership

    def get_membership(self, user_id: str) -> Optional[UserMembership]:
        """获取用户会员信息"""
        membership = self._memberships.get(user_id)

        # 如果没有会员记录，自动创建试用
        if not membership:
            membership = self.create_trial_membership(user_id)

        return membership

    def upgrade_membership(
        self,
        user_id: str,
        tier: MembershipTier,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY
    ) -> UserMembership:
        """升级/更改会员等级"""
        plan = MEMBERSHIP_PLANS[tier]

        # 计算价格
        if billing_cycle == BillingCycle.MONTHLY:
            price = plan.price_cny_monthly
        elif billing_cycle == BillingCycle.QUARTERLY:
            price = plan.price_cny_quarterly
        else:
            price = plan.price_cny_yearly

        # 计算有效期
        if billing_cycle == BillingCycle.MONTHLY:
            end_date = datetime.utcnow() + timedelta(days=30)
        elif billing_cycle == BillingCycle.QUARTERLY:
            end_date = datetime.utcnow() + timedelta(days=90)
        else:
            end_date = datetime.utcnow() + timedelta(days=365)

        # 创建或更新会员
        if user_id in self._memberships:
            membership = self._memberships[user_id]
            membership.tier = tier
            membership.status = "active"
            membership.billing_cycle = billing_cycle
            membership.end_date = end_date
            membership.tokens_remaining = plan.benefits.monthly_tokens
            membership.tokens_used_this_period = 0
            membership.next_billing_date = end_date
        else:
            membership = UserMembership(
                user_id=user_id,
                tier=tier,
                status="active",
                start_date=datetime.utcnow(),
                end_date=end_date,
                billing_cycle=billing_cycle,
                next_billing_date=end_date,
                tokens_remaining=plan.benefits.monthly_tokens
            )
            self._memberships[user_id] = membership

        # 记录支付
        payment = PaymentRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount_cny=price,
            payment_type="subscription",
            description=f"{plan.name} - {billing_cycle.value}",
            status="success",
            paid_at=datetime.utcnow()
        )
        self._payments.append(payment)

        return membership

    def purchase_tokens(self, user_id: str, package_id: str) -> PaymentRecord:
        """购买Token加油包"""
        package = next((p for p in TOKEN_PACKAGES if p.id == package_id), None)
        if not package:
            raise ValueError(f"Token package {package_id} not found")

        membership = self.get_membership(user_id)
        if not membership:
            raise ValueError("Membership not found")

        # 创建支付记录
        payment = PaymentRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount_cny=package.price_cny,
            payment_type="extra_tokens",
            description=f"Token包: {package.name}",
            status="pending",
            metadata={
                "package_id": package_id,
                "token_amount": package.token_amount + package.bonus_tokens
            }
        )
        self._payments.append(payment)

        # 模拟支付成功
        payment.status = "success"
        payment.paid_at = datetime.utcnow()

        # 增加用户token
        total_tokens = package.token_amount + package.bonus_tokens
        membership.extra_tokens_purchased += total_tokens
        membership.extra_tokens_remaining += total_tokens

        return payment

    def consume_tokens(self, user_id: str, amount: int) -> bool:
        """消费Token"""
        membership = self.get_membership(user_id)
        if not membership:
            return False

        if not membership.is_active():
            return False

        total_available = membership.get_total_available_tokens()
        if total_available < amount:
            return False

        # 先消费周期额度，再消费额外额度
        if membership.tokens_remaining >= amount:
            membership.tokens_remaining -= amount
        else:
            remaining = amount - membership.tokens_remaining
            membership.tokens_remaining = 0
            membership.extra_tokens_remaining -= remaining

        membership.tokens_used_this_period += amount

        return True

    def get_plan_details(self, tier: MembershipTier) -> Dict[str, Any]:
        """获取套餐详情"""
        plan = MEMBERSHIP_PLANS[tier]
        return {
            "tier": tier.value,
            "name": plan.name,
            "description": plan.description,
            "prices": {
                "monthly": plan.price_cny_monthly,
                "quarterly": plan.price_cny_quarterly,
                "yearly": plan.price_cny_yearly
            },
            "benefits": asdict(plan.benefits),
            "is_popular": plan.is_popular
        }

    def get_all_plans(self) -> List[Dict[str, Any]]:
        """获取所有套餐"""
        return [self.get_plan_details(tier) for tier in MembershipTier]

    def get_token_packages(self) -> List[Dict[str, Any]]:
        """获取Token加油包"""
        return [
            {
                "id": p.id,
                "name": p.name,
                "token_amount": p.token_amount,
                "bonus_tokens": p.bonus_tokens,
                "total_tokens": p.token_amount + p.bonus_tokens,
                "price_cny": p.price_cny,
                "validity_days": p.validity_days,
                "description": p.description
            }
            for p in TOKEN_PACKAGES
        ]

    def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """获取使用统计"""
        membership = self.get_membership(user_id)
        if not membership:
            return {}

        plan = MEMBERSHIP_PLANS[membership.tier]
        total_quota = plan.benefits.monthly_tokens + membership.extra_tokens_purchased

        return {
            "tier": membership.tier.value,
            "status": membership.status,
            "is_active": membership.is_active(),
            "period_start": membership.start_date.isoformat(),
            "period_end": membership.end_date.isoformat() if membership.end_date else None,
            "tokens": {
                "monthly_quota": plan.benefits.monthly_tokens,
                "monthly_remaining": membership.tokens_remaining,
                "extra_purchased": membership.extra_tokens_purchased,
                "extra_remaining": membership.extra_tokens_remaining,
                "used_this_period": membership.tokens_used_this_period,
                "total_available": membership.get_total_available_tokens()
            },
            "features": asdict(plan.benefits),
            "next_billing_date": membership.next_billing_date.isoformat() if membership.next_billing_date else None,
            "auto_renew": membership.auto_renew
        }

    def get_payment_history(self, user_id: str) -> List[Dict[str, Any]]:
        """获取支付历史"""
        payments = [p for p in self._payments if p.user_id == user_id]
        return [
            {
                "id": p.id,
                "amount_cny": p.amount_cny,
                "type": p.payment_type,
                "description": p.description,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
                "paid_at": p.paid_at.isoformat() if p.paid_at else None
            }
            for p in sorted(payments, key=lambda x: x.created_at, reverse=True)
        ]

    def check_feature_access(self, user_id: str, feature: str) -> bool:
        """检查功能访问权限"""
        membership = self.get_membership(user_id)
        if not membership or not membership.is_active():
            return False

        plan = MEMBERSHIP_PLANS[membership.tier]
        benefits = plan.benefits

        feature_map = {
            "vision": benefits.can_use_vision,
            "voice": benefits.can_use_voice,
            "video": benefits.can_use_video,
            "export": benefits.can_export,
            "collaborate": benefits.can_collaborate,
            "advanced_analysis": benefits.can_use_advanced_analysis
        }

        return feature_map.get(feature, False)


# 单例
_membership_service: Optional[MembershipService] = None


def get_membership_service() -> MembershipService:
    """获取会员服务单例"""
    global _membership_service
    if _membership_service is None:
        _membership_service = MembershipService()
    return _membership_service
