"""
AI Tools Marketplace Service
AI科研工具商店服务 - 工具发布、购买、评价管理
"""

import uuid
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .models import Tool, ToolType, PricingType, ToolStatus, ToolReview, ToolPurchase, DeveloperProfile


class MarketplaceService:
    """工具商店服务"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._reviews: Dict[str, List[ToolReview]] = {}
        self._purchases: Dict[str, ToolPurchase] = {}
        self._developers: Dict[str, DeveloperProfile] = {}

    # ==================== 工具管理 ====================

    def create_tool(
        self,
        name: str,
        description: str,
        tool_type: ToolType,
        developer_id: str,
        **kwargs
    ) -> Tool:
        """创建工具"""
        tool = Tool(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            tool_type=tool_type,
            developer_id=developer_id,
            status=ToolStatus.DRAFT,
            **kwargs
        )
        self._tools[tool.id] = tool
        return tool

    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """获取工具详情"""
        tool = self._tools.get(tool_id)
        if tool and tool.status == ToolStatus.PUBLISHED:
            tool.download_count += 1
        return tool

    def update_tool(
        self,
        tool_id: str,
        developer_id: str,
        **updates
    ) -> Optional[Tool]:
        """更新工具"""
        tool = self._tools.get(tool_id)
        if not tool or tool.developer_id != developer_id:
            return None

        for key, value in updates.items():
            if hasattr(tool, key):
                setattr(tool, key, value)

        tool.updated_at = datetime.utcnow()
        return tool

    def publish_tool(self, tool_id: str, developer_id: str) -> bool:
        """发布工具"""
        tool = self._tools.get(tool_id)
        if not tool or tool.developer_id != developer_id:
            return False

        tool.status = ToolStatus.PENDING
        # 实际应提交审核
        tool.status = ToolStatus.PUBLISHED
        tool.published_at = datetime.utcnow()

        # 更新开发者统计
        self._update_developer_stats(tool.developer_id)

        return True

    def list_tools(
        self,
        tool_type: Optional[ToolType] = None,
        category: Optional[str] = None,
        pricing: Optional[PricingType] = None,
        sort_by: str = "popular",
        limit: int = 20
    ) -> List[Tool]:
        """列出工具"""
        tools = [
            t for t in self._tools.values()
            if t.status == ToolStatus.PUBLISHED
        ]

        if tool_type:
            tools = [t for t in tools if t.tool_type == tool_type]

        if category:
            tools = [t for t in tools if category in t.categories]

        if pricing:
            tools = [t for t in tools if t.pricing_type == pricing]

        # 排序
        if sort_by == "popular":
            tools.sort(key=lambda x: x.download_count, reverse=True)
        elif sort_by == "rated":
            tools.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == "newest":
            tools.sort(key=lambda x: x.published_at or x.created_at, reverse=True)
        elif sort_by == "price_asc":
            tools.sort(key=lambda x: x.price)
        elif sort_by == "price_desc":
            tools.sort(key=lambda x: x.price, reverse=True)

        return tools[:limit]

    def search_tools(
        self,
        query: str,
        limit: int = 20
    ) -> List[Tool]:
        """搜索工具"""
        query_lower = query.lower()

        tools = [
            t for t in self._tools.values()
            if t.status == ToolStatus.PUBLISHED and (
                query_lower in t.name.lower() or
                query_lower in t.description.lower() or
                any(query_lower in tag.lower() for tag in t.tags)
            )
        ]

        # 按相关性排序（名称匹配优先）
        def relevance_score(tool: Tool) -> float:
            score = 0.0
            if query_lower in tool.name.lower():
                score += 10
            if query_lower in tool.description.lower():
                score += 5
            score += tool.rating * 2
            score += tool.download_count * 0.001
            return score

        tools.sort(key=relevance_score, reverse=True)
        return tools[:limit]

    def get_developer_tools(self, developer_id: str) -> List[Tool]:
        """获取开发者的工具"""
        return [
            t for t in self._tools.values()
            if t.developer_id == developer_id
        ]

    # ==================== 购买管理 ====================

    def purchase_tool(
        self,
        tool_id: str,
        user_id: str
    ) -> Optional[ToolPurchase]:
        """购买工具"""
        tool = self._tools.get(tool_id)
        if not tool or tool.status != ToolStatus.PUBLISHED:
            return None

        # 检查是否已购买
        existing = self._get_purchase(tool_id, user_id)
        if existing:
            return existing

        # 免费工具
        if tool.pricing_type == PricingType.FREE:
            purchase = ToolPurchase(
                id=str(uuid.uuid4()),
                tool_id=tool_id,
                user_id=user_id,
                amount=0,
                currency=tool.currency
            )
            self._purchases[purchase.id] = purchase
            return purchase

        # 付费工具
        expires_at = None
        if tool.pricing_type == PricingType.SUBSCRIPTION:
            if tool.subscription_period == "monthly":
                expires_at = datetime.utcnow() + timedelta(days=30)
            else:
                expires_at = datetime.utcnow() + timedelta(days=365)

        license_key = self._generate_license_key(tool_id, user_id)

        purchase = ToolPurchase(
            id=str(uuid.uuid4()),
            tool_id=tool_id,
            user_id=user_id,
            amount=tool.price,
            currency=tool.currency,
            expires_at=expires_at,
            license_key=license_key
        )

        self._purchases[purchase.id] = purchase
        return purchase

    def check_purchase(self, tool_id: str, user_id: str) -> bool:
        """检查是否已购买"""
        purchase = self._get_purchase(tool_id, user_id)
        if not purchase:
            return False

        if purchase.expires_at and datetime.utcnow() > purchase.expires_at:
            return False

        return True

    def _get_purchase(self, tool_id: str, user_id: str) -> Optional[ToolPurchase]:
        """获取购买记录"""
        for p in self._purchases.values():
            if p.tool_id == tool_id and p.user_id == user_id:
                return p
        return None

    def _generate_license_key(self, tool_id: str, user_id: str) -> str:
        """生成许可证密钥"""
        key_string = f"{tool_id}:{user_id}:{datetime.utcnow().timestamp()}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:32].upper()

    def get_user_purchases(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户购买记录"""
        purchases = [
            p for p in self._purchases.values()
            if p.user_id == user_id
        ]

        result = []
        for p in purchases:
            tool = self._tools.get(p.tool_id)
            if tool:
                result.append({
                    "purchase_id": p.id,
                    "tool_id": p.tool_id,
                    "tool_name": tool.name,
                    "amount": p.amount,
                    "currency": p.currency,
                    "purchased_at": p.purchased_at.isoformat(),
                    "expires_at": p.expires_at.isoformat() if p.expires_at else None,
                    "license_key": p.license_key[:8] + "..." if p.license_key else None
                })

        return result

    # ==================== 评价管理 ====================

    def add_review(
        self,
        tool_id: str,
        user_id: str,
        rating: int,
        title: str,
        content: str,
        is_recommended: bool = False
    ) -> Optional[ToolReview]:
        """添加评价"""
        tool = self._tools.get(tool_id)
        if not tool:
            return None

        # 检查是否已购买
        if not self.check_purchase(tool_id, user_id):
            return None

        review = ToolReview(
            id=str(uuid.uuid4()),
            tool_id=tool_id,
            user_id=user_id,
            rating=rating,
            title=title,
            content=content,
            is_recommended=is_recommended
        )

        if tool_id not in self._reviews:
            self._reviews[tool_id] = []

        self._reviews[tool_id].append(review)

        # 更新工具评分
        tool.rating_sum += rating
        tool.rating_count += 1
        tool.review_count += 1

        return review

    def get_reviews(self, tool_id: str, limit: int = 20) -> List[ToolReview]:
        """获取工具评价"""
        reviews = self._reviews.get(tool_id, [])
        reviews.sort(key=lambda x: x.helpful_count, reverse=True)
        return reviews[:limit]

    def mark_review_helpful(self, review_id: str, tool_id: str) -> bool:
        """标记评价有用"""
        reviews = self._reviews.get(tool_id, [])
        for review in reviews:
            if review.id == review_id:
                review.helpful_count += 1
                return True
        return False

    # ==================== 开发者管理 ====================

    def create_developer_profile(
        self,
        user_id: str,
        display_name: str,
        **kwargs
    ) -> DeveloperProfile:
        """创建开发者主页"""
        profile = DeveloperProfile(
            user_id=user_id,
            display_name=display_name,
            **kwargs
        )
        self._developers[user_id] = profile
        return profile

    def get_developer_profile(self, user_id: str) -> Optional[DeveloperProfile]:
        """获取开发者主页"""
        return self._developers.get(user_id)

    def update_developer_profile(
        self,
        user_id: str,
        **updates
    ) -> Optional[DeveloperProfile]:
        """更新开发者主页"""
        profile = self._developers.get(user_id)
        if not profile:
            return None

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        return profile

    def _update_developer_stats(self, developer_id: str):
        """更新开发者统计"""
        profile = self._developers.get(developer_id)
        if not profile:
            return

        tools = self.get_developer_tools(developer_id)
        published_tools = [t for t in tools if t.status == ToolStatus.PUBLISHED]

        profile.total_tools = len(published_tools)
        profile.total_downloads = sum(t.download_count for t in published_tools)

        total_rating = sum(t.rating for t in published_tools)
        profile.average_rating = total_rating / len(published_tools) if published_tools else 0.0

    def get_developer_revenue(self, developer_id: str) -> Dict[str, Any]:
        """获取开发者收入统计"""
        # 获取该开发者的所有销售
        tool_ids = {t.id for t in self.get_developer_tools(developer_id)}

        sales = [
            p for p in self._purchases.values()
            if p.tool_id in tool_ids and p.amount > 0
        ]

        total_revenue = sum(s.amount for s in sales)

        by_tool = {}
        for sale in sales:
            if sale.tool_id not in by_tool:
                by_tool[sale.tool_id] = {"count": 0, "revenue": 0.0}
            by_tool[sale.tool_id]["count"] += 1
            by_tool[sale.tool_id]["revenue"] += sale.amount

        return {
            "total_revenue": total_revenue,
            "total_sales": len(sales),
            "by_tool": by_tool
        }

    # ==================== 推荐 ====================

    def get_recommended_tools(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Tool]:
        """推荐工具"""
        # 获取用户已购买的工具类型
        user_purchases = [
            p for p in self._purchases.values()
            if p.user_id == user_id
        ]

        purchased_types = set()
        purchased_categories = set()

        for p in user_purchases:
            tool = self._tools.get(p.tool_id)
            if tool:
                purchased_types.add(tool.tool_type)
                purchased_categories.update(tool.categories)

        # 推荐相似工具
        candidates = [
            t for t in self._tools.values()
            if t.status == ToolStatus.PUBLISHED
            and not self.check_purchase(t.id, user_id)  # 未购买
        ]

        def relevance_score(tool: Tool) -> float:
            score = 0.0

            # 类型匹配
            if tool.tool_type in purchased_types:
                score += 5

            # 分类匹配
            for cat in tool.categories:
                if cat in purchased_categories:
                    score += 3

            # 热度
            score += tool.rating * 2
            score += tool.download_count * 0.001

            return score

        candidates.sort(key=relevance_score, reverse=True)
        return candidates[:limit]


# 单例
_marketplace_service = None


def get_marketplace_service() -> MarketplaceService:
    """获取商店服务单例"""
    global _marketplace_service
    if _marketplace_service is None:
        _marketplace_service = MarketplaceService()
    return _marketplace_service
