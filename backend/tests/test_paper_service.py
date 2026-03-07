"""
论文服务单元测试
测试论文CRUD、协作、版本管理等功能
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock


class TestPaperModel:
    """测试论文模型"""

    def test_paper_creation(self, mock_paper):
        """测试论文创建"""
        assert mock_paper["title"] == "Test Paper Title"
        assert mock_paper["status"] == "draft"
        assert mock_paper["owner_id"] == "test-user-id"

    def test_paper_status_transitions(self):
        """测试论文状态转换"""
        valid_statuses = ["draft", "review", "published", "archived"]
        assert "draft" in valid_statuses
        assert "published" in valid_statuses


class TestPaperCRUD:
    """测试论文CRUD操作"""

    @pytest.mark.asyncio
    async def test_create_paper(self, mock_user):
        """测试创建论文"""
        from services.paper.service import PaperService

        service = PaperService()
        paper_data = {
            "title": "New Research Paper",
            "abstract": "Abstract content",
            "content": "Main content",
        }

        with patch.object(service, "_save_paper", return_value={
            "id": "paper-123",
            **paper_data,
            "owner_id": mock_user["id"],
            "status": "draft",
            "created_at": datetime.now().isoformat(),
        }):
            result = await service.create_paper(mock_user["id"], paper_data)

        assert result["id"] == "paper-123"
        assert result["title"] == paper_data["title"]
        assert result["owner_id"] == mock_user["id"]

    @pytest.mark.asyncio
    async def test_get_paper_by_id(self):
        """测试通过ID获取论文"""
        from services.paper.service import PaperService

        service = PaperService()

        with patch.object(service, "_get_paper", return_value={
            "id": "paper-123",
            "title": "Test Paper",
            "status": "draft",
        }):
            result = await service.get_paper("paper-123")

        assert result["id"] == "paper-123"
        assert result["title"] == "Test Paper"

    @pytest.mark.asyncio
    async def test_get_paper_not_found(self):
        """测试获取不存在的论文"""
        from services.paper.service import PaperService

        service = PaperService()

        with patch.object(service, "_get_paper", return_value=None):
            result = await service.get_paper("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_update_paper(self):
        """测试更新论文"""
        from services.paper.service import PaperService

        service = PaperService()
        update_data = {"title": "Updated Title"}

        with patch.object(service, "_update_paper", return_value={
            "id": "paper-123",
            "title": "Updated Title",
            "status": "draft",
        }):
            result = await service.update_paper("paper-123", update_data)

        assert result["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_delete_paper(self):
        """测试删除论文"""
        from services.paper.service import PaperService

        service = PaperService()

        with patch.object(service, "_delete_paper", return_value=True):
            result = await service.delete_paper("paper-123")
            assert result is True


class TestPaperCollaboration:
    """测试论文协作"""

    @pytest.mark.asyncio
    async def test_add_collaborator(self):
        """测试添加协作者"""
        from services.paper.service import PaperService

        service = PaperService()

        with patch.object(service, "_add_collaborator", return_value={
            "paper_id": "paper-123",
            "user_id": "user-456",
            "role": "editor",
        }):
            result = await service.add_collaborator("paper-123", "user-456", "editor")

        assert result["role"] == "editor"

    @pytest.mark.asyncio
    async def test_remove_collaborator(self):
        """测试移除协作者"""
        from services.paper.service import PaperService

        service = PaperService()

        with patch.object(service, "_remove_collaborator", return_value=True):
            result = await service.remove_collaborator("paper-123", "user-456")
            assert result is True


class TestPaperPermissions:
    """测试论文权限"""

    @pytest.mark.asyncio
    async def test_owner_has_full_access(self):
        """测试拥有者有完全访问权限"""
        from services.paper.service import PaperService

        service = PaperService()
        paper = {"id": "paper-123", "owner_id": "user-123"}

        assert await service.has_permission(paper, "user-123", "write") is True
        assert await service.has_permission(paper, "user-123", "delete") is True

    @pytest.mark.asyncio
    async def test_collaborator_has_limited_access(self):
        """测试协作者有有限访问权限"""
        from services.paper.service import PaperService

        service = PaperService()
        paper = {
            "id": "paper-123",
            "owner_id": "user-123",
            "collaborators": [{"user_id": "user-456", "role": "viewer"}]
        }

        # Viewer can read but not delete
        with patch.object(service, "_get_collaborator_role", return_value="viewer"):
            assert await service.has_permission(paper, "user-456", "read") is True
            assert await service.has_permission(paper, "user-456", "delete") is False

    @pytest.mark.asyncio
    async def test_unauthorized_user_has_no_access(self):
        """测试未授权用户无访问权限"""
        from services.paper.service import PaperService

        service = PaperService()
        paper = {"id": "paper-123", "owner_id": "user-123"}

        with patch.object(service, "_get_collaborator_role", return_value=None):
            assert await service.has_permission(paper, "user-999", "read") is False


class TestPaperList:
    """测试论文列表"""

    @pytest.mark.asyncio
    async def test_list_user_papers(self):
        """测试列出用户论文"""
        from services.paper.service import PaperService

        service = PaperService()

        with patch.object(service, "_list_papers", return_value=[
            {"id": "paper-1", "title": "Paper 1"},
            {"id": "paper-2", "title": "Paper 2"},
        ]):
            result = await service.list_user_papers("user-123")

        assert len(result) == 2
        assert result[0]["title"] == "Paper 1"

    @pytest.mark.asyncio
    async def test_list_papers_with_filter(self):
        """测试带过滤条件的论文列表"""
        from services.paper.service import PaperService

        service = PaperService()

        with patch.object(service, "_list_papers", return_value=[
            {"id": "paper-1", "title": "Paper 1", "status": "published"},
        ]):
            result = await service.list_user_papers("user-123", status="published")

        assert len(result) == 1
        assert result[0]["status"] == "published"
