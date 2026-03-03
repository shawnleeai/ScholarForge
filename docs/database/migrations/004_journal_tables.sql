-- Migration: 004_journal_tables.sql
-- 创建期刊匹配服务相关表
-- 最后更新: 2026-03-03

-- ============== 期刊匹配记录表 ==============
CREATE TABLE IF NOT EXISTS journal_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    journal_id UUID REFERENCES journals(id) ON DELETE CASCADE,

    -- 匹配信息
    match_score DECIMAL(5,2),
    match_reasons JSONB DEFAULT '[]',
    estimated_acceptance_rate DECIMAL(5,2),

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_journal_matches_user ON journal_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_journal_matches_paper ON journal_matches(paper_id);
CREATE INDEX IF NOT EXISTS idx_journal_matches_journal ON journal_matches(journal_id);
CREATE INDEX IF NOT EXISTS idx_journal_matches_score ON journal_matches(match_score DESC);

-- ============== 投稿记录表 ==============
CREATE TABLE IF NOT EXISTS submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    journal_id UUID REFERENCES journals(id) ON DELETE SET NULL,

    -- 投稿信息
    manuscript_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'draft', -- draft/submitted/under_review/revision_required/accepted/rejected/withdrawn

    -- 时间节点
    submitted_at TIMESTAMP WITH TIME ZONE,
    first_decision_at TIMESTAMP WITH TIME ZONE,
    revision_submitted_at TIMESTAMP WITH TIME ZONE,
    final_decision_at TIMESTAMP WITH TIME ZONE,

    -- 决策信息
    decision VARCHAR(50), -- accept/minor_revision/major_revision/reject
    decision_letter TEXT,

    -- 审稿人信息（JSON存储）
    reviewers JSONB DEFAULT '[]',

    -- 备注
    notes TEXT,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_submissions_paper ON submissions(paper_id);
CREATE INDEX IF NOT EXISTS idx_submissions_journal ON submissions(journal_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_submitted ON submissions(submitted_at DESC);

-- ============== 期刊数据初始填充 ==============
-- 如果journals表为空，插入一些示例数据
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM journals LIMIT 1) THEN
        INSERT INTO journals (name, issn, subject_areas, keywords, impact_factor, acceptance_rate, scope, language, review_cycle_days) VALUES
        ('管理世界', '1002-5502', ARRAY['管理学', '经济学'], ARRAY['管理', '战略', '创新', '组织'], 5.2, 0.15, '管理学领域顶级期刊', 'zh', 60),
        ('系统工程理论与实践', '1000-6788', ARRAY['系统工程', '管理科学'], ARRAY['系统', '优化', '决策', '工程管理'], 3.5, 0.20, '系统工程领域核心期刊', 'zh', 45),
        ('科研管理', '1000-2995', ARRAY['管理学', '科技管理'], ARRAY['研发', '创新', '科技政策', '知识管理'], 2.8, 0.25, '科研管理领域专业期刊', 'zh', 50),
        ('管理科学学报', '1007-9807', ARRAY['管理科学', '运筹学'], ARRAY['管理科学', '运筹学', '决策', '优化'], 2.5, 0.22, '管理科学领域核心期刊', 'zh', 55),
        ('中国管理科学', '1003-207X', ARRAY['管理科学', '管理学'], ARRAY['管理', '决策', '系统', '优化'], 2.2, 0.28, '中国管理科学领域重要期刊', 'zh', 50),
        ('项目管理技术', '1672-4318', ARRAY['项目管理'], ARRAY['项目', '管理', '进度', '成本', '质量'], 1.2, 0.40, '项目管理专业期刊', 'zh', 30),
        ('计算机学报', '0254-4164', ARRAY['计算机科学'], ARRAY['计算机', '算法', '软件', '系统'], 3.0, 0.18, '计算机领域顶级中文期刊', 'zh', 60);
    END IF;
END $$;

-- ============== 备注 ==============
COMMENT ON TABLE journal_matches IS '期刊匹配历史记录表';
COMMENT ON TABLE submissions IS '投稿记录表，跟踪论文投稿状态';
