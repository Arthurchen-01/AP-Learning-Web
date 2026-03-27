import {
  PREPARING_DELAY_MS,
  createFreshState,
  ensureStateShape,
  loadState,
  persistState
} from "/ap/exam/mock-config.js";

const root = document.getElementById("preparing-root");
const params = new URLSearchParams(window.location.search);
const examId = params.get("examId");
const mode = params.get("mode") || "start";
const timekeepingModeOn = params.get("timekeepingModeOn") === "true";
const talkModeOn = params.get("talkModeOn") === "true";

init().catch((error) => {
  console.error(error);
  root.innerHTML = `<section class="panel-card"><p>Failed to prepare this paper: ${escapeHtml(String(error.message || error))}</p></section>`;
});

async function init() {
  if (!examId) {
    throw new Error("Missing examId");
  }

  const response = await fetch(`/mock-data/ap-exam-${examId}.json`);
  if (!response.ok) {
    throw new Error("Missing local exam data");
  }

  const exam = await response.json();
  const state = mode === "resume" ? (loadState(examId) || createFreshState(exam)) : createFreshState(exam);
  ensureStateShape(exam, state);

  state.startConfig = {
    timekeepingModeOn,
    talkModeOn
  };

  if (mode !== "resume") {
    state.sectionIndex = 0;
    state.questionIndex = 0;
    state.results = null;
    state.startedAt = null;
  }

  persistState(examId, state);

  root.innerHTML = `
    <section class="panel-card preparing-card">
      <div class="loader-orbit" aria-hidden="true"></div>
      <div class="micro-label">Preparing your test</div>
      <h1>We're Preparing Your Test Exam</h1>
      <p class="lede">This may take up to a minute. Please don't refresh this page or exit.</p>
      <p class="muted-copy">Loading section rules, restoring your local answers, and preparing the official test shell.</p>
    </section>
  `;

  window.setTimeout(() => {
    const query = new URLSearchParams({ examId, mode });
    window.location.href = `/ap/start/entrance/?${query.toString()}`;
  }, PREPARING_DELAY_MS);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
