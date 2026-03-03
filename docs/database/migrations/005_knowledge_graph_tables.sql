-- Migration: 005_knowledge_graph_tables.sql
-- 创建知识图谱服务相关表
-- 最后更新: 2026-03-03

-- ============== 知识图谱表 ==============
CREATE TABLE IF NOT EXISTS knowledge_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,

    -- 图谱信息
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- 统计信息
    node_count INTEGER DEFAULT 0,
    edge_count INTEGER DEFAULT 0,

    -- Neo4j 图谱ID
    neo4j_graph_id VARCHAR(100),

    -- 构建设置
    settings JSONB DEFAULT '{}',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_knowledge_graphs_user ON knowledge_graphs(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_graphs_paper ON knowledge_graphs(paper_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_graphs_created ON knowledge_graphs(created_at DESC);

-- ============== 概念实体表 ==============
CREATE TABLE IF NOT EXISTS concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 概念信息
    name VARCHAR(200) NOT NULL UNIQUE,
    concept_type VARCHAR(50) DEFAULT 'concept', -- concept/method/theory/person/paper/institution/keyword/domain
    description TEXT,

    -- 关键词和属性
    keywords TEXT[],
    frequency INTEGER DEFAULT 1,
    importance DECIMAL(3,2) DEFAULT 0.5,
    properties JSONB DEFAULT '{}',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_concepts_type ON concepts(concept_type);
CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name);
CREATE INDEX IF NOT EXISTS idx_concepts_keywords ON concepts USING GIN(keywords);

-- ============== 概念关系表 ==============
CREATE TABLE IF NOT EXISTS concept_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    target_concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,

    -- 关系信息
    relation_type VARCHAR(50) NOT NULL, -- related_to/part_of/derived_from/applies/cites/authored_by/belongs_to/uses
    weight DECIMAL(3,2) DEFAULT 1.0,
    evidence JSONB DEFAULT '[]',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(source_concept_id, target_concept_id, relation_type)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_concept_relations_source ON concept_relations(source_concept_id);
CREATE INDEX IF NOT EXISTS idx_concept_relations_target ON concept_relations(target_concept_id);
CREATE INDEX IF NOT EXISTS idx_concept_relations_type ON concept_relations(relation_type);

-- ============== 图谱-概念关联表 ==============
CREATE TABLE IF NOT EXISTS graph_concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES knowledge_graphs(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,

    -- 概念在图谱中的属性
    x_position DECIMAL(10,2),
    y_position DECIMAL(10,2),
    node_size DECIMAL(5,2) DEFAULT 1.0,
    color VARCHAR(20),

    UNIQUE(graph_id, concept_id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_graph_concepts_graph ON graph_concepts(graph_id);
CREATE INDEX IF NOT EXISTS idx_graph_concepts_concept ON graph_concepts(concept_id);

-- ============== 触发器 ==============
-- 更新时间戳
CREATE TRIGGER update_concepts_updated_at
    BEFORE UPDATE ON concepts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============== 备注 ==============
COMMENT ON TABLE knowledge_graphs IS '知识图谱表，存储图谱元数据';
COMMENT ON TABLE concepts IS '概念实体表，存储知识图谱中的概念节点';
COMMENT ON TABLE concept_relations IS '概念关系表，存储概念之间的关系';
COMMENT ON TABLE graph_concepts IS '图谱-概念关联表，存储概念在特定图谱中的布局信息';
