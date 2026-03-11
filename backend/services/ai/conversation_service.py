"""
对话管理服务
管理AI问答对话的创建、查询、更新和删除
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

# 导入异常类定义（放在文件开头避免循环导入）
class ConversationNotFoundError(Exception):
    """会话不存在异常"""
    pass


class ConversationAccessError(Exception):
    """会话访问权限异常"""
    pass


from .conversation_models import (
    Conversation,
    Message,
    Citation,
    ConversationContext,
    ConversationStatus,
    MessageRole,
    MessageType,
    ResearchQuestion,
    ResearchQuestionType,
)


class ConversationService:
    """对话管理服务"""

    def __init__(self, db_connection=None):
        self.db = db_connection
        # 内存缓存（实际应用使用Redis）
        self._cache: Dict[str, Conversation] = {}

    # ========== 会话管理 ==========

    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        context: Optional[ConversationContext] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        创建新会话

        Args:
            user_id: 用户ID
            title: 会话标题（可选，默认根据第一条消息生成）
            context: 会话上下文（关联的论文、文献等）
            metadata: 额外元数据

        Returns:
            Conversation: 新创建的会话
        """
        conversation = Conversation.create(
            user_id=user_id,
            title=title or "新对话",
            context=context,
            metadata=metadata or {},
        )

        # 保存到数据库
        await self._save_conversation_to_db(conversation)

        # 缓存
        self._cache[conversation.id] = conversation

        return conversation

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        include_messages: bool = True
    ) -> Conversation:
        """
        获取会话

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（用于权限验证）
            include_messages: 是否包含消息列表

        Returns:
            Conversation: 会话对象

        Raises:
            ConversationNotFoundError: 会话不存在
            ConversationAccessError: 无访问权限
        """
        # 先查缓存
        if conversation_id in self._cache:
            conversation = self._cache[conversation_id]
            if user_id and conversation.user_id != user_id:
                raise ConversationAccessError("无权访问此会话")
            return conversation

        # 从数据库查询
        conversation = await self._get_conversation_from_db(
            conversation_id,
            include_messages=include_messages
        )

        if not conversation:
            raise ConversationNotFoundError(f"会话 {conversation_id} 不存在")

        if user_id and conversation.user_id != user_id:
            raise ConversationAccessError("无权访问此会话")

        # 缓存
        self._cache[conversation_id] = conversation

        return conversation

    async def list_conversations(
        self,
        user_id: str,
        status: Optional[ConversationStatus] = None,
        limit: int = 20,
        offset: int = 0,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户的会话列表

        Args:
            user_id: 用户ID
            status: 筛选状态
            limit: 每页数量
            offset: 偏移量
            search_query: 搜索关键词

        Returns:
            Dict: 包含会话列表和总数
        """
        # 从数据库查询
        conversations = await self._list_conversations_from_db(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset,
            search_query=search_query
        )

        total = await self._count_conversations_from_db(
            user_id=user_id,
            status=status,
            search_query=search_query
        )

        return {
            "conversations": [c.to_dict(include_messages=False) for c in conversations],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None,
        context: Optional[ConversationContext] = None,
        status: Optional[ConversationStatus] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        更新会话

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（权限验证）
            title: 新标题
            context: 新上下文
            status: 新状态
            metadata: 更新的元数据（合并）

        Returns:
            Conversation: 更新后的会话
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        if title:
            conversation.title = title

        if context:
            conversation.context = context

        if status:
            conversation.status = status

        if metadata:
            conversation.metadata.update(metadata)

        conversation.updated_at = datetime.now()

        # 保存到数据库
        await self._update_conversation_in_db(conversation)

        # 更新缓存
        self._cache[conversation_id] = conversation

        return conversation

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        删除会话

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（权限验证）
            soft_delete: 是否软删除

        Returns:
            bool: 是否成功
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        if soft_delete:
            conversation.status = ConversationStatus.DELETED
            await self._update_conversation_in_db(conversation)
        else:
            await self._delete_conversation_from_db(conversation_id)

        # 清除缓存
        if conversation_id in self._cache:
            del self._cache[conversation_id]

        return True

    async def archive_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> Conversation:
        """
        归档会话

        Args:
            conversation_id: 会话ID
            user_id: 用户ID

        Returns:
            Conversation: 归档后的会话
        """
        return await self.update_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            status=ConversationStatus.ARCHIVED
        )

    # ========== 消息管理 ==========

    async def add_message(
        self,
        conversation_id: str,
        message: Message,
        auto_update_title: bool = False
    ) -> Message:
        """
        添加消息到会话

        Args:
            conversation_id: 会话ID
            message: 消息对象
            auto_update_title: 是否自动更新标题（基于第一条用户消息）

        Returns:
            Message: 添加的消息
        """
        conversation = await self.get_conversation(conversation_id)

        # 确保消息属于该会话
        message.conversation_id = conversation_id

        # 添加到会话
        conversation.add_message(message)

        # 如果是第一条用户消息且没有标题，自动生成标题
        if (auto_update_title and
            message.role == MessageRole.USER and
            conversation.title in ["新对话", "New Conversation"] and
            conversation.message_count == 1):
            conversation.title = conversation.generate_title(message.content, max_length=30)

        # 保存消息到数据库
        await self._save_message_to_db(message)

        # 更新会话统计
        await self._update_conversation_stats(conversation)

        # 更新缓存
        self._cache[conversation_id] = conversation

        return message

    async def get_messages(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        role: Optional[MessageRole] = None
    ) -> List[Message]:
        """
        获取会话的消息列表

        Args:
            conversation_id: 会话ID
            user_id: 用户ID（权限验证）
            limit: 数量限制
            offset: 偏移量
            role: 按角色筛选

        Returns:
            List[Message]: 消息列表
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        messages = conversation.messages

        if role:
            messages = [m for m in messages if m.role == role]

        # 按时间排序（最新的在后面）
        messages = sorted(messages, key=lambda m: m.created_at)

        return messages[offset:offset + limit]

    async def delete_message(
        self,
        conversation_id: str,
        message_id: str,
        user_id: str
    ) -> bool:
        """
        删除消息

        Args:
            conversation_id: 会话ID
            message_id: 消息ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        # 从会话中移除
        conversation.messages = [m for m in conversation.messages if m.id != message_id]
        conversation.message_count = len(conversation.messages)
        conversation.updated_at = datetime.now()

        # 从数据库删除
        await self._delete_message_from_db(message_id)

        # 更新会话
        await self._update_conversation_stats(conversation)

        # 更新缓存
        self._cache[conversation_id] = conversation

        return True

    # ========== 上下文管理 ==========

    async def update_context(
        self,
        conversation_id: str,
        user_id: str,
        paper_ids: Optional[List[str]] = None,
        article_ids: Optional[List[str]] = None,
        research_field: Optional[str] = None,
        research_question: Optional[str] = None,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """
        更新会话上下文

        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            paper_ids: 关联的论文ID列表
            article_ids: 关联的文献ID列表
            research_field: 研究领域
            research_question: 研究问题
            custom_context: 自定义上下文

        Returns:
            ConversationContext: 更新后的上下文
        """
        conversation = await self.get_conversation(conversation_id, user_id)

        if paper_ids is not None:
            conversation.context.paper_ids = paper_ids

        if article_ids is not None:
            conversation.context.article_ids = article_ids

        if research_field is not None:
            conversation.context.research_field = research_field

        if research_question is not None:
            conversation.context.research_question = research_question

        if custom_context is not None:
            conversation.context.custom_context.update(custom_context)

        conversation.updated_at = datetime.now()

        # 保存到数据库
        await self._update_conversation_in_db(conversation)

        # 更新缓存
        self._cache[conversation_id] = conversation

        return conversation.context

    async def get_context_for_llm(
        self,
        conversation_id: str,
        max_messages: int = 10,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        获取用于LLM的上下文

        Args:
            conversation_id: 会话ID
            max_messages: 最大消息数
            max_tokens: 最大token数

        Returns:
            Dict: 包含格式化的上下文信息
        """
        conversation = await self.get_conversation(conversation_id)

        # 获取最近的消息
        messages = conversation.get_context_messages(max_tokens=max_tokens)
        messages = messages[-max_messages:] if len(messages) > max_messages else messages

        # 格式化消息为LLM格式
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        return {
            "conversation_id": conversation_id,
            "title": conversation.title,
            "research_field": conversation.context.research_field,
            "research_question": conversation.context.research_question,
            "related_papers": conversation.context.paper_ids,
            "related_articles": conversation.context.article_ids,
            "message_history": formatted_messages,
            "message_count": len(formatted_messages),
        }

    # ========== 研究问题管理 ==========

    async def create_research_question(
        self,
        user_id: str,
        question: str,
        question_type: ResearchQuestionType = ResearchQuestionType.GENERAL,
        conversation_id: Optional[str] = None
    ) -> ResearchQuestion:
        """
        创建研究问题

        Args:
            user_id: 用户ID
            question: 问题内容
            question_type: 问题类型
            conversation_id: 关联的会话ID

        Returns:
            ResearchQuestion: 创建的研究问题
        """
        import uuid

        rq = ResearchQuestion(
            id=str(uuid.uuid4()),
            user_id=user_id,
            question=question,
            question_type=question_type,
            conversation_id=conversation_id,
        )

        await self._save_research_question_to_db(rq)

        return rq

    async def update_research_question_answer(
        self,
        question_id: str,
        answer: str,
        supporting_evidence: Optional[List[Citation]] = None,
        confidence_score: float = 0.0,
        consensus_level: Optional[str] = None
    ) -> ResearchQuestion:
        """
        更新研究问题的答案

        Args:
            question_id: 问题ID
            answer: 答案内容
            supporting_evidence: 支持证据
            confidence_score: 置信度
            consensus_level: 共识度

        Returns:
            ResearchQuestion: 更新后的问题
        """
        rq = await self._get_research_question_from_db(question_id)

        if not rq:
            raise ConversationNotFoundError(f"研究问题 {question_id} 不存在")

        rq.answer = answer
        if supporting_evidence:
            rq.supporting_evidence = supporting_evidence
        rq.confidence_score = confidence_score
        rq.consensus_level = consensus_level
        rq.answered_at = datetime.now()

        await self._update_research_question_in_db(rq)

        return rq

    # ========== 数据库操作 ==========

    async def _save_conversation_to_db(self, conversation: Conversation):
        """保存会话到数据库"""
        if not self.db:
            return

        from shared.database.models import Conversation as DBConversation

        db_conv = DBConversation(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            type="general",
            context_article_ids=conversation.context.article_ids,
            context_paper_id=conversation.context.paper_ids[0] if conversation.context.paper_ids else None,
            model=conversation.metadata.get("model", "stepfun"),
            temperature=conversation.metadata.get("temperature", 0.7),
            system_prompt=conversation.metadata.get("system_prompt"),
            is_pinned=conversation.metadata.get("is_pinned", False),
            is_archived=conversation.status == ConversationStatus.ARCHIVED,
        )

        self.db.add(db_conv)
        await self.db.flush()

    async def _get_conversation_from_db(
        self,
        conversation_id: str,
        include_messages: bool = True
    ) -> Optional[Conversation]:
        """从数据库获取会话"""
        if not self.db:
            return None

        from shared.database.models import Conversation as DBConversation
        from shared.database.models import Message as DBMessage

        # 查询会话
        result = await self.db.execute(
            select(DBConversation).where(DBConversation.id == conversation_id)
        )
        db_conv = result.scalar_one_or_none()

        if not db_conv:
            return None

        # 构建会话对象
        context = ConversationContext(
            paper_ids=[db_conv.context_paper_id] if db_conv.context_paper_id else [],
            article_ids=db_conv.context_article_ids or [],
        )

        status = ConversationStatus.ARCHIVED if db_conv.is_archived else ConversationStatus.ACTIVE

        conversation = Conversation(
            id=db_conv.id,
            user_id=db_conv.user_id,
            title=db_conv.title,
            status=status,
            context=context,
            messages=[],
            message_count=0,
            created_at=db_conv.created_at,
            updated_at=db_conv.updated_at,
            metadata={
                "model": db_conv.model,
                "temperature": db_conv.temperature,
                "system_prompt": db_conv.system_prompt,
                "is_pinned": db_conv.is_pinned,
            },
        )

        # 查询消息
        if include_messages:
            msg_result = await self.db.execute(
                select(DBMessage)
                .where(DBMessage.conversation_id == conversation_id)
                .order_by(DBMessage.sequence)
            )
            db_messages = msg_result.scalars().all()

            for db_msg in db_messages:
                msg = Message(
                    id=db_msg.id,
                    conversation_id=db_msg.conversation_id,
                    role=MessageRole(db_msg.role),
                    content=db_msg.content,
                    type=MessageType(db_msg.content_type),
                    citations=[Citation(**c) for c in (db_msg.citations or [])],
                    metadata=db_msg.metadata or {},
                    created_at=db_msg.created_at,
                    updated_at=db_msg.updated_at,
                    token_count=db_msg.input_tokens + db_msg.output_tokens,
                )
                conversation.messages.append(msg)

            conversation.message_count = len(conversation.messages)

        return conversation

    async def _list_conversations_from_db(
        self,
        user_id: str,
        status: Optional[ConversationStatus] = None,
        limit: int = 20,
        offset: int = 0,
        search_query: Optional[str] = None
    ) -> List[Conversation]:
        """从数据库获取会话列表"""
        if not self.db:
            return []

        from shared.database.models import Conversation as DBConversation

        query = select(DBConversation).where(DBConversation.user_id == user_id)

        # 状态过滤
        if status == ConversationStatus.ARCHIVED:
            query = query.where(DBConversation.is_archived == True)
        elif status == ConversationStatus.ACTIVE:
            query = query.where(DBConversation.is_archived == False)

        # 搜索
        if search_query:
            query = query.where(DBConversation.title.ilike(f"%{search_query}%"))

        # 排序和分页
        query = query.order_by(DBConversation.updated_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        db_convs = result.scalars().all()

        conversations = []
        for db_conv in db_convs:
            context = ConversationContext(
                paper_ids=[db_conv.context_paper_id] if db_conv.context_paper_id else [],
                article_ids=db_conv.context_article_ids or [],
            )
            conv_status = ConversationStatus.ARCHIVED if db_conv.is_archived else ConversationStatus.ACTIVE

            conv = Conversation(
                id=db_conv.id,
                user_id=db_conv.user_id,
                title=db_conv.title,
                status=conv_status,
                context=context,
                messages=[],
                message_count=0,
                created_at=db_conv.created_at,
                updated_at=db_conv.updated_at,
                metadata={
                    "model": db_conv.model,
                    "temperature": db_conv.temperature,
                },
            )
            conversations.append(conv)

        return conversations

    async def _count_conversations_from_db(
        self,
        user_id: str,
        status: Optional[ConversationStatus] = None,
        search_query: Optional[str] = None
    ) -> int:
        """统计会话数量"""
        if not self.db:
            return 0

        from shared.database.models import Conversation as DBConversation

        query = select(func.count(DBConversation.id)).where(DBConversation.user_id == user_id)

        if status == ConversationStatus.ARCHIVED:
            query = query.where(DBConversation.is_archived == True)
        elif status == ConversationStatus.ACTIVE:
            query = query.where(DBConversation.is_archived == False)

        if search_query:
            query = query.where(DBConversation.title.ilike(f"%{search_query}%"))

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _update_conversation_in_db(self, conversation: Conversation):
        """更新会话到数据库"""
        if not self.db:
            return

        from shared.database.models import Conversation as DBConversation

        await self.db.execute(
            update(DBConversation)
            .where(DBConversation.id == conversation.id)
            .values(
                title=conversation.title,
                context_article_ids=conversation.context.article_ids,
                context_paper_id=conversation.context.paper_ids[0] if conversation.context.paper_ids else None,
                is_archived=conversation.status == ConversationStatus.ARCHIVED,
                updated_at=datetime.now(),
            )
        )

    async def _delete_conversation_from_db(self, conversation_id: str):
        """从数据库删除会话"""
        if not self.db:
            return

        from shared.database.models import Conversation as DBConversation

        await self.db.execute(
            delete(DBConversation).where(DBConversation.id == conversation_id)
        )

    async def _save_message_to_db(self, message: Message):
        """保存消息到数据库"""
        if not self.db:
            return

        from shared.database.models import Message as DBMessage

        # 获取当前会话的最大序号
        max_seq_result = await self.db.execute(
            select(func.max(DBMessage.sequence)).where(DBMessage.conversation_id == message.conversation_id)
        )
        max_seq = max_seq_result.scalar() or 0

        db_msg = DBMessage(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role.value,
            content=message.content,
            content_type=message.type.value,
            citations=[c.to_dict() for c in message.citations],
            metadata=message.metadata,
            input_tokens=0,
            output_tokens=message.token_count,
            sequence=max_seq + 1,
        )

        self.db.add(db_msg)
        await self.db.flush()

    async def _delete_message_from_db(self, message_id: str):
        """从数据库删除消息"""
        if not self.db:
            return

        from shared.database.models import Message as DBMessage

        await self.db.execute(
            delete(DBMessage).where(DBMessage.id == message_id)
        )

    async def _update_conversation_stats(self, conversation: Conversation):
        """更新会话统计信息"""
        if not self.db:
            return

        from shared.database.models import Conversation as DBConversation
        from shared.database.models import Message as DBMessage

        # 统计消息数量
        count_result = await self.db.execute(
            select(func.count(DBMessage.id)).where(DBMessage.conversation_id == conversation.id)
        )
        msg_count = count_result.scalar() or 0

        # 更新会话
        await self.db.execute(
            update(DBConversation)
            .where(DBConversation.id == conversation.id)
            .values(
                updated_at=datetime.now(),
            )
        )

    async def _save_research_question_to_db(self, rq: ResearchQuestion):
        """保存研究问题到数据库"""
        # 研究问题暂不实现数据库存储
        pass

    async def _get_research_question_from_db(self, question_id: str) -> Optional[ResearchQuestion]:
        """从数据库获取研究问题"""
        # 研究问题暂不实现数据库存储
        return None

    async def _update_research_question_in_db(self, rq: ResearchQuestion):
        """更新研究问题到数据库"""
        # 研究问题暂不实现数据库存储
        pass

    # ========== 缓存管理 ==========

    def clear_cache(self, conversation_id: Optional[str] = None):
        """清除缓存"""
        if conversation_id:
            if conversation_id in self._cache:
                del self._cache[conversation_id]
        else:
            self._cache.clear()


# 服务实例
_conversation_service: Optional[ConversationService] = None


def get_conversation_service(db_connection=None) -> ConversationService:
    """获取对话服务单例"""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService(db_connection)
    return _conversation_service
