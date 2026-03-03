-- Migration: 003_progress_tables.sql
-- 创建进度管理相关表
-- 最后更新: 2026-03-03

-- ============== 里程碑表 ==============
CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,

    -- 里程碑信息
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- 时间安排
    planned_date DATE,
    actual_date DATE,

    -- 状态
    status VARCHAR(20) DEFAULT 'pending', -- pending/in_progress/completed/delayed/at_risk
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_milestones_paper ON milestones(paper_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON milestones(status);
CREATE INDEX IF NOT EXISTS idx_milestones_date ON milestones(planned_date);

-- ============== 任务表 ==============
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    milestone_id UUID REFERENCES milestones(id) ON DELETE SET NULL,

    -- 任务信息
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- 状态
    status VARCHAR(20) DEFAULT 'pending', -- pending/in_progress/completed/cancelled
    priority VARCHAR(20) DEFAULT 'medium', -- low/medium/high/urgent
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),

    -- 时间安排
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,

    -- 负责人
    assignee_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- 依赖关系（JSON存储依赖的任务ID列表）
    dependencies JSONB DEFAULT '[]',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_tasks_paper ON tasks(paper_id);
CREATE INDEX IF NOT EXISTS idx_tasks_milestone ON tasks(milestone_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id);

-- ============== 进度预警表 ==============
CREATE TABLE IF NOT EXISTS progress_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,

    -- 预警信息
    alert_type VARCHAR(50) NOT NULL, -- deadline_risk/progress_delay/task_delay/deadline_overdue/quality_issue
    severity VARCHAR(20) NOT NULL, -- low/medium/high/critical
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- 影响范围
    affected_items JSONB DEFAULT '[]', -- 受影响的里程碑/任务ID列表
    suggestions JSONB DEFAULT '[]', -- 建议措施

    -- 状态
    is_read BOOLEAN DEFAULT FALSE,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_note TEXT,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_progress_alerts_paper ON progress_alerts(paper_id);
CREATE INDEX IF NOT EXISTS idx_progress_alerts_severity ON progress_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_progress_alerts_read ON progress_alerts(paper_id, is_read);
CREATE INDEX IF NOT EXISTS idx_progress_alerts_created ON progress_alerts(created_at DESC);

-- ============== 进度设置表 ==============
CREATE TABLE IF NOT EXISTS progress_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL UNIQUE REFERENCES papers(id) ON DELETE CASCADE,

    -- 时间安排
    start_date DATE NOT NULL,
    target_completion_date DATE NOT NULL,
    working_days_per_week INTEGER DEFAULT 5,

    -- 提醒设置
    reminder_enabled BOOLEAN DEFAULT TRUE,
    reminder_days_before INTEGER DEFAULT 3,

    -- 自动预警
    auto_alert_enabled BOOLEAN DEFAULT TRUE,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_progress_settings_paper ON progress_settings(paper_id);

-- ============== 触发器 ==============
-- 更新时间戳
CREATE OR REPLACE FUNCTION update_progress_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_milestones_updated_at
    BEFORE UPDATE ON milestones
    FOR EACH ROW
    EXECUTE FUNCTION update_progress_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_progress_updated_at_column();

-- ============== 备注 ==============
COMMENT ON TABLE milestones IS '里程碑表，存储论文写作的关键节点';
COMMENT ON TABLE tasks IS '任务表，存储论文写作的详细任务';
COMMENT ON TABLE progress_alerts IS '进度预警表，存储自动检测的延期风险等预警信息';
COMMENT ON TABLE progress_settings IS '进度设置表，存储用户对进度管理的个性化设置';
