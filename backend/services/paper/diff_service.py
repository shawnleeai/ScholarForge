"""
论文版本对比服务
实现论文版本间的差异分析和可视化
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher, unified_diff, HtmlDiff
import re


class DiffBlock:
    """差异块"""
    def __init__(
        self,
        operation: str,  # equal, insert, delete, replace
        old_start: int,
        old_end: int,
        new_start: int,
        new_end: int,
        old_text: str = "",
        new_text: str = ""
    ):
        self.operation = operation
        self.old_start = old_start
        self.old_end = old_end
        self.new_start = new_start
        self.new_end = new_end
        self.old_text = old_text
        self.new_text = new_text


class VersionComparison:
    """版本对比结果"""
    def __init__(
        self,
        old_version: str,
        new_version: str,
        similarity: float,
        changes: List[DiffBlock],
        stats: Dict[str, int]
    ):
        self.old_version = old_version
        self.new_version = new_version
        self.similarity = similarity
        self.changes = changes
        self.stats = stats


class DiffService:
    """版本对比服务"""

    def __init__(self):
        pass

    async def compare_versions(
        self,
        old_content: str,
        new_content: str,
        old_version: str = "",
        new_version: str = ""
    ) -> VersionComparison:
        """比较两个版本的差异"""
        # 分行处理
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')

        # 计算相似度
        similarity = self._calculate_similarity(old_content, new_content)

        # 生成差异块
        changes = self._generate_diff_blocks(old_lines, new_lines)

        # 统计
        stats = self._calculate_stats(changes)

        return VersionComparison(
            old_version=old_version,
            new_version=new_version,
            similarity=similarity,
            changes=changes,
            stats=stats
        )

    def _calculate_similarity(self, old_text: str, new_text: str) -> float:
        """计算文本相似度"""
        return SequenceMatcher(None, old_text, new_text).ratio()

    def _generate_diff_blocks(
        self,
        old_lines: List[str],
        new_lines: List[str]
    ) -> List[DiffBlock]:
        """生成差异块列表"""
        sm = SequenceMatcher(None, old_lines, new_lines)
        blocks = []

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            block = DiffBlock(
                operation=tag,
                old_start=i1,
                old_end=i2,
                new_start=j1,
                new_end=j2,
                old_text='\n'.join(old_lines[i1:i2]),
                new_text='\n'.join(new_lines[j1:j2])
            )
            blocks.append(block)

        return blocks

    def _calculate_stats(self, changes: List[DiffBlock]) -> Dict[str, int]:
        """计算变更统计"""
        stats = {
            "insertions": 0,
            "deletions": 0,
            "modifications": 0,
            "unchanged": 0
        }

        for block in changes:
            if block.operation == 'insert':
                stats["insertions"] += block.new_end - block.new_start
            elif block.operation == 'delete':
                stats["deletions"] += block.old_end - block.old_start
            elif block.operation == 'replace':
                stats["modifications"] += max(
                    block.old_end - block.old_start,
                    block.new_end - block.new_start
                )
            else:
                stats["unchanged"] += block.old_end - block.old_start

        return stats

    async def generate_side_by_side_html(
        self,
        old_content: str,
        new_content: str,
        old_title: str = "旧版本",
        new_title: str = "新版本"
    ) -> str:
        """生成并排对比HTML"""
        differ = HtmlDiff(wrapcolumn=80)
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')

        html = differ.make_file(
            old_lines,
            new_lines,
            fromdesc=old_title,
            todesc=new_title,
            context=True
        )

        return html

    async def generate_unified_diff(
        self,
        old_content: str,
        new_content: str,
        old_filename: str = "old",
        new_filename: str = "new"
    ) -> str:
        """生成统一格式差异文本"""
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')

        diff = unified_diff(
            old_lines,
            new_lines,
            fromfile=old_filename,
            tofile=new_filename,
            lineterm=''
        )

        return '\n'.join(diff)

    async def compare_sections(
        self,
        old_sections: List[Dict[str, str]],
        new_sections: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """按章节对比"""
        results = []

        # 创建章节映射
        old_map = {s.get('title', ''): s.get('content', '') for s in old_sections}
        new_map = {s.get('title', ''): s.get('content', '') for s in new_sections}

        all_titles = set(old_map.keys()) | set(new_map.keys())

        for title in all_titles:
            old_content = old_map.get(title, '')
            new_content = new_map.get(title, '')

            comparison = await self.compare_versions(old_content, new_content)

            results.append({
                "title": title,
                "status": self._get_section_status(title, old_map, new_map),
                "similarity": comparison.similarity,
                "changes_count": len([c for c in comparison.changes if c.operation != 'equal']),
                "comparison": comparison
            })

        return results

    def _get_section_status(
        self,
        title: str,
        old_map: Dict[str, str],
        new_map: Dict[str, str]
    ) -> str:
        """获取章节状态"""
        if title not in old_map:
            return "added"
        if title not in new_map:
            return "removed"
        return "modified" if old_map[title] != new_map[title] else "unchanged"

    async def track_changes(
        self,
        content_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """追踪变更历史"""
        changes = []

        for i in range(1, len(content_history)):
            old = content_history[i - 1]
            new = content_history[i]

            comparison = await self.compare_versions(
                old.get('content', ''),
                new.get('content', ''),
                old.get('version', ''),
                new.get('version', '')
            )

            changes.append({
                "from_version": old.get('version'),
                "to_version": new.get('version'),
                "timestamp": new.get('timestamp'),
                "author": new.get('author'),
                "comparison": comparison
            })

        return changes


# 服务实例
diff_service = DiffService()
