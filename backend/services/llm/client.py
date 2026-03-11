"""
LLM 客户端简单封装
用于 defense 等服务
"""

import os
from typing import Optional, List, Dict, Any

# 从 ai 服务导入增强版 LLM 提供商
from services.ai.llm_provider_v2 import LLMService, GenerationResult


class LLMClient:
    """LLM 客户端简单封装"""

    def __init__(self, provider: Optional[str] = None):
        """
        初始化 LLM 客户端

        Args:
            provider: 提供商名称，默认使用环境变量 AI_DEFAULT_PROVIDER
        """
        self.provider = provider or os.getenv("AI_DEFAULT_PROVIDER", "openai")
        self._service = LLMService(
            openai_key=os.getenv("OPENAI_API_KEY"),
            anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
            deepseek_key=os.getenv("DEEPSEEK_API_KEY"),
            moonshot_key=os.getenv("MOONSHOT_API_KEY"),
            stepfun_key=os.getenv("STEPFUN_API_KEY"),
            default_provider=self.provider,
            fallback_enabled=True,
        )

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        生成文本

        Args:
            prompt: 提示词
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的文本
        """
        try:
            result: GenerationResult = await self._service.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return result.content
        except Exception as e:
            # 如果生成失败，返回空字符串或错误信息
            print(f"LLM生成失败: {e}")
            return ""

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        对话生成

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的回复
        """
        # 将消息列表转换为提示词
        prompt = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages])
        return await self.generate(prompt, model, temperature, max_tokens)

    async def health_check(self) -> Dict[str, Any]:
        """检查 LLM 服务健康状态"""
        try:
            health = await self._service.health_check()
            return {
                "status": "healthy" if health else "unavailable",
                "provider": self.provider,
            }
        except Exception as e:
            return {
                "status": "unavailable",
                "error": str(e),
                "provider": self.provider,
            }
