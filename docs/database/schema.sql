-- ScholarForge 数据库模式设计 v2.0
-- 一站式智能学术研究协作平台

-- ============== 扩展 UUID 支持 ==============
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 用于模糊搜索

-- ============== 枚举类型定义 ==============

-- 用户角色
CREATE TYPE user_role AS ENUM ('student', 'teacher', 'researcher', 'institution', 'admin');

-- 论文状态
CREATE TYPE paper_status AS ENUM ('draft', 'in_progress', 'review', 'revision', 'submitted', 'accepted', 'published', 'archived');

-- 协作角色
CREATE TYPE collab_role AS ENUM ('owner', 'editor', 'reviewer', 'viewer');

-- 批注类型
CREATE TYPE annotation_type AS ENUM ('comment', 'suggestion', 'question', 'correction', 'approval');

-- 批注状态
CREATE TYPE annotation_status AS ENUM ('pending', 'accepted', 'rejected', 'resolved');

-- 投稿状态
CREATE TYPE submission_status AS ENUM ('draft', 'submitted', 'under_review', 'revision_required', 'accepted', 'rejected', 'withdrawn');

-- ============== 用户与团队 ==============

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'student',
    full_name VARCHAR(200),
    avatar_url VARCHAR(500),
    bio TEXT,

    -- 学术信息
    university VARCHAR(200),
    department VARCHAR(200),
    major VARCHAR(200),
    research_interests TEXT[],  -- 研究兴趣数组
    orcid_id VARCHAR(50),       -- ORCID 研究者ID

    -- 偏好设置
    preferences JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',

    -- 订阅信息
    subscription_tier VARCHAR(20) DEFAULT 'free',  -- free, pro, team, enterprise
    subscription_expires_at TIMESTAMP,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- 索引优化
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_university ON users(university);
CREATE INDEX idx_users_role ON users(role);

-- 团队/实验室表
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 团队设置
    avatar_url VARCHAR(500),
    plan_type VARCHAR(20) DEFAULT 'free',  -- free, pro, enterprise
    max_members INTEGER DEFAULT 5,
    storage_quota BIGINT DEFAULT 10737418240,  -- 10GB in bytes

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 团队成员表
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member',  -- owner, admin, member

    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(team_id, user_id)
);

-- ============== 论文管理 ==============

-- 论文表
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    abstract TEXT,
    keywords TEXT[],

    -- 所有者与团队
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,

    -- 论文元数据
    paper_type VARCHAR(50) DEFAULT 'thesis',  -- thesis, journal, conference, report
    status paper_status NOT NULL DEFAULT 'draft',
    language VARCHAR(10) DEFAULT 'zh',

    -- 模板与格式
    template_id UUID REFERENCES paper_templates(id),
    citation_style VARCHAR(50) DEFAULT 'gb-t-7714-2015',

    -- 统计信息
    word_count INTEGER DEFAULT 0,
    page_count INTEGER DEFAULT 0,
    figure_count INTEGER DEFAULT 0,
    table_count INTEGER DEFAULT 0,
    reference_count INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_papers_owner ON papers(owner_id);
CREATE INDEX idx_papers_team ON papers(team_id);
CREATE INDEX idx_papers_status ON papers(status);
CREATE INDEX idx_papers_keywords ON papers USING GIN(keywords);

-- 论文章节表
CREATE TABLE paper_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES paper_sections(id) ON DELETE CASCADE,

    title VARCHAR(500),
    content TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,

    -- 章节元数据
    section_type VARCHAR(50),  -- chapter, section, subsection
    word_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_paper_sections_paper ON paper_sections(paper_id);
CREATE INDEX idx_paper_sections_parent ON paper_sections(parent_id);

-- 论文协作表
CREATE TABLE paper_collaborators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role collab_role NOT NULL DEFAULT 'viewer',

    -- 权限设置
    can_edit BOOLEAN DEFAULT FALSE,
    can_comment BOOLEAN DEFAULT TRUE,
    can_share BOOLEAN DEFAULT FALSE,

    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(paper_id, user_id)
);

CREATE INDEX idx_paper_collab_paper ON paper_collaborators(paper_id);
CREATE INDEX idx_paper_collab_user ON paper_collaborators(user_id);

-- 论文版本历史
CREATE TABLE paper_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    title VARCHAR(500),
    content_snapshot JSONB,  -- 存储完整快照或增量

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    change_summary TEXT,

    UNIQUE(paper_id, version_number)
);

CREATE INDEX idx_paper_versions_paper ON paper_versions(paper_id);

-- ============== 模板管理 ==============

-- 论文模板表
CREATE TABLE paper_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- 模板来源
    source_type VARCHAR(20) DEFAULT 'system',  -- system, university, journal, custom
    source_id VARCHAR(100),  -- 大学代码或期刊ISSN

    -- 模板配置
    config JSONB NOT NULL DEFAULT '{}',  -- 包含格式、样式等配置
    preview_url VARCHAR(500),

    -- 可见性
    is_public BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============== 批注系统 ==============

-- 批注表
CREATE TABLE annotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    section_id UUID REFERENCES paper_sections(id) ON DELETE CASCADE,

    -- 批注作者
    author_id UUID NOT NULL REFERENCES users(id),

    -- 批注内容
    annotation_type annotation_type NOT NULL DEFAULT 'comment',
    content TEXT NOT NULL,

    -- 位置信息（用于精确定位）
    position JSONB DEFAULT '{}',  -- {start_offset, end_offset, selector}

    -- 状态
    status annotation_status NOT NULL DEFAULT 'pending',

    -- 关联
    parent_id UUID REFERENCES annotations(id) ON DELETE CASCADE,  -- 支持回复
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_annotations_paper ON annotations(paper_id);
CREATE INDEX idx_annotations_author ON annotations(author_id);
CREATE INDEX idx_annotations_section ON annotations(section_id);
CREATE INDEX idx_annotations_status ON annotations(status);

-- ============== 文献管理 ==============

-- 文献表
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doi VARCHAR(100) UNIQUE,
    title TEXT NOT NULL,
    authors JSONB DEFAULT '[]',  -- [{name, orcid, affiliation}]
    abstract TEXT,
    keywords TEXT[],

    -- 来源信息
    source_type VARCHAR(20),  -- journal, conference, book, thesis, preprint
    source_name VARCHAR(500),  -- 期刊名或会议名
    source_db VARCHAR(20),    -- cnki, wos, ieee, arxiv, crossref

    -- 出版信息
    publication_year INTEGER,
    publication_date DATE,
    volume VARCHAR(50),
    issue VARCHAR(50),
    pages VARCHAR(50),
    issn VARCHAR(20),
    isbn VARCHAR(20),

    -- 指标
    citation_count INTEGER DEFAULT 0,
    impact_factor DECIMAL(5,3),

    -- 链接
    pdf_url VARCHAR(500),
    source_url VARCHAR(500),

    -- 原始数据
    raw_data JSONB,

    -- 索引时间
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_articles_doi ON articles(doi);
CREATE INDEX idx_articles_title ON articles USING GIN(to_tsvector('simple', title));
CREATE INDEX idx_articles_source_db ON articles(source_db);
CREATE INDEX idx_articles_year ON articles(publication_year);
CREATE INDEX idx_articles_keywords ON articles USING GIN(keywords);

-- 用户文献库
CREATE TABLE user_libraries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- 用户标注
    is_favorite BOOLEAN DEFAULT FALSE,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,

    -- 用户笔记
    notes TEXT,
    tags TEXT[],

    -- 分类
    folder_id UUID REFERENCES library_folders(id) ON DELETE SET NULL,

    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, article_id)
);

CREATE INDEX idx_user_libraries_user ON user_libraries(user_id);
CREATE INDEX idx_user_libraries_article ON user_libraries(article_id);

-- 文献文件夹
CREATE TABLE library_folders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES library_folders(id) ON DELETE CASCADE,

    name VARCHAR(200) NOT NULL,
    description TEXT,
    color VARCHAR(10),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============== 推荐系统 ==============

-- 推荐记录表
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- 推荐信息
    recommendation_score DECIMAL(5,4),
    recommendation_reason TEXT,
    algorithm_version VARCHAR(50),

    -- 推送信息
    pushed_at TIMESTAMP WITH TIME ZONE,
    push_channel VARCHAR(20),  -- email, app, wechat

    -- 用户反馈
    user_feedback VARCHAR(20),  -- clicked, saved, ignored, dismissed
    feedback_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, article_id, DATE(created_at))
);

CREATE INDEX idx_recommendations_user ON recommendations(user_id);
CREATE INDEX idx_recommendations_pushed ON recommendations(pushed_at);

-- ============== 期刊管理 ==============

-- 期刊数据库
CREATE TABLE journals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    issn VARCHAR(20) UNIQUE,
    eissn VARCHAR(20),

    -- 期刊信息
    publisher VARCHAR(200),
    subject_areas TEXT[],
    language VARCHAR(10),

    -- 指标
    impact_factor DECIMAL(5,3),
    h_index INTEGER,
    sjr DECIMAL(6,3),

    -- 投稿信息
    submission_url VARCHAR(500),
    review_cycle_days INTEGER,
    acceptance_rate DECIMAL(5,2),
    publication_fee DECIMAL(10,2),

    -- 开放获取
    is_open_access BOOLEAN DEFAULT FALSE,
    apc DECIMAL(10,2),  -- Article Processing Charge

    -- 其他
    description TEXT,
    scope TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_journals_issn ON journals(issn);
CREATE INDEX idx_journals_subject ON journals USING GIN(subject_areas);

-- 投稿记录
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    journal_id UUID REFERENCES journals(id) ON DELETE SET NULL,

    -- 投稿信息
    manuscript_id VARCHAR(100),  -- 期刊分配的稿件号
    status submission_status NOT NULL DEFAULT 'draft',

    -- 时间节点
    submitted_at TIMESTAMP WITH TIME ZONE,
    first_decision_at TIMESTAMP WITH TIME ZONE,
    revision_submitted_at TIMESTAMP WITH TIME ZONE,
    final_decision_at TIMESTAMP WITH TIME ZONE,

    -- 决策信息
    decision VARCHAR(50),  -- accept, minor_revision, major_revision, reject
    decision_letter TEXT,

    -- 审稿人
    reviewers JSONB DEFAULT '[]',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_submissions_paper ON submissions(paper_id);
CREATE INDEX idx_submissions_journal ON submissions(journal_id);
CREATE INDEX idx_submissions_status ON submissions(status);

-- ============== 图表管理 ==============

-- 图表资源表
CREATE TABLE figures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    section_id UUID REFERENCES paper_sections(id) ON DELETE SET NULL,

    -- 图表信息
    figure_type VARCHAR(50),  -- figure, table, equation
    figure_number INTEGER,
    caption TEXT,
    description TEXT,

    -- 文件信息
    file_url VARCHAR(500),
    file_format VARCHAR(20),
    file_size INTEGER,

    -- 图表数据（用于重新生成）
    chart_config JSONB,  -- ECharts或其他图表库配置
    source_data JSONB,   -- 原始数据

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_figures_paper ON figures(paper_id);

-- ============== 参考文献管理 ==============

-- 参考文献表
CREATE TABLE references (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE SET NULL,

    -- 引用信息
    citation_key VARCHAR(100),  -- BibTeX key
    reference_text TEXT NOT NULL,
    reference_type VARCHAR(50),  -- article, book, inproceedings, etc.

    -- 位置信息
    citation_positions JSONB DEFAULT '[]',  -- [{section_id, paragraph, position}]

    -- 格式化文本
    formatted_text TEXT,  -- 按当前引用格式格式化后的文本

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_references_paper ON references(paper_id);
CREATE INDEX idx_references_article ON references(article_id);

-- ============== 知识图谱 ==============

-- 概念实体表（与Neo4j同步）
CREATE TABLE concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    concept_type VARCHAR(50),  -- method, theory, application, domain
    description TEXT,
    aliases TEXT[],

    -- 外部关联
    wikidata_id VARCHAR(50),
    dbpedia_uri VARCHAR(500),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_concepts_name ON concepts USING GIN(to_tsvector('simple', name));

-- ============== 任务与进度管理 ==============

-- 任务表
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    assignee_id UUID REFERENCES users(id) ON DELETE SET NULL,

    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- 任务信息
    task_type VARCHAR(50),  -- writing, review, revision, submission
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
    priority VARCHAR(10) DEFAULT 'medium',  -- low, medium, high, urgent

    -- 时间
    due_date DATE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- 关联
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_paper ON tasks(paper_id);
CREATE INDEX idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- ============== 通知与消息 ==============

-- 通知表
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    title VARCHAR(500) NOT NULL,
    content TEXT,
    notification_type VARCHAR(50),  -- system, collaboration, deadline, recommendation

    -- 关联资源
    resource_type VARCHAR(50),  -- paper, annotation, task, etc.
    resource_id UUID,

    -- 状态
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(user_id, is_read);

-- ============== 审计日志 ==============

-- 审计日志表
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,

    -- 变更详情
    old_values JSONB,
    new_values JSONB,

    -- 请求信息
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- ============== 触发器 ==============

-- 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_papers_updated_at BEFORE UPDATE ON papers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_paper_sections_updated_at BEFORE UPDATE ON paper_sections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_annotations_updated_at BEFORE UPDATE ON annotations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_journals_updated_at BEFORE UPDATE ON journals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_submissions_updated_at BEFORE UPDATE ON submissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_figures_updated_at BEFORE UPDATE ON figures
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============== 视图 ==============

-- 论文协作视图
CREATE VIEW paper_collaboration_view AS
SELECT
    p.id as paper_id,
    p.title,
    p.status,
    p.owner_id,
    u.email as owner_email,
    u.full_name as owner_name,
    pc.user_id as collaborator_id,
    cu.email as collaborator_email,
    cu.full_name as collaborator_name,
    pc.role as collaborator_role
FROM papers p
JOIN users u ON p.owner_id = u.id
LEFT JOIN paper_collaborators pc ON p.id = pc.paper_id
LEFT JOIN users cu ON pc.user_id = cu.id;

-- 用户活动统计视图
CREATE VIEW user_activity_stats AS
SELECT
    u.id as user_id,
    u.email,
    u.full_name,
    COUNT(DISTINCT p.id) as paper_count,
    COUNT(DISTINCT a.id) as annotation_count,
    COUNT(DISTINCT ul.id) as library_count,
    MAX(p.updated_at) as last_paper_update,
    MAX(a.created_at) as last_annotation
FROM users u
LEFT JOIN papers p ON u.id = p.owner_id
LEFT JOIN annotations a ON u.id = a.author_id
LEFT JOIN user_libraries ul ON u.id = ul.user_id
GROUP BY u.id, u.email, u.full_name;

-- ============== 初始数据 ==============

-- 插入默认模板
INSERT INTO paper_templates (name, description, source_type, config, is_public) VALUES
('浙江大学硕士学位论文', '浙江大学研究生院官方学位论文模板', 'university', '{"margin": {"top": "2.5cm", "bottom": "2.5cm", "left": "3cm", "right": "2.5cm"}, "font": {"family": "SimSun", "size": "12pt"}, "line_spacing": "1.5"}', TRUE),
('GB/T 7714-2015', '中国国家标准参考文献格式', 'system', '{"citation_style": "gb-t-7714-2015"}', TRUE),
('IEEE期刊格式', 'IEEE期刊投稿标准格式', 'journal', '{"citation_style": "ieee", "font": {"family": "Times New Roman", "size": "10pt"}}', TRUE),
('APA第7版', 'APA格式第7版', 'system', '{"citation_style": "apa-7"}', TRUE);
