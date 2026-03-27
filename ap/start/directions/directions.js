import {
  BREAK_DURATION_SEC,
  createFreshState,
  deriveSectionMeta,
  ensureStateShape,
  formatClock,
  loadState,
  persistState
} from "/ap/exam/mock-config.js";

const root = document.getElementById("directions-root");
const params = new URLSearchParams(window.location.search);
const examId = params.get("examId");
const requestedSectionIndex = Number(params.get("sectionIndex") || "0");

let exam = null;
let state = null;
let breakTimerId = null;
let breakRemaining = BREAK_DURATION_SEC;

init().catch((error) => {
  console.error(error);
  root.innerHTML = `<section class="panel-card"><p>Failed to load directions: ${escapeHtml(String(error.message || error))}</p></section>`;
});

async function init() {
  if (!examId) {
    throw new Error("Missing examId");
  }

  const response = await fetch(`/mock-data/ap-exam-${examId}.json`);
  if (!response.ok) {
    throw new Error("Missing local exam data");
  }

  exam = await response.json();
  state = loadState(examId) || createFreshState(exam);
  ensureStateShape(exam, state);
  state.sectionIndex = clampSectionIndex(requestedSectionIndex, exam.sections.length);
  persistState(examId, state);
  bindHandlers();
  render();
}

function bindHandlers() {
  root.addEventListener("click", (event) => {
    const target = event.target.closest("[data-action]");
    if (!target) {
      return;
    }

    const action = target.dataset.action;
    if (action === "skip-break") {
      recordBreak(true);
      return;
    }
    if (action === "continue-break") {
      recordBreak(false);
      return;
    }
    if (action === "enter-exam" || action === "close-directions") {
      state.stage = "question";
      state.sectionStates[state.sectionIndex].status = "active";
      state.startedAt = state.startedAt || new Date().toISOString();
      persistState(examId, state);
      window.location.href = `/ap/exam/?examId=${encodeURIComponent(examId)}`;
    }
  });
}

function render() {
  stopBreakClock();
  if (shouldShowBreak()) {
    renderBreak();
    startBreakClock();
    return;
  }
  renderDirections();
}

function renderBreak() {
  const nextLabel = `Module ${state.sectionIndex + 1}`;
  root.innerHTML = `
    <section class="panel-card break-shell">
      <div class="micro-label">Scheduled break</div>
      <h1>Take a break</h1>
      <p class="lede">This module is over. You may take a scheduled break before you continue to ${escapeHtml(nextLabel)}.</p>
      <div class="break-clock">${formatClock(breakRemaining)}</div>
      <div class="action-strip">
        <button class="secondary-button" type="button" data-action="skip-break">Skip Break</button>
        <button class="primary-button" type="button" data-action="continue-break">Continue after Break</button>
      </div>
    </section>
  `;
}

function renderDirections() {
  const section = exam.sections[state.sectionIndex];
  const meta = deriveSectionMeta(section, exam);
  root.innerHTML = `
    <section class="panel-card directions-shell">
      <div class="directions-topline">
        <span class="micro-label">${escapeHtml(meta.subjectLine)}</span>
        <button class="icon-close" type="button" data-action="close-directions" aria-label="Close">×</button>
      </div>
      <div class="directions-frame">
        <div class="directions-heading">
          <h1>${escapeHtml(meta.sectionLabel)}</h1>
          <h2>${escapeHtml(meta.partLabel)}</h2>
        </div>
        <div class="directions-metadata">
          <div><strong>Time</strong><span>${escapeHtml(meta.timeLabel)}</span></div>
          <div><strong>Questions</strong><span>${meta.questionCount}</span></div>
          <div><strong>Calculator</strong><span>${escapeHtml(meta.calculatorRule)}</span></div>
        </div>
        <div class="directions-copy">${formatDirections(section.directions)}</div>
      </div>
      <div class="action-strip">
        <button class="primary-button" type="button" data-action="enter-exam">${state.sectionStates[state.sectionIndex].status === "active" ? "Resume Test" : "Continue"}</button>
      </div>
    </section>
  `;
}

function shouldShowBreak() {
  return state.sectionIndex > 0 && !state.breakState?.[state.sectionIndex];
}

function recordBreak(skipped) {
  state.breakState = state.breakState || {};
  state.breakState[state.sectionIndex] = {
    skipped,
    recordedAt: new Date().toISOString()
  };
  persistState(examId, state);
  render();
}

function startBreakClock() {
  stopBreakClock();
  breakTimerId = window.setInterval(() => {
    breakRemaining -= 1;
    const clock = root.querySelector(".break-clock");
    if (clock) {
      clock.textContent = formatClock(breakRemaining);
    }
    if (breakRemaining <= 0) {
      recordBreak(false);
    }
  }, 1000);
}

function stopBreakClock() {
  if (breakTimerId) {
    window.clearInterval(breakTimerId);
    breakTimerId = null;
  }
}

function formatDirections(text) {
  return escapeHtml(String(text || ""))
    .replace(/\n/g, "<br>");
}

function clampSectionIndex(index, total) {
  if (Number.isNaN(index) || index < 0) {
    return 0;
  }
  return Math.min(index, total - 1);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
