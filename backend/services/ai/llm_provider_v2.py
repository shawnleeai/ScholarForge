"""
LLM 提供商增强版
支持流式响应、Token统计、健康检查、成本估算
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, AsyncGenerator, Callable
from datetime import datetime

import httpx


class ProviderStatus(Enum):
    """提供商状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    NO_API_KEY = "no_api_key"


@dataclass
class TokenUsage:
    """Token 使用情况"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: 'TokenUsage'):
        """累加 Token 使用"""
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens


@dataclass
class GenerationResult:
    """生成结果"""
    content: str
    provider: str
    model: str
    usage: TokenUsage
    latency_ms: float
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict] = None


@dataclass
class ProviderHealth:
    """提供商健康状态"""
    provider: str
    status: ProviderStatus
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_checked: datetime = field(default_factory=datetime.now)
    supported_models: List[str] = field(default_factory=list)


class BaseLLMProvider(ABC):
    """LLM 提供商基类（增强版）"""

    # 模型价格配置 (每 1K tokens 的美元价格)
    PRICING = {
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.api_key = api_key
        self.model = model or self.default_model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._usage_stats: List[TokenUsage] = []

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商名称"""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """默认模型"""
        pass

    @property
    def has_valid_key(self) -> bool:
        """是否有有效的 API Key"""
        return self.api_key is not None and len(self.api_key) > 10

    def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> GenerationResult:
        """生成文本"""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> GenerationResult:
        """对话生成"""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealth:
        """检查提供商健康状态"""
        pass

    def estimate_cost(self, usage: TokenUsage) -> float:
        """估算成本（美元）"""
        model_pricing = self.PRICING.get(self.model, {"input": 0.01, "output": 0.03})
        input_cost = (usage.prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1000) * model_pricing["output"]
        return round(input_cost + output_cost, 6)

    def record_usage(self, usage: TokenUsage):
        """记录 Token 使用"""
        self._usage_stats.append(usage)
        # 保留最近 1000 条记录
        if len(self._usage_stats) > 1000:
            self._usage_stats = self._usage_stats[-1000:]

    def get_total_usage(self) -> TokenUsage:
        """获取总 Token 使用量"""
        total = TokenUsage()
        for usage in self._usage_stats:
            total.add(usage)
        return total

    def get_total_cost(self) -> float:
        """获取总成本"""
        return sum(self.estimate_cost(u) for u in self._usage_stats)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI 提供商（增强版）"""

    BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
        timeout: float = 60.0,
    ):
        super().__init__(api_key, model, timeout)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return "gpt-4-turbo-preview"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> GenerationResult:
        """生成文本"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, max_tokens, temperature)

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.has_valid_key:
            yield self._mock_response(prompt)
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        try:
            client = self._get_client()
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n[错误: {str(e)}]"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> GenerationResult:
        """对话生成"""
        start_time = time.time()

        if not self.has_valid_key:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content=self._mock_response(messages[-1]["content"] if messages else ""),
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="mock",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            client = self._get_client()
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            latency = (time.time() - start_time) * 1000

            usage_data = data.get("usage", {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )
            self.record_usage(usage)

            return GenerationResult(
                content=data["choices"][0]["message"]["content"],
                provider=self.provider_name,
                model=self.model,
                usage=usage,
                latency_ms=latency,
                finish_reason=data["choices"][0].get("finish_reason"),
                raw_response=data,
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content=f"调用 OpenAI API 失败: {str(e)}\n\n请检查 API Key 是否正确，或稍后重试。",
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="error",
            )

    async def check_health(self) -> ProviderHealth:
        """检查 OpenAI 服务健康状态"""
        if not self.has_valid_key:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.NO_API_KEY,
                error_message="未配置 API Key",
            )

        start_time = time.time()
        try:
            client = self._get_client()
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                models = [m["id"] for m in data.get("data", [])]
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    supported_models=models[:10],  # 只返回前10个
                )
            else:
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.DEGRADED,
                    latency_ms=latency,
                    error_message=f"API 返回状态码: {response.status_code}",
                )

        except Exception as e:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=str(e),
            )

    def _mock_response(self, prompt: str) -> str:
        """模拟响应（用于开发测试）"""
        prompt_lower = prompt.lower()
        if "续写" in prompt or "continue" in prompt_lower:
            return (
                "基于上述研究背景，本研究将采用混合研究方法，"
                "结合定量分析与案例研究，深入探讨该领域的关键因素。"
                "研究将分为三个阶段：首先通过文献综述梳理理论框架；"
                "其次设计问卷收集实证数据；最后通过案例分析验证研究假设。"
            )
        elif "润色" in prompt or "polish" in prompt_lower:
            return (
                "本研究采用混合研究方法，将定量分析与案例研究有机结合，"
                "系统性地探究核心影响因素。研究设计涵盖三个递进阶段："
                "理论框架构建、实证数据采集与假设验证。"
            )
        elif "翻译" in prompt or "translate" in prompt_lower:
            return (
                "This study employs a mixed-methods approach, combining quantitative "
                "analysis with case studies to systematically investigate the key factors."
            )
        elif "摘要" in prompt or "abstract" in prompt_lower:
            return (
                "本研究旨在探讨...通过...方法，研究发现..."
                "研究结论对...领域具有重要理论和实践意义。"
            )
        else:
            return (
                "[模拟响应] 这是一个用于开发的模拟响应。"
                "在实际部署时，请配置有效的 OpenAI API Key 以获得真实 AI 能力。"
            )


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude 提供商（增强版）"""

    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-opus-20240229",
        timeout: float = 60.0,
    ):
        super().__init__(api_key, model, timeout)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return "claude-3-opus-20240229"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> GenerationResult:
        """生成文本"""
        start_time = time.time()

        if not self.has_valid_key:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content=self._mock_response(prompt),
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="mock",
            )

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            client = self._get_client()
            response = await client.post(
                f"{self.BASE_URL}/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            latency = (time.time() - start_time) * 1000

            usage_data = data.get("usage", {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get("input_tokens", 0),
                completion_tokens=usage_data.get("output_tokens", 0),
                total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
            )
            self.record_usage(usage)

            return GenerationResult(
                content=data["content"][0]["text"],
                provider=self.provider_name,
                model=self.model,
                usage=usage,
                latency_ms=latency,
                finish_reason=data.get("stop_reason"),
                raw_response=data,
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content=f"调用 Claude API 失败: {str(e)}\n\n请检查 API Key 是否正确，或稍后重试。",
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="error",
            )

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.has_valid_key:
            yield self._mock_response(prompt)
            return

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            client = self._get_client()
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/messages",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            event = json.loads(data)
                            if event.get("type") == "content_block_delta":
                                if "delta" in event and "text" in event["delta"]:
                                    yield event["delta"]["text"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n[错误: {str(e)}]"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> GenerationResult:
        """对话生成"""
        # 将 OpenAI 格式转换为 Claude 格式
        prompt_parts = []
        for msg in messages:
            role = "Human" if msg["role"] == "user" else "Assistant"
            prompt_parts.append(f"{role}: {msg['content']}")
        prompt_parts.append("Human:")

        prompt = "\n\n".join(prompt_parts)

        # 提取系统提示
        system_prompt = None
        if messages and messages[0]["role"] == "system":
            system_prompt = messages[0]["content"]

        return await self.generate(prompt, max_tokens, temperature, system_prompt)

    async def check_health(self) -> ProviderHealth:
        """检查 Claude 服务健康状态"""
        if not self.has_valid_key:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.NO_API_KEY,
                error_message="未配置 API Key",
            )

        start_time = time.time()
        try:
            # 通过简单请求检查健康状态
            result = await self.generate("Hi", max_tokens=10)
            latency = (time.time() - start_time) * 1000

            if result.finish_reason != "error":
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    supported_models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                )
            else:
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.UNAVAILABLE,
                    latency_ms=latency,
                    error_message="API 请求失败",
                )

        except Exception as e:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=str(e),
            )

    def _mock_response(self, prompt: str) -> str:
        """模拟响应"""
        return (
            "[Claude 模拟响应] 作为学术写作助手，我建议您：\n\n"
            "1. **明确研究问题**：确保研究问题具体、可回答\n"
            "2. **文献综述完整**：系统回顾相关研究，找到研究空白\n"
            "3. **方法论严谨**：选择适合的研究方法，详细说明数据收集和分析过程\n"
            "4. **结果讨论深入**：不仅报告结果，还要解释其意义和局限性\n\n"
            "在实际使用时，请配置 Anthropic API Key 以获得 Claude 的真实能力。"
        )


class LLMService:
    """LLM 服务统一接口（增强版）"""

    def __init__(
        self,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        deepseek_key: Optional[str] = None,
        moonshot_key: Optional[str] = None,
        stepfun_key: Optional[str] = None,
        default_provider: str = "openai",
        fallback_enabled: bool = True,
    ):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.fallback_enabled = fallback_enabled
        self._default_provider = default_provider

        # 初始化提供商
        if openai_key:
            self.providers["openai"] = OpenAIProvider(api_key=openai_key)
        if anthropic_key:
            self.providers["anthropic"] = AnthropicProvider(api_key=anthropic_key)
        if deepseek_key:
            self.providers["deepseek"] = DeepSeekProvider(api_key=deepseek_key)
        if moonshot_key:
            self.providers["moonshot"] = MoonshotAIProvider(api_key=moonshot_key)
        if stepfun_key:
            self.providers["stepfun"] = StepFunProvider(api_key=stepfun_key)

    @property
    def default_provider(self) -> str:
        """获取默认提供商"""
        if self._default_provider in self.providers:
            return self._default_provider
        return next(iter(self.providers.keys())) if self.providers else "openai"

    def get_provider(self, provider_name: Optional[str] = None) -> Optional[BaseLLMProvider]:
        """获取提供商"""
        name = provider_name or self.default_provider
        return self.providers.get(name)

    def get_available_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        return [name for name, provider in self.providers.items() if provider.has_valid_key]

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> GenerationResult:
        """
        生成文本，支持故障转移

        Returns:
            GenerationResult: 包含生成内容、使用的提供商、Token使用量等信息
        """
        target_provider = provider or self.default_provider
        p = self.get_provider(target_provider)

        if p and p.has_valid_key:
            result = await p.generate(prompt, max_tokens, temperature, system_prompt)
            if result.finish_reason != "error":
                return result

        # 故障转移
        if self.fallback_enabled:
            for name, fallback in self.providers.items():
                if name != target_provider and fallback.has_valid_key:
                    result = await fallback.generate(prompt, max_tokens, temperature, system_prompt)
                    if result.finish_reason != "error":
                        return result

        # 使用模拟响应
        return GenerationResult(
            content=OpenAIProvider(api_key=None)._mock_response(prompt),
            provider="mock",
            model="mock",
            usage=TokenUsage(),
            latency_ms=0,
            finish_reason="mock",
        )

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        target_provider = provider or self.default_provider
        p = self.get_provider(target_provider)

        if p and p.has_valid_key:
            async for chunk in p.generate_stream(prompt, max_tokens, temperature, system_prompt):
                yield chunk
        else:
            yield "[未配置有效的 AI 服务]\n\n"
            yield "请在设置中配置 OpenAI 或 Anthropic API Key 以启用 AI 功能。"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
        provider: Optional[str] = None,
    ) -> GenerationResult:
        """对话生成"""
        target_provider = provider or self.default_provider
        p = self.get_provider(target_provider)

        if p and p.has_valid_key:
            result = await p.chat(messages, max_tokens, temperature)
            if result.finish_reason != "error":
                return result

        # 故障转移
        if self.fallback_enabled:
            for name, fallback in self.providers.items():
                if name != target_provider and fallback.has_valid_key:
                    result = await fallback.chat(messages, max_tokens, temperature)
                    if result.finish_reason != "error":
                        return result

        return GenerationResult(
            content="[未配置有效的 AI 服务] 请在设置中配置 API Key。",
            provider="mock",
            model="mock",
            usage=TokenUsage(),
            latency_ms=0,
            finish_reason="mock",
        )

    async def check_all_health(self) -> List[ProviderHealth]:
        """检查所有提供商的健康状态"""
        health_results = []
        for name, provider in self.providers.items():
            health = await provider.check_health()
            health_results.append(health)
        return health_results

    def get_usage_report(self) -> Dict[str, Any]:
        """获取使用报告"""
        report = {
            "providers": {},
            "total_cost_usd": 0.0,
            "total_tokens": 0,
        }

        for name, provider in self.providers.items():
            usage = provider.get_total_usage()
            cost = provider.get_total_cost()
            report["providers"][name] = {
                "tokens": {
                    "prompt": usage.prompt_tokens,
                    "completion": usage.completion_tokens,
                    "total": usage.total_tokens,
                },
                "cost_usd": cost,
            }
            report["total_cost_usd"] += cost
            report["total_tokens"] += usage.total_tokens

        return report

    async def close(self):
        """关闭所有提供商的连接"""
        for provider in self.providers.values():
            await provider.close()


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek 提供商（国产大模型，支持函数调用）"""

    BASE_URL = "https://api.deepseek.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        timeout: float = 60.0,
    ):
        super().__init__(api_key, model, timeout)

    @property
    def provider_name(self) -> str:
        return "deepseek"

    @property
    def default_model(self) -> str:
        return "deepseek-chat"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> GenerationResult:
        """生成文本"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, max_tokens, temperature)

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.has_valid_key:
            yield "[未配置 DeepSeek API Key]"
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        try:
            client = self._get_client()
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n[错误: {str(e)}]"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> GenerationResult:
        """对话生成"""
        start_time = time.time()

        if not self.has_valid_key:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content="[未配置 DeepSeek API Key] 请在设置中配置 API Key。",
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="no_api_key",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            client = self._get_client()
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            latency = (time.time() - start_time) * 1000

            usage_data = data.get("usage", {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )
            self.record_usage(usage)

            return GenerationResult(
                content=data["choices"][0]["message"]["content"],
                provider=self.provider_name,
                model=self.model,
                usage=usage,
                latency_ms=latency,
                finish_reason=data["choices"][0].get("finish_reason"),
                raw_response=data,
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content=f"调用 DeepSeek API 失败: {str(e)}",
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="error",
            )

    async def check_health(self) -> ProviderHealth:
        """检查 DeepSeek 服务健康状态"""
        if not self.has_valid_key:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.NO_API_KEY,
                error_message="未配置 API Key",
            )

        start_time = time.time()
        try:
            client = self._get_client()
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                models = [m["id"] for m in data.get("data", [])]
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    supported_models=models[:5],
                )
            else:
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.DEGRADED,
                    latency_ms=latency,
                    error_message=f"API 返回状态码: {response.status_code}",
                )

        except Exception as e:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=str(e),
            )


class MoonshotAIProvider(BaseLLMProvider):
    """Moonshot AI (Kimi) 提供商"""

    BASE_URL = "https://api.moonshot.cn/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "moonshot-v1-8k",
        timeout: float = 60.0,
    ):
        super().__init__(api_key, model, timeout)

    @property
    def provider_name(self) -> str:
        return "moonshot"

    @property
    def default_model(self) -> str:
        return "moonshot-v1-8k"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> GenerationResult:
        """生成文本"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, max_tokens, temperature)

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.has_valid_key:
            yield "[未配置 Moonshot AI API Key]"
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        try:
            client = self._get_client()
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n[错误: {str(e)}]"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> GenerationResult:
        """对话生成"""
        start_time = time.time()

        if not self.has_valid_key:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content="[未配置 Moonshot AI API Key] 请在设置中配置 API Key。",
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="no_api_key",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            client = self._get_client()
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            latency = (time.time() - start_time) * 1000

            usage_data = data.get("usage", {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )
            self.record_usage(usage)

            return GenerationResult(
                content=data["choices"][0]["message"]["content"],
                provider=self.provider_name,
                model=self.model,
                usage=usage,
                latency_ms=latency,
                finish_reason=data["choices"][0].get("finish_reason"),
                raw_response=data,
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content=f"调用 Moonshot AI API 失败: {str(e)}",
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="error",
            )

    async def check_health(self) -> ProviderHealth:
        """检查 Moonshot AI 服务健康状态"""
        if not self.has_valid_key:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.NO_API_KEY,
                error_message="未配置 API Key",
            )

        start_time = time.time()
        try:
            client = self._get_client()
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                models = [m["id"] for m in data.get("data", [])]
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    supported_models=models[:5],
                )
            else:
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.DEGRADED,
                    latency_ms=latency,
                    error_message=f"API 返回状态码: {response.status_code}",
                )

        except Exception as e:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=str(e),
            )


class StepFunProvider(BaseLLMProvider):
    """阶跃星辰 (StepFun) 提供商

    官网: https://www.stepfun.com/
    API文档: https://platform.stepfun.com/docs

    支持模型:
    - step-1-8k: 轻量级，快速响应
    - step-1-32k: 标准模型
    - step-1-128k: 长文本支持
    - step-1-256k: 超长文本
    - step-2-16k: 新一代模型
    - step-2-200k: 超长上下文
    """

    BASE_URL = "https://api.stepfun.com/v1"

    # 阶跃星辰模型价格 (每 1K tokens 的美元价格，估算)
    PRICING = {
        "step-1-8k": {"input": 0.001, "output": 0.002},
        "step-1-32k": {"input": 0.002, "output": 0.004},
        "step-1-128k": {"input": 0.004, "output": 0.008},
        "step-1-256k": {"input": 0.008, "output": 0.016},
        "step-2-16k": {"input": 0.003, "output": 0.006},
        "step-2-200k": {"input": 0.006, "output": 0.012},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "step-1-8k",
        timeout: float = 60.0,
    ):
        super().__init__(api_key, model, timeout)

    @property
    def provider_name(self) -> str:
        return "stepfun"

    @property
    def default_model(self) -> str:
        return "step-1-8k"

    def estimate_cost(self, usage: TokenUsage) -> float:
        """估算成本（美元）"""
        model_pricing = self.PRICING.get(self.model, {"input": 0.001, "output": 0.002})
        input_cost = (usage.prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (usage.completion_tokens / 1000) * model_pricing["output"]
        return round(input_cost + output_cost, 6)

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> GenerationResult:
        """生成文本"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, max_tokens, temperature)

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.has_valid_key:
            yield "[未配置阶跃星辰 API Key]\n\n请在设置中配置 StepFun API Key 以启用阶跃星辰大模型。"
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        try:
            client = self._get_client()
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk.get("choices"):
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n[错误: {str(e)}]"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> GenerationResult:
        """对话生成"""
        start_time = time.time()

        if not self.has_valid_key:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content="[未配置阶跃星辰 API Key] 请在设置中配置 API Key。",
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="no_api_key",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            client = self._get_client()
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            latency = (time.time() - start_time) * 1000

            usage_data = data.get("usage", {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )
            self.record_usage(usage)

            return GenerationResult(
                content=data["choices"][0]["message"]["content"],
                provider=self.provider_name,
                model=self.model,
                usage=usage,
                latency_ms=latency,
                finish_reason=data["choices"][0].get("finish_reason"),
                raw_response=data,
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return GenerationResult(
                content=f"调用阶跃星辰 API 失败: {str(e)}",
                provider=self.provider_name,
                model=self.model,
                usage=TokenUsage(),
                latency_ms=latency,
                finish_reason="error",
            )

    async def check_health(self) -> ProviderHealth:
        """检查阶跃星辰服务健康状态"""
        if not self.has_valid_key:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.NO_API_KEY,
                error_message="未配置 API Key",
            )

        start_time = time.time()
        try:
            client = self._get_client()
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                models = [m["id"] for m in data.get("data", [])]
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency,
                    supported_models=models[:10],
                )
            else:
                return ProviderHealth(
                    provider=self.provider_name,
                    status=ProviderStatus.DEGRADED,
                    latency_ms=latency,
                    error_message=f"API 返回状态码: {response.status_code}",
                )

        except Exception as e:
            return ProviderHealth(
                provider=self.provider_name,
                status=ProviderStatus.UNAVAILABLE,
                error_message=str(e),
            )


# 向后兼容
__all__ = [
    "LLMService",
    "OpenAIProvider",
    "AnthropicProvider",
    "DeepSeekProvider",
    "MoonshotAIProvider",
    "StepFunProvider",
    "BaseLLMProvider",
    "GenerationResult",
    "TokenUsage",
    "ProviderHealth",
    "ProviderStatus",
]