"""
Voice Writing Service
语音驱动写作服务 - 支持语音输入、口语转学术化、语音播报
"""

import json
import tempfile
import os
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from uuid import UUID

from .stepfun_client import get_stepfun_client, StepFunModel


class VoiceWritingService:
    """语音写作服务"""

    def __init__(self):
        self.stepfun = get_stepfun_client()

    # ==================== 语音识别与处理 ====================

    async def transcribe_and_process(
        self,
        audio_data: bytes,
        paper_context: str = "",
        section_type: str = "general"
    ) -> Dict[str, Any]:
        """
        转录音频并处理为学术文本

        Args:
            audio_data: 音频数据
            paper_context: 当前论文上下文
            section_type: 章节类型 (abstract/introduction/method/results/discussion)
        """
        # 1. 语音识别
        asr_result = await self.stepfun.speech_to_text(
            audio_data=audio_data,
            language="zh"
        )

        transcribed_text = asr_result.get('text', '')

        if not transcribed_text:
            return {
                'success': False,
                'error': '语音识别失败',
                'transcribed_text': ''
            }

        # 2. 口语转学术化
        academic_text = await self._convert_to_academic(
            transcribed_text,
            paper_context,
            section_type
        )

        return {
            'success': True,
            'transcribed_text': transcribed_text,
            'academic_text': academic_text,
            'section_type': section_type
        }

    async def _convert_to_academic(
        self,
        spoken_text: str,
        context: str,
        section_type: str
    ) -> str:
        """将口语转换为学术化表达"""

        section_prompts = {
            'abstract': '摘要部分，需要简洁概括研究目的、方法、结果和结论',
            'introduction': '引言部分，需要介绍研究背景、问题陈述和研究意义',
            'method': '方法部分，需要详细描述实验设计、数据收集和分析方法',
            'results': '结果部分，需要客观呈现实验发现和数据',
            'discussion': '讨论部分，需要解释结果意义、对比已有研究和指出局限性',
            'conclusion': '结论部分，需要总结主要发现和提出未来方向',
            'general': '学术写作，保持专业术语和正式表达'
        }

        prompt = f"""请将以下口语化表达转换为专业的学术写作风格。

当前章节: {section_prompts.get(section_type, section_prompts['general'])}

上下文信息:
{context}

口语原文:
{spoken_text}

要求:
1. 使用正式、客观的学术语言
2. 保持原文的核心观点和信息
3. 添加适当的学术术语
4. 确保逻辑连贯
5. 消除口语化表达和冗余词汇
6. 使用被动语态（如适用）

请直接输出转换后的学术文本，不需要解释:"""

        messages = [
            {"role": "system", "content": "你是一位专业的学术写作编辑，擅长将口语转换为高质量的学术文本。"},
            {"role": "user", "content": prompt}
        ]

        response = await self.stepfun.chat_completion(
            messages=messages,
            model="step-1-128k",
            temperature=0.5
        )

        return response['choices'][0]['message']['content']

    # ==================== 语音指令处理 ====================

    async def process_voice_command(
        self,
        audio_data: bytes,
        current_document: str = "",
        cursor_position: int = 0
    ) -> Dict[str, Any]:
        """
        处理语音指令

        支持的指令:
        - "在[位置]插入[内容]"
        - "删除[段落/句子]"
        - "润色[这段/最后一句]"
        - "继续写"
        - "总结成摘要"
        - "生成参考文献"
        """
        # 1. 识别指令
        asr_result = await self.stepfun.speech_to_text(audio_data)
        command_text = asr_result.get('text', '')

        # 2. 解析指令
        system_prompt = """你是一位语音指令解析器。请分析用户的语音指令，提取以下信息:

支持的指令类型:
1. insert - 在指定位置插入内容
2. delete - 删除指定内容
3. polish - 润色指定内容
4. continue - 继续写作
5. summarize - 生成摘要
6. cite - 生成引用
7. translate - 翻译内容
8. format - 格式化文本

请返回JSON格式:
{
    "command_type": "指令类型",
    "target": "操作目标(段落/句子/全文等)",
    "content": "具体内容",
    "position": "位置描述",
    "confirmed_text": "向用户确认的语音播报文本"
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"当前文档:\n{current_document[:2000]}...\n\n语音指令: {command_text}"}
        ]

        response = await self.stepfun.chat_completion(
            messages=messages,
            model="step-1-32k"
        )

        try:
            result = json.loads(response['choices'][0]['message']['content'])
        except:
            result = {
                'command_type': 'unknown',
                'content': command_text,
                'confirmed_text': f'已收到：{command_text}'
            }

        # 3. 生成语音确认
        audio_response = await self.stepfun.text_to_speech(
            result.get('confirmed_text', '指令已收到')
        )

        return {
            'command_text': command_text,
            'parsed_command': result,
            'audio_response': audio_response,
            'timestamp': datetime.utcnow().isoformat()
        }

    # ==================== 实时语音写作流 ====================

    async def streaming_voice_writing(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        paper_context: str = "",
        on_interim_result: callable = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        实时语音写作流

        实现低延迟的边说边转写边处理
        """
        buffer = b''
        chunk_count = 0

        async for audio_chunk in audio_stream:
            buffer += audio_chunk
            chunk_count += 1

            # 每3秒处理一次
            if chunk_count >= 30:  # 假设每100ms一个chunk
                # 处理当前缓冲区
                try:
                    result = await self.transcribe_and_process(
                        buffer,
                        paper_context
                    )

                    if result['success']:
                        yield {
                            'type': 'interim',
                            'transcribed': result['transcribed_text'],
                            'processed': result['academic_text']
                        }

                        if on_interim_result:
                            await on_interim_result(result)

                except Exception as e:
                    yield {
                        'type': 'error',
                        'error': str(e)
                    }

                # 清空缓冲区
                buffer = b''
                chunk_count = 0

        # 处理剩余音频
        if buffer:
            final_result = await self.transcribe_and_process(
                buffer,
                paper_context
            )
            yield {
                'type': 'final',
                **final_result
            }

    # ==================== 语音播报 ====================

    async def generate_audio_feedback(
        self,
        text: str,
        voice_type: str = "xiaosi",
        speed: float = 1.0
    ) -> bytes:
        """生成语音反馈"""
        return await self.stepfun.text_to_speech(
            text=text,
            voice=voice_type,
            speed=speed
        )

    async def read_paper_aloud(
        self,
        paper_text: str,
        start_position: int = 0,
        voice_type: str = "xiaosi"
    ) -> AsyncGenerator[bytes, None]:
        """
        朗读论文

        分段朗读，支持长文本
        """
        # 分段处理
        chunks = self._split_text(paper_text[start_position:], max_length=1000)

        for chunk in chunks:
            audio = await self.stepfun.text_to_speech(
                text=chunk,
                voice=voice_type
            )
            yield audio

    def _split_text(self, text: str, max_length: int = 1000) -> list:
        """将长文本分段"""
        sentences = text.replace('。', '。|').replace('.', '.|').split('|')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    # ==================== 批量处理 ====================

    async def batch_process_recordings(
        self,
        recordings: list,
        paper_id: str
    ) -> Dict[str, Any]:
        """
        批量处理录音文件

        Args:
            recordings: 录音文件列表 [{"audio": bytes, "timestamp": str}]
            paper_id: 论文ID
        """
        results = []

        for i, recording in enumerate(recordings):
            try:
                result = await self.transcribe_and_process(
                    audio_data=recording['audio'],
                    paper_context=f"论文ID: {paper_id}"
                )
                results.append({
                    'index': i,
                    'success': True,
                    **result
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })

        return {
            'paper_id': paper_id,
            'total': len(recordings),
            'successful': sum(1 for r in results if r['success']),
            'results': results
        }


# 单例
_voice_writing_service: Optional[VoiceWritingService] = None


def get_voice_writing_service() -> VoiceWritingService:
    """获取语音写作服务单例"""
    global _voice_writing_service
    if _voice_writing_service is None:
        _voice_writing_service = VoiceWritingService()
    return _voice_writing_service
