"""
Video Abstract Service
视频摘要生成服务 - 自动生成论文介绍视频
"""

import json
import os
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, field

from .stepfun_client import get_stepfun_client


@dataclass
class VideoTemplate:
    """视频模板"""
    id: str
    name: str
    description: str
    style: Literal["academic", "modern", "minimal", "colorful"]
    duration: int  # 秒
    scenes: List[Dict[str, Any]]
    music_style: str


@dataclass
class VideoAbstract:
    """视频摘要"""
    paper_id: str
    title: str
    script: str
    scenes: List[Dict[str, Any]]
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    status: Literal["pending", "generating", "completed", "failed"] = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)


class VideoAbstractService:
    """视频摘要生成服务"""

    # 预定义模板
    TEMPLATES = {
        "academic": VideoTemplate(
            id="academic",
            name="学术经典",
            description="传统学术风格，简洁专业",
            style="academic",
            duration=180,
            scenes=[
                {"type": "title", "duration": 10},
                {"type": "abstract", "duration": 30},
                {"type": "method", "duration": 60},
                {"type": "results", "duration": 50},
                {"type": "conclusion", "duration": 30}
            ],
            music_style="classical"
        ),
        "modern": VideoTemplate(
            id="modern",
            name="现代简约",
            description="现代简约风格，动态效果",
            style="modern",
            duration=120,
            scenes=[
                {"type": "hook", "duration": 5},
                {"type": "problem", "duration": 20},
                {"type": "solution", "duration": 40},
                {"type": "impact", "duration": 35},
                {"type": "cta", "duration": 20}
            ],
            music_style="electronic"
        ),
        "minimal": VideoTemplate(
            id="minimal",
            name="极简风格",
            description="极简设计，内容为王",
            style="minimal",
            duration=90,
            scenes=[
                {"type": "intro", "duration": 10},
                {"type": "core", "duration": 60},
                {"type": "outro", "duration": 20}
            ],
            music_style="ambient"
        )
    }

    def __init__(self):
        self.stepfun = get_stepfun_client()
        self.output_dir = os.getenv("VIDEO_OUTPUT_DIR", "/tmp/videos")

    # ==================== 脚本生成 ====================

    async def generate_script(
        self,
        paper_data: Dict[str, Any],
        template_id: str = "academic",
        target_audience: Literal["experts", "general", "students"] = "experts",
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        生成视频脚本

        Args:
            paper_data: 论文数据
            template_id: 模板ID
            target_audience: 目标观众
            language: 语言
        """
        template = self.TEMPLATES.get(template_id, self.TEMPLATES["academic"])

        # 根据模板构建提示
        scene_descriptions = "\n".join([
            f"- {scene['type']}: 约{scene['duration']}秒"
            for scene in template.scenes
        ])

        audience_prompt = {
            "experts": "领域专家，使用专业术语",
            "general": "普通观众，通俗解释",
            "students": "学生群体，教学式讲解"
        }

        prompt = f"""请为一篇学术论文生成{template.duration}秒的视频脚本。

论文信息:
标题: {paper_data.get('title', '')}
作者: {', '.join(paper_data.get('authors', []))}
摘要: {paper_data.get('abstract', '')}
关键词: {', '.join(paper_data.get('keywords', []))}

视频风格: {template.name} - {template.description}
目标观众: {audience_prompt[target_audience]}

视频结构:
{scene_descriptions}

请以JSON格式返回完整脚本:
{{
    "title": "视频标题",
    "duration": {template.duration},
    "scenes": [
        {{
            "type": "场景类型",
            "start_time": 0,
            "end_time": 10,
            "narration": "旁白文字（口语化、自然）",
            "visual_description": "视觉画面描述",
            "key_points": ["要点1", "要点2"]
        }}
    ],
    "music_cues": [
        {{
            "time": 0,
            "type": "intro/transition/outro",
            "description": "音乐提示"
        }}
    ]
}}"""

        response = await self.stepfun.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="step-1-128k"
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

            script = json.loads(json_str.strip())
        except:
            script = {"raw_script": content}

        return script

    # ==================== 视频生成 ====================

    async def generate_video_scene(
        self,
        scene: Dict[str, Any],
        paper_title: str,
        style: str = "academic"
    ) -> bytes:
        """生成单个场景视频"""

        visual_prompt = f"""生成学术视频场景:

场景类型: {scene['type']}
时长: {scene.get('duration', 5)}秒
视觉描述: {scene.get('visual_description', '学术图表展示')}
论文标题: {paper_title}

风格: {style}
- academic: 专业学术风格，简洁图表
- modern: 现代动感风格
- minimal: 极简设计

要求:
- 高清晰度
- 专业美观
- 适合学术展示"""

        response = await self.stepfun.video_generation(
            prompt=visual_prompt,
            duration=min(scene.get('duration', 5), 10),  # 单次最多10秒
            resolution="720p"
        )

        # 这里假设API返回视频数据
        return response.get('video_data', b'')

    async def generate_video_abstract(
        self,
        paper_data: Dict[str, Any],
        template_id: str = "academic",
        generate_audio: bool = True,
        generate_video: bool = True
    ) -> VideoAbstract:
        """
        生成完整视频摘要

        Args:
            paper_data: 论文数据
            template_id: 模板ID
            generate_audio: 是否生成音频
            generate_video: 是否生成视频
        """
        paper_id = paper_data.get('id', str(datetime.utcnow().timestamp()))

        video_abstract = VideoAbstract(
            paper_id=paper_id,
            title=paper_data.get('title', '')
        )

        try:
            # 1. 生成脚本
            script = await self.generate_script(paper_data, template_id)
            video_abstract.script = json.dumps(script, ensure_ascii=False)
            video_abstract.scenes = script.get('scenes', [])

            # 2. 生成音频（旁白）
            if generate_audio:
                narration_text = " ".join([
                    scene.get('narration', '')
                    for scene in script.get('scenes', [])
                ])

                audio_data = await self.stepfun.text_to_speech(
                    text=narration_text,
                    voice="xiaosi",
                    speed=0.9  # 稍慢，便于理解
                )

                # 保存音频
                audio_filename = f"{paper_id}_audio.mp3"
                audio_path = os.path.join(self.output_dir, audio_filename)
                os.makedirs(self.output_dir, exist_ok=True)

                with open(audio_path, 'wb') as f:
                    f.write(audio_data)

                video_abstract.audio_url = audio_path

            # 3. 生成视频
            if generate_video:
                template = self.TEMPLATES.get(template_id, self.TEMPLATES["academic"])

                # 逐场景生成视频
                video_segments = []
                for scene in script.get('scenes', []):
                    try:
                        video_data = await self.generate_video_scene(
                            scene,
                            paper_data.get('title', ''),
                            template.style
                        )
                        video_segments.append(video_data)
                    except Exception as e:
                        print(f"Error generating scene {scene['type']}: {e}")

                # 合并视频片段（简化处理，实际应使用FFmpeg等工具）
                if video_segments:
                    merged_video = b''.join(video_segments)
                    video_filename = f"{paper_id}_video.mp4"
                    video_path = os.path.join(self.output_dir, video_filename)

                    with open(video_path, 'wb') as f:
                        f.write(merged_video)

                    video_abstract.video_url = video_path

            video_abstract.status = "completed"

        except Exception as e:
            video_abstract.status = "failed"
            print(f"Video generation failed: {e}")

        return video_abstract

    # ==================== 辅助功能 ====================

    async def generate_slide_deck(
        self,
        paper_data: Dict[str, Any],
        num_slides: int = 10
    ) -> List[Dict[str, Any]]:
        """
        生成演示幻灯片

        Args:
            paper_data: 论文数据
            num_slides: 幻灯片数量
        """
        prompt = f"""请为一篇学术论文生成{num_slides}页演示幻灯片的内容。

论文信息:
标题: {paper_data.get('title', '')}
摘要: {paper_data.get('abstract', '')}
方法: {paper_data.get('methodology', '')}
结果: {paper_data.get('results', '')}

请以JSON格式返回每页幻灯片:
[
    {{
        "slide_number": 1,
        "title": "幻灯片标题",
        "content": "主要内容（要点形式）",
        "speaker_notes": "演讲者备注",
        "visual_suggestion": "视觉元素建议"
    }}
]"""

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

            slides = json.loads(json_str.strip())
            return slides
        except:
            return []

    async def generate_conference_pitch(
        self,
        paper_data: Dict[str, Any],
        duration: int = 60
    ) -> Dict[str, Any]:
        """
        生成会议快速介绍（Pitch）

        Args:
            paper_data: 论文数据
            duration: 时长（秒）
        """
        prompt = f"""请为一篇学术论文生成{duration}秒的会议快速介绍（Elevator Pitch）。

论文信息:
{json.dumps(paper_data, ensure_ascii=False)[:5000]}

要求:
1. 开场吸引人（Hook）
2. 清晰的问题陈述
3. 核心方法的亮点
4. 关键结果的冲击
5. 强有力的结尾

请以JSON格式返回:
{{
    "hook": "开场白（10秒）",
    "problem": "问题陈述（15秒）",
    "solution": "解决方案（20秒）",
    "impact": "研究影响（10秒）",
    "closing": "结尾（5秒）",
    "full_script": "完整脚本",
    "key_visuals": ["视觉建议1", "视觉建议2"]
}}"""

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
            return {"raw_pitch": content}

    def get_available_templates(self) -> List[Dict[str, Any]]:
        """获取可用模板列表"""
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "style": t.style,
                "duration": t.duration,
                "scenes_count": len(t.scenes)
            }
            for t in self.TEMPLATES.values()
        ]


# 单例
_video_abstract_service: Optional[VideoAbstractService] = None


def get_video_abstract_service() -> VideoAbstractService:
    """获取视频摘要服务单例"""
    global _video_abstract_service
    if _video_abstract_service is None:
        _video_abstract_service = VideoAbstractService()
    return _video_abstract_service
