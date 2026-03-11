"""
AI科研助手Agent模型
定义Agent、对话、工具调用、记忆等核心模型
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(str, Enum):
    """Agent状态"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"  # 等待用户输入
    ERROR = "error"


class TaskType(str, Enum):
    """任务类型"""
    RESEARCH = "research"           # 文献调研
    WRITING = "writing"             # 写作辅助
    ANALYSIS = "analysis"           # 数据分析
    CODING = "coding"               # 代码辅助
    PLANNING = "planning"           # 研究规划
    REVIEW = "review"               # 论文审阅
    BRAINSTORMING = "brainstorming" # 头脑风暴


class ToolType(str, Enum):
    """工具类型"""
    SEARCH_PAPERS = "search_papers"         # 搜索论文
    READ_PAPER = "read_paper"               # 阅读论文
    GENERATE_CONTENT = "generate_content"   # 生成内容
    ANALYZE_DATA = "analyze_data"           # 分析数据
    CHECK_GRAMMAR = "check_grammar"         # 语法检查
    FORMAT_REFERENCES = "format_references" # 格式化引用
    CREATE_OUTLINE = "create_outline"       # 创建大纲
    SUMMARIZE = "summarize"                 # 总结
    TRANSLATE = "translate"                 # 翻译
    EXECUTE_CODE = "execute_code"           # 执行代码


@dataclass
class AgentMemory:
    """Agent记忆单元"""
    id: str
    user_id: str
    content: str                    # 记忆内容
    memory_type: str                # fact/preference/context/task
    importance: float = 1.0         # 重要性评分 (0-1)
    source: Optional[str] = None    # 来源（哪次对话）
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0


@dataclass
class ToolCall:
    """工具调用记录"""
    id: str
    tool_type: ToolType
    parameters: Dict[str, Any]      # 调用参数
    result: Optional[str] = None    # 执行结果
    status: str = "pending"         # pending/running/completed/failed
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class AgentMessage:
    """Agent对话消息"""
    id: str
    role: str                       # user/assistant/system/tool
    content: str
    session_id: str

    # 如果是工具调用
    tool_calls: List[ToolCall] = field(default_factory=list)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentSession:
    """Agent对话会话"""
    id: str
    user_id: str
    title: str
    task_type: TaskType

    # 状态
    status: AgentStatus = AgentStatus.IDLE
    current_step: int = 0
    total_steps: int = 0

    # 对话历史
    messages: List[AgentMessage] = field(default_factory=list)

    # 上下文信息
    context: Dict[str, Any] = field(default_factory=dict)

    # 相关资源
    paper_ids: List[str] = field(default_factory=list)
    project_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentTask:
    """Agent执行的任务"""
    id: str
    session_id: str
    description: str                # 任务描述

    # 执行计划
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step_index: int = 0

    # 执行结果
    result: Optional[str] = None
    outputs: List[Dict[str, Any]] = field(default_factory=list)

    # 状态
    status: str = "pending"         # pending/running/completed/failed
    progress: float = 0.0           # 0-100

    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class ProactiveSuggestion:
    """主动建议"""
    id: str
    user_id: str

    # 建议内容
    title: str
    description: str
    action_type: str                # write/read/analyze/remind

    # 触发条件
    trigger_context: Dict[str, Any] = field(default_factory=dict)

    # 用户反馈
    is_accepted: Optional[bool] = None
    is_dismissed: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class ResearchPlan:
    """研究计划"""
    id: str
    user_id: str
    title: str

    # 研究目标
    objectives: List[str] = field(default_factory=list)

    # 里程碑
    milestones: List[Dict[str, Any]] = field(default_factory=list)

    # 任务分解
    tasks: List[Dict[str, Any]] = field(default_factory=list)

    # 时间安排
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # 风险与对策
    risks: List[Dict[str, str]] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
