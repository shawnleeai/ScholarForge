"""
协作评论管理器
处理文档评论和批注
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class Comment:
    """评论数据"""
    id: str
    document_id: str
    user_id: str
    user_name: str
    content: str
    position: Optional[Dict] = None  # 文档位置信息
    selection: Optional[str] = None  # 选中的文本
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    resolved: bool = False
    replies: List['Comment'] = field(default_factory=list)
    parent_id: Optional[str] = None


class CommentManager:
    """评论管理器"""

    def __init__(self):
        self._comments: Dict[str, List[Comment]] = {}  # document_id -> comments

    def add_comment(
        self,
        document_id: str,
        user_id: str,
        user_name: str,
        content: str,
        position: Optional[Dict] = None,
        selection: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Comment:
        """添加评论"""
        comment = Comment(
            id=str(uuid.uuid4()),
            document_id=document_id,
            user_id=user_id,
            user_name=user_name,
            content=content,
            position=position,
            selection=selection,
            parent_id=parent_id,
        )

        if document_id not in self._comments:
            self._comments[document_id] = []

        if parent_id:
            # 添加到回复
            parent = self._find_comment(document_id, parent_id)
            if parent:
                parent.replies.append(comment)
        else:
            self._comments[document_id].append(comment)

        return comment

    def get_comments(self, document_id: str, include_resolved: bool = True) -> List[Comment]:
        """获取文档的所有评论"""
        comments = self._comments.get(document_id, [])
        if not include_resolved:
            return [c for c in comments if not c.resolved]
        return comments

    def update_comment(
        self,
        document_id: str,
        comment_id: str,
        content: str,
    ) -> Optional[Comment]:
        """更新评论"""
        comment = self._find_comment(document_id, comment_id)
        if comment:
            comment.content = content
            comment.updated_at = datetime.now()
        return comment

    def resolve_comment(self, document_id: str, comment_id: str) -> Optional[Comment]:
        """标记评论为已解决"""
        comment = self._find_comment(document_id, comment_id)
        if comment:
            comment.resolved = True
        return comment

    def delete_comment(self, document_id: str, comment_id: str) -> bool:
        """删除评论"""
        comments = self._comments.get(document_id, [])

        # 查找并删除
        for i, comment in enumerate(comments):
            if comment.id == comment_id:
                comments.pop(i)
                return True

            # 在回复中查找
            for j, reply in enumerate(comment.replies):
                if reply.id == comment_id:
                    comment.replies.pop(j)
                    return True

        return False

    def _find_comment(self, document_id: str, comment_id: str) -> Optional[Comment]:
        """查找评论"""
        comments = self._comments.get(document_id, [])

        for comment in comments:
            if comment.id == comment_id:
                return comment

            for reply in comment.replies:
                if reply.id == comment_id:
                    return reply

        return None

    def to_dict(self, comment: Comment) -> Dict:
        """转换为字典"""
        return {
            "id": comment.id,
            "document_id": comment.document_id,
            "user_id": comment.user_id,
            "user_name": comment.user_name,
            "content": comment.content,
            "position": comment.position,
            "selection": comment.selection,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            "resolved": comment.resolved,
            "parent_id": comment.parent_id,
            "replies": [self.to_dict(r) for r in comment.replies],
        }


# 全局评论管理器实例
comment_manager = CommentManager()
