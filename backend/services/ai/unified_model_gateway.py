"""
Unified Model Gateway
多模型API统一接入层 - 支持多提供商智能路由、负载均衡、计费追踪
"""

import asyncio
import json
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any, AsyncGenerator, Callable, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import random

import httpx


class ProviderType(str, Enum):
    """提供商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    MOONSHOT = "moonshot"
    STEPFUN = "stepfun"
    AZURE = "azure"
    ZHIPU = "zhipu"
    BAICHUAN = "baichuan"


class RoutingStrategy(str, Enum):
    """路由策略"""
    COST_OPTIMIZED = "cost_optimized"      # 成本优化
    QUALITY_FIRST = "quality_first"         # 质量优先
    SPEED_FIRST = "speed_first"             # 速度优先
    BALANCED = "balanced"                   # 平衡模式
    FALLBACK = "fallback"                   # 故障转移
    USER_PREFERENCE = "user_preference"     # 用户偏好


@dataclass
class ModelCapability:
    """模型能力"""
    supports_chat: bool = True
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_streaming: bool = True
    supports_json_mode: bool = False
    max_tokens: int = 4096
    context_window: int = 4096
    languages: List[str] = field(default_factory=lambda: ["en", "zh"])


@dataclass
class ModelInfo:
    """模型信息"""
    id: str
    name: str
    provider: ProviderType
    capabilities: ModelCapability
    pricing_input: float = 0.0      # 每1K tokens输入价格(美元)
    pricing_output: float = 0.0     # 每1K tokens输出价格(美元)
    is_available: bool = True
    priority: int = 5               # 优先级 1-10


@dataclass
class TokenConsumption:
    """Token消费记录"""
    user_id: str
    model_id: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    cost_cny: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    request_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserQuota:
    """用户配额"""
    user_id: str
    membership_tier: str          # trial/standard/pro/ultra
    total_quota: int              # 总token配额
    used_quota: int               # 已使用配额
    remaining_quota: int          # 剩余配额
    reset_date: datetime          # 重置日期
    extra_purchased: int = 0      # 额外购买额度


class ProviderInterface(ABC):
    """提供商接口抽象基类"""

    def __init__(self, provider_type: ProviderType, api_key: str, base_url: Optional[str] = None):
        self.provider_type = provider_type
        self.api_key = api_key
        self.base_url = base_url
        self.is_healthy = True
        self.last_error: Optional[str] = None
        self.request_count = 0
        self.error_count = 0
        self.avg_latency_ms = 0.0

    @abstractmethod
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """聊天补全"""
        pass

    @abstractmethod
    async def chat_completion_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天补全"""
        pass

    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """计算token数量"""
        pass

    def record_latency(self, latency_ms: float):
        """记录延迟"""
        self.avg_latency_ms = (self.avg_latency_ms * self.request_count + latency_ms) / (self.request_count + 1)
        self.request_count += 1

    def record_error(self, error: str):
        """记录错误"""
        self.error_count += 1
        self.last_error = error
        error_rate = self.error_count / max(self.request_count, 1)
        if error_rate > 0.2:  # 错误率超过20%
            self.is_healthy = False


class OpenAICompatibleProvider(ProviderInterface):
    """OpenAI兼容格式提供商基类"""

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if kwargs.get("response_format"):
            payload["response_format"] = kwargs["response_format"]

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                latency_ms = (time.time() - start_time) * 1000
                self.record_latency(latency_ms)

                return response.json()
            except Exception as e:
                self.record_error(str(e))
                raise

    async def chat_completion_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue

    def count_tokens(self, text: str, model: str) -> int:
        """简单估算token数量"""
        return len(text) // 4  # 粗略估算


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI提供商"""

    def __init__(self, api_key: str):
        super().__init__(ProviderType.OPENAI, api_key, "https://api.openai.com/v1")


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek提供商"""

    def __init__(self, api_key: str):
        super().__init__(ProviderType.DEEPSEEK, api_key, "https://api.deepseek.com/v1")


class MoonshotProvider(OpenAICompatibleProvider):
    """Moonshot(Kimi)提供商"""

    def __init__(self, api_key: str):
        super().__init__(ProviderType.MOONSHOT, api_key, "https://api.moonshot.cn/v1")


class ZhipuProvider(OpenAICompatibleProvider):
    """智谱AI提供商"""

    def __init__(self, api_key: str):
        super().__init__(ProviderType.ZHIPU, api_key, "https://open.bigmodel.cn/api/paas/v4")


class StepFunProvider(ProviderInterface):
    """阶跃星辰提供商 - 支持多模态"""

    def __init__(self, api_key: str):
        super().__init__(ProviderType.STEPFUN, api_key, "https://api.stepfun.com/v1")

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        # 复用现有的stepfun_client逻辑
        from .stepfun_client import get_stepfun_client

        stepfun = get_stepfun_client()
        start_time = time.time()

        try:
            result = await stepfun.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )

            latency_ms = (time.time() - start_time) * 1000
            self.record_latency(latency_ms)

            return result
        except Exception as e:
            self.record_error(str(e))
            raise

    async def chat_completion_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        from .stepfun_client import get_stepfun_client

        stepfun = get_stepfun_client()

        async for chunk in stepfun.chat_completion_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield chunk

    def count_tokens(self, text: str, model: str) -> int:
        return len(text) // 3  # 中文token估算


class ModelRegistry:
    """模型注册表"""

    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._provider_models: Dict[ProviderType, List[str]] = defaultdict(list)

        self._register_default_models()

    def _register_default_models(self):
        """注册默认模型"""
        # OpenAI 模型
        self.register(ModelInfo(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            provider=ProviderType.OPENAI,
            capabilities=ModelCapability(
                context_window=128000,
                max_tokens=4096,
                supports_vision=True,
                supports_function_calling=True,
                supports_json_mode=True
            ),
            pricing_input=0.01,
            pricing_output=0.03,
            priority=9
        ))

        self.register(ModelInfo(
            id="gpt-4o",
            name="GPT-4o",
            provider=ProviderType.OPENAI,
            capabilities=ModelCapability(
                context_window=128000,
                max_tokens=4096,
                supports_vision=True,
                supports_function_calling=True,
                supports_json_mode=True
            ),
            pricing_input=0.005,
            pricing_output=0.015,
            priority=10
        ))

        self.register(ModelInfo(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            provider=ProviderType.OPENAI,
            capabilities=ModelCapability(
                context_window=16385,
                max_tokens=4096,
                supports_function_calling=True
            ),
            pricing_input=0.0005,
            pricing_output=0.0015,
            priority=7
        ))

        # DeepSeek 模型
        self.register(ModelInfo(
            id="deepseek-chat",
            name="DeepSeek Chat",
            provider=ProviderType.DEEPSEEK,
            capabilities=ModelCapability(
                context_window=32768,
                max_tokens=4096
            ),
            pricing_input=0.00014,
            pricing_output=0.00028,
            priority=8
        ))

        self.register(ModelInfo(
            id="deepseek-coder",
            name="DeepSeek Coder",
            provider=ProviderType.DEEPSEEK,
            capabilities=ModelCapability(
                context_window=16384,
                max_tokens=4096
            ),
            pricing_input=0.00014,
            pricing_output=0.00028,
            priority=7
        ))

        # Moonshot 模型
        self.register(ModelInfo(
            id="moonshot-v1-8k",
            name="Moonshot 8K",
            provider=ProviderType.MOONSHOT,
            capabilities=ModelCapability(
                context_window=8192,
                max_tokens=4096
            ),
            pricing_input=0.0007,
            pricing_output=0.0007,
            priority=6
        ))

        self.register(ModelInfo(
            id="moonshot-v1-128k",
            name="Moonshot 128K",
            provider=ProviderType.MOONSHOT,
            capabilities=ModelCapability(
                context_window=131072,
                max_tokens=4096
            ),
            pricing_input=0.0035,
            pricing_output=0.0035,
            priority=6
        ))

        # 阶跃星辰模型
        self.register(ModelInfo(
            id="step-1-32k",
            name="Step-1 32K",
            provider=ProviderType.STEPFUN,
            capabilities=ModelCapability(
                context_window=32000,
                max_tokens=4096
            ),
            pricing_input=0.002,
            pricing_output=0.006,
            priority=8
        ))

        self.register(ModelInfo(
            id="step-1-128k",
            name="Step-1 128K",
            provider=ProviderType.STEPFUN,
            capabilities=ModelCapability(
                context_window=131072,
                max_tokens=4096
            ),
            pricing_input=0.007,
            pricing_output=0.021,
            priority=9
        ))

        self.register(ModelInfo(
            id="step-1-256k",
            name="Step-1 256K",
            provider=ProviderType.STEPFUN,
            capabilities=ModelCapability(
                context_window=262144,
                max_tokens=4096
            ),
            pricing_input=0.015,
            pricing_output=0.045,
            priority=8
        ))

        self.register(ModelInfo(
            id="step-1o",
            name="Step-1o (Vision)",
            provider=ProviderType.STEPFUN,
            capabilities=ModelCapability(
                context_window=32000,
                max_tokens=4096,
                supports_vision=True
            ),
            pricing_input=0.008,
            pricing_output=0.024,
            priority=9
        ))

        # 智谱AI模型
        self.register(ModelInfo(
            id="glm-4",
            name="GLM-4",
            provider=ProviderType.ZHIPU,
            capabilities=ModelCapability(
                context_window=131072,
                max_tokens=4096,
                supports_function_calling=True
            ),
            pricing_input=0.001,
            pricing_output=0.001,
            priority=7
        ))

    def register(self, model: ModelInfo):
        """注册模型"""
        self._models[model.id] = model
        self._provider_models[model.provider].append(model.id)

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        return self._models.get(model_id)

    def get_models_by_provider(self, provider: ProviderType) -> List[ModelInfo]:
        """获取提供商的所有模型"""
        model_ids = self._provider_models.get(provider, [])
        return [self._models[mid] for mid in model_ids if mid in self._models]

    def get_all_models(self) -> List[ModelInfo]:
        """获取所有模型"""
        return list(self._models.values())

    def find_models_by_capability(self, **capabilities) -> List[ModelInfo]:
        """按能力查找模型"""
        results = []
        for model in self._models.values():
            caps = model.capabilities
            match = all(
                getattr(caps, cap, False) == value
                for cap, value in capabilities.items()
            )
            if match:
                results.append(model)
        return results


class ProviderFactory:
    """提供商工厂"""

    _providers: Dict[ProviderType, type] = {
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.DEEPSEEK: DeepSeekProvider,
        ProviderType.MOONSHOT: MoonshotProvider,
        ProviderType.ZHIPU: ZhipuProvider,
        ProviderType.STEPFUN: StepFunProvider,
    }

    @classmethod
    def create(cls, provider_type: ProviderType, api_key: str) -> ProviderInterface:
        """创建提供商实例"""
        provider_class = cls._providers.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider_type}")
        return provider_class(api_key)

    @classmethod
    def register(cls, provider_type: ProviderType, provider_class: type):
        """注册新的提供商类型"""
        cls._providers[provider_type] = provider_class


class UnifiedModelGateway:
    """
    统一模型网关
    - 多提供商接入
    - 智能路由
    - 负载均衡
    - 计费追踪
    """

    # 汇率
    USD_TO_CNY = 7.2

    def __init__(self):
        self.registry = ModelRegistry()
        self.providers: Dict[ProviderType, ProviderInterface] = {}
        self.consumption_history: List[TokenConsumption] = []
        self.user_quotas: Dict[str, UserQuota] = {}
        self.default_strategy = RoutingStrategy.BALANCED

        # 初始化提供商
        self._init_providers()

    def _init_providers(self):
        """初始化提供商"""
        import os

        api_keys = {
            ProviderType.OPENAI: os.getenv("OPENAI_API_KEY", ""),
            ProviderType.DEEPSEEK: os.getenv("DEEPSEEK_API_KEY", ""),
            ProviderType.MOONSHOT: os.getenv("MOONSHOT_API_KEY", ""),
            ProviderType.ZHIPU: os.getenv("ZHIPU_API_KEY", ""),
            ProviderType.STEPFUN: os.getenv("STEPFUN_API_KEY", ""),
        }

        for provider_type, api_key in api_keys.items():
            if api_key:
                try:
                    self.providers[provider_type] = ProviderFactory.create(
                        provider_type, api_key
                    )
                except Exception as e:
                    print(f"Failed to initialize {provider_type}: {e}")

    def _calculate_cost(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> Tuple[float, float]:
        """计算成本 (USD, CNY)"""
        model = self.registry.get_model(model_id)
        if not model:
            return 0.0, 0.0

        input_cost = (prompt_tokens / 1000) * model.pricing_input
        output_cost = (completion_tokens / 1000) * model.pricing_output
        total_usd = input_cost + output_cost
        total_cny = total_usd * self.USD_TO_CNY

        return total_usd, total_cny

    def _select_provider(
        self,
        model_id: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        user_tier: str = "standard",
        required_capabilities: Optional[Dict[str, bool]] = None
    ) -> Tuple[ProviderType, str]:
        """
        选择最佳提供商和模型
        返回: (provider_type, model_id)
        """
        # 如果指定了模型，直接使用
        if model_id:
            model = self.registry.get_model(model_id)
            if model and model.is_available:
                return model.provider, model_id

        # 根据策略选择
        available_models = self.registry.get_all_models()

        # 过滤健康状态的提供商
        available_models = [
            m for m in available_models
            if m.provider in self.providers and self.providers[m.provider].is_healthy
        ]

        # 过滤必需能力
        if required_capabilities:
            available_models = [
                m for m in available_models
                if all(
                    getattr(m.capabilities, cap, False) == value
                    for cap, value in required_capabilities.items()
                )
            ]

        if not available_models:
            raise ValueError("No available models matching criteria")

        # 应用策略
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            # 选择最便宜的
            selected = min(available_models, key=lambda m: m.pricing_input + m.pricing_output)
        elif strategy == RoutingStrategy.QUALITY_FIRST:
            # 选择优先级最高的
            selected = max(available_models, key=lambda m: m.priority)
        elif strategy == RoutingStrategy.SPEED_FIRST:
            # 选择延迟最低的
            selected = min(
                available_models,
                key=lambda m: self.providers[m.provider].avg_latency_ms or 9999
            )
        elif strategy == RoutingStrategy.USER_PREFERENCE:
            # 根据用户等级选择
            tier_preferences = {
                "trial": ["gpt-3.5-turbo", "deepseek-chat"],
                "standard": ["gpt-4o", "step-1-128k", "moonshot-v1-8k"],
                "pro": ["gpt-4-turbo", "step-1-128k", "step-1o"],
                "ultra": ["gpt-4-turbo", "step-1-256k"]
            }
            preferences = tier_preferences.get(user_tier, tier_preferences["standard"])

            for pref_id in preferences:
                model = self.registry.get_model(pref_id)
                if model and model in available_models:
                    selected = model
                    break
            else:
                selected = available_models[0]
        else:  # BALANCED
            # 综合考虑价格和质量
            def score(m: ModelInfo) -> float:
                cost_score = 1 / (m.pricing_input + m.pricing_output + 0.001)
                quality_score = m.priority
                latency = self.providers[m.provider].avg_latency_ms or 1000
                speed_score = 1000 / (latency + 1)
                return quality_score * 0.4 + cost_score * 0.3 + speed_score * 0.3

            selected = max(available_models, key=score)

        return selected.provider, selected.id

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        model_id: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        track_consumption: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        统一聊天补全接口
        """
        # 检查用户配额
        if track_consumption:
            quota = self.user_quotas.get(user_id)
            if quota and quota.remaining_quota <= 0:
                raise ValueError("Token quota exceeded")

        # 获取用户等级
        user_tier = "standard"
        if quota:
            user_tier = quota.membership_tier

        # 选择提供商和模型
        provider_type, selected_model = self._select_provider(
            model_id=model_id,
            strategy=strategy,
            user_tier=user_tier
        )

        provider = self.providers.get(provider_type)
        if not provider:
            raise ValueError(f"Provider {provider_type} not available")

        # 执行请求
        start_time = time.time()
        result = await provider.chat_completion(
            model=selected_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )
        latency_ms = (time.time() - start_time) * 1000

        # 记录消费
        if track_consumption:
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

            cost_usd, cost_cny = self._calculate_cost(
                selected_model, prompt_tokens, completion_tokens
            )

            consumption = TokenConsumption(
                user_id=user_id,
                model_id=selected_model,
                provider=provider_type.value,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                cost_cny=cost_cny,
                request_id=hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()[:16]
            )

            self.consumption_history.append(consumption)

            # 更新用户配额
            if quota:
                quota.used_quota += total_tokens
                quota.remaining_quota -= total_tokens

        # 添加路由信息到结果
        result["_routing"] = {
            "provider": provider_type.value,
            "model": selected_model,
            "latency_ms": latency_ms,
            "strategy": strategy.value
        }

        return result

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        model_id: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        track_consumption: bool = True,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        统一流式聊天补全接口
        """
        user_tier = "standard"
        quota = self.user_quotas.get(user_id)
        if quota:
            user_tier = quota.membership_tier

        provider_type, selected_model = self._select_provider(
            model_id=model_id,
            strategy=strategy,
            user_tier=user_tier
        )

        provider = self.providers.get(provider_type)
        if not provider:
            raise ValueError(f"Provider {provider_type} not available")

        # 发送路由信息
        yield {
            "type": "routing",
            "provider": provider_type.value,
            "model": selected_model
        }

        # 流式生成
        content_buffer = []
        async for chunk in provider.chat_completion_stream(
            model=selected_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        ):
            content_buffer.append(chunk)
            yield {
                "type": "content",
                "content": chunk
            }

        # 发送完成事件
        yield {"type": "done"}

        # 记录消费（流式请求估算）
        if track_consumption:
            full_content = "".join(content_buffer)
            estimated_tokens = len(full_content) // 3

            cost_usd, cost_cny = self._calculate_cost(
                selected_model, len(messages) * 50, estimated_tokens
            )

            consumption = TokenConsumption(
                user_id=user_id,
                model_id=selected_model,
                provider=provider_type.value,
                prompt_tokens=len(messages) * 50,
                completion_tokens=estimated_tokens,
                total_tokens=len(messages) * 50 + estimated_tokens,
                cost_usd=cost_usd,
                cost_cny=cost_cny
            )

            self.consumption_history.append(consumption)

    def get_user_consumption(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取用户消费统计"""
        records = [
            c for c in self.consumption_history
            if c.user_id == user_id
            and (not start_date or c.timestamp >= start_date)
            and (not end_date or c.timestamp <= end_date)
        ]

        total_tokens = sum(r.total_tokens for r in records)
        total_cost_usd = sum(r.cost_usd for r in records)
        total_cost_cny = sum(r.cost_cny for r in records)

        by_model = defaultdict(lambda: {"tokens": 0, "cost_usd": 0})
        for r in records:
            by_model[r.model_id]["tokens"] += r.total_tokens
            by_model[r.model_id]["cost_usd"] += r.cost_usd

        return {
            "total_requests": len(records),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 4),
            "total_cost_cny": round(total_cost_cny, 4),
            "by_model": dict(by_model)
        }

    def set_user_quota(
        self,
        user_id: str,
        membership_tier: str,
        total_quota: int,
        reset_date: Optional[datetime] = None
    ):
        """设置用户配额"""
        if reset_date is None:
            reset_date = datetime.utcnow() + timedelta(days=30)

        self.user_quotas[user_id] = UserQuota(
            user_id=user_id,
            membership_tier=membership_tier,
            total_quota=total_quota,
            used_quota=0,
            remaining_quota=total_quota,
            reset_date=reset_date
        )

    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取所有可用模型"""
        models = self.registry.get_all_models()
        return [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider.value,
                "capabilities": asdict(m.capabilities),
                "pricing": {
                    "input": m.pricing_input,
                    "output": m.pricing_output
                },
                "is_available": m.is_available and m.provider in self.providers
            }
            for m in models
        ]

    def get_provider_health(self) -> List[Dict[str, Any]]:
        """获取提供商健康状态"""
        health = []
        for provider_type, provider in self.providers.items():
            health.append({
                "provider": provider_type.value,
                "is_healthy": provider.is_healthy,
                "avg_latency_ms": round(provider.avg_latency_ms, 2),
                "request_count": provider.request_count,
                "error_count": provider.error_count,
                "error_rate": round(
                    provider.error_count / max(provider.request_count, 1), 4
                ),
                "last_error": provider.last_error
            })
        return health


# 单例
_unified_gateway: Optional[UnifiedModelGateway] = None


def get_unified_model_gateway() -> UnifiedModelGateway:
    """获取统一模型网关单例"""
    global _unified_gateway
    if _unified_gateway is None:
        _unified_gateway = UnifiedModelGateway()
    return _unified_gateway
