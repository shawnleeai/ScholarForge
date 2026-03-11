"""
Model Gateway API Routes
多模型API网关路由 - 统一接入、计费、配额管理
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime

from .unified_model_gateway import (
    get_unified_model_gateway,
    RoutingStrategy,
    TokenConsumption
)

router = APIRouter(prefix="/models", tags=["models"])


# ==================== 请求/响应模型 ====================

class ChatCompletionRequest(BaseModel):
    """聊天补全请求"""
    messages: List[Dict[str, str]] = Field(..., description="消息列表")
    model: Optional[str] = Field(None, description="指定模型，为空则自动选择")
    temperature: float = Field(0.7, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    stream: bool = Field(False, description="是否流式输出")
    strategy: str = Field("balanced", description="路由策略: cost_optimized/quality_first/speed_first/balanced")


class ModelInfoResponse(BaseModel):
    """模型信息响应"""
    id: str
    name: str
    provider: str
    capabilities: Dict[str, Any]
    pricing: Dict[str, float]
    is_available: bool


class ConsumptionRecord(BaseModel):
    """消费记录"""
    model_id: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    cost_cny: float
    timestamp: datetime


class ConsumptionStats(BaseModel):
    """消费统计"""
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    total_cost_cny: float
    by_model: Dict[str, Dict[str, Any]]


class UserQuotaInfo(BaseModel):
    """用户配额信息"""
    user_id: str
    membership_tier: str
    total_quota: int
    used_quota: int
    remaining_quota: int
    reset_date: datetime
    usage_percentage: float


# ==================== 依赖注入 ====================

async def get_current_user(request: Request) -> str:
    """获取当前用户ID (简化版，实际应从JWT解析)"""
    return request.headers.get("X-User-ID", "anonymous")


# ==================== API端点 ====================

@router.get("/available", response_model=List[ModelInfoResponse])
async def get_available_models():
    """获取所有可用模型列表"""
    gateway = get_unified_model_gateway()
    models = gateway.get_available_models()
    return models


@router.post("/chat/completions")
async def chat_completion(
    request: ChatCompletionRequest,
    user_id: str = Depends(get_current_user)
):
    """
    统一聊天补全接口

    - 自动选择最佳模型（根据策略）
    - 支持指定模型
    - 自动记录token消费
    """
    gateway = get_unified_model_gateway()

    try:
        strategy = RoutingStrategy(request.strategy)
    except ValueError:
        strategy = RoutingStrategy.BALANCED

    try:
        if request.stream:
            # 流式响应
            async def generate_stream():
                async for chunk in gateway.chat_completion_stream(
                    messages=request.messages,
                    user_id=user_id,
                    model_id=request.model,
                    strategy=strategy,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ):
                    if chunk["type"] == "content":
                        yield f"data: {chunk['content']}\n\n"
                    elif chunk["type"] == "done":
                        yield "data: [DONE]\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream"
            )
        else:
            # 非流式响应
            result = await gateway.chat_completion(
                messages=request.messages,
                user_id=user_id,
                model_id=request.model,
                strategy=strategy,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False
            )

            return {
                "id": f"chatcmpl-{hash(str(request.messages)) % 1000000}",
                "object": "chat.completion",
                "created": int(datetime.utcnow().timestamp()),
                "model": result["_routing"]["model"],
                "choices": result.get("choices", []),
                "usage": result.get("usage", {}),
                "_routing": result["_routing"]
            }

    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {str(e)}")


@router.get("/consumption", response_model=ConsumptionStats)
async def get_user_consumption(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: str = Depends(get_current_user)
):
    """获取用户消费统计"""
    gateway = get_unified_model_gateway()
    stats = gateway.get_user_consumption(user_id, start_date, end_date)
    return ConsumptionStats(**stats)


@router.get("/quota", response_model=UserQuotaInfo)
async def get_user_quota(user_id: str = Depends(get_current_user)):
    """获取用户当前配额信息"""
    gateway = get_unified_model_gateway()
    quota = gateway.user_quotas.get(user_id)

    if not quota:
        # 返回默认配额
        return UserQuotaInfo(
            user_id=user_id,
            membership_tier="trial",
            total_quota=100000,
            used_quota=0,
            remaining_quota=100000,
            reset_date=datetime.utcnow(),
            usage_percentage=0.0
        )

    usage_percentage = (quota.used_quota / quota.total_quota * 100) if quota.total_quota > 0 else 0

    return UserQuotaInfo(
        user_id=quota.user_id,
        membership_tier=quota.membership_tier,
        total_quota=quota.total_quota,
        used_quota=quota.used_quota,
        remaining_quota=quota.remaining_quota,
        reset_date=quota.reset_date,
        usage_percentage=round(usage_percentage, 2)
    )


@router.post("/quota/{user_id}")
async def set_user_quota(
    user_id: str,
    membership_tier: str,
    total_quota: int,
    admin_key: str
):
    """
    设置用户配额（管理接口）

    - membership_tier: trial/standard/pro/ultra
    - total_quota: token配额数量
    """
    # 简化验证，实际应该使用管理员认证
    if admin_key != "admin_secret_key":
        raise HTTPException(status_code=403, detail="Unauthorized")

    gateway = get_unified_model_gateway()
    gateway.set_user_quota(user_id, membership_tier, total_quota)

    return {
        "message": "Quota updated successfully",
        "user_id": user_id,
        "membership_tier": membership_tier,
        "total_quota": total_quota
    }


@router.get("/health")
async def get_provider_health():
    """获取各提供商健康状态"""
    gateway = get_unified_model_gateway()
    health = gateway.get_provider_health()
    return {"providers": health}


@router.get("/strategies")
async def get_routing_strategies():
    """获取可用路由策略说明"""
    return {
        "strategies": [
            {
                "id": "cost_optimized",
                "name": "成本优先",
                "description": "选择价格最低的可用模型"
            },
            {
                "id": "quality_first",
                "name": "质量优先",
                "description": "选择性能最好的模型（GPT-4、Step-1等）"
            },
            {
                "id": "speed_first",
                "name": "速度优先",
                "description": "选择响应速度最快的模型"
            },
            {
                "id": "balanced",
                "name": "平衡模式",
                "description": "综合考虑价格、质量、速度"
            },
            {
                "id": "user_preference",
                "name": "用户偏好",
                "description": "根据用户会员等级推荐合适模型"
            }
        ]
    }


@router.post("/compare")
async def compare_models(
    prompt: str,
    models: List[str],
    user_id: str = Depends(get_current_user)
):
    """
    模型对比测试

    同时在多个模型上运行相同提示词，对比结果
    """
    gateway = get_unified_model_gateway()

    if len(models) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 models for comparison")

    results = []
    for model_id in models:
        try:
            result = await gateway.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                user_id=user_id,
                model_id=model_id,
                stream=False
            )

            results.append({
                "model": model_id,
                "content": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "routing": result.get("_routing", {})
            })
        except Exception as e:
            results.append({
                "model": model_id,
                "error": str(e)
            })

    return {
        "prompt": prompt,
        "comparisons": results
    }
