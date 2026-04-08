import {
  ensureStateShape,
  loadState,
  persistState
} from "../../exam/mock-config.js";

const root = document.getElementById("entrance-root");
const params = new URLSearchParams(window.location.search);
const examId = params.get("examId");

init().catch((error) => {
  console.error(error);
  root.innerHTML = `<section class="panel-card"><p>Failed to open: ${escapeHtml(String(error.message || error))}</p></section>`;
});

async function init() {
  if (!examId) throw new Error("Missing examId");

  const response = await fetch(window.sitePath(`/mock-data/ap-exam-${examId}.json`));
  if (!response.ok) throw new Error("Missing local exam data");

  const exam = await response.json();
  const state = loadState(examId);
  if (!state) throw new Error("No local start state found");

  ensureStateShape(exam, state);
  persistState(examId, state);

  const sectionIndex = Number(state.sectionIndex || 0);
  const section = exam.sections[sectionIndex];
  const sectionLabel = section?.title || `Section ${sectionIndex + 1}`;

  // 计算总题数
  const totalQuestions = (exam.sections || []).reduce((sum, s) => sum + (s.questions?.length || 0), 0);
  const sectionQuestions = section?.questions?.length || 0;

  // 计算总时间（所有模块）
  const totalMinutes = (exam.sections || []).reduce((sum, s) => {
    const t = s.time_limit_minutes;
    return sum + (typeof t === 'number' ? t : 0);
  }, 0);
  const sectionMinutes = section?.time_limit_minutes || 0;

  // 规则说明文字
  const directions = section?.directions
    ? section.directions.replace(/\n+/g, ' ').trim()
    : 'Please read all directions carefully before starting.';

  root.innerHTML = `
    <section class="panel-card entrance-simple">
      <div class="entrance-title">${escapeHtml(sectionLabel)}</div>

      <p class="entrance-rules">${escapeHtml(directions)}</p>

      <div class="entrance-meta">
        <div class="meta-item">
          <span class="meta-value">${sectionQuestions}</span>
          <span class="meta-label">Questions</span>
        </div>
        <div class="meta-divider"></div>
        <div class="meta-item">
          <span class="meta-value">${sectionMinutes} min</span>
          <span class="meta-label">Time Limit</span>
        </div>
        ${exam.sections.length > 1 ? `
        <div class="meta-divider"></div>
        <div class="meta-item">
          <span class="meta-value">${totalQuestions}</span>
          <span class="meta-label">Total Questions</span>
        </div>
        ` : ''}
      </div>

      <div class="entrance-start">
        <button class="primary-button" id="start-btn">Start Section</button>
      </div>
    </section>
  `;

  document.getElementById("start-btn")?.addEventListener("click", () => {
    const query = new URLSearchParams({ examId, sectionIndex: String(sectionIndex) });
    window.location.href = window.sitePath(`/ap/start/directions/?${query.toString()}`);
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
