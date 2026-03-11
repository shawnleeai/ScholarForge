"""
Research Showcase Service
科研成果与团队展示平台 - 论文展示、团队主页、学术影响力
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class ShowcaseType(str, Enum):
    """展示类型"""
    PAPER = "paper"           # 论文
    PROJECT = "project"       # 项目
    DATASET = "dataset"       # 数据集
    CODE = "code"             # 代码
    PATENT = "patent"         # 专利
    PRESENTATION = "presentation"  # 演示


class Visibility(str, Enum):
    """可见性"""
    PUBLIC = "public"         # 公开
    TEAM = "team"            # 团队内
    PRIVATE = "private"       # 私密


@dataclass
class ShowcaseItem:
    """展示项目"""
    id: str
    type: ShowcaseType
    title: str
    description: str
    owner_id: str
    team_id: Optional[str] = None
    visibility: Visibility = Visibility.PUBLIC
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # 关联资源
    paper_id: Optional[str] = None
    project_id: Optional[str] = None
    external_url: Optional[str] = None
    files: List[str] = field(default_factory=list)

    # 元数据
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    thumbnail_url: Optional[str] = None

    # 统计
    view_count: int = 0
    like_count: int = 0
    download_count: int = 0
    citation_count: int = 0


@dataclass
class TeamProfile:
    """团队主页"""
    id: str
    name: str
    description: str
    creator_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    # 团队信息
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None

    # 成员
    members: List[str] = field(default_factory=list)
    admins: List[str] = field(default_factory=list)

    # 统计数据
    total_papers: int = 0
    total_citations: int = 0
    h_index: float = 0.0

    # 社交
    followers: List[str] = field(default_factory=list)
    following: List[str] = field(default_factory=list)


@dataclass
class ResearcherProfile:
    """研究者个人主页"""
    user_id: str
    display_name: str
    bio: str = ""
    title: str = ""  # 职称
    institution: str = ""
    department: str = ""
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None

    # 联系信息
    email: Optional[str] = None
    personal_website: Optional[str] = None
    orcid: Optional[str] = None
    google_scholar: Optional[str] = None
    github: Optional[str] = None
    twitter: Optional[str] = None

    # 研究兴趣
    research_interests: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)

    # 统计
    total_papers: int = 0
    total_citations: int = 0
    h_index: float = 0.0
    i10_index: int = 0

    # 社交
    followers: List[str] = field(default_factory=list)
    following: List[str] = field(default_factory=list)
    teams: List[str] = field(default_factory=list)


@dataclass
class Comment:
    """评论"""
    id: str
    showcase_id: str
    author_id: str
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_id: Optional[str] = None  # 回复的评论ID


class ResearchShowcaseService:
    """科研展示服务"""

    def __init__(self):
        self._items: Dict[str, ShowcaseItem] = {}
        self._team_profiles: Dict[str, TeamProfile] = {}
        self._researcher_profiles: Dict[str, ResearcherProfile] = {}
        self._comments: Dict[str, List[Comment]] = {}

    # ==================== 展示项目管理 ====================

    def create_showcase(
        self,
        item_type: ShowcaseType,
        title: str,
        description: str,
        owner_id: str,
        **kwargs
    ) -> ShowcaseItem:
        """创建展示项目"""
        item = ShowcaseItem(
            id=str(uuid.uuid4()),
            type=item_type,
            title=title,
            description=description,
            owner_id=owner_id,
            **kwargs
        )
        self._items[item.id] = item
        return item

    def get_showcase(self, item_id: str) -> Optional[ShowcaseItem]:
        """获取展示项目"""
        item = self._items.get(item_id)
        if item:
            item.view_count += 1
        return item

    def update_showcase(
        self,
        item_id: str,
        owner_id: str,
        **updates
    ) -> Optional[ShowcaseItem]:
        """更新展示项目"""
        item = self._items.get(item_id)
        if not item or item.owner_id != owner_id:
            return None

        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)

        item.updated_at = datetime.utcnow()
        return item

    def delete_showcase(self, item_id: str, owner_id: str) -> bool:
        """删除展示项目"""
        item = self._items.get(item_id)
        if not item or item.owner_id != owner_id:
            return False

        del self._items[item_id]
        return True

    def list_showcases(
        self,
        item_type: Optional[ShowcaseType] = None,
        owner_id: Optional[str] = None,
        team_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "created",
        limit: int = 20
    ) -> List[ShowcaseItem]:
        """列出展示项目"""
        items = list(self._items.values())

        # 只返回公开项目
        items = [i for i in items if i.visibility == Visibility.PUBLIC]

        if item_type:
            items = [i for i in items if i.type == item_type]

        if owner_id:
            items = [i for i in items if i.owner_id == owner_id]

        if team_id:
            items = [i for i in items if i.team_id == team_id]

        if tags:
            items = [
                i for i in items
                if any(tag in i.tags for tag in tags)
            ]

        # 排序
        if sort_by == "popular":
            items.sort(key=lambda x: x.view_count + x.like_count, reverse=True)
        elif sort_by == "cited":
            items.sort(key=lambda x: x.citation_count, reverse=True)
        else:  # created
            items.sort(key=lambda x: x.created_at, reverse=True)

        return items[:limit]

    def like_showcase(self, item_id: str, user_id: str) -> bool:
        """点赞展示项目"""
        item = self._items.get(item_id)
        if item:
            item.like_count += 1
            return True
        return False

    # ==================== 团队主页管理 ====================

    def create_team_profile(
        self,
        name: str,
        description: str,
        creator_id: str,
        **kwargs
    ) -> TeamProfile:
        """创建团队主页"""
        team = TeamProfile(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            creator_id=creator_id,
            members=[creator_id],
            admins=[creator_id],
            **kwargs
        )
        self._team_profiles[team.id] = team
        return team

    def get_team_profile(self, team_id: str) -> Optional[TeamProfile]:
        """获取团队主页"""
        return self._team_profiles.get(team_id)

    def update_team_profile(
        self,
        team_id: str,
        updater_id: str,
        **updates
    ) -> Optional[TeamProfile]:
        """更新团队主页"""
        team = self._team_profiles.get(team_id)
        if not team or updater_id not in team.admins:
            return None

        for key, value in updates.items():
            if hasattr(team, key):
                setattr(team, key, value)

        return team

    def join_team(self, team_id: str, user_id: str) -> bool:
        """加入团队"""
        team = self._team_profiles.get(team_id)
        if team and user_id not in team.members:
            team.members.append(user_id)
            return True
        return False

    def leave_team(self, team_id: str, user_id: str) -> bool:
        """离开团队"""
        team = self._team_profiles.get(team_id)
        if team and user_id in team.members:
            team.members.remove(user_id)
            if user_id in team.admins:
                team.admins.remove(user_id)
            return True
        return False

    def search_teams(
        self,
        query: Optional[str] = None,
        institution: Optional[str] = None,
        limit: int = 20
    ) -> List[TeamProfile]:
        """搜索团队"""
        teams = list(self._team_profiles.values())

        if query:
            teams = [
                t for t in teams
                if query.lower() in t.name.lower() or
                query.lower() in t.description.lower()
            ]

        if institution:
            teams = [
                t for t in teams
                if t.institution and institution.lower() in t.institution.lower()
            ]

        # 按影响力排序
        teams.sort(
            key=lambda x: x.total_citations * 0.5 + len(x.members) * 10,
            reverse=True
        )

        return teams[:limit]

    # ==================== 研究者个人主页 ====================

    def create_researcher_profile(
        self,
        user_id: str,
        display_name: str,
        **kwargs
    ) -> ResearcherProfile:
        """创建研究者主页"""
        profile = ResearcherProfile(
            user_id=user_id,
            display_name=display_name,
            **kwargs
        )
        self._researcher_profiles[user_id] = profile
        return profile

    def get_researcher_profile(
        self,
        user_id: str
    ) -> Optional[ResearcherProfile]:
        """获取研究者主页"""
        return self._researcher_profiles.get(user_id)

    def update_researcher_profile(
        self,
        user_id: str,
        **updates
    ) -> Optional[ResearcherProfile]:
        """更新研究者主页"""
        profile = self._researcher_profiles.get(user_id)
        if not profile:
            return None

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        return profile

    def follow_researcher(
        self,
        user_id: str,
        target_user_id: str
    ) -> bool:
        """关注研究者"""
        target = self._researcher_profiles.get(target_user_id)
        user = self._researcher_profiles.get(user_id)

        if target and user:
            if user_id not in target.followers:
                target.followers.append(user_id)
            if target_user_id not in user.following:
                user.following.append(target_user_id)
            return True
        return False

    def unfollow_researcher(
        self,
        user_id: str,
        target_user_id: str
    ) -> bool:
        """取消关注"""
        target = self._researcher_profiles.get(target_user_id)
        user = self._researcher_profiles.get(user_id)

        if target and user:
            if user_id in target.followers:
                target.followers.remove(user_id)
            if target_user_id in user.following:
                user.following.remove(target_user_id)
            return True
        return False

    def search_researchers(
        self,
        query: Optional[str] = None,
        interests: Optional[List[str]] = None,
        institution: Optional[str] = None,
        limit: int = 20
    ) -> List[ResearcherProfile]:
        """搜索研究者"""
        profiles = list(self._researcher_profiles.values())

        if query:
            profiles = [
                p for p in profiles
                if query.lower() in p.display_name.lower()
            ]

        if interests:
            profiles = [
                p for p in profiles
                if any(i in p.research_interests for i in interests)
            ]

        if institution:
            profiles = [
                p for p in profiles
                if p.institution and institution.lower() in p.institution.lower()
            ]

        # 按影响力排序
        profiles.sort(
            key=lambda x: x.h_index * 10 + x.total_citations * 0.01,
            reverse=True
        )

        return profiles[:limit]

    # ==================== 评论系统 ====================

    def add_comment(
        self,
        showcase_id: str,
        author_id: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Comment:
        """添加评论"""
        comment = Comment(
            id=str(uuid.uuid4()),
            showcase_id=showcase_id,
            author_id=author_id,
            content=content,
            parent_id=parent_id
        )

        if showcase_id not in self._comments:
            self._comments[showcase_id] = []

        self._comments[showcase_id].append(comment)
        return comment

    def get_comments(self, showcase_id: str) -> List[Comment]:
        """获取评论列表"""
        return self._comments.get(showcase_id, [])

    # ==================== 统计分析 ====================

    def get_showcase_stats(self, item_id: str) -> Dict[str, Any]:
        """获取展示统计"""
        item = self._items.get(item_id)
        if not item:
            return {}

        return {
            "views": item.view_count,
            "likes": item.like_count,
            "downloads": item.download_count,
            "citations": item.citation_count,
            "engagement_score": (
                item.view_count * 1 +
                item.like_count * 5 +
                item.download_count * 10 +
                item.citation_count * 20
            )
        }

    def get_leaderboard(self, metric: str = "citations", limit: int = 10) -> List[Dict[str, Any]]:
        """获取排行榜"""
        items = list(self._items.values())

        if metric == "citations":
            items.sort(key=lambda x: x.citation_count, reverse=True)
        elif metric == "views":
            items.sort(key=lambda x: x.view_count, reverse=True)
        elif metric == "recent":
            items.sort(key=lambda x: x.created_at, reverse=True)

        return [
            {
                "id": item.id,
                "title": item.title,
                "type": item.type.value,
                "owner_id": item.owner_id,
                "metric_value": getattr(item, f"{metric}_count", 0),
                "thumbnail_url": item.thumbnail_url
            }
            for item in items[:limit]
        ]


# 单例
_showcase_service = None


def get_showcase_service() -> ResearchShowcaseService:
    """获取展示服务单例"""
    global _showcase_service
    if _showcase_service is None:
        _showcase_service = ResearchShowcaseService()
    return _showcase_service
