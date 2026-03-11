/**
 * ScholarForge 浏览器扩展 - 内容脚本
 * 页面文献提取、侧边栏注入、交互处理
 */

(function() {
  'use strict';

  // 防止重复注入
  if (window.scholarForgeInjected) return;
  window.scholarForgeInjected = true;

  // 状态
  let sidebarVisible = false;
  let sidebarFrame = null;

  // 学术网站匹配规则
  const ACADEMIC_SITES = {
    'scholar.google.com': 'google-scholar',
    'pubmed.ncbi.nlm.nih.gov': 'pubmed',
    'arxiv.org': 'arxiv',
    'doi.org': 'doi',
    'sci-hub': 'sci-hub',
    'ieee.org': 'ieee',
    'acm.org': 'acm',
    'springer.com': 'springer',
    'science.org': 'science',
    'nature.com': 'nature',
    'sciencedirect.com': 'sciencedirect',
    'wiley.com': 'wiley',
    'tandfonline.com': 'taylor-francis',
    'jstor.org': 'jstor'
  };

  // 初始化
  function initialize() {
    console.log('ScholarForge 内容脚本已加载');

    // 检测是否在学术网站
    detectAcademicSite();

    // 注入浮动按钮
    injectFloatingButton();

    // 监听消息
    chrome.runtime.onMessage.addListener(handleMessage);
  }

  // 检测当前是否在学术网站
  function detectAcademicSite() {
    const hostname = window.location.hostname;
    const siteType = Object.keys(ACADEMIC_SITES).find(site =>
      hostname.includes(site)
    );

    if (siteType) {
      document.body.dataset.scholarForgeSite = ACADEMIC_SITES[siteType];
      console.log('检测到学术网站:', ACADEMIC_SITES[siteType]);
    }
  }

  // 注入浮动按钮
  function injectFloatingButton() {
    const button = document.createElement('div');
    button.id = 'scholarforge-float-btn';
    button.innerHTML = `
      <div class="sf-float-icon">📚</div>
      <div class="sf-float-tooltip">ScholarForge</div>
    `;
    button.addEventListener('click', toggleSidebar);
    document.body.appendChild(button);
  }

  // 切换侧边栏
  function toggleSidebar() {
    if (sidebarVisible) {
      hideSidebar();
    } else {
      showSidebar();
    }
  }

  // 显示侧边栏
  function showSidebar() {
    if (!sidebarFrame) {
      sidebarFrame = document.createElement('iframe');
      sidebarFrame.id = 'scholarforge-sidebar';
      sidebarFrame.src = chrome.runtime.getURL('sidebar/sidebar.html');
      document.body.appendChild(sidebarFrame);
    }

    sidebarFrame.classList.add('visible');
    document.body.classList.add('scholarforge-sidebar-open');
    sidebarVisible = true;
  }

  // 隐藏侧边栏
  function hideSidebar() {
    if (sidebarFrame) {
      sidebarFrame.classList.remove('visible');
    }
    document.body.classList.remove('scholarforge-sidebar-open');
    sidebarVisible = false;
  }

  // 消息处理器
  function handleMessage(request, sender, sendResponse) {
    switch (request.action) {
      case 'extract-article':
        sendResponse(extractArticle());
        break;

      case 'get-selection-context':
        sendResponse(getSelectionContext(request.selection));
        break;

      case 'extract-link':
        sendResponse(extractLinkInfo(request.url));
        break;

      case 'toggle-sidebar':
        toggleSidebar();
        sendResponse({ success: true, visible: sidebarVisible });
        break;

      case 'get-page-info':
        sendResponse({
          success: true,
          data: {
            url: window.location.href,
            title: document.title,
            site: detectSiteType()
          }
        });
        break;

      default:
        sendResponse({ success: false, error: '未知操作' });
    }

    return true;
  }

  // 提取文章信息
  function extractArticle() {
    try {
      const data = {
        title: extractTitle(),
        authors: extractAuthors(),
        abstract: extractAbstract(),
        keywords: extractKeywords(),
        journal: extractJournal(),
        year: extractYear(),
        doi: extractDOI(),
        pdfUrl: extractPDFUrl(),
        citations: extractCitations()
      };

      return { success: true, data };
    } catch (error) {
      console.error('提取文章失败:', error);
      return { success: false, error: error.message };
    }
  }

  // 提取标题
  function extractTitle() {
    // 尝试多种选择器
    const selectors = [
      'h1.article-title',
      'h1.title',
      '[data-testid="article-title"]',
      'meta[name="citation_title"]',
      'meta[property="og:title"]'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        if (selector.startsWith('meta')) {
          return element.getAttribute('content');
        }
        return element.textContent.trim();
      }
    }

    // 回退到页面标题
    return document.title.replace(/ - .*/, '').trim();
  }

  // 提取作者
  function extractAuthors() {
    const authors = [];

    // 尝试多种选择器
    const selectors = [
      '.author-name',
      '.author',
      '[data-testid="author-name"]',
      'meta[name="citation_author"]'
    ];

    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        elements.forEach(el => {
          const name = selector.startsWith('meta')
            ? el.getAttribute('content')
            : el.textContent.trim();
          if (name && !authors.includes(name)) {
            authors.push(name);
          }
        });
        break;
      }
    }

    return authors;
  }

  // 提取摘要
  function extractAbstract() {
    const selectors = [
      '.abstract',
      '#abstract',
      '[data-testid="abstract"]',
      'meta[name="citation_abstract"]',
      'meta[name="description"]'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        if (selector.startsWith('meta')) {
          return element.getAttribute('content');
        }
        return element.textContent.trim();
      }
    }

    return '';
  }

  // 提取关键词
  function extractKeywords() {
    const keywords = [];

    // 尝试 meta 标签
    const metaKeywords = document.querySelector('meta[name="keywords"]');
    if (metaKeywords) {
      const content = metaKeywords.getAttribute('content');
      if (content) {
        keywords.push(...content.split(',').map(k => k.trim()));
      }
    }

    // 尝试页面内容
    const keywordElements = document.querySelectorAll('.keyword');
    keywordElements.forEach(el => {
      const text = el.textContent.trim();
      if (text && !keywords.includes(text)) {
        keywords.push(text);
      }
    });

    return keywords;
  }

  // 提取期刊信息
  function extractJournal() {
    const selectors = [
      '.journal-title',
      'meta[name="citation_journal_title"]',
      '.publication-title'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        if (selector.startsWith('meta')) {
          return element.getAttribute('content');
        }
        return element.textContent.trim();
      }
    }

    return '';
  }

  // 提取年份
  function extractYear() {
    const selectors = [
      '.year',
      '.publication-year',
      'meta[name="citation_publication_date"]',
      'meta[name="citation_date"]'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        const content = selector.startsWith('meta')
          ? element.getAttribute('content')
          : element.textContent.trim();
        const year = content.match(/\d{4}/);
        if (year) return parseInt(year[0]);
      }
    }

    return null;
  }

  // 提取 DOI
  function extractDOI() {
    // 从 URL 提取
    const urlMatch = window.location.href.match(/doi\/(10\.\d{4,}\/.+)/);
    if (urlMatch) return urlMatch[1];

    // 从 meta 标签提取
    const metaDOI = document.querySelector('meta[name="citation_doi"]');
    if (metaDOI) return metaDOI.getAttribute('content');

    // 从页面内容提取
    const doiElement = document.querySelector('.doi');
    if (doiElement) {
      const text = doiElement.textContent;
      const match = text.match(/(10\.\d{4,}\/.+)/);
      if (match) return match[1];
    }

    return '';
  }

  // 提取 PDF 链接
  function extractPDFUrl() {
    const selectors = [
      'a[href$=".pdf"]',
      'meta[name="citation_pdf_url"]',
      '.pdf-link'
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        if (selector.startsWith('meta')) {
          return element.getAttribute('content');
        }
        return element.getAttribute('href');
      }
    }

    return '';
  }

  // 提取引用信息
  function extractCitations() {
    const citationInfo = {
      count: null,
      format: null
    };

    // 尝试找到引用计数
    const citationElements = document.querySelectorAll('.citation-count, .cite-count');
    citationElements.forEach(el => {
      const text = el.textContent;
      const match = text.match(/(\d+)/);
      if (match) {
        citationInfo.count = parseInt(match[1]);
      }
    });

    return citationInfo;
  }

  // 获取选中内容的上下文
  function getSelectionContext(selection) {
    const selectionObj = window.getSelection();
    if (selectionObj.rangeCount === 0) {
      return { context: '' };
    }

    const range = selectionObj.getRangeAt(0);
    const container = range.commonAncestorContainer.parentElement;

    return {
      context: container.textContent.substring(0, 500),
      surroundingText: getSurroundingText(range)
    };
  }

  // 获取周围文本
  function getSurroundingText(range) {
    const container = range.commonAncestorContainer;
    const text = container.textContent;
    const start = Math.max(0, range.startOffset - 100);
    const end = Math.min(text.length, range.endOffset + 100);
    return text.substring(start, end);
  }

  // 提取链接信息
  function extractLinkInfo(url) {
    // 这里可以实现获取链接页面标题的逻辑
    // 由于跨域限制，可能需要通过后台服务代理
    return {
      url: url,
      title: null // 需要后台获取
    };
  }

  // 检测网站类型
  function detectSiteType() {
    const hostname = window.location.hostname;
    for (const [site, type] of Object.entries(ACADEMIC_SITES)) {
      if (hostname.includes(site)) {
        return type;
      }
    }
    return 'general';
  }

  // 启动
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }
})();
