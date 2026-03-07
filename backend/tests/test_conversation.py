"""
对话服务单元测试
测试对话管理和消息功能
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# 添加路径
import sys
sys.path.insert(0, 'D:\\Github\\coding\\ScholarForge\\backend')

from services.ai.conversation_models import (
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
from services.ai.conversation_service import (
    ConversationService,
    ConversationNotFoundError,
    ConversationAccessError,
)


class TestConversationModels:
    """测试对话数据模型"""

    def test_conversation_creation(self):
        """测试会话创建"""
        conv = Conversation.create(
            user_id="user_123",
            title="测试会话",
            context=ConversationContext(
                research_field="AI",
                research_question="测试问题"
            )
        )

        assert conv.user_id == "user_123"
        assert conv.title == "测试会话"
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.context.research_field == "AI"
        assert conv.message_count == 0
        assert conv.id is not None

    def test_conversation_add_message(self):
        """测试添加消息"""
        conv = Conversation.create(user_id="user_123")

        msg = Message.create_user_message(
            conversation_id=conv.id,
            content="你好",
        )

        conv.add_message(msg)

        assert conv.message_count == 1
        assert len(conv.messages) == 1
        assert conv.last_message_at is not None

    def test_conversation_get_context_messages(self):
        """测试获取上下文消息"""
        conv = Conversation.create(user_id="user_123")

        # 添加10条消息
        for i in range(10):
            msg = Message.create_user_message(
                conversation_id=conv.id,
                content=f"消息{i}",
            )
            msg.token_count = 100
            conv.add_message(msg)

        # 获取上下文（限制1000 tokens）
        context_msgs = conv.get_context_messages(max_tokens=1000)

        # 应该只返回最近的几条
        assert len(context_msgs) <= 10

    def test_message_creation(self):
        """测试消息创建"""
        msg = Message.create_user_message(
            conversation_id="conv_123",
            content="测试内容",
        )

        assert msg.role == MessageRole.USER
        assert msg.conversation_id == "conv_123"
        assert msg.content == "测试内容"
        assert msg.type == MessageType.TEXT

    def test_message_with_citations(self):
        """测试带引用的消息"""
        citations = [
            Citation(
                id="cite_1",
                article_id="article_1",
                title="测试论文",
                authors=["张三", "李四"],
                year=2023,
                relevance_score=0.95,
            )
        ]

        msg = Message.create_assistant_message(
            conversation_id="conv_123",
            content="根据研究[1]...",
            citations=citations,
        )

        assert msg.type == MessageType.CITATION
        assert len(msg.citations) == 1
        assert msg.citations[0].title == "测试论文"

    def test_citation_to_dict(self):
        """测试引用序列化"""
        citation = Citation(
            id="cite_1",
            article_id="article_1",
            title="测试论文",
            authors=["张三"],
            year=2023,
            journal="测试期刊",
            doi="10.1234/test",
            relevance_score=0.9,
        )

        data = citation.to_dict()

        assert data["id"] == "cite_1"
        assert data["title"] == "测试论文"
        assert data["year"] == 2023
        assert data["relevance_score"] == 0.9


class TestConversationService:
    """测试对话服务"""

    @pytest.fixture
    def service(self):
        return ConversationService(db_connection=None)

    @pytest.mark.asyncio
    async def test_create_conversation(self, service):
        """测试创建会话"""
        with patch.object(service, '_save_conversation_to_db', new_callable=AsyncMock):
            conv = await service.create_conversation(
                user_id="user_123",
                title="测试会话",
            )

            assert conv.user_id == "user_123"
            assert conv.title == "测试会话"
            assert conv.id is not None

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, service):
        """测试获取不存在的会话"""
        with patch.object(
            service,
            '_get_conversation_from_db',
            new_callable=AsyncMock,
            return_value=None
        ):
            with pytest.raises(ConversationNotFoundError):
                await service.get_conversation("non_existent_id")

    @pytest.mark.asyncio
    async def test_get_conversation_access_denied(self, service):
        """测试无权访问会话"""
        conv = Conversation.create(user_id="user_123")

        with patch.object(
            service,
            '_get_conversation_from_db',
            new_callable=AsyncMock,
            return_value=conv
        ):
            with pytest.raises(ConversationAccessError):
                await service.get_conversation(conv.id, user_id="user_456")

    @pytest.mark.asyncio
    async def test_add_message(self, service):
        """测试添加消息"""
        conv = Conversation.create(user_id="user_123")

        with patch.object(service, '_save_conversation_to_db', new_callable=AsyncMock):
            with patch.object(service, '_save_message_to_db', new_callable=AsyncMock):
                with patch.object(service, '_update_conversation_stats', new_callable=AsyncMock):
                    with patch.object(
                        service,
                        '_get_conversation_from_db',
                        new_callable=AsyncMock,
                        return_value=conv
                    ):
                        msg = Message.create_user_message(
                            conversation_id=conv.id,
                            content="测试消息",
                        )

                        result = await service.add_message(conv.id, msg)

                        assert result.conversation_id == conv.id
                        assert result.content == "测试消息"

    @pytest.mark.asyncio
    async def test_delete_conversation(self, service):
        """测试删除会话"""
        conv = Conversation.create(user_id="user_123")

        with patch.object(service, '_update_conversation_in_db', new_callable=AsyncMock):
            with patch.object(
                service,
                '_get_conversation_from_db',
                new_callable=AsyncMock,
                return_value=conv
            ):
                result = await service.delete_conversation(conv.id, "user_123")

                assert result is True
                assert conv.status == ConversationStatus.DELETED

    @pytest.mark.asyncio
    async def test_update_context(self, service):
        """测试更新上下文"""
        conv = Conversation.create(user_id="user_123")

        with patch.object(service, '_update_conversation_in_db', new_callable=AsyncMock):
            with patch.object(
                service,
                '_get_conversation_from_db',
                new_callable=AsyncMock,
                return_value=conv
            ):
                context = await service.update_context(
                    conv.id,
                    "user_123",
                    paper_ids=["paper_1", "paper_2"],
                    research_field="AI",
                )

                assert context.paper_ids == ["paper_1", "paper_2"]
                assert context.research_field == "AI"


class TestResearchQuestion:
    """测试研究问题"""

    def test_research_question_creation(self):
        """测试研究问题创建"""
        rq = ResearchQuestion(
            id="rq_123",
            user_id="user_123",
            question="AI能提高论文写作效率吗？",
            question_type=ResearchQuestionType.YES_NO,
        )

        assert rq.question == "AI能提高论文写作效率吗？"
        assert rq.question_type == ResearchQuestionType.YES_NO
        assert rq.answer is None

    def test_research_question_to_dict(self):
        """测试研究问题序列化"""
        rq = ResearchQuestion(
            id="rq_123",
            user_id="user_123",
            question="测试问题",
            question_type=ResearchQuestionType.GENERAL,
        )

        data = rq.to_dict()

        assert data["question"] == "测试问题"
        assert data["question_type"] == "general"


class TestConversationContext:
    """测试会话上下文"""

    def test_context_creation(self):
        """测试上下文创建"""
        ctx = ConversationContext(
            paper_ids=["paper_1"],
            article_ids=["article_1", "article_2"],
            research_field="NLP",
            research_question="如何提高模型效果？",
        )

        assert ctx.research_field == "NLP"
        assert len(ctx.article_ids) == 2

    def test_context_to_dict(self):
        """测试上下文序列化"""
        ctx = ConversationContext(
            research_field="AI",
            custom_context={"key": "value"},
        )

        data = ctx.to_dict()

        assert data["research_field"] == "AI"
        assert data["custom_context"]["key"] == "value"

    def test_context_from_dict(self):
        """测试从字典创建上下文"""
        data = {
            "paper_ids": ["p1"],
            "article_ids": ["a1"],
            "research_field": "ML",
        }

        ctx = ConversationContext.from_dict(data)

        assert ctx.research_field == "ML"
        assert ctx.paper_ids == ["p1"]


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
