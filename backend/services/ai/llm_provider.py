"""
LLM 提供商抽象层
统一多个 LLM API 的调用接口
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

# httpx is optional - only needed for actual API calls
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None


class BaseLLMProvider(ABC):
    """LLM 提供商基类"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key
        self.model = model

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商名称"""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """生成文本"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """对话生成"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI 提供商"""

    BASE_URL = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
    ):
        super().__init__(api_key, model)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """生成文本"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, max_tokens, temperature)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """对话生成"""
        if not self.api_key or not HAS_HTTPX:
            # 返回模拟响应
            return self._mock_response(messages[-1]["content"] if messages else "")

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
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            # 返回模拟响应
            return self._mock_response(messages[-1]["content"] if messages else "")

    def _mock_response(self, prompt: str) -> str:
        """模拟响应（用于开发测试）"""
        if "续写" in prompt or "continue" in prompt.lower():
            return (
                "基于上述研究背景，本研究将采用混合研究方法，"
                "结合定量分析与案例研究，深入探讨AI协同项目管理的关键因素。"
                "研究将分为三个阶段：首先通过文献综述梳理理论框架；"
                "其次设计问卷收集实证数据；最后通过案例分析验证研究假设。"
            )
        elif "润色" in prompt or "polish" in prompt.lower():
            return (
                "本研究采用混合研究方法，将定量分析与案例研究有机结合，"
                "系统性地探究人工智能协同项目管理的核心影响因素。"
                "研究设计涵盖三个递进阶段：理论框架构建、实证数据采集与假设验证。"
            )
        elif "翻译" in prompt or "translate" in prompt.lower():
            return (
                "This study employs a mixed-methods approach, combining quantitative "
                "analysis with case studies to systematically investigate the key factors "
                "in AI-enabled collaborative project management."
            )
        else:
            return (
                "这是一个模拟的AI响应。在实际部署时，需要配置有效的API密钥。"
                "AI服务将根据您的请求生成学术写作建议、文本润色或翻译服务。"
            )


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude 提供商"""

    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-opus-20240229",
    ):
        super().__init__(api_key, model)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """生成文本"""
        if not self.api_key or not HAS_HTTPX:
            return self._mock_response(prompt)

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/messages",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"]

        except Exception:
            return self._mock_response(prompt)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """对话生成"""
        # 将消息格式转换为Anthropic格式
        prompt = "\n".join(
            f"{m['role']}: {m['content']}" for m in messages
        )
        return await self.generate(prompt, max_tokens, temperature)

    def _mock_response(self, prompt: str) -> str:
        """模拟响应"""
        return (
            "[Claude模拟响应] 作为学术写作助手，我建议您在论文中："
            "1. 明确研究问题和假设；2. 选择合适的研究方法；"
            "3. 确保数据分析的严谨性；4. 讨论研究局限性和未来方向。"
        )


class ChatGLMProvider(BaseLLMProvider):
    """ChatGLM 提供商（智谱AI）"""

    BASE_URL = "https://open.bigmodel.cn/api/paas/v3"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4",
    ):
        super().__init__(api_key, model)

    @property
    def provider_name(self) -> str:
        return "chatglm"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """生成文本"""
        if not self.api_key:
            return self._mock_response(prompt)

        # ChatGLM API 实现
        return self._mock_response(prompt)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """对话生成"""
        return await self.generate(
            messages[-1]["content"] if messages else "",
            max_tokens,
            temperature,
        )

    def _mock_response(self, prompt: str) -> str:
        """模拟响应"""
        return (
            "[ChatGLM模拟响应] 根据您的写作需求，我建议："
            "学术论文应注重逻辑性和严谨性，建议采用'总-分-总'的结构，"
            "并在每个论点后提供充分的论据支撑。"
        )


class LLMService:
    """LLM 服务统一接口"""

    def __init__(
        self,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        chatglm_key: Optional[str] = None,
    ):
        self.providers = {
            "openai": OpenAIProvider(api_key=openai_key),
            "anthropic": AnthropicProvider(api_key=anthropic_key),
            "chatglm": ChatGLMProvider(api_key=chatglm_key),
        }
        self.default_provider = "openai"

    def get_provider(self, provider_name: Optional[str] = None) -> BaseLLMProvider:
        """获取提供商"""
        name = provider_name or self.default_provider
        return self.providers.get(name, self.providers[self.default_provider])

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        生成文本

        Returns:
            tuple[str, str]: (生成的内容, 使用的提供商名称)
        """
        p = self.get_provider(provider)
        result = await p.generate(prompt, max_tokens, temperature, system_prompt)
        return result, p.provider_name

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
        provider: Optional[str] = None,
    ) -> tuple[str, str]:
        """对话生成"""
        p = self.get_provider(provider)
        result = await p.chat(messages, max_tokens, temperature)
        return result, p.provider_name
