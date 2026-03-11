"""
AI科研助手Agent服务
实现智能Agent的核心逻辑：任务规划、工具调用、记忆管理、主动建议
"""

import uuid
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime, timedelta

from .models import (
    AgentSession, AgentMessage, AgentTask, AgentMemory, ProactiveSuggestion,
    ToolCall, ResearchPlan, AgentStatus, TaskType, ToolType
)


class AIAgentService:
    """AI科研助手Agent服务"""

    def __init__(self):
        # 内存存储（实际应使用数据库）
        self._sessions: Dict[str, AgentSession] = {}
        self._tasks: Dict[str, AgentTask] = {}
        self._memories: Dict[str, AgentMemory] = {}
        self._suggestions: Dict[str, ProactiveSuggestion] = {}
        self._plans: Dict[str, ResearchPlan] = {}

    # ==================== 会话管理 ====================

    def create_session(
        self,
        user_id: str,
        title: str,
        task_type: TaskType,
        context: Optional[Dict] = None
    ) -> AgentSession:
        """创建Agent会话"""
        session = AgentSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            task_type=task_type,
            context=context or {}
        )

        # 添加系统提示
        system_msg = AgentMessage(
            id=str(uuid.uuid4()),
            role="system",
            content=self._get_system_prompt(task_type),
            session_id=session.id
        )
        session.messages.append(system_msg)

        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """获取会话"""
        return self._sessions.get(session_id)

    def list_sessions(
        self,
        user_id: str,
        task_type: Optional[TaskType] = None
    ) -> List[AgentSession]:
        """列出用户会话"""
        sessions = [
            s for s in self._sessions.values()
            if s.user_id == user_id
        ]
        if task_type:
            sessions = [s for s in sessions if s.task_type == task_type]
        return sorted(sessions, key=lambda x: x.updated_at, reverse=True)

    def _get_system_prompt(self, task_type: TaskType) -> str:
        """获取系统提示词"""
        prompts = {
            TaskType.RESEARCH: """你是一个专业的科研助手，擅长文献调研和研究方向分析。
你可以帮助用户：
1. 搜索相关文献
2. 分析研究热点和趋势
3. 识别研究空白
4. 生成文献综述大纲
5. 推荐相关研究方法

请使用专业、准确的学术语言。""",

            TaskType.WRITING: """你是一个学术写作专家，擅长论文写作和润色。
你可以帮助用户：
1. 撰写论文各章节
2. 改进语言表达
3. 检查语法和格式
4. 优化论文结构
5. 生成摘要和结论

请确保写作符合学术规范。""",

            TaskType.ANALYSIS: """你是一个数据分析专家，擅长科研数据处理和分析。
你可以帮助用户：
1. 分析实验数据
2. 选择合适的统计方法
3. 解释分析结果
4. 生成数据可视化建议
5. 检查数据质量

请提供准确、可靠的分析建议。""",

            TaskType.CODING: """你是一个科研编程专家，擅长科学计算和算法实现。
你可以帮助用户：
1. 编写数据分析代码
2. 实现算法
3. 调试程序
4. 优化代码性能
5. 生成技术文档

请编写清晰、高效的代码，并添加必要的注释。""",

            TaskType.PLANNING: """你是一个研究规划专家，擅长项目管理和时间规划。
你可以帮助用户：
1. 制定研究计划
2. 分解项目任务
3. 设置里程碑
4. 评估风险
5. 优化资源配置

请提供切实可行的规划建议。""",

            TaskType.REVIEW: """你是一个论文审稿专家，擅长学术质量评估。
你可以帮助用户：
1. 审阅论文初稿
2. 识别逻辑漏洞
3. 评估方法合理性
4. 检查引用规范
5. 提供改进建议

请保持客观、专业的态度。""",

            TaskType.BRAINSTORMING: """你是一个创新思维专家，擅长激发科研灵感。
你可以帮助用户：
1. 拓展研究思路
2. 提出创新假设
3. 探索跨学科联系
4. 设计实验方案
5. 解决研究难题

请保持开放、创造性的思维。"""
        }
        return prompts.get(task_type, prompts[TaskType.RESEARCH])

    # ==================== 对话处理 ====================

    async def chat(
        self,
        session_id: str,
        user_message: str,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        与Agent对话
        支持流式响应
        """
        session = self._sessions.get(session_id)
        if not session:
            yield json.dumps({"error": "Session not found"})
            return

        # 更新状态
        session.status = AgentStatus.THINKING
        session.updated_at = datetime.utcnow()

        # 添加用户消息
        user_msg = AgentMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=user_message,
            session_id=session_id
        )
        session.messages.append(user_msg)

        # 分析用户意图
        intent = self._analyze_intent(user_message)

        # 如果需要工具调用
        if intent.get("requires_tool"):
            session.status = AgentStatus.EXECUTING

            # 执行工具调用
            tool_results = await self._execute_tools(
                session_id,
                intent.get("tools", [])
            )

            # 添加工具消息
            for result in tool_results:
                tool_msg = AgentMessage(
                    id=str(uuid.uuid4()),
                    role="tool",
                    content=result.get("result", ""),
                    session_id=session_id,
                    metadata={"tool_type": result.get("tool_type")}
                )
                session.messages.append(tool_msg)

        # 生成AI响应
        if stream:
            async for chunk in self._generate_stream_response(session, user_message):
                yield chunk
        else:
            response = await self._generate_response(session, user_message)
            yield json.dumps({
                "type": "complete",
                "content": response
            })

        session.status = AgentStatus.IDLE

    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """分析用户意图，判断是否需要工具调用"""
        intent = {
            "requires_tool": False,
            "tools": []
        }

        # 简单关键词匹配（实际应使用NLP模型）
        tool_keywords = {
            ToolType.SEARCH_PAPERS: ["搜索", "查找", "文献", "论文", "相关研究"],
            ToolType.READ_PAPER: ["阅读", "分析", "这篇论文", "PDF"],
            ToolType.GENERATE_CONTENT: ["写作", "撰写", "生成", "草稿"],
            ToolType.CHECK_GRAMMAR: ["检查", "润色", "语法", "修改"],
            ToolType.FORMAT_REFERENCES: ["引用", "参考文献", "格式"],
            ToolType.CREATE_OUTLINE: ["大纲", "结构", "框架"],
            ToolType.SUMMARIZE: ["总结", "摘要", "概括"],
            ToolType.TRANSLATE: ["翻译", "英文", "中文"],
        }

        for tool_type, keywords in tool_keywords.items():
            if any(kw in message for kw in keywords):
                intent["requires_tool"] = True
                intent["tools"].append({
                    "type": tool_type,
                    "parameters": {"query": message}
                })

        return intent

    async def _execute_tools(
        self,
        session_id: str,
        tools: List[Dict]
    ) -> List[Dict]:
        """执行工具调用"""
        results = []

        for tool in tools:
            tool_call = ToolCall(
                id=str(uuid.uuid4()),
                tool_type=tool["type"],
                parameters=tool.get("parameters", {})
            )

            # 模拟工具执行
            result = await self._mock_tool_execution(tool_call)
            tool_call.result = result
            tool_call.status = "completed"
            tool_call.completed_at = datetime.utcnow()

            results.append({
                "tool_type": tool["type"].value,
                "result": result
            })

        return results

    async def _mock_tool_execution(self, tool_call: ToolCall) -> str:
        """模拟工具执行（实际应调用真实工具）"""
        tool_type = tool_call.tool_type
        params = tool_call.parameters

        if tool_type == ToolType.SEARCH_PAPERS:
            return f"已搜索到10篇相关文献，包括：Transformer架构、注意力机制、BERT模型等"

        elif tool_type == ToolType.SUMMARIZE:
            return "这篇论文提出了一个新的注意力机制，在多个基准测试中取得了SOTA结果..."

        elif tool_type == ToolType.CREATE_OUTLINE:
            return """已生成论文大纲：
1. 引言
   1.1 研究背景
   1.2 问题陈述
2. 相关工作
   2.1 传统方法
   2.2 深度学习方法
3. 方法
   3.1 模型架构
   3.2 训练策略
4. 实验
5. 结论"""

        elif tool_type == ToolType.CHECK_GRAMMAR:
            return "已检查完成，发现3处语法问题，建议修改：..."

        else:
            return f"工具 {tool_type.value} 执行完成"

    async def _generate_stream_response(
        self,
        session: AgentSession,
        user_message: str
    ) -> AsyncGenerator[str, None]:
        """生成流式响应"""
        # 获取相关记忆
        memories = self._get_relevant_memories(
            session.user_id,
            user_message,
            limit=3
        )

        # 构建提示
        memory_context = ""
        if memories:
            memory_context = "\n相关背景信息：\n" + "\n".join([
                f"- {m.content}" for m in memories
            ])

        # 模拟流式生成
        response_parts = self._simulate_agent_response(
            session.task_type,
            user_message,
            memory_context
        )

        full_content = ""
        for part in response_parts:
            full_content += part
            yield json.dumps({
                "type": "chunk",
                "content": part
            })

        # 保存AI消息
        ai_msg = AgentMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=full_content,
            session_id=session.id
        )
        session.messages.append(ai_msg)

        # 提取记忆
        self._extract_memory(session.user_id, user_message, full_content)

        yield json.dumps({
            "type": "complete",
            "content": full_content
        })

    async def _generate_response(
        self,
        session: AgentSession,
        user_message: str
    ) -> str:
        """生成完整响应（非流式）"""
        parts = []
        async for chunk in self._generate_stream_response(session, user_message):
            data = json.loads(chunk)
            if data.get("type") == "complete":
                return data.get("content", "")
            parts.append(data.get("content", ""))
        return "".join(parts)

    def _simulate_agent_response(
        self,
        task_type: TaskType,
        user_message: str,
        memory_context: str
    ) -> List[str]:
        """模拟Agent响应（实际应调用LLM）"""
        # 模拟思考过程
        thinking = [
            "让我分析一下您的需求...",
            "根据您的问题，",
            "我需要搜索相关资料...",
            memory_context if memory_context else "",
            "\n"
        ]

        # 根据任务类型生成回复
        if task_type == TaskType.RESEARCH:
            response = [
                "这是一个很有价值的研究方向。",
                "\n\n基于我的分析，",
                "我建议您可以从以下几个方面入手：",
                "\n1. 首先阅读Transformer和BERT相关的经典论文",
                "\n2. 关注最近2年的顶会论文（NeurIPS、ICML、ACL）",
                "\n3. 使用ScholarForge的文献综述功能整理思路",
                "\n\n需要我帮您生成一个详细的研究计划吗？"
            ]
        elif task_type == TaskType.WRITING:
            response = [
                "我理解您需要写作帮助。",
                "\n\n让我为您生成一个初步的草稿：",
                "\n\n**1. 引言**",
                "\n近年来，深度学习技术在自然语言处理领域取得了突破性进展...",
                "\n\n**2. 方法概述**",
                "\n本文提出的方法基于注意力机制...",
                "\n\n您希望我对哪个部分进行详细展开？"
            ]
        elif task_type == TaskType.ANALYSIS:
            response = [
                "我来帮您分析这个数据。",
                "\n\n从数据分布来看：",
                "\n- 样本总量：1000个",
                "\n- 平均值：0.75",
                "\n- 标准差：0.12",
                "\n\n**统计检验结果**：",
                "\nt值 = 3.45, p < 0.001，结果显著。",
                "\n\n建议您使用柱状图展示组间差异，需要我生成可视化代码吗？"
            ]
        else:
            response = [
                "收到您的请求。",
                "\n\n我正在处理中...",
                "\n\n根据当前情况，我建议：",
                "\n1. 先明确具体目标",
                "\n2. 制定详细的执行计划",
                "\n3. 分阶段验证结果",
                "\n\n有什么我可以具体帮助您的吗？"
            ]

        return thinking + response

    # ==================== 记忆管理 ====================

    def _extract_memory(
        self,
        user_id: str,
        user_message: str,
        ai_response: str
    ) -> None:
        """从对话中提取记忆"""
        # 提取用户偏好
        preferences = self._extract_preferences(user_message)
        for pref in preferences:
            memory = AgentMemory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                content=pref,
                memory_type="preference",
                importance=0.8
            )
            self._memories[memory.id] = memory

        # 提取事实信息
        facts = self._extract_facts(user_message, ai_response)
        for fact in facts:
            memory = AgentMemory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                content=fact,
                memory_type="fact",
                importance=0.6
            )
            self._memories[memory.id] = memory

    def _extract_preferences(self, message: str) -> List[str]:
        """提取用户偏好"""
        preferences = []

        # 研究兴趣
        if "研究方向" in message or "感兴趣" in message:
            preferences.append(f"研究兴趣：{message}")

        # 写作风格
        if "正式" in message or "简洁" in message:
            preferences.append(f"偏好风格：{message}")

        return preferences

    def _extract_facts(self, user_msg: str, ai_msg: str) -> List[str]:
        """提取事实信息"""
        facts = []

        # 论文信息
        if "论文" in user_msg:
            facts.append(f"正在处理的论文：{user_msg[:50]}...")

        # 研究主题
        if "研究" in user_msg:
            facts.append(f"研究主题相关：{user_msg[:50]}...")

        return facts

    def _get_relevant_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[AgentMemory]:
        """获取相关记忆"""
        memories = [
            m for m in self._memories.values()
            if m.user_id == user_id
        ]

        # 简单相关性排序（实际应使用向量相似度）
        for m in memories:
            # 更新访问信息
            words = set(query.lower().split())
            memory_words = set(m.content.lower().split())
            overlap = len(words & memory_words)
            m.access_count += 1
            m.last_accessed = datetime.utcnow()

        # 按重要性和相关性排序
        memories.sort(
            key=lambda x: (x.importance, x.access_count),
            reverse=True
        )

        return memories[:limit]

    # ==================== 主动建议 ====================

    def generate_proactive_suggestions(self, user_id: str) -> List[ProactiveSuggestion]:
        """生成主动建议"""
        suggestions = []

        # 基于用户活动生成建议
        user_sessions = self.list_sessions(user_id)

        # 建议1：如果长时间没有写作
        if user_sessions:
            last_session = user_sessions[0]
            days_since = (datetime.utcnow() - last_session.updated_at).days

            if days_since > 3:
                suggestion = ProactiveSuggestion(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    title="继续您的论文写作",
                    description=f"您已有{days_since}天没有进行写作了。要继续之前的进度吗？",
                    action_type="write",
                    trigger_context={"last_session_id": last_session.id}
                )
                suggestions.append(suggestion)
                self._suggestions[suggestion.id] = suggestion

        # 建议2：基于研究计划
        plans = self.list_research_plans(user_id)
        for plan in plans:
            # 检查即将到期的里程碑
            for milestone in plan.milestones:
                due_date = milestone.get("due_date")
                if due_date and isinstance(due_date, str):
                    due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    days_left = (due_date - datetime.utcnow()).days

                    if 0 < days_left <= 7:
                        suggestion = ProactiveSuggestion(
                            id=str(uuid.uuid4()),
                            user_id=user_id,
                            title=f"里程碑提醒：{milestone.get('title', '')}",
                            description=f"距离'{milestone.get('title')}'截止还有{days_left}天",
                            action_type="remind",
                            trigger_context={"milestone_id": milestone.get('id'), "plan_id": plan.id}
                        )
                        suggestions.append(suggestion)
                        self._suggestions[suggestion.id] = suggestion

        # 建议3：文献调研提醒
        research_sessions = [s for s in user_sessions if s.task_type == TaskType.RESEARCH]
        if len(research_sessions) > 3:
            suggestion = ProactiveSuggestion(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title="整理文献综述",
                description="您已调研了多篇文献，建议整理成文献综述",
                action_type="write"
            )
            suggestions.append(suggestion)
            self._suggestions[suggestion.id] = suggestion

        return suggestions

    def get_suggestions(self, user_id: str, include_dismissed: bool = False) -> List[ProactiveSuggestion]:
        """获取用户的建议"""
        suggestions = [
            s for s in self._suggestions.values()
            if s.user_id == user_id
            and (include_dismissed or not s.is_dismissed)
        ]
        return sorted(suggestions, key=lambda x: x.created_at, reverse=True)

    def accept_suggestion(self, suggestion_id: str) -> bool:
        """接受建议"""
        suggestion = self._suggestions.get(suggestion_id)
        if suggestion:
            suggestion.is_accepted = True
            return True
        return False

    def dismiss_suggestion(self, suggestion_id: str) -> bool:
        """忽略建议"""
        suggestion = self._suggestions.get(suggestion_id)
        if suggestion:
            suggestion.is_dismissed = True
            return True
        return False

    # ==================== 研究计划 ====================

    def create_research_plan(
        self,
        user_id: str,
        title: str,
        objectives: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ResearchPlan:
        """创建研究计划"""
        plan = ResearchPlan(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            objectives=objectives,
            start_date=start_date,
            end_date=end_date
        )

        # 自动生成里程碑和任务
        plan.milestones = self._generate_milestones(objectives, start_date, end_date)
        plan.tasks = self._generate_tasks(objectives, plan.milestones)

        self._plans[plan.id] = plan
        return plan

    def _generate_milestones(
        self,
        objectives: List[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """生成里程碑"""
        milestones = [
            {"id": str(uuid.uuid4()), "title": "文献调研完成", "order": 1},
            {"id": str(uuid.uuid4()), "title": "实验设计完成", "order": 2},
            {"id": str(uuid.uuid4()), "title": "数据收集完成", "order": 3},
            {"id": str(uuid.uuid4()), "title": "论文初稿完成", "order": 4},
            {"id": str(uuid.uuid4()), "title": "论文定稿提交", "order": 5}
        ]

        # 分配日期
        if start_date and end_date:
            total_days = (end_date - start_date).days
            for i, milestone in enumerate(milestones):
                milestone["due_date"] = (
                    start_date + timedelta(days=int(total_days * (i + 1) / len(milestones)))
                ).isoformat()

        return milestones

    def _generate_tasks(
        self,
        objectives: List[str],
        milestones: List[Dict]
    ) -> List[Dict[str, Any]]:
        """生成任务列表"""
        tasks = []

        for obj in objectives:
            tasks.extend([
                {"id": str(uuid.uuid4()), "title": f"研究：{obj[:30]}...", "status": "todo"},
                {"id": str(uuid.uuid4()), "title": f"实验：验证{obj[:20]}...", "status": "todo"},
                {"id": str(uuid.uuid4()), "title": f"写作：撰写{obj[:20]}...", "status": "todo"}
            ])

        return tasks

    def get_research_plan(self, plan_id: str) -> Optional[ResearchPlan]:
        """获取研究计划"""
        return self._plans.get(plan_id)

    def list_research_plans(self, user_id: str) -> List[ResearchPlan]:
        """列出用户的研究计划"""
        plans = [
            p for p in self._plans.values()
            if p.user_id == user_id
        ]
        return sorted(plans, key=lambda x: x.updated_at, reverse=True)

    def update_plan_progress(
        self,
        plan_id: str,
        milestone_id: Optional[str] = None,
        task_id: Optional[str] = None,
        status: str = "completed"
    ) -> Optional[ResearchPlan]:
        """更新计划进度"""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        if milestone_id:
            for m in plan.milestones:
                if m.get("id") == milestone_id:
                    m["status"] = status
                    m["completed_at"] = datetime.utcnow().isoformat()

        if task_id:
            for t in plan.tasks:
                if t.get("id") == task_id:
                    t["status"] = status
                    t["completed_at"] = datetime.utcnow().isoformat()

        plan.updated_at = datetime.utcnow()
        return plan

    # ==================== 任务执行 ====================

    def create_task(
        self,
        session_id: str,
        description: str,
        steps: Optional[List[Dict]] = None
    ) -> AgentTask:
        """创建Agent任务"""
        task = AgentTask(
            id=str(uuid.uuid4()),
            session_id=session_id,
            description=description,
            steps=steps or []
        )

        self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """获取任务"""
        return self._tasks.get(task_id)

    async def execute_task(self, task_id: str) -> AsyncGenerator[Dict, None]:
        """执行任务"""
        task = self._tasks.get(task_id)
        if not task:
            yield {"error": "Task not found"}
            return

        task.status = "running"
        total_steps = len(task.steps) or 1

        for i, step in enumerate(task.steps or [{"action": "execute"}]):
            task.current_step_index = i
            task.progress = (i / total_steps) * 100

            yield {
                "type": "progress",
                "step": i + 1,
                "total": total_steps,
                "action": step.get("action", "processing"),
                "progress": task.progress
            }

            # 模拟执行
            import asyncio
            await asyncio.sleep(0.5)

        task.status = "completed"
        task.progress = 100.0
        task.completed_at = datetime.utcnow()
        task.result = "任务执行完成"

        yield {
            "type": "complete",
            "result": task.result
        }


# 单例
_ai_agent_service = None


def get_ai_agent_service() -> AIAgentService:
    """获取AI Agent服务单例"""
    global _ai_agent_service
    if _ai_agent_service is None:
        _ai_agent_service = AIAgentService()
    return _ai_agent_service
