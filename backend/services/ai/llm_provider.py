"""
LLM 提供商抽象层
统一多个 LLM API 的调用接口

向后兼容版本 - 使用 llm_provider_v2.py 中的增强实现
"""

import logging
from typing import Optional, List, Dict, Any

# 从增强版导入所有核心类
from .llm_provider_v2 import (
    LLMService as LLMServiceV2,
    OpenAIProvider,
    AnthropicProvider,
    BaseLLMProvider,
    GenerationResult,
    TokenUsage,
    ProviderHealth,
    ProviderStatus,
)

logger = logging.getLogger(__name__)


# 保持向后兼容的 LLMService 类
class LLMService(LLMServiceV2):
    """LLM 服务统一接口（向后兼容）"""

    def __init__(
        self,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        chatglm_key: Optional[str] = None,
        deepseek_key: Optional[str] = None,
        moonshot_key: Optional[str] = None,
        stepfun_key: Optional[str] = None,
    ):
        super().__init__(
            openai_key=openai_key,
            anthropic_key=anthropic_key,
            deepseek_key=deepseek_key,
            moonshot_key=moonshot_key,
            stepfun_key=stepfun_key,
            default_provider="openai",
            fallback_enabled=True,
        )
        # ChatGLM 暂未实现，记录警告
        if chatglm_key:
            logger.warning("ChatGLMProvider 尚未实现，chatglm_key 将被忽略")

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        生成文本（向后兼容）

        Returns:
            tuple[str, str]: (生成的内容, 使用的提供商名称)
        """
        result = await super().generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            provider=provider,
        )
        return result.content, result.provider

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
        provider: Optional[str] = None,
    ) -> tuple[str, str]:
        """对话生成（向后兼容）"""
        result = await super().chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            provider=provider,
        )
        return result.content, result.provider
