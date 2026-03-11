"""
研究动态 Feed 服务
处理研究动态生成、关注和推荐
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """活动类型"""
    # 文献相关
    PUBLISH_PAPER = "publish_paper"
    CITE_PAPER = "cite_paper"
    ADD_TO_LIBRARY = "add_to_library"
    WRITE_NOTE = "write_note"

    # 写作相关
    CREATE_DRAFT = "create_draft"
    COMPLETE_DRAFT = "complete_draft"
    SHARE_DRAFT = "share_draft"

    # 团队相关
    JOIN_TEAM = "join_team"
    CREATE_TEAM = "create_team"
    START_PROJECT = "start_project"
    COMPLETE_PROJECT = "complete_project"

    # 评论相关
    COMMENT = "comment"
    LIKE = "like"
    SHARE = "share"


class FeedItem(BaseModel):
    """动态项"""
    id: str
    user_id: str
    username: str
    user_avatar: Optional[str] = None
    activity_type: ActivityType
    target_type: str                      # paper, draft, team, project, comment
    target_id: str
    target_title: str
    target_url: Optional[str] = None
    content: Optional[str] = None         # 动态内容（如评论内容）
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    # 社交数据
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    is_liked: bool = False


class UserFollow(BaseModel):
    """用户关注关系"""
    follower_id: str                      # 关注者
    following_id: str                     # 被关注者
    created_at: datetime = Field(default_factory=datetime.now)


class TeamFollow(BaseModel):
    """团队关注关系"""
    user_id: str
    team_id: str
    created_at: datetime = Field(default_factory=datetime.now)


class TopicFollow(BaseModel):
    """话题关注"""
    user_id: str
    topic: str                            # 研究话题/领域
    created_at: datetime = Field(default_factory=datetime.now)


class FeedFilter(BaseModel):
    """动态筛选"""
    activity_types: Optional[List[ActivityType]] = None
    target_types: Optional[List[str]] = None
    date_range: Optional[tuple] = None
    teams_only: bool = False
    following_only: bool = False


class FeedService:
    """研究动态服务"""

    def __init__(self):
        self._feed_items: List[FeedItem] = []
        self._user_follows: List[UserFollow] = []
        self._team_follows: List[TeamFollow] = []
        self._topic_follows: List[TopicFollow] = []
        self._user_likes: Dict[str, set] = {}  # user_id -> set of feed_item_ids

        # 初始化示例数据
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例动态数据"""
        sample_feeds = [
            FeedItem(
                id=str(uuid.uuid4()),
                user_id="user_001",
                username="张教授",
                user_avatar=None,
                activity_type=ActivityType.PUBLISH_PAPER,
                target_type="paper",
                target_id="paper_001",
                target_title="深度学习在医学影像诊断中的应用",
                content="我们的新论文刚刚被接收！探索了Transformer架构在医学影像中的创新应用。",
                metadata={
                    "journal": "Nature Medicine",
                    "coauthors": ["李博士", "王同学"],
                    "citations": 0
                },
                created_at=datetime.now() - timedelta(hours=2),
                likes_count=45,
                comments_count=12
            ),
            FeedItem(
                id=str(uuid.uuid4()),
                user_id="user_002",
                username="李博士",
                user_avatar=None,
                activity_type=ActivityType.COMPLETE_PROJECT,
                target_type="project",
                target_id="proj_001",
                target_title="多模态学习框架开发",
                content="历时8个月，我们的多模态学习框架终于完成了！支持文本、图像、音频的统一处理。",
                metadata={
                    "team_id": "team_001",
                    "team_name": "机器学习研究组",
                    "duration_days": 240
                },
                created_at=datetime.now() - timedelta(hours=5),
                likes_count=32,
                comments_count=8
            ),
            FeedItem(
                id=str(uuid.uuid4()),
                user_id="user_003",
                username="王同学",
                user_avatar=None,
                activity_type=ActivityType.WRITE_NOTE,
                target_type="paper",
                target_id="paper_002",
                target_title="Attention Is All You Need",
                content="重读经典，对位置编码有了更深的理解。分享一下我的笔记。",
                metadata={
                    "note_length": 2500,
                    "key_insights": ["位置编码", "多头注意力", "残差连接"]
                },
                created_at=datetime.now() - timedelta(hours=8),
                likes_count=28,
                comments_count=15
            ),
            FeedItem(
                id=str(uuid.uuid4()),
                user_id="user_004",
                username="陈研究员",
                user_avatar=None,
                activity_type=ActivityType.JOIN_TEAM,
                target_type="team",
                target_id="team_002",
                target_title="自然语言处理实验室",
                metadata={
                    "institution": "某某大学",
                    "research_fields": ["NLP", "大语言模型"]
                },
                created_at=datetime.now() - timedelta(days=1),
                likes_count=15,
                comments_count=3
            ),
            FeedItem(
                id=str(uuid.uuid4()),
                user_id="user_001",
                username="张教授",
                user_avatar=None,
                activity_type=ActivityType.SHARE_DRAFT,
                target_type="draft",
                target_id="draft_001",
                target_title="大语言模型微调综述",
                content="初稿完成，欢迎同行提出宝贵意见！涵盖了最新的PEFT方法。",
                metadata={
                    "word_count": 8500,
                    "sections": 6,
                    "progress": 70
                },
                created_at=datetime.now() - timedelta(days=2),
                likes_count=56,
                comments_count=23
            ),
            FeedItem(
                id=str(uuid.uuid4()),
                user_id="user_005",
                username="刘博士后",
                user_avatar=None,
                activity_type=ActivityType.CITE_PAPER,
                target_type="paper",
                target_id="paper_003",
                target_title="BERT: Pre-training of Deep Bidirectional Transformers",
                content="在最新的工作中引用了这篇经典论文，探讨了双向编码的优势。",
                metadata={
                    "citing_paper": "我们的新工作",
                    "citation_context": "相关方法"
                },
                created_at=datetime.now() - timedelta(days=2, hours=12),
                likes_count=19,
                comments_count=4
            ),
        ]

        self._feed_items.extend(sample_feeds)

        # 示例关注关系
        self._user_follows.extend([
            UserFollow(follower_id="current_user", following_id="user_001"),
            UserFollow(follower_id="current_user", following_id="user_002"),
            UserFollow(follower_id="current_user", following_id="user_003"),
        ])

    async def get_feed(
        self,
        user_id: str,
        filter_params: Optional[FeedFilter] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取用户动态流"""
        items = self._feed_items.copy()

        if filter_params:
            # 只显示关注的人
            if filter_params.following_only:
                following_ids = {
                    f.following_id for f in self._user_follows
                    if f.follower_id == user_id
                }
                items = [item for item in items if item.user_id in following_ids]

            # 活动类型筛选
            if filter_params.activity_types:
                items = [item for item in items if item.activity_type in filter_params.activity_types]

            # 目标类型筛选
            if filter_params.target_types:
                items = [item for item in items if item.target_type in filter_params.target_types]

        # 按时间排序
        items.sort(key=lambda x: x.created_at, reverse=True)

        # 标记点赞状态
        user_likes = self._user_likes.get(user_id, set())
        for item in items:
            item.is_liked = item.id in user_likes

        # 分页
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        items = items[start:end]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def get_user_activities(
        self,
        user_id: str,
        activity_types: Optional[List[ActivityType]] = None,
        limit: int = 50
    ) -> List[FeedItem]:
        """获取特定用户的活动"""
        items = [item for item in self._feed_items if item.user_id == user_id]

        if activity_types:
            items = [item for item in items if item.activity_type in activity_types]

        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]

    async def create_activity(self, feed_item: FeedItem) -> FeedItem:
        """创建动态"""
        if not feed_item.id:
            feed_item.id = str(uuid.uuid4())

        self._feed_items.insert(0, feed_item)

        # 限制总数
        if len(self._feed_items) > 10000:
            self._feed_items = self._feed_items[:10000]

        return feed_item

    async def like_feed_item(self, feed_item_id: str, user_id: str) -> bool:
        """点赞动态"""
        item = next((f for f in self._feed_items if f.id == feed_item_id), None)
        if not item:
            return False

        if user_id not in self._user_likes:
            self._user_likes[user_id] = set()

        if feed_item_id in self._user_likes[user_id]:
            # 取消点赞
            self._user_likes[user_id].remove(feed_item_id)
            item.likes_count = max(0, item.likes_count - 1)
            return False
        else:
            # 点赞
            self._user_likes[user_id].add(feed_item_id)
            item.likes_count += 1
            return True

    async def add_comment(
        self,
        feed_item_id: str,
        user_id: str,
        username: str,
        content: str
    ) -> Optional[Dict[str, Any]]:
        """添加评论"""
        item = next((f for f in self._feed_items if f.id == feed_item_id), None)
        if not item:
            return None

        item.comments_count += 1

        comment = {
            "id": str(uuid.uuid4()),
            "feed_item_id": feed_item_id,
            "user_id": user_id,
            "username": username,
            "content": content,
            "created_at": datetime.now()
        }

        return comment

    async def follow_user(self, follower_id: str, following_id: str) -> bool:
        """关注用户"""
        # 检查是否已关注
        existing = next(
            (f for f in self._user_follows
             if f.follower_id == follower_id and f.following_id == following_id),
            None
        )

        if existing:
            # 取消关注
            self._user_follows = [
                f for f in self._user_follows
                if not (f.follower_id == follower_id and f.following_id == following_id)
            ]
            return False
        else:
            # 添加关注
            follow = UserFollow(
                follower_id=follower_id,
                following_id=following_id
            )
            self._user_follows.append(follow)
            return True

    async def follow_team(self, user_id: str, team_id: str) -> bool:
        """关注团队"""
        existing = next(
            (f for f in self._team_follows
             if f.user_id == user_id and f.team_id == team_id),
            None
        )

        if existing:
            self._team_follows = [
                f for f in self._team_follows
                if not (f.user_id == user_id and f.team_id == team_id)
            ]
            return False
        else:
            follow = TeamFollow(user_id=user_id, team_id=team_id)
            self._team_follows.append(follow)
            return True

    async def follow_topic(self, user_id: str, topic: str) -> bool:
        """关注话题"""
        existing = next(
            (f for f in self._topic_follows
             if f.user_id == user_id and f.topic == topic),
            None
        )

        if existing:
            self._topic_follows = [
                f for f in self._topic_follows
                if not (f.user_id == user_id and f.topic == topic)
            ]
            return False
        else:
            follow = TopicFollow(user_id=user_id, topic=topic)
            self._topic_follows.append(follow)
            return True

    async def get_following(self, user_id: str) -> Dict[str, List[Any]]:
        """获取用户的关注列表"""
        following_users = [
            f.following_id for f in self._user_follows
            if f.follower_id == user_id
        ]

        following_teams = [
            f.team_id for f in self._team_follows
            if f.user_id == user_id
        ]

        following_topics = [
            f.topic for f in self._topic_follows
            if f.user_id == user_id
        ]

        return {
            "users": following_users,
            "teams": following_teams,
            "topics": following_topics
        }

    async def get_followers(self, user_id: str) -> List[str]:
        """获取用户的粉丝列表"""
        return [
            f.follower_id for f in self._user_follows
            if f.following_id == user_id
        ]

    async def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门话题"""
        # 统计动态中的话题
        topic_counts = {}
        for item in self._feed_items:
            if item.metadata and "topics" in item.metadata:
                for topic in item.metadata["topics"]:
                    if topic not in topic_counts:
                        topic_counts[topic] = {"count": 0, "activity": 0}
                    topic_counts[topic]["count"] += 1
                    topic_counts[topic]["activity"] += item.likes_count + item.comments_count

        # 排序
        sorted_topics = sorted(
            topic_counts.items(),
            key=lambda x: x[1]["activity"],
            reverse=True
        )[:limit]

        return [
            {
                "name": topic,
                "mentions": data["count"],
                "activity": data["activity"]
            }
            for topic, data in sorted_topics
        ]

    async def get_recommended_users(
        self,
        user_id: str,
        research_interests: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取推荐关注的用户"""
        # 基于研究兴趣推荐
        # 实际项目中会更复杂的推荐算法

        current_following = {
            f.following_id for f in self._user_follows
            if f.follower_id == user_id
        }

        # 获取活跃用户
        active_users = {}
        for item in self._feed_items:
            if item.user_id == user_id:
                continue
            if item.user_id not in active_users:
                active_users[item.user_id] = {
                    "user_id": item.user_id,
                    "username": item.username,
                    "avatar": item.user_avatar,
                    "activities": 0,
                    "total_engagement": 0
                }
            active_users[item.user_id]["activities"] += 1
            active_users[item.user_id]["total_engagement"] += item.likes_count + item.comments_count

        # 过滤已关注，按活跃度排序
        recommendations = [
            user for user in active_users.values()
            if user["user_id"] not in current_following
        ]
        recommendations.sort(key=lambda x: x["total_engagement"], reverse=True)

        return recommendations[:limit]


# 服务实例
feed_service = FeedService()
