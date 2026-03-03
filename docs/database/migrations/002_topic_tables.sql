-- Migration: 002_topic_tables.sql
-- 创建选题助手相关表
-- 最后更新: 2026-03-03

-- ============== 选题建议表 ==============
CREATE TABLE IF NOT EXISTS topic_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 选题基本信息
    title VARCHAR(500) NOT NULL,
    description TEXT,
    field VARCHAR(100),
    keywords TEXT[],

    -- 可行性评估
    feasibility_score INTEGER DEFAULT 70,
    feasibility_level VARCHAR(20) DEFAULT 'medium', -- high/medium/low/risky

    -- 研究空白（JSON存储）
    research_gaps JSONB DEFAULT '[]',

    -- 资源需求
    required_methods TEXT[],
    required_data TEXT[],
    required_tools TEXT[],

    -- 时间估算
    estimated_duration_months INTEGER DEFAULT 6,

    -- 风险与应对
    risks TEXT[],
    mitigation_strategies TEXT[],

    -- 参考
    related_papers TEXT[],
    recent_trends TEXT[],

    -- 用户交互
    is_favorite BOOLEAN DEFAULT FALSE,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_topic_suggestions_user ON topic_suggestions(user_id);
CREATE INDEX IF NOT EXISTS idx_topic_suggestions_field ON topic_suggestions(field);
CREATE INDEX IF NOT EXISTS idx_topic_suggestions_favorite ON topic_suggestions(user_id, is_favorite);
CREATE INDEX IF NOT EXISTS idx_topic_suggestions_keywords ON topic_suggestions USING GIN(keywords);

-- ============== 开题报告表 ==============
CREATE TABLE IF NOT EXISTS proposal_outlines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topic_suggestions(id) ON DELETE SET NULL,

    -- 报告内容
    title VARCHAR(500) NOT NULL,
    background TEXT,
    objectives TEXT,

    -- 研究问题（JSON存储）
    research_questions JSONB DEFAULT '[]',

    -- 研究方法（JSON存储）
    research_methods JSONB DEFAULT '[]',

    -- 时间规划（JSON存储）
    timeline JSONB DEFAULT '[]',

    -- 预期成果
    expected_outcomes TEXT[],
    innovation_points TEXT[],
    references TEXT[],

    -- 元信息
    total_words INTEGER DEFAULT 0,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_proposal_outlines_user ON proposal_outlines(user_id);
CREATE INDEX IF NOT EXISTS idx_proposal_outlines_topic ON proposal_outlines(topic_id);
CREATE INDEX IF NOT EXISTS idx_proposal_outlines_generated ON proposal_outlines(generated_at DESC);

-- ============== 触发器：自动更新 updated_at ==============
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_topic_suggestions_updated_at
    BEFORE UPDATE ON topic_suggestions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============== 备注 ==============
COMMENT ON TABLE topic_suggestions IS '选题建议表，存储AI生成的选题建议';
COMMENT ON TABLE proposal_outlines IS '开题报告表，存储生成的开题报告大纲';
