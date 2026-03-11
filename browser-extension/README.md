# ScholarForge 浏览器扩展

## 安装说明

### 开发者模式安装

1. 打开 Chrome/Edge 浏览器，进入扩展管理页面:
   - Chrome: `chrome://extensions/`
   - Edge: `edge://extensions/`

2. 开启右上角的"开发者模式"

3. 点击"加载已解压的扩展程序"

4. 选择 `browser-extension` 文件夹

5. 扩展安装成功，浏览器工具栏会显示 ScholarForge 图标

### 图标文件

在 `icons/` 目录下放置以下图标文件:
- `icon16.png` - 16x16 像素
- `icon48.png` - 48x48 像素
- `icon128.png` - 128x128 像素

可以使用项目 logo 或生成简单的渐变色图标。

## 功能特性

### 1. 上下文菜单
- 📄 导入当前页面 - 从学术网站提取文献信息并导入
- 📝 导入选中内容为笔记 - 将选中的文本保存为笔记
- 🔗 导入链接文献 - 添加链接到待导入列表
- 📚 打开侧边栏 - 快速打开学术助手侧边栏
- 🔍 快速搜索 - 搜索选中的文本

### 2. 弹出窗口
- 当前页面信息展示
- 快速导入按钮
- 最近导入历史
- 快捷键提示

### 3. 侧边栏
- **文献库**: 当前页面信息、相关文献推荐
- **笔记**: 快速笔记、页面笔记管理
- **引用**: 多种引用格式( APA, MLA, Chicago, GB/T )
- **AI助手**: 智能问答、文章总结、写作建议
- **工具**: 翻译、定义、摘要、高亮、截图、导出

### 4. 快捷键
- `Ctrl+Shift+S` / `Cmd+Shift+S` - 切换侧边栏
- `Ctrl+Shift+I` / `Cmd+Shift+I` - 快速导入当前页面

## 支持的学术网站

- Google Scholar
- PubMed
- arXiv
- IEEE Xplore
- ACM Digital Library
- Springer
- Nature
- ScienceDirect
- Science
- Wiley Online Library
- Taylor & Francis
- JSTOR
- 以及支持标准 meta 标签的其他学术网站

## 配置选项

点击扩展弹出窗口的设置按钮，可以配置:
- API 服务器地址
- 自动提取设置
- 通知偏好
- 主题选择

## 开发调试

1. 修改代码后，在扩展管理页面点击刷新按钮
2. 查看控制台输出: 右键点击扩展图标 -> 检查弹出内容
3. 查看后台页面: 扩展详情 -> 背景页 -> 检查视图

## 注意事项

- 扩展需要连接到运行中的 ScholarForge 后端服务
- 默认 API 地址: `http://localhost:8000/api/v1`
- 部分功能需要登录 ScholarForge 账号
