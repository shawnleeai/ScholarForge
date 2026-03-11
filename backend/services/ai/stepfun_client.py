"""
StepFun Multi-Modal Client
阶跃星辰多模态统一客户端 - 支持文本、语音、图像、视频
"""

import os
import base64
import aiohttp
from typing import Optional, Literal, AsyncGenerator, Dict, Any
from dataclasses import dataclass
from enum import Enum


class StepFunModel(str, Enum):
    """阶跃星辰模型枚举"""
    # 文本模型
    STEP_1_32K = "step-1-32k"
    STEP_1_128K = "step-1-128k"
    STEP_1_256K = "step-1-256k"
    # 多模态模型
    STEP_1O = "step-1o"
    STEP_1V = "step-1v"
    # 语音模型
    STEP_ASR = "step-asr"
    STEP_TTS = "step-tts"
    # 视频模型
    STEP_VIDEO = "step-video"


@dataclass
class StepFunConfig:
    """阶跃模型配置"""
    api_key: str
    base_url: str = "https://api.stepfun.com/v1"
    timeout: int = 120

    # 模型默认配置
    default_temperature: float = 0.7
    max_tokens: Dict[str, int] = None

    def __post_init__(self):
        if self.max_tokens is None:
            self.max_tokens = {
                "step-1-32k": 32000,
                "step-1-128k": 128000,
                "step-1-256k": 256000,
            }


class StepFunMultiModalClient:
    """
    阶跃星辰多模态统一客户端

    支持功能:
    - 文本生成 (step-1-32k/128k/256k)
    - 语音识别 (step-asr)
    - 语音合成 (step-tts)
    - 图像理解 (step-1o)
    - 图像生成 (step-1v)
    - 视频生成 (step-video)
    """

    def __init__(self, config: Optional[StepFunConfig] = None):
        self.config = config or StepFunConfig(
            api_key=os.getenv("STEPFUN_API_KEY", "")
        )
        self._session: Optional[aiohttp.ClientSession] = None

        # 场景-模型映射
        self.scenario_model_map = {
            "writing_continuation": "step-1-128k",
            "quick_polish": "step-1-32k",
            "literature_review": "step-1-256k",
            "chart_analysis": "step-1o",
            "chart_generation": "step-1v",
            "voice_input": "step-asr",
            "voice_output": "step-tts",
            "video_abstract": "step-video",
            "logic_check": "step-1-128k",
            "multi_hop_qa": "step-1-128k",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self._session

    async def close(self):
        """关闭客户端"""
        if self._session and not self._session.closed:
            await self._session.close()

    # ==================== 文本生成 ====================

    async def chat_completion(
        self,
        messages: list,
        model: str = "step-1-128k",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        文本生成接口

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
        """
        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
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

        payload.update(kwargs)

        async with session.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def chat_completion_stream(
        self,
        messages: list,
        model: str = "step-1-128k",
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式文本生成"""
        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        payload.update(kwargs)

        async with session.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            response.raise_for_status()

            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta:
                            yield delta['content']
                    except:
                        pass

    # ==================== 语音识别 (ASR) ====================

    async def speech_to_text(
        self,
        audio_data: bytes,
        language: str = "zh",
        model: str = "step-asr"
    ) -> Dict[str, Any]:
        """
        语音识别

        Args:
            audio_data: 音频数据 (支持mp3, wav, m4a等)
            language: 语言 (zh/en)
            model: ASR模型
        """
        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}"
        }

        # 构建multipart表单
        data = aiohttp.FormData()
        data.add_field('file', audio_data, filename='audio.mp3')
        data.add_field('model', model)
        data.add_field('language', language)

        async with session.post(
            f"{self.config.base_url}/audio/transcriptions",
            headers=headers,
            data=data
        ) as response:
            response.raise_for_status()
            return await response.json()

    # ==================== 语音合成 (TTS) ====================

    async def text_to_speech(
        self,
        text: str,
        voice: str = "xiaosi",
        model: str = "step-tts",
        speed: float = 1.0,
        response_format: str = "mp3"
    ) -> bytes:
        """
        语音合成

        Args:
            text: 要合成的文本
            voice: 音色 (xiaosi/xiaoyan等)
            model: TTS模型
            speed: 语速 (0.5-2.0)
            response_format: 输出格式 (mp3/wav)
        """
        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": response_format
        }

        async with session.post(
            f"{self.config.base_url}/audio/speech",
            headers=headers,
            json=payload
        ) as response:
            response.raise_for_status()
            return await response.read()

    # ==================== 多模态理解 (Vision) ====================

    async def vision_analysis(
        self,
        image_data: bytes,
        prompt: str,
        model: str = "step-1o",
        detail: str = "auto"
    ) -> Dict[str, Any]:
        """
        图像理解分析

        Args:
            image_data: 图像数据
            prompt: 分析提示
            model: 视觉模型
            detail: 细节级别 (low/high/auto)
        """
        # 将图片转为base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": detail
                    }
                }
            ]
        }]

        return await self.chat_completion(
            messages=messages,
            model=model
        )

    # ==================== 图像生成 ====================

    async def image_generation(
        self,
        prompt: str,
        model: str = "step-1v",
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1
    ) -> Dict[str, Any]:
        """
        图像生成

        Args:
            prompt: 生成提示
            model: 图像生成模型
            size: 尺寸 (1024x1024/1024x1792/1792x1024)
            quality: 质量 (standard/hd)
            n: 生成数量
        """
        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n
        }

        async with session.post(
            f"{self.config.base_url}/images/generations",
            headers=headers,
            json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()

    # ==================== 视频生成 ====================

    async def video_generation(
        self,
        prompt: str,
        model: str = "step-video",
        duration: int = 5,
        resolution: str = "720p"
    ) -> Dict[str, Any]:
        """
        视频生成

        Args:
            prompt: 视频描述
            model: 视频生成模型
            duration: 时长 (秒)
            resolution: 分辨率 (720p/1080p)
        """
        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution
        }

        async with session.post(
            f"{self.config.base_url}/videos/generations",
            headers=headers,
            json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()

    # ==================== 场景化封装 ====================

    async def academic_writing(
        self,
        content: str,
        task: Literal["continue", "polish", "summarize", "translate"],
        context: str = "",
        stream: bool = False
    ) -> str:
        """
        学术写作助手

        Args:
            content: 输入内容
            task: 任务类型 (continue续写/polish润色/summarize总结/translate翻译)
            context: 上下文
            stream: 是否流式
        """
        # 根据任务选择模型
        if task == "summarize" and len(content) > 10000:
            model = "step-1-256k"
        else:
            model = "step-1-128k"

        task_prompts = {
            "continue": f"继续学术化地续写以下内容，保持专业术语和逻辑连贯:\n\n{content}",
            "polish": f"将以下内容润色为更专业的学术表达，保持原意但提升语言质量:\n\n{content}",
            "summarize": f"用学术语言总结以下内容的要点:\n\n{content}",
            "translate": f"将以下内容翻译成专业的学术英文:\n\n{content}"
        }

        messages = [
            {"role": "system", "content": "你是一位专业的学术写作助手，擅长学术论文写作、润色和翻译。"},
            {"role": "user", "content": task_prompts.get(task, content)}
        ]

        if context:
            messages[0]["content"] += f"\n\n上下文信息:\n{context}"

        if stream:
            result = ""
            async for chunk in self.chat_completion_stream(messages, model=model):
                result += chunk
            return result
        else:
            response = await self.chat_completion(messages, model=model)
            return response['choices'][0]['message']['content']

    async def voice_interactive_writing(
        self,
        audio_input: bytes,
        current_text: str = "",
        instruction: str = ""
    ) -> Dict[str, Any]:
        """
        语音交互写作

        流程: ASR识别 -> LLM理解处理 -> TTS播报确认
        """
        # 1. 语音识别
        asr_result = await self.speech_to_text(audio_input)
        recognized_text = asr_result.get('text', '')

        # 2. 理解用户意图并处理
        messages = [
            {"role": "system", "content": """你是一位学术写作语音助手。请分析用户的语音指令，执行相应的写作任务。
可用指令:
- "插入到[位置]": 将内容插入指定位置
- "润色这段": 改进表达质量
- "继续写": 续写内容
- "总结成摘要": 生成摘要
- "生成图表说明": 为图表写说明文字

请返回JSON格式: {"action": "动作", "content": "处理后的内容", "position": "插入位置"}"""},
            {"role": "user", "content": f"当前文本:\n{current_text}\n\n语音指令:\n{recognized_text}\n\n额外指令:\n{instruction}"}
        ]

        response = await self.chat_completion(messages, model="step-1-32k")
        result_text = response['choices'][0]['message']['content']

        # 3. 语音合成确认
        confirm_text = f"已理解，正在为您{recognized_text[:20]}..."
        audio_output = await self.text_to_speech(confirm_text)

        return {
            "recognized_text": recognized_text,
            "processed_result": result_text,
            "audio_response": audio_output,
            "action": "voice_writing"
        }


# 单例实例
_stepfun_client: Optional[StepFunMultiModalClient] = None


def get_stepfun_client() -> StepFunMultiModalClient:
    """获取阶跃客户端单例"""
    global _stepfun_client
    if _stepfun_client is None:
        api_key = os.getenv("STEPFUN_API_KEY")
        if not api_key:
            raise ValueError("STEPFUN_API_KEY environment variable is required")
        _stepfun_client = StepFunMultiModalClient(
            config=StepFunConfig(api_key=api_key)
        )
    return _stepfun_client
