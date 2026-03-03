-- Migration: 006_reference_tables.sql
-- 创建参考文献管理相关表
-- 最后更新: 2026-03-03

-- ============== 参考文献表 ==============
CREATE TABLE IF NOT EXISTS references_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,

    -- 基础文献信息
    title VARCHAR(500) NOT NULL,
    authors TEXT[],
    publication_year INTEGER,
    journal_name VARCHAR(300),
    volume VARCHAR(50),
    issue VARCHAR(50),
    pages VARCHAR(100),
    doi VARCHAR(200),
    pmid VARCHAR(50),
    url TEXT,

    -- 摘要和关键词
    abstract TEXT,
    keywords TEXT[],

    -- 出版信息
    publisher VARCHAR(200),
    publication_type VARCHAR(50) DEFAULT 'journal', -- journal/conference/book/thesis/report/online
    language VARCHAR(20) DEFAULT 'zh',

    -- 文件管理
    pdf_url TEXT,
    pdf_path TEXT,
    file_size INTEGER,

    -- 引用信息
    citation_count INTEGER DEFAULT 0,
    cited_times INTEGER DEFAULT 0, -- 被本文引用次数

    -- 元数据
    source_db VARCHAR(50), -- cnki/wos/ieee/arxiv/manual
    source_id VARCHAR(200), -- 原始数据源ID
    import_batch VARCHAR(100), -- 导入批次标识

    -- 用户标注
    notes TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    tags TEXT[],
    is_important BOOLEAN DEFAULT FALSE,
    is_read BOOLEAN DEFAULT FALSE,

    -- 分类
    folder_id UUID,
    category VARCHAR(100), -- 自定义分类

    -- 状态
    status VARCHAR(20) DEFAULT 'active', -- active/archived/deleted

    -- 时间戳
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_references_user ON references_table(user_id);
CREATE INDEX IF NOT EXISTS idx_references_paper ON references_table(paper_id);
CREATE INDEX IF NOT EXISTS idx_references_doi ON references_table(doi);
CREATE INDEX IF NOT EXISTS idx_references_title ON references_table USING GIN(to_tsvector('simple', title));
CREATE INDEX IF NOT EXISTS idx_references_authors ON references_table USING GIN(authors);
CREATE INDEX IF NOT EXISTS idx_references_keywords ON references_table USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_references_tags ON references_table USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_references_year ON references_table(publication_year);
CREATE INDEX IF NOT EXISTS idx_references_folder ON references_table(folder_id);
CREATE INDEX IF NOT EXISTS idx_references_type ON references_table(publication_type);
CREATE INDEX IF NOT EXISTS idx_references_added ON references_table(user_id, added_at DESC);

-- ============== 引用关系表 ==============
CREATE TABLE IF NOT EXISTS reference_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,

    -- 引用信息
    citing_ref_id UUID REFERENCES references_table(id) ON DELETE SET NULL,
    citing_position TEXT, -- 引用位置（章节）
    citation_text TEXT, -- 引用文本

    -- 被引用信息（如果是文献间引用）
    cited_ref_id UUID REFERENCES references_table(id) ON DELETE SET NULL,

    -- 引用格式
    citation_style VARCHAR(50) DEFAULT 'apa', -- apa/mla/chicago/gb7714
    formatted_citation TEXT,

    -- 引用序号
    citation_number INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_citations_paper ON reference_citations(paper_id);
CREATE INDEX IF NOT EXISTS idx_citations_citing ON reference_citations(citing_ref_id);
CREATE INDEX IF NOT EXISTS idx_citations_cited ON reference_citations(cited_ref_id);
CREATE INDEX IF NOT EXISTS idx_citations_number ON reference_citations(paper_id, citation_number);

-- ============== 文献文件夹表 ==============
CREATE TABLE IF NOT EXISTS reference_folders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(20) DEFAULT '#1890ff',
    parent_id UUID REFERENCES reference_folders(id) ON DELETE CASCADE,

    -- 排序
    sort_order INTEGER DEFAULT 0,

    -- 统计
    item_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ref_folders_user ON reference_folders(user_id);
CREATE INDEX IF NOT EXISTS idx_ref_folders_parent ON reference_folders(parent_id);

-- ============== 文献引用统计表（缓存） ==============
CREATE TABLE IF NOT EXISTS reference_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,

    -- 统计信息
    total_references INTEGER DEFAULT 0,
    journal_articles INTEGER DEFAULT 0,
    conference_papers INTEGER DEFAULT 0,
    books INTEGER DEFAULT 0,
    online_resources INTEGER DEFAULT 0,

    -- 年份分布
    year_distribution JSONB DEFAULT '{}',

    -- 作者统计
    top_authors JSONB DEFAULT '[]',

    -- 期刊统计
    top_journals JSONB DEFAULT '[]',

    -- 引用密度
    citations_per_section JSONB DEFAULT '{}',

    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ref_stats_paper ON reference_statistics(paper_id);

-- ============== 导入任务表 ==============
CREATE TABLE IF NOT EXISTS reference_import_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,

    -- 任务信息
    source_type VARCHAR(50) NOT NULL, -- zotero/endnote/mendeley/noteexpress/bibtex/ris
    file_name VARCHAR(255),
    file_path TEXT,

    -- 状态
    status VARCHAR(20) DEFAULT 'pending', -- pending/processing/completed/failed
    total_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,

    -- 错误信息
    error_message TEXT,
    failed_items JSONB DEFAULT '[]',

    -- 导入设置
    import_settings JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_import_tasks_user ON reference_import_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_import_tasks_status ON reference_import_tasks(status);

-- ============== 触发器：自动更新 updated_at ==============
CREATE TRIGGER update_references_updated_at
    BEFORE UPDATE ON references_table
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ref_folders_updated_at
    BEFORE UPDATE ON reference_folders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============== 备注 ==============
COMMENT ON TABLE references_table IS '参考文献表，存储用户收集的参考文献';
COMMENT ON TABLE reference_citations IS '引用关系表，记录论文中的引用情况';
COMMENT ON TABLE reference_folders IS '文献文件夹表';
COMMENT ON TABLE reference_statistics IS '文献统计缓存表';
COMMENT ON TABLE reference_import_tasks IS '文献导入任务表';
