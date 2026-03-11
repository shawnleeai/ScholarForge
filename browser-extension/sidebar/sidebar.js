/**
 * ScholarForge 浏览器扩展 - 侧边栏
 * 多功能学术助手侧边栏
 */

// 状态
let currentTab = null;
let currentPageInfo = null;
let activeTab = 'library';
let citations = [];
let currentFormat = 'apa';

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
  await initialize();
  setupEventListeners();
});

// 初始化
async function initialize() {
  try {
    // 获取当前页面信息
    const response = await sendToContent({ action: 'get-page-info' });
    if (response && response.success) {
      currentPageInfo = response.data;
      await loadCurrentPageArticle();
    }

    // 加载笔记
    loadPageNotes();

    // 更新引用格式
    updateCitationFormat();
  } catch (error) {
    console.error('初始化失败:', error);
  }
}

// 设置事件监听器
function setupEventListeners() {
  // 关闭按钮
  document.getElementById('close-btn').addEventListener('click', () => {
    sendToContent({ action: 'toggle-sidebar' });
  });

  // 标签切换
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      switchTab(tab);
    });
  });

  // 导入当前页面
  document.getElementById('import-current-btn').addEventListener('click', importCurrentPage);

  // 保存笔记
  document.getElementById('save-note-btn').addEventListener('click', saveNote);

  // 引用格式切换
  document.querySelectorAll('.format-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFormat = btn.dataset.format;
      updateCitationFormat();
    });
  });

  // 复制引用
  document.getElementById('copy-citation-btn').addEventListener('click', copyCitation);

  // AI 快速提示
  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      sendAIMessage(chip.dataset.prompt);
    });
  });

  // 发送消息
  document.getElementById('send-btn').addEventListener('click', () => {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (message) {
      sendAIMessage(message);
      input.value = '';
    }
  });

  // 回车发送
  document.getElementById('chat-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      document.getElementById('send-btn').click();
    }
  });

  // 工具按钮
  document.getElementById('tool-translate').addEventListener('click', () => useTool('translate'));
  document.getElementById('tool-define').addEventListener('click', () => useTool('define'));
  document.getElementById('tool-summarize').addEventListener('click', () => useTool('summarize'));
  document.getElementById('tool-highlight').addEventListener('click', () => useTool('highlight'));
  document.getElementById('tool-screenshot').addEventListener('click', () => useTool('screenshot'));
  document.getElementById('tool-export').addEventListener('click', () => useTool('export'));

  // 底部按钮
  document.getElementById('open-app-btn').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000' });
  });

  document.getElementById('settings-btn').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/settings' });
  });
}

// 切换标签
function switchTab(tab) {
  activeTab = tab;

  // 更新按钮状态
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });

  // 更新面板显示
  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.remove('active');
  });
  document.getElementById(`panel-${tab}`).classList.add('active');
}

// 加载当前页面文献
async function loadCurrentPageArticle() {
  try {
    const response = await sendToContent({ action: 'extract-article' });
    const cardEl = document.getElementById('current-page-card');

    if (response && response.success && response.data.title) {
      const data = response.data;
      cardEl.innerHTML = `
        <div class="article-card">
          <div class="article-title">${escapeHtml(data.title)}</div>
          ${data.authors?.length ? `<div class="article-meta">${data.authors.join(', ')}</div>` : ''}
          ${data.journal ? `<div class="article-meta">${data.journal}${data.year ? `, ${data.year}` : ''}</div>` : ''}
          ${data.doi ? `<div class="article-meta">DOI: ${data.doi}</div>` : ''}
          ${data.keywords?.length ? `
            <div class="article-tags">
              ${data.keywords.slice(0, 5).map(k => `<span class="article-tag">${escapeHtml(k)}</span>`).join('')}
            </div>
          ` : ''}
        </div>
      `;

      // 更新引用数据
      updateCitations(data);
    } else {
      cardEl.innerHTML = `
        <div class="page-placeholder">
          <span class="placeholder-icon">📄</span>
          <p>无法获取页面信息</p>
          <p style="font-size: 12px; margin-top: 8px;">请访问学术文献页面</p>
        </div>
      `;
    }
  } catch (error) {
    console.error('加载页面信息失败:', error);
  }
}

// 导入当前页面
async function importCurrentPage() {
  const btn = document.getElementById('import-current-btn');
  btn.disabled = true;
  btn.textContent = '导入中...';

  try {
    const response = await sendToContent({ action: 'extract-article' });

    if (response && response.success) {
      const result = await sendToBackground({
        action: 'import-article',
        data: {
          url: currentPageInfo?.url,
          ...response.data,
          source: 'browser_extension_sidebar'
        }
      });

      if (result.success) {
        btn.textContent = '✓ 已导入';
        setTimeout(() => {
          btn.disabled = false;
          btn.textContent = '📥 导入';
        }, 2000);
      } else {
        throw new Error(result.error);
      }
    }
  } catch (error) {
    console.error('导入失败:', error);
    btn.textContent = '导入失败';
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = '📥 导入';
    }, 2000);
  }
}

// 保存笔记
async function saveNote() {
  const input = document.getElementById('note-input');
  const tagSelect = document.getElementById('note-tag');
  const content = input.value.trim();

  if (!content) return;

  const note = {
    id: Date.now(),
    content,
    tag: tagSelect.value,
    url: currentPageInfo?.url,
    timestamp: new Date().toISOString()
  };

  // 保存到本地存储
  const storage = await chrome.storage.local.get('page_notes');
  const notes = storage.page_notes || {};
  const url = currentPageInfo?.url || 'general';

  if (!notes[url]) notes[url] = [];
  notes[url].unshift(note);

  await chrome.storage.local.set({ page_notes: notes });

  // 清空输入
  input.value = '';
  tagSelect.value = '';

  // 刷新笔记列表
  loadPageNotes();
}

// 加载页面笔记
async function loadPageNotes() {
  try {
    const storage = await chrome.storage.local.get('page_notes');
    const notes = storage.page_notes || {};
    const url = currentPageInfo?.url;
    const pageNotes = url ? notes[url] || [] : [];

    const container = document.getElementById('page-notes');

    if (pageNotes.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">📝</span>
          <p>暂无笔记</p>
        </div>
      `;
      return;
    }

    container.innerHTML = pageNotes.map(note => `
      <div class="note-item">
        <div class="note-content">${escapeHtml(note.content)}</div>
        <div class="note-meta">
          ${note.tag ? `<span class="note-tag ${note.tag}">${getTagLabel(note.tag)}</span>` : ''}
          <span class="note-time">${formatTime(note.timestamp)}</span>
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error('加载笔记失败:', error);
  }
}

// 获取标签名称
function getTagLabel(tag) {
  const labels = {
    idea: '💡 想法',
    question: '❓ 问题',
    important: '⭐ 重要',
    todo: '📌 待办'
  };
  return labels[tag] || tag;
}

// 更新引用
function updateCitations(data) {
  citations = data;
  updateCitationFormat();
}

// 更新引用格式
function updateCitationFormat() {
  const textEl = document.getElementById('citation-text');
  if (!citations || !textEl) return;

  const citation = generateCitation(citations, currentFormat);
  textEl.value = citation;
}

// 生成引用
function generateCitation(data, format) {
  const authors = data.authors || [];
  const year = data.year || new Date().getFullYear();
  const title = data.title || '';
  const journal = data.journal || '';

  switch (format) {
    case 'apa':
      return `${authors.join(', ')} (${year}). ${title}. ${journal}.`;

    case 'mla':
      return `${authors.join(', ')}. "${title}." ${journal}, ${year}.`;

    case 'chicago':
      return `${authors.join(', ')}. "${title}." ${journal} (${year}).`;

    case 'gb':
      return `${authors.join(', ')}. ${title}[J]. ${journal}, ${year}.`;

    default:
      return `${authors.join(', ')} (${year}). ${title}. ${journal}.`;
  }
}

// 复制引用
async function copyCitation() {
  const text = document.getElementById('citation-text').value;
  await navigator.clipboard.writeText(text);

  const btn = document.getElementById('copy-citation-btn');
  const originalText = btn.textContent;
  btn.textContent = '✓ 已复制';
  setTimeout(() => {
    btn.textContent = originalText;
  }, 2000);
}

// 发送 AI 消息
async function sendAIMessage(message) {
  const messagesEl = document.getElementById('chat-messages');

  // 添加用户消息
  const userMsg = document.createElement('div');
  userMsg.className = 'user-message';
  userMsg.innerHTML = `
    <div class="message-avatar">👤</div>
    <div class="message-content">${escapeHtml(message)}</div>
  `;
  messagesEl.appendChild(userMsg);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  // 显示加载状态
  const loadingMsg = document.createElement('div');
  loadingMsg.className = 'ai-message';
  loadingMsg.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content">思考中...</div>
  `;
  messagesEl.appendChild(loadingMsg);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  try {
    // 获取当前页面内容（用于上下文）
    const pageContent = await sendToContent({ action: 'extract-article' });

    // 发送到 AI 服务
    const response = await sendToBackground({
      action: 'api-request',
      endpoint: '/ai/chat',
      data: {
        message,
        context: pageContent?.data || null,
        source: 'sidebar'
      }
    });

    // 移除加载消息
    loadingMsg.remove();

    // 添加 AI 回复
    const aiMsg = document.createElement('div');
    aiMsg.className = 'ai-message';
    aiMsg.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-content">${response.data?.reply || '抱歉，我暂时无法回答这个问题。'}</div>
    `;
    messagesEl.appendChild(aiMsg);
    messagesEl.scrollTop = messagesEl.scrollHeight;

  } catch (error) {
    loadingMsg.remove();

    const errorMsg = document.createElement('div');
    errorMsg.className = 'ai-message';
    errorMsg.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-content">抱歉，发生了错误。请稍后再试。</div>
    `;
    messagesEl.appendChild(errorMsg);
  }
}

// 使用工具
async function useTool(tool) {
  switch (tool) {
    case 'translate':
      // 获取选中文本并翻译
      const selection = await sendToContent({ action: 'get-selection' });
      if (selection?.text) {
        // 调用翻译 API
        showToast('翻译功能开发中...');
      } else {
        showToast('请先选中要翻译的文本');
      }
      break;

    case 'define':
      showToast('术语定义功能开发中...');
      break;

    case 'summarize':
      showToast('摘要生成功能开发中...');
      break;

    case 'highlight':
      showToast('高亮功能开发中...');
      break;

    case 'screenshot':
      showToast('截图功能开发中...');
      break;

    case 'export':
      showToast('导出功能开发中...');
      break;
  }
}

// 发送到内容脚本
async function sendToContent(message) {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabs[0].id, message, (response) => {
      resolve(response);
    });
  });
}

// 发送到后台
async function sendToBackground(message) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(message, resolve);
  });
}

// 显示提示
function showToast(message) {
  // 创建临时提示元素
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%);
    background: #333;
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 13px;
    z-index: 1000;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
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

  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}
