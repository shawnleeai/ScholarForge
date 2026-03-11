"""
研究数据集模型
定义数据集、数据版本、元数据等数据模型
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DataType(str, Enum):
    """数据类型"""
    TABULAR = "tabular"          # 表格数据
    IMAGE = "image"              # 图像数据
    TEXT = "text"                # 文本数据
    AUDIO = "audio"              # 音频数据
    VIDEO = "video"              # 视频数据
    SPATIAL = "spatial"          # 空间数据
    TIME_SERIES = "time_series"  # 时序数据
    MIXED = "mixed"              # 混合数据


class DatasetStatus(str, Enum):
    """数据集状态"""
    DRAFT = "draft"              # 草稿
    PROCESSING = "processing"    # 处理中
    READY = "ready"              # 可用
    ARCHIVED = "archived"        # 已归档
    ERROR = "error"              # 错误


class AccessLevel(str, Enum):
    """访问级别"""
    PRIVATE = "private"          # 私有
    TEAM = "team"                # 团队
    ORGANIZATION = "organization"  # 组织
    PUBLIC = "public"            # 公开


class DatasetColumn(BaseModel):
    """数据集列信息"""
    name: str
    data_type: str               # int, float, string, datetime, etc.
    description: Optional[str] = None
    nullable: bool = True
    unique: bool = False
    stats: Dict[str, Any] = Field(default_factory=dict)  # min, max, mean, etc.
    sample_values: List[Any] = []


class DatasetVersion(BaseModel):
    """数据集版本"""
    id: str
    dataset_id: str
    version_number: str          # semver格式，如 "1.0.0"
    description: Optional[str] = None
    file_path: str
    file_size: int               # 字节
    row_count: Optional[int] = None
    checksum: str                # 文件校验和
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    changes: List[str] = []      # 版本变更说明
    is_latest: bool = True


class DataPreview(BaseModel):
    """数据预览"""
    columns: List[DatasetColumn]
    sample_data: List[Dict[str, Any]]  # 前N行数据
    total_rows: int
    total_columns: int
    memory_usage: Optional[int] = None  # 内存占用估计


class ResearchDataset(BaseModel):
    """研究数据集"""
    id: str
    name: str
    description: Optional[str] = None
    data_type: DataType
    status: DatasetStatus = DatasetStatus.DRAFT

    # 所属关系
    owner_id: str
    team_id: Optional[str] = None
    project_id: Optional[str] = None

    # 版本
    versions: List[DatasetVersion] = []
    current_version_id: Optional[str] = None

    # 元数据
    columns: List[DatasetColumn] = []
    tags: List[str] = []
    research_field: Optional[str] = None

    # 访问控制
    access_level: AccessLevel = AccessLevel.PRIVATE
    shared_with: List[str] = []  # 用户ID列表

    # 统计
    stats: Dict[str, Any] = Field(default_factory=dict)

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DataAnalysis(BaseModel):
    """数据分析结果"""
    id: str
    dataset_id: str
    version_id: str
    analysis_type: str           # profile, correlation, distribution, etc.
    results: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str


class DatasetSearchRequest(BaseModel):
    """数据集搜索请求"""
    query: Optional[str] = None
    data_type: Optional[DataType] = None
    research_field: Optional[str] = None
    access_level: Optional[AccessLevel] = None
    tags: Optional[List[str]] = None
    owner_id: Optional[str] = None
    page: int = 1
    page_size: int = 20


class DatasetCreateRequest(BaseModel):
    """创建数据集请求"""
    name: str
    description: Optional[str] = None
    data_type: DataType
    research_field: Optional[str] = None
    tags: List[str] = []
    access_level: AccessLevel = AccessLevel.PRIVATE


class DatasetUpdateRequest(BaseModel):
    """更新数据集请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    access_level: Optional[AccessLevel] = None


class VersionCreateRequest(BaseModel):
    """创建版本请求"""
    version_number: Optional[str] = None  # 不传则自动生成
    description: Optional[str] = None
    changes: List[str] = []
