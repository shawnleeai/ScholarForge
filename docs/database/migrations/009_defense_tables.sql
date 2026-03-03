/-- 答辩准备相关表
-- Migration: 009_defense_tables

-- 答辩检查清单表
CREATE TABLE defense_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    items JSONB NOT NULL DEFAULT '[]'::jsonb,  -- 检查项数组
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(paper_id)
);

CREATE INDEX idx_defense_checklists_paper ON defense_checklists(paper_id);
CREATE INDEX idx_defense_checklists_user ON defense_checklists(user_id);

-- 答辩PPT表
CREATE TABLE defense_ppts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template VARCHAR(50) NOT NULL DEFAULT 'academic',
    outline JSONB NOT NULL DEFAULT '{}'::jsonb,  -- PPT大纲
    status VARCHAR(20) NOT NULL DEFAULT 'draft',  -- draft, generated, finalized
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_defense_ppts_paper ON defense_ppts(paper_id);
CREATE INDEX idx_defense_ppts_user ON defense_ppts(user_id);

-- 答辩问答库表
CREATE TABLE defense_qa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,  -- NULL表示通用问题
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'general',  -- general, innovation, method, result
    difficulty VARCHAR(20) NOT NULL DEFAULT 'medium',  -- easy, medium, hard
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_defense_qa_paper ON defense_qa(paper_id);
CREATE INDEX idx_defense_qa_category ON defense_qa(category);

-- 模拟答辩会话表
CREATE TABLE defense_mock_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'ongoing',  -- ongoing, completed
    total_score NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_defense_mock_sessions_paper ON defense_mock_sessions(paper_id);
CREATE INDEX idx_defense_mock_sessions_user ON defense_mock_sessions(user_id);

-- 模拟答辩回答记录表
CREATE TABLE defense_mock_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES defense_mock_sessions(id) ON DELETE CASCADE,
    question_id UUID REFERENCES defense_qa(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    feedback TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_defense_mock_answers_session ON defense_mock_answers(session_id);

-- 答辩提醒设置表
CREATE TABLE defense_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    defense_date TIMESTAMP WITH TIME ZONE,
    remind_before INTERVAL,  -- 提前提醒时间
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(paper_id)
);

-- 添加注释
COMMENT ON TABLE defense_checklists IS '答辩准备检查清单';
COMMENT ON TABLE defense_ppts IS '答辩PPT大纲';
COMMENT ON TABLE defense_qa IS '答辩问答库';
COMMENT ON TABLE defense_mock_sessions IS '模拟答辩会话';
COMMENT ON TABLE defense_mock_answers IS '模拟答辩回答记录';
COMMENT ON TABLE defense_reminders IS '答辩提醒设置';
