"""
学术领域Prompt模板
针对学术问答、文献综述、方法建议等场景优化
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import json


class PromptType(str, Enum):
    """Prompt类型"""
    RESEARCH_QA = "research_qa"  # 研究问答
    LITERATURE_REVIEW = "literature_review"  # 文献综述
    METHOD_SUGGESTION = "method_suggestion"  # 方法建议
    PAPER_REVIEW = "paper_review"  # 论文审阅
    EXPERIMENT_DESIGN = "experiment_design"  # 实验设计
    STATISTICAL_ANALYSIS = "statistical_analysis"  # 统计分析
    WRITING_ASSISTANT = "writing_assistant"  # 写作辅助


class CitationStyle(str, Enum):
    """引用格式"""
    APA = "APA"
    MLA = "MLA"
    CHICAGO = "Chicago"
    GB_T_7714 = "GB/T 7714"


@dataclass
class PromptTemplate:
    """Prompt模板"""
    name: str
    type: PromptType
    template: str
    description: str
    version: str = "1.0"
    variables: List[str] = field(default_factory=list)
    examples: List[Dict] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)

    def format(self, **kwargs) -> str:
        """格式化模板"""
        return self.template.format(**kwargs)


class AcademicPrompts:
    """学术Prompt模板集合"""

    @staticmethod
    def get_research_qa_prompt(citation_style: CitationStyle = CitationStyle.GB_T_7714) -> PromptTemplate:
        """研究问答Prompt"""
        template = """你是一个学术研究助手，专门帮助研究人员回答专业问题。请基于提供的参考文献回答问题。

## 用户问题
{question}

## 参考文献
{references}

## 回答要求
1. **准确性和可验证性**：回答必须基于提供的参考文献，明确标注引用来源
2. **结构清晰**：使用标题和列表组织回答
3. **学术严谨**：使用专业术语，避免模糊表述
4. **批判性思维**：如果文献中有不同观点，请客观呈现
5. **引用格式**：使用{citation_style}格式标注引用，如[1]、[2]

## 回答结构
1. **直接回答**：简要直接地回答用户问题（2-3句话）
2. **详细解释**：提供更详细的背景和解释
3. **相关研究**：列举支持该答案的关键研究及其发现
4. **局限性和展望**：指出当前研究的局限性或未来研究方向

请开始回答："""

        return PromptTemplate(
            name="研究问答",
            type=PromptType.RESEARCH_QA,
            template=template,
            description="用于回答学术研究问题，基于提供的文献",
            variables=["question", "references", "citation_style"],
            examples=[
                {
                    "input": "大语言模型在医学领域的应用有哪些？",
                    "output": "根据文献[1][3]，大语言模型在医学领域主要应用于..."
                }
            ],
            tips=[
                "提供具体的研究名称和作者",
                "区分不同研究之间的观点差异",
                "指出证据的强弱程度"
            ]
        )

    @staticmethod
    def get_literature_review_prompt() -> PromptTemplate:
        """文献综述Prompt"""
        template = """你是一个文献综述专家。请基于提供的多篇文献，生成一篇结构化的文献综述。

## 综述主题
{topic}

## 待综述文献
{papers}

## 综述要求
1. **系统性**：按主题或时间线组织文献
2. **批判性**：比较不同研究的优缺点
3. **结构化**：包含引言、主体、结论
4. **趋势分析**：识别研究热点和发展趋势
5. **研究空白**：指出现有研究的不足之处

## 综述结构
### 1. 引言
- 研究背景和意义
- 综述范围和目标

### 2. 研究现状
按以下维度组织：
- **理论基础**：相关理论框架
- **研究方法**：常用研究方法和技术
- **主要发现**：各领域的关键发现
- **争议焦点**：存在争议的问题

### 3. 发展趋势
- 新兴研究方向
- 技术进展

### 4. 研究空白与展望
- 尚未解决的问题
- 未来研究方向

### 5. 结论
- 总结主要发现
- 对实践和政策的建议

请生成文献综述："""

        return PromptTemplate(
            name="文献综述",
            type=PromptType.LITERATURE_REVIEW,
            template=template,
            description="生成结构化的文献综述",
            variables=["topic", "papers"],
            tips=[
                "按主题而非按文章组织内容",
                "使用比较和对比",
                "注意引用原始文献"
            ]
        )

    @staticmethod
    def get_method_suggestion_prompt() -> PromptTemplate:
        """方法建议Prompt"""
        template = """你是一个研究方法专家。请基于研究问题推荐最合适的研究方法。

## 研究问题
{research_question}

## 研究背景
{background}

## 可用资源
{resources}

## 方法推荐框架
请从以下维度分析：

### 1. 研究类型判定
- 探索性 vs 验证性
- 定性 vs 定量 vs 混合方法

### 2. 数据收集方法
- 一手数据 vs 二手数据
- 实验法 vs 观察法 vs 调查法

### 3. 分析方法
- 统计分析（描述性、推断性）
- 质性分析（编码、主题分析）
- 机器学习方法（如适用）

### 4. 方法对比
| 方法 | 优势 | 局限 | 适用性评分 |
|------|------|------|-----------|

### 5. 具体建议
- 推荐的主要方法
- 备选方案
- 实施步骤

### 6. 注意事项
- 常见陷阱
- 方法局限性
- 改进建议

请提供详细的方法建议："""

        return PromptTemplate(
            name="方法建议",
            type=PromptType.METHOD_SUGGESTION,
            template=template,
            description="为研究问题推荐合适的研究方法",
            variables=["research_question", "background", "resources"]
        )

    @staticmethod
    def get_paper_review_prompt(review_aspect: str = "general") -> PromptTemplate:
        """论文审阅Prompt"""
        aspects = {
            "general": "全面审阅",
            "innovation": "创新性评估",
            "methodology": "方法论评估",
            "writing": "写作质量"
        }

        template = """你是一个专业的学术期刊审稿人。请对以下论文进行{review_aspect}审阅。

## 审阅标准
1. **创新性**：研究的新颖程度和贡献
2. **科学性**：研究设计的严谨性
3. **方法学**：方法的适当性和可靠性
4. **数据分析**：统计方法是否正确
5. **结果解释**：结论是否合理
6. **写作质量**：表达清晰度和逻辑性

## 论文内容
{paper_content}

## 审阅报告格式

### 1. 总体评价
- 论文质量评级（优秀/良好/需重大修改/拒稿）
- 主要优点（2-3点）
- 主要不足（2-3点）

### 2. 详细评价

#### 创新性
评分：⭐⭐⭐⭐⭐（1-5星）
评价：...

#### 方法论
评分：⭐⭐⭐⭐⭐（1-5星）
评价：...

#### 数据分析
评分：⭐⭐⭐⭐⭐（1-5星）
评价：...

#### 写作质量
评分：⭐⭐⭐⭐⭐（1-5星）
评价：...

### 3. 具体修改建议
- **必须修改**：影响论文质量的关键问题
- **建议修改**：可以提升论文的改进建议
- **可选修改**：细微的改进点

### 4. 审稿结论
- [ ] 接受发表
- [ ] 小修后接受
- [ ] 大修后再审
- [ ] 拒稿

理由：...

请生成审阅报告："""

        return PromptTemplate(
            name=f"论文审阅-{aspects.get(review_aspect, 'general')}",
            type=PromptType.PAPER_REVIEW,
            template=template,
            description=f"从{aspects.get(review_aspect, 'general')}角度审阅论文",
            variables=["paper_content", "review_aspect"]
        )

    @staticmethod
    def get_experiment_design_prompt() -> PromptTemplate:
        """实验设计Prompt"""
        template = """你是一个实验设计专家。请帮助设计一个严谨的实验方案。

## 研究假设
{hypothesis}

## 实验目的
{purpose}

## 约束条件
{constraints}

## 实验设计方案

### 1. 实验设计类型
- 设计类型（RCT、准实验、观察性研究等）
- 设计理由

### 2. 变量定义
- **自变量**：操作定义和水平
- **因变量**：测量指标和操作定义
- **控制变量**：需要控制的混淆因素
- **随机变量**：如何处理随机因素

### 3. 被试/样本
- **抽样方法**：如何选取样本
- **样本量计算**：统计功效分析
- **纳入/排除标准**：

### 4. 实验流程
1. 预实验准备
2. 基线测量
3. 干预/处理
4. 后测
5. 随访（如适用）

### 5. 数据收集
- 数据收集工具
- 数据质量控制

### 6. 统计分析计划
- 描述性统计
- 推断性统计
- 效应量计算

### 7. 伦理考虑
- 伦理审批
- 知情同意
- 隐私保护

### 8. 潜在问题与对策
- 预期困难
- 应对方案

请生成完整的实验设计方案："""

        return PromptTemplate(
            name="实验设计",
            type=PromptType.EXPERIMENT_DESIGN,
            template=template,
            description="设计严谨的实验方案",
            variables=["hypothesis", "purpose", "constraints"]
        )

    @staticmethod
    def get_statistical_analysis_prompt() -> PromptTemplate:
        """统计分析Prompt"""
        template = """你是一个生物统计学专家。请提供统计分析建议。

## 研究问题
{research_question}

## 数据描述
{data_description}

## 分析目标
{analysis_goal}

## 统计分析建议

### 1. 数据探索
- 数据清洗步骤
- 描述性统计
- 数据可视化建议

### 2. 假设检验
- 适用性检验（正态性、方差齐性等）
- 检验方法选择
- 多重比较校正

### 3. 统计方法
| 分析目标 | 推荐方法 | 备选方法 | 适用条件 |
|---------|---------|---------|---------|

### 4. 效应量
- 推荐指标
- 解释标准

### 5. 结果报告
- 必须报告的内容
- 结果解释模板

### 6. 常见错误
- 需要避免的错误
- 如何纠正

### 7. 软件实现
- R代码示例
- Python代码示例

请提供详细的统计分析建议："""

        return PromptTemplate(
            name="统计分析",
            type=PromptType.STATISTICAL_ANALYSIS,
            template=template,
            description="提供统计分析方法建议",
            variables=["research_question", "data_description", "analysis_goal"]
        )

    @staticmethod
    def get_writing_assistant_prompt(section_type: str = "general") -> PromptTemplate:
        """写作辅助Prompt"""
        sections = {
            "abstract": "摘要",
            "introduction": "引言",
            "methods": "方法",
            "results": "结果",
            "discussion": "讨论",
            "conclusion": "结论",
            "general": "通用写作"
        }

        section_tips = {
            "abstract": """摘要写作要点：
1. 结构：背景、目的、方法、结果、结论
2. 字数：通常200-300字
3. 避免：引用、缩写（首次使用）、图表引用""",
            "introduction": """引言写作要点：
1. 漏斗式结构：从宽泛到具体
2. 逻辑链：背景→问题→研究空白→本研究
3. 引用：支持每个关键陈述""",
            "methods": """方法部分要点：
1. 详细到可重复
2. 使用过去时态
3. 伦理声明（如适用）"""
        }

        template = """你是一个学术写作教练。请帮助改进{section_name}部分的写作。

{section_tips}

## 原始文本
{original_text}

## 改进建议

### 1. 内容评价
- **优点**：...
- **不足**：...

### 2. 结构优化
- 建议的结构调整
- 段落重组建议

### 3. 语言润色
- 具体修改建议（逐句）
- 学术表达优化

### 4. 改进后的版本
{improved_version}

### 5. 检查清单
- [ ] 逻辑连贯
- [ ] 学术规范
- [ ] 语法正确
- [ ] 引用规范"""

        return PromptTemplate(
            name=f"写作辅助-{sections.get(section_type, '通用')}",
            type=PromptType.WRITING_ASSISTANT,
            template=template,
            description=f"改进{sections.get(section_type, '通用')}部分的写作",
            variables=["section_name", "section_tips", "original_text", "improved_version"]
        )

    @classmethod
    def get_all_prompts(cls) -> Dict[PromptType, PromptTemplate]:
        """获取所有Prompt模板"""
        return {
            PromptType.RESEARCH_QA: cls.get_research_qa_prompt(),
            PromptType.LITERATURE_REVIEW: cls.get_literature_review_prompt(),
            PromptType.METHOD_SUGGESTION: cls.get_method_suggestion_prompt(),
            PromptType.PAPER_REVIEW: cls.get_paper_review_prompt(),
            PromptType.EXPERIMENT_DESIGN: cls.get_experiment_design_prompt(),
            PromptType.STATISTICAL_ANALYSIS: cls.get_statistical_analysis_prompt(),
            PromptType.WRITING_ASSISTANT: cls.get_writing_assistant_prompt(),
        }
