"""
Neo4j图数据库客户端
提供与Neo4j的连接和基础操作
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

try:
    from neo4j import GraphDatabase, Driver, Session, Transaction
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None
    Driver = None
    Session = None
    Transaction = None


class Neo4jClient:
    """
    Neo4j数据库客户端
    封装常用图数据库操作
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        初始化Neo4j客户端

        Args:
            uri: Neo4j连接URI (默认: bolt://localhost:7687)
            username: 用户名 (默认: neo4j)
            password: 密码 (默认: 从环境变量获取)
        """
        if not NEO4J_AVAILABLE:
            raise ImportError(
                "Neo4j driver not installed. "
                "Install with: pip install neo4j"
            )

        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = username or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password')

        self._driver: Optional[Driver] = None
        self._connected = False

    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # 验证连接
            self._driver.verify_connectivity()
            self._connected = True
            return True
        except (ServiceUnavailable, AuthError) as e:
            print(f"Neo4j connection failed: {e}")
            self._connected = False
            return False

    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._connected = False

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected

    @contextmanager
    def session(self):
        """获取数据库会话（上下文管理器）"""
        if not self._driver:
            raise RuntimeError("Database not connected")

        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def run_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行Cypher查询

        Args:
            query: Cypher查询语句
            parameters: 查询参数

        Returns:
            查询结果列表
        """
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行写操作"""
        with self.session() as session:
            result = session.execute_write(
                lambda tx: tx.run(query, parameters or {}).data()
            )
            return result

    def execute_read(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行读操作"""
        with self.session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, parameters or {}).data()
            )
            return result

    def create_constraints(self):
        """创建数据库约束和索引"""
        constraints = [
            # 唯一性约束
            "CREATE CONSTRAINT author_id IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE",

            # 索引
            "CREATE INDEX author_name IF NOT EXISTS FOR (a:Author) ON (a.name)",
            "CREATE INDEX paper_title IF NOT EXISTS FOR (p:Paper) ON (p.title)",
            "CREATE INDEX concept_name_idx IF NOT EXISTS FOR (c:Concept) ON (c.name)",
        ]

        for constraint in constraints:
            try:
                self.run_query(constraint)
            except Exception as e:
                print(f"Constraint creation warning: {e}")

    def clear_database(self):
        """清空数据库（危险操作！）"""
        query = "MATCH (n) DETACH DELETE n"
        self.execute_write(query)

    def get_statistics(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        queries = {
            'total_nodes': "MATCH (n) RETURN count(n) as count",
            'total_relationships': "MATCH ()-[r]->() RETURN count(r) as count",
            'authors': "MATCH (a:Author) RETURN count(a) as count",
            'papers': "MATCH (p:Paper) RETURN count(p) as count",
            'concepts': "MATCH (c:Concept) RETURN count(c) as count",
            'institutions': "MATCH (i:Institution) RETURN count(i) as count",
        }

        stats = {}
        for key, query in queries.items():
            try:
                result = self.run_query(query)
                stats[key] = result[0]['count'] if result else 0
            except Exception as e:
                print(f"Error getting {key}: {e}")
                stats[key] = 0

        return stats


# 全局客户端实例
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """获取Neo4j客户端单例"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client


def init_neo4j() -> bool:
    """初始化Neo4j连接"""
    client = get_neo4j_client()
    if client.connect():
        client.create_constraints()
        return True
    return False


# 测试代码
if __name__ == "__main__":
    client = Neo4jClient()
    if client.connect():
        print("✅ Neo4j connection successful")

        # 创建约束
        client.create_constraints()
        print("✅ Constraints created")

        # 获取统计
        stats = client.get_statistics()
        print(f"📊 Database statistics: {stats}")

        client.close()
    else:
        print("❌ Failed to connect to Neo4j")
