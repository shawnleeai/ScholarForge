"""
数据管理服务
处理数据集CRUD、版本管理、权限控制等
"""

import uuid
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from models import (
    ResearchDataset, DatasetVersion, DatasetColumn, DataPreview,
    DataType, DatasetStatus, AccessLevel,
    DatasetCreateRequest, DatasetUpdateRequest, VersionCreateRequest
)


class DatasetService:
    """数据集服务"""

    def __init__(self, data_dir: str = "./data/datasets"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 内存存储 (实际使用数据库)
        self._datasets: Dict[str, ResearchDataset] = {}
        self._previews: Dict[str, DataPreview] = {}

        # 初始化示例数据
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据集"""
        sample_dataset = ResearchDataset(
            id="ds_001",
            name="房价预测数据集",
            description="包含房屋特征和价格信息的回归分析数据集",
            data_type=DataType.TABULAR,
            status=DatasetStatus.READY,
            owner_id="user_001",
            research_field="机器学习",
            tags=["回归", "房价", "房地产"],
            columns=[
                DatasetColumn(
                    name="area",
                    data_type="float",
                    description="房屋面积（平方米）",
                    stats={"min": 20, "max": 500, "mean": 120}
                ),
                DatasetColumn(
                    name="bedrooms",
                    data_type="int",
                    description="卧室数量",
                    stats={"min": 1, "max": 6, "mean": 2.5}
                ),
                DatasetColumn(
                    name="price",
                    data_type="float",
                    description="房屋价格（万元）",
                    stats={"min": 50, "max": 2000, "mean": 350}
                ),
            ],
            versions=[
                DatasetVersion(
                    id="ver_001",
                    dataset_id="ds_001",
                    version_number="1.0.0",
                    description="初始版本",
                    file_path="ds_001/v1.0.0/data.csv",
                    file_size=1024 * 1024 * 2,  # 2MB
                    row_count=1000,
                    checksum="abc123",
                    created_by="user_001",
                )
            ],
            current_version_id="ver_001",
            stats={
                "total_versions": 1,
                "total_downloads": 45,
                "last_accessed": datetime.now().isoformat()
            }
        )
        self._datasets[sample_dataset.id] = sample_dataset

        # 示例预览数据
        self._previews[sample_dataset.id] = DataPreview(
            columns=sample_dataset.columns,
            sample_data=[
                {"area": 89.5, "bedrooms": 2, "price": 280},
                {"area": 120.0, "bedrooms": 3, "price": 420},
                {"area": 156.5, "bedrooms": 4, "price": 580},
                {"area": 75.0, "bedrooms": 2, "price": 195},
                {"area": 200.0, "bedrooms": 5, "price": 850},
            ],
            total_rows=1000,
            total_columns=3
        )

    async def create_dataset(
        self,
        user_id: str,
        request: DatasetCreateRequest
    ) -> ResearchDataset:
        """创建新数据集"""
        dataset_id = str(uuid.uuid4())

        dataset = ResearchDataset(
            id=dataset_id,
            name=request.name,
            description=request.description,
            data_type=request.data_type,
            owner_id=user_id,
            research_field=request.research_field,
            tags=request.tags,
            access_level=request.access_level,
            status=DatasetStatus.DRAFT
        )

        self._datasets[dataset_id] = dataset
        return dataset

    async def get_dataset(
        self,
        dataset_id: str,
        user_id: Optional[str] = None
    ) -> Optional[ResearchDataset]:
        """获取数据集详情"""
        dataset = self._datasets.get(dataset_id)
        if not dataset:
            return None

        # 检查访问权限
        if not self._can_access(dataset, user_id):
            raise PermissionError("没有权限访问此数据集")

        return dataset

    async def update_dataset(
        self,
        dataset_id: str,
        user_id: str,
        request: DatasetUpdateRequest
    ) -> Optional[ResearchDataset]:
        """更新数据集信息"""
        dataset = self._datasets.get(dataset_id)
        if not dataset:
            return None

        # 检查所有权
        if dataset.owner_id != user_id:
            raise PermissionError("只有所有者可以更新数据集")

        if request.name is not None:
            dataset.name = request.name
        if request.description is not None:
            dataset.description = request.description
        if request.tags is not None:
            dataset.tags = request.tags
        if request.access_level is not None:
            dataset.access_level = request.access_level

        dataset.updated_at = datetime.now()
        return dataset

    async def delete_dataset(self, dataset_id: str, user_id: str) -> bool:
        """删除数据集"""
        dataset = self._datasets.get(dataset_id)
        if not dataset:
            return False

        if dataset.owner_id != user_id:
            raise PermissionError("只有所有者可以删除数据集")

        del self._datasets[dataset_id]
        return True

    async def list_datasets(
        self,
        user_id: str,
        data_type: Optional[DataType] = None,
        research_field: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """列出用户可访问的数据集"""
        datasets = [
            ds for ds in self._datasets.values()
            if self._can_access(ds, user_id)
        ]

        if data_type:
            datasets = [ds for ds in datasets if ds.data_type == data_type]
        if research_field:
            datasets = [ds for ds in datasets if ds.research_field == research_field]

        total = len(datasets)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "datasets": datasets[start:end],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def create_version(
        self,
        dataset_id: str,
        user_id: str,
        file_path: str,
        request: VersionCreateRequest
    ) -> Optional[DatasetVersion]:
        """创建新版本"""
        dataset = self._datasets.get(dataset_id)
        if not dataset:
            return None

        if dataset.owner_id != user_id:
            raise PermissionError("只有所有者可以创建版本")

        # 生成版本号
        version_number = request.version_number
        if not version_number:
            # 自动递增版本号
            if dataset.versions:
                latest = dataset.versions[-1].version_number
                parts = latest.split(".")
                version_number = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
            else:
                version_number = "1.0.0"

        # 计算文件信息
        file_size = Path(file_path).stat().st_size
        checksum = self._calculate_checksum(file_path)

        version = DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            version_number=version_number,
            description=request.description,
            file_path=file_path,
            file_size=file_size,
            checksum=checksum,
            created_by=user_id,
            changes=request.changes,
            is_latest=True
        )

        # 更新旧版本
        for v in dataset.versions:
            v.is_latest = False

        dataset.versions.append(version)
        dataset.current_version_id = version.id
        dataset.status = DatasetStatus.READY
        dataset.updated_at = datetime.now()

        return version

    async def get_preview(
        self,
        dataset_id: str,
        version_id: Optional[str] = None,
        sample_size: int = 100
    ) -> Optional[DataPreview]:
        """获取数据预览"""
        dataset = self._datasets.get(dataset_id)
        if not dataset:
            return None

        # 返回缓存的预览或生成新的
        if dataset_id in self._previews:
            return self._previews[dataset_id]

        return None

    async def analyze_dataset(
        self,
        dataset_id: str,
        version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """分析数据集"""
        preview = await self.get_preview(dataset_id, version_id)
        if not preview:
            return {}

        analysis = {
            "columns": [],
            "correlations": {},
            "missing_values": {},
            "recommendations": []
        }

        for col in preview.columns:
            col_analysis = {
                "name": col.name,
                "type": col.data_type,
                "stats": col.stats
            }
            analysis["columns"].append(col_analysis)

        return analysis

    def _can_access(
        self,
        dataset: ResearchDataset,
        user_id: Optional[str] = None
    ) -> bool:
        """检查用户是否有权限访问数据集"""
        if dataset.access_level == AccessLevel.PUBLIC:
            return True
        if not user_id:
            return False
        if dataset.owner_id == user_id:
            return True
        if user_id in dataset.shared_with:
            return True
        return False

    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# 服务实例
dataset_service = DatasetService()
