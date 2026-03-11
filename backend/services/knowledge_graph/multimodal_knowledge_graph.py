"""
Multimodal Knowledge Graph Service
多模态知识图谱服务 - 支持图像、文本的多模态知识抽取与可视化
"""

import json
import base64
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from .neo4j_client import get_neo4j_client
from ..ai.stepfun_client import get_stepfun_client


class EntityType(str, Enum):
    """实体类型"""
    PAPER = "Paper"
    AUTHOR = "Author"
    CONCEPT = "Concept"
    INSTITUTION = "Institution"
    FIGURE = "Figure"  # 新增：图表实体
    DATASET = "Dataset"  # 新增：数据集实体
    METHOD = "Method"  # 新增：方法实体


class RelationType(str, Enum):
    """关系类型"""
    CITES = "CITES"
    AUTHORED = "AUTHORED"
    CO_AUTHOR = "CO_AUTHOR"
    BELONGS_TO = "BELONGS_TO"
    AFFILIATED_WITH = "AFFILIATED_WITH"
    CONTAINS = "CONTAINS"  # 新增：论文包含图表
    USES_METHOD = "USES_METHOD"  # 新增：使用某方法
    USES_DATASET = "USES_DATASET"  # 新增：使用某数据集
    SIMILAR_TO = "SIMILAR_TO"  # 新增：相似关系


@dataclass
class FigureEntity:
    """图表实体"""
    id: str
    paper_id: str
    figure_number: int
    caption: str
    description: str
    type: str  # "figure" | "table"
    key_data: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class MethodEntity:
    """方法实体"""
    id: str
    name: str
    description: str
    category: str  # "model" | "algorithm" | "framework"
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]


@dataclass
class DatasetEntity:
    """数据集实体"""
    id: str
    name: str
    description: str
    domain: str
    size: str
    format: str
    source_url: Optional[str] = None


class MultimodalKnowledgeGraph:
    """多模态知识图谱服务"""

    def __init__(self):
        self.neo4j = get_neo4j_client()
        self.stepfun = get_stepfun_client()

    # ==================== 多模态实体抽取 ====================

    async def extract_from_figure(
        self,
        figure_image: bytes,
        caption: str,
        paper_context: str
    ) -> Dict[str, Any]:
        """
        从图表图片中抽取知识

        Args:
            figure_image: 图表图片数据
            caption: 图表标题
            paper_context: 论文上下文
        """
        # 使用step-1o多模态理解
        prompt = f"""请分析这张学术论文中的图表，提取以下信息：

图表标题: {caption}

请提取并以JSON格式返回：
{{
    "figure_type": "图表类型(line_chart/bar_chart/scatter_plot/table等)",
    "main_finding": "图表展示的主要发现",
    "key_data_points": ["关键数据点1", "关键数据点2"],
    "x_axis": "X轴含义",
    "y_axis": "Y轴含义",
    "comparison_groups": ["对比组1", "对比组2"],
    "statistical_info": {{
        "sample_size": "样本量",
        "significance": "显著性信息"
    }},
    "conclusion": "从图表得出的结论"
}}"""

        response = await self.stepfun.vision_analysis(
            image_data=figure_image,
            prompt=prompt,
            model="step-1o",
            detail="high"
        )

        content = response['choices'][0]['message']['content']

        # 解析JSON
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            figure_analysis = json.loads(json_str.strip())
        except:
            figure_analysis = {"raw_analysis": content}

        return {
            "caption": caption,
            "analysis": figure_analysis,
            "extracted_at": datetime.utcnow().isoformat()
        }

    async def extract_methods_from_text(
        self,
        text: str,
        paper_id: str
    ) -> List[MethodEntity]:
        """从文本中抽取方法实体"""

        prompt = f"""请从以下论文方法章节中抽取所有使用的方法、模型或算法。

论文内容:
{text[:15000]}

请以JSON数组格式返回：
[
    {{
        "name": "方法名称",
        "description": "方法描述",
        "category": "model/algorithm/framework",
        "parameters": {{"参数名": "参数值"}},
        "performance_metrics": {{"指标名": 数值}}
    }}
]"""

        response = await self.stepfun.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="step-1-128k"
        )

        content = response['choices'][0]['message']['content']

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            methods_data = json.loads(json_str.strip())

            methods = []
            for i, method_data in enumerate(methods_data):
                method = MethodEntity(
                    id=f"{paper_id}_method_{i}",
                    name=method_data.get("name", "Unknown"),
                    description=method_data.get("description", ""),
                    category=method_data.get("category", "method"),
                    parameters=method_data.get("parameters", {}),
                    performance_metrics=method_data.get("performance_metrics", {})
                )
                methods.append(method)

            return methods
        except:
            return []

    async def extract_datasets_from_text(
        self,
        text: str,
        paper_id: str
    ) -> List[DatasetEntity]:
        """从文本中抽取数据集实体"""

        prompt = f"""请从以下论文中抽取所有使用的数据集。

论文内容:
{text[:15000]}

请以JSON数组格式返回：
[
    {{
        "name": "数据集名称",
        "description": "数据集描述",
        "domain": "领域",
        "size": "数据规模",
        "format": "数据格式"
    }}
]"""

        response = await self.stepfun.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="step-1-128k"
        )

        content = response['choices'][0]['message']['content']

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            else:
                json_str = content

            datasets_data = json.loads(json_str.strip())

            datasets = []
            for i, ds_data in enumerate(datasets_data):
                dataset = DatasetEntity(
                    id=f"{paper_id}_dataset_{i}",
                    name=ds_data.get("name", "Unknown"),
                    description=ds_data.get("description", ""),
                    domain=ds_data.get("domain", ""),
                    size=ds_data.get("size", ""),
                    format=ds_data.get("format", "")
                )
                datasets.append(dataset)

            return datasets
        except:
            return []

    # ==================== 知识图谱构建 ====================

    async def build_multimodal_graph(
        self,
        paper_data: Dict[str, Any],
        figures: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        构建多模态知识图谱

        Args:
            paper_data: 论文数据
            figures: 图表列表 [{"image": bytes, "caption": str, "number": int}]
        """
        results = {
            "paper_id": paper_data.get("id"),
            "entities_created": 0,
            "relationships_created": 0,
            "figures_analyzed": 0,
            "methods_extracted": 0,
            "datasets_extracted": 0
        }

        # 1. 创建基础论文节点
        self._create_paper_node(paper_data)

        # 2. 分析图表
        if figures:
            for figure in figures:
                try:
                    figure_analysis = await self.extract_from_figure(
                        figure_image=figure["image"],
                        caption=figure.get("caption", ""),
                        paper_context=paper_data.get("abstract", "")
                    )

                    # 创建图表实体
                    figure_entity = FigureEntity(
                        id=f"{paper_data['id']}_fig_{figure['number']}",
                        paper_id=paper_data["id"],
                        figure_number=figure["number"],
                        caption=figure.get("caption", ""),
                        description=figure_analysis["analysis"].get("main_finding", ""),
                        type=figure_analysis["analysis"].get("figure_type", "figure"),
                        key_data=figure_analysis["analysis"].get("key_data_points", [])
                    )

                    self._create_figure_node(figure_entity)
                    self._create_contains_rel(paper_data["id"], figure_entity.id)
                    results["figures_analyzed"] += 1

                except Exception as e:
                    print(f"Error analyzing figure {figure.get('number')}: {e}")

        # 3. 抽取方法
        methods = await self.extract_methods_from_text(
            paper_data.get("content", paper_data.get("abstract", "")),
            paper_data["id"]
        )

        for method in methods:
            self._create_method_node(method)
            self._create_uses_method_rel(paper_data["id"], method.id)
            results["methods_extracted"] += 1

        # 4. 抽取数据集
        datasets = await self.extract_datasets_from_text(
            paper_data.get("content", paper_data.get("abstract", "")),
            paper_data["id"]
        )

        for dataset in datasets:
            self._create_dataset_node(dataset)
            self._create_uses_dataset_rel(paper_data["id"], dataset.id)
            results["datasets_extracted"] += 1

        results["entities_created"] = (
            results["figures_analyzed"] +
            results["methods_extracted"] +
            results["datasets_extracted"]
        )

        return results

    # ==================== 数据库操作 ====================

    def _create_paper_node(self, paper_data: Dict[str, Any]):
        """创建论文节点"""
        query = """
        MERGE (p:Paper {id: $id})
        ON CREATE SET
            p.title = $title,
            p.abstract = $abstract,
            p.year = $year,
            p.venue = $venue,
            p.doi = $doi,
            p.created_at = datetime()
        ON MATCH SET
            p.title = $title,
            p.abstract = $abstract,
            p.updated_at = datetime()
        """
        self.neo4j.execute_write(query, {
            'id': paper_data['id'],
            'title': paper_data.get('title', ''),
            'abstract': paper_data.get('abstract', ''),
            'year': paper_data.get('year'),
            'venue': paper_data.get('venue', ''),
            'doi': paper_data.get('doi', '')
        })

    def _create_figure_node(self, figure: FigureEntity):
        """创建图表节点"""
        query = """
        MERGE (f:Figure {id: $id})
        ON CREATE SET
            f.paper_id = $paper_id,
            f.figure_number = $figure_number,
            f.caption = $caption,
            f.description = $description,
            f.type = $type,
            f.key_data = $key_data,
            f.created_at = datetime()
        """
        self.neo4j.execute_write(query, {
            'id': figure.id,
            'paper_id': figure.paper_id,
            'figure_number': figure.figure_number,
            'caption': figure.caption,
            'description': figure.description,
            'type': figure.type,
            'key_data': json.dumps(figure.key_data)
        })

    def _create_method_node(self, method: MethodEntity):
        """创建方法节点"""
        query = """
        MERGE (m:Method {id: $id})
        ON CREATE SET
            m.name = $name,
            m.description = $description,
            m.category = $category,
            m.parameters = $parameters,
            m.performance_metrics = $performance_metrics,
            m.created_at = datetime()
        """
        self.neo4j.execute_write(query, {
            'id': method.id,
            'name': method.name,
            'description': method.description,
            'category': method.category,
            'parameters': json.dumps(method.parameters),
            'performance_metrics': json.dumps(method.performance_metrics)
        })

    def _create_dataset_node(self, dataset: DatasetEntity):
        """创建数据集节点"""
        query = """
        MERGE (d:Dataset {id: $id})
        ON CREATE SET
            d.name = $name,
            d.description = $description,
            d.domain = $domain,
            d.size = $size,
            d.format = $format,
            d.created_at = datetime()
        """
        self.neo4j.execute_write(query, {
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'domain': dataset.domain,
            'size': dataset.size,
            'format': dataset.format
        })

    def _create_contains_rel(self, paper_id: str, figure_id: str):
        """创建包含关系"""
        query = """
        MATCH (p:Paper {id: $paper_id})
        MATCH (f:Figure {id: $figure_id})
        MERGE (p)-[r:CONTAINS]->(f)
        ON CREATE SET r.created_at = datetime()
        """
        self.neo4j.execute_write(query, {
            'paper_id': paper_id,
            'figure_id': figure_id
        })

    def _create_uses_method_rel(self, paper_id: str, method_id: str):
        """创建使用方法关系"""
        query = """
        MATCH (p:Paper {id: $paper_id})
        MATCH (m:Method {id: $method_id})
        MERGE (p)-[r:USES_METHOD]->(m)
        ON CREATE SET r.created_at = datetime()
        """
        self.neo4j.execute_write(query, {
            'paper_id': paper_id,
            'method_id': method_id
        })

    def _create_uses_dataset_rel(self, paper_id: str, dataset_id: str):
        """创建使用数据集关系"""
        query = """
        MATCH (p:Paper {id: $paper_id})
        MATCH (d:Dataset {id: $dataset_id})
        MERGE (p)-[r:USES_DATASET]->(d)
        ON CREATE SET r.created_at = datetime()
        """
        self.neo4j.execute_write(query, {
            'paper_id': paper_id,
            'dataset_id': dataset_id
        })

    # ==================== 查询与分析 ====================

    def find_similar_methods(self, method_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """查找相似方法"""
        query = """
        MATCH (m1:Method {name: $method_name})
        MATCH (m2:Method)
        WHERE m1 <> m2
        AND (
            m2.name CONTAINS $method_name OR
            m1.category = m2.category
        )
        RETURN m2.name as name, m2.description as description,
               m2.category as category, m2.performance_metrics as metrics
        LIMIT $limit
        """
        return self.neo4j.run_query(query, {
            'method_name': method_name,
            'limit': limit
        })

    def get_method_evolution(self, concept: str) -> List[Dict[str, Any]]:
        """获取方法演进路径"""
        query = """
        MATCH (p:Paper)-[r:USES_METHOD]->(m:Method)
        WHERE m.name CONTAINS $concept OR m.description CONTAINS $concept
        RETURN p.year as year, p.title as title, m.name as method,
               m.performance_metrics as metrics
        ORDER BY p.year ASC
        """
        return self.neo4j.run_query(query, {'concept': concept})

    def get_dataset_usage_network(self, dataset_name: str) -> Dict[str, Any]:
        """获取数据集使用网络"""
        query = """
        MATCH (d:Dataset {name: $dataset_name})
        MATCH (p:Paper)-[:USES_DATASET]->(d)
        OPTIONAL MATCH (p)-[:USES_METHOD]->(m:Method)
        RETURN d.name as dataset,
               collect(DISTINCT {paper: p.title, year: p.year, method: m.name}) as usages
        """
        result = self.neo4j.run_query(query, {'dataset_name': dataset_name})
        return result[0] if result else {}

    def search_by_figure_content(self, description: str, limit: int = 10) -> List[Dict[str, Any]]:
        """根据图表内容搜索论文"""
        query = """
        MATCH (f:Figure)
        WHERE f.description CONTAINS $description
           OR f.caption CONTAINS $description
        MATCH (p:Paper)-[:CONTAINS]->(f)
        RETURN p.title as title, p.year as year,
               f.caption as caption, f.description as description
        LIMIT $limit
        """
        return self.neo4j.run_query(query, {
            'description': description,
            'limit': limit
        })


# 单例
_multimodal_kg: Optional[MultimodalKnowledgeGraph] = None


def get_multimodal_kg() -> MultimodalKnowledgeGraph:
    """获取多模态知识图谱服务单例"""
    global _multimodal_kg
    if _multimodal_kg is None:
        _multimodal_kg = MultimodalKnowledgeGraph()
    return _multimodal_kg
