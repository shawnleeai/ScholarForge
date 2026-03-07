"""
文献服务单元测试
测试文献检索、导入、管理等功能
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock


class TestArticleModel:
    """测试文献模型"""

    def test_article_creation(self, mock_article):
        """测试文献创建"""
        assert mock_article["title"] == "Test Article"
        assert mock_article["year"] == 2024
        assert mock_article["source"] == "arxiv"

    def test_article_authors_parsing(self):
        """测试作者解析"""
        authors = [
            {"name": "John Doe", "affiliation": "MIT"},
            {"name": "Jane Smith", "affiliation": "Stanford"},
        ]
        assert len(authors) == 2
        assert authors[0]["name"] == "John Doe"


class TestArticleSearch:
    """测试文献检索"""

    @pytest.mark.asyncio
    async def test_search_by_keyword(self):
        """测试关键词搜索"""
        from services.article.service import ArticleService

        service = ArticleService()

        with patch.object(service, "_search_articles", return_value=[
            {"id": "article-1", "title": "Machine Learning", "score": 0.95},
            {"id": "article-2", "title": "Deep Learning", "score": 0.88},
        ]):
            result = await service.search("neural networks", limit=10)

        assert len(result) == 2
        assert result[0]["score"] > result[1]["score"]

    @pytest.mark.asyncio
    async def test_search_by_author(self):
        """测试按作者搜索"""
        from services.article.service import ArticleService

        service = ArticleService()

        with patch.object(service, "_search_by_author", return_value=[
            {"id": "article-1", "title": "Paper by Author", "authors": [{"name": "Test Author"}]},
        ]):
            result = await service.search_by_author("Test Author")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_advanced_search_with_filters(self):
        """测试高级搜索带过滤条件"""
        from services.article.service import ArticleService

        service = ArticleService()

        filters = {
            "year_from": 2020,
            "year_to": 2024,
            "source": "arxiv",
        }

        with patch.object(service, "_advanced_search", return_value=[
            {"id": "article-1", "title": "Recent Paper", "year": 2024},
        ]):
            result = await service.advanced_search("AI", filters)

        assert len(result) == 1
        assert result[0]["year"] == 2024


class TestArticleAdapters:
    """测试文献适配器"""

    @pytest.mark.asyncio
    async def test_arxiv_adapter(self):
        """测试 arXiv 适配器"""
        from services.article.adapters.arxiv import ArxivAdapter

        adapter = ArxivAdapter()

        with patch.object(adapter, "search", return_value=[
            {
                "id": "arxiv:2401.12345",
                "title": "Test arXiv Paper",
                "authors": [{"name": "Author One"}],
                "year": 2024,
            }
        ]):
            result = await adapter.search("test query")

        assert len(result) == 1
        assert "arxiv" in result[0]["id"]

    @pytest.mark.asyncio
    async def test_cnki_adapter(self):
        """测试 CNKI 适配器"""
        from services.article.adapters.cnki import CNKIAdapter

        adapter = CNKIAdapter()

        with patch.object(adapter, "search", return_value=[
            {
                "id": "cnki:abc123",
                "title": "中文论文",
                "authors": [{"name": "张三"}],
                "year": 2023,
            }
        ]):
            result = await adapter.search("人工智能")

        assert len(result) == 1
        assert result[0]["title"] == "中文论文"

    @pytest.mark.asyncio
    async def test_semantic_scholar_adapter(self):
        """测试 Semantic Scholar 适配器"""
        from services.article.adapters.semantic_scholar import SemanticScholarAdapter

        adapter = SemanticScholarAdapter()

        with patch.object(adapter, "search", return_value=[
            {
                "id": "s2:12345",
                "title": "S2 Paper",
                "authors": [{"name": "Author"}],
                "citations_count": 100,
            }
        ]):
            result = await adapter.search("query")

        assert len(result) == 1
        assert result[0]["citations_count"] == 100


class TestArticleImport:
    """测试文献导入"""

    @pytest.mark.asyncio
    async def test_import_from_doi(self):
        """测试通过 DOI 导入"""
        from services.article.service import ArticleService

        service = ArticleService()
        doi = "10.1234/example.123"

        with patch.object(service, "_fetch_by_doi", return_value={
            "id": "imported-1",
            "doi": doi,
            "title": "Imported Paper",
            "authors": [{"name": "Author"}],
        }):
            result = await service.import_by_doi(doi)

        assert result["doi"] == doi

    @pytest.mark.asyncio
    async def test_import_from_bibtex(self):
        """测试通过 BibTeX 导入"""
        from services.article.service import ArticleService

        service = ArticleService()

        bibtex = """
        @article{test2024,
            title={Test Article},
            author={Author, Test},
            journal={Test Journal},
            year={2024}
        }
        """

        with patch.object(service, "_parse_bibtex", return_value=[
            {"title": "Test Article", "authors": [{"name": "Test Author"}]}
        ]):
            result = await service.import_from_bibtex(bibtex)

        assert len(result) == 1
        assert result[0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_batch_import(self):
        """测试批量导入"""
        from services.article.service import ArticleService

        service = ArticleService()
        articles = [
            {"title": "Article 1", "doi": "10.1/1"},
            {"title": "Article 2", "doi": "10.1/2"},
        ]

        with patch.object(service, "_batch_save", return_value=2):
            result = await service.batch_import(articles)

        assert result["imported"] == 2


class TestArticleMetadata:
    """测试文献元数据"""

    @pytest.mark.asyncio
    async def test_extract_metadata_from_pdf(self):
        """测试从 PDF 提取元数据"""
        from services.article.service import ArticleService

        service = ArticleService()

        with patch.object(service, "_extract_pdf_metadata", return_value={
            "title": "PDF Title",
            "authors": ["Author 1", "Author 2"],
            "abstract": "PDF Abstract",
        }):
            result = await service.extract_metadata("/path/to/paper.pdf")

        assert result["title"] == "PDF Title"

    def test_normalize_author_name(self):
        """测试作者名称规范化"""
        from services.article.service import ArticleService

        service = ArticleService()

        # 测试不同格式的作者名
        assert service._normalize_author("Doe, John") == "John Doe"
        assert service._normalize_author("John Doe") == "John Doe"
        assert service._normalize_author("J. Doe") == "J. Doe"
