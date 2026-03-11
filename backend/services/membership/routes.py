"""
Membership API Routes
会员体系API路由 - 订阅管理、支付、配额查询
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from .service import get_membership_service
from .models import MembershipTier, BillingCycle

router = APIRouter(prefix="/membership", tags=["membership"])


# ==================== 请求/响应模型 ====================

class UpgradeRequest(BaseModel):
    """升级会员请求"""
    tier: str = Field(..., description="会员等级: trial/standard/pro/ultra")
    billing_cycle: str = Field("monthly", description="计费周期: monthly/quarterly/yearly")


class PurchaseTokensRequest(BaseModel):
    """购买Token请求"""
    package_id: str = Field(..., description="Token包ID")


class MembershipResponse(BaseModel):
    """会员信息响应"""
    tier: str
    status: str
    is_active: bool
    period_start: str
    period_end: Optional[str]
    tokens: dict
    features: dict
    next_billing_date: Optional[str]
    auto_renew: bool


class PlanResponse(BaseModel):
    """套餐信息响应"""
    tier: str
    name: str
    description: str
    prices: dict
    benefits: dict
    is_popular: bool


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== API端点 ====================

@router.get("/plans", response_model=List[PlanResponse])
async def get_membership_plans():
    """获取所有会员套餐"""
    service = get_membership_service()
    return service.get_all_plans()


@router.get("/current", response_model=MembershipResponse)
async def get_current_membership(user_id: str = Depends(get_current_user)):
    """获取当前用户会员信息"""
    service = get_membership_service()
    membership = service.get_membership(user_id)

    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    return service.get_usage_stats(user_id)


@router.post("/upgrade")
async def upgrade_membership(
    request: UpgradeRequest,
    user_id: str = Depends(get_current_user)
):
    """
    升级/订阅会员

    支持的会员等级:
    - trial: 免费试用 (14天)
    - standard: 标准版 (¥68/月)
    - pro: 专业版 (¥168/月)
    - ultra: 旗舰版 (¥488/月)
    """
    service = get_membership_service()

    try:
        tier = MembershipTier(request.tier)
        billing_cycle = BillingCycle(request.billing_cycle)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {e}")

    # 创建支付订单
    plan = service.get_plan_details(tier)
    price = plan["prices"][request.billing_cycle]

    # 执行升级
    membership = service.upgrade_membership(user_id, tier, billing_cycle)

    return {
        "message": "Membership upgraded successfully",
        "user_id": user_id,
        "tier": tier.value,
        "billing_cycle": billing_cycle.value,
        "amount_cny": price,
        "period_start": membership.start_date.isoformat(),
        "period_end": membership.end_date.isoformat() if membership.end_date else None,
        "tokens_remaining": membership.tokens_remaining
    }


@router.get("/tokens/packages")
async def get_token_packages():
    """获取Token加油包列表"""
    service = get_membership_service()
    return service.get_token_packages()


@router.post("/tokens/purchase")
async def purchase_tokens(
    request: PurchaseTokensRequest,
    user_id: str = Depends(get_current_user)
):
    """购买Token加油包"""
    service = get_membership_service()

    try:
        payment = service.purchase_tokens(user_id, request.package_id)
        return {
            "message": "Token purchase successful",
            "payment_id": payment.id,
            "amount_cny": payment.amount_cny,
            "tokens_added": payment.metadata.get("token_amount", 0),
            "status": payment.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usage")
async def get_usage_stats(user_id: str = Depends(get_current_user)):
    """获取用户使用统计"""
    service = get_membership_service()
    stats = service.get_usage_stats(user_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Membership not found")

    return stats


@router.get("/payments")
async def get_payment_history(user_id: str = Depends(get_current_user)):
    """获取支付历史"""
    service = get_membership_service()
    history = service.get_payment_history(user_id)

    return {
        "user_id": user_id,
        "total_payments": len(history),
        "payments": history
    }


@router.get("/check/{feature}")
async def check_feature_access(feature: str, user_id: str = Depends(get_current_user)):
    """
    检查功能访问权限

    功能列表:
    - vision: 视觉理解
    - voice: 语音功能
    - video: 视频生成
    - export: 导出功能
    - collaborate: 协作功能
    - advanced_analysis: 高级分析
    """
    service = get_membership_service()
    has_access = service.check_feature_access(user_id, feature)

    membership = service.get_membership(user_id)

    return {
        "user_id": user_id,
        "feature": feature,
        "has_access": has_access,
        "tier": membership.tier.value if membership else None
    }


@router.post("/cancel")
async def cancel_membership(user_id: str = Depends(get_current_user)):
    """取消订阅（不续费）"""
    service = get_membership_service()
    membership = service.get_membership(user_id)

    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    membership.auto_renew = False

    return {
        "message": "Membership cancelled successfully",
        "user_id": user_id,
        "current_tier": membership.tier.value,
        "period_end": membership.end_date.isoformat() if membership.end_date else None,
        "note": "You can still use the service until the end of current period"
    }


@router.post("/renew")
async def renew_membership(user_id: str = Depends(get_current_user)):
    """手动续费"""
    service = get_membership_service()
    membership = service.get_membership(user_id)

    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    # 执行续费
    new_membership = service.upgrade_membership(
        user_id,
        membership.tier,
        membership.billing_cycle
    )

    return {
        "message": "Membership renewed successfully",
        "user_id": user_id,
        "tier": new_membership.tier.value,
        "new_period_end": new_membership.end_date.isoformat() if new_membership.end_date else None
    }


@router.get("/comparison")
async def get_plan_comparison():
    """获取套餐对比表"""
    service = get_membership_service()
    plans = service.get_all_plans()

    # 提取关键对比字段
    comparison = {
        "tiers": [p["tier"] for p in plans],
        "names": [p["name"] for p in plans],
        "prices_monthly": [p["prices"]["monthly"] for p in plans],
        "features": {
            "monthly_tokens": [p["benefits"]["monthly_tokens"] for p in plans],
            "max_context_window": [p["benefits"]["max_context_window"] for p in plans],
            "storage_gb": [p["benefits"]["storage_gb"] for p in plans],
            "max_projects": [p["benefits"]["max_projects"] for p in plans],
            "max_papers": [p["benefits"]["max_papers"] for p in plans],
            "can_use_vision": [p["benefits"]["can_use_vision"] for p in plans],
            "can_use_voice": [p["benefits"]["can_use_voice"] for p in plans],
            "can_use_video": [p["benefits"]["can_use_video"] for p in plans],
            "can_collaborate": [p["benefits"]["can_collaborate"] for p in plans],
            "support_level": [p["benefits"]["support_level"] for p in plans]
        }
    }

    return comparison
