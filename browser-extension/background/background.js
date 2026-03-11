/**
 * ScholarForge 浏览器扩展 - 后台服务
 * 处理消息通信、上下文菜单、存储管理
 */

// 配置
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000/api/v1',
  STORAGE_KEY: 'scholarforge_config'
};

// 初始化
chrome.runtime.onInstalled.addListener((details) => {
  console.log('ScholarForge 扩展已安装', details);

  // 创建上下文菜单
  createContextMenus();

  // 初始化存储
  initializeStorage();
});

// 创建上下文菜单
function createContextMenus() {
  // 移除现有菜单
  chrome.contextMenus.removeAll(() => {
    // 添加主菜单
    chrome.contextMenus.create({
      id: 'scholarforge-main',
      title: 'ScholarForge 学术助手',
      contexts: ['all']
    });

    // 添加子菜单项
    chrome.contextMenus.create({
      id: 'import-page',
      parentId: 'scholarforge-main',
      title: '📄 导入当前页面',
      contexts: ['page']
    });

    chrome.contextMenus.create({
      id: 'import-selection',
      parentId: 'scholarforge-main',
      title: '📝 导入选中内容为笔记',
      contexts: ['selection']
    });

    chrome.contextMenus.create({
      id: 'import-link',
      parentId: 'scholarforge-main',
      title: '🔗 导入链接文献',
      contexts: ['link']
    });

    chrome.contextMenus.create({
      id: 'separator-1',
      parentId: 'scholarforge-main',
      type: 'separator',
      contexts: ['all']
    });

    chrome.contextMenus.create({
      id: 'open-sidebar',
      parentId: 'scholarforge-main',
      title: '📚 打开侧边栏',
      contexts: ['all']
    });

    chrome.contextMenus.create({
      id: 'quick-search',
      parentId: 'scholarforge-main',
      title: '🔍 快速搜索',
      contexts: ['selection']
    });
  });
}

// 初始化存储
async function initializeStorage() {
  const defaultConfig = {
    apiUrl: CONFIG.API_BASE_URL,
    autoExtract: true,
    showNotifications: true,
    sidebarEnabled: true,
    theme: 'light'
  };

  const existing = await chrome.storage.sync.get(CONFIG.STORAGE_KEY);
  if (!existing[CONFIG.STORAGE_KEY]) {
    await chrome.storage.sync.set({ [CONFIG.STORAGE_KEY]: defaultConfig });
  }
}

// 处理上下文菜单点击
chrome.contextMenus.onClicked.addListener((info, tab) => {
  switch (info.menuItemId) {
    case 'import-page':
      importCurrentPage(tab);
      break;
    case 'import-selection':
      importSelection(tab, info.selectionText);
      break;
    case 'import-link':
      importLink(tab, info.linkUrl);
      break;
    case 'open-sidebar':
      toggleSidebar(tab);
      break;
    case 'quick-search':
      quickSearch(info.selectionText);
      break;
  }
});

// 处理快捷键命令
chrome.commands.onCommand.addListener((command, tab) => {
  switch (command) {
    case 'toggle-sidebar':
      toggleSidebar(tab);
      break;
    case 'quick-import':
      importCurrentPage(tab);
      break;
  }
});

// 导入当前页面
async function importCurrentPage(tab) {
  try {
    // 向内容脚本发送消息，提取页面信息
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'extract-article'
    });

    if (response && response.success) {
      // 发送到 ScholarForge API
      const result = await sendToScholarForge('/articles/import', {
        url: tab.url,
        title: response.data.title,
        authors: response.data.authors,
        abstract: response.data.abstract,
        keywords: response.data.keywords,
        journal: response.data.journal,
        year: response.data.year,
        doi: response.data.doi,
        source: 'browser_extension'
      });

      showNotification('导入成功', `已导入: ${response.data.title.substring(0, 50)}...`);
    } else {
      showNotification('导入失败', '无法提取页面信息');
    }
  } catch (error) {
    console.error('导入失败:', error);
    showNotification('导入失败', error.message);
  }
}

// 导入选中的内容
async function importSelection(tab, selectionText) {
  try {
    // 获取页面上下文
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'get-selection-context',
      selection: selectionText
    });

    // 创建笔记
    await sendToScholarForge('/notes/quick', {
      content: selectionText,
      source_url: tab.url,
      source_title: tab.title,
      context: response?.context || '',
      created_at: new Date().toISOString()
    });

    showNotification('笔记已保存', '选中的内容已保存到 ScholarForge');
  } catch (error) {
    console.error('保存笔记失败:', error);
    showNotification('保存失败', error.message);
  }
}

// 导入链接
async function importLink(tab, linkUrl) {
  try {
    // 获取链接信息
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'extract-link',
      url: linkUrl
    });

    await sendToScholarForge('/articles/import', {
      url: linkUrl,
      title: response?.data?.title || linkUrl,
      source: 'browser_extension_link'
    });

    showNotification('链接已添加', '文献链接已添加到待导入列表');
  } catch (error) {
    console.error('导入链接失败:', error);
    showNotification('导入失败', error.message);
  }
}

// 切换侧边栏
async function toggleSidebar(tab) {
  try {
    await chrome.tabs.sendMessage(tab.id, { action: 'toggle-sidebar' });
  } catch (error) {
    console.error('切换侧边栏失败:', error);
  }
}

// 快速搜索
function quickSearch(query) {
  const searchUrl = `${CONFIG.API_BASE_URL}/search?q=${encodeURIComponent(query)}`;
  chrome.tabs.create({ url: searchUrl });
}

// 发送到 ScholarForge API
async function sendToScholarForge(endpoint, data) {
  const config = await chrome.storage.sync.get(CONFIG.STORAGE_KEY);
  const apiUrl = config[CONFIG.STORAGE_KEY]?.apiUrl || CONFIG.API_BASE_URL;

  const response = await fetch(`${apiUrl}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Extension-Version': chrome.runtime.getManifest().version
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`API 请求失败: ${response.status}`);
  }

  return response.json();
}

// 显示通知
function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: title,
    message: message
  });
}

// 监听来自内容脚本和弹出窗口的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  handleMessage(request, sender, sendResponse);
  return true; // 保持消息通道开放
});

// 消息处理器
async function handleMessage(request, sender, sendResponse) {
  switch (request.action) {
    case 'get-config':
      const config = await chrome.storage.sync.get(CONFIG.STORAGE_KEY);
      sendResponse({ success: true, data: config[CONFIG.STORAGE_KEY] });
      break;

    case 'save-config':
      await chrome.storage.sync.set({ [CONFIG.STORAGE_KEY]: request.config });
      sendResponse({ success: true });
      break;

    case 'api-request':
      try {
        const result = await sendToScholarForge(request.endpoint, request.data);
        sendResponse({ success: true, data: result });
      } catch (error) {
        sendResponse({ success: false, error: error.message });
      }
      break;

    case 'import-article':
      try {
        const result = await sendToScholarForge('/articles/import', request.data);
        sendResponse({ success: true, data: result });
        showNotification('导入成功', '文献已成功导入 ScholarForge');
      } catch (error) {
        sendResponse({ success: false, error: error.message });
      }
      break;

    default:
      sendResponse({ success: false, error: '未知操作' });
  }
}

console.log('ScholarForge 后台服务已启动');
