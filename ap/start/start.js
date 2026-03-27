import {
  START_OPTIONS,
  createFreshState,
  ensureStateShape,
  loadState,
  persistState,
  storageKey
} from "/ap/exam/mock-config.js";

const root = document.getElementById("start-root");
const params = new URLSearchParams(window.location.search);
const examId = params.get("examId");

let exam = null;
let catalogItem = null;
let progress = null;
let config = Object.fromEntries(START_OPTIONS.map((item) => [item.key, item.defaultValue]));

init().catch((error) => {
  console.error(error);
  root.innerHTML = `<div class="panel-card"><p>Failed to load the start page: ${escapeHtml(String(error.message || error))}</p></div>`;
});

async function init() {
  if (!examId) {
    throw new Error("Missing examId");
  }

  const [catalogResponse, examResponse] = await Promise.all([
    fetch("/mock-data/exam-catalog.json"),
    fetch(`/mock-data/ap-exam-${examId}.json`)
  ]);

  if (!catalogResponse.ok || !examResponse.ok) {
    throw new Error("Missing local exam data");
  }

  const catalog = await catalogResponse.json();
  exam = await examResponse.json();
  catalogItem = catalog.items.find((entry) => entry.examId === examId) || {};
  progress = getProgressState(examId);

  const existingState = loadState(examId) || createFreshState(exam);
  ensureStateShape(exam, existingState);
  config = { ...config, ...existingState.startConfig };

  render();
  bindHandlers();
}

function bindHandlers() {
  root.addEventListener("click", (event) => {
    const target = event.target.closest("[data-action]");
    if (!target) {
      return;
    }

    const action = target.dataset.action;
    if (action === "toggle-option") {
      const key = target.dataset.key;
      config[key] = !config[key];
      render();
      return;
    }

    if (action === "start-new") {
      localStorage.removeItem(storageKey(examId));
      goPreparing("start");
      return;
    }

    if (action === "resume") {
      goPreparing("resume");
    }
  });
}

function goPreparing(mode) {
  const query = new URLSearchParams({
    examId,
    mode,
    timekeepingModeOn: String(Boolean(config.timekeepingModeOn)),
    talkModeOn: String(Boolean(config.talkModeOn))
  });
  window.location.href = `/ap/start/preparing/?${query.toString()}`;
}

function render() {
  const displayTitle = catalogItem.title || exam.title || examId;
  root.innerHTML = `
    <section class="panel-card choose-card">
      <div class="choose-head">
        <div>
          <div class="micro-label">Full-Length Practice</div>
          <h1>Choose Full-Length Practice</h1>
          <p class="lede">${escapeHtml(cleanText(displayTitle))}</p>
        </div>
        <a class="text-link" href="/mock/">Back</a>
      </div>

      <div class="option-stack">
        ${START_OPTIONS.map((item) => `
          <button class="setting-row" type="button" data-action="toggle-option" data-key="${item.key}">
            <span>
              <strong>${escapeHtml(item.label)}</strong>
              <span>${escapeHtml(item.description)}</span>
            </span>
            <span class="toggle-pill ${config[item.key] ? "is-on" : ""}">
              ${escapeHtml(config[item.key] ? item.enabledLabel : item.disabledLabel)}
            </span>
          </button>
        `).join("")}
      </div>

      <div class="notice-strip">This imported paper currently runs in practice mode only. Answers and progress save locally in this browser.</div>

      <div class="action-strip">
        <button class="primary-button" type="button" data-action="start-new">Start</button>
        ${progress.canResume ? `<button class="secondary-button" type="button" data-action="resume">Resume</button>` : ""}
      </div>

      ${progress.hasProgress ? `
        <div class="status-note">
          <strong>Local progress found.</strong>
          <span>${progress.canResume ? "Resume your last attempt or start over." : "You can start a new attempt from this page."}</span>
        </div>
      ` : ""}
    </section>
  `;
}

function getProgressState(targetExamId) {
  try {
    const state = loadState(targetExamId);
    if (!state) {
      return { hasProgress: false, canResume: false };
    }
    const hasAnswers = (state.sectionStates || []).some((section) =>
      (section.answers || []).some((answer) => Array.isArray(answer) ? answer.length > 0 : String(answer || "").trim().length > 0)
    );
    const hasProgress = Boolean(state.startedAt || hasAnswers || state.results);
    return {
      hasProgress,
      canResume: hasProgress && !state.results
    };
  } catch (error) {
    console.warn("Failed to parse local progress", error);
    return { hasProgress: false, canResume: false };
  }
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
