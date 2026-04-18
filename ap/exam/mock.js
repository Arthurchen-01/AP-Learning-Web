import {
  TOOL_MENU_ITEMS,
  createFreshState,
  deriveSectionMeta,
  ensureStateShape,
  formatClock,
  loadExamShellData,
  loadState,
  normalizeExamText,
  persistState,
  storageKey
} from "./mock-config.js";

const app = document.getElementById("app");

/* ─── Math rendering helpers (v2: KaTeX auto-render) ─── */

let katexLoadPromise = null;

function loadKatex() {
  if (katexLoadPromise) return katexLoadPromise;
  katexLoadPromise = new Promise((resolve) => {
    if (window.katex && window.renderMathInElement) { resolve(); return; }
    if (!document.querySelector("link[data-katex-styles]")) {
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css";
      css.dataset.katexStyles = "true";
      document.head.appendChild(css);
    }
    const loadAutoRender = () => {
      if (window.renderMathInElement) { resolve(); return; }
      const ar = document.createElement("script");
      ar.src = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js";
      ar.onload = () => resolve();
      ar.onerror = () => resolve();
      document.head.appendChild(ar);
    };
    if (window.katex) { loadAutoRender(); return; }
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js";
    s.onload = loadAutoRender;
    s.onerror = () => resolve();
    document.head.appendChild(s);
  });
  return katexLoadPromise;
}

function normalizeLatexForKatex(html) {
  return html
    .replace(/\\begin\{tabular\}\{([^}]*)\}([\s\S]*?)\\end\{tabular\}/g, (_, cols, body) => `$$\\begin{array}{${cols}}${body}\\end{array}$$`)
    .replace(/\\begin\{tabular\}/g, "\\begin{array}")
    .replace(/\\end\{tabular\}/g, "\\end{array}");
}

function sanitizeImportedHtml(value) {
  const template = document.createElement("template");
  template.innerHTML = String(value || "").trim();
  template.content.querySelectorAll("script, style").forEach((node) => node.remove());
  template.content.querySelectorAll("annotation").forEach((node) => node.remove());
  template.content.querySelectorAll(".formatted_line_break").forEach((node) => node.replaceWith(document.createElement("br")));
  template.content.querySelectorAll(".choiceNum").forEach((node) => node.remove());
  template.content.querySelectorAll(".choiceTxt, .stem_paragraph").forEach((node) => {
    node.replaceWith(...node.childNodes);
  });
  template.content.querySelectorAll("semantics").forEach((node) => {
    const keep = [...node.childNodes].filter((child) => child.nodeType !== Node.ELEMENT_NODE || child.tagName.toLowerCase() !== "annotation");
    if (keep.length) {
      node.replaceWith(...keep);
    }
  });
  template.content.querySelectorAll("img").forEach((node) => {
    node.loading = "lazy";
  });
  return template.innerHTML.trim();
}

function renderLatexInElement(root) {
  if (!window.katex || !root) {
    return;
  }

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node.parentElement;
      if (!parent) {
        return NodeFilter.FILTER_REJECT;
      }
      if (parent.closest("math, .katex, script, style, textarea, pre, code")) {
        return NodeFilter.FILTER_REJECT;
      }
      return /\$\$[\s\S]+?\$\$|\$[^$]+\$|\\\([\s\S]+?\\\)|\\\[[\s\S]+?\\\]/.test(node.textContent)
        ? NodeFilter.FILTER_ACCEPT
        : NodeFilter.FILTER_REJECT;
    }
  });

  const textNodes = [];
  while (walker.nextNode()) {
    textNodes.push(walker.currentNode);
  }

  const latexPattern = /\$\$([\s\S]+?)\$\$|\$([^$]+)\$|\\\(([\s\S]+?)\\\)|\\\[([\s\S]+?)\\\]/g;
  textNodes.forEach((node) => {
    const text = node.textContent || "";
    let lastIndex = 0;
    let match;
    const fragment = document.createDocumentFragment();

    while ((match = latexPattern.exec(text))) {
      if (match.index > lastIndex) {
        fragment.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
      }

      const latex = match[1] || match[2] || match[3] || match[4] || "";
      const displayMode = Boolean(match[1] || match[4]);
      const wrapper = document.createElement(displayMode ? "div" : "span");
      try {
        wrapper.innerHTML = window.katex.renderToString(latex.trim(), { throwOnError: false, displayMode });
      } catch {
        wrapper.textContent = match[0];
      }
      fragment.appendChild(wrapper);
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex === 0) {
      return;
    }
    if (lastIndex < text.length) {
      fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
    }
    node.replaceWith(fragment);
  });
}

function formatText(value) {
  if (!value) return "";
  // HTML (MathML etc.) — sanitize and return
  if (/<[a-z][\s\S]*>/i.test(value)) {
    return sanitizeImportedHtml(value);
  }
  // Plain text (LaTeX $...$ or plain) — escape and return; auto-render handles $ later
  const cleaned = normalizeExamText(value);
  return escapeHtml(cleaned).replace(/\n/g, "<br>");
}

function replaceBrokenImage(image) {
  if (!image || image.dataset.fallbackApplied === "true") {
    return;
  }
  const altText = String(image.getAttribute("alt") || "Figure unavailable.").trim();
  const fallback = document.createElement("div");
  fallback.className = "image-fallback";
  fallback.textContent = altText;
  image.dataset.fallbackApplied = "true";
  image.replaceWith(fallback);
}

function attachImageFallbacks() {
  document.querySelectorAll(".question-text img, .option-copy img").forEach((image) => {
    if (image.dataset.fallbackBound === "true") {
      return;
    }
    image.dataset.fallbackBound = "true";
    image.addEventListener("error", () => replaceBrokenImage(image), { once: true });
    if (image.complete && image.naturalWidth === 0) {
      replaceBrokenImage(image);
    }
  });
}

async function renderMathAfterMount() {
  await loadKatex();
  if (!window.katex) return;

  document.querySelectorAll(".question-text, .option-copy, .frq-part-content").forEach((el) => {
    if (el.dataset.mathRendered === "true") return;
    el.dataset.mathRendered = "true";
    el.innerHTML = normalizeLatexForKatex(el.innerHTML);
    renderLatexInElement(el);
  });
}
const params = new URLSearchParams(window.location.search);
const examId = params.get("examId");

const RESULTS_EXAM_IDS = new Set(["1902622411800285184", "calc-bc-2018-intl", "1902622411338911744", "calc-bc-2017-intl", "2016Intl", "calc-bc-2016-intl", "2015Intl", "calc-bc-2015-intl", "2018Intl_MECH", "physics-c-mech-2018-intl", "2018Intl_EM", "physics-c-em-2018-intl", "2017Intl_MECH", "physics-c-mech-2017-intl"]);
const TRUNK_CONTRACT_PATHS = {
  'calc-bc-2018-intl': '/v2/data/contracts/ap-calculus-bc-trunk-contract.json',
  'calc-bc-2017-intl': '/v2/data/contracts/ap-calculus-bc-trunk-contract.json',
  'calc-bc-2016-intl': '/v2/data/contracts/ap-calculus-bc-trunk-contract.json',
  'calc-bc-2015-intl': '/v2/data/contracts/ap-calculus-bc-trunk-contract.json',
  'physics-c-mech-2018-intl': '/v2/data/contracts/ap-physics-c-mechanics-trunk-contract.json',
  'physics-c-em-2018-intl': '/v2/data/contracts/ap-physics-c-electricity-magnetism-trunk-contract.json'
};
const CALC_BC_TRUNK_CONTRACT_PATH = TRUNK_CONTRACT_PATHS['calc-bc-2018-intl'];

function getBranchMappingPath() {
  const examIdStr = String(examId || "");
  if (examIdStr === "1902622411338911744" || examIdStr === "calc-bc-2017-intl") {
    return "/v2/data/calc-bc-2017-intl/question-branch-mapping.json";
  }
  if (examIdStr === "2016Intl" || examIdStr === "calc-bc-2016-intl") {
    return "/v2/data/calc-bc-2016-intl/question-branch-mapping.json";
  }
  if (examIdStr === "2015Intl" || examIdStr === "calc-bc-2015-intl") {
    return "/v2/data/calc-bc-2015-intl/question-branch-mapping.json";
  }
  if (examIdStr === "2018Intl_MECH" || examIdStr === "physics-c-mech-2018-intl") {
    return "/v2/data/physics-c-mech-2018-intl/question-branch-mapping.json";
  }
  if (examIdStr === "2017Intl_MECH" || examIdStr === "physics-c-mech-2017-intl") {
    return "/v2/data/physics-c-mech-2017-intl/question-branch-mapping.json";
  }
  if (examIdStr === "2018Intl_EM" || examIdStr === "physics-c-em-2018-intl") {
    return "/v2/data/physics-c-em-2018-intl/question-branch-mapping.json";
  }
  return "/v2/data/calc-bc-2018-intl/question-branch-mapping.json";
}

let exam = null;
let state = null;
let timerId = null;
let branchDiagnosticsResources = null;
let answerKeyMap = null;

init().catch((error) => {
  console.error(error);
  app.innerHTML = `<div class="exam-center"><section class="shell-card"><h1>Unable to load this exam</h1><p>${escapeHtml(String(error.message || error))}</p></section></div>`;
});

async function init() {
  if (!examId) {
    throw new Error("Missing examId");
  }

  exam = await loadExamShellData(examId);
  branchDiagnosticsResources = await loadBranchDiagnosticsResources();
  answerKeyMap = await loadAnswerKeys();
  state = loadState(examId) || createFreshState(exam);
  ensureStateShape(exam, state);
  let stateChanged = false;
  if (!state.sectionStates[state.sectionIndex]) {
    state.sectionIndex = 0;
    stateChanged = true;
  }
  if (state.sectionStates[state.sectionIndex].status === "locked") {
    state.sectionStates[state.sectionIndex].status = "active";
    stateChanged = true;
  }
  if (stateChanged) {
    persistState(examId, state);
  }
  bindHandlers();
  render();
  startTimer();
}

function bindHandlers() {
  app.addEventListener("click", handleClick);
  app.addEventListener("change", handleChange);
  app.addEventListener("input", handleInput);
}

function handleClick(event) {
  const target = event.target.closest("[data-action]");
  if (!target) {
    return;
  }

  const action = target.dataset.action;
  if (action === "prev-question") {
    setQuestionIndex(state.questionIndex - 1);
    return;
  }
  if (action === "next-question") {
    const lastIndex = currentSection().questions.length - 1;
    if (state.questionIndex >= lastIndex) {
      state.stage = "review";
    } else {
      state.questionIndex += 1;
    }
    persistAndRender();
    return;
  }
  if (action === "go-question") {
    state.questionIndex = Number(target.dataset.questionIndex);
    state.stage = "question";
    state.ui.navigatorOpen = false;
    persistAndRender();
    return;
  }
  if (action === "toggle-flag") {
    const flags = sectionState().flagged;
    flags[state.questionIndex] = !flags[state.questionIndex];
    persistAndRender();
    return;
  }
  if (action === "open-review") {
    state.stage = "review";
    persistAndRender();
    return;
  }
  if (action === "back-to-questions") {
    state.stage = "question";
    persistAndRender();
    return;
  }
  if (action === "submit-module") {
    finishModule();
    return;
  }
  if (action === "advance-flow") {
    continueAfterModule();
    return;
  }
  if (action === "restart-exam") {
    showConfirm(
      'Are you absolutely sure?',
      'You can start over from here. Your answer records for this exam will be lost after this operation. Are you sure?',
      () => {
        localStorage.removeItem(storageKey(examId));
        localStorage.removeItem(`mokaoai-local-mock:${examId}`);
        window.location.href = window.sitePath(`/ap/start/?examId=${encodeURIComponent(examId)}`);
      }
    );
    return;
  }

  // ── 通用确认弹窗 ────────────────────────────────
  function showConfirm(title, body, onConfirm) {
    const shell = document.getElementById('confirm-shell');
    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-body').textContent = body;
    shell.style.display = 'flex';
    document.getElementById('confirm-cancel').onclick = () => { shell.style.display = 'none'; };
    document.getElementById('confirm-ok').onclick = () => { shell.style.display = 'none'; onConfirm(); };
  }
  if (action === "toggle-navigator") {
    state.ui.navigatorOpen = !state.ui.navigatorOpen;
    persistAndRender();
    return;
  }
  if (action === "toggle-directions") {
    state.ui.directionsOpen = !state.ui.directionsOpen;
    persistAndRender();
    return;
  }
  if (action === "toggle-more") {
    state.ui.moreOpen = !state.ui.moreOpen;
    persistAndRender();
    return;
  }
  if (action === "toggle-help") {
    state.ui.helpOpen = !state.ui.helpOpen;
    state.ui.moreOpen = true;
    persistAndRender();
    return;
  }
  if (action === "toggle-shortcuts") {
    state.ui.shortcutsOpen = !state.ui.shortcutsOpen;
    state.ui.moreOpen = true;
    persistAndRender();
    return;
  }
  if (action === "toggle-notes") {
    state.ui.notesOpen = !state.ui.notesOpen;
    persistAndRender();
    return;
  }
  if (action === "toggle-scratch") {
    state.ui.scratchOpen = !state.ui.scratchOpen;
    persistAndRender();
    return;
  }
  if (action === "toggle-line-reader") {
    state.ui.lineReaderOn = !state.ui.lineReaderOn;
    state.ui.moreOpen = true;
    persistAndRender();
    return;
  }
  if (action === "toggle-assistive") {
    state.ui.assistiveOpen = !state.ui.assistiveOpen;
    state.ui.moreOpen = true;
    persistAndRender();
    return;
  }
  if (action === "toggle-break-tool") {
    state.ui.onScheduleBreak = !state.ui.onScheduleBreak;
    state.ui.moreOpen = true;
    persistAndRender();
    return;
  }
  if (action === "toggle-hide-timer") {
    state.ui.hideTimer = !state.ui.hideTimer;
    persistAndRender();
    return;
  }
  if (action === "close-panel") {
    state.ui.helpOpen = false;
    state.ui.shortcutsOpen = false;
    state.ui.notesOpen = false;
    state.ui.scratchOpen = false;
    state.ui.assistiveOpen = false;
    state.ui.moreOpen = false;
    persistAndRender();
    return;
  }
  if (action === "expand-all" || action === "collapse-all") {
    persistAndRender();
    return;
  }
  if (action === "view-results") {
    state.stage = "results";
    persistAndRender();
  }
}

function handleChange(event) {
  const question = currentQuestion();
  if (!question) {
    return;
  }

  if (question.type === "single") {
    const input = event.target.closest("input[type='radio'][name='answer']");
    if (input) {
      sectionState().answers[state.questionIndex] = input.value;
      persistAndRender();
    }
    return;
  }

  if (question.type === "multi") {
    const input = event.target.closest("input[type='checkbox'][name='answer']");
    if (input) {
      const selected = new Set(sectionState().answers[state.questionIndex] || []);
      if (input.checked) {
        selected.add(input.value);
      } else {
        selected.delete(input.value);
      }
      sectionState().answers[state.questionIndex] = [...selected];
      persistAndRender();
    }
  }
}

function handleInput(event) {
  const scratchpad = event.target.closest(".scratchpad");
  if (scratchpad) {
    sectionState().scratchpad = scratchpad.value;
    persistState(examId, state);
    return;
  }

  const question = currentQuestion();
  if (!question || question.type !== "frq") {
    return;
  }
  const textarea = event.target.closest("textarea[name='answer']");
  if (!textarea) {
    return;
  }
  sectionState().answers[state.questionIndex] = textarea.value;
  persistState(examId, state);
}

function persistAndRender() {
  persistState(examId, state);
  render();
}

function setQuestionIndex(nextIndex) {
  const last = currentSection().questions.length - 1;
  state.questionIndex = Math.max(0, Math.min(last, nextIndex));
  persistAndRender();
}

function currentSection() {
  return exam.sections[state.sectionIndex];
}

function sectionState() {
  return state.sectionStates[state.sectionIndex];
}

function currentQuestion() {
  return currentSection().questions[state.questionIndex];
}

function startTimer() {
  stopTimer();
  timerId = window.setInterval(() => {
    if (!state.startConfig.timekeepingModeOn) {
      return;
    }
    if (!["question", "review"].includes(state.stage)) {
      return;
    }
    if (sectionState().status !== "active") {
      return;
    }
    sectionState().timeRemainingSec -= 1;
    if (sectionState().timeRemainingSec <= 0) {
      sectionState().timeRemainingSec = 0;
      finishModule();
      return;
    }
    persistState(examId, state);
    const clock = document.querySelector("[data-role='timer']");
    if (clock) {
      clock.textContent = formatClock(sectionState().timeRemainingSec);
    }
  }, 1000);
}

function stopTimer() {
  if (timerId) {
    window.clearInterval(timerId);
    timerId = null;
  }
}

function finishModule() {
  sectionState().status = "completed";
  state.stage = "module-end";
  state.ui.navigatorOpen = false;
  persistAndRender();
}

function continueAfterModule() {
  if (state.sectionIndex < exam.sections.length - 1) {
    state.sectionIndex += 1;
    state.questionIndex = 0;
    state.sectionStates[state.sectionIndex].status = "locked";
    persistState(examId, state);
      window.location.href = window.sitePath(`/ap/start/directions/?examId=${encodeURIComponent(examId)}&sectionIndex=${state.sectionIndex}`);
    return;
  }

  state.results = buildResultSummary();
  state.stage = "results";
  stopTimer();
  persistAndRender();
}

function buildResultSummary() {
  const sections = exam.sections.map((section, sectionIndex) => ({
    title: section.title,
    partTitle: section.partTitle,
    answered: state.sectionStates[sectionIndex].answers.filter((answer, index) => isAnswered(answer, section.questions[index])).length,
    total: section.questions.length,
    flagged: state.sectionStates[sectionIndex].flagged.filter(Boolean).length
  }));

  const mcqAccuracy = computeMcqAccuracy();
  return { sections, mcqAccuracy };
}

function computeMcqAccuracy() {
  if (!answerKeyMap || answerKeyMap.size === 0) {
    return null;
  }

  let totalMcq = 0;
  let correctMcq = 0;
  let answeredMcq = 0;

  exam.sections.forEach((section, sectionIndex) => {
    section.questions.forEach((question, questionIndex) => {
      if (question.type === 'frq') {
        return;
      }
      totalMcq += 1;
      const userAnswer = state.sectionStates[sectionIndex].answers[questionIndex];
      const correctAnswer = answerKeyMap.get(String(question.id));
      if (isAnswered(userAnswer, question)) {
        answeredMcq += 1;
        if (correctAnswer && String(userAnswer).trim().toUpperCase() === String(correctAnswer).trim()) {
          correctMcq += 1;
        }
      }
    });
  });

  if (totalMcq === 0) {
    return null;
  }

  const rate = totalMcq > 0 ? correctMcq / totalMcq : 0;
  // Heuristic: MCQ is ~50% of AP score, estimate 1-5
  const estimatedScore = rate >= 0.85 ? 5 : rate >= 0.70 ? 4 : rate >= 0.55 ? 3 : rate >= 0.40 ? 2 : 1;

  return {
    totalMcq,
    correctMcq,
    answeredMcq,
    rate: Math.round(rate * 100),
    estimatedScore
  };
}

async function loadBranchDiagnosticsResources() {
  if (!isCalcBcResultsExam()) {
    return null;
  }

  try {
    const [mappingResponse, contractResponse] = await Promise.all([
      fetch(window.sitePath(getBranchMappingPath())),
      fetch(window.sitePath(CALC_BC_TRUNK_CONTRACT_PATH))
    ]);

    if (!mappingResponse.ok || !contractResponse.ok) {
      console.warn("Branch diagnostics resources unavailable", {
        examId,
        mappingStatus: mappingResponse.status,
        contractStatus: contractResponse.status
      });
      return null;
    }

    const [mapping, contract] = await Promise.all([
      mappingResponse.json(),
      contractResponse.json()
    ]);

    return {
      mapping,
      contract
    };
  } catch (error) {
    console.warn("Failed to load branch diagnostics resources", examId, error);
    return null;
  }
}

function isCalcBcResultsExam() {
  return RESULTS_EXAM_IDS.has(String(examId || ""));
}

const ANSWER_KEY_PATHS = {
  '1902622411800285184': '/v2/data/calc-bc-2018-intl/questions.json',
  'calc-bc-2018-intl': '/v2/data/calc-bc-2018-intl/questions.json',
  '1902622411338911744': '/v2/data/calc-bc-2017-intl/questions.json',
  'calc-bc-2017-intl': '/v2/data/calc-bc-2017-intl/questions.json'
};

async function loadAnswerKeys() {
  if (!isCalcBcResultsExam()) {
    return null;
  }
  const path = ANSWER_KEY_PATHS[String(examId || "")];
  if (!path) {
    return null;
  }
  try {
    const response = await fetch(window.sitePath(path));
    if (!response.ok) {
      return null;
    }
    const questions = await response.json();
    if (!Array.isArray(questions)) {
      return null;
    }
    const map = new Map();
    questions.forEach((q) => {
      if (q.question_id && q.correct_answer) {
        map.set(String(q.question_id), String(q.correct_answer));
      }
    });
    return map.size > 0 ? map : null;
  } catch {
    return null;
  }
}

function buildBranchDiagnostics() {
  if (!isCalcBcResultsExam() || !branchDiagnosticsResources?.mapping || !branchDiagnosticsResources?.contract) {
    return null;
  }

  const questionRecords = flattenExamQuestions();
  const mappingEntries = Array.isArray(branchDiagnosticsResources.mapping?.mappings)
    ? branchDiagnosticsResources.mapping.mappings
    : [];
  const contract = branchDiagnosticsResources.contract || {};
  const trunkById = new Map((contract.trunks || []).map((item) => [item.id, item]));
  const branchById = new Map((contract.branches || []).map((item) => [item.id, item]));
  const questionBySequence = new Map(questionRecords.map((record) => [record.sequenceInExam, record]));
  const questionById = new Map(questionRecords.map((record) => [String(record.question?.id || ""), record]));

  const mappedRecords = mappingEntries
    .map((mappingEntry) => {
      const record = questionBySequence.get(Number(mappingEntry.sequenceInExam)) || questionById.get(String(mappingEntry.questionId || ""));
      if (!record) {
        return null;
      }
      const branchId = mappingEntry.branchId || (Array.isArray(mappingEntry.branchIds) ? mappingEntry.branchIds[0] : "");
      return {
        record,
        mappingEntry,
        trunkId: mappingEntry.trunkId,
        trunk: trunkById.get(mappingEntry.trunkId) || null,
        branchId,
        branch: branchById.get(branchId) || null,
        answered: isAnswered(record.answer, record.question)
      };
    })
    .filter(Boolean);

  if (!mappedRecords.length) {
    return {
      available: false,
      reason: "No mapped questions matched this exam attempt."
    };
  }

  const mappedSequenceSet = new Set(mappedRecords.map((item) => item.record.sequenceInExam));
  const unmappedVisibleQuestionCount = questionRecords.filter((record) => !mappedSequenceSet.has(record.sequenceInExam)).length;
  const answeredMappedCount = mappedRecords.filter((item) => item.answered).length;
  const unansweredMappedCount = mappedRecords.length - answeredMappedCount;
  const diagnosticsByTrunk = aggregateCoverage(mappedRecords, (item) => item.trunkId, (item) => ({
    id: item.trunkId,
    name: item.trunk?.name || item.trunkId,
    description: item.trunk?.description || ""
  }));
  const diagnosticsByBranch = aggregateCoverage(mappedRecords, (item) => item.branchId, (item) => ({
    id: item.branchId,
    name: item.branch?.name || item.branchId,
    description: item.branch?.description || "",
    trunkId: item.trunkId,
    trunkName: item.trunk?.name || item.trunkId
  }));

  diagnosticsByTrunk.sort(compareCoverageDiagnostics);
  diagnosticsByBranch.sort(compareCoverageDiagnostics);

  const weakBranches = diagnosticsByBranch.filter((item) => item.unansweredCount > 0).slice(0, 3);
  const coveredBranches = diagnosticsByBranch.filter((item) => item.answeredCount > 0).slice(0, 3);

  return {
    available: true,
    mappedQuestionCount: mappedRecords.length,
    answeredMappedCount,
    unansweredMappedCount,
    mappedCoverageRate: mappedRecords.length ? answeredMappedCount / mappedRecords.length : 0,
    unmappedVisibleQuestionCount,
    diagnosticsByTrunk,
    diagnosticsByBranch,
    weakBranches,
    coveredBranches
  };
}

function flattenExamQuestions() {
  let sequenceInExam = 0;
  return exam.sections.flatMap((section, sectionIndex) =>
    section.questions.map((question, questionIndex) => {
      sequenceInExam += 1;
      return {
        section,
        sectionIndex,
        question,
        questionIndex,
        sequenceInExam,
        answer: state.sectionStates?.[sectionIndex]?.answers?.[questionIndex]
      };
    })
  );
}

function aggregateCoverage(items, getKey, createMeta) {
  const buckets = new Map();

  items.forEach((item) => {
    const key = getKey(item);
    if (!key) {
      return;
    }
    if (!buckets.has(key)) {
      buckets.set(key, {
        ...createMeta(item),
        mappedCount: 0,
        answeredCount: 0,
        unansweredCount: 0,
        sequences: []
      });
    }
    const bucket = buckets.get(key);
    bucket.mappedCount += 1;
    bucket.sequences.push(item.record.sequenceInExam);
    if (item.answered) {
      bucket.answeredCount += 1;
    } else {
      bucket.unansweredCount += 1;
    }
  });

  return [...buckets.values()].map((bucket) => ({
    ...bucket,
    coverageRate: bucket.mappedCount ? bucket.answeredCount / bucket.mappedCount : 0,
    riskLabel: getCoverageRiskLabel(bucket)
  }));
}

function getCoverageRiskLabel(bucket) {
  if (bucket.unansweredCount >= Math.max(2, Math.ceil(bucket.mappedCount / 2))) {
    return "Needs follow-up";
  }
  if (bucket.unansweredCount > 0) {
    return "Partially covered";
  }
  return "Covered in this attempt";
}

function compareCoverageDiagnostics(left, right) {
  if (right.unansweredCount !== left.unansweredCount) {
    return right.unansweredCount - left.unansweredCount;
  }
  if (left.coverageRate !== right.coverageRate) {
    return left.coverageRate - right.coverageRate;
  }
  if (right.mappedCount !== left.mappedCount) {
    return right.mappedCount - left.mappedCount;
  }
  return String(left.name || "").localeCompare(String(right.name || ""));
}

function formatCoverageRatio(answeredCount, mappedCount) {
  return `${answeredCount}/${mappedCount} answered`;
}

function formatSequenceSummary(sequences) {
  return sequences.length ? `Questions ${sequences.join(", ")}` : "Questions unavailable";
}

const EXAM_ID_SLUG_MAP = {
  '2015Intl': 'calc-bc-2015-intl',
  'calc-bc-2015-intl': 'calc-bc-2015-intl',
  '1902622411338911744': 'calc-bc-2017-intl',
  'calc-bc-2017-intl': 'calc-bc-2017-intl',
  '1902622411800285184': 'calc-bc-2018-intl',
  'calc-bc-2018-intl': 'calc-bc-2018-intl'
};

function buildBranchDrillHref(branchId) {
  if (!branchId || !isCalcBcResultsExam()) {
    return "";
  }
  const rawId = String(examId || "");
  const drillExamId = EXAM_ID_SLUG_MAP[rawId] || rawId;
  return window.sitePath(`/training/?examId=${encodeURIComponent(drillExamId)}&branchId=${encodeURIComponent(branchId)}`);
}

function renderBranchDiagnostics() {
  const diagnostics = buildBranchDiagnostics();
  if (!diagnostics) {
    return "";
  }

  if (!diagnostics.available) {
    return `
      <section class="diagnostic-panel">
        <div class="diagnostic-panel__header">
          <div>
            <div class="micro-kicker">Trunk and branch diagnosis</div>
            <h2>Cal BC structure diagnosis</h2>
          </div>
        </div>
        <p class="diagnostic-panel__note">Branch mapping is not available for this attempt yet.</p>
      </section>
    `;
  }

  const priorityCopy = diagnostics.weakBranches.length
    ? diagnostics.weakBranches.map((item) => `${escapeHtml(item.name)} (${item.unansweredCount} not yet answered across ${item.mappedCount} mapped questions)`).join("; ")
    : "No mapped branch is currently showing unanswered risk.";
  const coveredCopy = diagnostics.coveredBranches.length
    ? diagnostics.coveredBranches.map((item) => `${escapeHtml(item.name)} (${formatCoverageRatio(item.answeredCount, item.mappedCount)})`).join("; ")
    : "No mapped branch has answered coverage yet.";

  return `
    <section class="diagnostic-panel">
      <div class="diagnostic-panel__header">
        <div>
          <div class="micro-kicker">Trunk and branch diagnosis</div>
          <h2>Cal BC structure diagnosis</h2>
        </div>
        <p class="diagnostic-panel__note">This summary uses mapped-question coverage only. It does not estimate correctness or AP score yet.</p>
      </div>
      <div class="diagnostic-summary-grid">
        <article class="result-card diagnostic-summary-card">
          <strong>Mapped question coverage</strong>
          <span>${diagnostics.answeredMappedCount}/${diagnostics.mappedQuestionCount} answered</span>
          <p>${diagnostics.unansweredMappedCount} mapped question(s) were left blank, so those trunks and branches stay at higher follow-up risk.</p>
        </article>
        <article class="result-card diagnostic-summary-card">
          <strong>Priority follow-up</strong>
          <span>${diagnostics.weakBranches.length ? `${diagnostics.weakBranches.length} branch(es)` : "No open branch risk"}</span>
          <p>${priorityCopy}</p>
        </article>
        <article class="result-card diagnostic-summary-card">
          <strong>Branches you already touched</strong>
          <span>${diagnostics.coveredBranches.length ? `${diagnostics.coveredBranches.length} branch(es)` : "No covered branches yet"}</span>
          <p>${coveredCopy}</p>
        </article>
        <article class="result-card diagnostic-summary-card">
          <strong>Graceful fallback</strong>
          <span>${diagnostics.unmappedVisibleQuestionCount} unmapped question(s)</span>
          <p>Unmapped questions are excluded from trunk/branch aggregation, so the results page stays stable while coverage grows.</p>
        </article>
      </div>
      <div class="diagnostic-detail-grid">
        <section class="diagnostic-column">
          <div class="diagnostic-column__title-row">
            <h3>By trunk</h3>
            <span>Coverage and follow-up risk</span>
          </div>
          ${renderCoverageCards(diagnostics.diagnosticsByTrunk, { showTrunkName: false })}
        </section>
        <section class="diagnostic-column">
          <div class="diagnostic-column__title-row">
            <h3>By branch</h3>
            <span>Mapped sample questions only</span>
          </div>
          ${renderCoverageCards(diagnostics.diagnosticsByBranch, { showTrunkName: true, showBranchDrill: true })}
        </section>
      </div>
    </section>
  `;
}

function renderCoverageCards(items, options = {}) {
  if (!items.length) {
    return `<p class="diagnostic-panel__note">No mapped coverage is available yet.</p>`;
  }

  return `
    <div class="diagnostic-card-stack">
      ${items.map((item) => {
        const drillHref = options.showBranchDrill ? buildBranchDrillHref(item.id) : "";
        return `
        <article class="diagnostic-card ${item.unansweredCount > 0 ? "is-risk" : "is-covered"}">
          <div class="diagnostic-card__topline">
            <strong>${escapeHtml(item.name)}</strong>
            <span class="diagnostic-badge">${escapeHtml(item.riskLabel)}</span>
          </div>
          ${options.showTrunkName ? `<div class="diagnostic-card__meta">Trunk: ${escapeHtml(item.trunkName || "Unknown trunk")}</div>` : ""}
          ${item.description ? `<p>${escapeHtml(item.description)}</p>` : ""}
          <div class="diagnostic-card__stats">
            <span>${formatCoverageRatio(item.answeredCount, item.mappedCount)}</span>
            <span>${item.unansweredCount} unanswered</span>
          </div>
          <div class="diagnostic-card__meta">${escapeHtml(formatSequenceSummary(item.sequences))}</div>
          ${drillHref ? `<div class="diagnostic-card__actions"><a class="secondary-button inline-button diagnostic-link" href="${drillHref}">Open branch drill</a></div>` : ""}
        </article>
      `;
      }).join("")}
    </div>
  `;
}

function render() {
  if (state.stage === "review") {
    renderReview();
  } else if (state.stage === "module-end") {
    renderModuleEnd();
  } else if (state.stage === "results") {
    renderResults();
  } else {
    renderExam();
  }
  attachImageFallbacks();
  renderMathAfterMount();
  scrollCurrentChipIntoView();
}

function scrollCurrentChipIntoView() {
  const chip = document.querySelector('.question-chip.is-current');
  if (chip && chip.parentElement) {
    chip.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  }
}

function renderExam() {
  const section = currentSection();
  const question = currentQuestion();
  const meta = deriveSectionMeta(section, exam);
  const flagged = sectionState().flagged[state.questionIndex];
  const answer = sectionState().answers[state.questionIndex];
  const isEmpty = !question.prompt || !question.prompt.trim();
  const isPlaceholder = isEmpty && (!question.options || question.options.length === 0);

  app.innerHTML = `
    <div class="exam-layout ${question.type === "frq" ? "is-frq" : ""}">
      ${renderTopBar(meta)}
      ${renderToolPanels()}
      <main class="exam-body">
        <section class="workspace ${question.type === "frq" ? "workspace-frq" : ""}">
          <div class="question-pane ${state.ui.lineReaderOn ? "line-reader-on" : ""}">
            <div class="question-label">Question ${state.questionIndex + 1}</div>
            <div class="question-content">
              ${isPlaceholder
                ? `<div class="question-text" style="color:var(--text-muted);font-style:italic;padding:2rem;text-align:center;border:1px dashed var(--border-light);border-radius:8px;background:rgba(59,130,246,0.05);">
                    <div style="font-size:2rem;margin-bottom:0.5rem;">📝</div>
                    <div style="font-size:1.1rem;font-weight:600;color:var(--text);">FRQ 题目暂缺</div>
                    <div style="margin-top:0.5rem;font-size:0.9rem;">此题为自由作答部分（FRQ），题目内容尚未导入。<br>你可以跳过此题，或标记后回来补充。</div>
                  </div>`
                : `<div class="question-text">${formatText(question.prompt)}</div>`}
              ${renderOptions(question, answer)}
            </div>
          </div>
          ${question.type === "frq" ? `
            <aside class="response-pane">
              <div class="response-head">
                <strong>Response</strong>
                <span>Saved automatically</span>
              </div>
              <textarea name="answer" placeholder="Write your response here.">${escapeHtml(String(answer || ""))}</textarea>
            </aside>
          ` : ""}
        </section>
      </main>
      ${renderBottomNav()}
      ${state.ui.navigatorOpen ? renderNavigatorModal() : ""}
      ${state.ui.directionsOpen ? renderDirectionsModal(meta) : ""}
    </div>
  `;
}

function renderTopBar(meta) {
  const timerText = state.ui.hideTimer ? "Timer hidden" : formatClock(sectionState().timeRemainingSec);
  return `
    <header class="exam-topbar">
      <div class="left-cluster">
        <div class="section-copy">
          <div class="kicker">${escapeHtml(meta.sectionLabel)}</div>
          <div class="title-line">${escapeHtml(meta.partLabel)}</div>
        </div>
        <button class="top-link" type="button" data-action="toggle-directions">Directions</button>
      </div>
      <div class="timer-cluster">
        <span class="timer-label">${state.startConfig.timekeepingModeOn ? "Time Remaining" : "Timer"}</span>
        <strong data-role="timer">${escapeHtml(timerText)}</strong>
        <button class="timer-toggle" type="button" data-action="toggle-hide-timer">${state.ui.hideTimer ? "Show" : "Hide"}</button>
      </div>
      <div class="tool-cluster">
        <button class="tool-pill" type="button" data-action="toggle-notes">Highlights &amp; Notes</button>
        <button class="tool-pill" type="button" data-action="toggle-scratch">Scratchpad</button>
        <button class="tool-pill" type="button" data-action="toggle-more">More</button>
      </div>
    </header>
  `;
}

function renderToolPanels() {
  const panels = [];
  if (state.ui.moreOpen) {
    panels.push(`
      <section class="floating-panel more-panel">
        <div class="panel-head">
          <strong>More</strong>
          <div class="panel-actions">
            <button class="panel-link" type="button" data-action="expand-all">Expand all</button>
            <button class="panel-link" type="button" data-action="collapse-all">Collapse all</button>
            <button class="panel-link" type="button" data-action="close-panel">Close</button>
          </div>
        </div>
        <div class="menu-grid">
          ${TOOL_MENU_ITEMS.map((item) => {
            const action = item === "Help"
              ? "toggle-help"
              : item === "Keyboard Shortcuts"
              ? "toggle-shortcuts"
              : item === "Assistive Technology"
              ? "toggle-assistive"
              : item === "Line Reader"
              ? "toggle-line-reader"
              : "toggle-break-tool";
            return `<button class="menu-item" type="button" data-action="${action}">${escapeHtml(item)}</button>`;
          }).join("")}
        </div>
      </section>
    `);
  }
  if (state.ui.helpOpen) {
    panels.push(renderInfoPanel("Help", "Use Next to move through the module. Open Question Navigator at any time to jump between questions."));
  }
  if (state.ui.shortcutsOpen) {
    panels.push(renderInfoPanel("Keyboard Shortcuts", "Use Tab to move between controls. Arrow keys and screen-reader shortcuts are preserved by the browser."));
  }
  if (state.ui.notesOpen) {
    panels.push(renderInfoPanel("Highlights & Notes", "Highlighting and note-taking are mocked in this browser build. The panel is here so the full shell still matches the official flow."));
  }
  if (state.ui.scratchOpen) {
    panels.push(`
      <section class="floating-panel info-panel">
        <div class="panel-head">
          <strong>Scratchpad</strong>
          <button class="panel-link" type="button" data-action="close-panel">Close</button>
        </div>
        <textarea class="scratchpad" placeholder="Use this area for rough work.">${escapeHtml(sectionState().scratchpad || "")}</textarea>
      </section>
    `);
  }
  if (state.ui.assistiveOpen) {
    panels.push(renderInfoPanel("Assistive Technology", "Line reader, timer visibility, and modal-based directions are available in this mocked shell."));
  }
  if (state.ui.onScheduleBreak) {
    panels.push(renderInfoPanel("On-Schedule Break", "Scheduled breaks appear between modules. You can still skip them from the transition page."));
  }
  return panels.length ? `<div class="panel-stack">${panels.join("")}</div>` : "";
}

function renderInfoPanel(title, body) {
  return `
    <section class="floating-panel info-panel">
      <div class="panel-head">
        <strong>${escapeHtml(title)}</strong>
        <button class="panel-link" type="button" data-action="close-panel">Close</button>
      </div>
      <p>${escapeHtml(body)}</p>
    </section>
  `;
}

function renderOptions(question, answer) {
  if (question.type === "frq") {
    return "";
  }
  if (!question.options || question.options.length === 0) {
    return `<div style="color:var(--text-muted);font-style:italic;padding:1rem 0;font-size:0.9rem;">暂无选项</div>`;
  }
  const values = Array.isArray(answer) ? answer : [];
  return `
    <div class="option-list">
      ${question.options.map((option) => {
        const selected = question.type === "single" ? answer === option.key : values.includes(option.key);
        return `
          <label class="option-row ${selected ? "is-selected" : ""}">
            <input
              type="${question.type === "single" ? "radio" : "checkbox"}"
              name="answer"
              value="${escapeHtml(option.key)}"
              ${selected ? "checked" : ""}>
            <span class="option-key">${escapeHtml(option.key)}</span>
            <div class="option-copy">${formatText(option.content || option.text)}</div>
          </label>
        `;
      }).join("")}
    </div>
  `;
}

function renderBottomNav() {
  const section = currentSection();
  const isFlagged = sectionState().flagged[state.questionIndex];
  return `
    <footer class="question-footer">
      <div class="footer-progress">
        <strong data-action="toggle-navigator" style="cursor:pointer">Question ${state.questionIndex + 1} of ${section.questions.length}</strong>
        <span>${countAnswered(state.sectionIndex)}/${section.questions.length} answered</span>
      </div>
      <div class="question-strip">
        ${section.questions.map((question, index) => {
          const answered = isAnswered(sectionState().answers[index], question);
          const flagged = sectionState().flagged[index];
          const isPlaceholder = !question.prompt || (!question.prompt.trim() && (!question.options || question.options.length === 0));
          return `
            <button class="question-chip ${index === state.questionIndex ? "is-current" : ""} ${answered ? "is-answered" : ""} ${flagged ? "is-flagged" : ""} ${isPlaceholder ? "is-placeholder" : ""}" type="button" data-action="go-question" data-question-index="${index}" ${isPlaceholder ? 'title="FRQ 题目暂缺"' : ""}>
              ${index + 1}
            </button>
          `;
        }).join("")}
      </div>
      <div class="footer-actions">
        <button class="secondary-footer ${isFlagged ? "flagged" : ""}" type="button" data-action="toggle-flag">${isFlagged ? "★ Unflag" : "☆ Flag for Review"}</button>
        <button class="secondary-footer" type="button" data-action="toggle-navigator">Navigator</button>
        <button class="primary-footer" type="button" data-action="prev-question" ${state.questionIndex === 0 ? "disabled" : ""}>Back</button>
        <button class="primary-footer" type="button" data-action="next-question">${state.questionIndex === section.questions.length - 1 ? "Review" : "Next"}</button>
      </div>
    </footer>
  `;
}

function renderNavigatorModal() {
  return `
    <div class="modal-shell">
      <section class="modal-card">
        <div class="panel-head">
          <strong>Question Navigator</strong>
          <button class="panel-link" type="button" data-action="toggle-navigator">Close</button>
        </div>
        <div class="navigator-grid">
          ${currentSection().questions.map((question, index) => {
            const answered = isAnswered(sectionState().answers[index], question);
            const flagged = sectionState().flagged[index];
            return `<button class="question-chip ${index === state.questionIndex ? "is-current" : ""} ${answered ? "is-answered" : ""} ${flagged ? "is-flagged" : ""}" type="button" data-action="go-question" data-question-index="${index}">${index + 1}</button>`;
          }).join("")}
        </div>
        <button class="primary-button inline-button" type="button" data-action="open-review">Review Questions</button>
      </section>
    </div>
  `;
}

function renderDirectionsModal(meta) {
  return `
    <div class="modal-shell">
      <section class="modal-card directions-modal">
        <div class="panel-head">
          <strong>Directions</strong>
          <button class="panel-link" type="button" data-action="toggle-directions">Close</button>
        </div>
        <div class="directions-grid">
          <div><strong>${escapeHtml(meta.sectionLabel)}</strong><span>${escapeHtml(meta.partLabel)}</span></div>
          <div><strong>Time</strong><span>${escapeHtml(meta.timeLabel)}</span></div>
          <div><strong>Questions</strong><span>${meta.questionCount}</span></div>
          <div><strong>Calculator</strong><span>${escapeHtml(meta.calculatorRule)}</span></div>
        </div>
        <div class="modal-copy">${escapeHtml(normalizeExamText(currentSection().directions || ""))}</div>
      </section>
    </div>
  `;
}

function renderReview() {
  const section = currentSection();
  app.innerHTML = `
    <div class="exam-center">
      <section class="shell-card review-shell">
        <div class="micro-kicker">Review</div>
        <h1>Check Your Work</h1>
        <p>Use Next when you are ready to leave this module. You can still return to any question before you continue.</p>
        <div class="navigator-grid">
          ${section.questions.map((question, index) => {
            const answered = isAnswered(sectionState().answers[index], question);
            const flagged = sectionState().flagged[index];
            return `<button class="question-chip ${answered ? "is-answered" : ""} ${flagged ? "is-flagged" : ""}" type="button" data-action="go-question" data-question-index="${index}">${index + 1}</button>`;
          }).join("")}
        </div>
        <div class="review-summary">
          <span>${countAnswered(state.sectionIndex)} answered</span>
          <span>${sectionState().flagged.filter(Boolean).length} flagged</span>
          <span>${formatClock(sectionState().timeRemainingSec)} remaining</span>
        </div>
        <div class="action-row">
          <button class="secondary-button inline-button" type="button" data-action="back-to-questions">Back</button>
          <button class="primary-button inline-button" type="button" data-action="submit-module">Next</button>
        </div>
      </section>
    </div>
  `;
}

function renderModuleEnd() {
  const hasNext = state.sectionIndex < exam.sections.length - 1;
  app.innerHTML = `
    <div class="exam-center">
      <section class="shell-card review-shell">
        <div class="micro-kicker">Module complete</div>
        <h1>This module is over</h1>
        <p>${hasNext ? "Select Next to continue to the next part of the exam." : "Select Next to finish this practice test."}</p>
        <div class="review-summary">
          <span>${countAnswered(state.sectionIndex)} answered</span>
          <span>${sectionState().flagged.filter(Boolean).length} flagged</span>
          <span>${formatClock(sectionState().timeRemainingSec)} remaining</span>
        </div>
        <div class="action-row">
          <button class="primary-button inline-button" type="button" data-action="advance-flow">Next</button>
        </div>
      </section>
    </div>
  `;
}

function renderResults() {
  const resultData = state.results || buildResultSummary();
  const results = resultData.sections || resultData;
  const mcqAccuracy = resultData.mcqAccuracy || null;

  let accuracyHtml = '';
  if (mcqAccuracy) {
    const scoreColor = mcqAccuracy.estimatedScore >= 4 ? '#059669' : mcqAccuracy.estimatedScore >= 3 ? '#d97706' : '#dc2626';
    accuracyHtml = `
      <div class="accuracy-panel">
        <div class="accuracy-panel__row">
          <div class="accuracy-panel__cell">
            <div class="accuracy-panel__label">MCQ Accuracy</div>
            <div class="accuracy-panel__value" style="color:#0369a1;">${mcqAccuracy.rate}%</div>
            <div class="accuracy-panel__detail">${mcqAccuracy.correctMcq} / ${mcqAccuracy.totalMcq} correct</div>
          </div>
          <div class="accuracy-panel__cell">
            <div class="accuracy-panel__label">Est. AP Score</div>
            <div class="accuracy-panel__value" style="color:${scoreColor};">${mcqAccuracy.estimatedScore}</div>
            <div class="accuracy-panel__detail">Heuristic (MCQ only)</div>
          </div>
          <div class="accuracy-panel__cell">
            <div class="accuracy-panel__label">FRQ</div>
            <div class="accuracy-panel__value" style="color:#64748b;">--</div>
            <div class="accuracy-panel__detail">Not scored yet</div>
          </div>
        </div>
      </div>`;
  } else {
    accuracyHtml = `
      <div class="accuracy-panel accuracy-panel--fallback">
        <p>Answer key not available for this exam. Correctness scoring will be added when answer keys are imported.</p>
      </div>`;
  }

  app.innerHTML = `
    <div class="exam-center">
      <section class="shell-card review-shell review-shell--results">
        <div class="micro-kicker">Practice complete</div>
        <h1>AP Practice Test</h1>
        <p>Your answers have been saved. ${mcqAccuracy ? 'Below is your MCQ accuracy and estimated score.' : 'Answer keys are not yet available for scoring.'}</p>
        ${accuracyHtml}
        <div class="result-grid">
          ${results.map((section) => `
            <article class="result-card">
              <strong>${escapeHtml(section.title)}</strong>
              <span>${escapeHtml(section.partTitle || "")}</span>
              <p>${section.answered}/${section.total} answered · ${section.flagged} flagged</p>
            </article>
          `).join("")}
        </div>
        ${renderBranchDiagnostics()}
        <div class="action-row">
          <button class="secondary-button inline-button" type="button" data-action="restart-exam">Start Again</button>
        </div>
      </section>
      <div class="modal-shell" id="confirm-shell" style="display:none;">
        <section class="modal-card">
          <div class="panel-head">
            <strong id="confirm-title"></strong>
          </div>
          <p class="modal-copy" id="confirm-body"></p>
          <div class="action-row">
            <button class="secondary-button inline-button" type="button" id="confirm-cancel">Cancel</button>
            <button class="primary-button inline-button" type="button" id="confirm-ok">Start Again</button>
          </div>
        </section>
      </div>
    </div>
  `;
}

function countAnswered(sectionIndex) {
  return exam.sections[sectionIndex].questions.filter((question, index) => isAnswered(state.sectionStates[sectionIndex].answers[index], question)).length;
}

function isAnswered(answer, question) {
  if (question.type === "multi") {
    return Array.isArray(answer) && answer.length > 0;
  }
  return String(answer || "").trim().length > 0;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
