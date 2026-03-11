# ScholarForge Phase 3 开发规划

> 目标：让 ScholarForge **真正可用**，显著提升科研效率
> 更新日期：2026-03-04

---

## 一、现状总结

### 1.1 已完成的功能 ✅

| 模块 | 状态 | 说明 |
|------|------|------|
| 用户认证 | ✅ 完成 | JWT认证、注册登录 |
| 论文管理 | ✅ 完成 | CRUD、版本控制 |
| 选题助手 | ✅ 完成 | AI选题建议、可行性分析 |
| 进度管理 | ✅ 完成 | 甘特图、里程碑追踪 |
| 知识图谱 | ✅ 完成 | 概念关系可视化 |
| 期刊匹配 | ✅ 完成 | 智能期刊推荐 |
| 查重检测 | ✅ 完成 | 多引擎支持（Mock） |
| 格式排版 | ✅ 完成 | 模板系统 |
| 答辩准备 | ✅ 完成 | PPT生成、常见问题 |

### 1.2 已增强的功能 🔧

| 模块 | 增强内容 | 状态 |
|------|----------|------|
| AI服务 | 流式响应、Token统计、健康检查、故障转移 | ✅ 完成 |
| LLMProvider | 支持OpenAI/Claude真实调用、成本估算 | ✅ 完成 |

---

## 二、Phase 3 核心开发任务

### Phase 3.1: 真实AI集成（已完成）✅

**交付成果**：
- [x] 增强版 LLMProvider (`llm_provider_v2.py`)
- [x] 流式响应支持 (`/ai/stream`)
- [x] Token使用统计 (`/ai/usage`)
- [x] 健康检查端点 (`/ai/health`)
- [x] 批量生成接口 (`/ai/batch`)

### Phase 3.2: PDF文献智能解析（进行中）🚧

**目标**：实现PDF文献的智能解析和内容提取

**核心功能**：
1. **PDF文本提取**
   - 提取PDF中的文本内容
   - 保留段落结构和格式
   - 支持扫描版PDF的OCR识别

2. **参考文献解析**
   - 自动识别参考文献列表
   - 解析GB/T 7714、APA等格式
   - 生成结构化引用数据

3. **图表提取**
   - 识别并提取PDF中的图片、表格
   - OCR识别图表中的文字
   - 生成图表描述

4. **智能摘要生成**
   - 基于AI生成文献摘要
   - 提取核心观点、研究方法、关键发现
   - 生成研究脉络图

**技术方案**：
```
backend/services/pdf_parser/
├── __init__.py
├── parser.py          # 主解析器
├── extractors/        # 提取器模块
│   ├── __init__.py
│   ├── text.py        # 文本提取
│   ├── references.py  # 参考文献提取
│   ├── figures.py     # 图表提取
│   └── metadata.py    # 元数据提取
├── ai_analyzer.py     # AI分析器
└── schemas.py         # 数据模型
```

**API设计**：
- `POST /api/v1/pdf/parse` - 解析PDF文件
- `POST /api/v1/pdf/extract/references` - 提取参考文献
- `POST /api/v1/pdf/analyze` - AI分析文献
- `GET /api/v1/pdf/status/{task_id}` - 查询解析状态

### Phase 3.3: 文献综述自动生成（待开发）📋

**目标**：基于多篇文献自动生成综述

**核心功能**：
1. **文献对比分析**
   - 多文献主题对比
   - 研究方法对比
   - 研究结果对比

2. **综述生成**
   - 自动生成文献综述草稿
   - 研究脉络识别
   - 研究空白分析

3. **引用推荐**
   - 基于内容推荐相关文献
   - 引用完整性检查

### Phase 3.4: 真实学术数据库对接（待开发）📋

**目标**：对接真实学术数据库API

**优先级**：
1. **arXiv** - 完全免费，无需API Key
2. **Semantic Scholar** - 免费学术API
3. **CrossRef** - DOI解析
4. **CNKI/IEEE** - 需申请API权限

---

## 三、立即实施：PDF解析服务开发

现在开始实现 PDF 解析服务的核心代码。

### 3.1 数据模型定义

```python
# schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class PDFMetadata(BaseModel):
    """PDF元数据"""
    title: Optional[str]
    authors: List[str]
    abstract: Optional[str]
    keywords: List[str]
    doi: Optional[str]
    publication_year: Optional[int]
    journal: Optional[str]
    pages: Optional[int]

class Reference(BaseModel):
    """参考文献"""
    id: str
    raw_text: str
    authors: List[str]
    title: str
    journal: Optional[str]
    year: Optional[int]
    doi: Optional[str]
    cited_in_paper: bool = False

class Figure(BaseModel):
    """图表"""
    id: str
    type: str  # "figure" | "table"
    caption: Optional[str]
    page_number: int
    ocr_text: Optional[str]
    description: Optional[str]

class PDFContent(BaseModel):
    """PDF内容"""
    full_text: str
    sections: List[Dict[str, str]]  # [{"title": "", "content": ""}]
    references: List[Reference]
    figures: List[Figure]
    metadata: PDFMetadata

class PDFParseResult(BaseModel):
    """PDF解析结果"""
    task_id: str
    status: str  # "pending" | "processing" | "completed" | "failed"
    file_name: str
    file_size: int
    content: Optional[PDFContent]
    ai_summary: Optional[str]
    ai_key_points: List[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
```

### 3.2 文本提取器

```python
# extractors/text.py
import re
from typing import List, Dict, Tuple
import fitz  # PyMuPDF

class TextExtractor:
    """PDF文本提取器"""

    def __init__(self):
        self.section_patterns = [
            r'^\s*1\.\s*引言|Introduction',
            r'^\s*2\.\s*相关研究|Related\s+Work|Literature\s+Review',
            r'^\s*3\.\s*方法|Methodology|Methods',
            r'^\s*4\.\s*实验|Experiments|Results',
            r'^\s*5\.\s*讨论|Discussion',
            r'^\s*6\.\s*结论|Conclusion',
            r'^\s*参考|References|Bibliography',
        ]

    async def extract(self, pdf_path: str) -> Dict:
        """提取PDF文本"""
        doc = fitz.open(pdf_path)

        full_text = ""
        sections = []
        current_section = {"title": "开头", "content": ""}

        for page_num, page in enumerate(doc):
            text = page.get_text()
            full_text += f"\n\n--- Page {page_num + 1} ---\n\n{text}"

            # 识别章节
            lines = text.split('\n')
            for line in lines:
                section_title = self._detect_section(line)
                if section_title:
                    if current_section["content"]:
                        sections.append(current_section)
                    current_section = {"title": section_title, "content": line + "\n"}
                else:
                    current_section["content"] += line + "\n"

        if current_section["content"]:
            sections.append(current_section)

        doc.close()

        return {
            "full_text": full_text,
            "sections": sections,
            "page_count": len(doc),
        }

    def _detect_section(self, line: str) -> Optional[str]:
        """检测章节标题"""
        for pattern in self.section_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return line.strip()
        return None
```

### 3.3 参考文献提取器

```python
# extractors/references.py
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Reference:
    raw_text: str
    authors: List[str]
    title: str
    year: int
    journal: str
    doi: str = None

class ReferenceExtractor:
    """参考文献提取器"""

    # 支持多种引用格式
    PATTERNS = {
        'gb_t_7714': r'\[\d+\].+',  # [1] 作者. 标题[J]. 期刊...
        'apa': r'\w+,.+\(\d{4}\).+',  # Author, A. (2024). Title...
        'ieee': r'\[\d+\].+',  # [1] A. Author, "Title"...
    }

    def extract(self, text: str) -> List[Reference]:
        """从文本中提取参考文献"""
        references = []

        # 找到参考文献章节
        ref_section = self._find_reference_section(text)
        if not ref_section:
            return references

        # 按行分割并解析
        lines = ref_section.split('\n')
        current_ref = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是新条目的开始
            if self._is_new_reference(line):
                if current_ref:
                    ref = self._parse_reference(current_ref)
                    if ref:
                        references.append(ref)
                current_ref = line
            else:
                current_ref += " " + line

        # 处理最后一个引用
        if current_ref:
            ref = self._parse_reference(current_ref)
            if ref:
                references.append(ref)

        return references

    def _find_reference_section(self, text: str) -> str:
        """找到参考文献章节"""
        patterns = [
            r'(?:参考文献|References|Bibliography)[\s\n]*(.+?)(?=\n\s*\n|\Z)',
            r'(?:参考文献|References|Bibliography)[\s\n]*(.+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1)
        return ""

    def _is_new_reference(self, line: str) -> bool:
        """检查是否是新参考文献的开始"""
        return bool(re.match(r'^[\[\(]?\d+[\]\)]?\s+|^\w+\s*,', line))

    def _parse_reference(self, text: str) -> Optional[Reference]:
        """解析单个参考文献"""
        # 提取年份
        year_match = re.search(r'(\d{4})', text)
        year = int(year_match.group(1)) if year_match else None

        # 提取作者（简化处理）
        authors = []
        author_match = re.match(r'^(?:\[\d+\]\s*)?([^.,]+)', text)
        if author_match:
            authors = [a.strip() for a in author_match.group(1).split(',')]

        # 提取标题（[]之间或引号之间的内容）
        title_match = re.search(r'["「]([^"」]+)["」]|\[([^\]]+)\]', text)
        title = title_match.group(1) or title_match.group(2) if title_match else "Unknown"

        # 提取期刊（通常在最）
        journal = "Unknown"
        if '[J]' in text:
            journal_match = re.search(r'\[J\]\.?\s*([^.,]+)', text)
            if journal_match:
                journal = journal_match.group(1)

        # 提取DOI
        doi_match = re.search(r'10\.\d{4,}/[^\s,]+', text)
        doi = doi_match.group(0) if doi_match else None

        return Reference(
            raw_text=text,
            authors=authors,
            title=title,
            year=year,
            journal=journal,
            doi=doi,
        )
```

### 3.4 AI分析器

```python
# ai_analyzer.py
from typing import List, Dict
from ..ai.llm_provider_v2 import LLMService, GenerationResult

class PDFAnalyzer:
    """PDF AI分析器"""

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def generate_summary(self, text: str, max_length: int = 500) -> str:
        """生成文献摘要"""
        # 截断文本避免超出token限制
        truncated = text[:15000] if len(text) > 15000 else text

        prompt = f"""请为以下学术论文生成一段简洁的摘要（{max_length}字以内）：

论文内容：
{truncated}

要求：
1. 概括研究背景和目的
2. 说明研究方法
3. 总结主要发现
4. 指出研究意义

摘要："""

        result = await self.llm.generate(
            prompt=prompt,
            max_tokens=max_length,
            temperature=0.3,
            system_prompt="你是一位专业的学术文献分析专家。",
        )
        return result.content

    async def extract_key_points(self, text: str) -> List[str]:
        """提取核心观点"""
        truncated = text[:15000] if len(text) > 15000 else text

        prompt = f"""请从以下论文中提取5-8个核心观点或关键发现：

论文内容：
{truncated}

请以JSON数组格式返回，例如：["观点1", "观点2", ...]

核心观点："""

        result = await self.llm.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.3,
        )

        # 尝试解析JSON
        try:
            import json
            points = json.loads(result.content)
            if isinstance(points, list):
                return points
        except:
            pass

        # 如果解析失败，按行分割
        return [line.strip('- ') for line in result.content.split('\n') if line.strip()]

    async def analyze_methodology(self, text: str) -> Dict:
        """分析研究方法"""
        truncated = text[:10000] if len(text) > 10000 else text

        prompt = f"""请分析以下论文的研究方法：

论文内容：
{truncated}

请用JSON格式返回：
{{
    "research_type": "研究类型（定性/定量/混合）",
    "data_collection": "数据收集方法",
    "sample_size": "样本量",
    "analysis_method": "分析方法",
    "tools": "使用的工具或软件"
}}

分析结果："""

        result = await self.llm.generate(
            prompt=prompt,
            max_tokens=800,
            temperature=0.3,
        )

        try:
            import json
            return json.loads(result.content)
        except:
            return {"raw_analysis": result.content}

    async def identify_research_gap(self, text: str) -> List[str]:
        """识别研究空白"""
        truncated = text[:10000] if len(text) > 10000 else text

        prompt = f"""请分析以下论文中指出的研究空白或未来研究方向：

论文内容：
{truncated}

请列出3-5个研究空白："""

        result = await self.llm.generate(
            prompt=prompt,
            max_tokens=800,
            temperature=0.4,
        )

        return [line.strip('- ') for line in result.content.split('\n') if line.strip()]
```

---

## 四、前端集成

### 4.1 PDF上传组件

```typescript
// components/pdf/PDFUploader.tsx
import React, { useState } from 'react'
import { Upload, message, Progress } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { pdfService } from '@/services'

const { Dragger } = Upload

export const PDFUploader: React.FC<{
  onParseComplete: (result: PDFParseResult) => void
}> = ({ onParseComplete }) => {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleUpload = async (file: File) => {
    setUploading(true)
    setProgress(0)

    try {
      // 上传PDF
      const uploadResult = await pdfService.upload(file, (p) => setProgress(p))

      // 开始解析
      message.loading('正在解析PDF，请稍候...', 0)
      const parseResult = await pdfService.parse(uploadResult.fileId)

      message.destroy()
      message.success('解析完成！')
      onParseComplete(parseResult)
    } catch (error) {
      message.error('解析失败：' + error.message)
    } finally {
      setUploading(false)
    }

    return false
  }

  return (
    <div>
      <Dragger
        beforeUpload={handleUpload}
        accept=".pdf"
        disabled={uploading}
        showUploadList={false}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽PDF文件到此处上传</p>
        <p className="ant-upload-hint">
          支持学术论文PDF，自动提取文本、参考文献和图表
        </p>
      </Dragger>
      {uploading && (
        <Progress percent={progress} status="active" />
      )}
    </div>
  )
}
```

---

## 五、实施建议

### 5.1 优先级排序

1. **高优先级**（立即实施）：
   - PDF文本提取服务
   - 参考文献自动解析
   - AI摘要生成

2. **中优先级**（1-2周）：
   - 图表提取和OCR
   - arXiv真实API对接
   - 文献综述生成功能

3. **低优先级**（后续版本）：
   - CNKI/IEEE付费API对接
   - 高级文献分析功能

### 5.2 依赖安装

```bash
# PDF处理
pip install PyMuPDF pdfplumber pdf2image

# OCR（可选）
pip install pytesseract paddleocr

# 异步任务队列（用于大文件处理）
pip install celery redis
```

### 5.3 配置更新

```env
# .env 文件新增
AI_PARSER_MAX_FILE_SIZE=50MB
AI_PARSER_TIMEOUT=300
OCR_ENABLED=true
```

---

## 六、预期效果

### 6.1 科研效率提升

| 功能 | 传统方式耗时 | 使用ScholarForge | 效率提升 |
|------|-------------|-----------------|---------|
| 文献阅读 | 30分钟/篇 | 5分钟（AI摘要） | 6倍 |
| 参考文献整理 | 1小时/10篇 | 自动提取 | 10倍 |
| 文献综述写作 | 1周 | 2天（AI辅助） | 3.5倍 |
| 论文排版 | 半天 | 一键排版 | 10倍 |

### 6.2 用户价值

1. **学生**：快速理解文献、自动生成综述、规范排版
2. **教师**：批量检查学生论文、快速评估研究质量
3. **研究人员**：文献管理、研究趋势分析、协作写作

---

**下一步行动**：开始实施 PDF 解析服务的核心代码开发。
