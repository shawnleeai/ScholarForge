-- Migration: 007_plagiarism_tables.sql
-- 创建查重检测相关表
-- 最后更新: 2026-03-03

-- ============== 查重任务表 ==============
CREATE TABLE IF NOT EXISTS plagiarism_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,

    -- 任务信息
    task_name VARCHAR(200),
    file_path TEXT,
    file_hash VARCHAR(64), -- 文件哈希用于检测重复提交

    -- 状态
    status VARCHAR(20) DEFAULT 'pending', -- pending/processing/completed/failed/cancelled

    -- 查重引擎
    engine VARCHAR(50) DEFAULT 'local', -- local/turnitin/paperpass/cnki

    -- 相似度统计
    overall_similarity DECIMAL(5,2), -- 总体相似度 0-100
    internet_similarity DECIMAL(5,2),
    publications_similarity DECIMAL(5,2),
    student_papers_similarity DECIMAL(5,2),

    -- 详细结果（JSONB存储）
    matches JSONB DEFAULT '[]', -- 相似片段列表
    sources JSONB DEFAULT '[]', -- 来源列表

    -- 报告
    report_url TEXT,
    report_path TEXT,

    -- 处理时间
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- 错误信息
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_plagiarism_user ON plagiarism_checks(user_id);
CREATE INDEX IF NOT EXISTS idx_plagiarism_paper ON plagiarism_checks(paper_id);
CREATE INDEX IF NOT EXISTS idx_plagiarism_status ON plagiarism_checks(status);
CREATE INDEX IF NOT EXISTS idx_plagiarism_submitted ON plagiarism_checks(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_plagiarism_hash ON plagiarism_checks(file_hash);

-- ============== 查重历史记录表（归档） ==============
CREATE TABLE IF NOT EXISTS plagiarism_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_id UUID REFERENCES plagiarism_checks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,

    version INTEGER DEFAULT 1, -- 第几次查重

    similarity DECIMAL(5,2),
    report_url TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_plagiarism_history_paper ON plagiarism_history(paper_id);
CREATE INDEX IF NOT EXISTS idx_plagiarism_history_version ON plagiarism_history(paper_id, version);

-- ============== 查重白名单表 ==============
CREATE TABLE IF NOT EXISTS plagiarism_whitelist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,

    -- 白名单内容
    content TEXT NOT NULL, -- 文本片段
    content_hash VARCHAR(64), -- 哈希值

    -- 原因
    reason TEXT,
    source VARCHAR(200), -- 来源说明（如"自己已发表论文"）

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_plagiarism_whitelist_user ON plagiarism_whitelist(user_id);
CREATE INDEX IF NOT EXISTS idx_plagiarism_whitelist_paper ON plagiarism_whitelist(paper_id);
CREATE INDEX IF NOT EXISTS idx_plagiarism_whitelist_hash ON plagiarism_whitelist(content_hash);

-- ============== 查重设置表 ==============
CREATE TABLE IF NOT EXISTS plagiarism_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- 默认引擎
    default_engine VARCHAR(50) DEFAULT 'local',

    -- 排除设置
    exclude_bibliography BOOLEAN DEFAULT TRUE,
    exclude_quotes BOOLEAN DEFAULT FALSE,
    exclude_small_sources BOOLEAN DEFAULT TRUE,
    small_source_threshold INTEGER DEFAULT 8, -- 小于多少词的来源排除

    -- 灵敏度
    sensitivity VARCHAR(20) DEFAULT 'medium', -- low/medium/high

    -- 通知设置
    notify_on_complete BOOLEAN DEFAULT TRUE,
    notify_threshold INTEGER DEFAULT 30, -- 超过此相似度发送警告

    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============== 备注 ==============
COMMENT ON TABLE plagiarism_checks IS '查重检测任务表';
COMMENT ON TABLE plagiarism_history IS '查重历史记录表';
COMMENT ON TABLE plagiarism_whitelist IS '查重白名单表（排除不计入相似度的内容）';
COMMENT ON TABLE plagiarism_settings IS '用户查重设置表';
