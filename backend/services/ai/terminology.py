"""
术语库管理
维护学术术语的翻译和定义
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class TerminologyEntry(BaseModel):
    """术语条目"""
    id: str
    source_term: str                    # 源语言术语
    target_term: str                    # 目标语言术语
    source_lang: str = "en"            # 源语言
    target_lang: str = "zh"            # 目标语言
    domain: str                        # 领域/学科
    definition: Optional[str] = None   # 定义
    context: Optional[str] = None      # 使用语境
    examples: List[str] = []           # 例句
    verified: bool = False             # 是否已验证
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    usage_count: int = 0               # 使用次数


class TerminologyDatabase:
    """术语数据库"""

    def __init__(self):
        self._entries: Dict[str, TerminologyEntry] = {}
        self._init_default_terms()

    def _init_default_terms(self):
        """初始化默认学术术语"""
        default_terms = [
            TerminologyEntry(
                id="term_001",
                source_term="machine learning",
                target_term="机器学习",
                domain="computer_science",
                definition="一种让计算机系统从数据中学习和改进的方法",
                verified=True,
                created_by="system"
            ),
            TerminologyEntry(
                id="term_002",
                source_term="deep learning",
                target_term="深度学习",
                domain="computer_science",
                definition="基于多层神经网络的机器学习方法",
                verified=True,
                created_by="system"
            ),
            TerminologyEntry(
                id="term_003",
                source_term="neural network",
                target_term="神经网络",
                domain="computer_science",
                definition="受人脑神经元结构启发的计算模型",
                verified=True,
                created_by="system"
            ),
            TerminologyEntry(
                id="term_004",
                source_term="natural language processing",
                target_term="自然语言处理",
                domain="computer_science",
                definition="使计算机能够理解、解释和生成人类语言的技术",
                verified=True,
                created_by="system"
            ),
            TerminologyEntry(
                id="term_005",
                source_term="abstract",
                target_term="摘要",
                domain="academic_writing",
                definition="对论文或研究内容的简短总结",
                verified=True,
                created_by="system"
            ),
        ]
        for term in default_terms:
            self._entries[term.id] = term

    async def add_term(self, entry: TerminologyEntry) -> TerminologyEntry:
        """添加术语"""
        self._entries[entry.id] = entry
        return entry

    async def get_term(self, term_id: str) -> Optional[TerminologyEntry]:
        """获取术语"""
        return self._entries.get(term_id)

    async def search_terms(
        self,
        query: str,
        domain: Optional[str] = None,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None
    ) -> List[TerminologyEntry]:
        """搜索术语"""
        results = []
        query_lower = query.lower()

        for entry in self._entries.values():
            if (query_lower in entry.source_term.lower() or
                query_lower in entry.target_term.lower()):

                if domain and entry.domain != domain:
                    continue
                if source_lang and entry.source_lang != source_lang:
                    continue
                if target_lang and entry.target_lang != target_lang:
                    continue

                results.append(entry)

        return sorted(results, key=lambda x: x.usage_count, reverse=True)

    async def update_term(
        self,
        term_id: str,
        updates: Dict[str, Any]
    ) -> Optional[TerminologyEntry]:
        """更新术语"""
        entry = self._entries.get(term_id)
        if not entry:
            return None

        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        entry.updated_at = datetime.now()
        return entry

    async def delete_term(self, term_id: str) -> bool:
        """删除术语"""
        if term_id in self._entries:
            del self._entries[term_id]
            return True
        return False

    async def get_domains(self) -> List[str]:
        """获取所有领域"""
        domains = set()
        for entry in self._entries.values():
            domains.add(entry.domain)
        return sorted(list(domains))

    async def get_translation(
        self,
        source_term: str,
        domain: Optional[str] = None
    ) -> Optional[str]:
        """获取术语翻译"""
        source_lower = source_term.lower()

        for entry in self._entries.values():
            if entry.source_term.lower() == source_lower:
                if domain and entry.domain != domain:
                    continue
                entry.usage_count += 1
                return entry.target_term

        return None


# 数据库实例
terminology_db = TerminologyDatabase()
