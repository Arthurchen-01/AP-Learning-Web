document.addEventListener('DOMContentLoaded', async () => {
  const statusEl = document.getElementById('status');
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const exportBtn = document.getElementById('exportBtn');
  const infoEl = document.getElementById('info');

  const targetPatterns = [
    /mokaoai\.com/i,
    /examId=/i,
    /\/ap\//i,
    /mokao/i
  ];

  async function getActiveTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
  }

  async function getTabStatus(tabId) {
    return chrome.tabs.sendMessage(tabId, { type: 'GET_STATUS' });
  }

  async function ensureContentScript(tabId) {
    try {
      await chrome.tabs.sendMessage(tabId, { type: 'GET_STATUS' });
      return true;
    } catch {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: ['src/content/content-script.js']
      });
      return true;
    }
  }

  function setBadge(text, color) {
    chrome.action.setBadgeText({ text });
    if (color) chrome.action.setBadgeBackgroundColor({ color });
  }

  function renderIdle(url) {
    statusEl.textContent = 'Ready';
    statusEl.className = 'status active';
    statusEl.style.background = '#d4edda';
    statusEl.style.color = '#155724';
    infoEl.textContent = `Current: ${url.substring(0, 35)}...`;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    exportBtn.disabled = false;
    setBadge('', null);
  }

  function renderRunning() {
    statusEl.textContent = 'Capturing...';
    statusEl.className = 'status active';
    statusEl.style.background = '#f8d7da';
    statusEl.style.color = '#721c24';
    infoEl.textContent = 'Recording page activity...';
    startBtn.disabled = true;
    stopBtn.disabled = false;
    exportBtn.disabled = true;
    setBadge('REC', '#dc3545');
  }

  function renderError(message) {
    statusEl.textContent = 'Error';
    statusEl.className = 'status inactive';
    statusEl.style.background = '#fff3cd';
    statusEl.style.color = '#856404';
    infoEl.textContent = message;
  }

  const tab = await getActiveTab();
  if (!tab || !tab.url) {
    renderError('Cannot read the current tab.');
    return;
  }

  const isTarget = targetPatterns.some((pattern) => pattern.test(tab.url));
  if (!isTarget) {
    renderError(`Current: ${tab.url.substring(0, 40)}`);
    startBtn.disabled = true;
    stopBtn.disabled = true;
    exportBtn.disabled = true;
    setBadge('!', '#ffc107');
    return;
  }

  try {
    const response = await getTabStatus(tab.id);
    if (response?.captureActive) {
      renderRunning();
    } else {
      renderIdle(tab.url);
    }
  } catch {
    renderIdle(tab.url);
  }

  startBtn.addEventListener('click', async () => {
    try {
      await ensureContentScript(tab.id);
      await chrome.tabs.sendMessage(tab.id, { type: 'START_CAPTURE' });
      renderRunning();
    } catch (error) {
      console.error('Start capture error:', error);
      renderError(error.message || 'Failed to start capture.');
    }
  });

  stopBtn.addEventListener('click', async () => {
    try {
      await chrome.tabs.sendMessage(tab.id, { type: 'STOP_CAPTURE' });
      renderIdle(tab.url);
      setBadge('OK', '#28a745');
    } catch (error) {
      console.error('Stop capture error:', error);
      renderError(error.message || 'Failed to stop capture.');
    }
  });

  exportBtn.addEventListener('click', async () => {
    try {
      infoEl.textContent = 'Exporting...';
      const result = await chrome.runtime.sendMessage({ type: 'EXPORT_SESSION' });
      if (!result?.ok) {
        throw new Error(result?.error || 'Export failed.');
      }
      infoEl.textContent = `Export completed. Files: ${result.eventCount || 0} events, ${result.networkCount || 0} requests.`;
      setBadge('OK', '#28a745');
    } catch (error) {
      console.error('Export error:', error);
      renderError(error.message || 'Failed to export.');
    }
  });
});
