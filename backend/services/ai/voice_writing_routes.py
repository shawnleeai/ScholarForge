"""
Voice Writing API Routes
语音写作API路由
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from .voice_writing_service import get_voice_writing_service

router = APIRouter(prefix="/voice-writing", tags=["voice-writing"])


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    paper_context: str = Form(""),
    section_type: str = Form("general")
):
    """
    转录音频并转换为学术文本

    - **audio**: 音频文件 (mp3/wav/m4a)
    - **paper_context**: 当前论文上下文
    - **section_type**: 章节类型 (abstract/introduction/method/results/discussion/conclusion)
    """
    service = get_voice_writing_service()

    # 读取音频数据
    audio_data = await audio.read()

    result = await service.transcribe_and_process(
        audio_data=audio_data,
        paper_context=paper_context,
        section_type=section_type
    )

    return result


@router.post("/command")
async def process_voice_command(
    audio: UploadFile = File(...),
    current_document: str = Form(""),
    cursor_position: int = Form(0)
):
    """
    处理语音指令

    支持的指令:
    - 在[位置]插入[内容]
    - 删除[段落/句子]
    - 润色[这段/最后一句]
    - 继续写
    - 总结成摘要
    - 生成参考文献
    """
    service = get_voice_writing_service()

    audio_data = await audio.read()

    result = await service.process_voice_command(
        audio_data=audio_data,
        current_document=current_document,
        cursor_position=cursor_position
    )

    return {
        'command_text': result['command_text'],
        'parsed_command': result['parsed_command'],
        'timestamp': result['timestamp']
    }


@router.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    voice: str = Form("xiaosi"),
    speed: float = Form(1.0)
):
    """
    文本转语音

    - **text**: 要合成的文本
    - **voice**: 音色 (xiaosi/xiaoyan)
    - **speed**: 语速 (0.5-2.0)
    """
    service = get_voice_writing_service()

    audio_data = await service.generate_audio_feedback(
        text=text,
        voice_type=voice,
        speed=speed
    )

    return StreamingResponse(
        iter([audio_data]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=speech.mp3"}
    )


@router.websocket("/ws/stream")
async def voice_writing_websocket(websocket: WebSocket):
    """
    WebSocket实时语音写作

    客户端发送音频流，服务端实时返回转写和加工结果
    """
    await websocket.accept()
    service = get_voice_writing_service()

    try:
        while True:
            # 接收音频数据
            message = await websocket.receive_text()
            data = json.loads(message)

            if data.get('type') == 'audio_chunk':
                # 处理音频块
                audio_bytes = base64.b64decode(data['audio'])

                # 这里简化处理，实际应该累积缓冲区
                result = await service.transcribe_and_process(
                    audio_data=audio_bytes,
                    paper_context=data.get('context', '')
                )

                await websocket.send_json({
                    'type': 'result',
                    'data': result
                })

            elif data.get('type') == 'finalize':
                # 结束录音，返回最终结果
                await websocket.send_json({
                    'type': 'final',
                    'message': 'Processing complete'
                })

    except WebSocketDisconnect:
        pass


import json
import base64
