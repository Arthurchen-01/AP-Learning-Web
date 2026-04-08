import {
  TOOL_MENU_ITEMS,
  createFreshState,
  deriveSectionMeta,
  ensureStateShape,
  formatClock,
  loadState,
  normalizeExamText,
  persistState,
  storageKey
} from "./mock-config.js";

const app = document.getElementById("app");

/* ─── Math rendering helpers ─── */

// Load KaTeX and return when ready
function loadKatex() {
  return new Promise((resolve) => {
    if (window.katex) return resolve();
    const css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css';
    document.head.appendChild(css);
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js';
    script.onload = () => resolve();
    script.onerror = () => resolve();
    document.head.appendChild(script);
  });
}

// Convert cleaned exam text to LaTeX where possible
function textToLatex(text) {
  let s = text;

  // Integral signs
  s = s.replace(/∫/g, '\\int ');

  // Sum/product
  s = s.replace(/∑/g, '\\sum ');
  s = s.replace(/∏/g, '\\prod ');

  // Square root patterns: "√x" or "sqrt(x)"
  s = s.replace(/√\s*(\w)/g, '\\sqrt{$1}');
  s = s.replace(/sqrt\s*\(([^)]+)\)/g, '\\sqrt{$1}');

  // Infinity
  s = s.replace(/∞/g, '\\infty ');

  // Greek letters
  s = s.replace(/π/g, '\\pi ');
  s = s.replace(/θ/g, '\\theta ');
  s = s.replace(/α/g, '\\alpha ');
  s = s.replace(/β/g, '\\beta ');
  s = s.replace(/γ/g, '\\gamma ');
  s = s.replace(/Δ/g, '\\Delta ');
  s = s.replace(/δ/g, '\\delta ');
  s = s.replace(/ε/g, '\\epsilon ');
  s = s.replace(/μ/g, '\\mu ');
  s = s.replace(/σ/g, '\\sigma ');
  s = s.replace(/Σ/g, '\\Sigma ');
  s = s.replace(/ω/g, '\\omega ');
  s = s.replace(/Ω/g, '\\Omega ');
  s = s.replace(/λ/g, '\\lambda ');
  s = s.replace(/ρ/g, '\\rho ');
  s = s.replace(/τ/g, '\\tau ');
  s = s.replace(/φ/g, '\\phi ');
  s = s.replace(/ψ/g, '\\psi ');

  // ≤ ≥ ≠ ≈
  s = s.replace(/≤/g, '\\le ');
  s = s.replace(/≥/g, '\\ge ');
  s = s.replace(/≠/g, '\\ne ');
  s = s.replace(/≈/g, '\\approx ');

  // ± × ÷
  s = s.replace(/±/g, '\\pm ');
  s = s.replace(/×/g, '\\times ');
  s = s.replace(/÷/g, '\\div ');

  // Derivative prime: f ′ ( x ) → f'(x)
  s = s.replace(/\s*′\s*/g, "'");

  // Negative sign normalization
  s = s.replace(/−/g, '-');

  // ── Trig functions (MUST come before exponent rule) ──
  // Step 1: Convert "cos 2 (" → "\cos^{2}("  and "cos 2 " → "\cos^{2} "
  s = s.replace(/(sin|cos|tan|cot|sec|csc)\s+(\d+)\s*\(/g, '\\$1^{$2}(');
  s = s.replace(/(sin|cos|tan|cot|sec|csc)\s+(\d+)(?=[\s,)])/g, '\\$1^{$2}');
  // Step 2: Convert "sin(" → "\sin("
  s = s.replace(/(sin|cos|tan|cot|sec|csc)\(/g, '\\$1(');
  // Step 3: Convert any remaining trig name (handles "2sin", "-sin", " sin", etc.)
  // Replace all bare trig names not already preceded by backslash
  s = s.replace(/([^\\]|^)(sin|cos|tan|cot|sec|csc)\b/g, '$1\\$2');

  // Inverse trig
  s = s.replace(/(sin|cos|tan)⁻¹/g, '\\$1^{-1}');

  // ln / log / exp
  s = s.replace(/\bln\s/g, '\\ln ');
  s = s.replace(/\bln\(/g, '\\ln(');
  s = s.replace(/\blog\s/g, '\\log ');
  s = s.replace(/\bexp\s*\(/g, '\\exp(');
  s = s.replace(/\bexp\s/g, '\\exp ');

  // ── Fractions ──
  s = s.replace(/(\w+)\s*\/\s*(\w+)/g, '\\frac{$1}{$2}');
  s = s.replace(/\(([^)]+)\)\s*\/\s*\(([^)]+)\)/g, '\\frac{$1}{$2}');

  // ── Exponents (after trig conversion) ──
  // Single letter + space + number: "x 3" → "x^{3}"
  s = s.replace(/([a-zA-Z])\s+(\d+)(?!\s*[a-zA-Z])/g, '$1^{$2}');

  // Negative exponents: "t -5/2" or "t -5"
  s = s.replace(/([a-zA-Z])\s+-(\d+)\/(\d+)/g, '$1^{-$2/$3}');
  s = s.replace(/([a-zA-Z])\s+-(\d+)(?!\d)/g, '$1^{-$2}');

  // Power on parentheses: "( x 3 + 2 ) 2" → "(x^3+2)^2"
  s = s.replace(/\)\s+(\d+)(?!\s*[a-zA-Z.])/g, ')^{$1}');

  // Clean up spaces
  s = s.replace(/\s+/g, ' ').trim();

  return s;
}

// Try to render text containing math with KaTeX
function renderMathInElement(html) {
  if (!window.katex) return html;

  // Split by MathType blocks (should already be stripped by normalizeExamText)
  // Then try to render each segment that looks like math

  // Strategy: wrap detected math sections in spans, then render with KaTeX
  const placeholder = '\x00';
  const blocks = [];
  let result = html;

  // Find <br> tags and protect them
  result = result.replace(/<br\s*\/?>/g, placeholder + 'BR' + placeholder);

  // Try to convert and render the entire text as math if it looks like a math expression
  // Heuristic: contains math symbols, trig functions, integrals, etc.
  const mathSignals = /\\?(?:sin|cos|tan|cot|sec|csc|ln|log|exp|∫|∑|∏|√|π|θ|α|β|∞|≤|≥|≠|±|′)/;
  const hasDerivative = /[fgh]\s*['′]\s*\(/;
  const hasPowers = /[a-zA-Z]\s*\{?\d+\}?/;
  const hasFraction = /\\frac|[−-]\s*\d+\s*\/\s*\d+/;

  // Process line by line (split by <br>)
  const lines = result.split(placeholder + 'BR' + placeholder);
  const renderedLines = lines.map(line => {
    // Unescape HTML entities for KaTeX processing
    let cleanText = line
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");

    // Skip if no math signals at all
    if (!mathSignals.test(cleanText) && !hasDerivative.test(cleanText)) {
      return line;
    }

    try {
      const latex = textToLatex(cleanText);
      if (latex && latex !== cleanText) {
        const rendered = window.katex.renderToString(latex, {
          throwOnError: false,
          displayMode: false,
          trust: true,
          strict: false
        });
        return `<span class="math-block">${rendered}</span>`;
      }
    } catch (e) {
      // Fall back to original text
    }
    return line;
  });

  return renderedLines.join('<br>');
}

// Enhanced formatText that tries to render math
function formatText(value) {
  if (!value) return "";
  // If the value contains HTML (MathML, spans, etc.), render it directly
  if (/<[a-z][\s\S]*>/i.test(value)) {
    return value;
  }
  const cleaned = normalizeExamText(value);
  const escaped = escapeHtml(cleaned).replace(/\n/g, "<br>");
  return escaped;
}

// After DOM is set, apply KaTeX rendering
async function renderMathAfterMount() {
  await loadKatex();
  if (!window.katex) return;

  document.querySelectorAll('.question-text, .option-copy').forEach(el => {
    if (el.dataset.mathRendered) return;
    el.dataset.mathRendered = 'true';

    // If the element already contains MathML, skip KaTeX processing
    if (el.querySelector('math') || el.innerHTML.includes('<math')) {
      return;
    }

    const html = el.innerHTML;
    const rendered = renderMathInElement(html);
    if (rendered !== html) {
      el.innerHTML = rendered;
    }
  });
}
const params = new URLSearchParams(window.location.search);
const examId = params.get("examId");

let exam = null;
let state = null;
let timerId = null;

init().catch((error) => {
  console.error(error);
  app.innerHTML = `<div class="exam-center"><section class="shell-card"><h1>Unable to load this exam</h1><p>${escapeHtml(String(error.message || error))}</p></section></div>`;
});

async function init() {
  if (!examId) {
    throw new Error("Missing examId");
  }

const response = await fetch(window.sitePath(`/mock-data/ap-exam-${examId}.json`));
  if (!response.ok) {
    throw new Error(`Missing mock data for examId ${examId}`);
  }

  exam = await response.json();
  state = loadState(examId) || createFreshState(exam);
  ensureStateShape(exam, state);
  if (!state.sectionStates[state.sectionIndex]) {
    state.sectionIndex = 0;
  }
  if (state.sectionStates[state.sectionIndex].status === "locked") {
    state.sectionStates[state.sectionIndex].status = "active";
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
    if (!["question", "review", "module-end"].includes(state.stage)) {
      return;
    }
    if (sectionState().status !== "active" && state.stage !== "module-end") {
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
  return exam.sections.map((section, sectionIndex) => ({
    title: section.title,
    partTitle: section.partTitle,
    answered: state.sectionStates[sectionIndex].answers.filter((answer, index) => isAnswered(answer, section.questions[index])).length,
    total: section.questions.length,
    flagged: state.sectionStates[sectionIndex].flagged.filter(Boolean).length
  }));
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
  renderMathAfterMount();
}

function renderExam() {
  const section = currentSection();
  const question = currentQuestion();
  const meta = deriveSectionMeta(section, exam);
  const flagged = sectionState().flagged[state.questionIndex];
  const answer = sectionState().answers[state.questionIndex];

  app.innerHTML = `
    <div class="exam-layout ${question.type === "frq" ? "is-frq" : ""}">
      ${renderTopBar(meta)}
      ${renderToolPanels()}
      <main class="exam-body">
        <section class="workspace ${question.type === "frq" ? "workspace-frq" : ""}">
          <div class="question-pane ${state.ui.lineReaderOn ? "line-reader-on" : ""}">
            <div class="question-label">Question ${state.questionIndex + 1}</div>
            <div class="question-content">
              <div class="question-text">${formatText(question.prompt)}</div>
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
            <span class="option-copy">${formatText(option.content || option.text)}</span>
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
          return `
            <button class="question-chip ${index === state.questionIndex ? "is-current" : ""} ${answered ? "is-answered" : ""} ${flagged ? "is-flagged" : ""}" type="button" data-action="go-question" data-question-index="${index}">
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
  const results = state.results || buildResultSummary();
  app.innerHTML = `
    <div class="exam-center">
      <section class="shell-card review-shell">
        <div class="micro-kicker">Practice complete</div>
        <h1>AP Practice Test</h1>
        <p>This imported paper is still running in practice mode. Answers were saved, but official scoring and answer keys have not been imported yet.</p>
        <div class="result-grid">
          ${results.map((section) => `
            <article class="result-card">
              <strong>${escapeHtml(section.title)}</strong>
              <span>${escapeHtml(section.partTitle || "")}</span>
              <p>${section.answered}/${section.total} answered · ${section.flagged} flagged</p>
            </article>
          `).join("")}
        </div>
        <div class="action-row">
          <button class="secondary-button inline-button" type="button" data-action="restart-exam">Start Again</button>
        </div>
      </section>
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
