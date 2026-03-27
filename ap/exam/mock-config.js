export const PREPARING_DELAY_MS = 1400;
export const BREAK_DURATION_SEC = 600;

export const START_OPTIONS = [
  {
    key: "timekeepingModeOn",
    label: "Timer mode",
    description: "Show the official countdown and auto-submit when time runs out.",
    enabledLabel: "On",
    disabledLabel: "Off",
    defaultValue: true
  },
  {
    key: "talkModeOn",
    label: "Talk mode",
    description: "Keep helper prompts available while you are still outside the test interface.",
    enabledLabel: "On",
    disabledLabel: "Off",
    defaultValue: false
  }
];

export const ENTRANCE_PANELS = [
  {
    title: "Timing",
    body: "Your timer begins when you enter the first part. Hide or show the timer at any point during the exam."
  },
  {
    title: "Scores",
    body: "This imported paper currently runs in practice mode. Answers are saved, but official scoring has not been imported yet."
  },
  {
    title: "Assistive Technology",
    body: "Highlights, notes, line reader, keyboard shortcuts, and other supports stay available throughout the test shell."
  }
];

export const TOOL_MENU_ITEMS = [
  "Help",
  "Keyboard Shortcuts",
  "Assistive Technology",
  "Line Reader",
  "On-Schedule Break"
];

export function storageKey(examId) {
  return `mokaoai-local-mock:${examId}`;
}

export function initialAnswer(question) {
  return question.type === "multi" ? [] : "";
}

export function createFreshState(examData) {
  return {
    stage: "question",
    sectionIndex: 0,
    questionIndex: 0,
    startedAt: null,
    lastSavedAt: Date.now(),
    startConfig: {
      timekeepingModeOn: true,
      talkModeOn: false
    },
    breakState: {},
    ui: {
      navigatorOpen: false,
      directionsOpen: false,
      moreOpen: false,
      helpOpen: false,
      shortcutsOpen: false,
      notesOpen: false,
      scratchOpen: false,
      lineReaderOn: false,
      hideTimer: false,
      assistiveOpen: false,
      onScheduleBreak: false
    },
    sectionStates: examData.sections.map((section) => ({
      status: "locked",
      timeRemainingSec: section.limitMinutes * 60,
      answers: section.questions.map((question) => initialAnswer(question)),
      flagged: section.questions.map(() => false)
    })),
    results: null
  };
}

export function loadState(examId) {
  try {
    const raw = localStorage.getItem(storageKey(examId));
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.warn("Failed to restore exam state", examId, error);
    return null;
  }
}

export function persistState(examId, state) {
  state.lastSavedAt = Date.now();
  localStorage.setItem(storageKey(examId), JSON.stringify(state));
}

export function ensureStateShape(exam, state) {
  state.startConfig = {
    timekeepingModeOn: true,
    talkModeOn: false,
    ...(state.startConfig || {})
  };
  state.breakState = state.breakState || {};
  state.ui = {
    navigatorOpen: false,
    directionsOpen: false,
    moreOpen: false,
    helpOpen: false,
    shortcutsOpen: false,
    notesOpen: false,
    scratchOpen: false,
    lineReaderOn: false,
    hideTimer: false,
    assistiveOpen: false,
    onScheduleBreak: false,
    ...(state.ui || {})
  };
  state.sectionStates = Array.isArray(state.sectionStates) ? state.sectionStates : [];

  exam.sections.forEach((section, index) => {
    const existing = state.sectionStates[index];
    if (!existing) {
      state.sectionStates[index] = {
        status: "locked",
        timeRemainingSec: section.limitMinutes * 60,
        answers: section.questions.map((question) => initialAnswer(question)),
        flagged: section.questions.map(() => false)
      };
      return;
    }

    existing.status = typeof existing.status === "string" ? existing.status : "locked";
    existing.timeRemainingSec = typeof existing.timeRemainingSec === "number" ? existing.timeRemainingSec : section.limitMinutes * 60;
    existing.answers = Array.isArray(existing.answers) ? existing.answers : section.questions.map((question) => initialAnswer(question));
    existing.flagged = Array.isArray(existing.flagged) ? existing.flagged : section.questions.map(() => false);

    if (existing.answers.length < section.questions.length) {
      existing.answers = existing.answers.concat(
        section.questions.slice(existing.answers.length).map((question) => initialAnswer(question))
      );
    }
    if (existing.flagged.length < section.questions.length) {
      existing.flagged = existing.flagged.concat(
        section.questions.slice(existing.flagged.length).map(() => false)
      );
    }
  });
}

export function deriveSectionMeta(section, exam) {
  const sectionLabel = section.title || "Section";
  const partLabel = section.partTitle || "Part";
  const directions = String(section.directions || "");
  const calculatorAllowed = /calculator is allowed/i.test(directions);
  const calculatorRule = calculatorAllowed
    ? "Calculator is allowed for this part of the exam."
    : "No calculator is allowed for this part of the exam.";
  const subjectLine = String(exam.subjectName || exam.title || "AP Practice Test");

  return {
    sectionLabel,
    partLabel,
    subjectLine,
    calculatorRule,
    questionCount: section.questions.length,
    timeLabel: section.limitMinutes >= 60
      ? `${section.limitMinutes / 60} hour${section.limitMinutes === 60 ? "" : "s"}`
      : `${section.limitMinutes} minutes`
  };
}

export function normalizeExamText(value) {
  return String(value || "")
    .replaceAll("路", "·")
    .replaceAll("鈥?", "'")
    .replaceAll("鈭?", "-")
    .replaceAll("鈪?", "II")
    .replaceAll("鈱?", "")
    .replaceAll("蟺", "π")
    .replaceAll("宦", "")
    .replace(/\s+@[\w]+@/g, "")
    .replace(/MathType@MTEF@[^ ]+/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

export function formatClock(totalSeconds) {
  const safe = Math.max(0, Math.round(totalSeconds));
  const hours = Math.floor(safe / 3600);
  const minutes = Math.floor((safe % 3600) / 60);
  const seconds = safe % 60;
  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}
