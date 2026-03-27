// content/content-script.js
// AP Exam Capture - Content Script (MVP)
// 注入到 AP 模考页面，负责数据采集

// ==================== 配置 ====================
const CONFIG = {
  // AP 模考页面的 URL 特征
  examPatterns: [
    /mokaoai\.com.*\/ap\//i,
    /exam/i,
    /assessment/i,
    /quiz/i,
    /test/i
  ],
  // 需要拦截的 API 路径
  apiPatterns: [
    /\/api\//i,
    /\/v\d+\//i,
    /\.json$/i,
    /\/questions?/i,
    /\/answers?/i,
    /\/progress/i,
    /\/session/i
  ],
  // 事件关键词映射（基于 mokaoai.com 实际页面）
  eventKeywords: {
    'start': ['start', 'begin', 'commencer', 'iniciar', '시작', '开始考试'],
    'resume': ['resume', 'continuar', 'reprendre', '재개', '继续'],
    'next': ['next', 'suivant', 'siguiente', '다음', '下一题'],
    'previous': ['prev', 'previous', 'precedent', 'anterior', '이전', '上一题'],
    'flag': ['flag', 'bookmark', 'marcar', '标记', '收藏'],
    'review': ['review', 'reviser', 'revisar', '复核', '检查'],
    'module_change': ['module', 'part', 'section', '部分'],
    'submit': ['submit', 'envoyer', 'enviar', '提交', '提交答案'],
    'back': ['back', '返回', '后退'],
    'reselect': ['reselect', '重新选择', '重选'],
    'confirm': ['confirm', '确认', '确定'],
    'cancel': ['cancel', '取消']
  },
  // 注水状态关键词
  injectedStateKeys: [
    '__NEXT_DATA__',
    '__INITIAL_STATE__',
    '__NUXT__',
    '__INITIAL_PROPS__',
    '__PRELOADED_STATE__',
    'window.__REDUX_STATE__',
    'window.__STATE__'
  ]
};

// ==================== 状态 ====================
let sessionId = null;
let captureActive = false;
let previousUrl = location.href;
let previousStorage = null;
let previousIndexedDB = null;
let eventDebounceTimer = null;
let isExamPage = false;
let networkInterceptInstalled = false;
let listenersAttached = false;
let mutationObserver = null;
let urlPollTimer = null;
let originalFetch = null;
let originalXHROpen = null;
let originalXHRSend = null;

// ==================== 初始化 ====================
function init() {
  // 检测是否是 AP 模考页面
  isExamPage = detectExamPage();
  console.log(`[AP-Capture] Content script loaded, isExamPage: ${isExamPage}`);

  if (isExamPage) {
    startCapture();
  }

  // 监听来自 popup 或 background 的消息
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    const { type } = message;
    
    switch (type) {
      case 'START_CAPTURE':
        startCapture();
        sendResponse({ success: true, captureActive: captureActive });
        break;
      case 'STOP_CAPTURE':
        stopCapture();
        sendResponse({ success: true });
        break;
      case 'GET_STATUS':
        sendResponse({ captureActive, eventCount: 0, networkCount: 0 });
        break;
      case 'CAPTURE_NOW':
        captureSnapshot('manual');
        sendResponse({ success: true });
        break;
      default:
        sendResponse({ error: 'Unknown message type' });
    }
    return true; // 保持消息通道开放
  });

  // 监听页面变化（单页应用）
  observeUrlChange();

  // 监听 visibility change（页面切换）
  document.addEventListener('visibilitychange', handleVisibilityChange);
}

function detectExamPage() {
  const url = location.href.toLowerCase();
  const title = document.title.toLowerCase();
  return CONFIG.examPatterns.some(p => p.test(url) || p.test(title));
}

// ==================== 采集控制 ====================
function startCapture() {
  if (captureActive) return;

  captureActive = true;
  previousStorage = getStorageSnapshot();
  previousIndexedDB = getIndexedDBSnapshot();

  console.log('[AP-Capture] 🚀 Capture started on this page');

  // 通知 background
  try {
    chrome.runtime.sendMessage({ type: 'START_CAPTURE' });
  } catch (e) {
    console.log('[AP-Capture] Background not available:', e.message);
  }

  // 初始化时立即采集一次
  captureSnapshot('init');

  // 启动网络拦截
  interceptNetwork();

  // 启动事件监听
  attachEventListeners();
}

function stopCapture() {
  if (!captureActive) return;

  captureActive = false;
  console.log('[AP-Capture] ⏹️ Capture stopped');
  chrome.runtime.sendMessage({ type: 'STOP_CAPTURE' });
}

// ==================== 网络拦截 ====================
function interceptNetwork() {
  if (networkInterceptInstalled) return;

  // 拦截 fetch
  originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : args[0].url;
    const method = args[1]?.method || 'GET';
    const requestId = generateRequestId(url, method);

    // 发送请求信息给 background
    chrome.runtime.sendMessage({
      type: 'NETWORK_REQUEST',
      payload: {
        requestId,
        url: url,
        method: method,
        headers: extractHeaders(args[1]),
        body: args[1]?.body || null,
        tabId: null
      }
    });

    try {
      const response = await originalFetch.apply(this, args);

      // 克隆 response 以便读取 body
      const clonedResponse = response.clone();
      let responseBody = null;
      const contentType = response.headers.get('content-type') || '';

      if (contentType.includes('application/json') || contentType.includes('text/')) {
        try {
          responseBody = await clonedResponse.json();
        } catch {
          responseBody = await clonedResponse.text();
        }
      }

      // 发送响应信息给 background
      chrome.runtime.sendMessage({
        type: 'NETWORK_RESPONSE',
        payload: {
          requestId,
          url: url,
          status: response.status,
          headers: extractHeadersFromResponse(response.headers),
          body: responseBody
        }
      });

      return response;
    } catch (error) {
      console.error('[AP-Capture] Fetch error:', error);
      throw error;
    }
  };

  // 拦截 XMLHttpRequest
  originalXHROpen = XMLHttpRequest.prototype.open;
  originalXHRSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this._xhrCapture = {
      method: method,
      url: url,
      requestId: generateRequestId(url, method)
    };
    return originalXHROpen.apply(this, [method, url, ...rest]);
  };

  XMLHttpRequest.prototype.send = function(body) {
    if (this._xhrCapture) {
      chrome.runtime.sendMessage({
        type: 'NETWORK_REQUEST',
        payload: {
          requestId: this._xhrCapture.requestId,
          url: this._xhrCapture.url,
          method: this._xhrCapture.method,
          body: body,
          tabId: null
        }
      });
    }

    this.addEventListener('load', function() {
      if (this._xhrCapture) {
        let responseBody = null;
        try {
          responseBody = JSON.parse(this.responseText);
        } catch {
          responseBody = this.responseText;
        }

        chrome.runtime.sendMessage({
          type: 'NETWORK_RESPONSE',
          payload: {
            requestId: this._xhrCapture.requestId,
            url: this._xhrCapture.url,
            status: this.status,
            headers: {},
            body: responseBody
          }
        });
      }
    });

    return originalXHRSend.apply(this, [body]);
  };

  networkInterceptInstalled = true;
}

function generateRequestId(url, method) {
  return `${method}-${url}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
}

function extractHeaders(options) {
  if (!options || !options.headers) return {};
  if (options.headers instanceof Headers) {
    const result = {};
    options.headers.forEach((v, k) => result[k] = v);
    return result;
  }
  return options.headers;
}

function extractHeadersFromResponse(headers) {
  const result = {};
  headers.forEach((v, k) => result[k] = v);
  return result;
}

// ==================== 事件监听 ====================
function attachEventListeners() {
  if (listenersAttached) return;

  // 监听常见的考试交互
  const clickableElements = document.querySelectorAll('button, a, [role="button"], [data-action]');

  clickableElements.forEach(el => {
    el.addEventListener('click', handleElementClick, true);
  });

  // 使用 MutationObserver 捕获动态添加的元素
  mutationObserver = new MutationObserver((mutations) => {
    mutations.forEach(mutation => {
      mutation.addedNodes.forEach(node => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          attachClickListener(node);
        }
      });
    });
  });

  mutationObserver.observe(document.body, { childList: true, subtree: true });

  // 监听键盘事件
  document.addEventListener('keydown', handleKeyDown, true);
  listenersAttached = true;
}

function attachClickListener(element) {
  if (element.tagName === 'BUTTON' || element.tagName === 'A' || element.getAttribute('role') === 'button') {
    element.addEventListener('click', handleElementClick, true);
  }
  element.querySelectorAll('button, a, [role="button"]').forEach(el => {
    el.addEventListener('click', handleElementClick, true);
  });
}

function handleElementClick(event) {
  if (!captureActive) return;

  const target = event.target;
  const text = target.textContent?.trim().toLowerCase() || '';
  const ariaLabel = target.getAttribute('aria-label')?.toLowerCase() || '';
  const dataAction = target.getAttribute('data-action')?.toLowerCase() || '';
  const id = target.id?.toLowerCase() || '';
  const className = target.className?.toLowerCase() || '';

  // 合并所有文本特征
  const allText = `${text} ${ariaLabel} ${dataAction} ${id} ${className}`;

  // 检测事件类型
  const eventType = detectEventType(allText);
  if (eventType) {
    debounceCapture(eventType, {
      clickTarget: target.tagName,
      text: text,
      ariaLabel: ariaLabel,
      url: location.href
    });
  }
}

function handleKeyDown(event) {
  if (!captureActive) return;

  const key = event.key;
  const eventTypeMap = {
    'ArrowRight': 'next',
    'ArrowLeft': 'previous',
    'n': 'next',
    'p': 'previous'
  };

  if (eventTypeMap[key]) {
    debounceCapture(eventTypeMap[key], {
      key: key,
      url: location.href
    });
  }
}

function detectEventType(text) {
  for (const [eventType, keywords] of Object.entries(CONFIG.eventKeywords)) {
    if (keywords.some(kw => text.includes(kw))) {
      return eventType;
    }
  }
  return null;
}

function debounceCapture(eventType, details) {
  if (eventDebounceTimer) {
    clearTimeout(eventDebounceTimer);
  }

  eventDebounceTimer = setTimeout(() => {
    captureEvent(eventType, details);
  }, 100); // 100ms 防抖
}

// ==================== 存储快照 ====================
function getStorageSnapshot() {
  const snapshot = {
    localStorage: {},
    sessionStorage: {}
  };

  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      snapshot.localStorage[key] = localStorage.getItem(key);
    }
  } catch (e) {
    snapshot.localStorage = { error: e.message };
  }

  try {
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      snapshot.sessionStorage[key] = sessionStorage.getItem(key);
    }
  } catch (e) {
    snapshot.sessionStorage = { error: e.message };
  }

  return snapshot;
}

async function getIndexedDBSnapshot() {
  // IndexedDB 完整快照 - MVP 版
  const result = {};

  try {
    const databases = await indexedDB.databases();
    
    for (const dbInfo of databases.slice(0, 5)) { // 最多5个 DB
      const dbName = dbInfo.name;
      if (!dbName) continue;
      
      try {
        const db = await openIndexedDB(dbName, dbInfo.version);
        const stores = {};
        
        for (const storeName of db.objectStoreNames) {
          const data = await readAllFromStore(db, storeName);
          stores[storeName] = {
            count: data.length,
            sample: data.slice(0, 10), // 最多存10条样本
            keys: data.map(d => d.key).slice(0, 50) // 存前50个key
          };
        }
        
        result[dbName] = {
          version: dbInfo.version,
          stores: stores
        };
        
        db.close();
      } catch (e) {
        result[dbName] = { error: e.message };
      }
    }
  } catch (e) {
    return { error: e.message };
  }

  return result;
}

// 辅助函数：打开 IndexedDB
function openIndexedDB(dbName, version) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(dbName, version);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// 辅助函数：读取 object store 的所有数据
function readAllFromStore(db, storeName) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readonly');
    const store = tx.objectStore(storeName);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => resolve([]);
  });
}

// ==================== Storage Diff（增量对比） ====================
// 比较前后两次 storage 快照，返回差异
function getStorageDiff(prev, curr) {
  const diff = {
    localStorage: { added: {}, removed: {}, changed: {} },
    sessionStorage: { added: {}, removed: {}, changed: {} }
  };
  
  // localStorage diff
  const prevKeys = prev?.localStorage ? Object.keys(prev.localStorage) : [];
  const currKeys = curr?.localStorage ? Object.keys(curr.localStorage) : [];
  
  // added
  for (const key of currKeys) {
    if (!prevKeys.includes(key)) {
      diff.localStorage.added[key] = curr.localStorage[key];
    }
  }
  
  // removed
  for (const key of prevKeys) {
    if (!currKeys.includes(key)) {
      diff.localStorage.removed[key] = prev.localStorage[key];
    }
  }
  
  // changed
  for (const key of currKeys) {
    if (prevKeys.includes(key) && prev.localStorage[key] !== curr.localStorage[key]) {
      diff.localStorage.changed[key] = {
        from: prev.localStorage[key],
        to: curr.localStorage[key]
      };
    }
  }
  
  // sessionStorage diff（同样逻辑）
  const prevSSKeys = prev?.sessionStorage ? Object.keys(prev.sessionStorage) : [];
  const currSSKeys = curr?.sessionStorage ? Object.keys(curr.sessionStorage) : [];
  
  for (const key of currSSKeys) {
    if (!prevSSKeys.includes(key)) {
      diff.sessionStorage.added[key] = curr.sessionStorage[key];
    }
  }
  
  for (const key of prevSSKeys) {
    if (!currSSKeys.includes(key)) {
      diff.sessionStorage.removed[key] = prev.sessionStorage[key];
    }
  }
  
  for (const key of currSSKeys) {
    if (prevSSKeys.includes(key) && prev.sessionStorage[key] !== curr.sessionStorage[key]) {
      diff.sessionStorage.changed[key] = {
        from: prev.sessionStorage[key],
        to: curr.sessionStorage[key]
      };
    }
  }
  
  return diff;
}

// ==================== 注水状态捕获 ====================
function getInjectedState() {
  const state = {};

  // __NEXT_DATA__
  if (window.__NEXT_DATA__) {
    state.nextData = window.__NEXT_DATA__;
  }

  // __INITIAL_STATE__ (React)
  if (window.__INITIAL_STATE__) {
    state.initialState = window.__INITIAL_STATE__;
  }

  // Redux
  if (window.__REDUX_STATE__) {
    state.redux = window.__REDUX_STATE__;
  }

  // Vuex
  if (window.__NUXT__) {
    state.nuxt = window.__NUXT__;
  }

  // 遍历 window 找常见注水对象
  for (const key of Object.keys(window)) {
    if (key.startsWith('__') && key.endsWith('__')) {
      try {
        const val = window[key];
        if (typeof val === 'object' && val !== null) {
          state[key] = JSON.parse(JSON.stringify(val));
        }
      } catch {
        state[key] = '[Circular or Non-JSON]';
      }
    }
  }

  return state;
}

// ==================== 完整快照采集 ====================
function captureSnapshot(trigger) {
  if (!captureActive) return;

  // 获取当前存储快照
  const currentStorage = getStorageSnapshot();
  
  // 计算 storage diff
  const storageDiff = previousStorage ? getStorageDiff(previousStorage, currentStorage) : null;

  // 存储快照
  chrome.runtime.sendMessage({
    type: 'STORAGE_SNAPSHOT',
    payload: {
      url: location.href,
      trigger: trigger,
      localStorage: currentStorage.localStorage,
      sessionStorage: currentStorage.sessionStorage,
      storageDiff: storageDiff // 增量差异
    }
  });

  // IndexedDB
  getIndexedDBSnapshot().then(idbSnapshot => {
    chrome.runtime.sendMessage({
      type: 'STORAGE_SNAPSHOT',
      payload: {
        url: location.href,
        trigger: trigger,
        indexedDB: idbSnapshot
      }
    });
  });

  // 注水状态
  const injectedState = getInjectedState();
  chrome.runtime.sendMessage({
    type: 'INJECTED_STATE',
    payload: {
      url: location.href,
      trigger: trigger,
      ...injectedState
    }
  });

  // 更新 previousStorage
  previousStorage = currentStorage;
}

function captureEvent(eventType, details) {
  if (!captureActive) return;

  // 提取当前题目信息
  const questionInfo = extractQuestionInfo();

  chrome.runtime.sendMessage({
    type: 'PAGE_EVENT',
    payload: {
      eventType: eventType,
      url: location.href,
      questionNumber: questionInfo.number,
      section: questionInfo.section,
      part: questionInfo.part,
      details: details
    }
  });

  // 触发增强数据采集（工具栏、DOM样式、MathML）
  captureEnhanceData();
}

function extractQuestionInfo() {
  // 尝试从 DOM 中提取题目编号和 section 信息
  // 需要根据实际页面结构调整选择器
  const info = {
    number: null,
    section: null,
    part: null
  };

  // 尝试常见的题目编号选择器
  const numberSelectors = [
    '[data-question-number]',
    '.question-number',
    '#question-number',
    '[class*="question"]',
    '[class*="number"]'
  ];

  for (const selector of numberSelectors) {
    const el = document.querySelector(selector);
    if (el) {
      const match = el.textContent.match(/\d+/);
      if (match) {
        info.number = parseInt(match[0]);
        break;
      }
    }
  }

  // 尝试提取 section/part
  const sectionSelectors = [
    '[data-section]',
    '.section-label',
    '[class*="section"]'
  ];

  for (const selector of sectionSelectors) {
    const el = document.querySelector(selector);
    if (el) {
      info.section = el.textContent.trim();
      break;
    }
  }

  return info;
}

// ==================== URL 变化监听 ====================
function observeUrlChange() {
  if (urlPollTimer) return;

  // 对于 SPA，监听 popstate
  window.addEventListener('popstate', () => {
    onUrlChange();
  });

  // 轮询检测（作为补充）
  urlPollTimer = setInterval(() => {
    if (location.href !== previousUrl) {
      previousUrl = location.href;
      onUrlChange();
    }
  }, 1000);
}

function onUrlChange() {
  if (!captureActive) {
    // 检测是否进入考试页面
    if (detectExamPage()) {
      startCapture();
    }
    return;
  }

  // URL 变化时重新采集快照
  captureSnapshot('url-change');
}

// ==================== 页面切换处理 ====================
function handleVisibilityChange() {
  if (document.hidden) {
    // 页面隐藏时不做特殊处理
    return;
  }

  // 页面重新显示时检查状态
  if (captureActive) {
    captureSnapshot('visibility-change');
  }
}

// ==================== 工具栏配置数据采集 ====================
// 检测考试工具栏的按钮状态和可见性
function captureToolbarConfig() {
  const config = {
    timestamp: new Date().toISOString(),
    url: location.href,
    section: extractSectionInfo(),
    visibleTools: {},
    toolDetails: [],
    timerState: null,
    moreMenuItems: []
  };

  // 定义工具栏按钮的常见特征（根据 mokaoai 网站调整）
  const toolPatterns = {
    calculator: [
      { tag: 'button', text: /calc/i },
      { tag: 'button', ariaLabel: /calc/i },
      { class: /calc/i },
      { id: /calc/i }
    ],
    notes: [
      { tag: 'button', text: /note/i },
      { tag: 'button', ariaLabel: /note/i },
      { class: /note/i },
      { id: /note/i }
    ],
    highlights: [
      { tag: 'button', text: /highlight/i },
      { tag: 'button', ariaLabel: /highlight/i },
      { class: /highlight/i },
      { id: /highlight/i }
    ],
    lineReader: [
      { tag: 'button', text: /line.*read/i },
      { tag: 'button', ariaLabel: /line.*read/i },
      { class: /line.*read/i }
    ],
    more: [
      { tag: 'button', text: /more/i },
      { tag: 'button', ariaLabel: /more/i },
      { class: /more/i },
      { id: /more/i }
    ],
    timer: [
      { class: /timer/i },
      { class: /time/i },
      { id: /timer/i }
    ]
  };

  // 遍历每种工具，检测是否存在且可见
  for (const [toolName, patterns] of Object.entries(toolPatterns)) {
    let found = null;
    
    for (const pattern of patterns) {
      const elements = findElementsByPattern(pattern);
      if (elements.length > 0) {
        const visible = elements.some(el => isElementVisible(el));
        if (visible) {
          found = {
            type: toolName,
            found: true,
            visible: true,
            count: elements.length,
            position: elements[0].getBoundingClientRect().toJSON()
          };
          break;
        }
      }
    }

    config.visibleTools[toolName] = found ? found.visible : false;
    if (found) {
      config.toolDetails.push(found);
    }
  }

  // 尝试获取 Timer 状态
  const timerEl = document.querySelector('[class*="timer"], [class*="time"]');
  if (timerEl) {
    config.timerState = {
      visible: isElementVisible(timerEl),
      text: timerEl.textContent?.trim().substring(0, 50)
    };
  }

  // 尝试点击 More 菜单并捕获子项（如果有的话）
  captureMoreMenuItems(config);

  console.log('[AP-Capture] 🛠️ Toolbar config captured:', config.visibleTools);

  // 发送到 background
  chrome.runtime.sendMessage({
    type: 'TOOLBAR_CONFIG',
    payload: config
  });

  return config;
}

// 辅助函数：根据模式查找元素
function findElementsByPattern(pattern) {
  const results = [];
  
  if (pattern.tag) {
    const elements = document.querySelectorAll(pattern.tag);
    elements.forEach(el => {
      const text = el.textContent?.toLowerCase() || '';
      const ariaLabel = el.getAttribute('aria-label')?.toLowerCase() || '';
      const className = el.className?.toLowerCase() || '';
      const id = el.id?.toLowerCase() || '';
      
      if (pattern.text && pattern.text.test(text)) results.push(el);
      else if (pattern.ariaLabel && pattern.ariaLabel.test(ariaLabel)) results.push(el);
      else if (pattern.class && pattern.class.test(className)) results.push(el);
      else if (pattern.id && pattern.id.test(id)) results.push(el);
    });
  } else if (pattern.class) {
    const elements = document.querySelectorAll(`[class*="${pattern.class.source || pattern.class}"]`);
    results.push(...elements);
  } else if (pattern.id) {
    const elements = document.querySelectorAll(`[id*="${pattern.id.source || pattern.id}"]`);
    results.push(...elements);
  }
  
  return results;
}

// 辅助函数：检查元素是否可见
function isElementVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  return style.display !== 'none' && 
         style.visibility !== 'hidden' && 
         style.opacity !== '0' &&
         el.offsetParent !== null;
}

// 提取当前的 Section/Part 信息
function extractSectionInfo() {
  const info = { section: null, part: null };
  
  // 尝试从 URL 参数提取
  const params = new URLSearchParams(location.search);
  info.section = params.get('section') || params.get('part') || null;
  
  // 尝试从 DOM 提取
  const sectionEl = document.querySelector('[class*="section"], [data-section]');
  if (sectionEl) {
    info.section = sectionEl.textContent?.trim() || info.section;
  }
  
  const partEl = document.querySelector('[class*="part"], [data-part]');
  if (partEl) {
    info.part = partEl.textContent?.trim() || info.part;
  }
  
  return info;
}

// 尝试捕获 More 菜单的子项
function captureMoreMenuItems(config) {
  const morePatterns = [
    { text: /more/i, ariaLabel: /more/i },
    { class: /more/i }
  ];
  
  for (const pattern of morePatterns) {
    const elements = findElementsByPattern(pattern);
    const visibleMore = elements.filter(el => isElementVisible(el));
    
    if (visibleMore.length > 0) {
      // 尝试模拟点击获取菜单项
      try {
        const event = new MouseEvent('click', { bubbles: true });
        visibleMore[0].dispatchEvent(event);
        
        // 等待菜单展开
        setTimeout(() => {
          const menuItems = document.querySelectorAll('[role="menuitem"], [class*="dropdown"] li, [class*="menu"] li');
          config.moreMenuItems = Array.from(menuItems).map(item => ({
            text: item.textContent?.trim().substring(0, 50),
            visible: isElementVisible(item)
          }));
        }, 200);
      } catch (e) {
        console.log('[AP-Capture] Could not capture more menu:', e.message);
      }
      break;
    }
  }
}

// ==================== DOM/CSS 渲染资源采集 ====================
// 采集关键元素的 computed styles 和 CSS 类名详情
function captureDOMStyles() {
  const result = {
    timestamp: new Date().toISOString(),
    url: location.href,
    questionElement: null,
    optionElements: [],
    styles: {},
    resources: {}
  };

  // 采集题目区域的样式
  const questionSelectors = [
    '.stem_paragraph',
    '.question-stem',
    '[class*="stem"]',
    '[class*="question"]'
  ];

  for (const selector of questionSelectors) {
    const el = document.querySelector(selector);
    if (el) {
      result.questionElement = captureElementStyle(el);
      break;
    }
  }

  // 采集选项区域的样式
  const optionSelectors = [
    '.choice_paragraph',
    '.option',
    '[class*="choice"]',
    '[class*="option"]'
  ];

  for (const selector of optionSelectors) {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
      result.optionElements = Array.from(elements).slice(0, 5).map(el => captureElementStyle(el));
      break;
    }
  }

  // 采集页面基础样式
  result.styles = {
    fontFamily: getComputedStyle(document.body).fontFamily,
    fontSize: getComputedStyle(document.body).fontSize,
    backgroundColor: getComputedStyle(document.body).backgroundColor,
    color: getComputedStyle(document.body).color,
    lineHeight: getComputedStyle(document.body).lineHeight
  };

  // 采集资源索引
  result.resources = captureResourceIndex();

  console.log('[AP-Capture] 🎨 DOM styles captured');

  chrome.runtime.sendMessage({
    type: 'DOM_STYLES',
    payload: result
  });

  return result;
}

// 采集资源索引（CSS、图片、JS）
function captureResourceIndex() {
  const resources = {
    stylesheets: [],
    scripts: [],
    images: [],
    fonts: []
  };

  // CSS
  document.querySelectorAll('link[rel="stylesheet"]').forEach(el => {
    resources.stylesheets.push({
      href: el.href,
      media: el.media
    });
  });

  // JS
  document.querySelectorAll('script[src]').forEach(el => {
    resources.scripts.push({
      src: el.src
    });
  });

  // Images
  document.querySelectorAll('img').forEach((el, i) => {
    if (i < 20) { // 限制数量
      resources.images.push({
        src: el.src,
        alt: el.alt,
        width: el.width,
        height: el.height
      });
    }
  });

  return resources;
}

// 采集关键 DOM 元素的 outerHTML
function captureDOMSnapshot() {
  const result = {
    timestamp: new Date().toISOString(),
    url: location.href,
    snapshots: {}
  };

  // 关键选择器（基于 mokaoai JSON 结构）
  const keySelectors = {
    stem: '.stem_paragraph, [class*="stem"]',
    question: '[class*="question"]',
    choices: '.choice_paragraph, [class*="choice"]',
    passage: '.passage, [class*="passage"]',
    codeBlock: '.standalone_code, [class*="code"]',
    questionNav: '[class*="nav"], [class*="question"]'
  };

  for (const [name, selector] of Object.entries(keySelectors)) {
    const el = document.querySelector(selector);
    if (el) {
      result.snapshots[name] = {
        selector: selector,
        outerHTML: el.outerHTML.substring(0, 2000), // 截断
        textContent: el.textContent?.trim().substring(0, 500)
      };
    }
  }

  console.log('[AP-Capture] 📸 DOM snapshot captured');

  chrome.runtime.sendMessage({
    type: 'DOM_SNAPSHOT',
    payload: result
  });

  return result;
}

// 辅助函数：采集单个元素的样式详情
function captureElementStyle(el) {
  const style = getComputedStyle(el);
  return {
    tag: el.tagName.toLowerCase(),
    className: el.className,
    id: el.id,
    computedStyles: {
      fontFamily: style.fontFamily,
      fontSize: style.fontSize,
      fontWeight: style.fontWeight,
      color: style.color,
      backgroundColor: style.backgroundColor,
      padding: style.padding,
      margin: style.margin,
      border: style.border,
      borderRadius: style.borderRadius,
      lineHeight: style.lineHeight,
      textAlign: style.textAlign,
      display: style.display,
      position: style.position,
      width: style.width,
      height: style.height
    },
    boundingRect: el.getBoundingClientRect().toJSON()
  };
}

// ==================== MathML/KaTeX 详细提取 ====================
// 提取数学公式的详细信息
function captureMathExpressions() {
  const result = {
    timestamp: new Date().toISOString(),
    url: location.href,
    mathElements: []
  };

  // 查找所有 MathML 元素
  const mathMLs = document.querySelectorAll('math');
  mathMLs.forEach((math, index) => {
    result.mathElements.push({
      index: index,
      type: 'mathml',
      alttext: math.getAttribute('alttext') || '',
      display: math.getAttribute('display') || 'inline',
      html: math.outerHTML,
      // 提取关键子元素
      operators: extractMathOperators(math),
      // computed styles
      computedStyle: {
        fontFamily: getComputedStyle(math).fontFamily,
        color: getComputedStyle(math).color
      }
    });
  });

  // 查找 KaTeX 相关元素
  const katexElements = document.querySelectorAll('.katex, .MathJax, [class*="katex"]');
  katexElements.forEach((el, index) => {
    result.mathElements.push({
      index: mathMLs.length + index,
      type: 'katex',
      html: el.outerHTML.substring(0, 500),
      className: el.className
    });
  });

  // 查找 .math_expression 类（mokaoai 使用的）
  const mathExprs = document.querySelectorAll('.math_expression');
  mathExprs.forEach((el, index) => {
    const mathChild = el.querySelector('math');
    result.mathElements.push({
      index: mathMLs.length + katexElements.length + index,
      type: 'math_expression',
      hasMathML: !!mathChild,
      alttext: mathChild?.getAttribute('alttext') || '',
      html: el.innerHTML.substring(0, 300)
    });
  });

  console.log(`[AP-Capture] 🔢 Found ${result.mathElements.length} math elements`);

  chrome.runtime.sendMessage({
    type: 'MATH_ELEMENTS',
    payload: result
  });

  return result;
}

// 辅助函数：从 MathML 提取运算符
function extractMathOperators(math) {
  const operators = [];
  const operatorTags = ['mo', 'mi', 'mn', 'ms'];
  
  operatorTags.forEach(tag => {
    const elements = math.querySelectorAll(tag);
    elements.forEach(el => {
      const text = el.textContent?.trim();
      if (text && text.length <= 5) {
        operators.push(text);
      }
    });
  });
  
  return [...new Set(operators)]; // 去重
}

// ==================== 增强的采集触发 ====================
// 在每次事件时触发增强采集
function captureEnhanceData() {
  captureToolbarConfig();
  captureDOMStyles();
  captureMathExpressions();
  captureDOMSnapshot();
}

// ==================== 启动 ====================
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// 页面即将卸载时停止采集
window.addEventListener('beforeunload', () => {
  if (captureActive) {
    chrome.runtime.sendMessage({ type: 'STOP_CAPTURE' });
  }
});
