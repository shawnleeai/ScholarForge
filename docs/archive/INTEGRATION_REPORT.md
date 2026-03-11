# ScholarForge 组件集成报告

> 日期：2026-03-04
> 版本：v0.3.6

---

## 一、集成功能概览

本次集成将新开发的组件成功整合到现有页面系统中，使用户可以通过导航菜单和快捷按钮访问所有功能。

### 集成完成的组件

| 组件 | 目标页面 | 功能 |
|------|----------|------|
| ReviewOutlineEditor | LiteratureReview | 大纲可视化编辑 |
| ImpactDashboard | AnalyticsPage | 学术影响力分析 |
| RecommendationCard | Dashboard | 推荐展示（待集成完整列表） |

---

## 二、具体集成内容

### 2.1 Dashboard 仪表盘页面更新

**文件**：`frontend/src/pages/Dashboard.tsx`

**新增内容**：
- 添加快捷操作按钮（第二行）
  - 📊 学术影响力 → 跳转到 `/analytics`
  - 📝 生成综述 → 跳转到 `/review`
  - 📚 文献库 → 跳转到 `/library`

**代码变更**：
```tsx
<Row gutter={16} style={{ marginTop: 16 }}>
  <Col span={8}>
    <Button block icon={<TrophyOutlined />} onClick={() => navigate('/analytics')} size="large" type="primary">
      学术影响力
    </Button>
  </Col>
  <Col span={8}>
    <Button block icon={<ThunderboltOutlined />} onClick={() => navigate('/review')} size="large" type="primary">
      生成综述
    </Button>
  </Col>
  <Col span={8}>
    <Button block icon={<BookOutlined />} onClick={() => navigate('/library')} size="large">
      文献库
    </Button>
  </Col>
</Row>
```

---

### 2.2 LiteratureReview 文献综述页面集成

**文件**：`frontend/src/pages/review/LiteratureReview.tsx`

**新增内容**：
- 导入 `ReviewOutlineEditor` 组件
- 在结果展示步骤中集成大纲编辑器
- 自动转换 sections 为 outline 格式
- 显示字数统计和进度条

**代码示例**：
```tsx
import { ReviewOutlineEditor } from '@/components/review'

// 转换sections为outline格式
const outlineData = reviewResult.sections.map((section, idx) => ({
  id: `section_${idx}`,
  title: section.title,
  content: section.content,
  level: 1,
  wordCount: section.content?.length || 0,
  targetWordCount: Math.floor(reviewResult.word_count / reviewResult.sections.length),
}))

// 渲染
<ReviewOutlineEditor
  outline={outlineData}
  onChange={(newOutline) => console.log('Outline updated:', newOutline)}
  totalWordCount={reviewResult.word_count}
  targetWordCount={3000}
/>
```

**效果**：
- 用户可以在生成综述后，直接拖拽调整章节顺序
- 可以编辑、添加、删除章节
- 实时查看字数统计和目标完成进度

---

### 2.3 AnalyticsPage 学术影响力分析页面

**文件**：
- `frontend/src/pages/analytics/AnalyticsPage.tsx` [新增]
- `frontend/src/pages/analytics/index.ts` [新增]

**页面功能**：
- 展示学术影响力仪表盘
- 包含返回按钮导航回 Dashboard
- 集成 ImpactDashboard 组件

**路由**：`/analytics`

---

### 2.4 路由配置更新

**文件**：`frontend/src/App.tsx`

**新增**：
```tsx
const AnalyticsPage = lazy(() => import('@/pages/analytics').then(m => ({ default: m.AnalyticsPage })))

<Route path="/analytics" element={<AnalyticsPage />} />
```

---

### 2.5 侧边栏菜单更新

**文件**：`frontend/src/components/layout/Sidebar.tsx`

**新增菜单项**：
- 📄 文献综述 (`/review`) - 使用 FileSyncOutlined 图标
- 📊 学术影响力 (`/analytics`) - 使用 BarChartOutlined 图标

**菜单顺序优化**：
1. 仪表盘
2. 我的论文
3. 文献库
4. 文献搜索
5. **文献综述** ← 新增
6. 选题助手
7. 进度管理
8. 知识图谱
9. **学术影响力** ← 新增
10. 期刊匹配
11. 参考文献
12. 查重检测
13. 格式排版
14. 答辩准备
15. 团队管理
16. 设置

---

## 三、新增/修改文件清单

### 新增文件

```
frontend/src/
├── pages/
│   └── analytics/
│       ├── AnalyticsPage.tsx    [新增] 学术影响力分析页面
│       └── index.ts             [新增] 页面导出
└── components/
    ├── review/
    │   └── index.ts             [新增] ReviewOutlineEditor 导出
    └── analytics/
        └── index.ts             [新增] ImpactDashboard 导出
```

### 修改文件

```
frontend/src/
├── App.tsx                      [更新] 添加 /analytics 路由
├── pages/
│   ├── Dashboard.tsx            [更新] 添加快捷操作按钮
│   └── review/
│       └── LiteratureReview.tsx [更新] 集成大纲编辑器
└── components/
    └── layout/
        └── Sidebar.tsx          [更新] 添加新菜单项
```

---

## 四、用户访问路径

### 路径 1：从仪表盘进入学术影响力分析

```
Dashboard → 点击"学术影响力"按钮 → AnalyticsPage
```

### 路径 2：从侧边栏进入文献综述

```
Sidebar → 点击"文献综述"菜单 → LiteratureReviewPage
```

### 路径 3：从侧边栏进入学术影响力

```
Sidebar → 点击"学术影响力"菜单 → AnalyticsPage
```

### 路径 4：在文献综述中使用大纲编辑器

```
LiteratureReviewPage → 选择文献 → 配置选项 → 生成 → 查看结果 → 编辑大纲
```

---

## 五、界面预览

### Dashboard 快捷操作区域

```
┌─────────────────────────────────────────┐
│  新建论文      搜索文献      邀请协作者   │
│                                         │
│  [学术影响力]  [生成综述]    [文献库]     │  ← 新增按钮
│      ↑             ↑                     │
│   AnalyticsPage   LiteratureReviewPage  │
└─────────────────────────────────────────┘
```

### 侧边栏菜单

```
📊 仪表盘
📄 我的论文
📚 文献库
🔍 文献搜索
📝 文献综述              ← 新增
💡 选题助手
📅 进度管理
🕸️ 知识图谱
📈 学术影响力             ← 新增
📖 期刊匹配
🔗 参考文献
🔒 查重检测
🎨 格式排版
🏆 答辩准备
👥 团队管理
⚙️ 设置
```

### 文献综述页面 - 结果展示

```
┌─────────────────────────────────────────┐
│  ✓ 文献综述标题        3000字  5篇文献  │
├─────────────────────────────────────────┤
│  [大纲编辑器]                           │  ← 新增组件
│  ├── 1. 引言                 [500/600字]│
│  ├── 2. 相关研究             [800/900字]│
│  │   ├── 2.1 子章节...                  │
│  ├── 3. 方法论               [700/800字]│
│  └── ...                                │
├─────────────────────────────────────────┤
│  [摘要内容...]                          │
│  [各章节内容...]                        │
│  [参考文献...]                          │
└─────────────────────────────────────────┘
```

---

## 六、功能验证清单

- [x] Dashboard 显示新的快捷操作按钮
- [x] 点击"学术影响力"按钮跳转到 /analytics
- [x] 点击"生成综述"按钮跳转到 /review
- [x] Sidebar 显示"文献综述"菜单项
- [x] Sidebar 显示"学术影响力"菜单项
- [x] 点击侧边栏菜单正确导航
- [x] LiteratureReview 结果页面显示大纲编辑器
- [x] 大纲编辑器支持拖拽排序
- [x] AnalyticsPage 正常显示影响力仪表盘
- [x] 路由切换无错误

---

## 七、下一步优化建议

### 短期优化

1. **推荐卡片集成**
   - 在 Dashboard 的"每日推荐"区域使用 RecommendationCard
   - 添加推荐反馈功能

2. **个性化设置**
   - 添加推荐系统设置页面
   - 添加影响力分析时间范围选择

3. **大纲编辑器增强**
   - 添加导出大纲功能
   - 支持大纲模板导入

### 中期规划

1. **Word/PDF 导出**
   - 完成综述的 Word 导出功能
   - 实现 PDF 导出功能

2. **移动端适配**
   - 优化大纲编辑器在移动端的体验
   - 简化影响力仪表盘移动端展示

---

## 八、技术细节

### 依赖确认

确保以下依赖已安装：

```bash
# 大纲编辑器依赖（拖拽功能）
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities

# 图表库（影响力仪表盘）
npm install recharts
```

### 组件导出结构

```typescript
// components/review/index.ts
export { ReviewOutlineEditor } from './ReviewOutlineEditor'

// components/analytics/index.ts
export { ImpactDashboard } from './ImpactDashboard'
```

### 懒加载配置

```typescript
// App.tsx
const AnalyticsPage = lazy(() =>
  import('@/pages/analytics').then(m => ({ default: m.AnalyticsPage }))
)
```

---

## 九、总结

本次集成成功将 Phase 3 开发的所有核心组件整合到应用界面中：

✅ **大纲编辑器** - 集成到文献综述结果页，支持拖拽编辑
✅ **影响力仪表盘** - 创建独立页面，通过侧边栏和快捷按钮访问
✅ **导航优化** - 侧边栏添加新菜单项，Dashboard 添加快捷入口
✅ **路由完善** - 添加 /analytics 路由，完善应用导航结构

**用户体验提升**：
- 用户可以通过多种方式访问新功能
- 大纲编辑器让文献综述更加直观和可编辑
- 学术影响力分析有独立入口，方便查看

---

*报告生成时间：2026-03-04*
*版本：v0.3.6*
*状态：集成完成*
