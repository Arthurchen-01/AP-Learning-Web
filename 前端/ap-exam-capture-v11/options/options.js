// options/options.js
// AP Exam Capture - Options Page

document.addEventListener('DOMContentLoaded', () => {
  const statusEl = document.getElementById('status');
  const statusTextEl = document.getElementById('status-text');
  const eventCountEl = document.getElementById('event-count');
  const networkCountEl = document.getElementById('network-count');
  const sessionIdEl = document.getElementById('session-id');

  const startBtn = document.getElementById('start-btn');
  const stopBtn = document.getElementById('stop-btn');
  const exportBtn = document.getElementById('export-btn');

  // 获取当前状态
  async function updateStatus() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id) return;

      const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_STATUS' });
      
      if (response?.captureActive) {
        statusEl.className = 'status active';
        statusTextEl.textContent = '采集中';
        startBtn.disabled = true;
        stopBtn.disabled = false;
      } else {
        statusEl.className = 'status inactive';
        statusTextEl.textContent = '未激活';
        startBtn.disabled = false;
        stopBtn.disabled = true;
      }

      eventCountEl.textContent = response?.eventCount || 0;
      networkCountEl.textContent = response?.networkCount || 0;
      sessionIdEl.textContent = response?.sessionId?.substring(0, 12) || '-';
    } catch (err) {
      console.log('Cannot get status, likely not on exam page');
    }
  }

  // 开始采集
  startBtn.addEventListener('click', async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab?.id) {
        await chrome.tabs.sendMessage(tab.id, { type: 'START_CAPTURE' });
        updateStatus();
      }
    } catch (err) {
      alert('请先打开 AP 模考页面');
    }
  });

  // 停止采集
  stopBtn.addEventListener('click', async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab?.id) {
        await chrome.tabs.sendMessage(tab.id, { type: 'STOP_CAPTURE' });
        updateStatus();
      }
    } catch (err) {
      console.error(err);
    }
  });

  // 导出数据
  exportBtn.addEventListener('click', async () => {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'EXPORT_SESSION' });
      console.log('Export triggered', response);
    } catch (err) {
      console.error(err);
    }
  });

  // 定期更新状态
  updateStatus();
  setInterval(updateStatus, 2000);
});