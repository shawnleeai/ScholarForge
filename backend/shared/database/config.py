"""
数据库配置
支持多环境、多数据库类型配置
"""

import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


class DatabaseType(str, Enum):
    """数据库类型"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


class DeploymentEnv(str, Enum):
    """部署环境"""
    LOCAL = "local"
    DOCKER = "docker"
    ALIYUN = "aliyun"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


@dataclass
class DatabaseConfig:
    """数据库配置类"""

    # 基础配置
    db_type: DatabaseType = DatabaseType.POSTGRESQL
    host: str = "localhost"
    port: int = 5432
    database: str = "scholarforge"
    username: str = "postgres"
    password: str = ""

    # 连接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # 高级配置
    echo: bool = False  # SQL语句日志
    ssl_mode: Optional[str] = None  # SSL模式
    ssl_ca_cert: Optional[str] = None  # SSL证书路径
    charset: str = "utf8mb4"  # MySQL字符集

    # 读写分离配置
    read_replicas: list = field(default_factory=list)

    @classmethod
    def from_env(cls, env_prefix: str = "DB") -> "DatabaseConfig":
        """从环境变量加载配置"""
        db_type_str = os.getenv(f"{env_prefix}_TYPE", "postgresql").lower()

        return cls(
            db_type=DatabaseType(db_type_str),
            host=os.getenv(f"{env_prefix}_HOST", "localhost"),
            port=int(os.getenv(f"{env_prefix}_PORT", "5432")),
            database=os.getenv(f"{env_prefix}_NAME", "scholarforge"),
            username=os.getenv(f"{env_prefix}_USER", "postgres"),
            password=os.getenv(f"{env_prefix}_PASSWORD", ""),
            pool_size=int(os.getenv(f"{env_prefix}_POOL_SIZE", "10")),
            max_overflow=int(os.getenv(f"{env_prefix}_MAX_OVERFLOW", "20")),
            echo=os.getenv(f"{env_prefix}_ECHO", "false").lower() == "true",
            ssl_mode=os.getenv(f"{env_prefix}_SSL_MODE"),
            ssl_ca_cert=os.getenv(f"{env_prefix}_SSL_CA"),
        )

    @classmethod
    def local_postgresql(cls) -> "DatabaseConfig":
        """本地PostgreSQL配置"""
        return cls(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="scholarforge",
            username="postgres",
            password=os.getenv("DB_PASSWORD", "postgres"),
        )

    @classmethod
    def local_mysql(cls) -> "DatabaseConfig":
        """本地MySQL配置"""
        return cls(
            db_type=DatabaseType.MYSQL,
            host="localhost",
            port=3306,
            database="scholarforge",
            username="root",
            password=os.getenv("DB_PASSWORD", ""),
            charset="utf8mb4",
        )

    @classmethod
    def aliyun_rds(cls) -> "DatabaseConfig":
        """阿里云RDS配置"""
        return cls(
            db_type=DatabaseType.POSTGRESQL,
            host=os.getenv("ALIYUN_DB_HOST", ""),
            port=int(os.getenv("ALIYUN_DB_PORT", "5432")),
            database=os.getenv("ALIYUN_DB_NAME", "scholarforge"),
            username=os.getenv("ALIYUN_DB_USER", ""),
            password=os.getenv("ALIYUN_DB_PASSWORD", ""),
            ssl_mode="require",
            ssl_ca_cert=os.getenv("ALIYUN_DB_SSL_CA"),
        )

    @classmethod
    def aws_rds(cls) -> "DatabaseConfig":
        """AWS RDS配置"""
        return cls(
            db_type=DatabaseType.POSTGRESQL,
            host=os.getenv("AWS_DB_HOST", ""),
            port=int(os.getenv("AWS_DB_PORT", "5432")),
            database=os.getenv("AWS_DB_NAME", "scholarforge"),
            username=os.getenv("AWS_DB_USER", ""),
            password=os.getenv("AWS_DB_PASSWORD", ""),
            ssl_mode="require",
        )

    @property
    def async_dsn(self) -> str:
        """生成异步数据库DSN"""
        if self.db_type == DatabaseType.POSTGRESQL:
            driver = "postgresql+asyncpg"
        elif self.db_type == DatabaseType.MYSQL:
            driver = "mysql+aiomysql"
        elif self.db_type == DatabaseType.SQLITE:
            driver = "sqlite+aiosqlite"
            return f"{driver}:///{self.database}"
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")

        return f"{driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def sync_dsn(self) -> str:
        """生成同步数据库DSN (用于Alembic迁移)"""
        if self.db_type == DatabaseType.POSTGRESQL:
            driver = "postgresql+psycopg2"
        elif self.db_type == DatabaseType.MYSQL:
            driver = "mysql+pymysql"
        elif self.db_type == DatabaseType.SQLITE:
            driver = "sqlite"
            return f"{driver}:///{self.database}"
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")

        return f"{driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_engine_options(self) -> Dict[str, Any]:
        """获取SQLAlchemy引擎配置"""
        options = {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo,
        }

        # SSL配置
        if self.ssl_mode:
            connect_args = {}
            if self.db_type == DatabaseType.POSTGRESQL:
                connect_args["ssl"] = self.ssl_mode
                if self.ssl_ca_cert:
                    connect_args["sslrootcert"] = self.ssl_ca_cert
            elif self.db_type == DatabaseType.MYSQL:
                connect_args["ssl_mode"] = self.ssl_mode
                connect_args["charset"] = self.charset

            if connect_args:
                options["connect_args"] = connect_args

        return options


def get_deployment_config(env: DeploymentEnv) -> DatabaseConfig:
    """根据部署环境获取配置"""
    config_map = {
        DeploymentEnv.LOCAL: DatabaseConfig.local_postgresql,
        DeploymentEnv.DOCKER: DatabaseConfig.local_postgresql,
        DeploymentEnv.ALIYUN: DatabaseConfig.aliyun_rds,
        DeploymentEnv.AWS: DatabaseConfig.aws_rds,
    }

    config_factory = config_map.get(env, DatabaseConfig.from_env)
    return config_factory()
