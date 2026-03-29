import {
  ENTRANCE_PANELS,
  ensureStateShape,
  loadState,
  persistState
} from "../../exam/mock-config.js";

const root = document.getElementById("entrance-root");
const params = new URLSearchParams(window.location.search);
const examId = params.get("examId");

init().catch((error) => {
  console.error(error);
  root.innerHTML = `<section class="panel-card"><p>Failed to open the test shell: ${escapeHtml(String(error.message || error))}</p></section>`;
});

async function init() {
  if (!examId) {
    throw new Error("Missing examId");
  }

  const response = await fetch(window.sitePath(`/mock-data/ap-exam-${examId}.json`));
  if (!response.ok) {
    throw new Error("Missing local exam data");
  }

  const exam = await response.json();
  const state = loadState(examId);
  if (!state) {
    throw new Error("No local start state found");
  }

  ensureStateShape(exam, state);
  persistState(examId, state);

  root.innerHTML = `
    <section class="panel-card entrance-card">
      <div class="micro-label">Official Practice Shell</div>
      <h1>AP Practice Test</h1>
      <div class="entrance-grid">
        ${ENTRANCE_PANELS.map((panel) => `
          <article class="info-card">
            <strong>${escapeHtml(panel.title)}</strong>
            <p>${escapeHtml(panel.body)}</p>
          </article>
        `).join("")}
      </div>
      <div class="entrance-footer">
        <span>${escapeHtml(cleanText(exam.title || exam.subjectName || "AP Practice Test"))}</span>
        <button class="primary-button" type="button" id="next-button">Next</button>
      </div>
    </section>
  `;

  document.getElementById("next-button")?.addEventListener("click", () => {
    const query = new URLSearchParams({
      examId,
      sectionIndex: String(state.sectionIndex || 0)
    });
    window.location.href = window.sitePath(`/ap/start/directions/?${query.toString()}`);
  });
}

function cleanText(value) {
  return String(value || "").replaceAll("路", "·").trim();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
