"""
查询重写模块
使用LLM优化用户查询，提升检索效果
"""

import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RewriteStrategy(str, Enum):
    """重写策略"""
    EXPAND = "expand"  # 扩展查询
    DECOMPOSE = "decompose"  # 分解复杂查询
    CLARIFY = "clarify"  # 澄清模糊查询
    KEYWORD = "keyword"  # 提取关键词


@dataclass
class RewrittenQuery:
    """重写后的查询"""
    original: str
    rewritten: str
    strategy: RewriteStrategy
    sub_queries: List[str]
    keywords: List[str]
    explanation: str


class QueryRewriter:
    """查询重写器"""

    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: LLM客户端，用于生成重写
        """
        self.llm = llm_client

    async def rewrite(
        self,
        query: str,
        context: Optional[str] = None,
        strategy: RewriteStrategy = RewriteStrategy.EXPAND
    ) -> RewrittenQuery:
        """
        重写查询

        Args:
            query: 原始查询
            context: 可选的上下文信息
            strategy: 重写策略

        Returns:
            重写后的查询
        """
        if not self.llm:
            # 如果没有LLM，使用简单的重写
            return self._simple_rewrite(query)

        # 构建提示
        prompt = self._build_prompt(query, context, strategy)

        try:
            response = await self.llm.generate(prompt)
            return self._parse_response(query, response, strategy)
        except Exception as e:
            logger.error(f"Query rewrite failed: {e}")
            return self._simple_rewrite(query)

    def _build_prompt(
        self,
        query: str,
        context: Optional[str],
        strategy: RewriteStrategy
    ) -> str:
        """构建重写提示"""

        base_prompt = f"""你是一个学术搜索查询优化专家。请优化以下用户查询以提高检索效果。

原始查询: {query}
"""

        if context:
            base_prompt += f"""
上下文信息: {context}
"""

        if strategy == RewriteStrategy.EXPAND:
            base_prompt += """
请执行以下操作:
1. 重写查询，添加同义词和相关术语
2. 提取3-5个关键搜索词
3. 生成2-3个子查询，从不同角度表达相同需求
4. 简要解释重写的理由

请按以下格式输出:
重写后: [优化后的查询]
关键词: [关键词1, 关键词2, ...]
子查询:
- [子查询1]
- [子查询2]
解释: [解释]
"""

        elif strategy == RewriteStrategy.DECOMPOSE:
            base_prompt += """
这是一个复杂查询，请将其分解为多个简单子查询。

请按以下格式输出:
重写后: [简化后的主查询]
关键词: [关键词1, 关键词2, ...]
子查询:
- [子查询1: 针对某一方面]
- [子查询2: 针对另一方面]
- [子查询3: 针对第三方面]
解释: [为什么这样分解]
"""

        elif strategy == RewriteStrategy.KEYWORD:
            base_prompt += """
请从查询中提取关键搜索词，包括:
1. 核心概念词
2. 方法/技术词
3. 应用领域词

请按以下格式输出:
重写后: [原始查询]
关键词: [核心词1, 核心词2, 方法词1, 领域词1, ...]
子查询:
- [基于核心词的查询]
- [基于方法词的查询]
解释: [关键词提取理由]
"""

        return base_prompt

    def _parse_response(
        self,
        original: str,
        response: str,
        strategy: RewriteStrategy
    ) -> RewrittenQuery:
        """解析LLM响应"""
        lines = response.strip().split('\n')

        rewritten = original
        keywords = []
        sub_queries = []
        explanation = ""

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('重写后:'):
                rewritten = line.replace('重写后:', '').strip()
                current_section = 'rewritten'
            elif line.startswith('关键词:'):
                kw_text = line.replace('关键词:', '').strip()
                keywords = [k.strip() for k in kw_text.strip('[]').split(',')]
                current_section = 'keywords'
            elif line.startswith('子查询:'):
                current_section = 'sub_queries'
            elif line.startswith('- ') and current_section == 'sub_queries':
                sub_queries.append(line[2:].strip())
            elif line.startswith('解释:'):
                explanation = line.replace('解释:', '').strip()

        # 如果没有提取到子查询，使用重写后的查询
        if not sub_queries:
            sub_queries = [rewritten]

        return RewrittenQuery(
            original=original,
            rewritten=rewritten,
            strategy=strategy,
            sub_queries=sub_queries,
            keywords=keywords,
            explanation=explanation
        )

    def _simple_rewrite(self, query: str) -> RewrittenQuery:
        """简单的查询重写（无需LLM）"""
        # 简单的关键词提取
        words = query.lower().split()

        # 去除停用词
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'is', 'are'}
        keywords = [w for w in words if w not in stop_words][:5]

        # 生成简单子查询
        sub_queries = [query]
        if len(keywords) >= 2:
            sub_queries.append(f"{keywords[0]} {keywords[1]}")

        return RewrittenQuery(
            original=query,
            rewritten=query,
            strategy=RewriteStrategy.KEYWORD,
            sub_queries=sub_queries,
            keywords=keywords,
            explanation="简单关键词提取（无LLM）"
        )

    async def rewrite_for_hyde(
        self,
        query: str,
        documents: List[str]
    ) -> str:
        """
        HyDE (Hypothetical Document Embeddings)
        生成假设性文档用于检索
        """
        if not self.llm:
            return query

        prompt = f"""基于以下问题，生成一段可能包含答案的假设性文档摘要。

问题: {query}

请生成一段100-200字的文档摘要，这段文档应该:
1. 直接回答或部分回答问题
2. 使用相关学术术语
3. 包含可能出现在真实文献中的关键信息

生成的摘要:"""

        try:
            hypothetical_doc = await self.llm.generate(prompt)
            return hypothetical_doc.strip()
        except Exception as e:
            logger.error(f"HyDE generation failed: {e}")
            return query


class ConversationalQueryRewriter:
    """对话式查询重写器

    维护对话历史，重写多轮查询
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.history: List[Dict] = []

    def add_turn(self, query: str, response: str):
        """添加对话轮次"""
        self.history.append({
            "query": query,
            "response": response
        })

    def clear_history(self):
        """清空历史"""
        self.history = []

    async def rewrite_with_history(self, current_query: str) -> str:
        """
        基于对话历史重写当前查询

        将指代消解（如"它"、"这个"）替换为具体实体
        """
        if not self.llm or not self.history:
            return current_query

        # 构建历史上下文
        history_text = ""
        for turn in self.history[-3:]:  # 最近3轮
            history_text += f"Q: {turn['query']}\nA: {turn['response']}\n\n"

        prompt = f"""基于以下对话历史，重写最后一个查询，将指代词（如"它"、"这个"、"那个"）替换为具体实体。

对话历史:
{history_text}

当前查询: {current_query}

请重写当前查询，使其不依赖上下文也能被理解。只输出重写后的查询，不要解释。

重写后的查询:"""

        try:
            rewritten = await self.llm.generate(prompt)
            return rewritten.strip()
        except Exception as e:
            logger.error(f"Conversational rewrite failed: {e}")
            return current_query
