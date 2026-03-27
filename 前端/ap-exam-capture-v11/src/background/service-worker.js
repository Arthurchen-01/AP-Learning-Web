let sessionId = null;
let captureActive = false;
let eventLog = [];
let networkLog = [];
let storageSnapshot = null;
let injectedStateSnapshot = null;

function initSession() {
  sessionId = `ap-capture-${Date.now()}`;
  eventLog = [];
  networkLog = [];
  storageSnapshot = null;
  injectedStateSnapshot = null;
  console.log(`[AP-Capture] Session started: ${sessionId}`);
}

initSession();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const { type, payload } = message || {};

  switch (type) {
    case 'NETWORK_REQUEST':
      handleNetworkRequest(payload);
      sendResponse({ ok: true });
      break;
    case 'NETWORK_RESPONSE':
      handleNetworkResponse(payload);
      sendResponse({ ok: true });
      break;
    case 'STORAGE_SNAPSHOT':
      handleStorageSnapshot(payload);
      sendResponse({ ok: true });
      break;
    case 'INJECTED_STATE':
      handleInjectedState(payload);
      sendResponse({ ok: true });
      break;
    case 'PAGE_EVENT':
      handlePageEvent(payload);
      sendResponse({ ok: true });
      break;
    case 'TOOLBAR_CONFIG':
      handleToolbarConfig(payload);
      sendResponse({ ok: true });
      break;
    case 'DOM_STYLES':
      handleDomStyles(payload);
      sendResponse({ ok: true });
      break;
    case 'MATH_ELEMENTS':
      handleMathElements(payload);
      sendResponse({ ok: true });
      break;
    case 'DOM_SNAPSHOT':
      handleDomSnapshot(payload);
      sendResponse({ ok: true });
      break;
    case 'START_CAPTURE':
      Promise.resolve(startCapture())
        .then((result) => sendResponse({ ok: true, ...(result || {}), sessionId, captureActive }))
        .catch((error) => sendResponse({ ok: false, error: error.message }));
      return true;
    case 'STOP_CAPTURE':
      Promise.resolve(stopCapture())
        .then((result) => sendResponse({ ok: true, ...(result || {}), sessionId, captureActive }))
        .catch((error) => sendResponse({ ok: false, error: error.message }));
      return true;
    case 'EXPORT_SESSION':
      Promise.resolve(exportSession())
        .then((result) => sendResponse({ ok: true, ...(result || {}), sessionId, captureActive }))
        .catch((error) => sendResponse({ ok: false, error: error.message }));
      return true;
    case 'GET_STATUS':
      sendResponse({
        ok: true,
        sessionId,
        captureActive,
        eventCount: eventLog.length,
        networkCount: networkLog.length
      });
      break;
    default:
      console.warn(`[AP-Capture] Unknown message type: ${type}`);
      sendResponse({ ok: false, error: `Unknown message type: ${type}` });
      break;
  }
});

function handleNetworkRequest(payload = {}) {
  if (!captureActive) return;

  networkLog.push({
    type: 'request',
    id: payload.requestId || generateId(),
    timestamp: new Date().toISOString(),
    url: payload.url,
    method: payload.method || 'GET',
    headers: payload.headers || {},
    body: payload.body || null,
    tabId: payload.tabId || null
  });
}

function handleNetworkResponse(payload = {}) {
  if (!captureActive) return;

  const matched = networkLog.find((entry) => entry.id === payload.requestId);
  if (!matched) return;

  matched.status = payload.status;
  matched.responseHeaders = payload.headers || {};
  matched.responseBody = payload.body || null;
  matched.responseTimestamp = new Date().toISOString();
}

function handleStorageSnapshot(payload = {}) {
  if (!captureActive) return;

  storageSnapshot = {
    ...(storageSnapshot || {}),
    timestamp: new Date().toISOString(),
    localStorage: payload.localStorage ?? storageSnapshot?.localStorage ?? {},
    sessionStorage: payload.sessionStorage ?? storageSnapshot?.sessionStorage ?? {},
    indexedDB: payload.indexedDB ?? storageSnapshot?.indexedDB ?? null,
    storageDiff: payload.storageDiff ?? storageSnapshot?.storageDiff ?? null,
    url: payload.url || storageSnapshot?.url || null
  };
}

function handleInjectedState(payload = {}) {
  if (!captureActive) return;

  injectedStateSnapshot = {
    timestamp: new Date().toISOString(),
    nextData: payload.nextData || null,
    initialState: payload.initialState || null,
    nuxt: payload.nuxt || null,
    vuex: payload.vuex || null,
    redux: payload.redux || null,
    url: payload.url || null
  };
}

function handlePageEvent(payload = {}) {
  if (!captureActive) return;

  const event = {
    id: generateId(),
    timestamp: new Date().toISOString(),
    eventType: payload.eventType,
    url: payload.url,
    questionNumber: payload.questionNumber || null,
    section: payload.section || null,
    part: payload.part || null,
    details: payload.details || {},
    storageSnapshot: storageSnapshot ? { ...storageSnapshot } : null,
    injectedState: injectedStateSnapshot ? { ...injectedStateSnapshot } : null,
    recentNetwork: getRecentNetwork()
  };

  eventLog.push(event);
}

function handleToolbarConfig(payload) {
  if (!captureActive || !eventLog.length) return;
  eventLog[eventLog.length - 1].toolbar = payload;
}

function handleDomStyles(payload) {
  if (!captureActive || !eventLog.length) return;
  eventLog[eventLog.length - 1].domStyles = payload;
}

function handleMathElements(payload) {
  if (!captureActive || !eventLog.length) return;
  eventLog[eventLog.length - 1].mathElements = payload;
}

function handleDomSnapshot(payload) {
  if (!captureActive || !eventLog.length) return;
  eventLog[eventLog.length - 1].domSnapshot = payload;
}

function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

function getRecentNetwork() {
  return networkLog.slice(-10).map((entry) => ({
    id: entry.id,
    timestamp: entry.timestamp,
    method: entry.method,
    url: maskUrl(entry.url),
    status: entry.status,
    bodySize: entry.responseBody ? JSON.stringify(entry.responseBody).length : 0
  }));
}

function maskUrl(url) {
  try {
    const parsed = new URL(url);
    const params = new URLSearchParams(parsed.search);
    const masked = [];
    for (const [key, value] of params) {
      if (['token', 'key', 'secret', 'auth', 'password'].some((part) => key.toLowerCase().includes(part))) {
        masked.push(`${key}=[REDACTED]`);
      } else {
        masked.push(`${key}=${value}`);
      }
    }
    parsed.search = masked.join('&');
    return parsed.toString();
  } catch {
    return url;
  }
}

function startCapture() {
  captureActive = true;
  initSession();
  console.log('[AP-Capture] Capture started');
  return saveManifest();
}

function stopCapture() {
  captureActive = false;
  console.log('[AP-Capture] Capture stopped');
  return exportSession();
}

async function downloadJsonFile(content, filename) {
  const dataUrl = `data:application/json;charset=utf-8,${encodeURIComponent(content)}`;
  return chrome.downloads.download({
    url: dataUrl,
    filename,
    saveAs: false
  });
}

async function downloadHtmlFile(content, filename) {
  const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(content)}`;
  return chrome.downloads.download({
    url: dataUrl,
    filename,
    saveAs: false
  });
}

async function saveManifest() {
  const manifest = {
    sessionId,
    startedAt: new Date().toISOString(),
    version: '1.0.0',
    description: 'AP Exam Capture Session',
    targetUrl: 'https://mokaoai.com/en/ap/',
    captureSettings: {
      networkLogging: true,
      storageCapture: true,
      storageDiff: true,
      indexedDBCapture: true,
      injectedStateCapture: true,
      eventCapture: true,
      toolbarCapture: true,
      domStylesCapture: true,
      mathCapture: true
    },
    eventIndex: eventLog.map((event) => ({
      id: event.id,
      timestamp: event.timestamp,
      eventType: event.eventType,
      questionNumber: event.questionNumber,
      url: event.url
    })),
    networkIndex: networkLog.slice(0, 100).map((entry) => ({
      id: entry.id,
      timestamp: entry.timestamp,
      method: entry.method,
      url: maskUrl(entry.url),
      status: entry.status
    }))
  };

  const manifestDownloadId = await downloadJsonFile(
    JSON.stringify(manifest, null, 2),
    `${sessionId}/session-manifest.json`
  );
  return { manifestDownloadId };
}

async function exportSession() {
  const activeSessionId = sessionId || `ap-capture-${Date.now()}`;
  const sessionData = {
    sessionId: activeSessionId,
    exportedAt: new Date().toISOString(),
    summary: {
      totalEvents: eventLog.length,
      totalNetworkEntries: networkLog.length,
      captureActive
    },
    manifest: {
      sessionId: activeSessionId,
      startedAt: new Date().toISOString(),
      version: '1.0.0'
    },
    timeline: eventLog.map((event) => ({
      id: event.id,
      timestamp: event.timestamp,
      eventType: event.eventType,
      questionNumber: event.questionNumber,
      section: event.section,
      part: event.part,
      url: event.url,
      hasStorage: !!event.storageSnapshot,
      hasInjectedState: !!event.injectedState,
      hasToolbar: !!event.toolbar,
      hasDomStyles: !!event.domStyles,
      hasMath: !!event.mathElements
    })),
    events: eventLog,
    network: networkLog.slice(0, 500)
  };

  const exportDownloadId = await downloadJsonFile(
    JSON.stringify(sessionData, null, 2),
    `${activeSessionId}/session-export.json`
  );
  const indexDownloadId = await downloadHtmlFile(
    generateHtmlIndex(activeSessionId),
    `${activeSessionId}/index.html`
  );

  return {
    sessionId: activeSessionId,
    exportDownloadId,
    indexDownloadId,
    eventCount: eventLog.length,
    networkCount: networkLog.length
  };
}

function generateHtmlIndex(activeSessionId) {
  const eventList = eventLog.slice(0, 50).map((event) => `
    <tr>
      <td>${event.timestamp}</td>
      <td>${event.eventType}</td>
      <td>${event.questionNumber || '-'}</td>
      <td>${String(event.url || '').substring(0, 80)}</td>
    </tr>
  `).join('');

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AP Exam Capture - ${activeSessionId}</title>
  <style>
    body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
    h1 { color: #333; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background: #f5f5f5; }
    .summary { background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 20px 0; }
  </style>
</head>
<body>
  <h1>AP Exam Capture - Session ${activeSessionId}</h1>
  <div class="summary">
    <p>Total events: ${eventLog.length}</p>
    <p>Total network requests: ${networkLog.length}</p>
    <p>Exported at: ${new Date().toISOString()}</p>
  </div>
  <table>
    <tr>
      <th>Time</th>
      <th>Event Type</th>
      <th>Question</th>
      <th>URL</th>
    </tr>
    ${eventList}
  </table>
</body>
</html>`;
}

console.log('[AP-Capture] Service Worker loaded');
