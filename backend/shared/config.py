"""
应用配置模块
使用 pydantic-settings 管理环境变量配置
"""

import logging
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Optional, List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# 定位项目根目录的 .env 文件
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础配置
    app_name: str = "ScholarForge"
    app_version: str = "0.1.0"
    debug: bool = False

    # 服务配置
    service_name: str = "scholarforge-service"
    service_port: int = 8000

    # 数据库配置（生产环境请通过环境变量设置）
    database_url: str = "postgresql://user:password@localhost:5432/scholarforge"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"

    # JWT 配置（开发环境有默认值，生产环境必须设置）
    jwt_secret: str = ""  # 默认为空，在 __init__ 中处理
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 1  # 访问令牌1小时过期，提高安全性
    jwt_refresh_expire_days: int = 7  # 刷新令牌7天过期

    # CORS 配置（逗号分隔的字符串或JSON数组）
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS来源，支持逗号分隔字符串或列表"""
        if isinstance(v, str):
            # 尝试解析为JSON数组
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # 按逗号分割
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # 外部 API 配置
    cnki_api_key: Optional[str] = None
    cnki_api_secret: Optional[str] = None
    wos_api_key: Optional[str] = None
    ieee_api_key: Optional[str] = None

    # AI 服务配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"

    # 国产大模型配置
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    moonshot_api_key: Optional[str] = None
    moonshot_model: str = "moonshot-v1-8k"

    # 阶跃星辰配置
    stepfun_api_key: Optional[str] = None
    stepfun_model: str = "step-1-8k"

    # AI 默认设置
    ai_default_provider: str = "openai"
    ai_fallback_enabled: bool = True

    # 文件存储配置（开发环境有默认值，生产环境必须设置）
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "scholarforge"
    minio_secure: bool = False

    # Elasticsearch 配置
    elasticsearch_url: str = "http://localhost:9200"

    # Neo4j 配置（开发环境有默认值，生产环境必须设置）
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    def model_post_init(self, __context):
        """初始化后处理：为开发环境生成默认值，生产环境发出警告"""
        # JWT Secret 处理
        if not self.jwt_secret:
            if self.debug:
                # 开发环境：生成随机密钥
                object.__setattr__(self, 'jwt_secret', secrets.token_urlsafe(32))
                logger.warning("JWT_SECRET 未设置，已为开发环境生成随机密钥。生产环境请设置环境变量！")
            else:
                raise ValueError(
                    "JWT_SECRET 环境变量未设置！生产环境必须配置安全的 JWT 密钥。"
                )

        # MinIO 配置检查
        if not self.minio_access_key or not self.minio_secret_key:
            if self.debug:
                logger.warning(
                    "MINIO_ACCESS_KEY 或 MINIO_SECRET_KEY 未设置。"
                    "文件存储功能可能无法正常工作。"
                )

        # Neo4j 配置检查
        if not self.neo4j_password:
            if self.debug:
                logger.warning(
                    "NEO4J_PASSWORD 未设置。知识图谱功能可能无法正常工作。"
                )


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
