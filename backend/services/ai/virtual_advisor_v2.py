"""
Virtual Advisor V2 Service
AI虚拟导师V2 - 支持语音对话、视频生成、个性化配置
"""

import json
import os
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from .stepfun_client import get_stepfun_client, StepFunModel


class AdvisorPersonality(str, Enum):
    """导师性格类型"""
    POISONOUS = "poisonous"      # 毒舌
    GENTLE = "gentle"           # 温和
    STRICT = "strict"           # 严格
    HUMOROUS = "humorous"       # 幽默
    ENCOURAGING = "encouraging" # 鼓励型
    BALANCED = "balanced"       # 平衡型


class ReviewFocus(str, Enum):
    """审阅关注点"""
    INNOVATION = "innovation"   # 创新性
    METHODOLOGY = "methodology" # 方法论
    WRITING = "writing"         # 写作表达
    LOGIC = "logic"             # 逻辑结构
    COMPREHENSIVE = "comprehensive" # 全面


@dataclass
class AdvisorConfig:
    """导师配置"""
    personality: AdvisorPersonality = AdvisorPersonality.BALANCED
    focus_areas: List[ReviewFocus] = field(default_factory=lambda: [ReviewFocus.COMPREHENSIVE])
    voice_enabled: bool = True
    video_enabled: bool = False
    response_speed: Literal["fast", "normal", "thoughtful"] = "normal"
    language: str = "zh"
    strictness_level: int = 5  # 1-10


@dataclass
class ReviewSession:
    """审阅会话"""
    session_id: str
    user_id: str
    paper_id: Optional[str]
    advisor_config: AdvisorConfig
    messages: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    review_points: List[Dict[str, Any]] = field(default_factory=list)


class VirtualAdvisorV2:
    """AI虚拟导师V2"""

    # 性格系统提示词
    PERSONALITY_PROMPTS = {
        AdvisorPersonality.POISONOUS: """你是一位毒舌但专业的导师。说话直接、尖锐，但总能一针见血地指出问题。
风格特点:
- 语言犀利，不留情面
- 直接指出问题本质
- 用反问激发思考
- 偶尔讽刺但富有洞察力""",

        AdvisorPersonality.GENTLE: """你是一位温和耐心的导师。善于引导，循序渐进地帮助学生。
风格特点:
- 语气温和友善
- 循循善诱
- 给予充分鼓励
- 耐心解答问题""",

        AdvisorPersonality.STRICT: """你是一位严谨认真的导师。对学术要求严格，注重细节。
风格特点:
- 要求严格
- 注重逻辑和数据
- 强调学术规范
- 追求精益求精""",

        AdvisorPersonality.HUMOROUS: """你是一位幽默风趣的导师。用轻松的方式传授知识。
风格特点:
- 语言幽默
- 善用比喻
- 寓教于乐
- 缓解学术压力""",

        AdvisorPersonality.ENCOURAGING: """你是一位善于激励的导师。总能发现学生的闪光点。
风格特点:
- 积极正面
- 善于发现进步
- 给予信心
- 强调潜力""",

        AdvisorPersonality.BALANCED: """你是一位平衡的导师。既有专业要求，又善解人意。
风格特点:
- 客观公正
- 建设性批评
- 既有要求又有支持
- 专业且亲和"""
    }

    # 关注点提示词
    FOCUS_PROMPTS = {
        ReviewFocus.INNOVATION: "重点关注研究创新性，评估 novelty 和贡献度。",
        ReviewFocus.METHODOLOGY: "重点关注研究方法，评估实验设计、数据分析和可复现性。",
        ReviewFocus.WRITING: "重点关注写作表达，评估语言质量、逻辑流畅度和学术规范。",
        ReviewFocus.LOGIC: "重点关注逻辑结构，评估论证链条、假设合理性和结论支持度。",
        ReviewFocus.COMPREHENSIVE: "全面审阅所有方面，包括创新、方法、写作和逻辑。"
    }

    def __init__(self):
        self.stepfun = get_stepfun_client()
        self.sessions: Dict[str, ReviewSession] = {}

    # ==================== 会话管理 ====================

    def create_session(
        self,
        user_id: str,
        paper_id: Optional[str] = None,
        config: Optional[AdvisorConfig] = None
    ) -> ReviewSession:
        """创建审阅会话"""
        session = ReviewSession(
            session_id=str(uuid4()),
            user_id=user_id,
            paper_id=paper_id,
            advisor_config=config or AdvisorConfig()
        )
        self.sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ReviewSession]:
        """获取会话"""
        return self.sessions.get(session_id)

    def close_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """关闭会话并生成总结"""
        session = self.sessions.pop(session_id, None)
        if not session:
            return None

        # 生成会话总结
        summary = self._generate_session_summary(session)
        return summary

    # ==================== 核心审阅功能 ====================

    async def review_paper(
        self,
        session_id: str,
        paper_content: str,
        review_type: Literal["quick", "detailed", "deep"] = "detailed"
    ) -> Dict[str, Any]:
        """
        审阅论文

        Args:
            session_id: 会话ID
            paper_content: 论文内容
            review_type: 审阅类型 (quick快速/detailed详细/deep深度)
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        config = session.advisor_config

        # 构建系统提示
        system_prompt = self._build_system_prompt(config)

        # 根据审阅类型调整
        review_prompts = {
            "quick": "请快速审阅这篇论文，指出最突出的3-5个问题。",
            "detailed": "请详细审阅这篇论文，从创新性、方法、写作、逻辑等方面给出全面评价。",
            "deep": "请深度审阅这篇论文，进行批判性分析，识别潜在问题，提出具体改进建议。"
        }

        # 构建审查提示
        prompt = f"""{review_prompts[review_type]}

请按以下JSON格式输出审阅结果：
{{
    "overall_score": 0-100,
    "overall_comment": "总体评价",
    "dimensions": [
        {{
            "name": "创新性|方法|写作|逻辑",
            "score": 0-100,
            "comment": "具体评价",
            "strengths": ["优点1", "优点2"],
            "weaknesses": ["不足1", "不足2"],
            "suggestions": ["建议1", "建议2"]
        }}
    ],
    "critical_issues": ["关键问题1", "关键问题2"],
    "priority_actions": ["优先改进1", "优先改进2"],
    "encouragement": "鼓励的话"
}}

论文内容:
{paper_content[:20000]}"""

        response = await self.stepfun.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="step-1-256k"  # 使用长上下文模型
        )

        content = response['choices'][0]['message']['content']

        # 解析JSON
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            review_result = json.loads(json_str.strip())
        except:
            review_result = {"raw_review": content}

        # 记录到会话
        session.review_points.append({
            "type": "paper_review",
            "result": review_result,
            "timestamp": datetime.utcnow().isoformat()
        })

        return review_result

    async def chat(
        self,
        session_id: str,
        message: str,
        paper_context: str = "",
        stream: bool = False
    ) -> str:
        """
        对话交流

        Args:
            session_id: 会话ID
            message: 用户消息
            paper_context: 论文上下文
            stream: 是否流式输出
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        config = session.advisor_config
        system_prompt = self._build_system_prompt(config)

        # 构建消息历史
        messages = [{"role": "system", "content": system_prompt}]

        if paper_context:
            messages.append({
                "role": "system",
                "content": f"当前论文上下文:\n{paper_context[:10000]}"
            })

        # 添加历史消息（保留最近5轮）
        for msg in session.messages[-10:]:
            messages.append(msg)

        messages.append({"role": "user", "content": message})

        # 记录用户消息
        session.messages.append({"role": "user", "content": message})

        if stream:
            response_text = ""
            async for chunk in self.stepfun.chat_completion_stream(
                messages=messages,
                model="step-1-128k"
            ):
                response_text += chunk
        else:
            response = await self.stepfun.chat_completion(
                messages=messages,
                model="step-1-128k"
            )
            response_text = response['choices'][0]['message']['content']

        # 记录助手回复
        session.messages.append({"role": "assistant", "content": response_text})

        return response_text

    async def voice_chat(
        self,
        session_id: str,
        audio_input: bytes,
        paper_context: str = ""
    ) -> Dict[str, Any]:
        """
        语音对话

        流程: ASR识别 -> LLM处理 -> TTS合成
        """
        # 1. 语音识别
        asr_result = await self.stepfun.speech_to_text(audio_input)
        user_text = asr_result.get('text', '')

        if not user_text:
            return {
                "success": False,
                "error": "语音识别失败"
            }

        # 2. 对话处理
        response_text = await self.chat(session_id, user_text, paper_context)

        # 3. 语音合成
        audio_response = await self.stepfun.text_to_speech(response_text)

        return {
            "success": True,
            "user_text": user_text,
            "advisor_response": response_text,
            "audio_response": audio_response
        }

    async def generate_review_video(
        self,
        review_content: str,
        paper_title: str
    ) -> bytes:
        """
        生成审阅视频

        使用step-video生成导师形象的视频反馈
        """
        # 构建视频生成提示
        video_prompt = f"""生成一段学术导师审阅视频:

场景: 专业学术办公室背景
人物: 友好的学术导师
动作: 认真审阅论文、点头、做笔记
氛围: 专业、建设性、鼓励性

审阅内容概要: {review_content[:500]}
论文标题: {paper_title}

要求:
- 导师形象专业亲和
- 表情自然专注
- 光线明亮温暖
- 时长5-10秒"""

        # 调用视频生成
        response = await self.stepfun.video_generation(
            prompt=video_prompt,
            duration=5,
            resolution="720p"
        )

        # 返回视频数据
        return response.get('video_data', b'')

    # ==================== 辅助方法 ====================

    def _build_system_prompt(self, config: AdvisorConfig) -> str:
        """构建系统提示"""
        personality_prompt = self.PERSONALITY_PROMPTS[config.personality]

        focus_prompts = [self.FOCUS_PROMPTS[f] for f in config.focus_areas]
        focus_section = "\n".join(focus_prompts)

        strictness_desc = {
            1: "非常宽松，以鼓励为主",
            5: "适度严格，平衡要求和支持",
            10: "非常严格，追求完美"
        }.get(config.strictness_level, "适度严格")

        return f"""{personality_prompt}

审阅关注点:
{focus_section}

严格程度: {strictness_desc} ({config.strictness_level}/10)

角色设定:
- 你是一位经验丰富的学术导师
- 你擅长审阅学术论文并提供建设性反馈
- 你的建议既有学术严谨性又实用可行
- 你会根据学生水平调整反馈方式

回复原则:
1. 保持设定的性格特点
2. 基于论文内容给出具体建议
3. 既有批评也要有鼓励
4. 建议要可操作、可执行
5. 使用中文回复"""

    def _generate_session_summary(self, session: ReviewSession) -> Dict[str, Any]:
        """生成会话总结"""
        duration = (datetime.utcnow() - session.start_time).total_seconds()

        return {
            "session_id": session.id,
            "duration_seconds": duration,
            "message_count": len(session.messages),
            "review_points_count": len(session.review_points),
            "advisor_personality": session.advisor_config.personality.value,
            "focus_areas": [f.value for f in session.advisor_config.focus_areas],
            "start_time": session.start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat()
        }

    async def generate_mock_defense_questions(
        self,
        paper_content: str,
        num_questions: int = 10
    ) -> List[Dict[str, Any]]:
        """生成模拟答辩问题"""

        prompt = f"""基于以下论文内容，生成{num_questions}个可能的答辩问题。

要求:
1. 问题要覆盖论文的核心内容
2. 包含简单、中等、困难三个难度级别
3. 问题要具体，能测试学生对研究的理解
4. 提供参考答案要点

请以JSON格式返回:
[
    {{
        "question": "问题内容",
        "difficulty": "easy/medium/hard",
        "category": "创新/方法/结果/局限",
        "key_points": ["回答要点1", "回答要点2"],
        "follow_up": "可能的追问"
    }}
]

论文内容:
{paper_content[:15000]}"""

        response = await self.stepfun.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="step-1-128k"
        )

        content = response['choices'][0]['message']['content']

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str.strip())
        except:
            return [{"question": content, "difficulty": "medium"}]


# 单例
_virtual_advisor_v2: Optional[VirtualAdvisorV2] = None


def get_virtual_advisor_v2() -> VirtualAdvisorV2:
    """获取虚拟导师V2单例"""
    global _virtual_advisor_v2
    if _virtual_advisor_v2 is None:
        _virtual_advisor_v2 = VirtualAdvisorV2()
    return _virtual_advisor_v2
