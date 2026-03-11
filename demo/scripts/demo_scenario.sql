-- ScholarForge 演示数据初始化脚本
-- 适用于 PostgreSQL

-- 插入演示用户
INSERT INTO users (id, email, name, avatar, role, institution, department, major, created_at, is_demo)
VALUES (
    'demo_user_001',
    'xiaoming.wang@example.edu',
    '王小明',
    '/avatars/demo/xiaoming.png',
    'student',
    '浙江大学',
    '工程师学院',
    '工程管理（MEM）',
    NOW(),
    TRUE
) ON CONFLICT (id) DO UPDATE SET is_demo = TRUE;

-- 插入演示论文
INSERT INTO papers (id, user_id, title, abstract, keywords, status, progress, target_words, total_words, created_at, updated_at)
VALUES (
    'demo_paper_001',
    'demo_user_001',
    '基于多Agent协同的智能科研论文写作系统项目管理研究',
    '随着大语言模型技术的快速发展，人与AI Agent的协同工作模式正在深刻改变科研论文写作的方式。本研究以智能科研论文写作系统ScholarForge为案例，探索多Agent协同的项目管理机制。',
    ARRAY['Human-Agent Collaboration', 'Multi-Agent Systems', 'Project Management', 'AI', 'LLM'],
    'in_progress',
    40,
    50000,
    20000,
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 插入论文章节
INSERT INTO chapters (id, paper_id, chapter_number, title, word_count, status, created_at)
VALUES
    ('demo_chapter_001', 'demo_paper_001', 1, '绪论', 20000, 'completed', NOW()),
    ('demo_chapter_002', 'demo_paper_001', 2, '理论基础', 19500, 'completed', NOW()),
    ('demo_chapter_003', 'demo_paper_001', 3, '系统架构设计', 19500, 'in_progress', NOW()),
    ('demo_chapter_004', 'demo_paper_001', 4, '关键技术实现', 21000, 'pending', NOW()),
    ('demo_chapter_005', 'demo_paper_001', 5, '系统测试与案例分析', 18500, 'pending', NOW()),
    ('demo_chapter_006', 'demo_paper_001', 6, '结论与展望', 7000, 'pending', NOW())
ON CONFLICT (id) DO NOTHING;

-- 插入演示文献
INSERT INTO references_table (id, user_id, title, author, year, journal, doi, abstract, keywords, citations, is_core, category, created_at)
SELECT
    ref->>'id',
    'demo_user_001',
    ref->>'title',
    ref->>'author',
    (ref->>'year')::int,
    ref->>'journal',
    ref->>'doi',
    ref->>'abstract',
    ARRAY(SELECT jsonb_array_elements_text(ref->'keywords')),
    (ref->>'citations')::int,
    (ref->>'is_core')::boolean,
    ref->>'category',
    NOW()
FROM jsonb_array_elements('
[
  {"id": "ref_001", "title": "A Unified Framework for Human-Agent Collaboration", "author": "Microsoft Research", "year": 2025, "journal": "MSR Technical Report", "doi": "", "abstract": "This paper proposes a unified framework for Human-Agent Collaboration.", "keywords": ["Human-Agent Collaboration", "Framework"], "citations": 128, "is_core": true, "category": "人机协同理论"},
  {"id": "ref_002", "title": "Towards fluid human-agent collaboration", "author": "Chiari, M., et al.", "year": 2025, "journal": "Frontiers in Robotics and AI", "doi": "10.3389/frobt.2025.1532693", "abstract": "This study explores dynamic human-agent collaboration.", "keywords": ["Human-Agent Collaboration"], "citations": 56, "is_core": true, "category": "人机协同理论"},
  {"id": "ref_003", "title": "LLM-Based Human-Agent Collaboration and Interaction Systems: A Survey", "author": "Peng, H., et al.", "year": 2025, "journal": "ACL Findings", "doi": "", "abstract": "Comprehensive survey of LLM-based Human-Agent Collaboration systems.", "keywords": ["LLM", "Survey"], "citations": 89, "is_core": true, "category": "人机协同理论"},
  {"id": "ref_004", "title": "Shaping the Future of Project Management With AI", "author": "PMI", "year": 2025, "journal": "PMI Report", "doi": "", "abstract": "How AI is transforming project management.", "keywords": ["AI", "Project Management"], "citations": 234, "is_core": true, "category": "AI项目管理"},
  {"id": "ref_005", "title": "Agent2Agent Protocol Specification", "author": "Google", "year": 2025, "journal": "Google Technical Report", "doi": "", "abstract": "The A2A protocol enables AI agents to communicate.", "keywords": ["A2A", "Protocol"], "citations": 156, "is_core": true, "category": "Agent通信协议"}
]'::jsonb) AS ref
ON CONFLICT (id) DO NOTHING;

-- 创建演示配置
INSERT INTO app_settings (key, value, description)
VALUES
    ('demo_mode_enabled', 'true', '是否启用演示模式'),
    ('demo_user_id', 'demo_user_001', '演示用户ID'),
    ('demo_auto_login', 'true', '是否自动登录演示用户'),
    ('demo_show_wizard', 'true', '是否显示演示向导')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- 插入演示活动记录
INSERT INTO activities (user_id, action, entity_type, entity_id, details, created_at)
VALUES
    ('demo_user_001', 'login', 'user', 'demo_user_001', '{"ip": "127.0.0.1", "device": "Chrome"}'::jsonb, NOW() - INTERVAL '2 hours'),
    ('demo_user_001', 'create', 'paper', 'demo_paper_001', '{"title": "基于多Agent协同的智能科研论文写作系统项目管理研究"}'::jsonb, NOW() - INTERVAL '7 days'),
    ('demo_user_001', 'complete_chapter', 'chapter', 'demo_chapter_001', '{"chapter": 1, "title": "绪论"}'::jsonb, NOW() - INTERVAL '5 days'),
    ('demo_user_001', 'complete_chapter', 'chapter', 'demo_chapter_002', '{"chapter": 2, "title": "理论基础"}'::jsonb, NOW() - INTERVAL '2 days'),
    ('demo_user_001', 'start_chapter', 'chapter', 'demo_chapter_003', '{"chapter": 3, "title": "系统架构设计"}'::jsonb, NOW() - INTERVAL '1 day'),
    ('demo_user_001', 'search_literature', 'reference', '', '{"keywords": ["Human-Agent Collaboration"], "results_count": 45}'::jsonb, NOW() - INTERVAL '6 days'),
    ('demo_user_001', 'add_reference', 'reference', 'ref_001', '{"title": "A Unified Framework for Human-Agent Collaboration"}'::jsonb, NOW() - INTERVAL '6 days'),
    ('demo_user_001', 'ai_writing', 'ai', '', '{"task_type": "continue", "word_count": 500}'::jsonb, NOW() - INTERVAL '3 days'),
    ('demo_user_001', 'plagiarism_check', 'plagiarism', 'demo_paper_001', '{"similarity": 12.8}'::jsonb, NOW() - INTERVAL '1 day')
ON CONFLICT DO NOTHING;

-- 创建演示模板
INSERT INTO templates (id, name, description, category, content, is_demo, created_at)
VALUES (
    'demo_template_thesis',
    'MEM硕士论文模板',
    '浙江大学工程管理硕士论文标准模板',
    'thesis',
    '{
        "structure": [
            {"chapter": 1, "title": "绪论", "sections": ["研究背景", "研究意义", "国内外研究现状", "研究内容与方法", "论文结构"]},
            {"chapter": 2, "title": "理论基础", "sections": ["项目管理理论", "人机协同理论", "多Agent系统理论", "大语言模型技术"]},
            {"chapter": 3, "title": "系统架构设计", "sections": ["需求分析", "系统总体架构", "多Agent协同机制设计", "人机协作流程设计"]},
            {"chapter": 4, "title": "关键技术实现", "sections": ["基于LLM的智能写作Agent", "基于RAG的知识检索Agent", "多Agent协同调度机制", "实时协作与版本管理"]},
            {"chapter": 5, "title": "系统测试与案例分析", "sections": ["测试环境与工具", "功能测试与评估", "性能测试与分析", "ScholarForge项目案例分析"]},
            {"chapter": 6, "title": "结论与展望", "sections": ["研究结论", "创新点总结", "研究局限与展望"]}
        ],
        "format": {
            "page_size": "A4",
            "margins": {"top": "2.54cm", "bottom": "2.54cm", "left": "3.17cm", "right": "3.17cm"},
            "font": {"chinese": "宋体", "english": "Times New Roman"},
            "font_size": {"title1": "16pt", "title2": "14pt", "title3": "12pt", "body": "12pt"},
            "line_spacing": "1.5"
        }
    }'::jsonb,
    TRUE,
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 输出完成信息
SELECT '演示数据初始化完成' AS status;
