-- 性能优化索引
-- Migration: 010_performance_indexes
-- 为常用查询添加索引以优化性能

-- 选题建议表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_topic_suggestions_user_created
ON topic_suggestions(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_topic_suggestions_field
ON topic_suggestions(field) WHERE field IS NOT NULL;

-- 进度里程碑表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_milestones_paper_due
ON milestones(paper_id, due_date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_milestones_status
ON milestones(status) WHERE status != 'completed';

-- 进度任务表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_milestone
ON tasks(milestone_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_assignee
ON tasks(assignee_id, status) WHERE assignee_id IS NOT NULL;

-- 期刊匹配表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_journal_matches_score
ON journal_matches(paper_id, match_score DESC);

-- 知识图谱节点表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_nodes_paper
ON knowledge_nodes(paper_id, node_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_nodes_label
ON knowledge_nodes USING gin(to_tsvector('simple', label));

-- 知识图谱关系表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_edges_source
ON knowledge_edges(source_id, relation_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_edges_target
ON knowledge_edges(target_id, relation_type);

-- 参考文献表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_references_paper
ON references_table(paper_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_references_doi
ON references_table(doi) WHERE doi IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_references_folder
ON references_table(folder_id) WHERE folder_id IS NOT NULL;

-- 引用关系表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_citations_paper
ON citations(paper_id, citation_type);

-- 查重检测表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plagiarism_checks_paper
ON plagiarism_checks(paper_id, submitted_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plagiarism_checks_status
ON plagiarism_checks(status) WHERE status IN ('pending', 'processing');

-- 查重白名单表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_plagiarism_whitelist_paper
ON plagiarism_whitelist(paper_id);

-- 格式模板表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_format_templates_public
ON format_templates(is_public, template_type) WHERE is_public = TRUE;

-- 格式任务表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_format_tasks_user
ON format_tasks(user_id, created_at DESC);

-- 答辩检查清单表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_defense_checklists_paper_user
ON defense_checklists(paper_id, user_id);

-- 答辩PPT表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_defense_ppts_paper_status
ON defense_ppts(paper_id, status);

-- 答辩问答库表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_defense_qa_paper_category
ON defense_qa(paper_id, category) WHERE paper_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_defense_qa_difficulty
ON defense_qa(difficulty);

-- 添加注释
COMMENT ON INDEX idx_topic_suggestions_user_created IS '优化用户选题历史查询';
COMMENT ON INDEX idx_milestones_paper_due IS '优化论文里程碑截止日期查询';
COMMENT ON INDEX idx_knowledge_nodes_label IS 'GIN索引，用于节点标签全文搜索';
COMMENT ON INDEX idx_references_doi IS '优化DOI去重检查';
COMMENT ON INDEX idx_plagiarism_checks_status IS '优化待处理查重任务查询';
