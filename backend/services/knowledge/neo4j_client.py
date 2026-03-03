"""
Neo4j 图数据库客户端
Knowledge Graph Neo4j Client
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from neo4j import AsyncGraphDatabase, AsyncDriver


@dataclass
class Neo4jNode:
    """Neo4j 节点"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any]


@dataclass
class Neo4jEdge:
    """Neo4j 关系"""
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any]


class Neo4jClient:
    """Neo4j 客户端"""

    def __init__(
        self,
        uri: str = None,
        username: str = None,
        password: str = None
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self._driver: Optional[AsyncDriver] = None

    async def connect(self):
        """连接到 Neo4j"""
        self._driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )

    async def close(self):
        """关闭连接"""
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def verify_connectivity(self) -> bool:
        """验证连接是否可用"""
        try:
            if not self._driver:
                await self.connect()
            await self._driver.verify_connectivity()
            return True
        except Exception as e:
            print(f"Neo4j连接失败: {e}")
            return False

    async def create_node(
        self,
        node_id: str,
        label: str,
        node_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """创建节点"""
        if not self._driver:
            await self.connect()

        properties = properties or {}
        properties["id"] = node_id
        properties["type"] = node_type
        properties["label"] = label

        query = f"""
        MERGE (n:Node {{id: $id}})
        SET n.label = $label, n.type = $type
        SET n += $properties
        RETURN n
        """

        try:
            async with self._driver.session() as session:
                await session.run(query, {
                    "id": node_id,
                    "label": label,
                    "type": node_type,
                    "properties": {k: v for k, v in properties.items() if k not in ["id", "label", "type"]}
                })
            return True
        except Exception as e:
            print(f"创建节点失败: {e}")
            return False

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """创建关系"""
        if not self._driver:
            await self.connect()

        properties = properties or {}

        query = f"""
        MATCH (a:Node {{id: $source_id}})
        MATCH (b:Node {{id: $target_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties
        RETURN r
        """

        try:
            async with self._driver.session() as session:
                await session.run(query, {
                    "source_id": source_id,
                    "target_id": target_id,
                    "properties": properties
                })
            return True
        except Exception as e:
            print(f"创建关系失败: {e}")
            return False

    async def get_node(self, node_id: str) -> Optional[Neo4jNode]:
        """获取节点"""
        if not self._driver:
            await self.connect()

        query = """
        MATCH (n:Node {id: $id})
        RETURN n
        """

        try:
            async with self._driver.session() as session:
                result = await session.run(query, {"id": node_id})
                record = await result.single()
                if record:
                    node = record["n"]
                    return Neo4jNode(
                        id=node["id"],
                        label=node.get("label", ""),
                        type=node.get("type", "concept"),
                        properties=dict(node)
                    )
                return None
        except Exception as e:
            print(f"获取节点失败: {e}")
            return None

    async def get_neighbors(
        self,
        node_id: str,
        depth: int = 1
    ) -> Tuple[Optional[Neo4jNode], List[Dict[str, Any]]]:
        """获取节点的邻居"""
        if not self._driver:
            await self.connect()

        # 获取中心节点
        center = await self.get_node(node_id)
        if not center:
            return None, []

        query = """
        MATCH path = (center:Node {id: $id})-[:RELATED_TO|PART_OF|USES|CITES*1..$depth]-(neighbor:Node)
        WHERE neighbor.id <> $id
        RETURN neighbor, relationships(path)[0] as rel, length(path) as distance
        LIMIT 50
        """

        try:
            async with self._driver.session() as session:
                result = await session.run(query, {
                    "id": node_id,
                    "depth": depth
                })

                neighbors = []
                async for record in result:
                    neighbor_node = record["neighbor"]
                    rel = record["rel"]
                    distance = record["distance"]

                    neighbors.append({
                        "node": Neo4jNode(
                            id=neighbor_node["id"],
                            label=neighbor_node.get("label", ""),
                            type=neighbor_node.get("type", "concept"),
                            properties=dict(neighbor_node)
                        ),
                        "relation": rel.type if hasattr(rel, "type") else "RELATED_TO",
                        "distance": distance
                    })

                return center, neighbors
        except Exception as e:
            print(f"获取邻居失败: {e}")
            return center, []

    async def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 4
    ) -> Optional[List[Dict[str, Any]]]:
        """查找两个节点之间的路径"""
        if not self._driver:
            await self.connect()

        query = """
        MATCH path = shortestPath(
            (start:Node {id: $start_id})-[:RELATED_TO|PART_OF|USES|CITES|DERIVED_FROM*1..$max_depth]-(end:Node {id: $end_id})
        )
        RETURN path
        """

        try:
            async with self._driver.session() as session:
                result = await session.run(query, {
                    "start_id": start_id,
                    "end_id": end_id,
                    "max_depth": max_depth
                })

                record = await result.single()
                if record:
                    path = record["path"]
                    nodes = []
                    edges = []

                    for node in path.nodes:
                        nodes.append({
                            "id": node["id"],
                            "label": node.get("label", ""),
                            "type": node.get("type", "concept")
                        })

                    for rel in path.relationships:
                        edges.append({
                            "source": rel.start_node["id"],
                            "target": rel.end_node["id"],
                            "type": rel.type
                        })

                    return {"nodes": nodes, "edges": edges, "length": len(edges)}

                return None
        except Exception as e:
            print(f"查找路径失败: {e}")
            return None

    async def get_subgraph(
        self,
        node_ids: List[str],
        depth: int = 2
    ) -> Dict[str, Any]:
        """获取子图"""
        if not self._driver:
            await self.connect()

        query = """
        MATCH (n:Node)
        WHERE n.id IN $node_ids
        OPTIONAL MATCH path = (n)-[:RELATED_TO|PART_OF|USES|CITES*1..$depth]-(m:Node)
        WHERE m.id <> n.id
        RETURN n, collect(DISTINCT m) as neighbors, collect(DISTINCT relationships(path)[0]) as rels
        """

        try:
            async with self._driver.session() as session:
                result = await session.run(query, {
                    "node_ids": node_ids,
                    "depth": depth
                })

                nodes = {}
                edges = []

                async for record in result:
                    center = record["n"]
                    neighbors = record["neighbors"]
                    rels = record["rels"]

                    nodes[center["id"]] = {
                        "id": center["id"],
                        "label": center.get("label", ""),
                        "type": center.get("type", "concept"),
                        "properties": dict(center)
                    }

                    for neighbor in neighbors:
                        nodes[neighbor["id"]] = {
                            "id": neighbor["id"],
                            "label": neighbor.get("label", ""),
                            "type": neighbor.get("type", "concept"),
                            "properties": dict(neighbor)
                        }

                    for rel in rels:
                        if rel:
                            edges.append({
                                "source": rel.start_node["id"],
                                "target": rel.end_node["id"],
                                "type": rel.type
                            })

                return {
                    "nodes": list(nodes.values()),
                    "edges": edges
                }
        except Exception as e:
            print(f"获取子图失败: {e}")
            return {"nodes": [], "edges": []}

    async def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        if not self._driver:
            await self.connect()

        try:
            async with self._driver.session() as session:
                # 节点统计
                node_query = """
                MATCH (n:Node)
                RETURN count(n) as total, n.type as type
                """
                node_result = await session.run(node_query)

                node_types = {}
                total_nodes = 0
                async for record in node_result:
                    count = record["total"]
                    node_type = record["type"] or "unknown"
                    node_types[node_type] = count
                    total_nodes += count

                # 关系统计
                rel_query = """
                MATCH ()-[r]->()
                RETURN count(r) as total
                """
                rel_result = await session.run(rel_query)
                rel_record = await rel_result.single()
                total_edges = rel_record["total"] if rel_record else 0

                return {
                    "total_nodes": total_nodes,
                    "total_edges": total_edges,
                    "node_types": node_types,
                }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {"total_nodes": 0, "total_edges": 0, "node_types": {}}

    async def clear_graph(self) -> bool:
        """清空图谱（慎用）"""
        if not self._driver:
            await self.connect()

        try:
            async with self._driver.session() as session:
                await session.run("MATCH (n) DETACH DELETE n")
            return True
        except Exception as e:
            print(f"清空图谱失败: {e}")
            return False


# 全局 Neo4j 客户端实例
neo4j_client = Neo4jClient()
