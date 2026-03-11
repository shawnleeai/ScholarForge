"""
对话会话模型
定义AI问答对话系统的数据模型
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import uuid


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    CITATION = "citation"  # 带引用的回答
    ERROR = "error"
    STREAMING = "streaming"  # 流式响应中


class ConversationStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ResearchQuestionType(str, Enum):
    """研究问题类型"""
    YES_NO = "yes_no"  # 是/否问题
    HOW = "how"  # 如何/方法问题
    WHY = "why"  # 为什么/因果问题
    WHAT = "what"  # 是什么/定义问题
    COMPARE = "compare"  # 对比问题
    GENERAL = "general"  # 一般性问题


@dataclass
class Citation:
    """引用信息"""
    id: str
    article_id: str
    title: str
    authors: List[str]
    year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    snippet: str = ""  # 引用片段
    relevance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "article_id": self.article_id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "url": self.url,
            "snippet": self.snippet,
            "relevance_score": self.relevance_score,
        }


@dataclass
class Message:
    """对话消息"""
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    type: MessageType = MessageType.TEXT
    citations: List[Citation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    parent_id: Optional[str] = None  # 支持线程式回复
    token_count: int = 0
    latency_ms: Optional[int] = None  # 响应延迟

    def __post_init__(self):
        if isinstance(self.role, str):
            self.role = MessageRole(self.role)
        if isinstance(self.type, str):
            self.type = MessageType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role.value,
            "content": self.content,
            "type": self.type.value,
            "citations": [c.to_dict() for c in self.citations],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "parent_id": self.parent_id,
            "token_count": self.token_count,
            "latency_ms": self.latency_ms,
        }

    @classmethod
    def create_user_message(
        cls,
        conversation_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Message":
        """创建用户消息"""
        return cls(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            type=MessageType.TEXT,
            metadata=metadata or {},
        )

    @classmethod
    def create_assistant_message(
        cls,
        conversation_id: str,
        content: str,
        citations: Optional[List[Citation]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Message":
        """创建助手消息"""
        msg_type = MessageType.CITATION if citations else MessageType.TEXT
        return cls(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            type=msg_type,
            citations=citations or [],
            metadata=metadata or {},
        )


@dataclass
class ConversationContext:
    """会话上下文"""
    # 关联的论文ID
    paper_ids: List[str] = field(default_factory=list)
    # 关联的文献ID
    article_ids: List[str] = field(default_factory=list)
    # 研究领域/主题
    research_field: Optional[str] = None
    # 研究问题
    research_question: Optional[str] = None
    # 自定义上下文
    custom_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_ids": self.paper_ids,
            "article_ids": self.article_ids,
            "research_field": self.research_field,
            "research_question": self.research_question,
            "custom_context": self.custom_context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        return cls(
            paper_ids=data.get("paper_ids", []),
            article_ids=data.get("article_ids", []),
            research_field=data.get("research_field"),
            research_question=data.get("research_question"),
            custom_context=data.get("custom_context", {}),
        )


@dataclass
class Conversation:
    """对话会话"""
    id: str
    user_id: str
    title: str
    status: ConversationStatus = ConversationStatus.ACTIVE
    context: ConversationContext = field(default_factory=ConversationContext)
    messages: List[Message] = field(default_factory=list)
    message_count: int = 0
    total_tokens: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_message_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = ConversationStatus(self.status)
        if isinstance(self.context, dict):
            self.context = ConversationContext.from_dict(self.context)

    def to_dict(self, include_messages: bool = True) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "status": self.status.value,
            "context": self.context.to_dict(),
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "metadata": self.metadata,
        }
        if include_messages:
            result["messages"] = [m.to_dict() for m in self.messages]
        return result

    def add_message(self, message: Message) -> None:
        """添加消息"""
        self.messages.append(message)
        self.message_count += 1
        self.total_tokens += message.token_count
        self.last_message_at = message.created_at
        self.updated_at = datetime.now()

    def get_last_n_messages(self, n: int = 5) -> List[Message]:
        """获取最近的n条消息"""
        return self.messages[-n:] if len(self.messages) >= n else self.messages

    def get_context_messages(self, max_tokens: int = 4000) -> List[Message]:
        """
        获取上下文消息（用于LLM）
        优先保留最近的消息，同时确保不超过token限制
        """
        messages = []
        total_tokens = 0

        # 从后向前遍历，保留最近的消息
        for msg in reversed(self.messages):
            if total_tokens + msg.token_count > max_tokens:
                break
            messages.insert(0, msg)
            total_tokens += msg.token_count

        return messages

    def generate_title(self, first_message_content: str, max_length: int = 50) -> str:
        """基于第一条消息生成标题"""
        # 移除多余空白，限制长度
        title = first_message_content.strip()
        if len(title) > max_length:
            title = title[:max_length] + "..."
        return title

    @classmethod
    def create(
        cls,
        user_id: str,
        title: Optional[str] = None,
        context: Optional[ConversationContext] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Conversation":
        """创建新会话"""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title or "新对话",
            status=ConversationStatus.ACTIVE,
            context=context or ConversationContext(),
            metadata=metadata or {},
        )


@dataclass
class ChatSession:
    """聊天会话（用于WebSocket连接管理）"""
    id: str
    user_id: str
    conversation_id: str
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity_at: datetime = field(default_factory=datetime.now)
    client_info: Dict[str, Any] = field(default_factory=dict)
    is_streaming: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "connected_at": self.connected_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat(),
            "client_info": self.client_info,
            "is_streaming": self.is_streaming,
        }


@dataclass
class ResearchQuestion:
    """研究问题"""
    id: str
    user_id: str
    question: str
    question_type: ResearchQuestionType
    conversation_id: Optional[str] = None
    answer: Optional[str] = None
    supporting_evidence: List[Citation] = field(default_factory=list)
    confidence_score: float = 0.0  # 答案置信度
    consensus_level: Optional[str] = None  # 学术界共识度
    created_at: datetime = field(default_factory=datetime.now)
    answered_at: Optional[datetime] = None

    def __post_init__(self):
        if isinstance(self.question_type, str):
            self.question_type = ResearchQuestionType(self.question_type)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question": self.question,
            "question_type": self.question_type.value,
            "conversation_id": self.conversation_id,
            "answer": self.answer,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "confidence_score": self.confidence_score,
            "consensus_level": self.consensus_level,
            "created_at": self.created_at.isoformat(),
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
        }


# 用于数据库存储的Schema定义（Pydantic风格）
CONVERSATION_SCHEMA = {
    "id": "VARCHAR(36) PRIMARY KEY",
    "user_id": "VARCHAR(36) NOT NULL",
    "title": "VARCHAR(200) NOT NULL",
    "status": "VARCHAR(20) DEFAULT 'active'",
    "context": "JSON",
    "message_count": "INTEGER DEFAULT 0",
    "total_tokens": "INTEGER DEFAULT 0",
    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "last_message_at": "TIMESTAMP",
    "metadata": "JSON",
}

MESSAGE_SCHEMA = {
    "id": "VARCHAR(36) PRIMARY KEY",
    "conversation_id": "VARCHAR(36) NOT NULL",
    "role": "VARCHAR(20) NOT NULL",
    "content": "TEXT NOT NULL",
    "type": "VARCHAR(20) DEFAULT 'text'",
    "citations": "JSON",
    "metadata": "JSON",
    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "updated_at": "TIMESTAMP",
    "parent_id": "VARCHAR(36)",
    "token_count": "INTEGER DEFAULT 0",
    "latency_ms": "INTEGER",
}


# 测试代码
if __name__ == "__main__":
    # 创建测试对话
    conversation = Conversation.create(
        user_id="user_123",
        context=ConversationContext(
            research_field="人工智能",
            research_question="深度学习在NLP中的应用",
        )
    )

    # 添加用户消息
    user_msg = Message.create_user_message(
        conversation_id=conversation.id,
        content="请总结一下深度学习在自然语言处理中的主要应用",
    )
    conversation.add_message(user_msg)

    # 更新标题
    conversation.title = conversation.generate_title(user_msg.content)

    # 添加助手消息（带引用）
    citations = [
        Citation(
            id="cite_1",
            article_id="paper_123",
            title="Attention Is All You Need",
            authors=["Vaswani et al."],
            year=2017,
            journal="NIPS",
            snippet="Transformer架构彻底改变了NLP领域...",
            relevance_score=0.95,
        )
    ]
    assistant_msg = Message.create_assistant_message(
        conversation_id=conversation.id,
        content="深度学习在NLP中有以下几个主要应用：...",
        citations=citations,
        metadata={"model": "gpt-4", "provider": "openai"},
    )
    conversation.add_message(assistant_msg)

    # 打印对话信息
    print(f"对话标题: {conversation.title}")
    print(f"消息数量: {conversation.message_count}")
    print(f"总Token数: {conversation.total_tokens}")
    print(f"上下文: {conversation.context.to_dict()}")

    # 打印消息
    for msg in conversation.messages:
        print(f"\n[{msg.role.value}] {msg.created_at}")
        print(f"内容: {msg.content[:50]}...")
        if msg.citations:
            print(f"引用: {len(msg.citations)} 篇文献")
