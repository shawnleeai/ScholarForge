-- Migration: 008_format_tables.sql
-- 创建格式排版相关表
-- 最后更新: 2026-03-03

-- ============== 格式模板表 ==============
CREATE TABLE IF NOT EXISTS format_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 模板基本信息
    name VARCHAR(200) NOT NULL,
    description TEXT,
    institution VARCHAR(200), -- 所属机构（学校/期刊）
    template_type VARCHAR(50) NOT NULL, -- thesis/journal/report/presentation
    is_public BOOLEAN DEFAULT FALSE,

    -- 格式规范（JSONB存储）
    format_config JSONB NOT NULL DEFAULT '{}',

    -- 文件路径
    template_file TEXT, -- Word/LaTeX模板文件路径
    preview_image TEXT, -- 预览图

    -- 创建者
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- 使用统计
    usage_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_format_templates_type ON format_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_format_templates_public ON format_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_format_templates_institution ON format_templates(institution);

-- ============== 论文格式任务表 ==============
CREATE TABLE IF NOT EXISTS format_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    template_id UUID REFERENCES format_templates(id) ON DELETE SET NULL,

    -- 任务信息
    task_name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'pending', -- pending/processing/completed/failed

    -- 输入输出
    source_content JSONB, -- 原始内容（各章节）
    formatted_content JSONB, -- 格式化后的内容

    -- 导出文件
    output_format VARCHAR(20) DEFAULT 'pdf', -- pdf/docx/latex
    output_path TEXT,
    output_url TEXT,

    -- 格式检查报告
    format_check_report JSONB,

    -- 处理时间
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- 错误信息
    error_message TEXT
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_format_tasks_user ON format_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_format_tasks_paper ON format_tasks(paper_id);
CREATE INDEX IF NOT EXISTS idx_format_tasks_status ON format_tasks(status);

-- ============== 格式检查规则表 ==============
CREATE TABLE IF NOT EXISTS format_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES format_templates(id) ON DELETE CASCADE,

    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- font/margin/heading/citation/page_number/etc
    description TEXT,

    -- 规则配置
    rule_config JSONB NOT NULL,

    -- 是否必须
    is_required BOOLEAN DEFAULT TRUE,

    -- 严重程度
    severity VARCHAR(20) DEFAULT 'error', -- error/warning/info

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_format_rules_template ON format_rules(template_id);
CREATE INDEX IF NOT EXISTS idx_format_rules_type ON format_rules(rule_type);

-- ============== 用户格式设置表 ==============
CREATE TABLE IF NOT EXISTS format_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- 默认模板
    default_thesis_template_id UUID REFERENCES format_templates(id) ON DELETE SET NULL,
    default_journal_template_id UUID REFERENCES format_templates(id) ON DELETE SET NULL,

    -- 导出设置
    default_export_format VARCHAR(20) DEFAULT 'pdf',
    auto_generate_toc BOOLEAN DEFAULT TRUE,
    auto_number_pages BOOLEAN DEFAULT TRUE,

    -- 自定义格式偏好
    preferences JSONB DEFAULT '{}',

    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============== 备注 ==============
COMMENT ON TABLE format_templates IS '格式模板表，存储各种论文格式规范';
COMMENT ON TABLE format_tasks IS '格式排版任务表';
COMMENT ON TABLE format_rules IS '格式检查规则表';
COMMENT ON TABLE format_settings IS '用户格式设置表';
