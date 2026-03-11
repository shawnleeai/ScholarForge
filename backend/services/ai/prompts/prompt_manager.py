"""
Prompt管理器
支持Prompt版本管理、A/B测试、效果追踪
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

from .academic_prompts import AcademicPrompts, PromptTemplate, PromptType

logger = logging.getLogger(__name__)


class PromptStatus(str, Enum):
    """Prompt状态"""
    DRAFT = "draft"  # 草稿
    ACTIVE = "active"  # 活跃
    DEPRECATED = "deprecated"  # 已弃用
    ARCHIVED = "archived"  # 已归档


@dataclass
class PromptVersion:
    """Prompt版本"""
    version: str
    template: str
    created_at: datetime
    created_by: str
    changes: str  # 变更说明
    performance_score: Optional[float] = None


@dataclass
class PromptMetrics:
    """Prompt效果指标"""
    prompt_id: str
    version: str
    total_calls: int = 0
    avg_response_length: float = 0
    avg_latency_ms: float = 0
    user_rating_avg: float = 0
    user_ratings_count: int = 0
    success_rate: float = 0
    error_rate: float = 0
    last_used: Optional[datetime] = None


class PromptManager:
    """Prompt管理器"""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Args:
            storage_path: 存储路径，用于持久化Prompt数据
        """
        self.storage_path = storage_path
        self.prompts: Dict[str, Dict] = {}  # prompt_id -> prompt_data
        self.versions: Dict[str, List[PromptVersion]] = {}  # prompt_id -> versions
        self.metrics: Dict[str, PromptMetrics] = {}  # prompt_id:version -> metrics
        self.active_versions: Dict[str, str] = {}  # prompt_id -> active_version

        # 加载默认Prompt
        self._load_default_prompts()

        # 尝试加载持久化数据
        if storage_path:
            self._load_from_storage()

    def _load_default_prompts(self):
        """加载默认学术Prompt"""
        default_prompts = AcademicPrompts.get_all_prompts()

        for prompt_type, template in default_prompts.items():
            prompt_id = f"default_{prompt_type.value}"

            self.prompts[prompt_id] = {
                "id": prompt_id,
                "name": template.name,
                "type": prompt_type.value,
                "description": template.description,
                "status": PromptStatus.ACTIVE,
                "created_at": datetime.now(),
                "variables": template.variables,
                "tips": template.tips,
            }

            # 创建初始版本
            version = PromptVersion(
                version="1.0",
                template=template.template,
                created_at=datetime.now(),
                created_by="system",
                changes="初始版本"
            )

            self.versions[prompt_id] = [version]
            self.active_versions[prompt_id] = "1.0"

            # 初始化指标
            self.metrics[f"{prompt_id}:1.0"] = PromptMetrics(
                prompt_id=prompt_id,
                version="1.0"
            )

    def create_prompt(
        self,
        name: str,
        prompt_type: PromptType,
        template: str,
        description: str,
        variables: List[str],
        created_by: str = "user"
    ) -> str:
        """
        创建新Prompt

        Returns:
            prompt_id
        """
        # 生成ID
        prompt_id = f"{prompt_type.value}_{hashlib.md5(name.encode()).hexdigest()[:8]}"

        if prompt_id in self.prompts:
            raise ValueError(f"Prompt with name '{name}' already exists")

        # 创建Prompt
        self.prompts[prompt_id] = {
            "id": prompt_id,
            "name": name,
            "type": prompt_type.value,
            "description": description,
            "status": PromptStatus.ACTIVE,
            "created_at": datetime.now(),
            "variables": variables,
            "tips": [],
        }

        # 创建初始版本
        version = PromptVersion(
            version="1.0",
            template=template,
            created_at=datetime.now(),
            created_by=created_by,
            changes="初始版本"
        )

        self.versions[prompt_id] = [version]
        self.active_versions[prompt_id] = "1.0"

        self.metrics[f"{prompt_id}:1.0"] = PromptMetrics(
            prompt_id=prompt_id,
            version="1.0"
        )

        logger.info(f"Created new prompt: {prompt_id}")
        return prompt_id

    def update_prompt(
        self,
        prompt_id: str,
        new_template: str,
        changes: str,
        updated_by: str = "user"
    ) -> str:
        """
        更新Prompt（创建新版本）

        Returns:
            新版本号
        """
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt not found: {prompt_id}")

        # 计算新版本号
        versions = self.versions[prompt_id]
        current_version = versions[-1].version
        new_version = self._increment_version(current_version)

        # 创建新版本
        version = PromptVersion(
            version=new_version,
            template=new_template,
            created_at=datetime.now(),
            created_by=updated_by,
            changes=changes
        )

        versions.append(version)

        # 初始化新版本的指标
        self.metrics[f"{prompt_id}:{new_version}"] = PromptMetrics(
            prompt_id=prompt_id,
            version=new_version
        )

        logger.info(f"Created new version {new_version} for prompt: {prompt_id}")
        return new_version

    def set_active_version(self, prompt_id: str, version: str):
        """设置活跃版本"""
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt not found: {prompt_id}")

        if not any(v.version == version for v in self.versions[prompt_id]):
            raise ValueError(f"Version {version} not found for prompt {prompt_id}")

        self.active_versions[prompt_id] = version
        logger.info(f"Set active version {version} for prompt: {prompt_id}")

    def get_prompt(self, prompt_id: str, version: Optional[str] = None) -> PromptTemplate:
        """
        获取Prompt

        Args:
            prompt_id: Prompt ID
            version: 指定版本，None则使用活跃版本

        Returns:
            Prompt模板
        """
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt not found: {prompt_id}")

        prompt_data = self.prompts[prompt_id]

        # 确定版本
        if version is None:
            version = self.active_versions.get(prompt_id, "1.0")

        # 获取版本数据
        version_obj = next(
            (v for v in self.versions[prompt_id] if v.version == version),
            None
        )

        if version_obj is None:
            raise ValueError(f"Version {version} not found")

        return PromptTemplate(
            name=prompt_data["name"],
            type=PromptType(prompt_data["type"]),
            template=version_obj.template,
            description=prompt_data["description"],
            version=version,
            variables=prompt_data.get("variables", []),
            tips=prompt_data.get("tips", [])
        )

    def record_usage(
        self,
        prompt_id: str,
        version: str,
        latency_ms: float,
        response_length: int,
        success: bool = True
    ):
        """记录Prompt使用情况"""
        key = f"{prompt_id}:{version}"

        if key not in self.metrics:
            self.metrics[key] = PromptMetrics(
                prompt_id=prompt_id,
                version=version
            )

        metrics = self.metrics[key]
        metrics.total_calls += 1
        metrics.last_used = datetime.now()

        # 更新平均延迟
        metrics.avg_latency_ms = (
            (metrics.avg_latency_ms * (metrics.total_calls - 1) + latency_ms)
            / metrics.total_calls
        )

        # 更新平均响应长度
        metrics.avg_response_length = (
            (metrics.avg_response_length * (metrics.total_calls - 1) + response_length)
            / metrics.total_calls
        )

        # 更新成功率
        if success:
            metrics.success_rate = (
                (metrics.success_rate * (metrics.total_calls - 1) + 1)
                / metrics.total_calls
            )
        else:
            metrics.success_rate = (
                metrics.success_rate * (metrics.total_calls - 1)
                / metrics.total_calls
            )
            metrics.error_rate = 1 - metrics.success_rate

    def record_rating(
        self,
        prompt_id: str,
        version: str,
        rating: float  # 1-5
    ):
        """记录用户评分"""
        key = f"{prompt_id}:{version}"

        if key not in self.metrics:
            return

        metrics = self.metrics[key]
        metrics.user_ratings_count += 1
        metrics.user_rating_avg = (
            (metrics.user_rating_avg * (metrics.user_ratings_count - 1) + rating)
            / metrics.user_ratings_count
        )

    def compare_versions(
        self,
        prompt_id: str,
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        """
        比较两个版本的性能

        Returns:
            比较结果
        """
        key_a = f"{prompt_id}:{version_a}"
        key_b = f"{prompt_id}:{version_b}"

        metrics_a = self.metrics.get(key_a)
        metrics_b = self.metrics.get(key_b)

        if not metrics_a or not metrics_b:
            return {"error": "Metrics not found for one or both versions"}

        return {
            "version_a": version_a,
            "version_b": version_b,
            "comparison": {
                "total_calls": {
                    "a": metrics_a.total_calls,
                    "b": metrics_b.total_calls,
                    "winner": "a" if metrics_a.total_calls > metrics_b.total_calls else "b"
                },
                "avg_latency_ms": {
                    "a": round(metrics_a.avg_latency_ms, 2),
                    "b": round(metrics_b.avg_latency_ms, 2),
                    "winner": "a" if metrics_a.avg_latency_ms < metrics_b.avg_latency_ms else "b"
                },
                "user_rating_avg": {
                    "a": round(metrics_a.user_rating_avg, 2),
                    "b": round(metrics_b.user_rating_avg, 2),
                    "winner": "a" if metrics_a.user_rating_avg > metrics_b.user_rating_avg else "b"
                },
                "success_rate": {
                    "a": round(metrics_a.success_rate, 4),
                    "b": round(metrics_b.success_rate, 4),
                    "winner": "a" if metrics_a.success_rate > metrics_b.success_rate else "b"
                }
            }
        }

    def get_best_version(self, prompt_id: str) -> Optional[str]:
        """
        根据指标获取最佳版本
        """
        if prompt_id not in self.prompts:
            return None

        versions = self.versions[prompt_id]
        best_version = None
        best_score = -1

        for version in versions:
            key = f"{prompt_id}:{version.version}"
            metrics = self.metrics.get(key)

            if not metrics or metrics.total_calls < 10:  # 至少需要10次调用
                continue

            # 综合评分
            score = (
                metrics.user_rating_avg * 0.4 +
                metrics.success_rate * 5 * 0.3 +  # 转换为5分制
                (1 - min(metrics.avg_latency_ms / 5000, 1)) * 5 * 0.3  # 延迟越短越好
            )

            if score > best_score:
                best_score = score
                best_version = version.version

        return best_version

    def list_prompts(
        self,
        prompt_type: Optional[PromptType] = None,
        status: Optional[PromptStatus] = None
    ) -> List[Dict]:
        """列出所有Prompt"""
        results = []

        for prompt_id, prompt_data in self.prompts.items():
            # 过滤
            if prompt_type and prompt_data["type"] != prompt_type.value:
                continue
            if status and prompt_data["status"] != status:
                continue

            # 获取活跃版本的指标
            active_version = self.active_versions.get(prompt_id, "1.0")
            metrics_key = f"{prompt_id}:{active_version}"
            metrics = self.metrics.get(metrics_key)

            results.append({
                "id": prompt_id,
                "name": prompt_data["name"],
                "type": prompt_data["type"],
                "description": prompt_data["description"],
                "status": prompt_data["status"],
                "active_version": active_version,
                "version_count": len(self.versions.get(prompt_id, [])),
                "metrics": {
                    "total_calls": metrics.total_calls if metrics else 0,
                    "avg_rating": round(metrics.user_rating_avg, 2) if metrics else 0,
                    "success_rate": round(metrics.success_rate, 4) if metrics else 0
                }
            })

        return results

    def _increment_version(self, current_version: str) -> str:
        """递增版本号"""
        parts = current_version.split(".")
        if len(parts) == 2:
            major, minor = int(parts[0]), int(parts[1])
            return f"{major}.{minor + 1}"
        return "1.0"

    def _load_from_storage(self):
        """从存储加载数据"""
        import os
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 恢复数据
            # 注意：实际实现需要更完整的反序列化逻辑
            logger.info(f"Loaded prompts from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")

    def save_to_storage(self):
        """保存到存储"""
        if not self.storage_path:
            return

        try:
            data = {
                "prompts": self.prompts,
                "versions": {
                    k: [asdict(v) for v in vs]
                    for k, vs in self.versions.items()
                },
                "metrics": {
                    k: asdict(m) for k, m in self.metrics.items()
                },
                "active_versions": self.active_versions
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Saved prompts to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save prompts: {e}")


# 全局Prompt管理器实例
prompt_manager = PromptManager()
