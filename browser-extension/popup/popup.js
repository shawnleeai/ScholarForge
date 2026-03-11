/**
 * ScholarForge 浏览器扩展 - 弹出窗口
 * 快速导入和常用功能入口
 */

// 状态
let currentTab = null;
let isImporting = false;

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
  await initialize();
  setupEventListeners();
});

// 初始化
async function initialize() {
  try {
    // 获取当前标签页
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tabs[0];

    // 更新页面信息
    updatePageInfo();

    // 加载最近导入
    loadRecentImports();
  } catch (error) {
    console.error('初始化失败:', error);
  }
}

// 更新页面信息
function updatePageInfo() {
  if (currentTab) {
    document.getElementById('page-title').textContent = currentTab.title || '未知页面';
    document.getElementById('page-url').textContent = currentTab.url || '';
  }
}

// 设置事件监听器
function setupEventListeners() {
  // 导入按钮
  document.getElementById('import-btn').addEventListener('click', handleImport);

  // 笔记按钮
  document.getElementById('note-btn').addEventListener('click', () => {
    openSidebar('notes');
  });

  // 引用按钮
  document.getElementById('cite-btn').addEventListener('click', handleCopyCitation);

  // 侧边栏按钮
  document.getElementById('sidebar-btn').addEventListener('click', () => {
    toggleSidebar();
  });

  // 查看全部按钮
  document.getElementById('view-all-btn').addEventListener('click', () => {
    openScholarForge('/library');
  });

  // 设置按钮
  document.getElementById('settings-btn').addEventListener('click', () => {
    openScholarForge('/settings');
  });

  // 帮助按钮
  document.getElementById('help-btn').addEventListener('click', () => {
    openScholarForge('/help');
  });
}

// 处理导入
async function handleImport() {
  if (isImporting) return;

  isImporting = true;
  showImportStatus(true);

  try {
    // 向内容脚本发送提取请求
    const response = await chrome.tabs.sendMessage(currentTab.id, {
      action: 'extract-article'
    });

    if (response && response.success) {
      // 保存到 ScholarForge
      const result = await sendToBackground({
        action: 'import-article',
        data: {
          url: currentTab.url,
          title: response.data.title,
          authors: response.data.authors,
          abstract: response.data.abstract,
          keywords: response.data.keywords,
          journal: response.data.journal,
          year: response.data.year,
          doi: response.data.doi,
          pdf_url: response.data.pdfUrl,
          source: 'browser_extension'
        }
      });

      if (result.success) {
        showToast('导入成功！', 'success');
        addToRecentImports({
          title: response.data.title,
          url: currentTab.url,
          timestamp: new Date().toISOString()
        });
      } else {
        showToast('导入失败: ' + result.error, 'error');
      }
    } else {
      showToast('无法提取页面信息', 'error');
    }
  } catch (error) {
    console.error('导入失败:', error);
    showToast('导入失败: ' + error.message, 'error');
  } finally {
    isImporting = false;
    showImportStatus(false);
  }
}

// 复制引用
async function handleCopyCitation() {
  try {
    const response = await chrome.tabs.sendMessage(currentTab.id, {
      action: 'extract-article'
    });

    if (response && response.success) {
      const citation = generateCitation(response.data);
      await navigator.clipboard.writeText(citation);
      showToast('引用已复制到剪贴板', 'success');
    } else {
      showToast('无法获取文献信息', 'error');
    }
  } catch (error) {
    console.error('复制引用失败:', error);
    showToast('复制失败', 'error');
  }
}

// 生成引用
function generateCitation(data) {
  const authors = data.authors?.join(', ') || 'Unknown';
  const year = data.year || new Date().getFullYear();
  const title = data.title || '';
  const journal = data.journal || '';

  return `${authors} (${year}). ${title}. ${journal}.`;
}

// 切换侧边栏
async function toggleSidebar() {
  try {
    await chrome.tabs.sendMessage(currentTab.id, {
      action: 'toggle-sidebar'
    });
    window.close();
  } catch (error) {
    console.error('切换侧边栏失败:', error);
  }
}

// 打开侧边栏特定标签
async function openSidebar(tab) {
  try {
    await chrome.tabs.sendMessage(currentTab.id, {
      action: 'open-sidebar-tab',
      tab: tab
    });
    window.close();
  } catch (error) {
    console.error('打开侧边栏失败:', error);
  }
}

// 打开 ScholarForge
function openScholarForge(path) {
  chrome.tabs.create({
    url: `http://localhost:3000${path}`
  });
}

// 显示导入状态
function showImportStatus(show) {
  const statusEl = document.getElementById('import-status');
  statusEl.style.display = show ? 'block' : 'none';
}

// 显示提示
function showToast(message, type) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}

// 发送到后台
async function sendToBackground(message) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(message, resolve);
  });
}

// 加载最近导入
async function loadRecentImports() {
  try {
    const storage = await chrome.storage.local.get('recent_imports');
    const imports = storage.recent_imports || [];

    const listEl = document.getElementById('imports-list');

    if (imports.length === 0) {
      listEl.innerHTML = '<div class="empty-state">暂无导入记录</div>';
      return;
    }

    listEl.innerHTML = imports.slice(0, 3).map(item => `
      <div class="import-item" data-url="${item.url}">
        <div class="import-title">${escapeHtml(item.title)}</div>
        <div class="import-meta">${formatTime(item.timestamp)}</div>
      </div>
    `).join('');

    // 添加点击事件
    listEl.querySelectorAll('.import-item').forEach(item => {
      item.addEventListener('click', () => {
        chrome.tabs.create({ url: item.dataset.url });
      });
    });
  } catch (error) {
    console.error('加载最近导入失败:', error);
  }
}

// 添加到最近导入
async function addToRecentImports(item) {
  try {
    const storage = await chrome.storage.local.get('recent_imports');
    let imports = storage.recent_imports || [];

    // 去重
    imports = imports.filter(i => i.url !== item.url);

    // 添加新项
    imports.unshift(item);

    // 限制数量
    imports = imports.slice(0, 10);

    await chrome.storage.local.set({ recent_imports: imports });
    loadRecentImports();
  } catch (error) {
    console.error('保存最近导入失败:', error);
  }
}

// 转义 HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 格式化时间
function formatTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;

  return date.toLocaleDateString('zh-CN');
}
