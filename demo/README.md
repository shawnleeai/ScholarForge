# ScholarForge 产品演示

本目录包含ScholarForge产品演示所需的脚本、数据和资源。

## 目录结构

```
demo/
├── README.md                   # 本文件
├── data/                       # 演示数据文件
│   ├── demo_user.json         # 演示用户信息（浙江大学MEM硕士生）
│   ├── demo_papers.json       # 演示论文数据
│   ├── demo_references.json   # 演示文献库（30篇核心文献）
│   └── sample_papers.json     # 示例论文数据
├── scripts/                    # 数据加载脚本
│   ├── demo_scenario.sql      # SQL初始化脚本
│   ├── demo_scenarios.md      # 演示脚本和场景
│   ├── load_demo_data.sh      # Linux/Mac加载脚本
│   ├── load_demo_data.ps1     # Windows加载脚本
│   └── seed_demo_data.py      # 数据种子脚本
├── presentation/               # 演示文稿
│   └── slides.html            # HTML演示文稿
└── assets/                     # 演示资源文件
    └── avatars/               # 用户头像
```

## 快速开始

### 1. 准备演示环境

```bash
# 1. 启动后端服务
cd backend
python -m services.gateway.main  # 主网关服务

# 2. 在另一个终端启动前端开发服务器
cd frontend
npm run dev
```

### 2. 加载演示数据

```bash
# 运行数据种子脚本（首次使用）
python scripts/seed_demo_data.py

# 如需重置演示数据
python scripts/seed_demo_data.py --reset
```

### 3. 开始演示

#### 方式一：HTML演示文稿（推荐用于路演）

```bash
# 直接在浏览器中打开演示文稿
open demo/presentation/slides.html
```

演示文稿特性：
- 键盘导航：方向键或空格切换幻灯片
- 触摸滑动：移动端支持左右滑动
- 全屏模式：点击全屏按钮或按 F11
- 响应式设计：适配各种屏幕尺寸

#### 方式二：交互式产品导览（推荐用于用户引导）

使用以下账号登录演示环境：
- **邮箱**: demo@scholarforge.io
- **密码**: Demo123456

登录后，在Dashboard页面点击"开始使用"按钮启动交互式导览。

## 演示场景

### 场景一：文献发现与管理 (5分钟)
展示每日推荐、智能搜索和文献管理功能

**关键功能点**：
- 每日论文推荐卡片（基于用户兴趣）
- 语义搜索（自然语言查询）
- 文献库管理（标签、收藏夹）
- PDF阅读和批注

### 场景二：AI研究助手 (5分钟)
展示研究问答、文献综述生成和多轮对话

**关键功能点**：
- 研究问答（基于文献库）
- 文献综述生成
- 多轮对话和追问
- 对比表格生成

### 场景三：论文写作 (5分钟)
展示大纲生成、AI写作辅助和引用管理

**关键功能点**：
- 智能大纲生成
- AI续写和润色
- 智能引用推荐
- 查重和格式检查

### 场景四：协作与分享 (3分钟)
展示团队管理、实时协作和成果分享

**关键功能点**：
- 团队邀请和管理
- 实时协作编辑
- 评论和批注
- 版本历史

### 场景五：研究数据与可视化 (2分钟)
展示知识图谱和研究分析

**关键功能点**：
- 文献知识图谱
- 引用趋势分析
- 研究热点词云
- 个人学术影响力

## 演示技巧

1. **提前准备**: 确保网络稳定，提前加载所有页面
2. **备用方案**: 准备截图作为API故障时的备用
3. **互动**: 鼓励观众提问，展示相关功能
4. **时间控制**: 每个场景严格控制在时间内

## 常见问题

**Q: AI响应慢怎么办？**
A: 可以使用预录制的响应，或提前运行一次让系统预热。

**Q: API故障怎么办？**
A: 切换到离线演示模式，使用本地模拟数据。

**Q: 如何自定义演示数据？**
A: 修改 `data/sample_papers.json` 文件，添加自己的论文数据。

## 交互式导览组件

### GuidedTour 组件

位于 `frontend/src/components/demo/GuidedTour.tsx`

**功能**：
- 步骤引导：分步骤展示产品功能
- 元素高亮：自动高亮目标元素
- 智能定位：自动计算提示框位置
- 边界检测：防止提示框超出屏幕
- 导航控制：上一步/下一步/跳过/完成

**使用方式**：
```tsx
import { DemoLauncher } from '@/components/demo'

// 在Dashboard页面添加启动按钮
<DemoLauncher />
```

### DemoProvider

位于 `frontend/src/components/demo/DemoProvider.tsx`

**功能**：
- 全局演示状态管理
- 演示数据提供
- 步骤控制逻辑
- 事件追踪（可选）

**使用方式**：
```tsx
import { DemoProvider, useDemo } from '@/components/demo'

// 在App.tsx中包装应用
<DemoProvider>
  <App />
</DemoProvider>

// 在组件中使用
const { isDemoMode, startDemo, endDemo } = useDemo()
```

## 演示文稿

### HTML演示文稿

位于 `demo/presentation/slides.html`

**特性**：
- 8张精美幻灯片，涵盖产品全貌
- 键盘/触摸/鼠标导航
- 响应式设计，支持移动设备
- 动画效果和过渡
- 全屏模式支持

**幻灯片内容**：
1. 封面 - 产品概述和价值主张
2. 痛点 - 研究人员面临的挑战
3. 解决方案 - ScholarForge如何解决这些问题
4. 核心功能1 - 文献发现
5. 核心功能2 - AI研究助手
6. 核心功能3 - 论文写作
7. 技术架构 - 技术栈和实现
8. 行动号召 - 开始试用

## 演示数据

### 数据文件

位于 `demo/data/sample_papers.json`

**包含**：
- 8篇AI/ML领域经典论文（Transformer、BERT、GPT-3等）
- 3个示例收藏夹
- 用户画像数据

### 种子脚本

位于 `scripts/seed_demo_data.py`

**功能**：
- 创建演示用户
- 导入论文数据
- 创建收藏夹和兴趣标签
- 生成每日推荐数据
- 创建示例对话

## 自定义演示

### 添加自定义演示步骤

编辑 `frontend/src/components/demo/demoData.ts`：

```typescript
export const demoSteps: DemoStep[] = [
  {
    id: 'your-step',
    target: '.your-element-class',  // CSS选择器
    title: '步骤标题',
    content: '步骤说明内容',
    placement: 'bottom',  // top/bottom/left/right
    action: () => {
      // 可选：步骤切换时执行的动作
    }
  },
  // ...
]
```

### 修改演示数据

编辑 `demo/data/sample_papers.json` 添加自己的论文数据。

### 自定义演示文稿

编辑 `demo/presentation/slides.html` 修改幻灯片内容和样式。

## 演示技巧

1. **提前准备**: 确保网络稳定，提前加载所有页面
2. **备用方案**: 准备截图作为API故障时的备用
3. **互动**: 鼓励观众提问，展示相关功能
4. **时间控制**: 每个场景严格控制在时间内

## 常见问题

**Q: AI响应慢怎么办？**
A: 可以使用预录制的响应，或提前运行一次让系统预热。

**Q: API故障怎么办？**
A: 切换到离线演示模式，使用本地模拟数据。

**Q: 如何自定义演示数据？**
A: 修改 `data/sample_papers.json` 文件，添加自己的论文数据。

**Q: 如何修改演示步骤？**
A: 编辑 `frontend/src/components/demo/demoData.ts` 文件。

**Q: 演示数据加载失败怎么办？**
A: 检查数据库连接，确保PostgreSQL/MySQL服务正常运行，然后重新运行 `python scripts/seed_demo_data.py`。

## 联系支持

演示问题请联系：support@scholarforge.io

---

**Last Updated**: 2024
**Version**: 1.0.0
